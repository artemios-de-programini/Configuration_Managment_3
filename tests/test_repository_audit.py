"""Аудит оформления git-репозитория по перечню нарушений."""

import ast
import re
import subprocess
import tokenize
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_NAME = "README.md"
GITIGNORE_NAME = ".gitignore"
SOURCE_DIR_NAME = "src"
TESTS_DIR_NAME = "tests"
INTERPRETER_RELATIVE = "src/interpreter.py"
RUN_SCRIPT_NAMES = ("run.sh", "tests/run.ps1")
PYTHON_SUFFIX = ".py"
CSV_SUFFIX = ".csv"
POWERSHELL_SUFFIX = ".ps1"
COMMIT_PREFIX = "feat: "
TAB = "\t"
NEWLINE = "\n"

MIN_README_LINES = 80
MAX_FILE_LINES = 1000
MAX_PYTHON_LINE = 79
MAX_CODE_LINE = 120
MAX_FUNCTION_LINES = 40
MAX_PARAMETERS = 7
MAX_COMPLEXITY = 10
MAX_STAGE_COMMITS = 5
MAX_BLANK_RUN = 2
SUCCESS_CODE = 0

SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
PASCAL_CASE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
UPPER_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")

REQUIRED_IGNORES = (
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    ".venv/",
    ".pytest_cache/",
    ".vscode/",
    ".idea/",
    "output/",
    "*.bin",
    "*.zip",
    "*.tar*",
    "build/",
    "dist/",
)

ARCHIVE_FRAGMENTS = (".zip", ".7z", ".rar", ".tar", ".gz")
BINARY_FRAGMENTS = (".bin", ".exe", ".dll", ".so", ".class")
PYTHON_SERVICE_FRAGMENTS = (
    "__pycache__",
    ".pyc",
    ".pyo",
    ".egg-info",
    ".pytest_cache",
)
BUILD_FRAGMENTS = ("build/", "dist/", "output/")
EDITOR_FRAGMENTS = (
    ".vscode/",
    ".idea/",
    ".iml",
    ".DS_Store",
    "Thumbs.db",
)

README_HEADINGS = (
    "# Практическая работа",
    "## Структура репозитория",
    "## Спецификация",
    "## Язык ассемблера",
    "## Запуск",
    "## Этапы разработки",
    "## Проверка оформления",
    "## Тестирование",
)

EXPECTED_COMMITS = (
    "feat: Этап 1. Перевод программы в промежуточное представление",
    "feat: Этап 2. Формирование машинного кода",
    "feat: Этап 3. Интерпретатор и операции с памятью",
    "feat: Этап 4. Реализация арифметико-логического устройства (АЛУ)",
    "feat: Этап 5. Выполнение тестовой задачи",
)
STAGE_FIVE_SUBJECT = EXPECTED_COMMITS[-1]


def run_git(*arguments):
    """Выполняет команду git в каталоге проекта."""
    command = ("git",) + arguments
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != SUCCESS_CODE:
        message = result.stderr.strip()
        raise AssertionError(f"git {arguments}: {message}")
    return result.stdout.splitlines()


def tracked_files():
    """Возвращает файлы, отслеживаемые Git."""
    return [name for name in run_git("ls-files") if name]


def python_files():
    """Возвращает отслеживаемые файлы Python."""
    return [name for name in tracked_files() if name.endswith(PYTHON_SUFFIX)]


def code_files():
    """Возвращает скрипты запуска и CSV-файлы проекта."""
    names = list(RUN_SCRIPT_NAMES)
    names.extend(
        name for name in tracked_files() if name.endswith(CSV_SUFFIX)
    )
    names.extend(
        name for name in tracked_files()
        if name.endswith(POWERSHELL_SUFFIX)
    )
    return names


def commit_subjects():
    """Возвращает темы всех коммитов истории."""
    return run_git("log", "--all", "--format=%s")


def read_text(name):
    """Читает файл проекта целиком."""
    return (ROOT / name).read_text(encoding="utf-8")


def read_lines(name):
    """Читает файл проекта построчно."""
    return read_text(name).splitlines()


def long_line_messages(name, limit):
    """Возвращает сообщения о слишком длинных строках файла."""
    messages = []
    for number, line in enumerate(read_lines(name), start=1):
        if len(line) > limit:
            messages.append(f"{name}:{number}: {len(line)} символов")
    return messages


def matching_files(fragments):
    """Возвращает файлы, в именах которых есть запрещённые фрагменты."""
    matched = []
    for name in tracked_files():
        if any(fragment in name for fragment in fragments):
            matched.append(name)
    return matched


def required_run_tokens():
    """Возвращает обязательные команды скриптов запуска."""
    tokens = ["src/main.py", "unittest", "output"]
    if (ROOT / INTERPRETER_RELATIVE).is_file():
        tokens.append("src/interpreter.py")
    return tokens


