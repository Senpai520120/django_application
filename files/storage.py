"""Единый интерфейс хранения для файлового менеджера.

Вьюхи работают только с этим интерфейсом и не знают, где лежат файлы.
Реализации строятся поверх штатного `django.core.files.storage`: локально —
`FileSystemStorage`, в проде — `S3Boto3Storage` из django-storages. Добавить
третий backend — значит написать ещё один подкласс и вернуть его из
`get_storage()`; шаблоны и вьюхи при этом не меняются.
"""

from __future__ import annotations

import posixpath
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from django.utils import timezone

from files.paths import normalize_path

#: Пустая папка в S3 — объект нулевого размера с ключом, оканчивающимся на «/».
S3_DIR_MARKER_SUFFIX = "/"

#: Сколько ключей S3 удаляет за один запрос delete_objects.
S3_DELETE_BATCH = 1000


@dataclass(frozen=True)
class Entry:
    """Строка списка: файл или папка."""

    name: str
    path: str
    is_dir: bool
    size: int | None = None
    modified: datetime | None = None

    @property
    def sort_key(self) -> tuple[bool, str]:
        return (not self.is_dir, self.name.lower())


class StorageError(Exception):
    """Ошибка, которую можно показать пользователю."""


class FileManagerStorage(ABC):
    """Контракт хранилища. Обе реализации обязаны вести себя одинаково."""

    @abstractmethod
    def list_dir(self, path: str = "") -> list[Entry]:
        """Содержимое папки, отсортированное: сначала папки, потом файлы."""

    @abstractmethod
    def make_dir(self, path: str) -> None:
        """Создать папку. Если она уже есть — StorageError."""

    @abstractmethod
    def save(self, path: str, file) -> str:
        """Записать файл. Если такой уже есть — StorageError."""

    @abstractmethod
    def open(self, path: str):
        """Открыть файл на чтение."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Удалить файл или папку (папку — рекурсивно)."""

    @abstractmethod
    def rename(self, path: str, new_name: str) -> str:
        """Переименовать файл или папку внутри той же родительской папки."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Есть ли по этому пути файл или папка."""

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        """Папка ли это."""

    @abstractmethod
    def size(self, path: str) -> int:
        """Размер файла в байтах."""

    @abstractmethod
    def total_size(self) -> int:
        """Суммарный объём хранилища — для лимита на общий размер."""


class LocalFileStorage(FileManagerStorage):
    """Файлы физически лежат на диске сервера."""

    def __init__(self, location: str | Path):
        self._root = Path(location).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._storage = FileSystemStorage(location=str(self._root))

    def _absolute(self, path: str) -> Path:
        """Абсолютный путь с проверкой, что он не вышел за корень.

        `normalize_path` отбивает `..` лексически, но остаётся симлинк, который
        уводит наружу уже после разрешения пути — поэтому проверяем результат.
        """
        relative = normalize_path(path)
        target = (self._root / relative).resolve()
        if target != self._root and self._root not in target.parents:
            raise SuspiciousFileOperation("Путь выходит за пределы хранилища.")
        return target

    def list_dir(self, path: str = "") -> list[Entry]:
        base = self._absolute(path)
        if not base.is_dir():
            raise StorageError("Папка не найдена.")

        relative = normalize_path(path)
        entries = []
        for child in base.iterdir():
            stat = child.stat()
            is_dir = child.is_dir()
            entries.append(
                Entry(
                    name=child.name,
                    path=(
                        posixpath.join(relative, child.name) if relative else child.name
                    ),
                    is_dir=is_dir,
                    size=None if is_dir else stat.st_size,
                    modified=(
                        timezone.make_aware(
                            datetime.fromtimestamp(stat.st_mtime),
                            timezone.get_default_timezone(),
                        )
                        if settings.USE_TZ
                        else datetime.fromtimestamp(stat.st_mtime)
                    ),
                )
            )
        return sorted(entries, key=lambda entry: entry.sort_key)

    def make_dir(self, path: str) -> None:
        target = self._absolute(path)
        if target.exists():
            raise StorageError("Папка или файл с таким именем уже существует.")
        target.mkdir(parents=True)

    def save(self, path: str, file) -> str:
        relative = normalize_path(path)
        if self.exists(relative):
            raise StorageError("Файл с таким именем уже существует.")
        return self._storage.save(relative, file)

    def open(self, path: str):
        target = self._absolute(path)
        if not target.is_file():
            raise StorageError("Файл не найден.")
        return self._storage.open(normalize_path(path), "rb")

    def delete(self, path: str) -> None:
        relative = normalize_path(path)
        if not relative:
            raise StorageError("Корневую папку удалить нельзя.")

        target = self._absolute(relative)
        if not target.exists():
            raise StorageError("Файл или папка не найдены.")

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    def rename(self, path: str, new_name: str) -> str:
        from files.paths import clean_name, parent_path

        relative = normalize_path(path)
        if not relative:
            raise StorageError("Корневую папку переименовать нельзя.")

        source = self._absolute(relative)
        if not source.exists():
            raise StorageError("Файл или папка не найдены.")

        parent = parent_path(relative)
        new_relative = (
            posixpath.join(parent, clean_name(new_name))
            if parent
            else clean_name(new_name)
        )
        destination = self._absolute(new_relative)
        if destination.exists():
            raise StorageError("Файл или папка с таким именем уже существует.")

        source.rename(destination)
        return new_relative

    def exists(self, path: str) -> bool:
        return self._absolute(path).exists()

    def is_dir(self, path: str) -> bool:
        return self._absolute(path).is_dir()

    def size(self, path: str) -> int:
        target = self._absolute(path)
        if not target.is_file():
            raise StorageError("Файл не найден.")
        return target.stat().st_size

    def total_size(self) -> int:
        return sum(f.stat().st_size for f in self._root.rglob("*") if f.is_file())


