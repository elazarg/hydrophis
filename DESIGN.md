Here’s a cleaned-up, self-consistent version of the design with your constraints baked in, and with the `while`/`for` parts fixed the way you asked.

---

# C with Python Syntax – Design Document

## 0. Overview

This language is **syntactically valid Python** (passes `ast.parse`) but has **C semantics**. A transpiler reads the Python AST and emits C. Python runtime behavior is irrelevant.

Core constraints:

1. Every file must parse with `ast.parse()`.
2. Semantics are C: primitive types, manual memory, UB, preprocessor, etc.
3. Translation decisions are **local** on the AST; there is **no type environment**.
4. `_` is **reserved** and used for address-of, deref, ++/--, compound literals, and pattern wildcards.
5. C-style `for` uses chained calls with **variables in the `for` target** and **types in the iterable**.
6. Do–while is encoded via a special `while ():` + trailing `if cond: continue` pattern.
7. Preprocessor conditionals are `if [expr]:`.
8. Macros vs variables vs functions are distinguished syntactically, not by runtime.

---

## 1. Types and Declarations

### 1.1 Basic Types

C types appear in annotations:

```python
x: int = 5          # int x = 5;
f: float = 3.14     # float f = 3.14;
c: char = 'a'       # char c = 'a';
d: double = 2.71828 # double d = 2.71828;
```

Direct mapping:

* `int`, `char`, `float`, `double`, `long`, `short`, `void` → same in C.

No inference; the transpiler prints what the annotation says.

### 1.2 Pointer Types

Unary minus in type position:

```python
p: -int        # int *p;
pp: --int      # int **pp;
cp: -char      # char *cp;
vp: -void      # void *vp;
```

Pattern: `UnaryOp(USub, type_expr)` → pointer to `type_expr`.

### 1.3 Array Types

Subscripted types:

```python
arr: int[10]           # int arr[10];
matrix: int[5][10]     # int matrix[5][10];
buf: char[256]         # char buf[256];
```

Nested subscripts → multidimensional arrays.

### 1.4 Pointer-to-Array Types

Unary `+` over an array type:

```python
p_arr: +int[10]        # int (*p_arr)[10];
p_mat: +int[5][10]     # int (*p_mat)[5][10];
```

### 1.5 Qualifiers and Storage Class on Types

Qualifiers as subscripts:

```python
x: const[int]          # const int x;
flag: volatile[int]    # volatile int flag;
u: unsigned[int]       # unsigned int u;

big: unsigned[long[long]]  # unsigned long long;
y: volatile[unsigned[int]] # volatile unsigned int;
```

Storage-like qualifiers on vars:

```python
gx: static[int] = 0    # static int gx = 0;
gy: extern[int]        # extern int gy;

def counter() -> int:
    count: static[int] = 0   # static int count = 0;
    count += 1
    return count
```

Purely syntactic: `NAME[TYPE]` → `NAME TYPE`.

### 1.6 Type Aliases (`typedef`)

Use `type`:

```python
type int_ptr = -int                 # typedef int *int_ptr;
type binop = int(int, int)          # typedef int (*binop)(int, int);
type byte = unsigned[char]          # typedef unsigned char byte;
```

---

## 2. Composite Types: Struct / Union / Enum

### 2.1 Structs

Class → struct:

```python
class Point:                        # struct Point {
    x: int                          #   int x;
    y: int                          #   int y;
                                    # };
```

Usage:

```python
p: Point                           # struct Point p;
p = Point(10, 20)                  # struct Point p = {10, 20};
p.x = 5                            # p.x = 5;
```

### 2.2 Nested Structs

```python
class Outer:
    value: int

    class Inner:
        x: int
        y: int

    inner: Inner
    other: Inner
```

→ `struct Outer { int value; struct Inner { ... }; struct Inner inner; struct Inner other; };`.

### 2.3 Struct Initialization

**Positional:**

```python
p: Point = Point(10, 20)           # struct Point p = {10, 20};
```

**Designated (in declaration):**

```python
p: Point(x=10, y=20)               # struct Point p = {.x = 10, .y = 20};
q: Point(x=5)                      # struct Point q = {.x = 5};
```

Annotation is `Call(func=Name('Point'), keywords=...)`.

**Compound literals via `_` (contextual type):**

```python
p: Point
p = _(x=10, y=20)                  # p = (struct Point){ .x = 10, .y = 20 };

items: Point[3] = [
    _(x=1, y=2),
    _(x=3, y=4),
    _(x=5, y=6),
]
```

`_(...)` is always “compound literal with designated fields”; the type is taken from the surrounding context (e.g., element type of the array).

### 2.4 Unions

```python
class Data(Union):                 # union Data {
    i: int                         #   int i;
    f: float                       #   float f;
    c: char                        #   char c;
                                   # };
d: Data
d.i = 42
```

