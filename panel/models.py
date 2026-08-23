"""Модели панели.

Пользователи и роли — встроенные `auth.User` и `auth.Group`, своих моделей для
них нет. Здесь живёт только аудит-лог изменений ролей.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models


class RoleChange(models.Model):
    """Кто, кому и какую роль назначил или снял."""

    ACTION_ADDED = "added"
    ACTION_REMOVED = "removed"
    ACTION_CHOICES = [
        (ACTION_ADDED, "назначена"),
        (ACTION_REMOVED, "снята"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_changes_made",
        verbose_name="кто изменил",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_changes_received",
        verbose_name="кому",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_changes",
        verbose_name="роль",
    )
    # Имя роли дублируется строкой, чтобы запись аудита пережила удаление группы.
    group_name = models.CharField("имя роли", max_length=150)
    action = models.CharField("действие", max_length=16, choices=ACTION_CHOICES)
    created_at = models.DateTimeField("когда", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "изменение роли"
        verbose_name_plural = "изменения ролей"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        actor = self.actor.username if self.actor else "система"
        verb = self.get_action_display()
        return (
            f"{actor}: роль «{self.group_name}» {verb} "
            f"пользователю {self.target.username}"
        )

    @classmethod
    def log_diff(cls, *, actor, target, before, after):
        """Записывает разницу между старым и новым набором ролей.

        `before` и `after` — множества объектов `Group`. Возвращает список
        созданных записей (пустой, если ничего не изменилось).
        """
        added = sorted(set(after) - set(before), key=lambda group: group.name)
        removed = sorted(set(before) - set(after), key=lambda group: group.name)

        entries = [
            cls(
                actor=actor,
                target=target,
                group=group,
                group_name=group.name,
                action=action,
            )
            for group, action in (
                *((group, cls.ACTION_ADDED) for group in added),
                *((group, cls.ACTION_REMOVED) for group in removed),
            )
        ]
        if entries:
            cls.objects.bulk_create(entries)
        return entries
