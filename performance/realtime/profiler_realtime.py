#!/usr/bin/env python3
"""
Real-time Profiler - Advanced Performance Monitoring and Analysis
Provides real-time performance profiling with detailed metrics and insights
"""

import time
import threading
import asyncio
import json
import psutil
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import inspect
from functools import wraps
from enum import Enum
import cProfile
import pstats
import io
from concurrent.futures import ThreadPoolExecutor
import weakref

class ProfileType(Enum):
    """Types of profiling"""
    FUNCTION = "function"
    DATABASE = "database"
    CACHE = "cache"
    WEBSOCKET = "websocket"
    MEMORY = "memory"
    NETWORK = "network"
    CUSTOM = "custom"

class AlertLevel(Enum):
    """Performance alert levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ProfileMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: float
    profile_type: ProfileType
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FunctionProfile:
    """Function execution profile"""
    function_name: str
    module_name: str
    execution_time_ms: float
    call_count: int
    avg_time_ms: float
    max_time_ms: float
    min_time_ms: float
    total_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float
    arguments_hash: str = ""

@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison"""
    metric_name: str
    baseline_value: float
    tolerance_percent: float
    created_time: float
    sample_size: int

class RealtimeProfiler:
    """Real-time performance profiling system"""

    def __init__(self, enable_continuous_profiling: bool = True,
                 sample_interval: float = 1.0):
        self.enable_continuous_profiling = enable_continuous_profiling
        self.sample_interval = sample_interval

        # Profile storage
        self.function_profiles: Dict[str, List[FunctionProfile]] = defaultdict(list)
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.performance_alerts: List[PerformanceAlert] = []
        self.baselines: Dict[str, PerformanceBaseline] = {}

        # Real-time metrics
        self.current_metrics: Dict[str, ProfileMetric] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Thresholds and alerts
        self.thresholds: Dict[str, Dict[str, float]] = {
            'function_time': {'warning': 100.0, 'error': 500.0, 'critical': 1000.0},
            'memory_usage': {'warning': 80.0, 'error': 90.0, 'critical': 95.0},
            'cpu_usage': {'warning': 70.0, 'error': 85.0, 'critical': 95.0},
            'response_time': {'warning': 200.0, 'error': 1000.0, 'critical': 5000.0},
            'error_rate': {'warning': 1.0, 'error': 5.0, 'critical': 10.0}
        }

        # Performance counters
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, float] = defaultdict(float)

        # Profiling state
        self.profiling_enabled = True
        self.active_profiles: Dict[str, cProfile.Profile] = {}
        self.profile_lock = threading.RLock()

        # Background monitoring
        self.running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.alert_thread: Optional[threading.Thread] = None

        # Performance regression detection
        self.regression_detection_enabled = True
        self.performance_history: Dict[str, List[float]] = defaultdict(list)

        # Setup logging
        self.logger = logging.getLogger("RealtimeProfiler")

        # Process information
        self.process = psutil.Process()

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize the profiler"""
        # Start background monitoring
        if self.enable_continuous_profiling:
            self._start_monitoring()

        # Set up signal handlers for graceful shutdown
        import signal
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)

    def _start_monitoring(self):
        """Start background monitoring threads"""
        self.running = True

        # Main monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ProfilerMonitor",
            daemon=True
        )
        self.monitoring_thread.start()

        # Alert processing thread
        self.alert_thread = threading.Thread(
            target=self._alert_processing_loop,
            name="AlertProcessor",
            daemon=True
        )
        self.alert_thread.start()

    def profile_function(self, profile_type: ProfileType = ProfileType.FUNCTION,
                        track_memory: bool = True, track_cpu: bool = True):
        """Decorator to profile function execution"""
        def decorator(func: Callable) -> Callable:
            function_name = f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.profiling_enabled:
                    return func(*args, **kwargs)

                return self._profile_function_execution(
                    func, args, kwargs, function_name,
                    profile_type, track_memory, track_cpu
                )

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.profiling_enabled:
                    return await func(*args, **kwargs)

                return await self._profile_async_function_execution(
                    func, args, kwargs, function_name,
                    profile_type, track_memory, track_cpu
                )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def _profile_function_execution(self, func: Callable, args: tuple,
                                  kwargs: dict, function_name: str,
                                  profile_type: ProfileType,
                                  track_memory: bool, track_cpu: bool) -> Any:
        """Profile synchronous function execution"""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024 * 1024) if track_memory else 0
        start_cpu = self.process.cpu_percent() if track_cpu else 0

        # Generate arguments hash for grouping
        args_hash = self._generate_args_hash(args, kwargs)

        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
            raise
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss / (1024 * 1024) if track_memory else 0
            end_cpu = self.process.cpu_percent() if track_cpu else 0

            execution_time_ms = (end_time - start_time) * 1000
            memory_usage_mb = end_memory - start_memory if track_memory else 0
            cpu_usage_percent = end_cpu - start_cpu if track_cpu else 0

            # Create profile
            profile = FunctionProfile(
                function_name=function_name,
                module_name=func.__module__,
                execution_time_ms=execution_time_ms,
                call_count=1,
                avg_time_ms=execution_time_ms,
                max_time_ms=execution_time_ms,
                min_time_ms=execution_time_ms,
                total_time_ms=execution_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                timestamp=start_time,
                arguments_hash=args_hash
            )

            # Store profile
            self._store_function_profile(function_name, profile)

            # Record metrics
            self._record_metric(f"function_time.{function_name}", execution_time_ms, "ms")
            if track_memory:
                self._record_metric(f"memory_usage.{function_name}", memory_usage_mb, "MB")
            if track_cpu:
                self._record_metric(f"cpu_usage.{function_name}", cpu_usage_percent, "%")

            # Check thresholds
            self._check_thresholds(f"function_time.{function_name}", execution_time_ms)

            # Log if needed
            if not success:
                self.logger.error(f"Function profile error: {function_name} - {error_message}")

        return result

    async def _profile_async_function_execution(self, func: Callable, args: tuple,
                                              kwargs: dict, function_name: str,
                                              profile_type: ProfileType,
                                              track_memory: bool, track_cpu: bool) -> Any:
        """Profile asynchronous function execution"""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024 * 1024) if track_memory else 0
        start_cpu = self.process.cpu_percent() if track_cpu else 0

        # Generate arguments hash for grouping
        args_hash = self._generate_args_hash(args, kwargs)

        try:
            result = await func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
            raise
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss / (1024 * 1024) if track_memory else 0
            end_cpu = self.process.cpu_percent() if track_cpu else 0

            execution_time_ms = (end_time - start_time) * 1000
            memory_usage_mb = end_memory - start_memory if track_memory else 0
            cpu_usage_percent = end_cpu - start_cpu if track_cpu else 0

            # Create profile
            profile = FunctionProfile(
                function_name=function_name,
                module_name=func.__module__,
                execution_time_ms=execution_time_ms,
                call_count=1,
                avg_time_ms=execution_time_ms,
                max_time_ms=execution_time_ms,
                min_time_ms=execution_time_ms,
                total_time_ms=execution_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                timestamp=start_time,
                arguments_hash=args_hash
            )

            # Store profile
            self._store_function_profile(function_name, profile)

            # Record metrics
            self._record_metric(f"function_time.{function_name}", execution_time_ms, "ms")
            if track_memory:
                self._record_metric(f"memory_usage.{function_name}", memory_usage_mb, "MB")
            if track_cpu:
                self._record_metric(f"cpu_usage.{function_name}", cpu_usage_percent, "%")

            # Check thresholds
            self._check_thresholds(f"function_time.{function_name}", execution_time_ms)

        return result

    def start_profiling(self, name: str):
        """Start detailed profiling for a section"""
        with self.profile_lock:
            if name in self.active_profiles:
                self.logger.warning(f"Profiling already active for {name}")
                return

            profile = cProfile.Profile()
            profile.enable()
            self.active_profiles[name] = profile

    def stop_profiling(self, name: str) -> Optional[Dict]:
        """Stop profiling and return results"""
        with self.profile_lock:
            profile = self.active_profiles.pop(name, None)
            if not profile:
                self.logger.warning(f"No active profiling for {name}")
                return None

            profile.disable()

            # Get statistics
            stats_stream = io.StringIO()
            stats = pstats.Stats(profile, stream=stats_stream)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # Top 20 functions

            return {
                'name': name,
                'stats': stats_stream.getvalue(),
                'total_calls': stats.total_calls
            }

    def record_metric(self, name: str, value: float, unit: str,
                     profile_type: ProfileType = ProfileType.CUSTOM,
                     metadata: Optional[Dict] = None):
        """Record a custom performance metric"""
        metric = ProfileMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            profile_type=profile_type,
            metadata=metadata or {}
        )

        self._record_metric(name, value, unit, profile_type, metadata)

    def _record_metric(self, name: str, value: float, unit: str,
                      profile_type: ProfileType = ProfileType.CUSTOM,
                      metadata: Optional[Dict] = None):
        """Internal metric recording"""
        metric = ProfileMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            profile_type=profile_type,
            metadata=metadata or {}
        )

        # Store current metric
        self.current_metrics[name] = metric

        # Add to history
        self.metric_history[name].append(metric)

        # Check thresholds
        self._check_thresholds(name, value)

        # Store in performance history for regression detection
        if self.regression_detection_enabled:
            self.performance_history[name].append(value)
            if len(self.performance_history[name]) > 100:
                self.performance_history[name] = self.performance_history[name][-50:]

    def _store_function_profile(self, function_name: str, profile: FunctionProfile):
        """Store function profile and update statistics"""
        with self.profile_lock:
            profiles = self.function_profiles[function_name]

            # Add new profile
            profiles.append(profile)

            # Update aggregated statistics
            if len(profiles) > 1:
                total_calls = len(profiles)
                total_time = sum(p.execution_time_ms for p in profiles)
                avg_time = total_time / total_calls
                max_time = max(p.execution_time_ms for p in profiles)
                min_time = min(p.execution_time_ms for p in profiles)

                # Update last profile with aggregated stats
                profiles[-1].call_count = total_calls
                profiles[-1].total_time_ms = total_time
                profiles[-1].avg_time_ms = avg_time
                profiles[-1].max_time_ms = max_time
                profiles[-1].min_time_ms = min_time

            # Keep only recent profiles
            if len(profiles) > 100:
                self.function_profiles[function_name] = profiles[-50:]

    def _check_thresholds(self, metric_name: str, value: float):
        """Check metric against thresholds and generate alerts"""
        # Determine threshold category
        category = None
        for cat in ['function_time', 'memory_usage', 'cpu_usage', 'response_time', 'error_rate']:
            if metric_name.startswith(cat):
                category = cat
                break

        if not category or category not in self.thresholds:
            return

        thresholds = self.thresholds[category]

        # Check each threshold level
        if value >= thresholds['critical']:
            self._create_alert(AlertLevel.CRITICAL, metric_name, value, thresholds['critical'])
        elif value >= thresholds['error']:
            self._create_alert(AlertLevel.ERROR, metric_name, value, thresholds['error'])
        elif value >= thresholds['warning']:
            self._create_alert(AlertLevel.WARNING, metric_name, value, thresholds['warning'])

    def _create_alert(self, level: AlertLevel, metric_name: str,
                     current_value: float, threshold_value: float):
        """Create performance alert"""
        alert = PerformanceAlert(
            alert_id=f"alert_{int(time.time() * 1000000)}_{metric_name}",
            level=level,
            message=f"Performance threshold exceeded for {metric_name}: {current_value:.2f} (threshold: {threshold_value:.2f})",
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=time.time()
        )

        self.performance_alerts.append(alert)

        # Log alert
        log_message = f"Performance Alert [{level.value.upper()}]: {alert.message}"
        if level == AlertLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == AlertLevel.ERROR:
            self.logger.error(log_message)
        elif level == AlertLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Keep only recent alerts
        if len(self.performance_alerts) > 1000:
            self.performance_alerts = self.performance_alerts[-500:]

    def _generate_args_hash(self, args: tuple, kwargs: dict) -> str:
        """Generate hash for function arguments"""
        try:
            # Convert args to string representation
            args_str = str(args) + str(sorted(kwargs.items()))
            return str(hash(args_str))
        except:
            return "unknown"

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                start_time = time.time()

                # Collect system metrics
                self._collect_system_metrics()

                # Detect performance regressions
                if self.regression_detection_enabled:
                    self._detect_regressions()

                # Cleanup old data
                self._cleanup_old_data()

                # Sleep for remaining time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.sample_interval - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = self.process.cpu_percent()
            self._record_metric("system.cpu_usage", cpu_percent, "%", ProfileType.CUSTOM)

            # Memory metrics
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self._record_metric("system.memory_usage", memory_mb, "MB", ProfileType.MEMORY)

            # Thread count
            thread_count = self.process.num_threads()
            self._record_metric("system.thread_count", thread_count, "count", ProfileType.CUSTOM)

            # File descriptors
            try:
                fd_count = self.process.num_fds()
                self._record_metric("system.fd_count", fd_count, "count", ProfileType.CUSTOM)
            except:
                pass

            # System-wide metrics
            system_memory = psutil.virtual_memory()
            self._record_metric("system.memory_total", system_memory.total / (1024 * 1024), "MB", ProfileType.CUSTOM)
            self._record_metric("system.memory_available", system_memory.available / (1024 * 1024), "MB", ProfileType.CUSTOM)
            self._record_metric("system.memory_percent", system_memory.percent, "%", ProfileType.CUSTOM)

        except Exception as e:
            self.logger.error(f"System metrics collection error: {e}")

    def _detect_regressions(self):
        """Detect performance regressions"""
        for metric_name, values in self.performance_history.items():
            if len(values) < 10:  # Need sufficient data
                continue

            # Compare recent performance with baseline
            recent_values = values[-5:]
            baseline_values = values[-20:-10] if len(values) >= 20 else values[:-5]

            if len(baseline_values) < 5:
                continue

            recent_avg = sum(recent_values) / len(recent_values)
            baseline_avg = sum(baseline_values) / len(baseline_values)

            # Check for significant degradation (>20% worse)
            if recent_avg > baseline_avg * 1.2:
                self._create_alert(
                    AlertLevel.WARNING,
                    f"regression.{metric_name}",
                    recent_avg,
                    baseline_avg * 1.2
                )

    def _cleanup_old_data(self):
        """Clean up old profiling data"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour ago

        # Clean old metrics
        for metric_name in list(self.metric_history.keys()):
            history = self.metric_history[metric_name]
            if history and history[0].timestamp < cutoff_time:
                # Keep only recent data
                self.metric_history[metric_name] = deque(
                    [m for m in history if m.timestamp > cutoff_time],
                    maxlen=1000
                )

        # Clean old alerts
        self.performance_alerts = [
            alert for alert in self.performance_alerts
            if alert.timestamp > cutoff_time
        ]

    def _alert_processing_loop(self):
        """Background thread for processing alerts"""
        while self.running:
            try:
                # Process recent alerts
                if self.performance_alerts:
                    recent_alerts = [
                        alert for alert in self.performance_alerts
                        if time.time() - alert.timestamp < 60  # Last minute
                    ]

                    # Check for alert patterns
                    self._analyze_alert_patterns(recent_alerts)

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")

    def _analyze_alert_patterns(self, alerts: List[PerformanceAlert]):
        """Analyze patterns in alerts"""
        if len(alerts) < 3:
            return

        # Group alerts by type
        alert_groups = defaultdict(list)
        for alert in alerts:
            alert_groups[alert.metric_name].append(alert)

        # Detect alert storms
        for metric_name, metric_alerts in alert_groups.items():
            if len(metric_alerts) >= 5:  # 5+ alerts for same metric
                self._create_alert(
                    AlertLevel.ERROR,
                    f"alert_storm.{metric_name}",
                    len(metric_alerts),
                    5.0
                )

    def set_threshold(self, category: str, level: str, value: float):
        """Set performance threshold"""
        if category not in self.thresholds:
            self.thresholds[category] = {}
        self.thresholds[category][level] = value

    def create_baseline(self, metric_name: str, sample_size: int = 100):
        """Create performance baseline from recent data"""
        if metric_name not in self.performance_history:
            self.logger.warning(f"No data available for baseline: {metric_name}")
            return

        values = self.performance_history[metric_name][-sample_size:]
        if len(values) < sample_size:
            self.logger.warning(f"Insufficient data for baseline: {metric_name}")
            return

        baseline_value = sum(values) / len(values)
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            baseline_value=baseline_value,
            tolerance_percent=10.0,  # 10% tolerance
            created_time=time.time(),
            sample_size=len(values)
        )

        self.baselines[metric_name] = baseline
        self.logger.info(f"Created baseline for {metric_name}: {baseline_value:.2f}")

    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': time.time(),
            'summary': {
                'total_functions_profiled': len(self.function_profiles),
                'total_metrics': len(self.current_metrics),
                'active_alerts': len(self.performance_alerts),
                'baselines_created': len(self.baselines)
            },
            'system_metrics': {},
            'top_slow_functions': [],
            'recent_alerts': [],
            'performance_trends': {}
        }

        # System metrics
        for name, metric in self.current_metrics.items():
            if name.startswith('system.'):
                report['system_metrics'][name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp
                }

        # Top slow functions
        function_stats = []
        for function_name, profiles in self.function_profiles.items():
            if profiles:
                latest_profile = profiles[-1]
                function_stats.append({
                    'name': function_name,
                    'avg_time_ms': latest_profile.avg_time_ms,
                    'max_time_ms': latest_profile.max_time_ms,
                    'call_count': latest_profile.call_count,
                    'total_time_ms': latest_profile.total_time_ms
                })

        function_stats.sort(key=lambda x: x['avg_time_ms'], reverse=True)
        report['top_slow_functions'] = function_stats[:10]

        # Recent alerts
        report['recent_alerts'] = [
            {
                'level': alert.level.value,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'metric_name': alert.metric_name,
                'current_value': alert.current_value
            }
            for alert in sorted(self.performance_alerts, key=lambda x: x.timestamp, reverse=True)[:10]
        ]

        # Performance trends
        for metric_name, history in list(self.metric_history.items())[:5]:
            if len(history) >= 2:
                recent_values = [m.value for m in list(history)[-10:]]
                trend = 'stable'
                if len(recent_values) >= 5:
                    if recent_values[-1] > recent_values[0] * 1.1:
                        trend = 'increasing'
                    elif recent_values[-1] < recent_values[0] * 0.9:
                        trend = 'decreasing'

                report['performance_trends'][metric_name] = {
                    'current_value': recent_values[-1],
                    'trend': trend,
                    'sample_count': len(recent_values)
                }

        return report

    def get_function_profile(self, function_name: str) -> Optional[Dict]:
        """Get detailed profile for a specific function"""
        profiles = self.function_profiles.get(function_name)
        if not profiles:
            return None

        latest_profile = profiles[-1]

        return {
            'function_name': latest_profile.function_name,
            'module_name': latest_profile.module_name,
            'call_count': latest_profile.call_count,
            'avg_time_ms': latest_profile.avg_time_ms,
            'max_time_ms': latest_profile.max_time_ms,
            'min_time_ms': latest_profile.min_time_ms,
            'total_time_ms': latest_profile.total_time_ms,
            'memory_usage_mb': latest_profile.memory_usage_mb,
            'cpu_usage_percent': latest_profile.cpu_usage_percent,
            'last_execution': latest_profile.timestamp,
            'performance_rating': self._get_performance_rating(latest_profile.avg_time_ms)
        }

    def _get_performance_rating(self, avg_time_ms: float) -> str:
        """Get performance rating based on execution time"""
        if avg_time_ms < 10:
            return "EXCELLENT"
        elif avg_time_ms < 50:
            return "GOOD"
        elif avg_time_ms < 100:
            return "ACCEPTABLE"
        elif avg_time_ms < 500:
            return "POOR"
        else:
            return "CRITICAL"

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        data = {
            'timestamp': time.time(),
            'metrics': {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp,
                    'type': metric.profile_type.value
                }
                for name, metric in self.current_metrics.items()
            },
            'alerts': [
                {
                    'level': alert.level.value,
                    'message': alert.message,
                    'metric_name': alert.metric_name,
                    'current_value': alert.current_value,
                    'threshold_value': alert.threshold_value,
                    'timestamp': alert.timestamp
                }
                for alert in self.performance_alerts
            ]
        }

        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.shutdown()

    def shutdown(self):
        """Shutdown the profiler"""
        self.running = False

        # Wait for threads
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.alert_thread:
            self.alert_thread.join(timeout=5)

        # Generate final report
        final_report = self.get_performance_report()
        self.logger.info("Final performance report generated")

        # Cleanup
        self.function_profiles.clear()
        self.current_metrics.clear()
        self.metric_history.clear()

        self.logger.info("Real-time profiler shutdown complete")

