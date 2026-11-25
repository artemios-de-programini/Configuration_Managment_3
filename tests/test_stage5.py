"""Автотесты этапа 5: тестовая задача и три примера программ."""

import io
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout

import _util
from interpreter import main as interpreter_main
from main import main as assembler_main

VECTOR_PROGRAM = _util.TESTS / "vector_equal_6.csv"
EXAMPLES = (
    (_util.TESTS / "example_1.csv", 300, 305, [0, 0, 0, 0, 0, 0]),
    (_util.TESTS / "example_2.csv", 800, 805, [1, 1, 1, 1, 1, 1]),
    (_util.TESTS / "example_3.csv", 980, 985, [1, 1, 1, 0, 1, 1]),
)


class VectorTaskTestCase(unittest.TestCase):
    """Тестовая задача варианта №8."""

    def test_instruction_count(self):
        """Программа состоит из 19 команд."""
        self.assertEqual(_util.run_file(VECTOR_PROGRAM).executed, 19)

    def test_result_in_first_vector(self):
        """Результат записан в первый вектор."""
        self.assertEqual(
            _util.cells(_util.run_file(VECTOR_PROGRAM), 100, 105),
            [1, 1, 0, 1, 1, 0],
        )

    def test_second_vector_is_intact(self):
        """Второй вектор не изменяется."""
        self.assertEqual(
            _util.cells(_util.run_file(VECTOR_PROGRAM), 200, 205),
            [5, 7, 0, 11, 13, 0],
        )


class ExamplesTestCase(unittest.TestCase):
    """Три примера программ с разными данными."""

    def test_examples(self):
        """Дампы примеров совпадают с ожидаемыми значениями."""
        for path, start, end, expected in EXAMPLES:
            with self.subTest(example=path.name):
                machine = _util.run_file(path)
                self.assertEqual(
                    _util.cells(machine, start, end), expected
                )


class VectorDumpTestCase(unittest.TestCase):
    """XML-дамп тестовой задачи."""

    def test_vector_dump(self):
        """Интерпретатор пишет дамп с результатами сравнения."""
        with _util.output_path(".xml") as dump_path:
            with _util.output_path() as binary:
                with redirect_stdout(io.StringIO()):
                    assembler_main([str(VECTOR_PROGRAM), str(binary)])
                with redirect_stdout(io.StringIO()):
                    interpreter_main(
                        [str(binary), str(dump_path), "100:105"]
                    )
            root = ET.parse(dump_path).getroot()
        self.assertEqual(
            [int(cell.text) for cell in root.findall("cell")],
            [1, 1, 0, 1, 1, 0],
        )


class ProgramsTestCase(unittest.TestCase):
    """Все корректные программы проекта собираются."""

    def test_all_programs_assemble(self):
        """Каждая программа даёт непустой машинный код."""
        programs = sorted(_util.TESTS.glob("*.csv"))
        programs.extend(sorted(_util.TESTS.glob("*.csv")))
        for path in programs:
            if path.name == "invalid_range.csv":
                continue
            with self.subTest(program=path.name):
                self.assertTrue(_util.assemble_file(path))

    def test_spec_program_size(self):
        """Программа спецификации занимает 21 байт."""
        self.assertEqual(
            len(_util.assemble_file(_util.TESTS / "spec_test.csv")), 21
        )
