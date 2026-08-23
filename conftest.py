"""Окружение для pytest.

pytest-django поднимает Django в `pytest_configure`, поэтому переменные нужно
выставить здесь — до импорта `config.settings`. Значения выставляются через
`setdefault`, так что в CI их можно переопределить снаружи.
"""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "False")
# В тестах не гоняем collectstatic, поэтому обычное хранилище вместо манифеста.
os.environ.setdefault(
    "STATICFILES_BACKEND",
    "django.contrib.staticfiles.storage.StaticFilesStorage",
)