class S3FileStorage(FileManagerStorage):
    """Файлы лежат в S3. Папки виртуальные: это префиксы ключей."""

    def __init__(self, location: str = ""):
        from storages.backends.s3 import S3Storage

        self._location = location.strip("/")
        self._storage = S3Storage(location=self._location)

    @property
    def _bucket(self) -> str:
        return self._storage.bucket_name

    @property
    def _client(self):
        return self._storage.connection.meta.client

    def _key(self, path: str) -> str:
        """Полный ключ объекта: префикс хранилища плюс относительный путь."""
        relative = normalize_path(path)
        if self._location and relative:
            return f"{self._location}/{relative}"
        return self._location or relative

    def _dir_prefix(self, path: str) -> str:
        key = self._key(path)
        return f"{key}{S3_DIR_MARKER_SUFFIX}" if key else ""

    def _iter_keys(self, prefix: str):
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            yield from page.get("Contents", ())

    def list_dir(self, path: str = "") -> list[Entry]:
        prefix = self._dir_prefix(path)
        relative = normalize_path(path)

        if relative and not self.is_dir(relative):
            raise StorageError("Папка не найдена.")

        entries: list[Entry] = []
        paginator = self._client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self._bucket, Prefix=prefix, Delimiter="/")

        for page in pages:
            for common in page.get("CommonPrefixes", ()):
                name = common["Prefix"][len(prefix) :].rstrip("/")
                if not name:
                    continue
                entries.append(
                    Entry(
                        name=name,
                        path=posixpath.join(relative, name) if relative else name,
                        is_dir=True,
                    )
                )
            for obj in page.get("Contents", ()):
                name = obj["Key"][len(prefix) :]
                if not name:  # маркер самой папки
                    continue
                entries.append(
                    Entry(
                        name=name,
                        path=posixpath.join(relative, name) if relative else name,
                        is_dir=False,
                        size=obj["Size"],
                        modified=obj["LastModified"],
                    )
                )

        return sorted(entries, key=lambda entry: entry.sort_key)

    def make_dir(self, path: str) -> None:
        relative = normalize_path(path)
        if not relative:
            raise StorageError("Пустое имя папки.")
        if self.exists(relative):
            raise StorageError("Папка или файл с таким именем уже существует.")
        self._client.put_object(
            Bucket=self._bucket, Key=self._dir_prefix(relative), Body=b""
        )

    def save(self, path: str, file) -> str:
        relative = normalize_path(path)
        if self.exists(relative):
            raise StorageError("Файл с таким именем уже существует.")
        return self._storage.save(relative, file)

    def open(self, path: str):
        relative = normalize_path(path)
        if not self._file_exists(relative):
            raise StorageError("Файл не найден.")
        return self._storage.open(relative, "rb")

    def delete(self, path: str) -> None:
        relative = normalize_path(path)
        if not relative:
            raise StorageError("Корневую папку удалить нельзя.")

        if self._file_exists(relative):
            self._storage.delete(relative)
            return

        if not self.is_dir(relative):
            raise StorageError("Файл или папка не найдены.")

        self._delete_prefix(self._dir_prefix(relative))

    def _delete_prefix(self, prefix: str) -> None:
        batch: list[dict[str, str]] = []
        for obj in self._iter_keys(prefix):
            batch.append({"Key": obj["Key"]})
            if len(batch) == S3_DELETE_BATCH:
                self._client.delete_objects(
                    Bucket=self._bucket, Delete={"Objects": batch}
                )
                batch = []
        if batch:
            self._client.delete_objects(Bucket=self._bucket, Delete={"Objects": batch})

    def rename(self, path: str, new_name: str) -> str:
        from files.paths import clean_name, parent_path

        relative = normalize_path(path)
        if not relative:
            raise StorageError("Корневую папку переименовать нельзя.")

        parent = parent_path(relative)
        cleaned = clean_name(new_name)
        new_relative = posixpath.join(parent, cleaned) if parent else cleaned

        if self.exists(new_relative):
            raise StorageError("Файл или папка с таким именем уже существует.")

        if self._file_exists(relative):
            self._copy(self._key(relative), self._key(new_relative))
            self._storage.delete(relative)
            return new_relative

        if not self.is_dir(relative):
            raise StorageError("Файл или папка не найдены.")

        old_prefix = self._dir_prefix(relative)
        new_prefix = self._dir_prefix(new_relative)
        keys = [obj["Key"] for obj in self._iter_keys(old_prefix)]
        for key in keys:
            self._copy(key, f"{new_prefix}{key[len(old_prefix):]}")
        self._delete_prefix(old_prefix)
        return new_relative

    def _copy(self, source_key: str, target_key: str) -> None:
        self._client.copy_object(
            Bucket=self._bucket,
            CopySource={"Bucket": self._bucket, "Key": source_key},
            Key=target_key,
        )

    def _file_exists(self, path: str) -> bool:
        relative = normalize_path(path)
        return bool(relative) and self._storage.exists(relative)

    def exists(self, path: str) -> bool:
        relative = normalize_path(path)
        if not relative:
            return True
        return self._file_exists(relative) or self.is_dir(relative)

    def is_dir(self, path: str) -> bool:
        relative = normalize_path(path)
        if not relative:
            return True
        response = self._client.list_objects_v2(
            Bucket=self._bucket, Prefix=self._dir_prefix(relative), MaxKeys=1
        )
        return response.get("KeyCount", 0) > 0

    def size(self, path: str) -> int:
        relative = normalize_path(path)
        if not self._file_exists(relative):
            raise StorageError("Файл не найден.")
        return self._storage.size(relative)

    def total_size(self) -> int:
        prefix = f"{self._location}/" if self._location else ""
        return sum(obj["Size"] for obj in self._iter_keys(prefix))


def get_storage() -> FileManagerStorage:
    """Хранилище, выбранное настройками. Единственная точка выбора backend'а."""
    backend = settings.FILE_MANAGER["BACKEND"]

    if backend == "local":
        return LocalFileStorage(settings.FILE_MANAGER["ROOT"])
    if backend == "s3":
        return S3FileStorage(location=settings.FILE_MANAGER["S3_LOCATION"])

    raise ImproperlyConfigured(
        f"Неизвестный backend файлового менеджера: {backend!r}. "
        "Допустимые значения FILE_STORAGE_BACKEND: local, s3."
    )
