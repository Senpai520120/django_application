"""Переиспользуемый контроль доступа для вьюх панели."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.permissions import is_admin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Пускает в панель только админов.

    Поведение достаётся от `AccessMixin` из коробки:

    * аноним — редирект на `LOGIN_URL` с `?next=`;
    * залогиненный не-админ — `PermissionDenied`, то есть HTTP 403.

    Наследуйте вьюху от этого миксина вместо копипаста проверок.
    """

    def test_func(self) -> bool:
        return is_admin(self.request.user)