def function_nodes(tree):
    """Возвращает описания функций и методов в синтаксическом дереве."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _needs_docstring(node):
    """Проверяет, что узел обязан иметь docstring."""
    return isinstance(
        node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    )


def docstring_messages(name, tree):
    """Проверяет наличие docstring у модуля, классов и функций."""
    messages = []
    if not ast.get_docstring(tree):
        messages.append(f"{name}: нет docstring модуля")
    for node in ast.walk(tree):
        if not _needs_docstring(node):
            continue
        if not ast.get_docstring(node):
            messages.append(
                f"{name}:{node.lineno}: нет docstring у {node.name}"
            )
    return messages


def comment_lines(name):
    """Возвращает номера строк с комментариями."""
    path = ROOT / name
    with path.open("rb") as stream:
        tokens = list(tokenize.tokenize(stream.readline))
    return [
        token.start[0]
        for token in tokens
        if token.type == tokenize.COMMENT
    ]


def _all_arguments(arguments):
    """Возвращает все аргументы функции, включая *args и **kwargs."""
    result = list(arguments.posonlyargs)
    result.extend(arguments.args)
    result.extend(arguments.kwonlyargs)
    if arguments.vararg:
        result.append(arguments.vararg)
    if arguments.kwarg:
        result.append(arguments.kwarg)
    return result


def _argument_messages(node, name):
    """Проверяет имена аргументов функции."""
    messages = []
    for argument in _all_arguments(node.args):
        if not SNAKE_CASE.match(argument.arg):
            messages.append(
                f"{name}:{node.lineno}: аргумент {argument.arg}"
            )
    return messages


def _function_name_messages(name, tree):
    """Проверяет имена функций, методов и их аргументов."""
    messages = []
    for node in function_nodes(tree):
        if not SNAKE_CASE.match(node.name):
            messages.append(
                f"{name}:{node.lineno}: имя функции {node.name}"
            )
        messages.extend(_argument_messages(node, name))
    return messages


def _class_name_messages(name, tree):
    """Проверяет имена классов."""
    messages = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not PASCAL_CASE.match(node.name):
                messages.append(
                    f"{name}:{node.lineno}: имя класса {node.name}"
                )
    return messages


def _check_module_name(identifier, name, line_no, messages):
    """Проверяет одно имя переменной модуля."""
    if UPPER_CASE.match(identifier) or SNAKE_CASE.match(identifier):
        return
    messages.append(f"{name}:{line_no}: имя переменной {identifier}")


def _module_name_messages(name, tree):
    """Проверяет имена переменных уровня модуля."""
    messages = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                _check_module_name(target.id, name, node.lineno, messages)
    return messages


def naming_messages(name, tree):
    """Собирает сообщения о нарушениях соглашений об именах."""
    messages = _function_name_messages(name, tree)
    messages.extend(_class_name_messages(name, tree))
    messages.extend(_module_name_messages(name, tree))
    return messages


def function_length_messages(name, tree):
    """Проверяет длину функций и методов."""
    messages = []
    for node in function_nodes(tree):
        length = node.end_lineno - node.lineno + 1
        if length > MAX_FUNCTION_LINES:
            messages.append(
                f"{name}:{node.lineno}: функция {node.name} "
                f"занимает {length} строк"
            )
    return messages


def parameter_messages(name, tree):
    """Проверяет число аргументов функций и методов."""
    messages = []
    for node in function_nodes(tree):
        count = len(_all_arguments(node.args))
        if count > MAX_PARAMETERS:
            messages.append(
                f"{name}:{node.lineno}: функция {node.name} "
                f"имеет {count} аргументов"
            )
    return messages


def _node_weight(node):
    """Возвращает вклад узла в цикломатическую сложность."""
    if isinstance(
        node,
        (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While,
         ast.ExceptHandler),
    ):
        return 1
    if isinstance(node, ast.BoolOp):
        return len(node.values) - 1
    if isinstance(node, ast.comprehension):
        return len(node.ifs)
    return 0


def complexity(node):
    """Считает цикломатическую сложность функции."""
    score = 1
    for child in ast.walk(node):
        score += _node_weight(child)
    return score


def complexity_messages(name, tree):
    """Проверяет цикломатическую сложность функций."""
    messages = []
    for node in function_nodes(tree):
        score = complexity(node)
        if score > MAX_COMPLEXITY:
            messages.append(
                f"{name}:{node.lineno}: функция {node.name} "
                f"имеет сложность {score}"
            )
    return messages


def _is_number(node):
    """Проверяет, что узел является числовым литералом."""
    if not isinstance(node, ast.Constant):
        return False
    if isinstance(node.value, bool):
        return False
    return isinstance(node.value, (int, float))


def numeric_compare_messages(name, tree):
    """Проверяет отсутствие числовых литералов в сравнениях."""
    messages = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left]
        operands.extend(node.comparators)
        if any(_is_number(item) for item in operands):
            messages.append(
                f"{name}:{node.lineno}: числовой литерал в сравнении"
            )
    return messages


def _is_special_literal(node):
    """Проверяет, что узел является None, True или False."""
    if not isinstance(node, ast.Constant):
        return False
    if node.value is None:
        return True
    return isinstance(node.value, bool)


def _has_equality_op(node):
    """Проверяет, что в сравнении есть оператор == или !=."""
    return any(
        isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops
    )


def _literal_compare_messages(name, tree):
    """Проверяет сравнения с None, True и False через == и !=."""
    messages = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not _has_equality_op(node):
            continue
        if any(_is_special_literal(item) for item in node.comparators):
            messages.append(
                f"{name}:{node.lineno}: сравнение с None или True/False"
            )
    return messages


def _default_argument_messages(name, tree):
    """Проверяет изменяемые значения аргументов по умолчанию."""
    messages = []
    for node in function_nodes(tree):
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                messages.append(
                    f"{name}:{node.lineno}: изменяемое значение "
                    f"по умолчанию"
                )
    return messages


def _bare_except_messages(name, tree):
    """Проверяет отсутствие конструкций bare except."""
    messages = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            messages.append(f"{name}:{node.lineno}: bare except")
    return messages


def _is_docstring_node(node):
    """Проверяет, что узел является docstring модуля."""
    if not isinstance(node, ast.Expr):
        return False
    return isinstance(node.value, ast.Constant)


def _import_messages(name, tree):
    """Проверяет, что импорты стоят в начале модуля."""
    messages = []
    seen_code = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if seen_code:
                messages.append(
                    f"{name}:{node.lineno}: импорт после кода"
                )
        elif not _is_docstring_node(node):
            seen_code = True
    return messages


def _whitespace_messages(name):
    """Проверяет пробелы в конце строк, табуляции и пустые строки."""
    messages = []
    blank_run = 0
    for number, line in enumerate(read_lines(name), start=1):
        if line.rstrip() != line:
            messages.append(f"{name}:{number}: пробелы в конце строки")
        if TAB in line:
            messages.append(f"{name}:{number}: символ табуляции")
        if line.strip():
            blank_run = 0
        else:
            blank_run += 1
            if blank_run > MAX_BLANK_RUN:
                messages.append(
                    f"{name}:{number}: больше двух пустых строк"
                )
    if not read_text(name).endswith(NEWLINE):
        messages.append(f"{name}: нет перевода строки в конце файла")
    return messages


def pep8_messages(name, tree):
    """Собирает сообщения о нарушениях PEP 8 в файле."""
    messages = _whitespace_messages(name)
    messages.extend(_import_messages(name, tree))
    messages.extend(_literal_compare_messages(name, tree))
    messages.extend(_default_argument_messages(name, tree))
    messages.extend(_bare_except_messages(name, tree))
    messages.extend(naming_messages(name, tree))
    return messages


def parse_tree(name):
    """Разбирает файл Python в синтаксическое дерево."""
    return ast.parse(read_text(name))


class RepositoryAuditTestCase(unittest.TestCase):
    """Комплексная проверка оформления репозитория."""

    def test_s1_readme_exists(self):
        """С1: в корне есть подробный README.md."""
        self.assertTrue((ROOT / README_NAME).is_file())
        self.assertGreaterEqual(
            len(read_lines(README_NAME)), MIN_README_LINES
        )

    def test_s1_readme_sections(self):
        """С1: README.md содержит обязательные разделы."""
        text = read_text(README_NAME)
        for heading in README_HEADINGS:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_s2_gitignore_patterns(self):
        """С2: .gitignore исключает обязательные шаблоны."""
        self.assertTrue((ROOT / GITIGNORE_NAME).is_file())
        text = read_text(GITIGNORE_NAME)
        for pattern in REQUIRED_IGNORES:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, text)

    def test_s3_sources_in_src(self):
        """С3: исходный код Python лежит в каталоге src."""
        self.assertTrue((ROOT / SOURCE_DIR_NAME).is_dir())
        for name in python_files():
            with self.subTest(file=name):
                self.assertTrue(
                    name.startswith(SOURCE_DIR_NAME + "/")
                    or name.startswith(TESTS_DIR_NAME + "/")
                )

    def test_s4_tests_in_tests(self):
        """С4: автотесты лежат в каталоге tests."""
        self.assertTrue((ROOT / TESTS_DIR_NAME).is_dir())
        for name in python_files():
            if Path(name).name.startswith("test_"):
                with self.subTest(file=name):
                    self.assertEqual(
                        Path(name).parent.name, TESTS_DIR_NAME
                    )

    def test_s5_run_scripts_exist(self):
        """С5: есть скрипты запуска run.sh и tests/run.ps1."""
        for script in RUN_SCRIPT_NAMES:
            with self.subTest(script=script):
                self.assertTrue((ROOT / script).is_file())

    def test_s5_run_scripts_commands(self):
        """С5: скрипты запускают ассемблер, интерпретатор и тесты."""
        for script in RUN_SCRIPT_NAMES:
            text = read_text(script).replace("\\", "/")
            for token in required_run_tokens():
                with self.subTest(script=script, token=token):
                    self.assertIn(token, text)

    def test_s6_commit_prefixes(self):
        """С6: каждый коммит начинается с префикса feat:."""
        for subject in commit_subjects():
            with self.subTest(subject=subject):
                self.assertTrue(subject.startswith(COMMIT_PREFIX))

    def test_s6_commit_messages(self):
        """С6: темы коммитов соответствуют этапам работы."""
        for subject in commit_subjects():
            with self.subTest(subject=subject):
                self.assertIn(subject, EXPECTED_COMMITS)

    def test_s6_stage_count(self):
        """С6: на финальном этапе в истории ровно пять коммитов."""
        subjects = commit_subjects()
        self.assertLessEqual(len(subjects), MAX_STAGE_COMMITS)
        if STAGE_FIVE_SUBJECT in subjects:
            self.assertEqual(len(subjects), MAX_STAGE_COMMITS)

    def test_g1_no_archives(self):
        """Г1: в Git нет архивов."""
        self.assertEqual(matching_files(ARCHIVE_FRAGMENTS), [])

    def test_g2_no_binaries(self):
        """Г2: в Git нет бинарных файлов."""
        self.assertEqual(matching_files(BINARY_FRAGMENTS), [])

    def test_g3_no_python_service_files(self):
        """Г3: в Git нет служебных файлов Python."""
        self.assertEqual(matching_files(PYTHON_SERVICE_FRAGMENTS), [])

    def test_g4_no_build_artifacts(self):
        """Г4: в Git нет артефактов сборки и каталога output."""
        self.assertEqual(matching_files(BUILD_FRAGMENTS), [])

    def test_g5_no_editor_settings(self):
        """Г5: в Git нет настроек редакторов и среды."""
        self.assertEqual(matching_files(EDITOR_FRAGMENTS), [])

    def test_r1_file_length(self):
        """Р1: ни один файл не длиннее 1000 строк."""
        for name in tracked_files():
            with self.subTest(file=name):
                self.assertLessEqual(
                    len(read_lines(name)), MAX_FILE_LINES
                )

    def test_r2_python_line_length(self):
        """Р2: строки Python не длиннее 79 символов."""
        for name in python_files():
            for message in long_line_messages(name, MAX_PYTHON_LINE):
                with self.subTest(file=name):
                    self.fail(message)

    def test_r6_code_line_length(self):
        """Р6: строки скриптов и CSV не длиннее 120 символов."""
        for name in code_files():
            for message in long_line_messages(name, MAX_CODE_LINE):
                with self.subTest(file=name):
                    self.fail(message)

    def test_f1_function_length(self):
        """Ф1: функции и методы не длиннее 40 строк."""
        for name in python_files():
            for message in function_length_messages(
                name, parse_tree(name)
            ):
                with self.subTest(file=name):
                    self.fail(message)

    def test_a1_parameter_count(self):
        """А1: у функций не более семи аргументов."""
        for name in python_files():
            for message in parameter_messages(name, parse_tree(name)):
                with self.subTest(file=name):
                    self.fail(message)

    def test_k1_no_comments(self):
        """К1: в Python-файлах нет комментариев."""
        for name in python_files():
            with self.subTest(file=name):
                self.assertEqual(comment_lines(name), [])

    def test_k1_docstrings(self):
        """К1: у модуля, класса и функции есть docstring."""
        for name in python_files():
            for message in docstring_messages(name, parse_tree(name)):
                with self.subTest(file=name):
                    self.fail(message)

    def test_c1_complexity(self):
        """Ц1: сложность функций не больше 10."""
        for name in python_files():
            for message in complexity_messages(name, parse_tree(name)):
                with self.subTest(file=name):
                    self.fail(message)

    def test_m1_no_numeric_comparisons(self):
        """М1: в сравнениях нет числовых литералов."""
        for name in python_files():
            for message in numeric_compare_messages(
                name, parse_tree(name)
            ):
                with self.subTest(file=name):
                    self.fail(message)

    def test_i1_pep8(self):
        """И1: код соответствует правилам PEP 8."""
        for name in python_files():
            for message in pep8_messages(name, parse_tree(name)):
                with self.subTest(file=name):
                    self.fail(message)
