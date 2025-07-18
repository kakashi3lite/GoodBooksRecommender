"""
Model Performance Monitoring for GoodBooks Recommender

This module provides comprehensive monitoring of ML model performance,
including real-time metrics, drift detection, and alerting.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
from enum import Enum

from src.core.logging import StructuredLogger
from src.core.monitoring import MetricsCollector

logger = StructuredLogger(__name__)
metrics = MetricsCollector()


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    """Model metric types."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC = "auc"
    LATENCY = "latency_ms"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage_mb"
    CPU_USAGE = "cpu_usage_percent"


@dataclass
class ModelMetric:
    """Individual model metric measurement."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    model_id: str
    model_version: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceAlert:
    """Performance alert information."""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    current_value: float
    threshold: float
    model_id: str
    timestamp: datetime
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class DriftDetector:
    """Statistical drift detection for model performance."""
    
    def __init__(self, window_size: int = 100, sensitivity: float = 0.05):
        self.window_size = window_size
        self.sensitivity = sensitivity
        self.baseline_metrics: Dict[MetricType, deque] = {}
        self.current_metrics: Dict[MetricType, deque] = {}
        
    def add_baseline_metric(self, metric_type: MetricType, value: float):
        """Add a baseline metric value."""
        if metric_type not in self.baseline_metrics:
            self.baseline_metrics[metric_type] = deque(maxlen=self.window_size)
        self.baseline_metrics[metric_type].append(value)
    
    def add_current_metric(self, metric_type: MetricType, value: float):
        """Add a current metric value."""
        if metric_type not in self.current_metrics:
            self.current_metrics[metric_type] = deque(maxlen=self.window_size)
        self.current_metrics[metric_type].append(value)
    
    def detect_drift(self, metric_type: MetricType) -> Dict[str, Any]:
        """Detect if there's significant drift in a metric."""
        if metric_type not in self.baseline_metrics or metric_type not in self.current_metrics:
            return {"drift_detected": False, "reason": "insufficient_data"}
        
        baseline_values = list(self.baseline_metrics[metric_type])
        current_values = list(self.current_metrics[metric_type])
        
        if len(baseline_values) < 10 or len(current_values) < 10:
            return {"drift_detected": False, "reason": "insufficient_data"}
        
        # Simple statistical test (in production, use proper statistical tests)
        baseline_mean = np.mean(baseline_values)
        current_mean = np.mean(current_values)
        baseline_std = np.std(baseline_values)
        
        if baseline_std == 0:
            return {"drift_detected": False, "reason": "zero_variance"}
        
        # Z-score based drift detection
        z_score = abs(current_mean - baseline_mean) / baseline_std
        drift_detected = z_score > (1.96 * (1 - self.sensitivity))  # Rough approximation
        
        return {
            "drift_detected": drift_detected,
            "z_score": z_score,
            "baseline_mean": baseline_mean,
            "current_mean": current_mean,
            "baseline_std": baseline_std,
            "change_percentage": ((current_mean - baseline_mean) / baseline_mean) * 100 if baseline_mean != 0 else 0
        }


