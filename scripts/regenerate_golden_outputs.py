#!/usr/bin/env python3
"""
Regenerate all golden output files.

This script should be run when the transpiler behavior is intentionally changed
and the golden outputs need to be updated to match.

Usage:
    python scripts/regenerate_golden_outputs.py
"""

import sys
from pathlib import Path

# Add src to path so we can import arafura
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arafura import transpile


def main() -> int:
    """Regenerate all golden output files."""
    project_root = Path(__file__).parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"
    golden_dir = project_root / "tests" / "golden_outputs"

    # Ensure directories exist
    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found: {fixtures_dir}", file=sys.stderr)
        return 1

    golden_dir.mkdir(parents=True, exist_ok=True)

    # Process all fixture files
    fixture_files = sorted(fixtures_dir.glob("*.py"))
    if not fixture_files:
        print(f"Warning: No fixture files found in {fixtures_dir}", file=sys.stderr)
        return 0

    print(f"Regenerating {len(fixture_files)} golden output files...")

    for fixture_file in fixture_files:
        try:
            # Read and transpile
            source = fixture_file.read_text(encoding="utf-8")
            c_code = transpile(source)

            # Write golden output
            golden_file = golden_dir / f"{fixture_file.stem}.c"
            golden_file.write_text(c_code, encoding="utf-8")

            print(f"  OK: {fixture_file.name} -> {golden_file.name}")

        except Exception as e:
            print(f"  ERROR: {fixture_file.name}: {e}", file=sys.stderr)
            return 1

    print(f"\nSuccess! Regenerated {len(fixture_files)} golden outputs.")
    print("Run 'pytest tests/test_golden_master.py' to verify.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
