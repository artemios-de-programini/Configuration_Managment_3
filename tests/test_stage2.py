"""Автотесты этапа 2: машинный код, запись файла и режим --test."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import _util
from assembler import assemble, encode_commands
from isa import decode, encode, format_bytes, make
from main import main as assembler_main

SPEC_BYTES = (
    bytes([0xC0, 0x3B, 0xE0, 0x08]),
    bytes([0x71, 0x26, 0xFC, 0x0E, 0x73]),
    bytes([0xE9, 0x12, 0x50, 0x01, 0x71]),
    bytes([0xC3, 0xB9, 0x25, 0x1C, 0x0A, 0x26, 0x00]),
)


def spec_program():
    """Возвращает программу спецификации."""
    return _util.load_program(_util.TESTS / "spec_test.csv")


class MachineCodeTestCase(unittest.TestCase):
    """Машинный код совпадает со спецификацией побайтово."""

    def test_sizes(self):
        """Размеры команд равны 4, 5, 5 и 7 байт."""
        chunks = encode_commands(spec_program())
        self.assertEqual([len(chunk) for chunk in chunks], [4, 5, 5, 7])

    def test_control_bytes(self):
        """Байты команд совпадают с контрольными значениями."""
        self.assertEqual(
            tuple(encode_commands(spec_program())), SPEC_BYTES
        )

    def test_hex_format(self):
        """Байтовая запись команды соответствует спецификации."""
        self.assertEqual(
            format_bytes(SPEC_BYTES[0]), "0xC0, 0x3B, 0xE0, 0x08"
        )
        self.assertEqual(
            format_bytes(SPEC_BYTES[-1]),
            "0xC3, 0xB9, 0x25, 0x1C, 0x0A, 0x26, 0x00",
        )

    def test_whole_program(self):
        """Вся программа занимает 21 байт."""
        code = assemble(spec_program())
        self.assertEqual(code, b"".join(SPEC_BYTES))
        self.assertEqual(len(code), 21)


class CodecRoundTripTestCase(unittest.TestCase):
    """Кодирование и декодирование взаимно обратны."""

    def test_round_trip(self):
        """Команды декодируются в исходное представление."""
        instructions = [
            make("load", 0, 0),
            make("load", 956, 568),
            make("read", 615, 959, 115),
            make("write", 302, 84, 113),
            make("eq", 156, 603, 647, 38),
            make("eq", 255, 16383, 16383, 16383),
        ]
        for instruction in instructions:
            with self.subTest(text=instruction.fields_text()):
                self.assertEqual(
                    decode(encode(instruction)), instruction
                )


class AssemblerCliTestCase(unittest.TestCase):
    """Работа командной строки ассемблера."""

    def test_test_mode_output(self):
        """Режим --test печатает байты команд и число команд."""
        with _util.output_path() as binary:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = assembler_main(
                    [
                        str(_util.TESTS / "spec_test.csv"),
                        str(binary),
                        "--test",
                    ]
                )
        self.assertEqual(code, 0)
        lines = buffer.getvalue().splitlines()
        self.assertEqual(
            lines[:4], [format_bytes(chunk) for chunk in SPEC_BYTES]
        )
        self.assertIn("Ассемблировано команд: 4", lines[-1])

    def test_binary_file_is_written(self):
        """Машинный код записывается в файл."""
        with _util.output_path() as binary:
            with redirect_stdout(io.StringIO()):
                assembler_main(
                    [str(_util.TESTS / "spec_test.csv"), str(binary)]
                )
            self.assertEqual(binary.read_bytes(), b"".join(SPEC_BYTES))

    def test_output_directory_is_created(self):
        """Каталог результата создаётся автоматически."""
        with _util.output_path() as binary:
            nested = binary.parent / "deep" / "program.bin"
            with redirect_stdout(io.StringIO()):
                code = assembler_main(
                    [str(_util.TESTS / "spec_test.csv"), str(nested)]
                )
            self.assertEqual(code, 0)
            self.assertTrue(nested.exists())

    def test_invalid_program_returns_error(self):
        """Ошибочная программа завершается кодом 1."""
        with _util.output_path() as binary:
            buffer = io.StringIO()
            with redirect_stderr(buffer):
                with redirect_stdout(io.StringIO()):
                    code = assembler_main(
                        [
                            str(_util.TESTS / "invalid_range.csv"),
                            str(binary),
                        ]
                    )
        self.assertEqual(code, 1)
        self.assertIn("вне диапазона", buffer.getvalue())

    def test_missing_input_file(self):
        """Отсутствующий файл программы завершается кодом 1."""
        with _util.output_path() as binary:
            buffer = io.StringIO()
            with redirect_stderr(buffer):
                with redirect_stdout(io.StringIO()):
                    code = assembler_main(
                        [str(_util.TESTS / "absent.csv"), str(binary)]
                    )
        self.assertEqual(code, 1)
        self.assertIn("не удалось прочитать", buffer.getvalue())
