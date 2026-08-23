"""Тестовые пользователи для локальной проверки приложения.

Команда идемпотентна: повторный запуск не плодит дубликаты, а приводит уже
существующих демо-юзеров к описанному здесь состоянию (пароль, роли, флаги).
"""

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.permissions import ADMIN_GROUP_NAME, USER_GROUP_NAME

#: Префикс, по которому команда узнаёт «свои» аккаунты (в том числе при --delete).
DEMO_PREFIX = "demo_"

DEFAULT_PASSWORD = "demo-password-123"

#: username, имя, фамилия, роли, is_staff, is_active, зачем нужен
DEMO_USERS = [
    (
        "demo_admin",
        "Анна",
        "Админова",
        [ADMIN_GROUP_NAME],
        False,
        True,
        "админ по группе admin",
    ),
    (
        "demo_staff",
        "Семён",
        "Стаффов",
        [],
        True,
        True,
        "админ по флагу is_staff",
    ),
    (
        "demo_user",
        "Иван",
        "Иванов",
        [USER_GROUP_NAME],
        False,
        True,
        "обычный юзер, на /manage/ получит 403",
    ),
    (
        "demo_inactive",
        "Пётр",
        "Отключённый",
        [USER_GROUP_NAME],
        False,
        False,
        "деактивирован, войти не сможет",
    ),
]

EXTRA_NAMES = [
    ("Мария", "Смирнова"),
    ("Олег", "Кузнецов"),
    ("Дарья", "Попова"),
    ("Никита", "Соколов"),
    ("Елена", "Лебедева"),
    ("Артём", "Новиков"),
    ("Ольга", "Морозова"),
    ("Павел", "Волков"),
    ("Ксения", "Зайцева"),
    ("Роман", "Егоров"),
]


class Command(BaseCommand):
    help = (
        "Создаёт тестовых пользователей (demo_*) для локальной проверки: админа "
        "по группе, админа по is_staff, обычного юзера, деактивированного и "
        "пачку обычных юзеров для пагинации."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help=f"пароль для всех демо-аккаунтов (по умолчанию {DEFAULT_PASSWORD})",
        )
        parser.add_argument(
            "--extra",
            type=int,
            default=10,
            help="сколько дополнительных обычных юзеров создать (по умолчанию 10)",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="удалить всех demo_*-пользователей и выйти",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="разрешить запуск при DEBUG=False (по умолчанию запрещено)",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "DEBUG=False: команда создаёт аккаунты с общеизвестным паролем и "
                "по умолчанию не работает вне разработки. Нужно осознанно — "
                "добавьте --force."
            )

        if options["delete"]:
            deleted, _ = User.objects.filter(username__startswith=DEMO_PREFIX).delete()
            self.stdout.write(
                self.style.SUCCESS(f"Демо-пользователи удалены (объектов: {deleted}).")
            )
            return

        extra = max(0, min(options["extra"], len(EXTRA_NAMES)))
        password = options["password"]

        with transaction.atomic():
            groups = {
                name: Group.objects.get_or_create(name=name)[0]
                for name in (ADMIN_GROUP_NAME, USER_GROUP_NAME)
            }
            rows = [self.upsert(spec, password, groups) for spec in DEMO_USERS]
            for index in range(extra):
                first_name, last_name = EXTRA_NAMES[index]
                spec = (
                    f"{DEMO_PREFIX}user{index + 1:02d}",
                    first_name,
                    last_name,
                    [USER_GROUP_NAME],
                    False,
                    True,
                    "обычный юзер (для поиска и пагинации)",
                )
                rows.append(self.upsert(spec, password, groups))

        self.report(rows, password)

    def upsert(self, spec, password, groups):
        """Создаёт или обновляет одного демо-юзера. Возвращает строку для отчёта."""
        username, first_name, last_name, role_names, is_staff, is_active, note = spec

        user, created = User.objects.get_or_create(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = f"{username}@example.com"
        user.is_staff = is_staff
        user.is_active = is_active
        user.set_password(password)
        user.save()
        user.groups.set([groups[name] for name in role_names])

        return (username, ", ".join(role_names) or "—", note, created)

    def report(self, rows, password):
        created_count = sum(1 for *_, created in rows if created)
        width = max(len(username) for username, *_ in rows)

        self.stdout.write("")
        self.stdout.write(f"{'ЛОГИН'.ljust(width)}  РОЛИ         ЗАЧЕМ")
        for username, roles, note, created in rows:
            mark = "+" if created else "="
            self.stdout.write(
                f"{mark} {username.ljust(width)}  {roles.ljust(11)}  {note}"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Пароль у всех: {password}"))
        updated_count = len(rows) - created_count
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано новых: {created_count}, обновлено: {updated_count}."
            )
        )
        self.stdout.write("Удалить их все: manage.py seed_demo_users --delete")
