# Arafura - C as Python Transpiler

A transpiler that converts Python syntax with C semantics into C code.

## Overview

Arafura allows you to write C programs using Python syntax. The code is syntactically valid Python (passes `ast.parse`) but has C semantics. The transpiler reads the Python AST and emits C code.

## Features

- **Valid Python syntax**: All source files are valid Python that can be parsed
- **C semantics**: Primitive types, manual memory management, pointers, etc.
- **Local AST translation**: No type inference, purely syntactic transformation
- **Full C feature support**: Structs, unions, enums, macros, preprocessor directives, goto/labels

## Installation

```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Print C code to stdout
arafura input.py

# Write to output file
arafura input.py -o output.c

# Check syntax without generating output
arafura input.py --check
```

## Example

Input (`example.py`):
```python
from stdio import *

@typedef(Node)
class Node:
    data: int
    next: -Node

def create_node(value: int) -> -Node:
    node: -Node = malloc(sizeof(Node))
    if node == None:
        return None
    node._.data = value
    node._.next = None
    return node

def main() -> int:
    head: -Node = create_node(42)
    printf("%d\n", head._.data)
    return 0
```

Output:
```c
#include <stdio.h>

typedef struct Node {
    int data;
    Node *next;
} Node;

Node *create_node(int value) {
    Node *node = malloc(sizeof(struct Node));
    if (node == NULL) {
        return NULL;
    }
    node->data = value;
    node->next = NULL;
    return node;
}

int main(void) {
    Node *head = create_node(42);
    printf("%d\n", head->data);
    return 0;
}
```

## Language Reference

### Types

- **Basic types**: `int`, `char`, `float`, `double`, `long`, `short`, `void`
- **Pointers**: `-int` for `int*`, `--int` for `int**`
- **Arrays**: `int[10]` for `int[10]`
- **Pointer-to-array**: `+int[10]` for `int (*)[10]`
- **Qualifiers**: `const[int]`, `volatile[int]`, `unsigned[int]`
- **Storage class**: `static[int]`, `extern[int]`
- **Composite type references**:
  - `type[F]` → `struct F`
  - `enum[E]` → `enum E`
  - `union[U]` → `union U`

### Special `_` Forms

The underscore is reserved for special operations:

- **Address-of**: `_.x` → `&x`
- **Dereference**: `ptr._` → `*ptr`
- **Pointer member**: `ptr._.field` → `ptr->field`
- **Increment**: `i ** _` → `i++`, `_ ** i` → `++i`
- **Decrement**: `i // _` → `i--`, `_ // i` → `--i`
- **Compound literals**: `_(x=1, y=2)` → designated initializer

### Composite Types

```python
# Plain struct (use type[F] to reference)
class Point:
    x: int
    y: int

p: type[Point]                    # struct Point p;

# Struct with typedef
@typedef(Point)
class Point:
    x: int
    y: int

p: Point                          # Point p; (uses typedef)

# Struct with inline variables
@var(v1, v2)
class Data:
    value: int
# Generates: struct Data { int value; } v1, v2;

# Combined typedef + var
@typedef(Point)
@var(p1, p2)
class Point:
    x: int
    y: int
# Generates: typedef struct Point { ... } Point; Point p1, p2;

# Union (use union[F] to reference)
class Data(Union):
    i: int
    f: float

d: union[Data]                    # union Data d;

# Enum (use enum[E] to reference)
class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2

c: enum[Color]                    # enum Color c;
```

### Control Flow

```python
# Regular if/elif/else
if x > 0:
    pass
elif x < 0:
    pass
else:
    pass

# While loop
while x < 10:
    x += 1

# C-style for loop
for i in int(i := 0)(i < 10)(i ** _):
    printf("%d\n", i)

# Do-while loop
while ():
    x ** _
    if x < 10:
        continue

# Goto and labels
LOOP: label
raise LOOP  # goto LOOP
```

### Functions and Macros

```python
# Function (all params and return annotated)
def add(a: int, b: int) -> int:
    return a + b

# Macro (no annotations)
def MAX(a, b):
    a if a > b else b

# Constant macro
PI: macro = 3.14159
```

### Preprocessor

```python
# Includes
import stdio              # #include "stdio.h"
from stdio import *       # #include <stdio.h>

# Conditional compilation
if [DEBUG]:               # #ifdef DEBUG
    printf("debug\n")
```

### Other Features

- **Casts**: `[int](3.14)` → `(int)3.14`
- **sizeof**: `sizeof(int)` → `sizeof(int)`
- **NULL**: `None` → `NULL`
- **Ternary**: `a if x > 0 else b` → `(x > 0 ? a : b)`
- **Walrus operator**: `(x := 5)` → `(x = 5)`

## Implementation

The transpiler is implemented in Python using the `ast` module. It:

1. Parses the input Python code into an AST
2. Performs a first pass to collect type names (structs, unions, enums)
3. Walks the AST and emits C code based on local patterns

No type inference is performed - all types must be explicitly annotated.

## Project Structure

```
arafura/
├── src/
│   └── arafura/
│       ├── __init__.py       # Package exports
│       ├── transpiler.py     # Main transpiler implementation
│       └── cli.py            # Command-line interface
├── tests/
│   ├── fixtures/             # Test input files (.py)
│   ├── golden_outputs/       # Expected output files (.c)
│   ├── conftest.py          # Pytest configuration
│   ├── test_golden_master.py # Golden master tests
│   └── test_transpiler.py   # Unit tests
├── pyproject.toml           # Project metadata and dependencies
└── README.md
```

## Testing

Run all tests:

```bash
# Install dev dependencies first
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only golden master tests
pytest tests/test_golden_master.py

# Run only unit tests
pytest tests/test_transpiler.py
```

### Golden Master Tests

The project uses golden master testing to ensure transpiler output stability. Golden outputs are stored in `tests/golden_outputs/` and are compared against current transpiler output.

To regenerate golden outputs after intentional changes:

```bash
python -m scripts.regenerate_golden_outputs
```

## Design Philosophy

- **Python syntax, C semantics**: Write code that looks like Python but behaves like C
- **No magic**: Every construct has a clear, predictable mapping to C
- **Local transformation**: No global analysis or type inference needed
- **Explicit over implicit**: All types, casts, and operations must be explicit

## Limitations

- No Python runtime features (no garbage collection, no dynamic typing, etc.)
- Requires explicit type annotations
- Some C features may require verbose syntax
- Error messages reference Python AST, not C concepts

## License

See DESIGN.md for the complete language specification.
