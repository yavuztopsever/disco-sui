"""Performance monitoring utilities."""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MetricPoint:
    """A single metric data point."""
    
    value: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Monitor for tracking performance metrics."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self._metrics: Dict[str, list[MetricPoint]] = {}
        self._start_times: Dict[str, float] = {}
    
    def start_timer(self, name: str) -> None:
        """Start a timer for a named operation.
        
        Args:
            name: Name of the operation to time
        """
        self._start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a timer and record its duration.
        
        Args:
            name: Name of the operation
            
        Returns:
            Duration in seconds if timer was started, None otherwise
        """
        start_time = self._start_times.pop(name, None)
        if start_time is None:
            return None
        
        duration = time.time() - start_time
        self.record_metric(f"{name}_duration", duration)
        return duration
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a metric value.
        
        Args:
            name: Name of the metric
            value: Value to record
        """
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(MetricPoint(value))
    
    def get_metric(self, name: str) -> Optional[list[MetricPoint]]:
        """Get all recorded values for a metric.
        
        Args:
            name: Name of the metric
            
        Returns:
            List of metric points if metric exists, None otherwise
        """
        return self._metrics.get(name)
    
    def get_latest_metric(self, name: str) -> Optional[MetricPoint]:
        """Get the most recent value for a metric.
        
        Args:
            name: Name of the metric
            
        Returns:
            Most recent metric point if metric exists, None otherwise
        """
        metric_points = self._metrics.get(name)
        return metric_points[-1] if metric_points else None
    
    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()
        self._start_times.clear() 