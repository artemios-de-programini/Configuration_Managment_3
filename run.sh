#!/usr/bin/env bash
set -euo pipefail

detect_python() {
    local candidate
    for candidate in python3 python; do
        if "$candidate" -c 'import sys' >/dev/null 2>&1; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

if [ -n "${PYTHON:-}" ]; then
    PYTHON_BIN="$PYTHON"
elif ! PYTHON_BIN="$(detect_python)"; then
    echo "Не найден интерпретатор Python 3" >&2
    exit 1
fi

"$PYTHON_BIN" src/main.py tests/spec_test.csv output/spec_test.bin --test
"$PYTHON_BIN" src/main.py tests/copy_array.csv output/copy_array.bin
"$PYTHON_BIN" src/interpreter.py output/copy_array.bin output/copy_array.xml 800:807
"$PYTHON_BIN" src/main.py tests/eq_test.csv output/eq_test.bin
"$PYTHON_BIN" src/interpreter.py output/eq_test.bin output/eq_test.xml 30:32
"$PYTHON_BIN" src/main.py tests/vector_equal_6.csv output/vector.bin
"$PYTHON_BIN" src/interpreter.py output/vector.bin output/vector.xml 100:105
"$PYTHON_BIN" src/main.py tests/example_1.csv output/example_1.bin
"$PYTHON_BIN" src/interpreter.py output/example_1.bin output/example_1.xml 300:305
"$PYTHON_BIN" src/main.py tests/example_2.csv output/example_2.bin
"$PYTHON_BIN" src/interpreter.py output/example_2.bin output/example_2.xml 800:805
"$PYTHON_BIN" src/main.py tests/example_3.csv output/example_3.bin
"$PYTHON_BIN" src/interpreter.py output/example_3.bin output/example_3.xml 980:985
"$PYTHON_BIN" -m unittest discover -s tests -v
