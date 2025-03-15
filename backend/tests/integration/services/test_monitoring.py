"""Integration tests for monitoring and metrics systems."""
import pytest
import asyncio
from datetime import datetime, timedelta

@pytest.mark.integration
class TestMonitoring:
    """Test suite for monitoring and metrics integration."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, initialized_services, validation_helper):
        """Test metrics collection and aggregation."""
        metrics_collector = initialized_services["metrics_collector"]
        
        # 1. Record various metrics
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
        
        # 2. Generate metrics report
        report = await metrics_collector.generate_report()
        await validation_helper(report,
                              total_operations=5,
                              unique_operation_types=3)
        
        # 3. Verify specific metrics
        api_stats = report.operation_stats["api_request"]
        await validation_helper(api_stats,
                              count=3,
                              avg_duration=lambda x: 100 <= x <= 150)
    
    @pytest.mark.asyncio
    async def test_system_monitoring(self, initialized_services, validation_helper):
        """Test system resource monitoring."""
        monitor_service = initialized_services["metrics_collector"]
        
        # 1. Collect system metrics
        metrics = await monitor_service.collect_system_metrics()
        await validation_helper(metrics,
                              cpu_usage=lambda x: 0 <= x <= 100,
                              memory_usage=lambda x: x > 0,
                              disk_usage=lambda x: x > 0)
        
        # 2. Monitor resource thresholds
        threshold_result = await monitor_service.check_resource_thresholds()
        await validation_helper(threshold_result,
                              thresholds_checked=True,
                              alerts=list)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, initialized_services, validation_helper):
        """Test performance monitoring and analysis."""
        monitor_service = initialized_services["metrics_collector"]
        
        # 1. Record performance metrics
        async def test_operation():
            await asyncio.sleep(0.1)
        
        for _ in range(5):
            with monitor_service.measure_performance("test_op"):
                await test_operation()
        
        # 2. Analyze performance
        analysis = await monitor_service.analyze_performance("test_op")
        await validation_helper(analysis,
                              operation_count=5,
                              avg_duration=lambda x: x >= 0.1,
                              has_outliers=bool)
    
    @pytest.mark.asyncio
    async def test_error_monitoring(self, initialized_services, validation_helper):
        """Test error monitoring and reporting."""
        error_handler = initialized_services["error_handler"]
        
        # 1. Record test errors
        test_errors = [
            ValueError("Test error 1"),
            RuntimeError("Test error 2"),
            FileNotFoundError("Test error 3")
        ]
        
        for error in test_errors:
            await error_handler.log_error(error)
        
        # 2. Generate error report
        report = await error_handler.generate_error_report()
        await validation_helper(report,
                              total_errors=3,
                              unique_error_types=3)
        
        # 3. Analyze error patterns
        analysis = await error_handler.analyze_error_patterns()
        await validation_helper(analysis,
                              patterns_found=bool,
                              recommendations=list)
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard(self, initialized_services, validation_helper):
        """Test monitoring dashboard data generation."""
        monitor_service = initialized_services["metrics_collector"]
        
        # 1. Generate dashboard data
        dashboard_data = await monitor_service.generate_dashboard_data()
        await validation_helper(dashboard_data,
                              sections=["system_metrics", "performance_metrics", "error_rates"],
                              timestamp=lambda x: isinstance(x, (int, float)))
        
        # 2. Verify metrics format
        system_metrics = dashboard_data.sections["system_metrics"]
        assert isinstance(system_metrics["cpu_usage"], (int, float))
        assert isinstance(system_metrics["memory_usage"], (int, float))
    
    @pytest.mark.asyncio
    async def test_historical_metrics(self, initialized_services, validation_helper):
        """Test historical metrics analysis."""
        metrics_collector = initialized_services["metrics_collector"]
        
        # 1. Record historical data
        start_time = datetime.now() - timedelta(hours=1)
        
        for i in range(6):
            timestamp = start_time + timedelta(minutes=i*10)
            await metrics_collector.record_metric(
                "test_metric",
                value=i*10,
                timestamp=timestamp
            )
        
        # 2. Analyze historical data
        analysis = await metrics_collector.analyze_historical_data(
            metric_name="test_metric",
            time_range=timedelta(hours=1)
        )
        
        await validation_helper(analysis,
                              data_points=6,
                              trend=lambda x: isinstance(x, str),
                              has_anomalies=bool) 