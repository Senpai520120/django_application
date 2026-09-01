"""Формы файлового менеджера.

Имена приходят от пользователя, поэтому каждая форма прогоняет их через
`files.paths` — единственное место, где решается, что допустимо.
"""

from django import forms
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from files.paths import MAX_NAME_LENGTH, clean_name, normalize_path


class PathField(forms.CharField):
    """Скрытое поле с путём до папки или файла."""

    widget = forms.HiddenInput

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def clean(self, value):
        value = super().clean(value)
        try:
            return normalize_path(value)
        except SuspiciousFileOperation as error:
            raise forms.ValidationError(str(error)) from error


class NameField(forms.CharField):
    """Имя файла или папки, уже проверенное на запрещённые символы."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", MAX_NAME_LENGTH)
        kwargs.setdefault("strip", True)
        super().__init__(**kwargs)

    def clean(self, value):
        value = super().clean(value)
        try:
            return clean_name(value)
        except SuspiciousFileOperation as error:
            raise forms.ValidationError(str(error)) from error


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Несколько файлов одним полем — по рецепту из документации Django."""

    def __init__(self, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(**kwargs)

    def clean(self, data, initial=None):
        clean_single = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_single(item, initial) for item in data]
        return [clean_single(data, initial)]


class FolderForm(forms.Form):
    path = PathField()
    name = NameField(label=_("Имя папки"))


class RenameForm(forms.Form):
    path = PathField(required=True)
    new_name = NameField(label=_("Новое имя"))


class UploadForm(forms.Form):
    path = PathField()
    files = MultipleFileField(label=_("Файлы"))

    def clean_files(self):
        uploaded = self.cleaned_data["files"]
        limit = settings.FILE_MANAGER["MAX_FILE_SIZE"]

        for item in uploaded:
            if item.size > limit:
                raise forms.ValidationError(
                    _("Файл «%(name)s» больше допустимых %(limit)s.")
                    % {"name": item.name, "limit": filesizeformat(limit)}
                )
            # Имя приходит из браузера: оно может содержать путь целиком.
            try:
                clean_name(item.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
            except SuspiciousFileOperation as error:
                raise forms.ValidationError(
                    _("Файл «%(name)s»: %(error)s")
                    % {"name": item.name, "error": error}
                ) from error

        return uploaded
