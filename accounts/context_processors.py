from accounts.permissions import is_admin


def panel_access(request):
    """Показывать ли в шапке ссылку на панель."""
    return {"is_panel_admin": is_admin(request.user)}
