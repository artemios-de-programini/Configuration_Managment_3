"""Числовые константы УВМ (вариант №8) и коды возврата программ."""

MIN_VALUE = 0
ZERO = 0
ONE = 1
TWO = 2

MEMORY_SIZE = 1 << 14
ADDRESS_MAX = MEMORY_SIZE - ONE
CONSTANT_MAX = (1 << 13) - ONE
OFFSET_MAX = (1 << 8) - ONE
OPCODE_MAX = (1 << 4) - ONE
MAX_COMMAND_SIZE = 7
RANGE_PARTS = 2

SUCCESS_CODE = 0
FAILURE_CODE = 1
