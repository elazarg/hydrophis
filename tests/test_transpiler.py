"""Unit tests for specific transpiler features."""

import ast

import pytest

from arafura import CTranspiler, transpile


class TestTypeEmission:
    """Test type emission functionality."""

    def test_basic_types(self) -> None:
        """Test basic type emission."""
        transpiler = CTranspiler()
        assert transpiler.emit_type(ast.parse("int").body[0].value, "x") == "int x"
        assert transpiler.emit_type(ast.parse("char").body[0].value, "c") == "char c"

    def test_pointer_types(self) -> None:
        """Test pointer type emission."""
        transpiler = CTranspiler()
        # -int -> int*
        node = ast.parse("-int").body[0].value
        assert transpiler.emit_type(node, "ptr") == "int *ptr"

    def test_array_types(self) -> None:
        """Test array type emission."""
        transpiler = CTranspiler()
        # int[10]
        node = ast.parse("int[10]").body[0].value
        result = transpiler.emit_type(node, "arr")
        assert "int" in result and "[10]" in result


class TestExpressionEmission:
    """Test expression emission functionality."""

    def test_constants(self) -> None:
        """Test constant emission."""
        transpiler = CTranspiler()
        assert transpiler.emit_expr(ast.Constant(42)) == "42"
        assert transpiler.emit_expr(ast.Constant(3.14)) == "3.14"
        assert transpiler.emit_expr(ast.Constant("hello")) == '"hello"'

    def test_none_to_null(self) -> None:
        """Test None -> NULL conversion."""
        transpiler = CTranspiler()
        node = ast.parse("None").body[0].value
        assert transpiler.emit_expr(node) == "NULL"

    def test_bool_to_int(self) -> None:
        """Test boolean -> int conversion."""
        source_true = """
x: int = True
"""
        source_false = """
x: int = False
"""
        output_true = transpile(source_true)
        output_false = transpile(source_false)
        assert "= 1;" in output_true
        assert "= 0;" in output_false

    def test_increment_decrement(self) -> None:
        """Test increment/decrement operators."""
        source = """
x: int = 0
x ** _
_ ** x
x // _
_ // x
"""
        output = transpile(source)
        assert "x++;" in output
        assert "++x;" in output
        assert "x--;" in output
        assert "--x;" in output


class TestStatements:
    """Test statement transpilation."""

    def test_variable_declaration(self) -> None:
        """Test variable declarations."""
        source = "x: int = 5"
        output = transpile(source)
        assert "int x = 5;" in output

    def test_function_definition(self) -> None:
        """Test function definitions."""
        source = """
def add(a: int, b: int) -> int:
    return a + b
"""
        output = transpile(source)
        assert "int add(int a, int b)" in output
        assert "return (a + b);" in output

    def test_if_statement(self) -> None:
        """Test if statements."""
        source = """
def test(x: int) -> void:
    if x > 0:
        x = 1
"""
        output = transpile(source)
        assert "if (x > 0)" in output


class TestCompositeTypes:
    """Test struct, union, and enum transpilation."""

    def test_struct_definition(self) -> None:
        """Test struct definitions."""
        source = """
class Point:
    x: int
    y: int
"""
        output = transpile(source)
        assert "struct Point {" in output
        assert "int x;" in output
        assert "int y;" in output
        assert "};" in output

    def test_union_definition(self) -> None:
        """Test union definitions."""
        source = """
class Data(Union):
    i: int
    f: float
"""
        output = transpile(source)
        assert "union Data {" in output
        assert "int i;" in output
        assert "float f;" in output

    def test_enum_definition(self) -> None:
        """Test enum definitions."""
        source = """
class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
"""
        output = transpile(source)
        assert "enum Color {" in output
        assert "RED = 0," in output
        assert "GREEN = 1," in output
        assert "BLUE = 2," in output


class TestSpecialForms:
    """Test special _ forms."""

    def test_address_of(self) -> None:
        """Test address-of operator."""
        source = """
def test() -> void:
    x: int = 5
    px: -int = _.x
"""
        output = transpile(source)
        assert "&x" in output

    def test_dereference(self) -> None:
        """Test dereference operator."""
        source = """
def test(ptr: -int) -> void:
    x: int = ptr._
"""
        output = transpile(source)
        assert "(*ptr)" in output

    def test_pointer_member_access(self) -> None:
        """Test pointer member access."""
        source = """
class Node:
    data: int

def test(node: -Node) -> void:
    x: int = node._.data
"""
        output = transpile(source)
        assert "node->data" in output


class TestPreprocessor:
    """Test preprocessor directive handling."""

    def test_include_from_import(self) -> None:
        """Test #include from import statements."""
        source = "from stdio import *"
        output = transpile(source)
        assert "#include <stdio.h>" in output

    def test_include_import(self) -> None:
        """Test #include from regular import."""
        source = "import stdio"
        output = transpile(source)
        assert '#include "stdio.h"' in output

    def test_macro_definition(self) -> None:
        """Test macro definitions."""
        source = "MAX_SIZE: macro = 100"
        output = transpile(source)
        assert "#define MAX_SIZE 100" in output

    def test_conditional_compilation(self) -> None:
        """Test conditional compilation."""
        source = """
if [DEBUG]:
    x: int = 1
"""
        output = transpile(source)
        assert "#ifdef DEBUG" in output
        assert "#endif" in output


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_syntax(self) -> None:
        """Test that invalid Python syntax raises an error."""
        with pytest.raises(SyntaxError):
            transpile("def invalid syntax")

    def test_unhandled_expression(self) -> None:
        """Test that unhandled expressions raise an error."""
        # Lambda is not a supported expression
        transpiler = CTranspiler()
        lambda_node = ast.parse("lambda x: x + 1").body[0].value
        with pytest.raises(ValueError, match="Unhandled expression"):
            transpiler.emit_expr(lambda_node)
