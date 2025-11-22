from stdio import *

# Test 1: Plain struct with type[] syntax
class PlainStruct:
    a: int
    b: int

x: type[PlainStruct]
ptr: -type[PlainStruct]

# Test 2: Typedef struct
@typedef(TypedefStruct)
class TypedefStruct:
    x: int
    y: int

# Can use bare name with typedef (uses the typedef)
ts: TypedefStruct
# type[] always gives struct tag (not recommended with typedef)
ts2: type[TypedefStruct]  # This will be struct TypedefStruct

# Test 3: Struct with @var
@var(v1)
class VarStruct:
    data: int

# Test 4: Struct with @var multiple
@var(v2, v3, v4)
class MultiVarStruct:
    value: int

# Test 5: Combined @typedef and @var
@typedef(Combined)
@var(c1, c2)
class Combined:
    field: int

# Test 6: Use typedef'd struct
def test() -> void:
    t: TypedefStruct
    t.x = 10
    t.y = 20

    # Pointer to typedef'd struct
    p: -TypedefStruct = _.t
    p._.x = 5

    # Array of typedef'd struct
    arr: TypedefStruct[3]
    arr[0] = TypedefStruct(1, 2)

# Test 7: Use plain struct with type[]
def test2() -> void:
    ps: type[PlainStruct]
    ps.a = 1
    ps.b = 2

    # Pointer to plain struct
    pptr: -type[PlainStruct] = _.ps
    pptr._.a = 3

# Test 8: Type alias with type[]
@typedef(Point)
class Point:
    x: int
    y: int

type PointPtr = -type[Point]

def test3() -> void:
    pp: PointPtr

# Test 9: Enum with enum[] syntax
class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2

def test4() -> void:
    c: enum[Color] = RED
    if c == GREEN:
        printf("green\n")

# Test 10: Union with union[] syntax
class Data(Union):
    i: int
    f: float

def test5() -> void:
    d: union[Data]
    d.i = 42

# Test 11: type[] syntax for plain struct
class ExplicitStruct:
    value: int

def test6() -> void:
    es: type[ExplicitStruct]
    es.value = 100
