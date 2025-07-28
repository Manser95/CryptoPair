# Testing Guide

This guide explains how to run tests for the Crypto Pairs API project.

## Quick Start

For new developers who want to quickly run all tests:

```bash
# Clone the repository and navigate to project root
git clone <repository-url>
cd cryptopair

# Run the automated setup and test
make setup-test
```

This command will:
1. Install all Python dependencies
2. Build Docker images
3. Run all tests locally

## Testing Commands

### Run All Tests in Docker (Recommended)

```bash
make test-docker
```

This command:
- Builds an isolated test environment
- Starts test dependencies (Redis)
- Runs all tests with coverage
- Cleans up after completion
- Generates coverage reports in `./coverage/`

### Run Tests in Existing Environment

If you already have the application running:

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run tests with detailed coverage
make test-all
```

### CI/CD Testing

For continuous integration environments:

```bash
make test-ci
```

This command:
- Builds fresh Docker images
- Runs tests with CI-friendly output
- Generates XML test reports
- Performs automatic cleanup

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── application/        # Use case tests
│   ├── domain/            # Domain entity tests
│   └── infrastructure/    # Infrastructure tests
├── integration/            # Integration tests
├── load/                  # Load and performance tests
├── conftest.py           # Shared fixtures
├── pytest.ini            # Pytest configuration
```

## Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/infrastructure/test_optimized_cache.py

# Run tests matching a pattern
pytest tests/ -k "cache"

# Run tests with specific markers
pytest tests/ -m "unit"
pytest tests/ -m "integration"
```

## Load Testing

### Using hey (simple HTTP load testing)

```bash
# Run load test
make test-load

# Run stress test (60 seconds)
make test-stress
```

### Using k6 (advanced scenarios)

```bash
make k6-test
```

### Using Locust (web UI)

```bash
make locust-test
# Open http://localhost:8089 in browser
```

## Coverage Reports

After running tests with coverage, reports are available in:
- Terminal: Coverage summary is displayed
- HTML: Open `coverage/index.html` in browser
- XML: `coverage.xml` for CI tools

## Troubleshooting

### Tests failing due to missing dependencies

```bash
# Install test dependencies
poetry install --with dev
```

### Docker-related issues

```bash
# Clean up Docker environment
make clean

# Rebuild images
docker-compose -f docker-compose.test.yml build --no-cache
```

### Permission issues

Ensure your user has permissions to run Docker commands without sudo.

## Best Practices

1. **Always run tests before committing**
2. **Write tests for new features**
3. **Maintain test coverage above 80%**
4. **Use appropriate test markers** (unit, integration, slow)
5. **Mock external dependencies** in unit tests
6. **Test error cases** not just happy paths

## Environment Variables for Testing

The test environment uses these defaults:
- `ENVIRONMENT=test`
- `LOG_LEVEL=warning`
- `CACHE_TTL_L1=1`
- `CACHE_TTL_L2=2`

You can override them in `docker-compose.test.yml` if needed.

## Adding New Tests

1. Create test file following naming convention: `test_*.py`
2. Use appropriate fixtures from `conftest.py`
3. Mark tests appropriately:
   ```python
   @pytest.mark.unit
   def test_something():
       pass
   
   @pytest.mark.integration
   async def test_api_endpoint():
       pass
   ```

## Continuous Integration

The project is ready for CI/CD integration. Use `make test-ci` in your pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: make test-ci
```

Test results will be available in:
- `test-results.xml` (JUnit format)
- `coverage.xml` (Cobertura format)