"""Integration tests for logging and monitoring flow."""

import pytest
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import logging
import json
import asyncio

from src.core.config import Settings
from src.services.logging.log_manager import LogManager
from src.services.monitoring.monitor_service import MonitorService
from src.services.metrics.metrics_collector import MetricsCollector
from src.core.obsidian_utils import ObsidianUtils

@pytest.fixture
def test_environment(tmp_path):
    """Set up test environment."""
    # Create necessary directories
    log_path = tmp_path / "logs"
    log_path.mkdir()
    metrics_path = tmp_path / "metrics"
    metrics_path.mkdir()
    monitoring_path = tmp_path / "monitoring"
    monitoring_path.mkdir()
    
    return {
        "log_path": log_path,
        "metrics_path": metrics_path,
        "monitoring_path": monitoring_path
    }

@pytest.mark.asyncio
async def test_log_configuration(test_environment):
    """Test logging configuration and initialization."""
    # Initialize services
    settings = Settings(
        LOG_PATH=str(test_environment["log_path"])
    )
    
    log_manager = LogManager()
    await log_manager.initialize(settings)
    
    # Configure logging
    config_result = await log_manager.configure_logging({
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "handlers": ["file", "console"]
    })
    
    # Verify configuration
    assert config_result.success is True
    assert config_result.active_handlers == 2
    
    # Test logging
    log_result = await log_manager.log_message(
        level="INFO",
        message="Test log message",
        module="test_module"
    )
    
    # Verify logging
    assert log_result.success is True
    assert log_result.log_file.exists()
    assert "Test log message" in log_result.log_file.read_text()

@pytest.mark.asyncio
async def test_log_rotation(test_environment):
    """Test log file rotation and archiving."""
    # Initialize services
    settings = Settings(
        LOG_PATH=str(test_environment["log_path"])
    )
    
    log_manager = LogManager()
    await log_manager.initialize(settings)
    
    # Configure rotation
    rotation_config = {
        "max_size": "1MB",
        "backup_count": 3,
        "compress": True
    }
    
    result = await log_manager.configure_rotation(rotation_config)
    
    # Verify rotation setup
    assert result.success is True
    
    # Generate logs to trigger rotation
    for i in range(1000):
        await log_manager.log_message(
            level="INFO",
            message=f"Test log message {i} with some padding..." * 100
        )
    
    # Verify rotation
    log_files = list(test_environment["log_path"].glob("*.log*"))
    assert len(log_files) > 1
    assert any(file.name.endswith(".gz") for file in log_files)

@pytest.mark.asyncio
async def test_performance_monitoring(test_environment):
    """Test performance monitoring and metrics collection."""
    # Initialize services
    settings = Settings(
        METRICS_PATH=str(test_environment["metrics_path"])
    )
    
    monitor_service = MonitorService()
    metrics_collector = MetricsCollector()
    
    await monitor_service.initialize(settings)
    await metrics_collector.initialize(settings)
    
    # Start monitoring
    await monitor_service.start_monitoring()
    
    # Simulate some operations
    async def test_operation():
        await asyncio.sleep(0.1)
        return "operation complete"
    
    with metrics_collector.measure_operation("test_op"):
        await test_operation()
    
    # Collect metrics
    metrics = await metrics_collector.collect_metrics()
    
    # Verify metrics
    assert metrics.success is True
    assert "test_op" in metrics.operations
    assert metrics.operations["test_op"].duration > 0
    assert metrics.operations["test_op"].count == 1

@pytest.mark.asyncio
async def test_error_logging(test_environment):
    """Test error logging and tracking."""
    # Initialize services
    settings = Settings(
        LOG_PATH=str(test_environment["log_path"])
    )
    
    log_manager = LogManager()
    await log_manager.initialize(settings)
    
    # Log different types of errors
    error_types = [
        ("ERROR", ValueError("Test error"), "test_module"),
        ("CRITICAL", RuntimeError("Critical error"), "system"),
        ("WARNING", UserWarning("Test warning"), "user")
    ]
    
    for level, error, module in error_types:
        result = await log_manager.log_error(
            level=level,
            error=error,
            module=module
        )
        assert result.success is True
    
    # Verify error logs
    error_log = test_environment["log_path"] / "error.log"
    log_content = error_log.read_text()
    
    assert "ValueError: Test error" in log_content
    assert "RuntimeError: Critical error" in log_content
    assert "UserWarning: Test warning" in log_content

