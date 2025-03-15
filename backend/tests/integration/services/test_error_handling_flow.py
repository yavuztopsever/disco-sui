"""Integration tests for error handling flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime
import logging

from src.core.config import Settings
from src.core.error_handler import ErrorHandler
from src.services.logging.log_manager import LogManager
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_environment(tmp_path):
    """Set up test environment."""
    # Create necessary directories
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    log_path = tmp_path / "logs"
    log_path.mkdir()
    error_path = tmp_path / "errors"
    error_path.mkdir()
    
    return {
        "vault_path": vault_path,
        "log_path": log_path,
        "error_path": error_path
    }

@pytest.mark.asyncio
async def test_error_logging(test_environment):
    """Test error logging functionality."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        LOG_PATH=str(test_environment["log_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    log_manager = LogManager()
    
    await error_handler.initialize(settings)
    await log_manager.initialize(settings)
    
    # Simulate error
    try:
        raise ValueError("Test error message")
    except Exception as e:
        result = await error_handler.log_error(e)
    
    # Verify error logging
    assert result.success is True
    assert result.error_id is not None
    
    # Check error log file
    log_file = test_environment["log_path"] / f"error_{result.error_id}.log"
    assert log_file.exists()
    log_content = log_file.read_text()
    assert "ValueError" in log_content
    assert "Test error message" in log_content

@pytest.mark.asyncio
async def test_error_categorization(test_environment):
    """Test error categorization and prioritization."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Test different error types
    errors = {
        "critical": RuntimeError("Critical system error"),
        "high": PermissionError("Access denied"),
        "medium": ValueError("Invalid input"),
        "low": Warning("Deprecation warning")
    }
    
    results = {}
    for severity, error in errors.items():
        try:
            raise error
        except Exception as e:
            results[severity] = await error_handler.categorize_error(e)
    
    # Verify categorization
    assert results["critical"].severity == "critical"
    assert results["high"].severity == "high"
    assert results["medium"].severity == "medium"
    assert results["low"].severity == "low"

@pytest.mark.asyncio
async def test_error_recovery(test_environment):
    """Test error recovery mechanisms."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Simulate recoverable error
    try:
        raise FileNotFoundError("Test file not found")
    except Exception as e:
        result = await error_handler.attempt_recovery(e)
    
    # Verify recovery attempt
    assert result.success is True
    assert result.recovery_action is not None
    assert result.resolved is True

@pytest.mark.asyncio
async def test_error_notification(test_environment):
    """Test error notification system."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Generate error notification
    error = Exception("Critical system error")
    result = await error_handler.notify_error(error, severity="critical")
    
    # Verify notification
    assert result.success is True
    assert result.notification_sent is True
    assert result.notification_type == "critical"

@pytest.mark.asyncio
async def test_error_aggregation(test_environment):
    """Test error aggregation and pattern detection."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Generate multiple similar errors
    errors = []
    for i in range(5):
        try:
            raise ValueError(f"Similar error {i}")
        except Exception as e:
            errors.append(e)
            await error_handler.log_error(e)
    
    # Analyze error patterns
    analysis = await error_handler.analyze_error_patterns()
    
    # Verify pattern detection
    assert analysis.success is True
    assert len(analysis.patterns) > 0
    assert analysis.patterns[0].occurrence_count == 5
    assert "ValueError" in analysis.patterns[0].error_type

@pytest.mark.asyncio
async def test_error_reporting(test_environment):
    """Test error reporting and analytics."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Generate test errors
    errors = [
        ValueError("Test error 1"),
        RuntimeError("Test error 2"),
        FileNotFoundError("Test error 3")
    ]
    
    for error in errors:
        try:
            raise error
        except Exception as e:
            await error_handler.log_error(e)
    
    # Generate error report
    report = await error_handler.generate_error_report()
    
    # Verify report
    assert report.success is True
    assert report.total_errors == 3
    assert len(report.error_types) == 3
    assert report.time_period is not None

@pytest.mark.asyncio
async def test_error_context_capture(test_environment):
    """Test error context capture and preservation."""
    # Initialize services
    settings = Settings(
        VAULT_PATH=str(test_environment["vault_path"]),
        ERROR_PATH=str(test_environment["error_path"])
    )
    
    error_handler = ErrorHandler()
    await error_handler.initialize(settings)
    
    # Create test context
    context = {
        "user_action": "file_operation",
        "file_path": "/test/path",
        "operation": "write",
        "timestamp": datetime.now()
    }
    
    # Simulate error with context
    try:
        raise PermissionError("Write permission denied")
    except Exception as e:
        result = await error_handler.capture_error_context(e, context)
    
    # Verify context capture
    assert result.success is True
    assert result.context == context
    assert result.error_info is not None
    assert "PermissionError" in result.error_info 