# Global profiler instance
realtime_profiler = RealtimeProfiler()

# Decorators for easy profiling
def profile_function(track_memory: bool = True, track_cpu: bool = True):
    """Decorator to profile function execution"""
    return realtime_profiler.profile_function(
        ProfileType.FUNCTION, track_memory, track_cpu
    )

def profile_database():
    """Decorator to profile database operations"""
    return realtime_profiler.profile_function(ProfileType.DATABASE)

def profile_cache():
    """Decorator to profile cache operations"""
    return realtime_profiler.profile_function(ProfileType.CACHE)

def track_performance(metric_name: str):
    """Decorator to track custom performance metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000
                realtime_profiler.record_metric(
                    metric_name, execution_time, "ms", ProfileType.CUSTOM
                )
        return wrapper
    return decorator

# Utility functions
def start_profiling(name: str):
    """Start detailed profiling"""
    realtime_profiler.start_profiling(name)

def stop_profiling(name: str) -> Optional[Dict]:
    """Stop profiling and get results"""
    return realtime_profiler.stop_profiling(name)

def get_performance_report() -> Dict:
    """Get current performance report"""
    return realtime_profiler.get_performance_report()

def record_metric(name: str, value: float, unit: str):
    """Record a performance metric"""
    realtime_profiler.record_metric(name, value, unit)