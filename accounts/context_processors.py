"""Контекст-процессоры приложения accounts."""

from accounts.permissions import is_admin


def panel_access(request):
    """Флаг `is_panel_admin` для шаблонов (показывать ли ссылку на панель)."""
    return {"is_panel_admin": is_admin(request.user)}
