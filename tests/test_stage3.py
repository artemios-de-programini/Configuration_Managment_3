"""Автотесты этапа 3: интерпретатор, память и XML-дамп."""

import io
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr, redirect_stdout

import _util
from constants import MEMORY_SIZE
from interpreter import (
    dump_memory,
    main as interpreter_main,
    parse_range,
    run,
)
from isa import MachineError, make
from machine import Machine
from main import main as assembler_main


def empty_machine():
    """Возвращает машину без машинного кода."""
    return Machine(b"")


def copy_machine():
    """Возвращает машину после копирования массива."""
    return _util.run_file(_util.TESTS / "copy_array.csv")


class MemoryModelTestCase(unittest.TestCase):
    """Память команд и память данных разделены."""

    def test_memories_are_separate(self):
        """Типы и размеры памятей соответствуют модели."""
        machine = Machine(b"\x00\x00\x00\x00")
        self.assertIsInstance(machine.code_memory, bytearray)
        self.assertIsInstance(machine.data_memory, list)
        self.assertEqual(len(machine.data_memory), MEMORY_SIZE)
        self.assertEqual(len(machine.code_memory), 4)

    def test_data_changes_do_not_touch_code(self):
        """Выполнение программы не меняет память команд."""
        code = bytes([0x00, 0x01, 0x02, 0x03])
        machine = run(code)
        self.assertEqual(bytes(machine.code_memory), code)


class ExecuteTestCase(unittest.TestCase):
    """Семантика команд load, read и write."""

    def test_load_const(self):
        """Команда load записывает константу."""
        machine = empty_machine()
        machine.execute(make("load", 100, 42))
        self.assertEqual(machine.data_memory[100], 42)

    def test_read_from_memory(self):
        """Команда read читает по базе и смещению."""
        machine = empty_machine()
        machine.execute(make("load", 0, 100))
        machine.execute(make("load", 107, 9))
        machine.execute(make("read", 0, 50, 7))
        self.assertEqual(machine.data_memory[50], 9)

    def test_write_to_memory(self):
        """Команда write пишет по базе и смещению."""
        machine = empty_machine()
        machine.execute(make("load", 0, 100))
        machine.execute(make("load", 30, 5))
        machine.execute(make("write", 30, 0, 8))
        self.assertEqual(machine.data_memory[108], 5)

    def test_zero_cells_by_default(self):
        """Незаполненные ячейки памяти равны нулю."""
        machine = empty_machine()
        machine.execute(make("load", 0, 200))
        machine.execute(make("read", 0, 51, 0))
        self.assertEqual(machine.data_memory[51], 0)


class CopyArrayTestCase(unittest.TestCase):
    """Тестовая программа копирования массива."""

    def test_instruction_count(self):
        """Программа состоит из 26 команд."""
        self.assertEqual(copy_machine().executed, 26)

    def test_source_array(self):
        """Исходный массив содержит ожидаемые значения."""
        self.assertEqual(
            _util.cells(copy_machine(), 700, 707),
            [11, 22, 33, 44, 55, 66, 77, 88],
        )

    def test_copied_array(self):
        """Скопированный массив совпадает с исходным."""
        machine = copy_machine()
        self.assertEqual(
            _util.cells(machine, 800, 807),
            _util.cells(machine, 700, 707),
        )


class XmlDumpTestCase(unittest.TestCase):
    """XML-дамп диапазона памяти."""

    def test_dump_structure(self):
        """Дамп содержит адреса и значения ячеек."""
        machine = copy_machine()
        with _util.output_path(".xml") as path:
            dump_memory(machine, 800, 807, path)
            root = ET.parse(path).getroot()
        self.assertEqual(root.tag, "memory_dump")
        self.assertEqual(root.get("start"), "800")
        self.assertEqual(root.get("end"), "807")
        self.assertEqual(root.get("instructions"), "26")
        cells = root.findall("cell")
        self.assertEqual(
            [int(cell.get("address")) for cell in cells],
            list(range(800, 808)),
        )
        self.assertEqual(
            [int(cell.text) for cell in cells],
            [11, 22, 33, 44, 55, 66, 77, 88],
        )

    def test_dump_creates_directory(self):
        """Дамп создаёт каталог результата."""
        machine = copy_machine()
        with _util.output_path(".xml") as path:
            nested = path.parent / "deep" / "dump.xml"
            dump_memory(machine, 0, 2, nested)
            self.assertTrue(nested.exists())


class InterpreterCliTestCase(unittest.TestCase):
    """Работа командной строки интерпретатора."""

    def test_run_and_dump(self):
        """Интерпретатор выполняет программу и пишет дамп."""
        with _util.output_path(".xml") as dump_path:
            with _util.output_path() as binary:
                with redirect_stdout(io.StringIO()):
                    assembler_main(
                        [
                            str(_util.TESTS / "copy_array.csv"),
                            str(binary),
                        ]
                    )
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = interpreter_main(
                        [str(binary), str(dump_path), "800:807"]
                    )
                self.assertEqual(code, 0)
                self.assertIn(
                    "Выполнено команд: 26", buffer.getvalue()
                )
            root = ET.parse(dump_path).getroot()
        self.assertEqual(
            [int(cell.text) for cell in root.findall("cell")],
            [11, 22, 33, 44, 55, 66, 77, 88],
        )

    def test_bad_range_returns_error(self):
        """Неверный диапазон завершается кодом 1."""
        with _util.output_path(".xml") as dump_path:
            with _util.output_path() as binary:
                binary.write_bytes(b"\x00\x00\x00\x00")
                buffer = io.StringIO()
                with redirect_stderr(buffer):
                    with redirect_stdout(io.StringIO()):
                        code = interpreter_main(
                            [str(binary), str(dump_path), "abc"]
                        )
        self.assertEqual(code, 1)
        self.assertIn("неверный формат диапазона", buffer.getvalue())


class ParseRangeTestCase(unittest.TestCase):
    """Проверка диапазона адресов из командной строки."""

    def test_valid_range(self):
        """Корректные диапазоны разбираются."""
        self.assertEqual(parse_range("100:105"), (100, 105))
        self.assertEqual(parse_range("0:16383"), (0, 16383))

    def test_invalid_ranges(self):
        """Некорректные диапазоны отклоняются."""
        texts = ("100", "10:5", "-1:5", "0:16384", ":", "1:2:3")
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_range(text)


class MachineErrorTestCase(unittest.TestCase):
    """Ошибки выполнения машинного кода."""

    def test_unknown_opcode(self):
        """Неизвестный код операции отклоняется."""
        machine = Machine(bytes([0x02]))
        with self.assertRaises(MachineError) as context:
            machine.step()
        self.assertIn("неизвестный код операции", str(context.exception))

    def test_truncated_command(self):
        """Оборванная команда отклоняется."""
        machine = Machine(bytes([0x00, 0x01]))
        with self.assertRaises(MachineError) as context:
            machine.step()
        self.assertIn("обрывается", str(context.exception))

    def test_address_out_of_memory(self):
        """Адрес вне памяти данных отклоняется."""
        machine = empty_machine()
        machine.execute(make("load", 0, 16383))
        with self.assertRaises(MachineError) as context:
            machine.execute(make("read", 0, 1, 255))
        self.assertIn("вне памяти данных", str(context.exception))
