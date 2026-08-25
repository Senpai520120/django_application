"""Настройки для тестов: не зависят от .env и от собранной статики."""

import os

# Выставляем до импорта основных настроек: там SECRET_KEY проверяется на импорте,
# а read_env не перетирает уже заданные переменные окружения.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "False")

from .settings import *  # noqa: E402, F403

# Манифест whitenoise требует collectstatic, в тестах он не нужен.
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Тесты создают десятки пользователей — на PBKDF2 это заметные секунды.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
