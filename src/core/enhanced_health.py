"""
Enhanced Health Monitoring System for GoodBooks Recommender

This module provides comprehensive health monitoring including:
- Multi-component health checks
- Dependency status monitoring
- Performance thresholds
- Automated alerting
- Health history tracking
"""

import asyncio
import time
import psutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
import json

from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Component types for health monitoring."""
    DATABASE = "database"
    CACHE = "cache"
    MODEL = "model"
    EXTERNAL_API = "external_api"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"


@dataclass
class HealthThresholds:
    """Health check thresholds."""
    response_time_warning: float = 1.0  # seconds
    response_time_critical: float = 5.0  # seconds
    error_rate_warning: float = 0.05  # 5%
    error_rate_critical: float = 0.20  # 20%
    memory_usage_warning: float = 0.80  # 80%
    memory_usage_critical: float = 0.95  # 95%
    cpu_usage_warning: float = 0.80  # 80%
    cpu_usage_critical: float = 0.95  # 95%
    disk_usage_warning: float = 0.85  # 85%
    disk_usage_critical: float = 0.95  # 95%


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None
    metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['component_type'] = self.component_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    overall_status: HealthStatus
    timestamp: datetime
    component_results: List[HealthCheckResult]
    system_metrics: Dict[str, float]
    alerts: List[str]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'overall_status': self.overall_status.value,
            'timestamp': self.timestamp.isoformat(),
            'component_results': [result.to_dict() for result in self.component_results],
            'system_metrics': self.system_metrics,
            'alerts': self.alerts,
            'summary': self.summary
        }


class HealthChecker(ABC):
    """Abstract base class for health checkers."""
    
    def __init__(self, name: str, component_type: ComponentType, 
                 thresholds: Optional[HealthThresholds] = None):
        self.name = name
        self.component_type = component_type
        self.thresholds = thresholds or HealthThresholds()
        self.last_result: Optional[HealthCheckResult] = None
        self.check_count = 0
        self.failure_count = 0
    
    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Perform health check and return result."""
        pass
    
    def determine_status(self, response_time: float, error_rate: float = 0.0) -> HealthStatus:
        """Determine health status based on metrics."""
        if error_rate >= self.thresholds.error_rate_critical:
            return HealthStatus.CRITICAL
        if (response_time >= self.thresholds.response_time_critical or 
            error_rate >= self.thresholds.error_rate_warning):
            return HealthStatus.UNHEALTHY
        if response_time >= self.thresholds.response_time_warning:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
    
    async def run_check(self) -> HealthCheckResult:
        """Run health check with error handling."""
        self.check_count += 1
        start_time = time.time()
        
        try:
            result = await self.check_health()
            self.last_result = result
            
            if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                self.failure_count += 1
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            response_time = (time.time() - start_time) * 1000
            
            error_result = HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Health check failed: {str(e)}",
                details={"error_type": type(e).__name__},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
            
            self.last_result = error_result
            return error_result


