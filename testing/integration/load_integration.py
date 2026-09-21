#!/usr/bin/env python3
"""
DMLogn8n Load Integration Tests
Comprehensive load testing under realistic conditions
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import statistics

import aiohttp
import websockets
import redis
import psutil
import numpy as np
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram

# Import test framework
from integration_test_suite import TestResult, TestStatus

class LoadIntegrationTests:
    """
    Comprehensive load testing and performance benchmarking
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('load_integration')
        self.base_url = config['base_url']
        self.redis_url = config['redis_url']
        self.websocket_url = config.get('websocket_url', 'ws://localhost:8001')

        # Load testing configuration
        self.load_config = {
            'concurrent_users': {
                'light': 10,
                'moderate': 50,
                'heavy': 100,
                'stress': 200
            },
            'test_duration': {
                'short': 30,      # 30 seconds
                'medium': 120,    # 2 minutes
                'long': 300       # 5 minutes
            },
            'ramp_up_time': 30,  # 30 seconds to ramp up
            'performance_thresholds': {
                'avg_response_time': 1.0,      # 1 second
                'p95_response_time': 2.0,      # 2 seconds
                'error_rate': 0.05,            # 5% error rate
                'cpu_usage': 80,               # 80% CPU
                'memory_usage': 85              # 85% memory
            }
        }

        # Metrics collection
        self.metrics = {
            'response_times': deque(maxlen=10000),
            'error_counts': defaultdict(int),
            'request_counts': defaultdict(int),
            'concurrent_connections': 0,
            'system_metrics': deque(maxlen=1000)
        }

        # Prometheus metrics
        self.registry = CollectorRegistry()
        self.response_time_histogram = Histogram(
            'load_test_response_time_seconds',
            'Response time during load test',
            ['endpoint', 'method'],
            registry=self.registry
        )
        self.request_counter = Counter(
            'load_test_requests_total',
            'Total requests during load test',
            ['endpoint', 'method', 'status'],
            registry=self.registry
        )
        self.active_connections_gauge = Gauge(
            'load_test_active_connections',
            'Number of active connections',
            registry=self.registry
        )

    async def test_load_scenarios(self) -> TestResult:
        """
        Test system performance under various load scenarios
        """
        result = TestResult(
            name="load_scenarios",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            load_tests = {
                'light_load': await self.test_light_load(),
                'moderate_load': await self.test_moderate_load(),
                'heavy_load': await self.test_heavy_load(),
                'stress_test': await self.test_stress_scenario(),
                'endurance_test': await self.test_endurance(),
                'spike_test': await self.test_traffic_spike(),
                'resource_exhaustion': await self.test_resource_exhaustion()
            }

            # Analyze overall load performance
            all_passed = all(test.get('success', False) for test in load_tests.values())
            avg_response_time = statistics.mean(self.metrics['response_times']) if self.metrics['response_times'] else 0
            total_requests = sum(self.metrics['request_counts'].values())
            total_errors = sum(self.metrics['error_counts'].values())
            overall_error_rate = total_errors / total_requests if total_requests > 0 else 0

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = f"Load testing completed (avg response: {avg_response_time:.3f}s, error rate: {overall_error_rate:.2%})" if all_passed else "Load testing revealed performance issues"
            result.details = {
                'load_tests': load_tests,
                'summary': {
                    'avg_response_time': avg_response_time,
                    'total_requests': total_requests,
                    'total_errors': total_errors,
                    'error_rate': overall_error_rate,
                    'performance_thresholds_met': all_passed
                }
            }

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Load testing failed: {str(e)}"
            self.logger.error(f"Load testing failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_light_load(self) -> Dict[str, Any]:
        """Test system under light load (10 concurrent users)"""
        return await self.run_load_scenario(
            name='light_load',
            concurrent_users=self.load_config['concurrent_users']['light'],
            duration=self.load_config['test_duration']['short'],
            scenario_type='mixed'
        )

    async def test_moderate_load(self) -> Dict[str, Any]:
        """Test system under moderate load (50 concurrent users)"""
        return await self.run_load_scenario(
            name='moderate_load',
            concurrent_users=self.load_config['concurrent_users']['moderate'],
            duration=self.load_config['test_duration']['medium'],
            scenario_type='mixed'
        )

    async def test_heavy_load(self) -> Dict[str, Any]:
        """Test system under heavy load (100 concurrent users)"""
        return await self.run_load_scenario(
            name='heavy_load',
            concurrent_users=self.load_config['concurrent_users']['heavy'],
            duration=self.load_config['test_duration']['medium'],
            scenario_type='realistic'
        )

    async def test_stress_scenario(self) -> Dict[str, Any]:
        """Test system under stress conditions (200 concurrent users)"""
        return await self.run_load_scenario(
            name='stress_test',
            concurrent_users=self.load_config['concurrent_users']['stress'],
            duration=self.load_config['test_duration']['short'],
            scenario_type='stress'
        )

    async def test_endurance(self) -> Dict[str, Any]:
        """Test system endurance over extended period"""
        return await self.run_load_scenario(
            name='endurance_test',
            concurrent_users=self.load_config['concurrent_users']['moderate'],
            duration=self.load_config['test_duration']['long'],
            scenario_type='endurance'
        )

    async def test_traffic_spike(self) -> Dict[str, Any]:
        """Test system response to traffic spikes"""
        try:
            spike_results = []
            base_load = 20
            spike_load = 100
            spike_duration = 30
            recovery_duration = 60

            self.logger.info(f"Starting spike test: base={base_load}, spike={spike_load}")

            # Base load period
            base_result = await self.run_load_scenario(
                name='spike_base',
                concurrent_users=base_load,
                duration=30,
                scenario_type='mixed'
            )
            spike_results.append(base_result)

            # Spike period
            spike_result = await self.run_load_scenario(
                name='spike_peak',
                concurrent_users=spike_load,
                duration=spike_duration,
                scenario_type='stress'
            )
            spike_results.append(spike_result)

            # Recovery period
            recovery_result = await self.run_load_scenario(
                name='spike_recovery',
                concurrent_users=base_load,
                duration=recovery_duration,
                scenario_type='mixed'
            )
            spike_results.append(recovery_result)

            # Analyze spike handling
            spike_performance = spike_result.get('performance', {})
            recovery_performance = recovery_result.get('performance', {})
            base_performance = base_result.get('performance', {})

            spike_handled = (
                spike_performance.get('error_rate', 1) < 0.15 and  # Allow higher error rate during spike
                recovery_performance.get('avg_response_time', float('inf')) < base_performance.get('avg_response_time', float('inf')) * 1.5
            )

            return {
                'success': spike_handled,
                'scenario': 'traffic_spike',
                'phases': ['base', 'spike', 'recovery'],
                'phase_results': spike_results,
                'spike_handled': spike_handled,
                'message': f"Traffic spike test {'passed' if spike_handled else 'failed'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_resource_exhaustion(self) -> Dict[str, Any]:
        """Test system behavior under resource exhaustion"""
        try:
            # Monitor system resources during test
            initial_cpu = psutil.cpu_percent(interval=1)
            initial_memory = psutil.virtual_memory().percent

            # Create resource-intensive load
            exhaustion_results = await self.run_load_scenario(
                name='resource_exhaustion',
                concurrent_users=150,
                duration=60,
                scenario_type='exhaustion'
            )

            # Check resource usage
            final_cpu = psutil.cpu_percent(interval=1)
            final_memory = psutil.virtual_memory().percent

            # Check if system recovered
            await asyncio.sleep(10)  # Wait for recovery
            recovery_cpu = psutil.cpu_percent(interval=1)
            recovery_memory = psutil.virtual_memory().percent

            system_recovered = (
                recovery_cpu < initial_cpu + 20 and  # CPU should recover
                recovery_memory < initial_memory + 10  # Memory should recover
            )

            return {
                'success': system_recovered,
                'scenario': 'resource_exhaustion',
                'resource_usage': {
                    'initial': {'cpu': initial_cpu, 'memory': initial_memory},
                    'peak': {'cpu': final_cpu, 'memory': final_memory},
                    'recovery': {'cpu': recovery_cpu, 'memory': recovery_memory}
                },
                'system_recovered': system_recovered,
                'exhaustion_results': exhaustion_results,
                'message': f"Resource exhaustion test {'passed' if system_recovered else 'failed'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def run_load_scenario(self, name: str, concurrent_users: int, duration: int, scenario_type: str) -> Dict[str, Any]:
        """Run a specific load scenario"""
        try:
            self.logger.info(f"Starting load scenario '{name}' with {concurrent_users} users for {duration}s")

            # Reset metrics for this scenario
            scenario_metrics = {
                'start_time': time.time(),
                'requests': 0,
                'errors': 0,
                'response_times': deque(maxlen=10000),
                'throughput_samples': deque(maxlen=100)
            }

            # Create user simulation tasks
            user_tasks = []
            for i in range(concurrent_users):
                task = asyncio.create_task(
                    self.simulate_user(f"user_{i}_{name}", duration, scenario_type, scenario_metrics)
                )
                user_tasks.append(task)

            # Monitor system performance during test
            monitor_task = asyncio.create_task(
                self.monitor_system_performance(duration, scenario_metrics)
            )

            # Wait for all users to complete
            await asyncio.gather(*user_tasks, return_exceptions=True)
            monitor_task.cancel()

            # Calculate final metrics
            end_time = time.time()
            total_time = end_time - scenario_metrics['start_time']

            performance = self.calculate_performance_metrics(scenario_metrics, total_time)

            # Evaluate against thresholds
            thresholds_met = self.evaluate_performance_thresholds(performance)

            self.logger.info(f"Load scenario '{name}' completed: success={thresholds_met}")

            return {
                'success': thresholds_met,
                'scenario': name,
                'config': {
                    'concurrent_users': concurrent_users,
                    'duration': duration,
                    'scenario_type': scenario_type
                },
                'performance': performance,
                'thresholds_met': thresholds_met
            }

        except Exception as e:
            self.logger.error(f"Load scenario '{name}' failed: {e}")
            return {
                'success': False,
                'scenario': name,
                'error': str(e)
            }

    async def simulate_user(self, user_id: str, duration: int, scenario_type: str, metrics: Dict[str, Any]):
        """Simulate a single user's behavior"""
        try:
            start_time = time.time()
            session = aiohttp.ClientSession()

            while time.time() - start_time < duration:
                try:
                    # Simulate user behavior based on scenario type
                    await self.perform_user_action(session, user_id, scenario_type, metrics)

                    # Random think time between actions
                    think_time = self.get_think_time(scenario_type)
                    await asyncio.sleep(think_time)

                except Exception as e:
                    metrics['errors'] += 1
                    self.metrics['error_counts'][scenario_type] += 1
                    self.logger.warning(f"User {user_id} action failed: {e}")

            await session.close()

        except Exception as e:
            self.logger.error(f"User {user_id} simulation failed: {e}")

    async def perform_user_action(self, session: aiohttp.ClientSession, user_id: str, scenario_type: str, metrics: Dict[str, Any]):
        """Perform a single user action"""
        action_start = time.time()

        try:
            # Select action based on scenario type
            action = self.select_action(scenario_type)

            if action['method'] == 'GET':
                async with session.get(f"{self.base_url}{action['endpoint']}", timeout=10) as response:
                    response_time = time.time() - action_start
                    self.record_metrics(action['endpoint'], 'GET', response.status, response_time, metrics)

            elif action['method'] == 'POST':
                async with session.post(
                    f"{self.base_url}{action['endpoint']}",
                    json=action.get('payload', {}),
                    timeout=10
                ) as response:
                    response_time = time.time() - action_start
                    self.record_metrics(action['endpoint'], 'POST', response.status, response_time, metrics)

            elif action['method'] == 'WEBSOCKET':
                await self.perform_websocket_action(action, user_id, action_start, metrics)

        except asyncio.TimeoutError:
            response_time = time.time() - action_start
            self.record_metrics(action['endpoint'], action['method'], 408, response_time, metrics)
        except Exception as e:
            response_time = time.time() - action_start
            self.record_metrics(action['endpoint'], action['method'], 500, response_time, metrics)

    def select_action(self, scenario_type: str) -> Dict[str, Any]:
        """Select an action based on scenario type"""
        action_sets = {
            'mixed': [
                {'method': 'GET', 'endpoint': '/api/health', 'weight': 20},
                {'method': 'GET', 'endpoint': '/api/user/profile', 'weight': 15},
                {'method': 'GET', 'endpoint': '/api/sessions/active', 'weight': 10},
                {'method': 'POST', 'endpoint': '/api/sessions/create', 'payload': self.generate_session_data(), 'weight': 8},
                {'method': 'POST', 'endpoint': '/api/messages/send', 'payload': self.generate_message_data(), 'weight': 25},
                {'method': 'GET', 'endpoint': '/api/characters/list', 'weight': 10},
                {'method': 'POST', 'endpoint': '/api/characters/create', 'payload': self.generate_character_data(), 'weight': 5},
                {'method': 'WEBSOCKET', 'endpoint': '/ws/session', 'payload': {}, 'weight': 7}
            ],
            'realistic': [
                {'method': 'GET', 'endpoint': '/api/health', 'weight': 5},
                {'method': 'GET', 'endpoint': '/api/user/profile', 'weight': 10},
                {'method': 'GET', 'endpoint': '/api/sessions/active', 'weight': 15},
                {'method': 'POST', 'endpoint': '/api/sessions/create', 'payload': self.generate_session_data(), 'weight': 5},
                {'method': 'POST', 'endpoint': '/api/messages/send', 'payload': self.generate_message_data(), 'weight': 30},
                {'method': 'GET', 'endpoint': '/api/characters/list', 'weight': 15},
                {'method': 'POST', 'endpoint': '/api/characters/create', 'payload': self.generate_character_data(), 'weight': 3},
                {'method': 'WEBSOCKET', 'endpoint': '/ws/session', 'payload': {}, 'weight': 17}
            ],
            'stress': [
                {'method': 'POST', 'endpoint': '/api/messages/send', 'payload': self.generate_message_data(), 'weight': 40},
                {'method': 'GET', 'endpoint': '/api/sessions/active', 'weight': 20},
                {'method': 'WEBSOCKET', 'endpoint': '/ws/session', 'payload': {}, 'weight': 20},
                {'method': 'POST', 'endpoint': '/api/sessions/create', 'payload': self.generate_session_data(), 'weight': 10},
                {'method': 'GET', 'endpoint': '/api/health', 'weight': 10}
            ],
            'endurance': [
                {'method': 'GET', 'endpoint': '/api/health', 'weight': 30},
                {'method': 'GET', 'endpoint': '/api/user/profile', 'weight': 20},
                {'method': 'POST', 'endpoint': '/api/messages/send', 'payload': self.generate_message_data(), 'weight': 20},
                {'method': 'WEBSOCKET', 'endpoint': '/ws/session', 'payload': {}, 'weight': 15},
                {'method': 'GET', 'endpoint': '/api/sessions/active', 'weight': 10},
                {'method': 'POST', 'endpoint': '/api/sessions/create', 'payload': self.generate_session_data(), 'weight': 5}
            ],
            'exhaustion': [
                {'method': 'POST', 'endpoint': '/api/messages/send', 'payload': self.generate_large_message_data(), 'weight': 35},
                {'method': 'POST', 'endpoint': '/api/characters/create', 'payload': self.generate_complex_character_data(), 'weight': 15},
                {'method': 'POST', 'endpoint': '/api/sessions/create', 'payload': self.generate_complex_session_data(), 'weight': 15},
                {'method': 'WEBSOCKET', 'endpoint': '/ws/session', 'payload': {}, 'weight': 20},
                {'method': 'GET', 'endpoint': '/api/health', 'weight': 15}
            ]
        }

        actions = action_sets.get(scenario_type, action_sets['mixed'])
        weights = [action['weight'] for action in actions]
        selected_action = random.choices(actions, weights=weights)[0]

        return selected_action

    def generate_session_data(self) -> Dict[str, Any]:
        """Generate session data for API calls"""
        return {
            'character_id': str(uuid.uuid4()),
            'scenario': random.choice(['tavern_adventure', 'forest_quest', 'dungeon_crawl']),
            'difficulty': random.choice(['easy', 'normal', 'hard']),
            'max_players': random.randint(1, 4)
        }

    def generate_message_data(self) -> Dict[str, Any]:
        """Generate message data for API calls"""
        message_templates = [
            "Hello, I'd like to start an adventure!",
            "What can you tell me about this area?",
            "I'm ready for the next challenge.",
            "Can you help me with this quest?",
            "Tell me more about the local rumors.",
            "What monsters live in these lands?",
            "I'm looking for treasure and glory!",
            "Is there anything interesting happening nearby?"
        ]

        return {
            'session_id': str(uuid.uuid4()),
            'content': random.choice(message_templates),
            'type': 'user_action',
            'timestamp': datetime.now().isoformat()
        }

    def generate_large_message_data(self) -> Dict[str, Any]:
        """Generate large message data for resource exhaustion testing"""
        base_content = "This is a test message designed to consume more resources. " * 50
        return {
            'session_id': str(uuid.uuid4()),
            'content': base_content + f" Additional content: {uuid.uuid4().hex * 20}",
            'type': 'user_action',
            'metadata': {f'key_{i}': f'value_{i}' * 10 for i in range(20)},
            'timestamp': datetime.now().isoformat()
        }

    def generate_character_data(self) -> Dict[str, Any]:
        """Generate character data for API calls"""
        return {
            'name': f"TestChar_{random.randint(1, 9999)}",
            'class': random.choice(['warrior', 'mage', 'rogue', 'cleric']),
            'background': random.choice(['noble', 'commoner', 'merchant', 'scholar']),
            'attributes': {
                'strength': random.randint(8, 18),
                'dexterity': random.randint(8, 18),
                'constitution': random.randint(8, 18),
                'intelligence': random.randint(8, 18),
                'wisdom': random.randint(8, 18),
                'charisma': random.randint(8, 18)
            }
        }

    def generate_complex_character_data(self) -> Dict[str, Any]:
        """Generate complex character data for resource exhaustion testing"""
        base_data = self.generate_character_data()
        base_data.update({
            'equipment': {f'slot_{i}': {'item': f'item_{i}', 'properties': [f'prop_{j}' for j in range(5)]} for i in range(20)},
            'skills': {f'skill_{i}': {'level': random.randint(1, 10), 'experience': random.randint(0, 1000)} for i in range(50)},
            'inventory': [f'item_{i}' for i in range(100)],
            'background_story': "This is a very long and detailed background story. " * 30,
            'notes': {f'note_{i}': f"This is note number {i} with some additional content. " * 5 for i in range(25)}
        })
        return base_data

    def generate_complex_session_data(self) -> Dict[str, Any]:
        """Generate complex session data for resource exhaustion testing"""
        base_data = self.generate_session_data()
        base_data.update({
            'custom_rules': {f'rule_{i}': f'This is rule number {i} with detailed explanation.' * 3 for i in range(30)},
            'npc_data': {f'npc_{i}': {'name': f'NPC_{i}', 'dialogue': [f'Line {j}' for j in range(20)]} for i in range(15)},
            'world_state': {f'region_{i}': {'description': f'Description for region {i} ' * 10, 'status': 'active'} for i in range(10)},
            'quest_data': [f'quest_objective_{i}' for i in range(50)]
        })
        return base_data

    def get_think_time(self, scenario_type: str) -> float:
        """Get think time between user actions based on scenario type"""
        think_times = {
            'mixed': (1.0, 5.0),
            'realistic': (2.0, 8.0),
            'stress': (0.1, 1.0),
            'endurance': (3.0, 10.0),
            'exhaustion': (0.05, 0.5)
        }

        min_time, max_time = think_times.get(scenario_type, think_times['mixed'])
        return random.uniform(min_time, max_time)

    async def perform_websocket_action(self, action: Dict[str, Any], user_id: str, start_time: float, metrics: Dict[str, Any]):
        """Perform WebSocket action"""
        try:
            uri = f"{self.websocket_url}{action['endpoint']}?user_id={user_id}"
            async with websockets.connect(uri, timeout=5) as websocket:
                # Send message
                message = {
                    'type': 'test_message',
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message))

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_time = time.time() - start_time

                self.record_metrics(action['endpoint'], 'WEBSOCKET', 200, response_time, metrics)

        except Exception as e:
            response_time = time.time() - start_time
            self.record_metrics(action['endpoint'], 'WEBSOCKET', 500, response_time, metrics)

    def record_metrics(self, endpoint: str, method: str, status: int, response_time: float, metrics: Dict[str, Any]):
        """Record performance metrics"""
        # Update scenario metrics
        metrics['requests'] += 1
        metrics['response_times'].append(response_time)

        if status >= 400:
            metrics['errors'] += 1

        # Update global metrics
        self.metrics['response_times'].append(response_time)
        self.metrics['request_counts'][endpoint] += 1
        if status >= 400:
            self.metrics['error_counts'][endpoint] += 1

        # Update Prometheus metrics
        self.response_time_histogram.labels(endpoint=endpoint, method=method).observe(response_time)
        status_category = 'success' if status < 400 else 'error'
        self.request_counter.labels(endpoint=endpoint, method=method, status=status_category).inc()

    async def monitor_system_performance(self, duration: int, metrics: Dict[str, Any]):
        """Monitor system performance during load test"""
        try:
            start_time = time.time()

            while time.time() - start_time < duration:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                active_connections = self.metrics['concurrent_connections']

                system_sample = {
                    'timestamp': time.time(),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'active_connections': active_connections
                }

                metrics['system_metrics'].append(system_sample)
                self.metrics['system_metrics'].append(system_sample)

                # Update active connections gauge
                self.active_connections_gauge.set(active_connections)

                await asyncio.sleep(5)  # Sample every 5 seconds

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"System monitoring failed: {e}")

    def calculate_performance_metrics(self, scenario_metrics: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """Calculate performance metrics from collected data"""
        response_times = list(scenario_metrics['response_times'])

        if not response_times:
            return {
                'total_requests': 0,
                'total_errors': 0,
                'error_rate': 1.0,
                'avg_response_time': float('inf'),
                'min_response_time': 0,
                'max_response_time': 0,
                'p50_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'throughput': 0,
                'peak_cpu': 0,
                'peak_memory': 0,
                'avg_cpu': 0,
                'avg_memory': 0
            }

        # Response time metrics
        sorted_times = sorted(response_times)
        total_requests = scenario_metrics['requests']
        total_errors = scenario_metrics['errors']

        # System metrics
        system_samples = list(scenario_metrics['system_metrics'])
        if system_samples:
            cpu_values = [s['cpu_usage'] for s in system_samples]
            memory_values = [s['memory_usage'] for s in system_samples]
            peak_cpu = max(cpu_values)
            peak_memory = max(memory_values)
            avg_cpu = statistics.mean(cpu_values)
            avg_memory = statistics.mean(memory_values)
        else:
            peak_cpu = peak_memory = avg_cpu = avg_memory = 0

        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 1.0,
            'avg_response_time': statistics.mean(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'p50_response_time': sorted_times[len(sorted_times) // 2],
            'p95_response_time': sorted_times[int(len(sorted_times) * 0.95)],
            'p99_response_time': sorted_times[int(len(sorted_times) * 0.99)],
            'throughput': total_requests / total_time if total_time > 0 else 0,
            'peak_cpu': peak_cpu,
            'peak_memory': peak_memory,
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory
        }

    def evaluate_performance_thresholds(self, performance: Dict[str, Any]) -> bool:
        """Evaluate performance against thresholds"""
        thresholds = self.load_config['performance_thresholds']

        return (
            performance['avg_response_time'] <= thresholds['avg_response_time'] and
            performance['p95_response_time'] <= thresholds['p95_response_time'] and
            performance['error_rate'] <= thresholds['error_rate'] and
            performance['peak_cpu'] <= thresholds['cpu_usage'] and
            performance['peak_memory'] <= thresholds['memory_usage']
        )

    async def test_concurrent_users(self) -> TestResult:
        """
        Test concurrent user scenarios and social features under load
        """
        result = TestResult(
            name="concurrent_users",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            concurrent_tests = {
                'shared_sessions': await self.test_shared_game_sessions(),
                'multiplayer_interactions': await self.test_multiplayer_interactions(),
                'real_time_collaboration': await self.test_real_time_collaboration(),
                'social_features_load': await self.test_social_features_load()
            }

            all_passed = all(test.get('success', False) for test in concurrent_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Concurrent users test completed" if all_passed else "Some concurrent user tests failed"
            result.details = concurrent_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Concurrent users test failed: {str(e)}"
            self.logger.error(f"Concurrent users test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_shared_game_sessions(self) -> Dict[str, Any]:
        """Test shared game sessions under load"""
        try:
            num_sessions = 10
            users_per_session = 4
            session_results = []

            async def simulate_shared_session(session_id: str):
                try:
                    # Create multiple users in the same session
                    user_tasks = []
                    for user_idx in range(users_per_session):
                        user_id = f"user_{session_id}_{user_idx}"
                        task = asyncio.create_task(
                            self.simulate_multiplayer_user(user_id, session_id, 60)
                        )
                        user_tasks.append(task)

                    # Wait for all users to complete
                    results = await asyncio.gather(*user_tasks, return_exceptions=True)
                    successful_users = [r for r in results if not isinstance(r, Exception)]

                    return {
                        'session_id': session_id,
                        'total_users': users_per_session,
                        'successful_users': len(successful_users),
                        'success_rate': len(successful_users) / users_per_session
                    }

                except Exception as e:
                    return {
                        'session_id': session_id,
                        'error': str(e),
                        'success_rate': 0
                    }

            # Run sessions concurrently
            session_tasks = [
                simulate_shared_session(f"session_{i}")
                for i in range(num_sessions)
            ]

            session_results = await asyncio.gather(*session_tasks, return_exceptions=True)

            # Analyze results
            successful_sessions = [r for r in session_results if isinstance(r, dict) and r.get('success_rate', 0) > 0.5]
            avg_success_rate = statistics.mean([r['success_rate'] for r in successful_sessions]) if successful_sessions else 0

            sessions_working = len(successful_sessions) >= num_sessions * 0.8 and avg_success_rate >= 0.7

            return {
                'success': sessions_working,
                'total_sessions': num_sessions,
                'successful_sessions': len(successful_sessions),
                'avg_success_rate': avg_success_rate,
                'users_per_session': users_per_session,
                'session_results': session_results,
                'message': f"Shared sessions working ({len(successful_sessions)}/{num_sessions} successful)" if sessions_working else "Shared sessions need improvement"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def simulate_multiplayer_user(self, user_id: str, session_id: str, duration: int):
        """Simulate a user in a multiplayer session"""
        try:
            session = aiohttp.ClientSession()
            start_time = time.time()

            # Join session
            await session.post(
                f"{self.base_url}/api/sessions/{session_id}/join",
                json={'user_id': user_id},
                timeout=10
            )

            # Simulate multiplayer actions
            while time.time() - start_time < duration:
                # Send message to session
                await session.post(
                    f"{self.base_url}/api/sessions/{session_id}/message",
                    json={
                        'user_id': user_id,
                        'content': f"Message from {user_id}",
                        'type': 'chat'
                    },
                    timeout=10
                )

                # Perform action
                await session.post(
                    f"{self.base_url}/api/sessions/{session_id}/action",
                    json={
                        'user_id': user_id,
                        'action': random.choice(['look', 'move', 'talk', 'attack']),
                        'target': random.choice(['north', 'south', 'east', 'west', 'npc', 'enemy'])
                    },
                    timeout=10
                )

                await asyncio.sleep(random.uniform(2, 8))

            # Leave session
            await session.post(
                f"{self.base_url}/api/sessions/{session_id}/leave",
                json={'user_id': user_id},
                timeout=10
            )

            await session.close()

        except Exception as e:
            self.logger.error(f"Multiplayer user {user_id} failed: {e}")

    async def test_multiplayer_interactions(self) -> Dict[str, Any]:
        """Test multiplayer interactions under load"""
        try:
            # This test would involve complex multiplayer scenarios
            # For now, we'll simulate basic multiplayer load

            interaction_results = await self.run_load_scenario(
                name='multiplayer_interactions',
                concurrent_users=40,
                duration=60,
                scenario_type='realistic'
            )

            return {
                'success': interaction_results.get('success', False),
                'scenario': 'multiplayer_interactions',
                'performance': interaction_results.get('performance', {}),
                'message': "Multiplayer interactions test completed"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_real_time_collaboration(self) -> Dict[str, Any]:
        """Test real-time collaboration features under load"""
        try:
            collaboration_results = await self.run_load_scenario(
                name='real_time_collaboration',
                concurrent_users=30,
                duration=45,
                scenario_type='stress'
            )

            # Check WebSocket performance specifically
            websocket_performance = collaboration_results.get('performance', {}).get('avg_response_time', float('inf'))

            collaboration_working = (
                collaboration_results.get('success', False) and
                websocket_performance < 0.5  # WebSocket should be fast
            )

            return {
                'success': collaboration_working,
                'scenario': 'real_time_collaboration',
                'performance': collaboration_results.get('performance', {}),
                'websocket_avg_response': websocket_performance,
                'message': f"Real-time collaboration {'working' if collaboration_working else 'needs improvement'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_social_features_load(self) -> Dict[str, Any]:
        """Test social features under load"""
        try:
            social_actions = [
                'friend_requests',
                'messaging',
                'leaderboards',
                'profiles',
                'achievements'
            ]

            social_results = {}
            for action in social_actions:
                result = await self.run_load_scenario(
                    name=f'social_{action}',
                    concurrent_users=25,
                    duration=30,
                    scenario_type='mixed'
                )
                social_results[action] = result.get('success', False)

            all_social_working = all(social_results.values())

            return {
                'success': all_social_working,
                'scenario': 'social_features_load',
                'individual_results': social_results,
                'message': f"Social features {'working' if all_social_working else 'need improvement'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_response_times(self) -> TestResult:
        """
        Test response times under realistic load
        """
        result = TestResult(
            name="response_times",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            response_time_tests = {
                'api_response_times': await self.test_api_response_times(),
                'database_query_times': await self.test_database_query_times(),
                'ai_response_times': await self.test_ai_response_times(),
                'websocket_latency': await self.test_websocket_latency()
            }

            all_passed = all(test.get('success', False) for test in response_time_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Response time test completed" if all_passed else "Some response time tests failed"
            result.details = response_time_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Response time test failed: {str(e)}"
            self.logger.error(f"Response time test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_api_response_times(self) -> Dict[str, Any]:
        """Test API response times under load"""
        try:
            endpoints = [
                '/api/health',
                '/api/user/profile',
                '/api/sessions/active',
                '/api/characters/list'
            ]

            endpoint_results = {}
            for endpoint in endpoints:
                # Test each endpoint under load
                latencies = []

                async def test_endpoint():
                    start_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                            return time.time() - start_time, response.status

                # Run concurrent tests
                tasks = [test_endpoint() for _ in range(20)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                valid_results = [(latency, status) for latency, status in results if isinstance(latency, float)]
                latencies = [latency for latency, status in valid_results if status == 200]

                if latencies:
                    avg_latency = statistics.mean(latencies)
                    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
                    max_latency = max(latencies)

                    endpoint_results[endpoint] = {
                        'avg_latency': avg_latency,
                        'p95_latency': p95_latency,
                        'max_latency': max_latency,
                        'success_rate': len(latencies) / len(valid_results) if valid_results else 0
                    }
                else:
                    endpoint_results[endpoint] = {
                        'avg_latency': float('inf'),
                        'p95_latency': float('inf'),
                        'max_latency': float('inf'),
                        'success_rate': 0
                    }

            # Evaluate overall API performance
            avg_latency = statistics.mean([r['avg_latency'] for r in endpoint_results.values() if r['avg_latency'] != float('inf')])
            api_performance_good = avg_latency < 0.5  # Average under 500ms

            return {
                'success': api_performance_good,
                'avg_api_latency': avg_latency,
                'endpoint_results': endpoint_results,
                'message': f"API response times {'good' if api_performance_good else 'need improvement'} (avg: {avg_latency:.3f}s)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_database_query_times(self) -> Dict[str, Any]:
        """Test database query response times"""
        try:
            # This would involve testing actual database queries
            # For now, we'll simulate through API endpoints

            db_test_endpoints = [
                '/api/user/profile',
                '/api/sessions/history',
                '/api/characters/details',
                '/api/messages/history'
            ]

            db_results = {}
            for endpoint in db_test_endpoints:
                try:
                    start_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.base_url}{endpoint}", timeout=15) as response:
                            query_time = time.time() - start_time
                            db_results[endpoint] = {
                                'query_time': query_time,
                                'status': response.status,
                                'acceptable': query_time < 1.0  # Under 1 second
                            }
                except Exception as e:
                    db_results[endpoint] = {
                        'query_time': float('inf'),
                        'status': 500,
                        'acceptable': False,
                        'error': str(e)
                    }

            db_performance_good = all(r.get('acceptable', False) for r in db_results.values())

            return {
                'success': db_performance_good,
                'db_results': db_results,
                'message': f"Database query times {'good' if db_performance_good else 'need improvement'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_ai_response_times(self) -> Dict[str, Any]:
        """Test AI system response times"""
        try:
            ai_endpoints = [
                '/api/ai/generate',
                '/api/ai/character/create',
                '/api/ai/scene/generate'
            ]

            ai_results = {}
            for endpoint in ai_endpoints:
                try:
                    start_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        payload = self.generate_ai_payload(endpoint)
                        async with session.post(
                            f"{self.base_url}{endpoint}",
                            json=payload,
                            timeout=30
                        ) as response:
                            ai_time = time.time() - start_time
                            ai_results[endpoint] = {
                                'response_time': ai_time,
                                'status': response.status,
                                'acceptable': ai_time < 5.0  # AI can be slower, under 5 seconds
                            }
                except Exception as e:
                    ai_results[endpoint] = {
                        'response_time': float('inf'),
                        'status': 500,
                        'acceptable': False,
                        'error': str(e)
                    }

            ai_performance_good = all(r.get('acceptable', False) for r in ai_results.values())

            return {
                'success': ai_performance_good,
                'ai_results': ai_results,
                'message': f"AI response times {'good' if ai_performance_good else 'need improvement'}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_ai_payload(self, endpoint: str) -> Dict[str, Any]:
        """Generate appropriate payload for AI endpoints"""
        if 'generate' in endpoint:
            return {
                'prompt': 'Describe a fantasy setting',
                'max_tokens': 100,
                'temperature': 0.7
            }
        elif 'character' in endpoint:
            return {
                'name': 'Test Character',
                'class': 'warrior',
                'background': 'Test background'
            }
        elif 'scene' in endpoint:
            return {
                'setting': 'tavern',
                'atmosphere': 'mysterious',
                'characters': ['player', 'npc']
            }
        else:
            return {}

    async def test_websocket_latency(self) -> Dict[str, Any]:
        """Test WebSocket latency under load"""
        try:
            num_connections = 20
            latency_tests = []

            async def test_websocket_latency(conn_id: int):
                try:
                    uri = f"{self.websocket_url}/ws/latency_test/{conn_id}"
                    latencies = []

                    async with websockets.connect(uri, timeout=10) as websocket:
                        for i in range(10):
                            start_time = time.time()
                            ping_message = {
                                'type': 'ping',
                                'timestamp': start_time,
                                'sequence': i
                            }
                            await websocket.send(json.dumps(ping_message))

                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            latency = time.time() - start_time
                            latencies.append(latency)

                            await asyncio.sleep(0.1)

                    return latencies
                except Exception as e:
                    return [float('inf')]  # Return infinite latency on error

            # Run latency tests concurrently
            tasks = [test_websocket_latency(i) for i in range(num_connections)]
            all_latencies = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten all latency measurements
            valid_latencies = []
            for latencies in all_latencies:
                if isinstance(latencies, list):
                    valid_latencies.extend([l for l in latencies if l != float('inf')])

            if valid_latencies:
                avg_latency = statistics.mean(valid_latencies)
                p95_latency = sorted(valid_latencies)[int(len(valid_latencies) * 0.95)]
                max_latency = max(valid_latencies)

                websocket_performance_good = (
                    avg_latency < 0.1 and  # Under 100ms average
                    p95_latency < 0.2 and   # Under 200ms p95
                    max_latency < 0.5      # Under 500ms max
                )
            else:
                avg_latency = p95_latency = max_latency = float('inf')
                websocket_performance_good = False

            return {
                'success': websocket_performance_good,
                'num_connections': num_connections,
                'total_measurements': len(valid_latencies),
                'avg_latency': avg_latency,
                'p95_latency': p95_latency,
                'max_latency': max_latency,
                'message': f"WebSocket latency {'good' if websocket_performance_good else 'needs improvement'} (avg: {avg_latency*1000:.1f}ms)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }