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
"$PYTHON_BIN" -m unittest discover -s tests -v