class DatabaseHealthChecker(HealthChecker):
    """Database health checker."""
    
    def __init__(self, name: str, db_connection_func: Callable, 
                 thresholds: Optional[HealthThresholds] = None):
        super().__init__(name, ComponentType.DATABASE, thresholds)
        self.db_connection_func = db_connection_func
    
    async def check_health(self) -> HealthCheckResult:
        """Check database health."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            if asyncio.iscoroutinefunction(self.db_connection_func):
                connection = await self.db_connection_func()
            else:
                connection = self.db_connection_func()
            
            # Perform simple query
            if hasattr(connection, 'execute'):
                if asyncio.iscoroutinefunction(connection.execute):
                    await connection.execute("SELECT 1")
                else:
                    connection.execute("SELECT 1")
            
            response_time = (time.time() - start_time) * 1000
            status = self.determine_status(response_time / 1000)
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=response_time,
                message=f"Database responsive in {response_time:.2f}ms",
                details={"query": "SELECT 1"},
                timestamp=datetime.utcnow(),
                metrics={"response_time_ms": response_time}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error=str(e)
            )


class CacheHealthChecker(HealthChecker):
    """Cache health checker."""
    
    def __init__(self, name: str, cache_client: Any, 
                 thresholds: Optional[HealthThresholds] = None):
        super().__init__(name, ComponentType.CACHE, thresholds)
        self.cache_client = cache_client
    
    async def check_health(self) -> HealthCheckResult:
        """Check cache health."""
        start_time = time.time()
        test_key = f"health_check_{int(time.time())}"
        test_value = "test_value"
        
        try:
            # Test set operation
            if hasattr(self.cache_client, 'set'):
                if asyncio.iscoroutinefunction(self.cache_client.set):
                    await self.cache_client.set(test_key, test_value, ex=60)
                else:
                    self.cache_client.set(test_key, test_value, ex=60)
            elif hasattr(self.cache_client, 'setex'):
                if asyncio.iscoroutinefunction(self.cache_client.setex):
                    await self.cache_client.setex(test_key, 60, test_value)
                else:
                    self.cache_client.setex(test_key, 60, test_value)
            
            # Test get operation
            if hasattr(self.cache_client, 'get'):
                if asyncio.iscoroutinefunction(self.cache_client.get):
                    retrieved_value = await self.cache_client.get(test_key)
                else:
                    retrieved_value = self.cache_client.get(test_key)
            
            # Test delete operation
            if hasattr(self.cache_client, 'delete'):
                if asyncio.iscoroutinefunction(self.cache_client.delete):
                    await self.cache_client.delete(test_key)
                else:
                    self.cache_client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            # Verify operations worked
            operations_success = retrieved_value == test_value
            status = (self.determine_status(response_time / 1000) 
                     if operations_success else HealthStatus.DEGRADED)
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=response_time,
                message=f"Cache operations completed in {response_time:.2f}ms",
                details={
                    "operations_tested": ["set", "get", "delete"],
                    "operations_success": operations_success
                },
                timestamp=datetime.utcnow(),
                metrics={"response_time_ms": response_time}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Cache operations failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error=str(e)
            )


class ModelHealthChecker(HealthChecker):
    """ML Model health checker."""
    
    def __init__(self, name: str, model_manager: Any, 
                 thresholds: Optional[HealthThresholds] = None):
        super().__init__(name, ComponentType.MODEL, thresholds)
        self.model_manager = model_manager
    
    async def check_health(self) -> HealthCheckResult:
        """Check model health."""
        start_time = time.time()
        
        try:
            # Check if model is loaded
            if hasattr(self.model_manager, 'current_model'):
                model_loaded = self.model_manager.current_model is not None
            else:
                model_loaded = True  # Assume loaded if no direct access
            
            # Test prediction if possible
            prediction_success = True
            if hasattr(self.model_manager, 'get_model_health'):
                health_info = self.model_manager.get_model_health()
                model_loaded = health_info.get('status') != 'no_model'
                prediction_success = health_info.get('model_responsive', True)
            
            response_time = (time.time() - start_time) * 1000
            
            if not model_loaded:
                status = HealthStatus.CRITICAL
                message = "Model not loaded"
            elif not prediction_success:
                status = HealthStatus.DEGRADED
                message = "Model loaded but not responsive"
            else:
                status = self.determine_status(response_time / 1000)
                message = f"Model healthy, checked in {response_time:.2f}ms"
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    "model_loaded": model_loaded,
                    "prediction_success": prediction_success
                },
                timestamp=datetime.utcnow(),
                metrics={"response_time_ms": response_time}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"Model health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error=str(e)
            )


class SystemResourceChecker(HealthChecker):
    """System resource health checker."""
    
    def __init__(self, name: str = "system_resources", 
                 thresholds: Optional[HealthThresholds] = None):
        super().__init__(name, ComponentType.MEMORY, thresholds)
    
    async def check_health(self) -> HealthCheckResult:
        """Check system resource health."""
        start_time = time.time()
        
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            
            memory_usage = memory.percent / 100.0
            cpu_usage = cpu_percent / 100.0
            disk_usage = disk.percent / 100.0
            
            # Determine overall status based on worst metric
            status = HealthStatus.HEALTHY
            alerts = []
            
            if (memory_usage >= self.thresholds.memory_usage_critical or
                cpu_usage >= self.thresholds.cpu_usage_critical or
                disk_usage >= self.thresholds.disk_usage_critical):
                status = HealthStatus.CRITICAL
            elif (memory_usage >= self.thresholds.memory_usage_warning or
                  cpu_usage >= self.thresholds.cpu_usage_warning or
                  disk_usage >= self.thresholds.disk_usage_warning):
                status = HealthStatus.DEGRADED
            
            # Generate alerts
            if memory_usage >= self.thresholds.memory_usage_warning:
                alerts.append(f"High memory usage: {memory_usage:.1%}")
            if cpu_usage >= self.thresholds.cpu_usage_warning:
                alerts.append(f"High CPU usage: {cpu_usage:.1%}")
            if disk_usage >= self.thresholds.disk_usage_warning:
                alerts.append(f"High disk usage: {disk_usage:.1%}")
            
            response_time = (time.time() - start_time) * 1000
            
            message = f"System resources checked in {response_time:.2f}ms"
            if alerts:
                message += f" - {'; '.join(alerts)}"
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                response_time_ms=response_time,
                message=message,
                details={
                    "memory_usage_percent": memory_usage * 100,
                    "cpu_usage_percent": cpu_usage * 100,
                    "disk_usage_percent": disk_usage * 100,
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024)
                },
                timestamp=datetime.utcnow(),
                metrics={
                    "memory_usage": memory_usage,
                    "cpu_usage": cpu_usage,
                    "disk_usage": disk_usage,
                    "response_time_ms": response_time
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.CRITICAL,
                response_time_ms=response_time,
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                error=str(e)
            )


class HealthMonitor:
    """
    Comprehensive health monitoring system.
    
    Features:
    - Multiple health checker registration
    - Periodic health checks
    - Health history tracking
    - Alert generation
    - Configurable thresholds
    """
    
    def __init__(self, check_interval: int = 30, history_retention_hours: int = 24):
        self.check_interval = check_interval
        self.history_retention_hours = history_retention_hours
        
        self.health_checkers: List[HealthChecker] = []
        self.health_history: List[SystemHealthReport] = []
        self.alert_callbacks: List[Callable] = []
        self.thresholds = HealthThresholds()
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._last_report: Optional[SystemHealthReport] = None
    
    def register_checker(self, checker: HealthChecker):
        """Register a health checker."""
        self.health_checkers.append(checker)
        logger.info(f"Registered health checker: {checker.name}")
    
    def register_alert_callback(self, callback: Callable[[SystemHealthReport], None]):
        """Register an alert callback function."""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._running:
            logger.warning("Health monitoring already running")
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started health monitoring with {len(self.health_checkers)} checkers")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped health monitoring")
    
    async def run_health_check(self) -> SystemHealthReport:
        """Run a complete health check and return the report."""
        if not self.health_checkers:
            logger.warning("No health checkers registered")
            return SystemHealthReport(
                overall_status=HealthStatus.UNKNOWN,
                timestamp=datetime.utcnow(),
                component_results=[],
                system_metrics={},
                alerts=["No health checkers registered"],
                summary={"status": "no_checkers"}
            )
        
        # Run all health checks concurrently
        check_tasks = [checker.run_check() for checker in self.health_checkers]
        component_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(component_results):
            if isinstance(result, Exception):
                logger.error(f"Health checker {self.health_checkers[i].name} failed: {result}")
                # Create a failure result
                valid_results.append(HealthCheckResult(
                    component_name=self.health_checkers[i].name,
                    component_type=self.health_checkers[i].component_type,
                    status=HealthStatus.CRITICAL,
                    response_time_ms=0.0,
                    message=f"Health check exception: {result}",
                    details={"exception": str(result)},
                    timestamp=datetime.utcnow(),
                    error=str(result)
                ))
            else:
                valid_results.append(result)
        
        # Determine overall status
        overall_status = self._determine_overall_status(valid_results)
        
        # Calculate system metrics
        system_metrics = self._calculate_system_metrics(valid_results)
        
        # Generate alerts
        alerts = self._generate_alerts(valid_results)
        
        # Create summary
        summary = self._create_summary(valid_results, overall_status)
        
        report = SystemHealthReport(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            component_results=valid_results,
            system_metrics=system_metrics,
            alerts=alerts,
            summary=summary
        )
        
        # Store in history
        self._store_in_history(report)
        
        # Send alerts if needed
        await self._send_alerts(report)
        
        self._last_report = report
        return report
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary."""
        if not self._last_report:
            return {"status": "unknown", "message": "No health checks run yet"}
        
        return {
            "overall_status": self._last_report.overall_status.value,
            "timestamp": self._last_report.timestamp.isoformat(),
            "component_count": len(self._last_report.component_results),
            "healthy_components": len([
                r for r in self._last_report.component_results 
                if r.status == HealthStatus.HEALTHY
            ]),
            "alerts_count": len(self._last_report.alerts),
            "summary": self._last_report.summary
        }
    
    def get_health_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_history = [
            report.to_dict() for report in self.health_history
            if report.timestamp >= cutoff_time
        ]
        
        return recent_history
    
    def get_component_health(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific component."""
        if not self._last_report:
            return None
        
        for result in self._last_report.component_results:
            if result.component_name == component_name:
                return result.to_dict()
        
        return None
    
    # Private methods
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self.run_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring loop error: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status."""
        if not results:
            return HealthStatus.UNKNOWN
        
        status_counts = {status: 0 for status in HealthStatus}
        for result in results:
            status_counts[result.status] += 1
        
        # Determine overall status based on worst component
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _calculate_system_metrics(self, results: List[HealthCheckResult]) -> Dict[str, float]:
        """Calculate aggregated system metrics."""
        if not results:
            return {}
        
        response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]
        
        metrics = {
            "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "component_count": len(results),
            "healthy_components": len([r for r in results if r.status == HealthStatus.HEALTHY]),
            "degraded_components": len([r for r in results if r.status == HealthStatus.DEGRADED]),
            "unhealthy_components": len([r for r in results if r.status == HealthStatus.UNHEALTHY]),
            "critical_components": len([r for r in results if r.status == HealthStatus.CRITICAL])
        }
        
        # Add component-specific metrics
        for result in results:
            if result.metrics:
                for key, value in result.metrics.items():
                    metrics[f"{result.component_name}_{key}"] = value
        
        return metrics
    
    def _generate_alerts(self, results: List[HealthCheckResult]) -> List[str]:
        """Generate alerts based on health check results."""
        alerts = []
        
        for result in results:
            if result.status == HealthStatus.CRITICAL:
                alerts.append(f"CRITICAL: {result.component_name} - {result.message}")
            elif result.status == HealthStatus.UNHEALTHY:
                alerts.append(f"UNHEALTHY: {result.component_name} - {result.message}")
            elif result.status == HealthStatus.DEGRADED:
                alerts.append(f"DEGRADED: {result.component_name} - {result.message}")
        
        return alerts
    
    def _create_summary(self, results: List[HealthCheckResult], 
                       overall_status: HealthStatus) -> Dict[str, Any]:
        """Create health check summary."""
        status_distribution = {}
        for status in HealthStatus:
            count = len([r for r in results if r.status == status])
            if count > 0:
                status_distribution[status.value] = count
        
        return {
            "overall_status": overall_status.value,
            "total_components": len(results),
            "status_distribution": status_distribution,
            "check_timestamp": datetime.utcnow().isoformat(),
            "issues_detected": len([r for r in results if r.status not in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]])
        }
    
    def _store_in_history(self, report: SystemHealthReport):
        """Store health report in history with retention policy."""
        self.health_history.append(report)
        
        # Clean up old history
        cutoff_time = datetime.utcnow() - timedelta(hours=self.history_retention_hours)
        self.health_history = [
            r for r in self.health_history 
            if r.timestamp >= cutoff_time
        ]
    
    async def _send_alerts(self, report: SystemHealthReport):
        """Send alerts to registered callbacks."""
        if report.alerts and self.alert_callbacks:
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(report)
                    else:
                        callback(report)
                except Exception as e:
                    logger.error(f"Alert callback failed: {str(e)}")


