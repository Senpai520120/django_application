"""Корневой URLconf проекта."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("accounts.urls")),
    path("manage/", include("panel.urls")),
    path("files/", include("files.urls")),
    # Стандартная админка Django — оставлена как референс, задача решается
    # кастомной панелью на /manage/.
    path("admin/", admin.site.urls),
]