@pytest.mark.asyncio
async def test_system_metrics_collection(test_environment):
    """Test system metrics collection and monitoring."""
    # Initialize services
    settings = Settings(
        METRICS_PATH=str(test_environment["metrics_path"])
    )
    
    metrics_collector = MetricsCollector()
    await metrics_collector.initialize(settings)
    
    # Collect system metrics
    metrics = await metrics_collector.collect_system_metrics()
    
    # Verify system metrics
    assert metrics.success is True
    assert metrics.cpu_usage is not None
    assert metrics.memory_usage is not None
    assert metrics.disk_usage is not None
    assert metrics.timestamp is not None

@pytest.mark.asyncio
async def test_performance_alerts(test_environment):
    """Test performance alerting system."""
    # Initialize services
    settings = Settings(
        MONITORING_PATH=str(test_environment["monitoring_path"])
    )
    
    monitor_service = MonitorService()
    await monitor_service.initialize(settings)
    
    # Configure alerts
    alert_config = {
        "cpu_threshold": 80,
        "memory_threshold": 90,
        "response_time_threshold": 1000
    }
    
    result = await monitor_service.configure_alerts(alert_config)
    assert result.success is True
    
    # Simulate high resource usage
    alerts = []
    
    async def alert_handler(alert):
        alerts.append(alert)
    
    await monitor_service.register_alert_handler(alert_handler)
    await monitor_service.simulate_high_usage()
    
    # Verify alerts
    assert len(alerts) > 0
    assert any(alert.type == "high_cpu_usage" for alert in alerts)

@pytest.mark.asyncio
async def test_log_analysis(test_environment):
    """Test log analysis and pattern detection."""
    # Initialize services
    settings = Settings(
        LOG_PATH=str(test_environment["log_path"])
    )
    
    log_manager = LogManager()
    await log_manager.initialize(settings)
    
    # Generate test logs
    test_logs = [
        ("ERROR", "Database connection failed", "database"),
        ("ERROR", "Database connection failed", "database"),
        ("WARNING", "Slow query detected", "database"),
        ("ERROR", "Database connection failed", "database"),
        ("INFO", "Operation successful", "api"),
        ("ERROR", "Invalid request", "api")
    ]
    
    for level, message, module in test_logs:
        await log_manager.log_message(level=level, message=message, module=module)
    
    # Analyze logs
    analysis = await log_manager.analyze_logs()
    
    # Verify analysis
    assert analysis.success is True
    assert analysis.error_count == 4
    assert analysis.warning_count == 1
    assert "database" in analysis.error_patterns
    assert analysis.error_patterns["database"]["count"] == 3

@pytest.mark.asyncio
async def test_metrics_aggregation(test_environment):
    """Test metrics aggregation and reporting."""
    # Initialize services
    settings = Settings(
        METRICS_PATH=str(test_environment["metrics_path"])
    )
    
    metrics_collector = MetricsCollector()
    await metrics_collector.initialize(settings)
    
    # Generate test metrics
    test_operations = [
        ("api_request", 100),
        ("database_query", 250),
        ("api_request", 150),
        ("file_operation", 300),
        ("api_request", 120)
    ]
    
    for op_name, duration in test_operations:
        with metrics_collector.measure_operation(op_name):
            await asyncio.sleep(duration / 1000)  # Convert to seconds
    
    # Aggregate metrics
    report = await metrics_collector.generate_report()
    
    # Verify aggregation
    assert report.success is True
    assert report.total_operations > 0
    assert "api_request" in report.operation_stats
    assert report.operation_stats["api_request"]["count"] == 3
    assert report.operation_stats["api_request"]["avg_duration"] > 0

@pytest.mark.asyncio
async def test_monitoring_dashboard_data(test_environment):
    """Test monitoring dashboard data generation."""
    # Initialize services
    settings = Settings(
        MONITORING_PATH=str(test_environment["monitoring_path"]),
        METRICS_PATH=str(test_environment["metrics_path"])
    )
    
    monitor_service = MonitorService()
    await monitor_service.initialize(settings)
    
    # Generate dashboard data
    dashboard_data = await monitor_service.generate_dashboard_data()
    
    # Verify dashboard data
    assert dashboard_data.success is True
    assert "system_metrics" in dashboard_data.sections
    assert "performance_metrics" in dashboard_data.sections
    assert "error_rates" in dashboard_data.sections
    assert dashboard_data.timestamp is not None
    
    # Verify data format
    system_metrics = dashboard_data.sections["system_metrics"]
    assert "cpu_usage" in system_metrics
    assert "memory_usage" in system_metrics
    assert isinstance(system_metrics["cpu_usage"], (int, float))
    assert isinstance(system_metrics["memory_usage"], (int, float)) 