"""Вьюхи кастомной панели администратора (/manage/).

Доступ везде через `AdminRequiredMixin`: аноним — редирект на логин,
залогиненный не-админ — 403.
"""

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin
from panel.forms import PanelUserCreationForm, UserRolesForm
from panel.models import RoleChange


class UserListView(AdminRequiredMixin, ListView):
    """Список пользователей с поиском (?q=) и пагинацией."""

    template_name = "panel/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.prefetch_related("groups").order_by("username")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class RoleListView(AdminRequiredMixin, ListView):
    """Список ролей (групп) с количеством участников."""

    template_name = "panel/role_list.html"
    context_object_name = "roles"
    queryset = Group.objects.annotate(members_count=Count("user")).order_by("name")


class UserRolesUpdateView(AdminRequiredMixin, UpdateView):
    """Назначение и снятие ролей конкретному пользователю."""

    model = User
    form_class = UserRolesForm
    template_name = "panel/user_roles_form.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("panel:user_list")

    def form_valid(self, form):
        before = set(self.object.groups.all())
        response = super().form_valid(form)
        after = set(self.object.groups.all())

        changes = RoleChange.log_diff(
            actor=self.request.user,
            target=self.object,
            before=before,
            after=after,
        )
        if changes:
            messages.success(
                self.request,
                f"Роли пользователя {self.object.username} обновлены "
                f"(изменений: {len(changes)}).",
            )
        else:
            messages.info(
                self.request, f"Роли пользователя {self.object.username} не изменились."
            )
        return response


class UserCreateView(AdminRequiredMixin, CreateView):
    """Создание пользователя админом (бонус)."""

    model = User
    form_class = PanelUserCreationForm
    template_name = "panel/user_form.html"
    success_url = reverse_lazy("panel:user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        RoleChange.log_diff(
            actor=self.request.user,
            target=self.object,
            before=set(),
            after=set(self.object.groups.all()),
        )
        messages.success(self.request, f"Пользователь {self.object.username} создан.")
        return response


class UserToggleActiveView(AdminRequiredMixin, View):
    """Активация/деактивация пользователя. Только POST."""

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)
        if target == request.user:
            messages.error(request, "Нельзя деактивировать самого себя.")
        else:
            target.is_active = not target.is_active
            target.save(update_fields=["is_active"])
            state = "активирован" if target.is_active else "деактивирован"
            messages.success(request, f"Пользователь {target.username} {state}.")
        return redirect("panel:user_list")


class AuditLogView(AdminRequiredMixin, ListView):
    """История изменений ролей (бонус)."""

    template_name = "panel/audit_list.html"
    context_object_name = "changes"
    paginate_by = 20
    queryset = RoleChange.objects.select_related("actor", "target")
