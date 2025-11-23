from stdio import *

# Test 1: list[T, n] for arrays
def test_list_arrays() -> void:
    a: list[int, 10]
    b: list[-char, 5]
    c: list[type[Node], 3]

# Test 2: Flexible array member list[T]
class Buffer:
    len: int
    data: list[char]

# Test 3: Bitfields bit[T, n]
class Flags:
    a: bit[unsigned[int], 3]
    b: bit[unsigned[int], 5]
    c: bit[int, 1]

# Test 4: Anonymous struct with @var
@var(point_a, point_b)
class _:
    x: int
    y: int

# Test 5: Anonymous union with @var
@var(data_u)
class _(Union):
    i: int
    f: float

# Test 6: Infinite loop for(;;)
def test_infinite_loop() -> void:
    i: int = 0
    while ():
        i ** _
        if i > 10:
            break

# Test 7: Do-while loop (still works)
def test_do_while() -> void:
    i: int = 0
    while ():
        printf("%d\n", i)
        i ** _
        if i < 5:
            continue

# Test 8: Preprocessor elif/else
if [DEBUG]:
    printf("debug mode\n")
elif [VERBOSE]:
    printf("verbose mode\n")
elif [QUIET]:
    printf("quiet mode\n")
else:
    printf("normal mode\n")

# Test 9: Preprocessor with not
if [not DISABLE_LOGGING]:
    printf("logging enabled\n")
elif [ERROR_ONLY]:
    printf("errors only\n")
else:
    printf("logging disabled\n")

# Test 10: match/case for switch with fallthrough
def test_switch(x: int) -> void:
    match x:
        case 1:
            printf("one\n")
            break
        case 2:
            printf("two or three\n")
        case 3:
            printf("three\n")
            break
        case _:
            printf("other\n")
            break

# Test 11: Combined example from design
class Node:
    data: int
    next: -type[Node]

@typedef(List)
class List:
    head: -type[Node]

def consume(l: -List) -> void:
    match l._.head._.data:
        case 0:
            break
        case _:
            break

def main() -> int:
    return 0