### 2.5 Enums

```python
class Color(Enum):                 # enum Color {
    RED = 0                        #   RED = 0,
    GREEN = 1                      #   GREEN = 1,
    BLUE = 2                       #   BLUE = 2
                                   # };
```

Use bare constants:

```python
c: Color = RED                     # enum Color c = RED;
if c == GREEN:
    ...
```

The transpiler treats `RED`, `GREEN`, `BLUE` as enum constants; Python’s Enum runtime is ignored.

---

## 3. `_`: Address-of, Deref, ++/--, Compound Literals

`_` is **reserved**. It must not be used as a normal variable or function.

### 3.1 Address-of

`_.target` → `&target`:

```python
x: int = 5
px: -int = _.x                     # int *px = &x;

arr: int[10]
p0: -int = _.arr[0]                # int *p0 = &arr[0];
```

Pattern: `Attribute(value=Name('_'), attr=...)`.

### 3.2 Dereference

`expr._` → `*expr`:

```python
v: int = px._                      # int v = *px;
px._ = 10                          # *px = 10;
```

Chained:

```python
pp: --int = _.px                   # int **pp = &px;
pp._._ = 42                        # **pp = 42;
```

Pattern: `Attribute(expr, '_')`, nested as needed.

### 3.3 Pointer Member Access

No type-based guessing. Use `._.` explicitly:

```python
ptr: -Point = _.p                  # struct Point *ptr = &p;

ptr._.x = 10                       # ptr->x = 10;
ptr._.y = 20                       # ptr->y = 20;

p: Point
p.x = 3                            # p.x = 3;  (no pointer)
```

Rule:

* `p.x` → `p.x`
* `ptr._.x` → `ptr->x`

### 3.4 Increment / Decrement

Encode `++`/`--` with `_` and `**`/`//`:

| C     | Python   |
| ----- | -------- |
| `i++` | `i ** _` |
| `++i` | `_ ** i` |
| `i--` | `i // _` |
| `--i` | `_ // i` |

Examples:

```python
i: int = 0
i ** _                               # i++;
_ ** i                               # ++i;
i // _                               # i--;
_ // i                               # --i;

x: int = (i ** _)                    # x = i++;
arr[i ** _] = 5                      # arr[i++] = 5;
```

Pointer variants:

```python
ptr: -int = arr
ptr ** _                             # ptr++;
_ ** ptr                             # ++ptr;
```

And combined with deref:

```python
(ptr ** _)._                         # *ptr++;
(_ ** ptr)._                         # *(++ptr);
(ptr._) ** _                         # (*ptr)++;
_ ** (ptr._)                         # ++(*ptr);
```

### 3.5 Compound Literals via `_`

Already covered above: `_(field=value, ...)` is a compound literal with designated initializers at the contextual type.

---

## 4. Expressions and Operators

### 4.1 Arithmetic, Bitwise, Logical

* Arithmetic: `+`, `-`, `*`, `/`, `%`
* Bitwise: `&`, `|`, `^`, `~`, `<<`, `>>`
* Comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`
* Logical: `and`, `or`, `not` → `&&`, `||`, `!`

Pointer arithmetic is just normal `+` / `-` on pointer lvalues in the generated C.

### 4.2 Ternary

```python
y = a if x > 0 else b               # y = (x > 0) ? a : b;
```

### 4.3 Assignment / Walrus

Statement assignment:

```python
x = 5                               # x = 5;
```

Assignment in expressions uses `:=`:

```python
if (x := foo()):
    ...

while (c := getchar()):
    ...
```

### 4.4 Casts

Cast syntax: `[TYPE](expr)`:

```python
i: int = [int](3.14)                # (int)3.14;
p: -int = [-int](vp)                # (int *)vp;
c: char =                 # (char)65;
f: float = [float](i)               # (float)i;
pp: --int = [--int](something)      # (int **)(something);
```

Pattern: `Call(func=List([TYPE_EXPR]), args=[EXPR])`.

### 4.5 `sizeof`

Use a `sizeof` pseudo-function:

```python
s: int = sizeof(int)                # sizeof(int);
n: int = sizeof(x)                  # sizeof(x);
sp: int = sizeof(Point)             # sizeof(struct Point);
dp: int = sizeof(ptr._)             # sizeof(*ptr);
```

### 4.6 NULL

`None` is `NULL`:

```python
ptr: -int = None                    # int *ptr = NULL;
if ptr == None:
    ...
```

---

## 5. Control Flow

### 5.1 Runtime `if / elif / else`

Normal `if` is runtime C `if`:

```python
if x > 0:
    y = 1
elif x < 0:
    y = -1
else:
    y = 0
```

→ `if (...) { ... } else if (...) { ... } else { ... }`.

### 5.2 Preprocessor `if`: `if [expr]:`

Special form for **conditional compilation**:

```python
if [DEBUG]:
    printf("Debug\n")
