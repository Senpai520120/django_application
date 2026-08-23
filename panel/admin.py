"""Регистрация аудит-лога в стандартной админке (только чтение)."""

from django.contrib import admin

from panel.models import RoleChange


@admin.register(RoleChange)
class RoleChangeAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "group_name", "target")
    list_filter = ("action", "group_name")
    search_fields = ("actor__username", "target__username", "group_name")
    readonly_fields = ("actor", "target", "group", "group_name", "action", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
