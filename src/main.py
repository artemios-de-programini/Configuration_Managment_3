"""CLI-ассемблер УВМ (вариант №8): CSV -> машинный код."""

import argparse
import sys
from pathlib import Path

from assembler import encode_commands, write_binary
from constants import FAILURE_CODE, SUCCESS_CODE
from csv_parser import load_program
from isa import AssemblyError, format_bytes


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
        help="файл машинного кода (little-endian)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="режим тестирования: печать байтов команд",
    )
    return parser


def _print_chunks(chunks: list[bytes]) -> None:
    """Печатает байты команд в формате спецификации."""
    for chunk in chunks:
        print(format_bytes(chunk))


def main(argv: list[str] | None = None) -> int:
    """Точка входа ассемблера; возвращает код возврата процесса."""
    args = build_parser().parse_args(argv)
    try:
        program = load_program(args.source)
        chunks = encode_commands(program)
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
        _print_chunks(chunks)

    machine_code = b"".join(chunks)
    try:
        write_binary(args.output, machine_code)
    except OSError as error:
        print(
            f"Ошибка: не удалось записать '{args.output}': {error}",
            file=sys.stderr,
        )
        return FAILURE_CODE

    print(
        f"Ассемблировано команд: {len(program)} -> "
        f"{args.output} ({len(machine_code)} байт)"
    )
    return SUCCESS_CODE


if __name__ == "__main__":
    raise SystemExit(main())
