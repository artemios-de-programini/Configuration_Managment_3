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
"$PYTHON_BIN" -m unittest discover -s tests -v