# Example usage and helper functions

def create_default_health_monitor() -> HealthMonitor:
    """Create a health monitor with default system checkers."""
    monitor = HealthMonitor(check_interval=30)
    
    # Add system resource checker
    monitor.register_checker(SystemResourceChecker())
    
    return monitor


async def simple_alert_callback(report: SystemHealthReport):
    """Simple alert callback that logs alerts."""
    if report.alerts:
        for alert in report.alerts:
            logger.warning(f"Health Alert: {alert}")


def setup_basic_health_monitoring(db_connection_func: Optional[Callable] = None,
                                cache_client: Any = None,
                                model_manager: Any = None) -> HealthMonitor:
    """Setup basic health monitoring with common components."""
    monitor = create_default_health_monitor()
    
    # Register alert callback
    monitor.register_alert_callback(simple_alert_callback)
    
    # Add database checker if provided
    if db_connection_func:
        monitor.register_checker(DatabaseHealthChecker("main_database", db_connection_func))
    
    # Add cache checker if provided
    if cache_client:
        monitor.register_checker(CacheHealthChecker("redis_cache", cache_client))
    
    # Add model checker if provided
    if model_manager:
        monitor.register_checker(ModelHealthChecker("ml_models", model_manager))
    
    return monitor


# Alias for backward compatibility
EnhancedHealthChecker = HealthMonitor
