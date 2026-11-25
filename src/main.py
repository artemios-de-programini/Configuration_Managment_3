"""CLI-ассемблер УВМ (вариант №8): разбор программы и вывод результата."""

import argparse
import sys
from pathlib import Path

from constants import FAILURE_CODE, SUCCESS_CODE
from csv_parser import load_program
from isa import AssemblyError


def build_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик аргументов командной строки ассемблера."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Ассемблер УВМ (вариант №8): CSV -> машинный код.",
    )
    parser.add_argument(
        "source",
        type=Path,
        help="исходная программа в формате CSV",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="файл машинного кода (создаётся на этапе 2)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="режим тестирования: печать представления программы",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Точка входа ассемблера; возвращает код возврата процесса."""
    args = build_parser().parse_args(argv)
    try:
        program = load_program(args.source)
    except OSError as error:
        print(
            f"Ошибка: не удалось прочитать '{args.source}': {error}",
            file=sys.stderr,
        )
        return FAILURE_CODE
    except AssemblyError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return FAILURE_CODE

    if args.test:
        for instruction in program:
            print(instruction.fields_text())

    print(f"Разобрано команд: {len(program)}")
    return SUCCESS_CODE


if __name__ == "__main__":
    raise SystemExit(main())
