"""Идемпотентный сид базовых ролей."""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.permissions import DEFAULT_GROUP_NAMES


class Command(BaseCommand):
    help = "Создаёт базовые роли-группы (admin, user). Запускать можно повторно."

    def handle(self, *args, **options):
        created_names = []
        for name in DEFAULT_GROUP_NAMES:
            _, created = Group.objects.get_or_create(name=name)
            if created:
                created_names.append(name)
                self.stdout.write(self.style.SUCCESS(f"Роль создана: {name}"))
            else:
                self.stdout.write(f"Роль уже существует: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Создано ролей: {len(created_names)}, "
                f"всего базовых ролей: {len(DEFAULT_GROUP_NAMES)}."
            )
        )
