# DiscoSui Tests

This directory contains all tests for the DiscoSui backend. The tests are organized into three main categories:

## Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── core/         # Tests for core functionality
│   ├── services/     # Tests for individual services
│   └── tools/        # Tests for tools
├── integration/       # Integration tests
│   ├── core/         # Core integration tests
│   ├── services/     # Service integration tests
│   └── tools/        # Tool integration tests
├── e2e/              # End-to-end tests
│   └── test_*.py     # Complete workflow tests
└── data/             # Test data
    ├── test_vault/   # Test Obsidian vault
    ├── test_audio/   # Test audio files
    ├── test_emails/  # Test email files
    └── test_vector_db/ # Test vector database
```

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test categories:
```bash
# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# End-to-end tests only
pytest tests/e2e

# Run tests with coverage report
pytest --cov=src

# Run tests and generate HTML coverage report
pytest --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- High coverage

### Integration Tests
- Test component interactions
- Limited mocking
- Focus on service integration
- Test real data flow

### End-to-End Tests
- Test complete workflows
- No mocking
- Test real system behavior
- Slower execution

## Test Data

The `data` directory contains test fixtures and sample data:

- `test_vault/`: Sample Obsidian vault structure
- `test_audio/`: Sample audio files for transcription
- `test_emails/`: Sample email files
- `test_vector_db/`: Vector database test data

## Writing Tests

### Guidelines

1. Follow the test naming convention:
   - Files: `test_*.py`
   - Classes: `Test*`
   - Functions: `test_*`

2. Use appropriate pytest markers:
   - `@pytest.mark.unit`
   - `@pytest.mark.integration`
   - `@pytest.mark.e2e`
   - `@pytest.mark.slow`
   - `@pytest.mark.api`
   - `@pytest.mark.db`

3. Use fixtures from `conftest.py`

4. Write clear test descriptions

5. Follow AAA pattern:
   - Arrange
   - Act
   - Assert

### Example

```python
@pytest.mark.unit
def test_audio_transcription(mock_audio_file):
    # Arrange
    transcriber = AudioTranscriber()
    
    # Act
    result = transcriber.transcribe(mock_audio_file)
    
    # Assert
    assert result.success
    assert len(result.text) > 0
```

## Coverage Requirements

- Unit tests: 90% coverage
- Integration tests: 70% coverage
- Overall coverage: 80% minimum

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Merges to main branch
- Nightly builds

## Dependencies

Test-specific dependencies are listed in `requirements.txt`:
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock
- hypothesis
- coverage 