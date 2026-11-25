"""Трансляция промежуточного представления в машинный код."""

from pathlib import Path

from isa import Instruction, encode


def assemble(program: list[Instruction]) -> bytes:
    """Транслирует список команд в двоичный машинный код."""
    return b"".join(encode(instruction) for instruction in program)


def encode_commands(program: list[Instruction]) -> list[bytes]:
    """Возвращает машинный код каждой команды отдельным фрагментом."""
    return [encode(instruction) for instruction in program]


def write_binary(path: Path, data: bytes) -> None:
    """Записывает машинный код в файл, создавая каталоги."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
