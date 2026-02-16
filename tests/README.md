# ComfyUI-Docker Test Suite

Comprehensive test suite for the ComfyUI-Docker revolutionary rebuild with unit, integration, E2E, and performance tests.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest settings and coverage configuration
├── requirements.txt         # Test dependencies
├── unit/                    # Unit tests
│   ├── test_config_generator.py
│   ├── test_download_manager.py
│   ├── test_model_validator.py
│   └── test_health_check.py
├── integration/             # Integration tests
│   └── test_startup.py
├── e2e/                     # End-to-end tests
│   ├── test_dashboard.py
│   └── test_startup_performance.py
├── performance/             # Performance tests
│   └── test_dashboard_performance.py
├── fixtures/                # Test data and fixtures
│   └── data/
├── mocks/                   # Mock objects and responses
└── reports/                 # Test reports (generated)
```

## Running Tests

### Install Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run specific test category
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # E2E tests only
pytest -m performance   # Performance tests only
```

### Run Specific Tests

```bash
# Run specific test file
pytest tests/unit/test_config_generator.py

# Run specific test class
pytest tests/unit/test_config_generator.py::TestConfigGenerator

# Run specific test function
pytest tests/unit/test_config_generator.py::TestConfigGenerator::test_initialization
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=scripts --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests for individual components:

- **Config Generator**: Tests YAML configuration generation
- **Download Manager**: Tests preset download functionality
- **Model Validator**: Tests model file validation
- **Health Check**: Tests system health checks

**Run time**: < 1 minute
**Coverage target**: 80%+

### Integration Tests (`tests/integration/`)

Tests for component interactions:

- **Startup Script**: Tests complete startup workflow
- **Preset Downloader**: Tests download integration
- **Model Validator**: Tests validation integration
- **Dashboard**: Tests API integration

**Run time**: 2-5 minutes
**Requirements**: May require external resources

### E2E Tests (`tests/e2e/`)

Full system tests:

- **Dashboard API**: Tests all API endpoints
- **WebSocket**: Tests real-time communication
- **UI Functionality**: Tests user interactions
- **Startup Performance**: Tests container startup time

**Run time**: 5-10 minutes
**Requirements**: Full system or Docker container

### Performance Tests (`tests/performance/`)

Benchmarks and performance tests:

- **Container Startup**: Target < 30s
- **API Response**: Target < 2s
- **Download Speed**: Target > 10 MB/s
- **Memory Usage**: Monitored for regressions

**Run time**: 5-15 minutes
**Markers**: `@pytest.mark.slow`

## Test Markers

Tests are marked with appropriate markers:

```bash
# Run tests by marker
pytest -m unit              # Unit tests
pytest -m integration       # Integration tests
pytest -m e2e               # E2E tests
pytest -m performance       # Performance tests
pytest -m slow              # Slow tests (>10s)
pytest -m requires_docker   # Tests requiring Docker
pytest -m requires_network  # Tests requiring network
```

## Fixtures

### Shared Fixtures (conftest.py)

- `test_config`: Test configuration
- `temp_dir`: Temporary directory for tests
- `mock_yaml_config`: Mock preset configuration
- `mock_download_manager`: Mock download manager
- `mock_comfyui_client`: Mock ComfyUI client

### Per-Category Fixtures

Each test category may have additional fixtures in their respective `conftest.py` files.

## Writing Tests

### Unit Test Example

```python
import pytest
from mymodule import MyClass

@pytest.mark.unit
class TestMyClass:
    def test_initialization(self):
        obj = MyClass()
        assert obj.is_initialized()

    def test_method(self):
        obj = MyClass()
        result = obj.method("input")
        assert result == "expected"
```

### Integration Test Example

```python
import pytest
from pathlib import Path

@pytest.mark.integration
class TestWorkflow:
    def test_complete_workflow(self, temp_dir):
        # Test full workflow
        result = run_workflow(temp_dir)
        assert result.success
```

### E2E Test Example

```python
import pytest
from fastapi.testclient import TestClient
from app.dashboard.main import app

@pytest.mark.e2e
class TestDashboard:
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r tests/requirements.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Coverage Goals

- **Overall coverage**: 80%+
- **Unit test coverage**: 90%+
- **Integration coverage**: 70%+
- **E2E coverage**: N/A (focus on critical paths)

## Troubleshooting

### Import Errors

```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker Tests Failing

```bash
# Start Docker daemon
sudo systemctl start docker

# Run Docker tests
pytest -m requires_docker -v
```

### Network Tests Failing

```bash
# Skip network tests
pytest -m "not requires_network"
```

## Contributing

When adding new features:

1. Write unit tests first (TDD)
2. Add integration tests for workflows
3. Add E2E tests for user-facing features
4. Update this README with new test documentation

## Performance Baselines

Current performance baselines (update as needed):

- **Container startup**: < 30s
- **Health check**: < 2s
- **API response**: < 2s
- **Config generation**: < 1s
- **Memory increase**: < 100MB during startup

## Test Reports

After running tests, reports are generated in:

- `htmlcov/` - HTML coverage report
- `coverage.xml` - XML coverage report (for CI)
- `pytest-report.html` - HTML test report (if pytest-html installed)
