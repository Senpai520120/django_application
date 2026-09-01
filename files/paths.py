"""Нормализация путей и имён файлового менеджера.

Единственное место, где решается, что пользователь имеет право адресовать.
Всё, что уводит за пределы корня хранилища, отбивается здесь, а не во вьюхах.
"""

import posixpath
import re

from django.core.exceptions import SuspiciousFileOperation

MAX_NAME_LENGTH = 120

# Разделители, управляющие символы и то, что ломает Windows-пути.
_FORBIDDEN_IN_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_DRIVE_LETTER = re.compile(r"^[a-zA-Z]:")


def clean_name(name: str) -> str:
    """Имя одного файла или папки, пригодное для записи в хранилище.

    Отбивает разделители пути, управляющие символы, точки в начале и хвосте,
    зарезервированные windows-имена и слишком длинные имена.
    """
    if not isinstance(name, str):
        raise SuspiciousFileOperation("Имя должно быть строкой.")

    # Null-байт не вырезаем, а отбиваем: иначе file\x00.exe станет file.exe.
    if "\x00" in name:
        raise SuspiciousFileOperation("Имя содержит null-байт.")

    name = name.strip()
    if not name:
        raise SuspiciousFileOperation("Пустое имя.")

    if _FORBIDDEN_IN_NAME.search(name):
        raise SuspiciousFileOperation("Имя содержит недопустимые символы.")

    # ".", ".." и скрытые точки в начале: путь наружу либо невидимый мусор.
    if name.strip(".") == "":
        raise SuspiciousFileOperation("Недопустимое имя.")

    name = name.strip(". ")
    if not name:
        raise SuspiciousFileOperation("Недопустимое имя.")

    stem = name.split(".", 1)[0].upper()
    if stem in _WINDOWS_RESERVED:
        raise SuspiciousFileOperation(f"Имя «{name}» зарезервировано системой.")

    if len(name) > MAX_NAME_LENGTH:
        raise SuspiciousFileOperation(f"Имя длиннее {MAX_NAME_LENGTH} символов.")

    return name


def normalize_path(path: str | None) -> str:
    """Относительный путь внутри корня хранилища.

    Возвращает путь в posix-виде без ведущего слэша: "", "docs", "docs/2024".
    Абсолютные пути, диски, `..` и null-байты считаются атакой.
    """
    if not path:
        return ""

    if not isinstance(path, str):
        raise SuspiciousFileOperation("Путь должен быть строкой.")

    if "\x00" in path:
        raise SuspiciousFileOperation("Путь содержит null-байт.")

    # Пользователь мог прийти из windows-клиента: приводим к одному виду.
    path = path.replace("\\", "/").strip()

    if path.startswith("/") or _DRIVE_LETTER.match(path):
        raise SuspiciousFileOperation("Абсолютные пути запрещены.")

    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise SuspiciousFileOperation("Выход за пределы корня запрещён.")
        parts.append(part)

    normalized = posixpath.normpath("/".join(parts)) if parts else ""
    if normalized in (".", "/"):
        return ""

    # normpath не должен был ничего «раскрутить», но проверяем результат тоже.
    if normalized.startswith(("..", "/")):
        raise SuspiciousFileOperation("Выход за пределы корня запрещён.")

    return normalized


def join_path(path: str, name: str) -> str:
    """Путь до вложенного элемента: сначала чистим имя, потом склеиваем."""
    parent = normalize_path(path)
    child = clean_name(name)
    return posixpath.join(parent, child) if parent else child


def parent_path(path: str) -> str:
    """Родительская папка для пути. Для корня — снова корень."""
    normalized = normalize_path(path)
    if not normalized:
        return ""
    return posixpath.dirname(normalized)


def breadcrumbs(path: str) -> list[tuple[str, str]]:
    """Пары «имя папки, путь до неё» для навигации от корня до текущей папки."""
    normalized = normalize_path(path)
    if not normalized:
        return []

    crumbs: list[tuple[str, str]] = []
    walked = ""
    for part in normalized.split("/"):
        walked = posixpath.join(walked, part) if walked else part
        crumbs.append((part, walked))
    return crumbs
