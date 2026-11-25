"""Автотесты этапа 4: бинарная операция == (АЛУ)."""

import unittest
import xml.etree.ElementTree as ET

import _util
from interpreter import dump_memory
from isa import decode, encode, make
from machine import Machine


def eq_machine():
    """Возвращает машину с данными для проверки операции ==."""
    machine = Machine(b"")
    machine.execute(make("load", 40, 500))
    machine.execute(make("load", 500, 42))
    machine.execute(make("load", 501, 7))
    machine.execute(make("load", 502, 42))
    machine.execute(make("load", 20, 42))
    machine.execute(make("load", 21, 99))
    return machine


def eq_program_machine():
    """Возвращает машину после теста операции ==."""
    return _util.run_file(_util.TESTS / "eq_test.csv")


class EqEncodingTestCase(unittest.TestCase):
    """Команда == кодируется в 7 байт."""

    def test_size(self):
        """Длина команды равна 7 байтам."""
        self.assertEqual(len(encode(make("eq", 156, 603, 647, 38))), 7)

    def test_control_bytes(self):
        """Байты команды совпадают с контрольным значением."""
        self.assertEqual(
            encode(make("eq", 156, 603, 647, 38)),
            bytes([0xC3, 0xB9, 0x25, 0x1C, 0x0A, 0x26, 0x00]),
        )

    def test_round_trip(self):
        """Команда декодируется обратно."""
        instruction = make("eq", 156, 603, 647, 38)
        self.assertEqual(decode(encode(instruction)), instruction)


class EqExecutionTestCase(unittest.TestCase):
    """Семантика операции ==."""

    def test_equal_values(self):
        """Равные значения дают единицу."""
        machine = eq_machine()
        machine.execute(make("eq", 0, 20, 30, 40))
        self.assertEqual(machine.data_memory[30], 1)

    def test_different_values(self):
        """Разные значения дают ноль."""
        machine = eq_machine()
        machine.execute(make("eq", 1, 21, 31, 40))
        self.assertEqual(machine.data_memory[31], 0)

    def test_offset_two(self):
        """Смещение два читает третий элемент вектора."""
        machine = eq_machine()
        machine.execute(make("eq", 2, 20, 32, 40))
        self.assertEqual(machine.data_memory[32], 1)

    def test_source_is_intact(self):
        """Исходные ячейки не изменяются."""
        machine = eq_machine()
        machine.execute(make("eq", 0, 20, 30, 40))
        self.assertEqual(machine.data_memory[20], 42)


class EqProgramTestCase(unittest.TestCase):
    """Тестовая программа этапа 4."""

    def test_instruction_count(self):
        """Программа состоит из девяти команд."""
        self.assertEqual(eq_program_machine().executed, 9)

    def test_results(self):
        """Результаты сравнения равны 1, 0 и 1."""
        self.assertEqual(
            _util.cells(eq_program_machine(), 30, 32), [1, 0, 1]
        )

    def test_source_values_are_intact(self):
        """Исходные значения первого вектора не изменяются."""
        self.assertEqual(
            _util.cells(eq_program_machine(), 500, 502), [42, 7, 42]
        )

    def test_xml_dump(self):
        """XML-дамп содержит результаты сравнения."""
        machine = eq_program_machine()
        with _util.output_path(".xml") as path:
            dump_memory(machine, 30, 32, path)
            root = ET.parse(path).getroot()
        self.assertEqual(
            [int(cell.text) for cell in root.findall("cell")], [1, 0, 1]
        )
