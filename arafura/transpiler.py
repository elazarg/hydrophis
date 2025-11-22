#!/usr/bin/env python3
"""
Transpiler from "C as Python" to C.
Converts syntactically valid Python (parseable by ast.parse) into C code.
"""

import ast
import sys


class CTranspiler(ast.NodeVisitor):
    """Transpiles Python AST to C code."""

    def __init__(self):
        self.indent_level = 0
        self.output = []
        self.context_type = None  # For compound literals with _
        self.struct_types = set()  # Track struct names
        self.union_types = set()   # Track union names
        self.enum_types = set()    # Track enum names

    def indent(self) -> str:
        """Return current indentation."""
        return "    " * self.indent_level

    def emit(self, code: str):
        """Emit a line of C code."""
        self.output.append(code)

    def get_output(self) -> str:
        """Get the final C code."""
        return "\n".join(self.output)

    # ========================================================================
    # TYPE EMISSION
    # ========================================================================

    def emit_type(self, node: ast.AST, var_name: str = "") -> str:
        """
        Emit a C type declaration.
        Returns the C type string with var_name positioned correctly.

        Examples:
        - int -> "int"
        - -int -> "int *"
        - int[10] -> "int[10]"
        - int(int, int) -> "int (*)(int, int)"
        - type[F] -> "struct F" or "F" (if typedef'd)
        """
        if isinstance(node, ast.Name):
            # Basic type: int, char, float, double, void, etc.
            # Bare names are used as-is (could be typedef names or basic types)
            type_name = node.id
            if var_name:
                return f"{type_name} {var_name}"
            else:
                return type_name

        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            # Pointer type: -int -> int *
            # Get inner type without var_name
            inner = self.emit_type(node.operand, "")

            if var_name:
                # For declarations like "int *px" or "int **pp"
                # Count how many trailing '*' the inner has
                star_count = len(inner) - len(inner.rstrip('*'))
                if star_count > 0:
                    # Inner like "int*" or "int**" - extract base and add stars before var_name
                    base = inner.rstrip('*')
                    stars = '*' * (star_count + 1)
                    return f"{base} {stars}{var_name}"
                else:
                    # Inner like "int" - simple case
                    return f"{inner} *{var_name}"
            else:
                # For types without var_name like function pointer params
                return f"{inner}*"

        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
            # Pointer-to-array: +int[10] -> int (*)[10]
            if isinstance(node.operand, ast.Subscript):
                elem_type = self.emit_type(node.operand.value, "")
                dims = self.collect_array_dimensions(node.operand)
                dim_str = "".join(f"[{self.emit_expr(d)}]" for d in dims)
                return f"{elem_type}(*{var_name}){dim_str}".strip()
            else:
                raise ValueError(f"Invalid pointer-to-array type: {ast.dump(node)}")

        elif isinstance(node, ast.Subscript):
            # Could be array type, qualifier, or type[F]
            if isinstance(node.value, ast.Name):
                name = node.value.id

                # Special case: type[F] (structs), union[F], enum[F]
                if name in ('type', 'union', 'enum'):
                    inner_name = node.slice.id if isinstance(node.slice, ast.Name) else None
                    if inner_name:
                        # type[F] -> "struct F"
                        # union[F] -> "union F"
                        # enum[F] -> "enum F"
                        if name == 'union':
                            type_str = f"union {inner_name}"
                        elif name == 'enum':
                            type_str = f"enum {inner_name}"
                        else:  # type
                            type_str = f"struct {inner_name}"

                        if var_name:
                            return f"{type_str} {var_name}"
                        else:
                            return type_str

                # Check if it's a qualifier/storage class
                if name in ('const', 'volatile', 'unsigned', 'static', 'extern', 'long'):
                    # Qualifier: const[int] -> const int
                    inner_type = self.emit_type(node.slice, var_name)
                    return f"{name} {inner_type}".strip()
                else:
                    # Array type: int[10] -> int[10]
                    dims = self.collect_array_dimensions(node)
                    elem_type = node.value
                    # Walk back to get the element type
                    while isinstance(elem_type, ast.Subscript):
                        elem_type = elem_type.value
                    base = self.emit_type(elem_type, var_name)
                    dim_str = "".join(f"[{self.emit_expr(d)}]" for d in dims)
                    return f"{base}{dim_str}".strip()
            elif isinstance(node.value, ast.Subscript):
                # Nested qualifier or array
                # Check if outer is a qualifier
                if isinstance(node.value.value, ast.Name) and node.value.value.id in ('const', 'volatile', 'unsigned', 'static', 'extern', 'long'):
                    # volatile[unsigned[int]] -> volatile unsigned int
                    inner = self.emit_type(node.value, "")
                    final_type = self.emit_type(node.slice, var_name)
                    return f"{inner} {final_type}".strip()
                # Check if outer is type[], enum[], or union[] (e.g., type[Point][3])
                elif isinstance(node.value.value, ast.Name) and node.value.value.id in ('type', 'enum', 'union'):
                    # Array of type[F]/enum[E]/union[U]
                    # node.value is type[Point], node.slice is 3
                    base_type = self.emit_type(node.value, "")  # Get "struct Point"
                    # Collect array dimensions (everything after type[Point])
                    dims = [node.slice]
                    # Check if there are more dimensions (e.g., type[Point][3][4])
                    # This is rare but possible
                    dim_str = "".join(f"[{self.emit_expr(d)}]" for d in dims)
                    if var_name:
                        return f"{base_type} {var_name}{dim_str}".strip()
                    else:
                        return f"{base_type}{dim_str}".strip()
                else:
                    # Array of arrays
                    dims = self.collect_array_dimensions(node)
                    elem_type = node.value
                    while isinstance(elem_type, ast.Subscript):
                        elem_type = elem_type.value
                    base = self.emit_type(elem_type, var_name)
                    dim_str = "".join(f"[{self.emit_expr(d)}]" for d in dims)
                    return f"{base}{dim_str}".strip()
            else:
                raise ValueError(f"Unhandled subscript type: {ast.dump(node)}")

        elif isinstance(node, ast.Call):
            # Function pointer type: int(int, int) -> int (*)(int, int)
            ret_type = self.emit_type(node.func, "")
            param_types = ", ".join(self.emit_type(arg, "") for arg in node.args)
            if not param_types:
                param_types = "void"
            if var_name:
                return f"{ret_type}(*{var_name})({param_types})".strip()
            else:
                return f"{ret_type}(*)({param_types})".strip()

        else:
            raise ValueError(f"Unhandled type node: {ast.dump(node)}")

    @staticmethod
    def collect_array_dimensions(node: ast.Subscript) -> list[ast.AST]:
        """Collect array dimensions in order: int[5][10] -> [5, 10]"""
        dims = []
        current = node
        while isinstance(current, ast.Subscript):
            dims.insert(0, current.slice)
            current = current.value
        return dims

    # ========================================================================
    # EXPRESSION EMISSION
    # ========================================================================

    def emit_expr(self, node: ast.AST) -> str:
        """Emit a C expression."""
        if isinstance(node, ast.Constant):
            return self.emit_constant(node)

        elif isinstance(node, ast.Name):
            if node.id == 'None':
                return 'NULL'
            elif node.id == 'True':
                return '1'
            elif node.id == 'False':
                return '0'
            else:
                return node.id

        elif isinstance(node, ast.BinOp):
            return self.emit_binop(node)

        elif isinstance(node, ast.UnaryOp):
            return self.emit_unaryop(node)

        elif isinstance(node, ast.Compare):
            return self.emit_compare(node)

        elif isinstance(node, ast.BoolOp):
            return self.emit_boolop(node)

        elif isinstance(node, ast.IfExp):
            # Ternary: a if cond else b -> (cond) ? a : b
            cond = self.emit_expr(node.test)
            true_val = self.emit_expr(node.body)
            false_val = self.emit_expr(node.orelse)
            return f"({cond} ? {true_val} : {false_val})"

        elif isinstance(node, ast.Call):
            return self.emit_call(node)

        elif isinstance(node, ast.Attribute):
            return self.emit_attribute(node)

        elif isinstance(node, ast.Subscript):
            return self.emit_subscript(node)

        elif isinstance(node, ast.List):
            # Array initializer or cast
            if len(node.elts) == 1:
                # Might be a cast: [int](expr)
                # This is handled in emit_call
                pass
            # Array literal: [1, 2, 3] -> {1, 2, 3}
            elts = ", ".join(self.emit_expr(e) for e in node.elts)
            return f"{{{elts}}}"

        elif isinstance(node, ast.Dict):
            # Designated initializer: {0: 1, 5: 6} -> {[0] = 1, [5] = 6}
            items = []
            for k, v in zip(node.keys, node.values):
                key_str = self.emit_expr(k)
                val_str = self.emit_expr(v)
                items.append(f"[{key_str}] = {val_str}")
            return f"{{{', '.join(items)}}}"

        elif isinstance(node, ast.Tuple):
            # Tuple for multiple expressions (used in for loops, etc.)
            return ", ".join(self.emit_expr(e) for e in node.elts)

        elif isinstance(node, ast.NamedExpr):
            # Walrus operator: (x := 5) -> (x = 5)
            target = self.emit_expr(node.target)
            value = self.emit_expr(node.value)
            return f"({target} = {value})"

        else:
            raise ValueError(f"Unhandled expression: {ast.dump(node)}")

    def emit_constant(self, node: ast.Constant) -> str:
        """Emit a constant value."""
        if isinstance(node.value, bool):
            # Check bool before int since bool is subclass of int
            return '1' if node.value else '0'
        elif isinstance(node.value, str):
            # String literal - escape properly
            escaped = (node.value
                      .replace('\\', '\\\\')
                      .replace('"', '\\"')
                      .replace('\n', '\\n')
                      .replace('\r', '\\r')
                      .replace('\t', '\\t'))
            return f'"{escaped}"'
        elif isinstance(node.value, int):
            return str(node.value)
        elif isinstance(node.value, float):
            return str(node.value)
        elif node.value is None:
            return 'NULL'
        else:
            return str(node.value)

    def emit_binop(self, node: ast.BinOp) -> str:
        """Emit binary operation."""
        left = self.emit_expr(node.left)
        right = self.emit_expr(node.right)

        # Check for increment/decrement patterns
        if isinstance(node.op, ast.Pow):
            # ** is used for increment
            if isinstance(node.right, ast.Name) and node.right.id == '_':
                # i ** _ -> i++
                return f"{left}++"
            elif isinstance(node.left, ast.Name) and node.left.id == '_':
                # _ ** i -> ++i
                return f"++{right}"

        elif isinstance(node.op, ast.FloorDiv):
            # // is used for decrement
            if isinstance(node.right, ast.Name) and node.right.id == '_':
                # i // _ -> i--
                return f"{left}--"
            elif isinstance(node.left, ast.Name) and node.left.id == '_':
                # _ // i -> --i
                return f"--{right}"

        # Regular binary operators
        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.BitAnd: '&',
            ast.BitOr: '|',
            ast.BitXor: '^',
            ast.LShift: '<<',
            ast.RShift: '>>',
            ast.FloorDiv: '/',  # Normal division in C
            ast.Pow: '**',  # Should not reach here if inc/dec handled
        }

        op_str = op_map.get(type(node.op))
        if op_str:
            return f"({left} {op_str} {right})"
        else:
            raise ValueError(f"Unhandled binary operator: {type(node.op)}")

    def emit_unaryop(self, node: ast.UnaryOp) -> str:
        """Emit unary operation."""
        operand = self.emit_expr(node.operand)

        op_map = {
            ast.Not: '!',
            ast.Invert: '~',
            ast.UAdd: '+',
            ast.USub: '-',
        }

        op_str = op_map.get(type(node.op))
        if op_str:
            return f"{op_str}{operand}"
        else:
            raise ValueError(f"Unhandled unary operator: {type(node.op)}")

    def emit_compare(self, node: ast.Compare) -> str:
        """Emit comparison."""
        left = self.emit_expr(node.left)

        op_map = {
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
        }

        parts = [left]
        for op, comparator in zip(node.ops, node.comparators):
            op_str = op_map.get(type(op))
            if op_str:
                comp = self.emit_expr(comparator)
                parts.append(op_str)
                parts.append(comp)
            else:
                raise ValueError(f"Unhandled comparison operator: {type(op)}")

        return " ".join(parts)

    def emit_boolop(self, node: ast.BoolOp) -> str:
        """Emit boolean operation (and/or)."""
        op_map = {
            ast.And: '&&',
            ast.Or: '||',
        }

        op_str = op_map.get(type(node.op))
        if not op_str:
            raise ValueError(f"Unhandled boolean operator: {type(node.op)}")

        values = [f"({self.emit_expr(v)})" for v in node.values]
        return f"({op_str.join(values)})"

    def emit_call(self, node: ast.Call) -> str:
        """Emit function call."""
        # Check for special forms

        # Cast: [TYPE](expr)
        if isinstance(node.func, ast.List) and len(node.func.elts) == 1:
            type_expr = node.func.elts[0]
            if len(node.args) == 1:
                type_str = self.emit_type(type_expr, "")
                expr_str = self.emit_expr(node.args[0])
                return f"(({type_str})({expr_str}))"

        # sizeof(...)
        if isinstance(node.func, ast.Name) and node.func.id == 'sizeof':
            if len(node.args) == 1:
                arg = node.args[0]
                # Emit the type as-is using emit_type
                # This respects type[F], enum[E], union[U] syntax
                if isinstance(arg, ast.Name):
                    # Simple name - emit as-is (could be typedef or basic type)
                    return f"sizeof({arg.id})"
                elif isinstance(arg, ast.Subscript):
                    # Could be type[F], enum[E], union[U], or array type
                    type_str = self.emit_type(arg, "")
                    return f"sizeof({type_str})"
                else:
                    # Expression like sizeof(ptr._) or sizeof(arr[0])
                    arg_str = self.emit_expr(arg)
                    return f"sizeof({arg_str})"

        # Compound literal with _: _(x=1, y=2)
        if isinstance(node.func, ast.Name) and node.func.id == '_':
            if node.keywords:
                # Designated initializer compound literal
                items = []
                for kw in node.keywords:
                    val = self.emit_expr(kw.value)
                    items.append(f".{kw.arg} = {val}")
                init_str = "{" + ", ".join(items) + "}"
                # Need context type - for now, emit generic form
                # In a real implementation, we'd track the expected type
                return f"({init_str})"

        # Struct constructor: Point(10, 20) or Point(x=10, y=20)
        if isinstance(node.func, ast.Name) and node.func.id in self.struct_types:
            if node.keywords:
                # Designated initializer
                items = []
                for kw in node.keywords:
                    val = self.emit_expr(kw.value)
                    items.append(f".{kw.arg} = {val}")
                init_str = "{" + ", ".join(items) + "}"
                return init_str
            else:
                # Positional initializer
                args_str = ", ".join(self.emit_expr(arg) for arg in node.args)
                return f"{{{args_str}}}"

        # Regular function call
        func_name = self.emit_expr(node.func)
        args_str = ", ".join(self.emit_expr(arg) for arg in node.args)
        return f"{func_name}({args_str})"

    def emit_attribute(self, node: ast.Attribute) -> str:
        """Emit attribute access."""
        # Check for special _ forms

        # Address-of: _.x -> &x
        if isinstance(node.value, ast.Name) and node.value.id == '_':
            return f"&{node.attr}"

        # Dereference: ptr._ -> *ptr
        if node.attr == '_':
            value = self.emit_expr(node.value)
            return f"(*{value})"

        # Pointer member access: ptr._.x
        # Need to check if value is ptr._
        if isinstance(node.value, ast.Attribute) and node.value.attr == '_':
            # ptr._.x -> ptr->x
            ptr = self.emit_expr(node.value.value)
            return f"{ptr}->{node.attr}"

        # Regular member access: p.x -> p.x
        value = self.emit_expr(node.value)
        return f"{value}.{node.attr}"

    def emit_subscript(self, node: ast.Subscript) -> str:
        """Emit subscript (array access)."""
        value = self.emit_expr(node.value)
        index = self.emit_expr(node.slice)
        return f"{value}[{index}]"

    # ========================================================================
    # STATEMENT EMISSION
    # ========================================================================

    def visit_Module(self, node: ast.Module):
        """Visit module (top level)."""
        # First pass: collect all type names
        for stmt in node.body:
            if isinstance(stmt, ast.ClassDef):
                is_union = any(isinstance(base, ast.Name) and base.id == 'Union' for base in stmt.bases)
                is_enum = any(isinstance(base, ast.Name) and base.id == 'Enum' for base in stmt.bases)
                if is_union:
                    self.union_types.add(stmt.name)
                elif is_enum:
                    self.enum_types.add(stmt.name)
                else:
                    self.struct_types.add(stmt.name)

        # Second pass: emit code
        for stmt in node.body:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import):
        """Handle import: import stdio -> #include "stdio.h" """
        for alias in node.names:
            self.emit(f'#include "{alias.name}.h"')

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from ... import: from stdio import * -> #include <stdio.h>"""
        if node.names[0].name == '*':
            self.emit(f'#include <{node.module}.h>')
        else:
            # Partial imports - treat as regular include
            self.emit(f'#include "{node.module}.h"')

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Handle annotated assignment (variable declaration)."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id

            # Check if it's a label
            if isinstance(node.annotation, ast.Name) and node.annotation.id == 'label':
                # Label: NAME: label -> NAME:
                self.emit(f"{var_name}:")
                return

            # Check if it's a macro
            if isinstance(node.annotation, ast.Name) and node.annotation.id == 'macro':
                # Constant macro: NAME: macro = VALUE
                value = self.emit_expr(node.value)
                self.emit(f"{self.indent()}#define {var_name} {value}")
            else:
                # Check if annotation is a Call with keywords (designated initializer)
                if isinstance(node.annotation, ast.Call) and node.annotation.keywords:
                    # Point(x=10, y=20) -> struct Point p = {.x = 10, .y = 20};
                    struct_name = node.annotation.func.id if isinstance(node.annotation.func, ast.Name) else "Unknown"
                    items = []
                    for kw in node.annotation.keywords:
                        val = self.emit_expr(kw.value)
                        items.append(f".{kw.arg} = {val}")
                    init_str = "{" + ", ".join(items) + "}"
                    self.emit(f"{self.indent()}struct {struct_name} {var_name} = {init_str};")
                else:
                    # Regular variable declaration
                    type_decl = self.emit_type(node.annotation, var_name)
                    if node.value:
                        value = self.emit_expr(node.value)
                        self.emit(f"{self.indent()}{type_decl} = {value};")
                    else:
                        self.emit(f"{self.indent()}{type_decl};")

    def visit_Assign(self, node: ast.Assign):
        """Handle assignment."""
        for target in node.targets:
            target_str = self.emit_expr(target)
            value_str = self.emit_expr(node.value)
            self.emit(f"{self.indent()}{target_str} = {value_str};")

    def visit_AugAssign(self, node: ast.AugAssign):
        """Handle augmented assignment: x += 1"""
        target = self.emit_expr(node.target)
        value = self.emit_expr(node.value)

        op_map = {
            ast.Add: '+=',
            ast.Sub: '-=',
            ast.Mult: '*=',
            ast.Div: '/=',
            ast.Mod: '%=',
            ast.BitAnd: '&=',
            ast.BitOr: '|=',
            ast.BitXor: '^=',
            ast.LShift: '<<=',
            ast.RShift: '>>=',
        }

        op_str = op_map.get(type(node.op))
        if op_str:
            self.emit(f"{self.indent()}{target} {op_str} {value};")
        else:
            raise ValueError(f"Unhandled augmented assignment operator: {type(node.op)}")

    def visit_Expr(self, node: ast.Expr):
        """Handle expression statement."""
        expr_str = self.emit_expr(node.value)
        self.emit(f"{self.indent()}{expr_str};")

    def visit_If(self, node: ast.If):
        """Handle if statement."""
        # Check for preprocessor conditional: if [expr]:
        if isinstance(node.test, ast.List) and len(node.test.elts) == 1:
            # Preprocessor conditional
            cond_expr = node.test.elts[0]

            # Determine #ifdef, #ifndef, or #if
            if isinstance(cond_expr, ast.Name):
                self.emit(f"{self.indent()}#ifdef {cond_expr.id}")
            elif isinstance(cond_expr, ast.UnaryOp) and isinstance(cond_expr.op, ast.Not):
                if isinstance(cond_expr.operand, ast.Name):
                    self.emit(f"{self.indent()}#ifndef {cond_expr.operand.id}")
                else:
                    cond_str = self.emit_expr(cond_expr)
                    self.emit(f"{self.indent()}#if {cond_str}")
            else:
                cond_str = self.emit_expr(cond_expr)
                self.emit(f"{self.indent()}#if {cond_str}")

            # Body
            for stmt in node.body:
                self.visit(stmt)

            self.emit(f"{self.indent()}#endif")
        else:
            # Regular if statement
            self.emit_if_chain(node)

    def emit_if_chain(self, node: ast.If):
        """Recursively emit if-elif-else chain."""
        cond = self.emit_expr(node.test)
        self.emit(f"{self.indent()}if ({cond}) {{")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

        # Handle orelse
        self.emit_orelse(node.orelse)

    def emit_orelse(self, orelse_stmts):
        """Emit else or elif chain."""
        if not orelse_stmts:
            self.emit(f"{self.indent()}}}")
            return

        if len(orelse_stmts) == 1 and isinstance(orelse_stmts[0], ast.If):
            # elif
            elif_node = orelse_stmts[0]
            elif_cond = self.emit_expr(elif_node.test)
            self.emit(f"{self.indent()}}} else if ({elif_cond}) {{")
            self.indent_level += 1
            for stmt in elif_node.body:
                self.visit(stmt)
            self.indent_level -= 1
            # Recursively handle the rest
            self.emit_orelse(elif_node.orelse)
        else:
            # else block
            self.emit(f"{self.indent()}}} else {{")
            self.indent_level += 1
            for stmt in orelse_stmts:
                self.visit(stmt)
            self.indent_level -= 1
            self.emit(f"{self.indent()}}}")

    def visit_While(self, node: ast.While):
        """Handle while statement."""
        # Check for do-while: while ():
        if isinstance(node.test, ast.Tuple) and len(node.test.elts) == 0:
            # Do-while loop
            # Last statement should be: if COND: continue
            if node.body and isinstance(node.body[-1], ast.If):
                last_if = node.body[-1]
                if (len(last_if.body) == 1 and
                    isinstance(last_if.body[0], ast.Continue) and
                    not last_if.orelse):
                    # Valid do-while
                    cond = self.emit_expr(last_if.test)
                    body_stmts = node.body[:-1]

                    self.emit(f"{self.indent()}do {{")
                    self.indent_level += 1
                    for stmt in body_stmts:
                        self.visit(stmt)
                    self.indent_level -= 1
                    self.emit(f"{self.indent()}}} while ({cond});")
                    return

            # If we reach here, it's malformed
            raise ValueError("Malformed do-while: while () must end with 'if COND: continue'")

        # Regular while loop
        cond = self.emit_expr(node.test)
        self.emit(f"{self.indent()}while ({cond}) {{")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.emit(f"{self.indent()}}}")

    def visit_For(self, node: ast.For):
        """Handle for statement (C-style for loop)."""
        # Pattern: for VARS in TYPES(INIT)(COND)(STEP):
        # Iterable is Call(Call(Call(TYPES, [INIT]), [COND]), [STEP])

        if isinstance(node.iter, ast.Call):
            # Try to match the pattern
            step_call = node.iter
            if isinstance(step_call.func, ast.Call):
                cond_call = step_call.func
                if isinstance(cond_call.func, ast.Call):
                    init_call = cond_call.func

                    # Extract components
                    types = init_call.func
                    init_expr = init_call.args[0] if init_call.args else None
                    cond_expr = cond_call.args[0] if cond_call.args else None
                    step_expr = step_call.args[0] if step_call.args else None

                    # Extract variables
                    if isinstance(node.target, ast.Tuple):
                        var_names = [elt.id for elt in node.target.elts if isinstance(elt, ast.Name)]
                        if isinstance(types, ast.Tuple):
                            type_exprs = types.elts
                        else:
                            type_exprs = [types] * len(var_names)
                    else:
                        var_names = [node.target.id]
                        type_exprs = [types]

                    # Emit declarations
                    # for (int i = 0, j = 10; i < 10; i++, j--)

                    # Build init clause
                    init_parts = []
                    if init_expr:
                        # Handle tuple of assignments or single assignment
                        if isinstance(init_expr, ast.Tuple):
                            for i, (var, typ, init_item) in enumerate(zip(var_names, type_exprs, init_expr.elts)):
                                if isinstance(init_item, ast.NamedExpr):
                                    val = self.emit_expr(init_item.value)
                                    type_str = self.emit_type(typ, "")
                                    if i == 0:
                                        init_parts.append(f"{type_str} {var} = {val}")
                                    else:
                                        init_parts.append(f"{var} = {val}")
                        else:
                            # Single variable
                            if isinstance(init_expr, ast.NamedExpr):
                                val = self.emit_expr(init_expr.value)
                                type_str = self.emit_type(type_exprs[0], "")
                                init_parts.append(f"{type_str} {var_names[0]} = {val}")

                    init_str = ", ".join(init_parts)
                    cond_str = self.emit_expr(cond_expr) if cond_expr else ""
                    step_str = self.emit_expr(step_expr) if step_expr else ""

                    self.emit(f"{self.indent()}for ({init_str}; {cond_str}; {step_str}) {{")
                    self.indent_level += 1
                    for stmt in node.body:
                        self.visit(stmt)
                    self.indent_level -= 1
                    self.emit(f"{self.indent()}}}")
                    return

        raise ValueError(f"Invalid for loop pattern: {ast.dump(node)}")

    def visit_Break(self, node: ast.Break):
        """Handle break statement."""
        self.emit(f"{self.indent()}break;")

    def visit_Continue(self, node: ast.Continue):
        """Handle continue statement."""
        self.emit(f"{self.indent()}continue;")

    def visit_Return(self, node: ast.Return):
        """Handle return statement."""
        if node.value:
            value = self.emit_expr(node.value)
            self.emit(f"{self.indent()}return {value};")
        else:
            self.emit(f"{self.indent()}return;")

    def visit_Raise(self, node: ast.Raise):
        """Handle raise (goto)."""
        if node.exc and isinstance(node.exc, ast.Name):
            label = node.exc.id
            self.emit(f"{self.indent()}goto {label};")
        else:
            raise ValueError(f"Invalid goto pattern: {ast.dump(node)}")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definition or macro."""
        # Determine if it's a function or macro
        has_return_annotation = node.returns is not None
        has_param_annotations = all(arg.annotation is not None for arg in node.args.args)

        if has_return_annotation and has_param_annotations:
            # C function
            self.emit_function(node)
        elif not has_return_annotation and not has_param_annotations:
            # Macro
            self.emit_macro(node)
        else:
            raise ValueError(f"Invalid function/macro definition: {node.name}")

    def emit_function(self, node: ast.FunctionDef):
        """Emit a C function."""
        func_name = node.name
        ret_type = self.emit_type(node.returns, "")

        # Parameters
        params = []
        for arg in node.args.args:
            param_type = self.emit_type(arg.annotation, arg.arg)
            params.append(param_type)

        if not params:
            params_str = "void"
        else:
            params_str = ", ".join(params)

        self.emit(f"{self.indent()}{ret_type} {func_name}({params_str}) {{")
        self.indent_level += 1

        for stmt in node.body:
            self.visit(stmt)

        self.indent_level -= 1
        self.emit(f"{self.indent()}}}")

    def emit_macro(self, node: ast.FunctionDef):
        """Emit a C macro."""
        macro_name = node.name

        # Parameters
        params = []
        has_varargs = False
        for arg in node.args.args:
            params.append(arg.arg)

        if node.args.vararg:
            has_varargs = True

        params_str = ", ".join(params)
        if has_varargs:
            if params_str:
                params_str += ", ..."
            else:
                params_str = "..."

        # Macro body
        # For single expression, emit it directly
        # For multiple statements, emit as multi-line macro
        if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
            body_expr = self.emit_expr(node.body[0].value)
            self.emit(f"{self.indent()}#define {macro_name}({params_str}) ({body_expr})")
        else:
            # Multi-statement macro (using do-while(0) pattern)
            self.emit(f"{self.indent()}#define {macro_name}({params_str}) do {{ \\")
            self.indent_level += 1
            for stmt in node.body:
                # Emit statement
                saved_output = self.output
                self.output = []
                self.visit(stmt)
                for line in self.output:
                    saved_output.append(line + " \\")
                self.output = saved_output
            self.indent_level -= 1
            self.emit(f"{self.indent()}}} while(0)")

    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definition (struct/union/enum)."""
        class_name = node.name

        # Check base classes to determine type
        is_union = any(isinstance(base, ast.Name) and base.id == 'Union' for base in node.bases)
        is_enum = any(isinstance(base, ast.Name) and base.id == 'Enum' for base in node.bases)

        # Check decorators for @typedef and @var
        has_typedef = False
        typedef_name = None
        var_names = []

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id == 'typedef':
                        # @typedef(Name)
                        has_typedef = True
                        if decorator.args and isinstance(decorator.args[0], ast.Name):
                            typedef_name = decorator.args[0].id
                    elif decorator.func.id == 'var':
                        # @var(a, b, c)
                        var_names = [arg.id for arg in decorator.args if isinstance(arg, ast.Name)]

        # Record the type
        if is_union:
            self.union_types.add(class_name)
            composite_type = "union"
        elif is_enum:
            self.enum_types.add(class_name)
            composite_type = "enum"
        else:
            self.struct_types.add(class_name)
            composite_type = "struct"

        if is_enum:
            # Enum
            if has_typedef:
                self.emit(f"{self.indent()}typedef enum {class_name} {{")
            else:
                self.emit(f"{self.indent()}enum {class_name} {{")
            self.indent_level += 1

            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) or isinstance(stmt, ast.Assign):
                    if isinstance(stmt, ast.AnnAssign):
                        name = stmt.target.id
                        value = self.emit_expr(stmt.value) if stmt.value else None
                    else:
                        name = stmt.targets[0].id
                        value = self.emit_expr(stmt.value)

                    if value:
                        self.emit(f"{self.indent()}{name} = {value},")
                    else:
                        self.emit(f"{self.indent()}{name},")

            self.indent_level -= 1

            # Emit closing with typedef or var declarations
            if has_typedef and var_names:
                # typedef ... } Name; Name a, b;
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}{typedef_name or class_name} {var_list};")
            elif has_typedef:
                # typedef ... } Name;
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
            elif var_names:
                # ... } a, b;
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}}} {var_list};")
            else:
                self.emit(f"{self.indent()}}};")

        elif is_union:
            # Union
            if has_typedef:
                self.emit(f"{self.indent()}typedef union {class_name} {{")
            else:
                self.emit(f"{self.indent()}union {class_name} {{")
            self.indent_level += 1

            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign):
                    field_name = stmt.target.id
                    field_type = self.emit_type(stmt.annotation, field_name)
                    self.emit(f"{self.indent()}{field_type};")

            self.indent_level -= 1

            # Emit closing with typedef or var declarations
            if has_typedef and var_names:
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}{typedef_name or class_name} {var_list};")
            elif has_typedef:
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
            elif var_names:
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}}} {var_list};")
            else:
                self.emit(f"{self.indent()}}};")

        else:
            # Struct
            if has_typedef:
                self.emit(f"{self.indent()}typedef struct {class_name} {{")
            else:
                self.emit(f"{self.indent()}struct {class_name} {{")
            self.indent_level += 1

            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign):
                    field_name = stmt.target.id
                    field_type = self.emit_type(stmt.annotation, field_name)
                    self.emit(f"{self.indent()}{field_type};")
                elif isinstance(stmt, ast.ClassDef):
                    # Nested struct
                    self.visit(stmt)

            self.indent_level -= 1

            # Emit closing with typedef or var declarations
            if has_typedef and var_names:
                # typedef ... } Name; Name a, b;
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}{typedef_name or class_name} {var_list};")
            elif has_typedef:
                # typedef ... } Name;
                self.emit(f"{self.indent()}}} {typedef_name or class_name};")
            elif var_names:
                # ... } a, b;
                var_list = ", ".join(var_names)
                self.emit(f"{self.indent()}}} {var_list};")
            else:
                self.emit(f"{self.indent()}}};")

    def visit_TypeAlias(self, node):
        """Handle type alias (typedef)."""
        # type int_ptr = -int
        # In Python 3.12+, this is ast.TypeAlias
        name = node.name.id if isinstance(node.name, ast.Name) else node.name
        type_expr = node.value

        type_str = self.emit_type(type_expr, name)
        self.emit(f"{self.indent()}typedef {type_str};")


def transpile(source_code: str) -> str:
    """Transpile Python source to C."""
    tree = ast.parse(source_code)
    transpiler = CTranspiler()
    transpiler.visit(tree)
    return transpiler.get_output()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python transpiler.py <input.py>")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file, 'r') as f:
        source = f.read()

    c_code = transpile(source)
    print(c_code)


if __name__ == '__main__':
    main()
