#!/bin/sh
set -e

echo "==> Миграции"
python manage.py migrate --noinput

echo "==> Базовые роли"
python manage.py seed_groups

# Только по явному флагу: пароль у этих аккаунтов общеизвестный.
if [ "${SEED_DEMO_USERS:-0}" = "1" ]; then
    echo "==> Тестовые пользователи (SEED_DEMO_USERS=1)"
    python manage.py seed_demo_users --force
fi

echo "==> Запуск: $*"
exec "$@"
