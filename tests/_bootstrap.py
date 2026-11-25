"""Добавляет каталоги проекта в путь импорта для автотестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src"


def add_import_path(path: Path) -> None:
    """Добавляет каталог в sys.path, если его там ещё нет."""
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


add_import_path(SOURCE_DIR)
add_import_path(ROOT)
