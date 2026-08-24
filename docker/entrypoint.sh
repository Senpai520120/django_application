#!/bin/sh
# Стартовая последовательность контейнера: подготовить БД и статику, затем
# передать управление команде из CMD (по умолчанию gunicorn).
set -e

echo "==> Миграции"
python manage.py migrate --noinput

echo "==> Базовые роли"
python manage.py seed_groups

# Тестовые пользователи создаются только по явному флагу. В образе по умолчанию
# выключено: аккаунты с общеизвестным паролем в бою не нужны.
if [ "${SEED_DEMO_USERS:-0}" = "1" ]; then
    echo "==> Тестовые пользователи (SEED_DEMO_USERS=1)"
    python manage.py seed_demo_users --force
fi

echo "==> Статика"
python manage.py collectstatic --noinput

echo "==> Запуск: $*"
exec "$@"
