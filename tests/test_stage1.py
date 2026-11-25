"""Автотесты этапа 1: разбор CSV и промежуточное представление."""

import unittest

import _util
from csv_parser import parse_program
from isa import AssemblyError


def spec_program():
    """Возвращает программу спецификации из тестового файла."""
    return _util.load_program(_util.TESTS / "spec_test.csv")


class SpecProgramTestCase(unittest.TestCase):
    """Тестовая программа спецификации разбирается по заданию."""

    def test_command_count(self):
        """В программе четыре команды."""
        self.assertEqual(len(spec_program()), 4)

    def test_fields_match_specification(self):
        """Поля и значения команд совпадают со спецификацией."""
        texts = [item.fields_text() for item in spec_program()]
        self.assertEqual(
            texts,
            [
                "A=0, B=956, C=568",
                "A=1, B=615, C=959, D=115",
                "A=9, B=302, C=84, D=113",
                "A=3, B=156, C=603, D=647, E=38",
            ],
        )

    def test_opcodes_and_sizes(self):
        """Коды операций и размеры команд соответствуют варианту."""
        program = spec_program()
        self.assertEqual([item.code for item in program], [0, 1, 9, 3])
        self.assertEqual([item.size for item in program], [4, 5, 5, 7])


class CsvSyntaxTestCase(unittest.TestCase):
    """Допустимые формы записи программы."""

    def test_header_is_optional(self):
        """Программа без заголовка разбирается."""
        program = parse_program("load,1,2\n")
        self.assertEqual(program[0].fields_text(), "A=0, B=1, C=2")

    def test_header_is_skipped(self):
        """Заголовок CSV не считается командой."""
        program = parse_program("command,b,c,d,e\nload,1,2\n")
        self.assertEqual(len(program), 1)

    def test_comments_and_empty_lines(self):
        """Комментарии и пустые строки игнорируются."""
        text = "# комментарий\n\n   \nread,1,2,3\n"
        self.assertEqual(len(parse_program(text)), 1)

    def test_hexadecimal_values(self):
        """Шестнадцатеричные значения полей разбираются."""
        program = parse_program("eq,0x0,0x10,0x20,0x30\n")
        self.assertEqual(program[0].values, (0, 16, 32, 48))

    def test_trailing_empty_columns(self):
        """Пустые столбцы в конце строки допустимы."""
        program = parse_program("read,1,2,3,\n")
        self.assertEqual(program[0].values, (1, 2, 3))

    def test_field_access_by_name(self):
        """Поля доступны по имени."""
        program = parse_program("write,10,20,30\n")
        self.assertEqual(program[0].field("A"), 9)
        self.assertEqual(program[0].field("B"), 10)
        self.assertEqual(program[0].field("C"), 20)
        self.assertEqual(program[0].field("D"), 30)


class CsvErrorTestCase(unittest.TestCase):
    """Некорректные программы дают понятную ошибку."""

    def check_error(self, text, fragment):
        """Проверяет, что разбор завершается ошибкой с фрагментом."""
        with self.assertRaises(AssemblyError) as context:
            parse_program(text)
        self.assertIn(fragment, str(context.exception))

    def test_unknown_mnemonic(self):
        """Неизвестная мнемоника отклоняется."""
        self.check_error("jump,1\n", "неизвестная команда 'jump'")

    def test_destination_out_of_range(self):
        """Адрес вне 14 бит отклоняется."""
        self.check_error(
            "load,16384,1\n", "B=16384 вне диапазона 0..16383"
        )

    def test_constant_out_of_range(self):
        """Константа вне 13 бит отклоняется."""
        self.check_error(
            "load,1,8192\n", "C=8192 вне диапазона 0..8191"
        )

    def test_offset_out_of_range(self):
        """Смещение вне 8 бит отклоняется."""
        self.check_error("read,1,2,256\n", "D=256 вне диапазона 0..255")

    def test_missing_field(self):
        """Незаполненное поле отклоняется."""
        self.check_error("eq,1,2,3\n", "не заполнено поле E")

    def test_extra_field(self):
        """Лишнее заполненное поле отклоняется."""
        self.check_error("load,1,2,3\n", "нет поля D")

    def test_not_a_number(self):
        """Нечисловое значение отклоняется."""
        self.check_error("load,1,abc\n", "не является целым числом")

    def test_negative_value(self):
        """Отрицательное значение отклоняется."""
        self.check_error("load,-1,1\n", "B=-1 вне диапазона")

    def test_wrong_header(self):
        """Неверный заголовок отклоняется."""
        self.check_error("cmd,a,b,c\nload,1,2\n", "неверный заголовок")

    def test_line_number_in_message(self):
        """Сообщение содержит номер ошибочной строки."""
        self.check_error("load,1,2\nload,20000,1\n", "Строка 2:")

    def test_missing_file(self):
        """Отсутствующий файл вызывает ошибку ввода-вывода."""
        with self.assertRaises(OSError):
            _util.load_program(_util.TESTS / "absent.csv")
