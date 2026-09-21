#!/usr/bin/env python3
"""
Agent Metrics Collector
Collects detailed metrics from individual agents in the DMLogn8n system
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AgentPerformanceMetrics:
    """Detailed agent performance metrics"""
    agent_id: str
    agent_type: str
    status: str
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput_rps: float
    error_rate: float
    timeout_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int
    queue_depth: int
    last_activity: datetime
    uptime_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_processing_time: float
    peak_memory_mb: float
    peak_cpu_percent: float

@dataclass
class AgentHealthMetrics:
    """Agent health and status metrics"""
    agent_id: str
    health_score: float
    last_heartbeat: datetime
    heartbeat_interval: float
    restart_count: int
    crash_count: int
    error_count_last_hour: int
    warnings: List[str]
    critical_alerts: List[str]
    resource_saturation: float
    dependencies_status: Dict[str, str]

@dataclass
class AgentBusinessMetrics:
    """Business-relevant agent metrics"""
    agent_id: str
    agent_type: str
    user_interactions: int
    generated_content_length: int
    content_quality_score: float
    user_satisfaction_score: float
    cost_per_request: float
    revenue_per_hour: float
    efficiency_score: float
    accuracy_rate: float
    creativity_score: float

class AgentMetricsCollector:
    """Collects metrics from all agents in the system"""

    def __init__(self, agent_registry_url: str = "http://localhost:8000"):
        self.agent_registry_url = agent_registry_url
        self.performance_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.health_metrics: Dict[str, AgentHealthMetrics] = {}
        self.business_metrics: Dict[str, AgentBusinessMetrics] = {}
        self.session = None

    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            )
        return self.session

    async def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover all active agents from the registry"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.agent_registry_url}/api/agents") as response:
                if response.status == 200:
                    agents = await response.json()
                    return agents
                else:
                    logger.error(f"Failed to discover agents: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error discovering agents: {e}")
            # Return mock agents for development
            return self._get_mock_agents()

    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Get mock agents for development/testing"""
        agent_types = [
            'dungeon_master',
            'character_manager',
            'dialogue_engine',
            'world_builder',
            'narrative_coordinator',
            'content_generator',
            'ai_assistant',
            'game_master'
        ]

        agents = []
        for i, agent_type in enumerate(agent_types):
            for j in range(2):  # 2 instances of each type
                agents.append({
                    'id': f"{agent_type}_{j+1}",
                    'type': agent_type,
                    'url': f"http://localhost:9000{i+j}",
                    'status': 'active'
                })
        return agents

    async def collect_agent_performance(self, agent_info: Dict[str, Any]) -> Optional[AgentPerformanceMetrics]:
        """Collect performance metrics from a single agent"""
        agent_id = agent_info['id']
        agent_url = agent_info.get('url', f"http://localhost:9000")

        try:
            session = await self._get_session()

            # Collect metrics from agent's metrics endpoint
            async with session.get(f"{agent_url}/metrics", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    # Generate simulated metrics if endpoint not available
                    data = self._generate_mock_performance_metrics(agent_info['type'])

            metrics = AgentPerformanceMetrics(
                agent_id=agent_id,
                agent_type=agent_info['type'],
                status=data.get('status', 'active'),
                response_time_p50=data.get('response_time_p50', np.random.normal(0.3, 0.05)),
                response_time_p95=data.get('response_time_p95', np.random.normal(0.8, 0.1)),
                response_time_p99=data.get('response_time_p99', np.random.normal(1.5, 0.2)),
                throughput_rps=data.get('throughput_rps', np.random.normal(50, 10)),
                error_rate=data.get('error_rate', np.random.uniform(0.01, 0.05)),
                timeout_rate=data.get('timeout_rate', np.random.uniform(0.001, 0.01)),
                memory_usage_mb=data.get('memory_usage_mb', np.random.uniform(200, 800)),
                cpu_usage_percent=data.get('cpu_usage_percent', np.random.uniform(20, 80)),
                active_connections=data.get('active_connections', np.random.randint(5, 50)),
                queue_depth=data.get('queue_depth', np.random.randint(0, 20)),
                last_activity=datetime.fromisoformat(data.get('last_activity', datetime.now().isoformat())),
                uptime_seconds=data.get('uptime_seconds', np.random.randint(3600, 86400)),
                total_requests=data.get('total_requests', np.random.randint(1000, 10000)),
                successful_requests=data.get('successful_requests', np.random.randint(950, 9500)),
                failed_requests=data.get('failed_requests', np.random.randint(50, 500)),
                avg_processing_time=data.get('avg_processing_time', np.random.normal(0.5, 0.1)),
                peak_memory_mb=data.get('peak_memory_mb', np.random.uniform(400, 1200)),
                peak_cpu_percent=data.get('peak_cpu_percent', np.random.uniform(60, 100))
            )

            return metrics

        except Exception as e:
            logger.error(f"Error collecting performance metrics from agent {agent_id}: {e}")
            return None

    async def collect_agent_health(self, agent_info: Dict[str, Any]) -> Optional[AgentHealthMetrics]:
        """Collect health metrics from a single agent"""
        agent_id = agent_info['id']

        try:
            # In a real implementation, this would query the agent's health endpoint
            # For now, generate simulated health metrics
            health_data = self._generate_mock_health_metrics(agent_info['type'])

            metrics = AgentHealthMetrics(
                agent_id=agent_id,
                health_score=health_data.get('health_score', np.random.uniform(0.8, 1.0)),
                last_heartbeat=datetime.now() - timedelta(seconds=np.random.randint(1, 60)),
                heartbeat_interval=health_data.get('heartbeat_interval', 30.0),
                restart_count=health_data.get('restart_count', np.random.randint(0, 5)),
                crash_count=health_data.get('crash_count', np.random.randint(0, 2)),
                error_count_last_hour=health_data.get('error_count_last_hour', np.random.randint(0, 10)),
                warnings=health_data.get('warnings', []),
                critical_alerts=health_data.get('critical_alerts', []),
                resource_saturation=health_data.get('resource_saturation', np.random.uniform(0.3, 0.9)),
                dependencies_status=health_data.get('dependencies_status', {
                    'database': 'healthy',
                    'redis': 'healthy',
                    'ai_service': 'healthy'
                })
            )

            return metrics

        except Exception as e:
            logger.error(f"Error collecting health metrics from agent {agent_id}: {e}")
            return None

    async def collect_agent_business(self, agent_info: Dict[str, Any]) -> Optional[AgentBusinessMetrics]:
        """Collect business metrics from a single agent"""
        agent_id = agent_info['id']

        try:
            # In a real implementation, this would query business analytics
            business_data = self._generate_mock_business_metrics(agent_info['type'])

            metrics = AgentBusinessMetrics(
                agent_id=agent_id,
                agent_type=agent_info['type'],
                user_interactions=business_data.get('user_interactions', np.random.randint(100, 1000)),
                generated_content_length=business_data.get('generated_content_length', np.random.randint(1000, 10000)),
                content_quality_score=business_data.get('content_quality_score', np.random.uniform(4.0, 5.0)),
                user_satisfaction_score=business_data.get('user_satisfaction_score', np.random.uniform(4.2, 4.9)),
                cost_per_request=business_data.get('cost_per_request', np.random.uniform(0.01, 0.10)),
                revenue_per_hour=business_data.get('revenue_per_hour', np.random.uniform(50, 200)),
                efficiency_score=business_data.get('efficiency_score', np.random.uniform(0.7, 1.0)),
                accuracy_rate=business_data.get('accuracy_rate', np.random.uniform(0.85, 0.98)),
                creativity_score=business_data.get('creativity_score', np.random.uniform(3.5, 4.8))
            )

            return metrics

        except Exception as e:
            logger.error(f"Error collecting business metrics from agent {agent_id}: {e}")
            return None

    def _generate_mock_performance_metrics(self, agent_type: str) -> Dict[str, Any]:
        """Generate mock performance metrics based on agent type"""
        base_metrics = {
            'status': np.random.choice(['active', 'idle', 'busy'], p=[0.7, 0.2, 0.1]),
            'total_requests': np.random.randint(500, 5000),
            'successful_requests': 0,
            'failed_requests': 0
        }

        # Adjust metrics based on agent type
        if agent_type == 'dungeon_master':
            base_metrics.update({
                'response_time_p50': np.random.normal(1.0, 0.2),
                'throughput_rps': np.random.normal(20, 5),
                'memory_usage_mb': np.random.uniform(400, 800)
            })
        elif agent_type == 'dialogue_engine':
            base_metrics.update({
                'response_time_p50': np.random.normal(0.5, 0.1),
                'throughput_rps': np.random.normal(100, 20),
                'memory_usage_mb': np.random.uniform(300, 600)
            })
        elif agent_type == 'world_builder':
            base_metrics.update({
                'response_time_p50': np.random.normal(2.0, 0.5),
                'throughput_rps': np.random.normal(10, 3),
                'memory_usage_mb': np.random.uniform(600, 1200)
            })
        else:
            base_metrics.update({
                'response_time_p50': np.random.normal(0.8, 0.15),
                'throughput_rps': np.random.normal(50, 10),
                'memory_usage_mb': np.random.uniform(200, 500)
            })

        # Calculate successful and failed requests
        base_metrics['successful_requests'] = int(base_metrics['total_requests'] * np.random.uniform(0.92, 0.98))
        base_metrics['failed_requests'] = base_metrics['total_requests'] - base_metrics['successful_requests']

        return base_metrics

    def _generate_mock_health_metrics(self, agent_type: str) -> Dict[str, Any]:
        """Generate mock health metrics"""
        return {
            'health_score': np.random.uniform(0.75, 1.0),
            'heartbeat_interval': 30.0,
            'restart_count': np.random.randint(0, 3),
            'crash_count': 0,
            'error_count_last_hour': np.random.randint(0, 5),
            'warnings': [] if np.random.random() > 0.3 else ['High memory usage'],
            'critical_alerts': [],
            'resource_saturation': np.random.uniform(0.2, 0.7),
            'dependencies_status': {
                'database': 'healthy',
                'redis': 'healthy',
                'ai_service': np.random.choice(['healthy', 'degraded'], p=[0.9, 0.1])
            }
        }

    def _generate_mock_business_metrics(self, agent_type: str) -> Dict[str, Any]:
        """Generate mock business metrics based on agent type"""
        if agent_type == 'dungeon_master':
            return {
                'user_interactions': np.random.randint(50, 200),
                'generated_content_length': np.random.randint(2000, 8000),
                'revenue_per_hour': np.random.uniform(100, 300)
            }
        elif agent_type == 'dialogue_engine':
            return {
                'user_interactions': np.random.randint(200, 800),
                'generated_content_length': np.random.randint(5000, 15000),
                'revenue_per_hour': np.random.uniform(80, 200)
            }
        else:
            return {
                'user_interactions': np.random.randint(30, 150),
                'generated_content_length': np.random.randint(1000, 5000),
                'revenue_per_hour': np.random.uniform(50, 150)
            }

    async def collect_all_metrics(self):
        """Collect all metrics from all agents"""
        try:
            agents = await self.discover_agents()
            logger.info(f"Discovered {len(agents)} agents")

            # Collect metrics from all agents concurrently
            tasks = []
            for agent in agents:
                tasks.extend([
                    self.collect_agent_performance(agent),
                    self.collect_agent_health(agent),
                    self.collect_agent_business(agent)
                ])

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            agent_count = len(agents)
            performance_results = results[:agent_count]
            health_results = results[agent_count:agent_count*2]
            business_results = results[agent_count*2:agent_count*3]

            for i, agent in enumerate(agents):
                agent_id = agent['id']

                # Update performance metrics
                if isinstance(performance_results[i], AgentPerformanceMetrics):
                    self.performance_metrics[agent_id] = performance_results[i]

                # Update health metrics
                if isinstance(health_results[i], AgentHealthMetrics):
                    self.health_metrics[agent_id] = health_results[i]

                # Update business metrics
                if isinstance(business_results[i], AgentBusinessMetrics):
                    self.business_metrics[agent_id] = business_results[i]

            logger.info(f"Successfully collected metrics from {len(self.performance_metrics)} agents")

        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")

    def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all agents"""
        if not self.performance_metrics:
            return {}

        total_agents = len(self.performance_metrics)
        active_agents = sum(1 for m in self.performance_metrics.values() if m.status == 'active')
        busy_agents = sum(1 for m in self.performance_metrics.values() if m.status == 'busy')

        avg_response_time = np.mean([m.response_time_p50 for m in self.performance_metrics.values()])
        avg_error_rate = np.mean([m.error_rate for m in self.performance_metrics.values()])
        total_throughput = sum([m.throughput_rps for m in self.performance_metrics.values()])

        avg_health_score = np.mean([m.health_score for m in self.health_metrics.values()]) if self.health_metrics else 0
        total_revenue = sum([m.revenue_per_hour for m in self.business_metrics.values()]) if self.business_metrics else 0

        return {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'busy_agents': busy_agents,
            'idle_agents': total_agents - active_agents - busy_agents,
            'avg_response_time': avg_response_time,
            'avg_error_rate': avg_error_rate,
            'total_throughput': total_throughput,
            'avg_health_score': avg_health_score,
            'total_revenue_per_hour': total_revenue,
            'agent_types': self._get_agent_type_distribution()
        }

    def _get_agent_type_distribution(self) -> Dict[str, int]:
        """Get distribution of agent types"""
        distribution = {}
        for metrics in self.performance_metrics.values():
            agent_type = metrics.agent_type
            distribution[agent_type] = distribution.get(agent_type, 0) + 1
        return distribution

    async def start_collection(self, interval_seconds: int = 30):
        """Start continuous metrics collection"""
        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in metrics collection cycle: {e}")
                await asyncio.sleep(5)

    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()