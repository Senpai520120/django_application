"""Общие фикстуры тестов."""

import pytest
from django.contrib.auth.models import Group, User

from accounts.permissions import ADMIN_GROUP_NAME, USER_GROUP_NAME

PASSWORD = "Str0ng-Pass!2024"


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def admin_group(db):
    """Группа admin создана data-миграцией accounts.0001_seed_groups."""
    return Group.objects.get(name=ADMIN_GROUP_NAME)


@pytest.fixture
def user_group(db):
    return Group.objects.get(name=USER_GROUP_NAME)


@pytest.fixture
def plain_user(db, user_group):
    """Обычный пользователь: роль user, доступа к панели нет."""
    user = User.objects.create_user(
        username="ivan",
        password=PASSWORD,
        email="ivan@example.com",
        first_name="Иван",
        last_name="Иванов",
    )
    user.groups.add(user_group)
    return user


@pytest.fixture
def group_admin(db, admin_group):
    """Админ по группе admin — без is_staff и без суперправ."""
    user = User.objects.create_user(
        username="boss",
        password=PASSWORD,
        email="boss@example.com",
    )
    user.groups.add(admin_group)
    return user


@pytest.fixture
def staff_admin(db):
    """Админ по флагу is_staff."""
    return User.objects.create_user(
        username="stafferson",
        password=PASSWORD,
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="root",
        email="root@example.com",
        password=PASSWORD,
    )
