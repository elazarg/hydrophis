# Test various features

from stdio import *

# Pointers and arrays
def test_pointers() -> void:
    x: int = 5
    px: -int = _.x                     # &x

    v: int = px._                      # *px
    px._ = 10                          # *px = 10

    arr: int[10]
    p0: -int = _.arr[0]                # &arr[0]

    # Pointer arithmetic
    pp: --int = _.px                   # int **pp = &px
    pp._._ = 42                        # **pp = 42

# Arrays
def test_arrays() -> void:
    arr: int[5] = [1, 2, 3, 4, 5]

    matrix: int[2][3] = [
        [1, 2, 3],
        [4, 5, 6],
    ]

    matrix[1][2] = 42

    # Designated initializer
    sparse: int[10] = {0: 1, 5: 6, 9: 10}

# Qualifiers
def test_qualifiers() -> void:
    x: const[int] = 5
    flag: volatile[int]
    u: unsigned[int] = 42
    big: unsigned[long[long]] = 1000000

# Casts
def test_casts() -> void:
    i: int = [int](3.14)
    vp: -void
    p: -int = [-int](vp)
    c: char = [char](65)

# Increment/decrement
def test_inc_dec() -> void:
    i: int = 0
    i ** _                             # i++
    _ ** i                             # ++i
    i // _                             # i--
    _ // i                             # --i

    arr: int[10]
    arr[i ** _] = 5                    # arr[i++] = 5

# Control flow
def test_control() -> void:
    x: int = 5

    # Regular if
    if x > 0:
        printf("positive\n")
    elif x < 0:
        printf("negative\n")
    else:
        printf("zero\n")

    # While
    while x < 10:
        x += 1

    # For loop
    for i in int(i := 0)(i < 5)(i ** _):
        printf("%d\n", i)

    # Do-while
    while ():
        x ** _
        if x < 20:
            continue

# Preprocessor
if [DEBUG]:
    printf("Debug mode\n")

# Macros
BUFFER_SIZE: macro = 1024
PI: macro = 3.14159

def SQUARE(x):
    x * x

def MIN(a, b):
    a if a < b else b

# Struct with designated initializer
class Point:
    x: int
    y: int

def test_struct() -> void:
    p: Point = Point(10, 20)           # {10, 20}
    q: Point(x=5, y=10)                # {.x = 5, .y = 10}
    p.x = 3

# Union
class Data(Union):
    i: int
    f: float
    c: char

def test_union() -> void:
    d: Data
    d.i = 42
    d.f = 3.14

# Enum
class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2

def test_enum() -> void:
    c: Color = RED
    if c == GREEN:
        printf("green\n")

# Goto and labels
def test_goto() -> void:
    i: int = 0

    LOOP: label
    if i > 10:
        raise END
    i ** _
    raise LOOP

    END: label
    printf("done\n")
