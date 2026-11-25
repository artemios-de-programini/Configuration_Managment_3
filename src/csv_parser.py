"""Разбор исходной программы УВМ из CSV-файла."""

import csv
from pathlib import Path

from isa import BY_MNEMONIC, AssemblyError, Instruction

HEADER_FIRST_CELLS = frozenset({"command", "cmd", "команда"})
HEADER_COLUMNS = ("command", "b", "c", "d", "e")
COLUMN_NAMES = ("B", "C", "D", "E")
COMMENT_PREFIX = "#"
HEX_PREFIXES = ("0x", "0o", "0b")


def parse_program(text: str) -> list[Instruction]:
    """Переводит текст CSV-программы в список команд."""
    instructions: list[Instruction] = []
    first_row = True
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        cells = _split_cells(line, line_no)
        if first_row:
            first_row = False
            if cells[0].lower() in HEADER_FIRST_CELLS:
                _check_header(cells, line_no)
                continue
        instructions.append(_parse_row(cells, line_no))
    return instructions


def load_program(path: Path) -> list[Instruction]:
    """Читает CSV-файл программы и возвращает список команд."""
    return parse_program(path.read_text(encoding="utf-8-sig"))


def _split_cells(line: str, line_no: int) -> list[str]:
    """Разбивает строку CSV на ячейки и убирает пробелы по краям."""
    try:
        row = next(csv.reader([line]))
    except csv.Error as error:
        raise AssemblyError(
            f"Строка {line_no}: ошибка CSV: {error}"
        ) from error
    return [cell.strip() for cell in row]


def _check_header(cells: list[str], line_no: int) -> None:
    """Проверяет, что заголовок CSV описывает ожидаемые столбцы."""
    expected = ",".join(HEADER_COLUMNS)
    names = [cell.lower() for cell in cells]
    prefix = list(HEADER_COLUMNS[: len(names)])
    if len(names) > len(HEADER_COLUMNS) or names != prefix:
        raise AssemblyError(
            f"Строка {line_no}: неверный заголовок CSV, "
            f"ожидается '{expected}'"
        )


def _parse_row(cells: list[str], line_no: int) -> Instruction:
    """Разбирает одну строку программы в команду."""
    mnemonic = cells[0].lower()
    opcode = BY_MNEMONIC.get(mnemonic)
    if opcode is None:
        raise _unknown_command(cells[0], line_no)
    values = _take_values(cells, opcode, mnemonic, line_no)
    operands = _parse_operands(values, opcode, mnemonic, line_no)
    return Instruction(opcode, operands)


def _unknown_command(text: str, line_no: int) -> AssemblyError:
    """Создаёт ошибку о неизвестной мнемонике."""
    allowed = ", ".join(sorted(BY_MNEMONIC))
    return AssemblyError(
        f"Строка {line_no}: неизвестная команда '{text}'; "
        f"допустимы: {allowed}"
    )


def _take_values(cells: list[str], opcode, mnemonic: str, line_no: int):
    """Отбрасывает пустые лишние столбцы и проверяет заполненные."""
    values = cells[1:]
    if len(values) > len(opcode.operands):
        _reject_extra(values, opcode, mnemonic, line_no)
        values = values[: len(opcode.operands)]
    return values


def _reject_extra(values, opcode, mnemonic: str, line_no: int) -> None:
    """Запрещает значения в полях, которых у команды нет."""
    first_extra = len(opcode.operands)
    for index in range(first_extra, len(values)):
        if values[index]:
            column = COLUMN_NAMES[index]
            raise AssemblyError(
                f"Строка {line_no}: у команды {mnemonic} нет поля "
                f"{column}, а значение '{values[index]}' задано"
            )


def _parse_operands(values, opcode, mnemonic: str, line_no: int):
    """Разбирает и проверяет значения всех полей команды."""
    operands = []
    for index, operand in enumerate(opcode.operands):
        cell = values[index] if index < len(values) else ""
        operands.append(_parse_operand(cell, operand, mnemonic, line_no))
    return operands


def _parse_operand(cell: str, operand, mnemonic: str, line_no: int) -> int:
    """Разбирает значение одного поля команды."""
    if not cell:
        raise AssemblyError(
            f"Строка {line_no}: у команды {mnemonic} не заполнено "
            f"поле {operand.name} ({operand.purpose})"
        )
    value = _parse_int(cell, line_no, operand.name)
    if not operand.fits(value):
        raise AssemblyError(
            f"Строка {line_no}: {operand.name}={value} вне диапазона "
            f"{operand.limit_text} ({operand.purpose})"
        )
    return value


def _parse_int(cell: str, line_no: int, field: str) -> int:
    """Разбирает целое число в десятичной или шестнадцатеричной записи."""
    try:
        if cell.lower().startswith(HEX_PREFIXES):
            return int(cell, 0)
        return int(cell, 10)
    except ValueError as error:
        raise AssemblyError(
            f"Строка {line_no}: значение поля {field} '{cell}' "
            f"не является целым числом"
        ) from error
