from stdio import *

# ============================================================================
# Test 1: Casts - cast[T](expr)
# ============================================================================

def test_casts() -> void:
    x: int = 42
    y: float = cast[float](x)
    p: -void = cast[-void](x)
    c: char = cast[char](65)

# ============================================================================
# Test 2: Escaped Identifiers - __ID → ID
# ============================================================================

def test_escaped_identifiers() -> void:
    # ___ → _ in C
    ___: int = 5

    # __FILE__ → FILE__ in C
    __FILE__: -char = "test.c"

    # Regular identifiers work as before
    x: int = 10

# ============================================================================
# Test 3: #undef Support - del NAME
# ============================================================================

MAX: macro = 100
MIN: macro = 0

del MAX
del MIN

# Multiple undefs
DEBUG: macro = 1
VERBOSE: macro = 2
del DEBUG, VERBOSE

# ============================================================================
# Test 4: C11 Qualifiers
# ============================================================================

# 4.1: atomic[T]
counter: atomic[int]
ptr: -atomic[int]

# 4.2: alignas[N, T]
aligned_var: alignas[16, int]
aligned_array: alignas[64, list[int, 10]]

# 4.3: alignof[T]
def test_alignof() -> void:
    a: size_t = alignof[type[Node]]
    b: size_t = alignof[int]

# 4.4: static_assert
class Node:
    data: int
    next: -type[Node]

def test_static_assert() -> void:
    static_assert(sizeof(type[Node]) > 0, "Node size must be positive")

# 4.5: thread_local[T]
tls_var: thread_local[int]
static_tls: static[thread_local[int]]

# ============================================================================
# Test 5: Anonymous Embedded Aggregates
# ============================================================================

class Outer:
    a: int

    # Anonymous embedded struct
    class _:
        x: int
        y: int

    b: int

class Tagged:
    tag: int

    # Anonymous embedded union
    class _(Union):
        i: int
        f: float
        d: double

# Anonymous enum in struct
class Widget:
    @var(color)
    class _(Enum):
        RED = 0
        GREEN = 1
        BLUE = 2

    value: int

# Top-level anonymous enum
@var(global_status)
class _(Enum):
    OK = 0
    ERROR = 1
    PENDING = 2

# ============================================================================
# Test 6: Function and Function Pointer Types
# ============================================================================

# 6.1: Function type - (args)(result)
type BinaryFunc = (int, int)(int)
type UnaryFunc = (double,)(void)  # Single-element tuple needs trailing comma
type NoArgFunc = ()(int)

# Function declaration with new syntax
add: (int, int)(int)

# 6.2: Function pointer type - -(args)(result)
callback: -(int, int)(int)
handler: -()(void)  # Function pointer: no args -> void

# Type alias for function pointer
type BinOp = -(int, int)(int)

# Function taking function pointer as argument
def apply(f: -(int, int)(int), a: int, b: int) -> int:
    return f(a, b)

# ============================================================================
# Test 7: Combined Examples
# ============================================================================

# Cast to function pointer
def test_function_cast() -> void:
    ptr: -void = cast[-void](0)
    fp: -(int, int)(int) = cast[-(int, int)(int)](ptr)

def main() -> int:
    return 0
