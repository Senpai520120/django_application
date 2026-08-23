#!/usr/bin/env python
"""Утилита командной строки Django."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover - защита от кривого окружения
        raise ImportError(
            "Не удалось импортировать Django. Он установлен и доступен в "
            "PYTHONPATH? Возможно, вы забыли активировать виртуальное окружение."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
