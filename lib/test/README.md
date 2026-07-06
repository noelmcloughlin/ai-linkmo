# CLI Testing

This directory contains unit tests for the AI-LinkMO CLI Demo commands documented in the main README.md.

## Test Structure

- **conftest.py** - Pytest fixtures including API server startup/shutdown
- **test_cli_examples.py** - Parametrized tests for all README CLI examples
- **validate_handlers.py** - Validation of handler signatures vs OpenAPI spec

## Running Tests

### Quick Test (API mode only, ~2 min)

```bash
uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v
```

### Full Test Suite (both modes, ~15 min)

```bash
uv run pytest lib/test/test_cli_examples.py -v
```

### Run with coverage

```bash
uv run pytest lib/test/ --cov=lib.cli --cov=lib.api --cov-report=html
```

### Run only fast tests (exclude slow)

```bash
uv run pytest lib/test/ -v -m "not slow"
```

### Run specific test

```bash
uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode[risk-count] -v
```

## Test Modes

### API Mode Tests

- **Requires**: Running FastAPI server (started automatically by fixture)
- **Speed**: Fast (~1s per test)
- **Coverage**: Tests API endpoints, server caching, HTTP handling

### Local Mode Tests

- **Requires**: No server (direct handler imports)
- **Speed**: Slow (~15s per test first run, then faster)
- **Coverage**: Tests direct library usage, handler logic

## Test Data

Tests use the AI Atlas Nexus knowledge graph (open source data). 
Tests marked with `byod_required=True` are skipped unless BYOD data is present.

## CI/CD Integration

### GitHub Actions

A working workflow is already set up at
[.github/workflows/cli-tests.yml](../../.github/workflows/cli-tests.yml); it
runs on every push/PR that touches `ai`, `lib/api/**`, `lib/cli/**`,
`lib/test/**`, `byo/**`, `pyproject.toml`, or `uv.lock`. Minimal equivalent:

```yaml
name: CLI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Install dependencies
        # pytest lives in the "test" extra - plain `uv sync` won't install it
        run: uv sync --extra test
      - name: Run API mode tests
        run: uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v
```

### GitLab CI Example

```yaml
test:cli:
  stage: test
  script:
    - uv sync --extra test
    - uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v
  artifacts:
    reports:
      junit: junit.xml
```

## Test Configuration

Tests are parametrized based on README.md examples. Each test case includes:

- Command arguments
- Expected minimum count
- Expected maximum count (None = unbounded)
- BYOD requirement flag

## Troubleshooting

### Server fails to start

- Check if port 8000 is already in use: `lsof -ti:8000`
- Kill processes on port 8000: `lsof -ti:8000 | xargs kill -9`
- Increase server startup timeout in conftest.py
- Run server manually: `uv run uvicorn lib.api.server:app --port 8001`

### Local mode tests timeout

- Increase timeout in cli_command() fixture call
- First run initializes library (slow), subsequent runs are faster

### Test count mismatches

- Data may have changed if using BYOD
- Check if base data was updated
- Review expected counts in test_cli_examples.py
