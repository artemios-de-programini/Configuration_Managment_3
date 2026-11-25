"""Память УВМ и выполнение команд варианта №8."""

from constants import (
    MAX_COMMAND_SIZE,
    MEMORY_SIZE,
    MIN_VALUE,
    ONE,
    ZERO,
)
from isa import (
    LOAD,
    READ,
    WRITE,
    Instruction,
    MachineError,
    decode,
)


class Machine:
    """Состояние учебной виртуальной машины."""

    def __init__(self, code: bytes, data_size: int = MEMORY_SIZE) -> None:
        """Загружает код в память команд и обнуляет память данных."""
        self.code_memory = bytearray(code)
        self.data_memory = [ZERO] * data_size
        self.pc = ZERO
        self.executed = ZERO

    def step(self) -> bool:
        """Выполняет одну команду; возвращает False в конце программы."""
        if self.pc >= len(self.code_memory):
            return False
        end = self.pc + MAX_COMMAND_SIZE
        chunk = bytes(self.code_memory[self.pc:end])
        instruction = decode(chunk)
        self.execute(instruction)
        self.pc += instruction.size
        self.executed += ONE
        return True

    def execute(self, instruction: Instruction) -> None:
        """Выполняет декодированную команду."""
        handler = HANDLERS.get(instruction.code)
        if handler is None:
            raise MachineError(
                f"команда {instruction.opcode.mnemonic} "
                f"(A={instruction.code}) не поддерживается"
            )
        handler(self, instruction)

    def load_cell(self, address: int, purpose: str) -> int:
        """Читает ячейку памяти данных с проверкой адреса."""
        self.check_address(address, purpose)
        return self.data_memory[address]

    def check_address(self, address: int, purpose: str) -> None:
        """Проверяет, что адрес попадает в память данных."""
        limit = len(self.data_memory)
        if address < MIN_VALUE or address >= limit:
            raise MachineError(
                f"{purpose} {address} вне памяти данных "
                f"({MIN_VALUE}..{limit - ONE}, pc={self.pc})"
            )

    def add_offset(self, base: int, offset: int) -> int:
        """Вычисляет адрес base + offset с проверкой результата."""
        address = base + offset
        self.check_address(address, "вычисленный адрес")
        return address


def _execute_load(machine: Machine, instruction: Instruction) -> None:
    """Выполняет загрузку константы в память данных."""
    address, value = instruction.values
    machine.check_address(address, "адрес назначения")
    machine.data_memory[address] = value


def _execute_read(machine: Machine, instruction: Instruction) -> None:
    """Выполняет чтение значения из памяти по базе и смещению."""
    base_cell, result, offset = instruction.values
    machine.check_address(result, "адрес результата")
    base = machine.load_cell(base_cell, "адрес базового указателя")
    source = machine.add_offset(base, offset)
    machine.data_memory[result] = machine.load_cell(
        source, "адрес источника"
    )


def _execute_write(machine: Machine, instruction: Instruction) -> None:
    """Выполняет запись значения в память по базе и смещению."""
    source, base_cell, offset = instruction.values
    base = machine.load_cell(base_cell, "адрес базового указателя")
    target = machine.add_offset(base, offset)
    machine.data_memory[target] = machine.load_cell(
        source, "адрес источника"
    )


HANDLERS = {
    LOAD.code: _execute_load,
    READ.code: _execute_read,
    WRITE.code: _execute_write,
}