```

→

```c
#ifdef DEBUG
    printf("Debug\n");
#endif
```

```python
if [not DEBUG]:
    ...
```

→

```c
#ifndef DEBUG
    ...
#endif
```

```python
if [DEBUG and LEVEL > 2]:
    ...
```

→

```c
#if DEBUG && LEVEL > 2
    ...
#endif
```

Rule: `If` whose `test` is a `List([expr])` is compiled as a preprocessor `#if/.../#endif`.

### 5.3 While

Standard while:

```python
while x < 10:
    x += 1
```

→ `while (x < 10) { x += 1; }`.

### 5.4 Do–While via `while ():` + final `if cond: continue`

A **do–while** loop:

```c
do {
    BODY;
} while (COND);
```

is encoded as:

```python
while ():
    # BODY...
    if COND:
        continue
```

Details:

* The test of the while is **exactly** `()` (empty tuple literal).
* The last statement in the body must be `if COND: continue`.
* The transpiler:

  * takes all statements in the body **except** that final `if` as `BODY`;
  * uses `COND` from that final `if` as the do–while condition.

So:

```python
while ():
    x: int = 0
    x ** _
    printf("%d\n", x)
    if x < 10:
        continue
```

→

```c
do {
    int x = 0;
    x++;
    printf("%d\n", x);
} while (x < 10);
```

Python semantics are irrelevant; this is just a recognizable AST pattern.

### 5.5 C-style `for` with Variables in Target, Types in Iterable

You want loop variables in the `for` binder, and **types** in the iterable.

A C `for (INIT; COND; STEP)` is encoded as:

```python
for VARS in TYPES(INIT)(COND)(STEP):
    BODY
```

* `VARS` is either a single name or a tuple of names (the actual loop variables).
* `TYPES` is either a single type expression or a tuple of type expressions.
* `INIT`, `COND`, `STEP` are expressions (can use `:=`, `**`, `//`, etc.).

#### Single variable example

```python
# C: for (int i = 0; i < 10; i++)
for i in int(i := 0)(i < 10)(i ** _):
    printf("%d\n", i)
```

* Target: `i`
* Iterable: `int(i := 0)(i < 10)(i ** _)`

  * `int` → type
  * `(i := 0)` → INIT
  * `(i < 10)` → COND
  * `(i ** _)` → STEP

#### Multiple variables

```python
# C: for (int i = 0, j = 10; i < 10; i++, j--)
for (i, j) in (int, int)((i := 0, j := 10))(i < 10)((i ** _, j // _)):
    printf("i=%d, j=%d\n", i, j)
```

* Target: `(i, j)`
* Types: `(int, int)`
* INIT: `(i := 0, j := 10)`
* COND: `i < 10`
* STEP: `(i ** _, j // _)`

#### Notes

* Types can be complex: `unsigned[int]`, `-int`, etc.:

  ```python
  for p in -int(p := arr)(p < arr + 10)(p ** _):
      ...
  ```

* The transpiler pattern-matches:

  * `For(target=VARS, iter=Call(Call(Call(TYPES, [INIT]), [COND]), [STEP]), body=...)`

and emits:

```c
TYPE_DECL VARS;    // with INIT folded into init clause
for (INIT; COND; STEP) {
    BODY
}
```

How you handle declarations vs initialization in detail is up to you, but syntactically the types live in the first call (`TYPES(...)`), and variables are in the `for` target.

### 5.6 Break / Continue

Same keywords:

```python
while True:
    if done:
        break
    if skip:
        continue
```

### 5.7 Goto and Labels

Labels:

```python
LOOP: label                         # LOOP:
```

Goto:

```python
raise LOOP                          # goto LOOP;
```

Example:

```python
def sum_to(n: int) -> int:
    i: int = 0
    s: int = 0

    LOOP: label
    if i > n:
        raise END
    s += i
    i ** _
    raise LOOP

    END: label
    return s
```

---

## 6. Functions and Function Pointers

### 6.1 Functions vs Macros (`def`)

Rule:

* A `def` is a **C function** iff it has:

  * a return annotation (`-> T`), and
  * **all parameters annotated**.
* A `def` is a **macro** iff:

  * it has **no** return annotation,
  * and **no** parameter annotations.

Everything else is invalid (or reserved) in this design.

Examples:

```python
def add(a: int, b: int) -> int:     # function: int add(int a, int b)
    return a + b

def MAX(a, b):                      # macro: #define MAX(a,b) ...
    a if a > b else b
```

### 6.2 Function Pointers

Type annotations:

```python
fptr: int(int, int)                 # int (*fptr)(int, int);
cb: void(-char)                     # void (*cb)(char *);
cmp: int(-void, -void)              # int (*cmp)(void *, void *);
noarg: int()                        # int (*noarg)(void);
```

