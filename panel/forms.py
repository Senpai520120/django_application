"""Формы панели. Максимум переиспользования встроенных форм Django."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User


def roles_field(**kwargs):
    """Чекбоксы со всеми существующими ролями (группами)."""
    kwargs.setdefault("label", "Роли")
    kwargs.setdefault("required", False)
    return forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        help_text="Отметьте роли, которые должны быть у пользователя.",
        **kwargs,
    )


class UserRolesForm(forms.ModelForm):
    """Назначение и снятие ролей: обычная ModelForm поверх `User.groups`."""

    groups = roles_field()

    class Meta:
        model = User
        fields = ["groups"]


class PanelUserCreationForm(UserCreationForm):
    """Создание пользователя админом (бонус).

    Наследуемся от встроенной `UserCreationForm`: валидация пароля и его
    хеширование достаются из коробки.
    """

    email = forms.EmailField(label="Email", required=False)
    groups = roles_field()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "groups")
