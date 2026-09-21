#!/usr/bin/env python3
"""
Performance Optimization Orchestrator for DMLogn8n Platform
Central coordination of all performance optimization systems
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from performance_profiler import AdvancedProfiler, profile_function
from resource_optimizer import ResourceOptimizer, allocate_resources
from database_optimizer import DatabaseOptimizer
from cache_manager import CacheManager, cached
from network_optimizer import NetworkOptimizer, optimize_network
from ai_model_optimizer import AIModelOptimizer
from concurrency_manager import ConcurrencyManager, thread_pool, async_task
from cost_optimizer import CostOptimizer

logger = logging.getLogger(__name__)

class PerformanceOrchestrator:
    """Central orchestrator for all performance optimization systems"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.systems = {}
        self.metrics_history = []
        self.optimization_recommendations = []
        self.active_alerts = []

        # Initialize all performance systems
        self._initialize_systems()

        # Health monitoring
        self.health_status = {}
        self.last_health_check = None

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'profiler': {
                'enabled': True,
                'history_size': 10000,
                'prometheus_enabled': True,
                'prometheus_port': 8000
            },
            'resource_optimizer': {
                'enabled': True,
                'strategy': 'balanced',
                'auto_tuning': True
            },
            'database_optimizer': {
                'enabled': True,
                'auto_indexing': True,
                'query_caching': True,
                'slow_query_threshold': 1.0
            },
            'cache_manager': {
                'enabled': True,
                'auto_warming': True,
                'compression_enabled': True,
                'layers': {
                    'l1_memory': {'enabled': True, 'max_size_mb': 100},
                    'l2_disk': {'enabled': True, 'max_size_mb': 1000}
                }
            },
            'network_optimizer': {
                'enabled': True,
                'auto_compression': True,
                'connection_pooling': True,
                'adaptive_timeout': True
            },
            'ai_model_optimizer': {
                'enabled': True,
                'dynamic_batching': True,
                'auto_quantization': False
            },
            'concurrency_manager': {
                'enabled': True,
                'auto_scaling': True,
                'performance_monitoring': True
            },
            'cost_optimizer': {
                'enabled': True,
                'auto_optimization': False,
                'budget_monitoring': True
            },
            'global': {
                'monitoring_interval': 60.0,
                'optimization_interval': 300.0,
                'health_check_interval': 30.0,
                'alert_cooldown': 300.0  # 5 minutes
            }
        }

    def _initialize_systems(self):
        """Initialize all performance optimization systems"""
        # Performance Profiler
        if self.config['profiler']['enabled']:
            self.systems['profiler'] = AdvancedProfiler(self.config['profiler'])

        # Resource Optimizer
        if self.config['resource_optimizer']['enabled']:
            self.systems['resource_optimizer'] = ResourceOptimizer(self.config['resource_optimizer'])

        # Database Optimizer
        if self.config['database_optimizer']['enabled']:
            self.systems['database_optimizer'] = DatabaseOptimizer(self.config['database_optimizer'])

        # Cache Manager
        if self.config['cache_manager']['enabled']:
            self.systems['cache_manager'] = CacheManager(self.config['cache_manager'])

        # Network Optimizer
        if self.config['network_optimizer']['enabled']:
            self.systems['network_optimizer'] = NetworkOptimizer(self.config['network_optimizer'])

        # AI Model Optimizer
        if self.config['ai_model_optimizer']['enabled']:
            self.systems['ai_model_optimizer'] = AIModelOptimizer(self.config['ai_model_optimizer'])

        # Concurrency Manager
        if self.config['concurrency_manager']['enabled']:
            self.systems['concurrency_manager'] = ConcurrencyManager(self.config['concurrency_manager'])

        # Cost Optimizer
        if self.config['cost_optimizer']['enabled']:
            self.systems['cost_optimizer'] = CostOptimizer(self.config['cost_optimizer'])

        logger.info(f"Initialized {len(self.systems)} performance optimization systems")

    async def start_all(self):
        """Start all performance optimization systems"""
        logger.info("Starting all performance optimization systems")

        # Start each system
        for system_name, system in self.systems.items():
            try:
                if hasattr(system, 'start_monitoring'):
                    system.start_monitoring()
                if hasattr(system, 'start_background_tasks'):
                    system.start_background_tasks()
                logger.info(f"Started {system_name}")
            except Exception as e:
                logger.error(f"Failed to start {system_name}: {e}")

        # Start global monitoring
        await self._start_global_monitoring()

        logger.info("All performance optimization systems started")

    async def stop_all(self):
        """Stop all performance optimization systems"""
        logger.info("Stopping all performance optimization systems")

        # Stop global monitoring
        await self._stop_global_monitoring()

        # Stop each system
        for system_name, system in self.systems.items():
            try:
                if hasattr(system, 'stop_monitoring'):
                    system.stop_monitoring()
                if hasattr(system, 'stop_background_tasks'):
                    system.stop_background_tasks()
                if hasattr(system, 'cleanup'):
                    await system.cleanup()
                if hasattr(system, 'close_connections'):
                    await system.close_connections()
                logger.info(f"Stopped {system_name}")
            except Exception as e:
                logger.error(f"Failed to stop {system_name}: {e}")

        logger.info("All performance optimization systems stopped")

    async def _start_global_monitoring(self):
        """Start global monitoring and coordination"""
        # This would start a global monitoring loop
        # For now, it's a placeholder
        pass

    async def _stop_global_monitoring(self):
        """Stop global monitoring"""
        # This would stop the global monitoring loop
        pass

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all performance systems"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'systems': {},
            'overall_health': 'unknown',
            'active_alerts': len(self.active_alerts),
            'total_recommendations': len(self.optimization_recommendations)
        }

        # Get status from each system
        for system_name, system in self.systems.items():
            try:
                if hasattr(system, 'get_performance_report'):
                    system_status = system.get_performance_report()
                elif hasattr(system, 'get_resource_status'):
                    system_status = system.get_resource_status()
                elif hasattr(system, 'get_pool_status'):
                    system_status = system.get_pool_status()
                elif hasattr(system, 'get_cache_stats'):
                    system_status = system.get_cache_stats()
                else:
                    system_status = {'status': 'active', 'type': type(system).__name__}

                status['systems'][system_name] = system_status

            except Exception as e:
                status['systems'][system_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        # Calculate overall health
        healthy_systems = sum(1 for s in status['systems'].values()
                            if isinstance(s, dict) and s.get('status') != 'error')
        total_systems = len(status['systems'])

        if healthy_systems == total_systems:
            status['overall_health'] = 'healthy'
        elif healthy_systems > total_systems * 0.7:
            status['overall_health'] = 'degraded'
        else:
            status['overall_health'] = 'unhealthy'

        return status

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_systems': len(self.systems),
                'healthy_systems': 0,
                'total_recommendations': 0,
                'critical_alerts': 0
            },
            'system_reports': {},
            'cross_system_insights': [],
            'global_recommendations': []
        }

        # Get reports from each system
        for system_name, system in self.systems.items():
            try:
                if hasattr(system, 'get_performance_report'):
                    system_report = system.get_performance_report()
                elif hasattr(system, 'get_cost_report'):
                    system_report = system.get_cost_report()
                elif hasattr(system, 'get_optimization_report'):
                    system_report = system.get_optimization_report()
                else:
                    system_report = {'message': f'Report not available for {system_name}'}

                report['system_reports'][system_name] = system_report

                # Update summary
                if isinstance(system_report, dict) and system_report.get('error') is None:
                    report['summary']['healthy_systems'] += 1

                if isinstance(system_report, dict):
                    # Count recommendations
                    if 'recommendations' in system_report:
                        report['summary']['total_recommendations'] += len(system_report['recommendations'])
                    if 'optimizations' in system_report:
                        report['summary']['total_recommendations'] += system_report['optimizations'].get('total_opportunities', 0)

            except Exception as e:
                report['system_reports'][system_name] = {
                    'error': str(e)
                }

        # Generate cross-system insights
        report['cross_system_insights'] = self._generate_cross_system_insights()

        # Generate global recommendations
        report['global_recommendations'] = self._generate_global_recommendations()

        return report

    def _generate_cross_system_insights(self) -> List[str]:
        """Generate insights that span multiple systems"""
        insights = []

        # Resource utilization vs cost analysis
        if 'resource_optimizer' in self.systems and 'cost_optimizer' in self.systems:
            insights.append("Consider correlating resource utilization metrics with cost data to identify optimization opportunities")

        # Database performance vs caching effectiveness
        if 'database_optimizer' in self.systems and 'cache_manager' in self.systems:
            insights.append("Analyze database query patterns alongside cache hit rates to identify caching opportunities")

        # AI model performance vs resource usage
        if 'ai_model_optimizer' in self.systems and 'resource_optimizer' in self.systems:
            insights.append("Monitor AI model inference performance alongside CPU/GPU utilization for optimal resource allocation")

        # Concurrency vs network performance
        if 'concurrency_manager' in self.systems and 'network_optimizer' in self.systems:
            insights.append("Analyze concurrency patterns alongside network latency to optimize request batching")

        return insights

    def _generate_global_recommendations(self) -> List[str]:
        """Generate platform-wide optimization recommendations"""
        recommendations = []

        # Health-based recommendations
        unhealthy_systems = [name for name, system in self.systems.items()
                           if hasattr(system, 'get_performance_report') and
                              system.get_performance_report().get('error') is not None]

        if unhealthy_systems:
            recommendations.append(f"Address issues in unhealthy systems: {', '.join(unhealthy_systems)}")

        # Configuration recommendations
        if not self.config['database_optimizer']['auto_indexing']:
            recommendations.append("Consider enabling automatic database indexing for query optimization")

        if not self.config['cache_manager']['compression_enabled']:
            recommendations.append("Consider enabling cache compression to reduce memory usage")

        if not self.config['network_optimizer']['auto_compression']:
            recommendations.append("Consider enabling automatic network compression to reduce bandwidth usage")

        # Performance monitoring recommendations
        if not self.config['profiler']['prometheus_enabled']:
            recommendations.append("Consider enabling Prometheus metrics for advanced monitoring and alerting")

        # Auto-scaling recommendations
        if not self.config['concurrency_manager']['auto_scaling']:
            recommendations.append("Consider enabling auto-scaling for better resource utilization")

        return recommendations

    # Delegate methods to individual systems
    async def execute_with_profiling(self, func_name: str, *args, **kwargs):
        """Execute function with performance profiling"""
        if 'profiler' in self.systems:
            profiler = self.systems['profiler']
            return await profiler.profile_function(func_name, *args, **kwargs)
        else:
            # Fallback execution
            return func_name(*args, **kwargs)

    async def execute_with_optimization(self, func: callable, *args, **kwargs):
        """Execute function with all optimizations applied"""
        # This would apply multiple optimization layers
        result = func(*args, **kwargs)
        return result

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all systems"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'systems': {},
            'alerts': self.active_alerts.copy()
        }

        for system_name, system in self.systems.items():
            try:
                # Basic health check
                if hasattr(system, 'get_performance_report'):
                    report = system.get_performance_report()
                    if 'error' in report:
                        health_status['systems'][system_name] = {
                            'status': 'unhealthy',
                            'error': report['error']
                        }
                        health_status['overall_status'] = 'degraded'
                    else:
                        health_status['systems'][system_name] = {
                            'status': 'healthy',
                            'last_check': datetime.now().isoformat()
                        }
                else:
                    health_status['systems'][system_name] = {
                        'status': 'unknown',
                        'message': 'Health check not available'
                    }

            except Exception as e:
                health_status['systems'][system_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'

        return health_status

# Convenience decorators that use the orchestrator
def optimized_execution(orchestrator: PerformanceOrchestrator, system_name: str = None):
    """Decorator for optimized execution using orchestrator"""
    def decorator(func: callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Apply optimizations based on available systems
            if system_name and system_name in orchestrator.systems:
                # Use specific system optimization
                pass

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Example usage
async def main():
    """Example usage of the performance orchestrator"""

    # Initialize orchestrator
    orchestrator = PerformanceOrchestrator({
        'profiler': {'enabled': True, 'prometheus_enabled': True},
        'resource_optimizer': {'enabled': True, 'auto_tuning': True},
        'cache_manager': {'enabled': True, 'compression_enabled': True},
        'global': {'monitoring_interval': 30.0}
    })

    try:
        # Start all systems
        await orchestrator.start_all()

        # Get system status
        status = orchestrator.get_system_status()
        print(f"System Status: {json.dumps(status, indent=2, default=str)}")

        # Get comprehensive report
        report = orchestrator.get_comprehensive_report()
        print(f"Performance Report: {json.dumps(report, indent=2, default=str)}")

        # Run for a while to collect data
        await asyncio.sleep(10)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Stop all systems
        await orchestrator.stop_all()

if __name__ == "__main__":
    asyncio.run(main())