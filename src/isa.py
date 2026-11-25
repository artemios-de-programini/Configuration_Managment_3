"""Система команд УВМ (вариант №8): поля, команды, промежуточное звено."""

from dataclasses import dataclass

from constants import (
    ADDRESS_MAX,
    CONSTANT_MAX,
    MIN_VALUE,
    OFFSET_MAX,
    ONE,
)

OPCODE_FIELD = "A"


class VmError(Exception):
    """Базовая ошибка ассемблера и интерпретатора УВМ."""


class AssemblyError(VmError):
    """Ошибка исходной программы или её трансляции."""


class MachineError(VmError):
    """Ошибка выполнения машинного кода."""


@dataclass(frozen=True, slots=True)
class Operand:
    """Поле команды: имя, позиция, разрядность и назначение."""

    name: str
    bit: int
    width: int
    max_value: int
    purpose: str

    @property
    def mask(self) -> int:
        """Маска поля для выделения значения из машинного слова."""
        return (ONE << self.width) - ONE

    @property
    def limit_text(self) -> str:
        """Человекочитаемый диапазон значений поля."""
        return f"{MIN_VALUE}..{self.max_value}"

    def fits(self, value: int) -> bool:
        """Проверяет, что значение помещается в поле без потери битов."""
        if value < MIN_VALUE:
            return False
        return value <= self.max_value


@dataclass(frozen=True, slots=True)
class Opcode:
    """Описание одной команды УВМ."""

    mnemonic: str
    code: int
    size: int
    operands: tuple[Operand, ...]
    action: str

    @property
    def names(self) -> tuple[str, ...]:
        """Имена полей команды в порядке их расположения в слове."""
        return tuple(operand.name for operand in self.operands)


LOAD = Opcode(
    mnemonic="load",
    code=0,
    size=4,
    operands=(
        Operand("B", 4, 14, ADDRESS_MAX, "адрес назначения"),
        Operand("C", 18, 13, CONSTANT_MAX, "константа"),
    ),
    action="data_mem[B] = C",
)

READ = Opcode(
    mnemonic="read",
    code=1,
    size=5,
    operands=(
        Operand("B", 4, 14, ADDRESS_MAX, "адрес базового указателя"),
        Operand("C", 18, 14, ADDRESS_MAX, "адрес результата"),
        Operand("D", 32, 8, OFFSET_MAX, "смещение"),
    ),
    action="data_mem[C] = data_mem[data_mem[B] + D]",
)

WRITE = Opcode(
    mnemonic="write",
    code=9,
    size=5,
    operands=(
        Operand("B", 4, 14, ADDRESS_MAX, "адрес источника"),
        Operand("C", 18, 14, ADDRESS_MAX, "адрес базового указателя"),
        Operand("D", 32, 8, OFFSET_MAX, "смещение"),
    ),
    action="data_mem[data_mem[C] + D] = data_mem[B]",
)

EQ = Opcode(
    mnemonic="eq",
    code=3,
    size=7,
    operands=(
        Operand("B", 4, 8, OFFSET_MAX, "смещение"),
        Operand("C", 12, 14, ADDRESS_MAX, "адрес второго операнда"),
        Operand("D", 26, 14, ADDRESS_MAX, "адрес результата"),
        Operand("E", 40, 14, ADDRESS_MAX, "адрес базового указателя"),
    ),
    action=(
        "data_mem[D] = 1 if data_mem[data_mem[E] + B]"
        " == data_mem[C] else 0"
    ),
)

OPCODES = (LOAD, READ, WRITE, EQ)
BY_CODE = {opcode.code: opcode for opcode in OPCODES}
BY_MNEMONIC = {opcode.mnemonic: opcode for opcode in OPCODES}


@dataclass(frozen=True, slots=True)
class Instruction:
    """Команда в промежуточном представлении."""

    opcode: Opcode
    values: tuple[int, ...]

    def __post_init__(self) -> None:
        """Проверяет, что число значений совпадает с числом полей."""
        expected = len(self.opcode.operands)
        if len(self.values) != expected:
            raise ValueError(
                f"у команды {self.opcode.mnemonic} полей "
                f"{expected}, а передано {len(self.values)}"
            )

    @property
    def code(self) -> int:
        """Код операции A."""
        return self.opcode.code

    @property
    def size(self) -> int:
        """Длина команды в байтах."""
        return self.opcode.size

    def field(self, name: str) -> int:
        """Возвращает значение поля по его имени."""
        if name == OPCODE_FIELD:
            return self.code
        try:
            index = self.opcode.names.index(name)
        except ValueError as error:
            raise KeyError(
                f"у команды {self.opcode.mnemonic} нет поля {name}"
            ) from error
        return self.values[index]

    def fields_text(self) -> str:
        """Представление команды в виде ``A=0, B=956, C=568``."""
        parts = [f"{OPCODE_FIELD}={self.code}"]
        parts.extend(
            f"{operand.name}={value}"
            for operand, value in zip(self.opcode.operands, self.values)
        )
        return ", ".join(parts)


def make(mnemonic: str, *values: int) -> Instruction:
    """Создаёт команду по мнемонике и значениям полей."""
    opcode = BY_MNEMONIC.get(mnemonic)
    if opcode is None:
        raise AssemblyError(
            f"неизвестная команда '{mnemonic}'; "
            f"допустимы: {', '.join(sorted(BY_MNEMONIC))}"
        )
    return Instruction(opcode, tuple(values))
