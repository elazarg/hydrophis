"""Arafura - C as Python Transpiler.

A transpiler that converts Python syntax with C semantics into C code.
"""

from arafura.transpiler import CTranspiler, transpile

__version__ = "0.1.0"
__all__ = ["CTranspiler", "transpile", "__version__"]
