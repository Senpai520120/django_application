"""Data-миграция: базовые роли admin и user.

Имена ролей захардкожены намеренно — миграция описывает исторический факт и не
должна меняться вслед за константами в коде.
"""

from django.db import migrations

GROUP_NAMES = ("admin", "user")


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in GROUP_NAMES:
        Group.objects.get_or_create(name=name)


def delete_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=GROUP_NAMES).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]
