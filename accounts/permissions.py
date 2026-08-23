"""Единая точка правды о том, кто такой «админ» в этом проекте.

Роли — это встроенные группы Django (`auth.Group`), отдельной модели Role нет.
"""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

ADMIN_GROUP_NAME = "admin"
USER_GROUP_NAME = "user"

#: Роли, которые создаёт сид (data-миграция и команда `seed_groups`).
DEFAULT_GROUP_NAMES = (ADMIN_GROUP_NAME, USER_GROUP_NAME)


def is_admin(user: AbstractBaseUser | AnonymousUser) -> bool:
    """Имеет ли пользователь доступ к панели /manage/.

    Админ — это участник группы `admin`, либо `is_staff`, либо суперпользователь.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name=ADMIN_GROUP_NAME).exists()
