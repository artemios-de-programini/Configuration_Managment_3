"""CLI-интерпретатор УВМ: выполнение кода и XML-дамп памяти."""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from constants import (
    ADDRESS_MAX,
    FAILURE_CODE,
    MEMORY_SIZE,
    MIN_VALUE,
    ONE,
    RANGE_PARTS,
    SUCCESS_CODE,
)
from isa import MachineError
from machine import Machine

RANGE_SEPARATOR = ":"
XML_ENCODING = "utf-8"
XML_INDENT = "  "
DECIMAL_BASE = 10
AUTO_BASE = 0
HEX_PREFIX = "0x"


def run(code: bytes, data_size: int = MEMORY_SIZE) -> Machine:
    """Загружает машинный код и выполняет программу до конца."""
    machine = Machine(code, data_size)
    while machine.step():
        pass
    return machine


def _parse_number(part: str, text: str) -> int:
    """Преобразует часть диапазона адресов в целое число."""
    base = DECIMAL_BASE
    if part.lower().startswith(HEX_PREFIX):
        base = AUTO_BASE
    try:
        return int(part, base)
    except ValueError as error:
        raise ValueError(_range_error(text)) from error


def _range_error(text: str) -> str:
    """Возвращает текст ошибки о неверном формате диапазона."""
    return f"неверный формат диапазона '{text}', ожидается start:end"


def parse_range(text: str) -> tuple[int, int]:
    """Разбирает диапазон адресов памяти данных вида start:end."""
    parts = text.strip().split(RANGE_SEPARATOR)
    if len(parts) != RANGE_PARTS or not all(parts):
        raise ValueError(_range_error(text))
    start = _parse_number(parts[0], text)
    end = _parse_number(parts[1], text)
    if start < MIN_VALUE or end > ADDRESS_MAX or start > end:
        raise ValueError(
            f"диапазон {start}:{end} вне памяти данных "
            f"({MIN_VALUE}..{ADDRESS_MAX}, start <= end)"
        )
    return start, end


def dump_memory(
    machine: Machine, start: int, end: int, path: Path
) -> None:
    """Сохраняет диапазон памяти данных в XML-файл."""
    attributes = {"start": str(start), "end": str(end)}
    root = ET.Element("memory_dump", attributes)
    root.set("instructions", str(machine.executed))
    for address in range(start, end + ONE):
        cell = ET.SubElement(root, "cell", {"address": str(address)})
        cell.text = str(machine.data_memory[address])
    ET.indent(root, space=XML_INDENT)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(path, encoding=XML_ENCODING, xml_declaration=True)


def _write_dump(
    machine: Machine, start: int, end: int, path: Path
) -> bool:
    """Пишет XML-дамп и сообщает об ошибке записи."""
    try:
        dump_memory(machine, start, end, path)
    except OSError as error:
        print(
            f"Ошибка: не удалось записать '{path}': {error}",
            file=sys.stderr,
        )
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик аргументов командной строки интерпретатора."""
    parser = argparse.ArgumentParser(
        prog="interpreter.py",
        description="Интерпретатор УВМ (вариант №8): код -> XML-дамп.",
    )
    parser.add_argument(
        "binary",
        type=Path,
        help="файл с машинным кодом программы",
    )
    parser.add_argument(
        "dump",
        type=Path,
        help="путь к XML-файлу дампа памяти",
    )
    parser.add_argument(
        "memory_range",
        metavar="start:end",
        help="диапазон адресов памяти данных для дампа",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Точка входа интерпретатора; возвращает код возврата процесса."""
    args = build_parser().parse_args(argv)
    try:
        start, end = parse_range(args.memory_range)
        code = args.binary.read_bytes()
        machine = run(code)
    except OSError as error:
        print(
            f"Ошибка: не удалось прочитать '{args.binary}': {error}",
            file=sys.stderr,
        )
        return FAILURE_CODE
    except (MachineError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return FAILURE_CODE

    if not _write_dump(machine, start, end, args.dump):
        return FAILURE_CODE

    print(f"Выполнено команд: {machine.executed}")
    print(f"Дамп памяти [{start}:{end}] сохранён в {args.dump}")
    return SUCCESS_CODE


if __name__ == "__main__":
    raise SystemExit(main())
