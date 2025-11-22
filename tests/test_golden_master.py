"""Golden master tests for the Arafura transpiler.

These tests ensure that the transpiler output remains consistent.
When intentionally changing transpiler behavior, regenerate golden outputs with:

    python src/arafura/transpiler.py tests/fixtures/<test>.py > tests/golden_outputs/<test>.c
"""

from pathlib import Path

import pytest

from arafura import transpile


def get_test_cases(fixtures_dir: Path, golden_outputs_dir: Path) -> list[tuple[str, Path, Path]]:
    """Discover all test cases by finding fixture/golden pairs."""
    test_cases = []
    for fixture_file in sorted(fixtures_dir.glob("*.py")):
        golden_file = golden_outputs_dir / f"{fixture_file.stem}.c"
        if golden_file.exists():
            test_cases.append((fixture_file.stem, fixture_file, golden_file))
    return test_cases


class TestGoldenMaster:
    """Golden master tests to ensure transpiler output stability."""

    @pytest.fixture(autouse=True)
    def setup(self, fixtures_dir: Path, golden_outputs_dir: Path) -> None:
        """Set up test directories."""
        self.fixtures_dir = fixtures_dir
        self.golden_outputs_dir = golden_outputs_dir

    @pytest.mark.parametrize(
        "test_name,fixture_path,golden_path",
        [
            pytest.param(name, fixture, golden, id=name)
            for name, fixture, golden in get_test_cases(
                Path(__file__).parent / "fixtures",
                Path(__file__).parent / "golden_outputs",
            )
        ],
    )
    def test_transpiler_output(
        self, test_name: str, fixture_path: Path, golden_path: Path
    ) -> None:
        """Test that transpiler output matches the golden master."""
        # Read input
        source = fixture_path.read_text(encoding="utf-8")

        # Transpile
        actual_output = transpile(source)

        # Read expected golden output
        expected_output = golden_path.read_text(encoding="utf-8")

        # Compare (normalize line endings)
        actual_lines = actual_output.strip().splitlines()
        expected_lines = expected_output.strip().splitlines()

        if actual_lines != expected_lines:
            # Generate detailed diff for better error messages
            diff_lines = []
            max_lines = max(len(actual_lines), len(expected_lines))
            for i in range(max_lines):
                actual_line = actual_lines[i] if i < len(actual_lines) else "<missing>"
                expected_line = expected_lines[i] if i < len(expected_lines) else "<missing>"
                if actual_line != expected_line:
                    diff_lines.append(f"Line {i + 1}:")
                    diff_lines.append(f"  Expected: {expected_line}")
                    diff_lines.append(f"  Actual:   {actual_line}")

            pytest.fail(
                f"Transpiler output differs from golden master for {test_name}:\n"
                + "\n".join(diff_lines[:50])  # Limit to first 50 differences
            )
