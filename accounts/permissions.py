"""Кто считается админом. Роли — встроенные auth.Group."""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

ADMIN_GROUP_NAME = "admin"
USER_GROUP_NAME = "user"

DEFAULT_GROUP_NAMES = (ADMIN_GROUP_NAME, USER_GROUP_NAME)


def is_admin(user: AbstractBaseUser | AnonymousUser) -> bool:
    """Участник группы admin, is_staff или суперпользователь.

    Результат кешируется на объекте пользователя: за запрос проверку зовут
    и миксин, и контекст-процессор, а запрос к БД нужен один.
    """
    cached = getattr(user, "_is_panel_admin", None)
    if cached is not None:
        return cached

    if not user.is_authenticated:
        result = False
    elif user.is_superuser or user.is_staff:
        result = True
    else:
        result = user.groups.filter(name=ADMIN_GROUP_NAME).exists()

    user._is_panel_admin = result
    return result