class ModelPerformanceMonitor:
    """Comprehensive model performance monitoring system."""
    
    def __init__(self, 
                 metrics_window_size: int = 1000,
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 drift_detection_enabled: bool = True):
        self.metrics_window_size = metrics_window_size
        self.alert_thresholds = alert_thresholds or {}
        self.drift_detection_enabled = drift_detection_enabled
        
        # Storage for metrics
        self.metrics_buffer: deque = deque(maxlen=metrics_window_size)
        self.aggregated_metrics: Dict[str, Dict[str, float]] = {}
        
        # Alert management
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Drift detection
        self.drift_detector = DriftDetector() if drift_detection_enabled else None
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start the performance monitoring system."""
        if self.monitoring_active:
            return
        
        logger.info("Starting model performance monitoring...")
        self.monitoring_active = True
        
        # Start background monitoring tasks
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Model performance monitoring started")
        
    async def stop_monitoring(self):
        """Stop the performance monitoring system."""
        if not self.monitoring_active:
            return
        
        logger.info("Stopping model performance monitoring...")
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Model performance monitoring stopped")
    
    async def record_metric(self, metric: ModelMetric):
        """Record a new model metric."""
        try:
            # Add to buffer
            self.metrics_buffer.append(metric)
            
            # Update aggregated metrics
            await self._update_aggregated_metrics(metric)
            
            # Check thresholds for alerts
            await self._check_alert_thresholds(metric)
            
            # Update drift detection
            if self.drift_detector:
                self.drift_detector.add_current_metric(metric.metric_type, metric.value)
            
            # Update Prometheus metrics
            metrics.histogram("model_metric_value", metric.value, {"metric_type": metric.metric_type.value})
            
        except Exception as e:
            logger.error(f"Failed to record metric: {str(e)}")
    
    async def record_prediction_metrics(self, 
                                      model_id: str,
                                      model_version: str,
                                      predictions: List[Any],
                                      actuals: List[Any] = None,
                                      latency_ms: float = None):
        """Record metrics from model predictions."""
        try:
            timestamp = datetime.utcnow()
            
            # Record latency if provided
            if latency_ms is not None:
                latency_metric = ModelMetric(
                    metric_type=MetricType.LATENCY,
                    value=latency_ms,
                    timestamp=timestamp,
                    model_id=model_id,
                    model_version=model_version
                )
                await self.record_metric(latency_metric)
            
            # Record throughput
            throughput_metric = ModelMetric(
                metric_type=MetricType.THROUGHPUT,
                value=len(predictions),
                timestamp=timestamp,
                model_id=model_id,
                model_version=model_version
            )
            await self.record_metric(throughput_metric)
            
            # Calculate accuracy if actuals provided
            if actuals and len(actuals) == len(predictions):
                accuracy = self._calculate_accuracy(predictions, actuals)
                accuracy_metric = ModelMetric(
                    metric_type=MetricType.ACCURACY,
                    value=accuracy,
                    timestamp=timestamp,
                    model_id=model_id,
                    model_version=model_version
                )
                await self.record_metric(accuracy_metric)
            
        except Exception as e:
            logger.error(f"Failed to record prediction metrics: {str(e)}")
    
    def _calculate_accuracy(self, predictions: List[Any], actuals: List[Any]) -> float:
        """Calculate prediction accuracy."""
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 0.0
        
        correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
        return correct / len(predictions)
    
    async def _update_aggregated_metrics(self, metric: ModelMetric):
        """Update aggregated metrics with new metric."""
        key = f"{metric.model_id}_{metric.metric_type.value}"
        
        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                'count': 0,
                'sum': 0.0,
                'min': float('inf'),
                'max': float('-inf'),
                'recent_values': deque(maxlen=100)
            }
        
        agg = self.aggregated_metrics[key]
        agg['count'] += 1
        agg['sum'] += metric.value
        agg['min'] = min(agg['min'], metric.value)
        agg['max'] = max(agg['max'], metric.value)
        agg['recent_values'].append(metric.value)
        agg['mean'] = agg['sum'] / agg['count']
        
        # Calculate standard deviation for recent values
        if len(agg['recent_values']) > 1:
            agg['std'] = np.std(list(agg['recent_values']))
        else:
            agg['std'] = 0.0
    
    async def _check_alert_thresholds(self, metric: ModelMetric):
        """Check if metric exceeds alert thresholds."""
        threshold_key = metric.metric_type.value
        
        if threshold_key not in self.alert_thresholds:
            return
        
        threshold = self.alert_thresholds[threshold_key]
        
        # Determine if threshold is exceeded (logic depends on metric type)
        alert_condition = False
        if metric.metric_type in [MetricType.ERROR_RATE, MetricType.LATENCY]:
            # Higher is worse
            alert_condition = metric.value > threshold
        elif metric.metric_type in [MetricType.ACCURACY, MetricType.PRECISION, MetricType.RECALL]:
            # Lower is worse
            alert_condition = metric.value < threshold
        
        if alert_condition:
            await self._create_alert(metric, threshold)
    
    async def _create_alert(self, metric: ModelMetric, threshold: float):
        """Create a performance alert."""
        alert_id = f"{metric.model_id}_{metric.metric_type.value}_{int(time.time())}"
        
        # Determine severity based on how much threshold is exceeded
        severity = self._determine_alert_severity(metric.value, threshold, metric.metric_type)
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            severity=severity,
            metric_type=metric.metric_type,
            message=f"Model {metric.model_id} {metric.metric_type.value} is {metric.value:.4f}, threshold: {threshold}",
            current_value=metric.value,
            threshold=threshold,
            model_id=metric.model_id,
            timestamp=metric.timestamp
        )
        
        self.active_alerts[alert_id] = alert
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")
        
        logger.warning(f"Performance alert created: {alert.message}")
        metrics.increment("performance_alerts_created", {"severity": severity.value})
    
    def _determine_alert_severity(self, value: float, threshold: float, metric_type: MetricType) -> AlertSeverity:
        """Determine alert severity based on threshold breach."""
        if metric_type in [MetricType.ERROR_RATE, MetricType.LATENCY]:
            # Higher is worse
            breach_ratio = value / threshold
        else:
            # Lower is worse
            breach_ratio = threshold / value if value > 0 else float('inf')
        
        if breach_ratio >= 2.0:
            return AlertSeverity.CRITICAL
        elif breach_ratio >= 1.5:
            return AlertSeverity.HIGH
        elif breach_ratio >= 1.2:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current aggregated metrics."""
        return {
            'total_metrics_recorded': len(self.metrics_buffer),
            'active_alerts_count': len(self.active_alerts),
            'aggregated_metrics': dict(self.aggregated_metrics),
            'monitoring_active': self.monitoring_active,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    async def get_model_metrics(self, model_id: str, metric_type: Optional[MetricType] = None) -> List[Dict[str, Any]]:
        """Get metrics for a specific model."""
        model_metrics = []
        
        for metric in self.metrics_buffer:
            if metric.model_id == model_id:
                if metric_type is None or metric.metric_type == metric_type:
                    model_metrics.append(metric.to_dict())
        
        return model_metrics
    
    async def get_drift_analysis(self, model_id: str) -> Dict[str, Any]:
        """Get drift analysis for a model."""
        if not self.drift_detector:
            return {"drift_detection_enabled": False}
        
        drift_results = {}
        
        for metric_type in MetricType:
            drift_result = self.drift_detector.detect_drift(metric_type)
            if drift_result.get("drift_detected"):
                drift_results[metric_type.value] = drift_result
        
        return {
            "drift_detection_enabled": True,
            "model_id": model_id,
            "drift_results": drift_results,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Perform drift detection
                if self.drift_detector:
                    await self._perform_drift_checks()
                
                # Clean up old resolved alerts
                await self._cleanup_old_alerts()
                
                # Update metrics
                metrics.gauge("active_alerts_count", len(self.active_alerts))
                metrics.gauge("metrics_buffer_size", len(self.metrics_buffer))
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
    
    async def _perform_drift_checks(self):
        """Perform drift detection checks."""
        try:
            for metric_type in MetricType:
                drift_result = self.drift_detector.detect_drift(metric_type)
                
                if drift_result.get("drift_detected"):
                    logger.warning(f"Drift detected for {metric_type.value}: {drift_result}")
                    metrics.increment("drift_detected", {"metric_type": metric_type.value})
                    
        except Exception as e:
            logger.error(f"Error in drift detection: {str(e)}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            alerts_to_remove = []
            for alert_id, alert in self.active_alerts.items():
                if alert.resolved and alert.timestamp < cutoff_time:
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.active_alerts[alert_id]
                
        except Exception as e:
            logger.error(f"Error cleaning up alerts: {str(e)}")
