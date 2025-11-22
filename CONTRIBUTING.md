# Contributing to Arafura

## Development Setup

1. **Requirements**: Python 3.13.x (exact version required due to AST brittleness)

2. **Installation**:
   ```bash
   # Clone the repository
   git clone <repo-url>
   cd arafura

   # Install in editable mode with dev dependencies
   pip install -e ".[dev]"
   ```

## Project Structure

```
arafura/
├── src/arafura/          # Source code
│   ├── __init__.py        # Package exports
│   ├── transpiler.py      # Core transpiler (CTranspiler class)
│   └── cli.py             # Command-line interface
├── tests/                  # Test suite
│   ├── fixtures/          # Input test files (.py)
│   ├── golden_outputs/    # Expected C outputs (.c)
│   ├── conftest.py       # Pytest fixtures
│   ├── test_golden_master.py  # Golden master tests
│   └── test_transpiler.py     # Unit tests
├── pyproject.toml         # Project metadata
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only golden master tests
pytest tests/test_golden_master.py

# Run only unit tests
pytest tests/test_transpiler.py

# Run a specific test
pytest tests/test_transpiler.py::TestTypeEmission::test_basic_types
```

## Testing Strategy

### Golden Master Tests

Golden master testing ensures transpiler output stability. Each test case has:
- Input: A Python file in `tests/fixtures/`
- Expected output: A C file in `tests/golden_outputs/`

**Adding a new golden master test:**

1. Create input file: `tests/fixtures/my_test.py`
2. Generate golden output:
   ```bash
   python src/arafura/transpiler.py tests/fixtures/my_test.py > tests/golden_outputs/my_test.c
   ```
3. Review the C output to ensure correctness
4. Run tests to verify: `pytest tests/test_golden_master.py`

**Updating golden outputs after intentional changes:**

```bash
# Regenerate all golden outputs
python src/arafura/transpiler.py tests/fixtures/example.py > tests/golden_outputs/example.c
python src/arafura/transpiler.py tests/fixtures/features.py > tests/golden_outputs/features.c
python src/arafura/transpiler.py tests/fixtures/typedef.py > tests/golden_outputs/typedef.c
```

### Unit Tests

Unit tests in `test_transpiler.py` test specific transpiler components:
- Type emission
- Expression emission
- Statement transpilation
- Special forms (_, pointers, etc.)
- Preprocessor directives
- Error handling

## Making Changes

1. **Understand the AST**: The transpiler works by transforming Python AST nodes to C code
2. **Run tests frequently**: `pytest -v`
3. **Add tests for new features**: Both unit tests and golden master tests
4. **Document special syntax**: Update README.md with examples

## Code Style

The project intentionally keeps dependencies minimal. No linters or formatters are included as dependencies. Write clear, readable code following Python conventions.

## Release Process

1. Update version in `pyproject.toml` and `src/arafura/__init__.py`
2. Run all tests: `pytest`
3. Update CHANGELOG (if exists)
4. Tag release: `git tag v0.x.0`
5. Build: `python -m build`
6. Publish: `python -m twine upload dist/*`

## Key Design Principles

- **Python 3.13 only**: AST handling is version-specific
- **Minimal dependencies**: Core has zero dependencies, dev only needs pytest
- **Local transformation**: No type inference, purely syntactic
- **Explicit over implicit**: All types must be annotated
- **Golden master testing**: Ensure output stability

## Common Tasks

### Adding support for a new C feature

1. Design Python syntax that maps to the C feature
2. Add example to `tests/fixtures/features.py`
3. Implement in `transpiler.py` (typically in `visit_*` or `emit_*` methods)
4. Regenerate golden output
5. Add unit test in `test_transpiler.py`
6. Document in README.md

### Debugging transpiler issues

```python
import ast
code = "x: int = 5"
tree = ast.parse(code)
print(ast.dump(tree, indent=2))  # See the AST structure
```

### Testing CLI changes

```bash
arafura tests/fixtures/example.py --check
arafura tests/fixtures/typedef.py -o output.c
arafura tests/fixtures/features.py  # stdout
```

## Questions?

Check the [DESIGN.md](DESIGN.md) for the complete language specification.
