"""Общие помощники автотестов проекта."""

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from _bootstrap import ROOT
from assembler import assemble
from csv_parser import load_program
from interpreter import run
from machine import Machine

TESTS = ROOT / "tests"


def assemble_file(path: Path) -> bytes:
    """Ассемблирует CSV-файл и возвращает машинный код."""
    return assemble(load_program(path))


def run_file(path: Path) -> Machine:
    """Ассемблирует и выполняет программу из CSV-файла."""
    return run(assemble_file(path))


def cells(machine: Machine, start: int, end: int) -> list[int]:
    """Возвращает значения памяти данных в диапазоне start..end."""
    return machine.data_memory[start:end + 1]


@contextmanager
def output_path(suffix: str = ".bin") -> Iterator[Path]:
    """Временный путь для выходного файла, удаляемый после теста."""
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory) / f"program{suffix}"
