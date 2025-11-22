#!/usr/bin/env python3
"""Command-line interface for Arafura transpiler."""

import argparse
import sys
from pathlib import Path

from arafura.transpiler import transpile


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="arafura",
        description="Transpile Python syntax with C semantics into C code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  arafura input.py                # Print C code to stdout
  arafura input.py -o output.c    # Write C code to file
  arafura input.py --check        # Check syntax without output
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input Python file to transpile",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output C file (default: stdout)",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if input can be transpiled without generating output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    # Read input file
    try:
        source = args.input.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Transpile
    try:
        c_code = transpile(source)
    except Exception as e:
        print(f"Transpilation error: {e}", file=sys.stderr)
        return 1

    # Handle check mode
    if args.check:
        print(f"OK: {args.input} transpiles successfully")
        return 0

    # Write output
    if args.output:
        try:
            args.output.write_text(c_code, encoding="utf-8")
            print(f"OK: Generated {args.output}")
            return 0
        except IOError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(c_code)
        return 0


if __name__ == "__main__":
    sys.exit(main())