Usage:

```python
fptr = add                          # fptr = add;
r: int = fptr(5, 3)                 # int r = fptr(5,3);
r2: int = (fptr._)(5, 3)            # int r2 = (*fptr)(5,3);
```

---

## 7. Macros, Variables, Includes

### 7.1 Constant Macros vs Variables

Top-level annotated assignment:

* Variables: `NAME: TYPE = EXPR` with `TYPE != macro`.
* Macros: `NAME: macro = EXPR`.

Examples:

```python
MAX_SIZE: int = 100                 # int MAX_SIZE = 100;    (real variable)

MAX_SIZE: macro = 100               # #define MAX_SIZE 100
PI: macro = 3.14159                 # #define PI 3.14159
NULL_PTR: macro = None              # #define NULL_PTR NULL
```

Pattern:

* `AnnAssign(Name, annotation=Name('macro'), value=expr)` → `#define NAME EXPR`.
* Anything else with `annotation != macro` → normal C variable definition.

### 7.2 Function-like Macros (`def` without annotations)

As above: a `def` with **no** return annotation and **no** parameter annotations is a macro.

Examples:

```python
def MAX(a, b):                      # #define MAX(a,b) ((a)>(b)?(a):(b))
    a if a > b else b

def SQUARE(x):                      # #define SQUARE(x) ((x)*(x))
    x * x

def SWAP(a, b):                     # multi-statement macro
    temp = a
    a = b
    b = temp
```

Variadic macro:

```python
def LOG(fmt, *args):                # #define LOG(fmt, ...) ...
    printf("[LOG] " + fmt + "\n", __VA_ARGS__)
```

The transpiler:

* Treats parameters as macro formals; `*args` → `...`.
* Rewrites `__VA_ARGS__` in the body to C `__VA_ARGS__`.

### 7.3 Includes

Mapping:

* `import stdio` → `#include "stdio.h"`
* `from stdio import *` → `#include <stdio.h>`

Examples:

```python
import stdio                        # #include "stdio.h"
from stdio import *                 # #include <stdio.h>
```

Usage:

```python
from stdio import *

printf("hello\n")
```

### 7.4 Preprocessor Conditionals

As already specified: `if [expr]:` around a block → `#if expr` / `#endif`.

---

## 8. Arrays, Memory, Strings

### 8.1 Arrays

```python
arr: int[10]                        # int arr[10];

arr: int[5] = [1, 2, 3, 4, 5]      # int arr[5] = {1,2,3,4,5};

arr: int[10] = {0: 1, 5: 6, 9: 10}
# int arr[10] = { [0] = 1, [5] = 6, [9] = 10 };
```

Multi-dim:

```python
matrix: int[2][3] = [
    [1, 2, 3],
    [4, 5, 6],
]

matrix[1][2] = 42
```

Array decay:

```python
arr: int[10]
p: -int = arr                       # int *p = arr;
q: -int = _.arr[0]                  # int *q = &arr[0];
```

### 8.2 Memory Management

```python
from stdlib import *

p: -int = malloc(sizeof(int))                  # int *p = malloc(sizeof(int));
p._ = 42                                       # *p = 42;
free(p)                                        # free(p);

arr: -int = malloc(10 * sizeof(int))           # int *arr = malloc(10*sizeof(int));
arr[0] = 1

arr2: -int = calloc(10, sizeof(int))           # int *arr2 = calloc(10,sizeof(int));
arr2 = realloc(arr2, 20 * sizeof(int))         # arr2 = realloc(arr2,20*sizeof(int));

if arr2 == None:
    return -1
```

### 8.3 Strings

```python
s: -char = "hello"                 # char *s = "hello";
buf: char[100] = "init"            # char buf[100] = "init";
```

With string functions:

```python
from string import *

len: int = strlen(s)
strcpy(buf, s)
```

---

## 9. Small End-to-End Example

```python
from stdio import *
from stdlib import *

MAX_SIZE: macro = 100              # #define MAX_SIZE 100

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

def print_list(head: -Node) -> void:
    curr: -Node = head
    while curr != None:
        printf("%d ", curr._.data)
        curr = curr._.next
    printf("\n")

def MAX(a, b):                     # macro
    a if a > b else b

def main() -> int:                 # function
    head: -Node = create_node(1)
    head._.next = create_node(2)
    head._.next._.next = create_node(3)

    print_list(head)

    # C-style for: for (int i = 0, j = 10; i < 5; i++, j--)
    for (i, j) in (int, int)((i := 0, j := 10))(i < 5)((i ** _, j // _)):
        printf("i=%d, j=%d\n", i, j)

    # do { ... } while (i < 10);
    while ():
        i ** _
        printf("i=%d\n", i)
        if i < 10:
            continue

    return 0
```

This is all valid Python syntax, but the semantics and code generation are entirely C.
