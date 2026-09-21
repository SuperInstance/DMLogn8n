#!/usr/bin/env python3
"""
DMLogn8n Real-time Testing
Comprehensive real-time features testing (WebSocket, live updates, synchronization)
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
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import websockets
import redis
import psutil
from collections import defaultdict, deque

# Import test framework
from integration_test_suite import TestResult, TestStatus

class RealTimeTesting:
    """
    Comprehensive real-time features testing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('real_time_testing')
        self.base_url = config['base_url']
        self.redis_url = config['redis_url']
        self.websocket_url = config.get('websocket_url', 'ws://localhost:8001')

        # Performance monitoring
        self.performance_metrics = defaultdict(list)
        self.message_latencies = deque(maxlen=1000)
        self.connection_stats = defaultdict(dict)

        # Test state
        self.active_connections = []
        self.test_sessions = []
        self.message_sequences = defaultdict(list)

    async def test_realtime_synchronization(self) -> TestResult:
        """
        Test real-time synchronization between multiple clients
        """
        result = TestResult(
            name="realtime_synchronization",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            sync_tests = {
                'websocket_connectivity': await self.test_websocket_connectivity(),
                'message_broadcast': await self.test_message_broadcast(),
                'session_sync': await self.test_session_synchronization(),
                'concurrent_connections': await self.test_concurrent_connections(),
                'connection_recovery': await self.test_connection_recovery(),
                'latency_measurement': await self.test_latency_measurement(),
                'message_ordering': await self.test_message_ordering()
            }

            all_passed = all(test.get('success', False) for test in sync_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Real-time synchronization test completed" if all_passed else "Some real-time tests failed"
            result.details = sync_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Real-time synchronization test failed: {str(e)}"
            self.logger.error(f"Real-time synchronization test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_websocket_connectivity(self) -> Dict[str, Any]:
        """Test basic WebSocket connectivity"""
        try:
            # Test multiple WebSocket connections
            connection_results = []
            test_connections = 5

            async def create_connection(conn_id):
                try:
                    uri = f"{self.websocket_url}/ws/test/{conn_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Send test message
                        test_message = {
                            'type': 'test_connection',
                            'connection_id': conn_id,
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(test_message))

                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        response_data = json.loads(response)

                        return {
                            'connection_id': conn_id,
                            'success': True,
                            'response_received': True,
                            'response_type': response_data.get('type'),
                            'latency': time.time() - time.time()  # Placeholder
                        }
                except Exception as e:
                    return {
                        'connection_id': conn_id,
                        'success': False,
                        'error': str(e)
                    }

            # Create connections concurrently
            tasks = [create_connection(i) for i in range(test_connections)]
            connection_results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_connections = [r for r in connection_results if isinstance(r, dict) and r.get('success', False)]
            success_rate = len(successful_connections) / test_connections

            return {
                'success': success_rate >= 0.8,
                'total_connections': test_connections,
                'successful_connections': len(successful_connections),
                'success_rate': success_rate,
                'connection_details': connection_results,
                'message': f"WebSocket connectivity working ({success_rate:.1%} success rate)" if success_rate >= 0.8 else "WebSocket connectivity issues detected"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_message_broadcast(self) -> Dict[str, Any]:
        """Test message broadcasting to multiple clients"""
        try:
            # Create multiple client connections
            num_clients = 3
            session_id = f"broadcast_test_{uuid.uuid4().hex[:8]}"

            clients = {}
            received_messages = defaultdict(list)

            async def client_handler(client_id):
                try:
                    uri = f"{self.websocket_url}/ws/session/{session_id}?client_id={client_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:
                        clients[client_id] = websocket

                        # Wait for messages
                        for _ in range(5):  # Expect 5 messages
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                                message_data = json.loads(message)
                                received_messages[client_id].append(message_data)
                            except asyncio.TimeoutError:
                                break

                        return {'client_id': client_id, 'messages_received': len(received_messages[client_id])}
                except Exception as e:
                    return {'client_id': client_id, 'error': str(e), 'messages_received': 0}

            # Start client handlers
            client_tasks = [client_handler(f"client_{i}") for i in range(num_clients)]

            # Wait a bit for connections to establish
            await asyncio.sleep(1)

            # Broadcast messages from main connection
            if len(clients) == num_clients:
                broadcaster = clients['client_0']  # Use first client as broadcaster

                for i in range(5):
                    broadcast_message = {
                        'type': 'broadcast',
                        'message': f"Broadcast message {i}",
                        'sender': 'client_0',
                        'timestamp': datetime.now().isoformat()
                    }
                    await broadcaster.send(json.dumps(broadcast_message))
                    await asyncio.sleep(0.1)  # Small delay between messages

            # Wait for all messages to be received
            await asyncio.sleep(2)

            # Get client results
            client_results = await asyncio.gather(*client_tasks, return_exceptions=True)

            # Analyze results
            successful_clients = [r for r in client_results if isinstance(r, dict) and r.get('messages_received', 0) >= 4]
            avg_messages_received = sum(r.get('messages_received', 0) for r in client_results if isinstance(r, dict)) / len(client_results)

            return {
                'success': len(successful_clients) >= num_clients - 1,  # Allow for 1 failure
                'num_clients': num_clients,
                'successful_clients': len(successful_clients),
                'avg_messages_received': avg_messages_received,
                'client_results': client_results,
                'message': f"Message broadcasting working ({len(successful_clients)}/{num_clients} clients successful)" if len(successful_clients) >= num_clients - 1 else "Message broadcasting issues detected"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_session_synchronization(self) -> Dict[str, Any]:
        """Test real-time session state synchronization"""
        try:
            session_id = f"sync_test_{uuid.uuid4().hex[:8]}"
            num_participants = 2

            # Track session state changes
            state_changes = defaultdict(list)

            async def participant_handler(participant_id):
                try:
                    uri = f"{self.websocket_url}/ws/session/{session_id}?participant_id={participant_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for state updates
                        for _ in range(10):  # Expect multiple state updates
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                message_data = json.loads(message)

                                if message_data.get('type') == 'state_update':
                                    state_changes[participant_id].append({
                                        'state': message_data.get('state'),
                                        'timestamp': message_data.get('timestamp'),
                                        'received_at': datetime.now().isoformat()
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'participant_id': participant_id, 'state_updates': len(state_changes[participant_id])}
                except Exception as e:
                    return {'participant_id': participant_id, 'error': str(e), 'state_updates': 0}

            # Start participants
            participant_tasks = [participant_handler(f"participant_{i}") for i in range(num_participants)]

            # Wait for connections
            await asyncio.sleep(1)

            # Simulate session state changes via HTTP API
            async with aiohttp.ClientSession() as session:
                state_updates = [
                    {'scene': 'tavern', 'mood': 'peaceful'},
                    {'scene': 'combat', 'mood': 'tense'},
                    {'scene': 'celebration', 'mood': 'joyful'}
                ]

                for i, state in enumerate(state_updates):
                    await session.post(
                        f"{self.base_url}/api/sessions/{session_id}/state",
                        json={
                            'state': state,
                            'update_id': i,
                            'timestamp': datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.5)

            # Wait for state synchronization
            await asyncio.sleep(3)

            # Get participant results
            participant_results = await asyncio.gather(*participant_tasks, return_exceptions=True)

            # Analyze synchronization
            successful_participants = [r for r in participant_results if isinstance(r, dict) and r.get('state_updates', 0) >= 2]

            # Check if all participants received similar state updates
            state_consistency = True
            if len(successful_participants) >= 2:
                reference_updates = len(state_changes[successful_participants[0]['participant_id']])
                for participant in successful_participants[1:]:
                    participant_updates = len(state_changes[participant['participant_id']])
                    if abs(participant_updates - reference_updates) > 1:  # Allow for 1 update difference
                        state_consistency = False
                        break

            return {
                'success': len(successful_participants) == num_participants and state_consistency,
                'num_participants': num_participants,
                'successful_participants': len(successful_participants),
                'state_consistency': state_consistency,
                'participant_results': participant_results,
                'state_changes': dict(state_changes),
                'message': f"Session synchronization working ({len(successful_participants)}/{num_participants} participants)" if len(successful_participants) == num_participants and state_consistency else "Session synchronization issues detected"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_concurrent_connections(self) -> Dict[str, Any]:
        """Test system handling of concurrent connections"""
        try:
            num_connections = 20
            connection_results = []
            successful_connections = 0
            total_connect_time = 0

            async def create_concurrent_connection(conn_id):
                start_time = time.time()
                try:
                    uri = f"{self.websocket_url}/ws/load_test/{conn_id}"
                    async with websockets.connect(uri, timeout=15) as websocket:
                        connect_time = time.time() - start_time

                        # Send and receive a test message
                        test_message = {
                            'type': 'load_test',
                            'connection_id': conn_id,
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(test_message))

                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)

                        return {
                            'connection_id': conn_id,
                            'success': True,
                            'connect_time': connect_time,
                            'response_received': True
                        }
                except Exception as e:
                    return {
                        'connection_id': conn_id,
                        'success': False,
                        'error': str(e),
                        'connect_time': time.time() - start_time
                    }

            # Create connections with controlled concurrency
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent connections

            async def limited_connection(conn_id):
                async with semaphore:
                    return await create_concurrent_connection(conn_id)

            # Start all connections
            start_time = time.time()
            tasks = [limited_connection(i) for i in range(num_connections)]
            connection_results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Analyze results
            successful_results = [r for r in connection_results if isinstance(r, dict) and r.get('success', False)]
            successful_connections = len(successful_results)

            if successful_results:
                avg_connect_time = sum(r['connect_time'] for r in successful_results) / len(successful_results)
                max_connect_time = max(r['connect_time'] for r in successful_results)
            else:
                avg_connect_time = max_connect_time = 0

            # Check system performance
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            performance_acceptable = (
                successful_connections >= num_connections * 0.8 and  # At least 80% success
                avg_connect_time < 3.0 and                         # Average connect time under 3s
                cpu_usage < 80 and                                  # CPU usage under 80%
                memory_usage < 85                                   # Memory usage under 85%
            )

            return {
                'success': performance_acceptable,
                'total_connections': num_connections,
                'successful_connections': successful_connections,
                'success_rate': successful_connections / num_connections,
                'total_time': total_time,
                'avg_connect_time': avg_connect_time,
                'max_connect_time': max_connect_time,
                'system_performance': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage
                },
                'performance_acceptable': performance_acceptable,
                'message': f"Concurrent connections handled well ({successful_connections}/{num_connections} successful)" if performance_acceptable else "Concurrent connection handling needs optimization"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_connection_recovery(self) -> Dict[str, Any]:
        """Test connection recovery and reconnection handling"""
        try:
            connection_id = f"recovery_test_{uuid.uuid4().hex[:8]}"
            recovery_results = []

            for attempt in range(3):  # Test 3 recovery scenarios
                try:
                    # Initial connection
                    uri = f"{self.websocket_url}/ws/recovery/{connection_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Send initial message
                        initial_message = {
                            'type': 'recovery_test',
                            'attempt': attempt,
                            'message': 'Initial connection'
                        }
                        await websocket.send(json.dumps(initial_message))

                        # Receive response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        response_data = json.loads(response)

                        # Simulate connection loss (close connection)
                        await websocket.close()
                        await asyncio.sleep(1)  # Wait for disconnection

                        # Attempt reconnection
                        try:
                            async with websockets.connect(uri, timeout=10) as websocket_reconnect:
                                # Send reconnection message
                                reconnect_message = {
                                    'type': 'reconnection',
                                    'attempt': attempt,
                                    'message': 'Reconnected successfully'
                                }
                                await websocket_reconnect.send(json.dumps(reconnect_message))

                                # Verify reconnection response
                                reconnect_response = await asyncio.wait_for(websocket_reconnect.recv(), timeout=5)
                                reconnect_data = json.loads(reconnect_response)

                                recovery_results.append({
                                    'attempt': attempt,
                                    'initial_connection': True,
                                    'reconnection': True,
                                    'session_preserved': reconnect_data.get('session_preserved', False),
                                    'recovery_time': 1.0  # Placeholder
                                })
                        except Exception as reconnect_error:
                            recovery_results.append({
                                'attempt': attempt,
                                'initial_connection': True,
                                'reconnection': False,
                                'error': str(reconnect_error),
                                'recovery_time': 1.0
                            })

                except Exception as e:
                    recovery_results.append({
                        'attempt': attempt,
                        'initial_connection': False,
                        'reconnection': False,
                        'error': str(e),
                        'recovery_time': 1.0
                    })

            successful_recoveries = [r for r in recovery_results if r.get('reconnection', False)]
            recovery_rate = len(successful_recoveries) / len(recovery_results)

            return {
                'success': recovery_rate >= 0.66,  # At least 2/3 successful recoveries
                'total_attempts': len(recovery_results),
                'successful_recoveries': len(successful_recoveries),
                'recovery_rate': recovery_rate,
                'recovery_details': recovery_results,
                'message': f"Connection recovery working ({recovery_rate:.1%} success rate)" if recovery_rate >= 0.66 else "Connection recovery needs improvement"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_latency_measurement(self) -> Dict[str, Any]:
        """Test message latency and response times"""
        try:
            num_measurements = 50
            latencies = []

            uri = f"{self.websocket_url}/ws/latency_test/{uuid.uuid4().hex[:8]}"

            async with websockets.connect(uri, timeout=10) as websocket:
                for i in range(num_measurements):
                    # Send timestamp message
                    send_time = time.time()
                    ping_message = {
                        'type': 'ping',
                        'timestamp': send_time,
                        'sequence': i
                    }
                    await websocket.send(json.dumps(ping_message))

                    # Wait for pong response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)

                    receive_time = time.time()
                    latency = receive_time - send_time
                    latencies.append(latency)

                    # Small delay between measurements
                    await asyncio.sleep(0.05)

            # Calculate statistics
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            median_latency = sorted(latencies)[len(latencies) // 2]

            # Calculate percentiles
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]

            latency_acceptable = (
                avg_latency < 0.1 and  # Average under 100ms
                p95 < 0.2 and         # 95th percentile under 200ms
                max_latency < 0.5      # Maximum under 500ms
            )

            return {
                'success': latency_acceptable,
                'measurements': num_measurements,
                'avg_latency_ms': avg_latency * 1000,
                'min_latency_ms': min_latency * 1000,
                'max_latency_ms': max_latency * 1000,
                'median_latency_ms': median_latency * 1000,
                'p95_latency_ms': p95 * 1000,
                'p99_latency_ms': p99 * 1000,
                'latency_acceptable': latency_acceptable,
                'message': f"Latency measurements good (avg: {avg_latency*1000:.1f}ms)" if latency_acceptable else "Latency needs optimization"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_message_ordering(self) -> Dict[str, Any]:
        """Test message ordering and sequencing"""
        try:
            num_messages = 20
            session_id = f"ordering_test_{uuid.uuid4().hex[:8]}"

            received_sequences = defaultdict(list)

            async def message_receiver(client_id):
                try:
                    uri = f"{self.websocket_url}/ws/ordering/{session_id}?client_id={client_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Receive messages
                        for _ in range(num_messages):
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                message_data = json.loads(message)

                                if message_data.get('sequence') is not None:
                                    received_sequences[client_id].append(message_data['sequence'])
                            except asyncio.TimeoutError:
                                break

                        return {'client_id': client_id, 'sequences': received_sequences[client_id]}
                except Exception as e:
                    return {'client_id': client_id, 'error': str(e), 'sequences': []}

            # Start message receiver
            receiver_task = asyncio.create_task(message_receiver('receiver'))

            # Wait for connection
            await asyncio.sleep(1)

            # Send ordered messages
            async with aiohttp.ClientSession() as session:
                for i in range(num_messages):
                    await session.post(
                        f"{self.base_url}/api/sessions/{session_id}/message",
                        json={
                            'message': f'Message {i}',
                            'sequence': i,
                            'timestamp': datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.02)  # Small delay between messages

            # Wait for all messages to be received
            await asyncio.sleep(3)

            # Get receiver result
            receiver_result = await receiver_task

            if isinstance(receiver_result, dict) and receiver_result.get('sequences'):
                sequences = receiver_result['sequences']

                # Check if messages are in order
                is_ordered = sequences == sorted(sequences)

                # Check for missing or duplicate messages
                expected_sequences = list(range(num_messages))
                missing_messages = set(expected_sequences) - set(sequences)
                duplicate_messages = len(sequences) - len(set(sequences))

                ordering_correct = (
                    is_ordered and
                    len(missing_messages) == 0 and
                    duplicate_messages == 0
                )

                return {
                    'success': ordering_correct,
                    'num_messages': num_messages,
                    'messages_received': len(sequences),
                    'is_ordered': is_ordered,
                    'missing_messages': list(missing_messages),
                    'duplicate_messages': duplicate_messages,
                    'received_sequences': sequences[:10],  # Show first 10 for brevity
                    'message': f"Message ordering working correctly" if ordering_correct else f"Message ordering issues (missing: {len(missing_messages)}, duplicates: {duplicate_messages})"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to receive messages for ordering test'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_live_updates(self) -> TestResult:
        """
        Test live update mechanisms and real-time notifications
        """
        result = TestResult(
            name="live_updates",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            live_update_tests = {
                'user_presence': await self.test_user_presence_updates(),
                'typing_indicators': await self.test_typing_indicators(),
                'game_state_updates': await self.test_game_state_updates(),
                'notification_system': await self.test_notification_system(),
                'event_broadcasting': await self.test_event_broadcasting()
            }

            all_passed = all(test.get('success', False) for test in live_update_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Live updates test completed" if all_passed else "Some live update tests failed"
            result.details = live_update_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Live updates test failed: {str(e)}"
            self.logger.error(f"Live updates test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_user_presence_updates(self) -> Dict[str, Any]:
        """Test user presence and online status updates"""
        try:
            session_id = f"presence_test_{uuid.uuid4().hex[:8]}"
            presence_updates = defaultdict(list)

            async def presence_client(client_id):
                try:
                    uri = f"{self.websocket_url}/ws/presence/{session_id}?client_id={client_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for presence updates
                        for _ in range(10):  # Expect multiple presence updates
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                message_data = json.loads(message)

                                if message_data.get('type') == 'presence_update':
                                    presence_updates[client_id].append({
                                        'user_id': message_data.get('user_id'),
                                        'status': message_data.get('status'),
                                        'timestamp': message_data.get('timestamp')
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'client_id': client_id, 'updates_received': len(presence_updates[client_id])}
                except Exception as e:
                    return {'client_id': client_id, 'error': str(e), 'updates_received': 0}

            # Start multiple clients
            num_clients = 3
            client_tasks = [presence_client(f"client_{i}") for i in range(num_clients)]

            # Wait for connections
            await asyncio.sleep(1)

            # Simulate presence changes via API
            async with aiohttp.ClientSession() as session:
                for i in range(num_clients):
                    # User joins
                    await session.post(
                        f"{self.base_url}/api/presence/join",
                        json={
                            'session_id': session_id,
                            'user_id': f"client_{i}",
                            'status': 'online'
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.5)

                # Wait for presence propagation
                await asyncio.sleep(2)

                # User leaves
                await session.post(
                    f"{self.base_url}/api/presence/leave",
                    json={
                        'session_id': session_id,
                        'user_id': 'client_0',
                        'status': 'offline'
                    },
                    timeout=10
                )

            # Wait for final updates
            await asyncio.sleep(2)

            # Get client results
            client_results = await asyncio.gather(*client_tasks, return_exceptions=True)

            # Analyze presence updates
            successful_clients = [r for r in client_results if isinstance(r, dict) and r.get('updates_received', 0) > 0]
            total_updates = sum(r.get('updates_received', 0) for r in client_results if isinstance(r, dict))

            presence_working = len(successful_clients) >= num_clients - 1 and total_updates >= num_clients

            return {
                'success': presence_working,
                'num_clients': num_clients,
                'successful_clients': len(successful_clients),
                'total_updates': total_updates,
                'presence_updates': dict(presence_updates),
                'message': f"User presence updates working ({len(successful_clients)}/{num_clients} clients received updates)" if presence_working else "User presence updates need improvement"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_typing_indicators(self) -> Dict[str, Any]:
        """Test typing indicators functionality"""
        try:
            session_id = f"typing_test_{uuid.uuid4().hex[:8]}"
            typing_events = defaultdict(list)

            async def typing_client(client_id):
                try:
                    uri = f"{self.websocket_url}/ws/typing/{session_id}?client_id={client_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for typing indicators
                        for _ in range(8):  # Expect multiple typing events
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=6)
                                message_data = json.loads(message)

                                if message_data.get('type') == 'typing_indicator':
                                    typing_events[client_id].append({
                                        'user_id': message_data.get('user_id'),
                                        'is_typing': message_data.get('is_typing'),
                                        'timestamp': message_data.get('timestamp')
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'client_id': client_id, 'typing_events': len(typing_events[client_id])}
                except Exception as e:
                    return {'client_id': client_id, 'error': str(e), 'typing_events': 0}

            # Start typing clients
            num_clients = 2
            client_tasks = [typing_client(f"client_{i}") for i in range(num_clients)]

            # Wait for connections
            await asyncio.sleep(1)

            # Simulate typing events
            async with aiohttp.ClientSession() as session:
                # Start typing
                await session.post(
                    f"{self.base_url}/api/typing/start",
                    json={
                        'session_id': session_id,
                        'user_id': 'client_0',
                        'message': 'Hello, I am typing a message...'
                    },
                    timeout=10
                )

                await asyncio.sleep(2)

                # Stop typing
                await session.post(
                    f"{self.base_url}/api/typing/stop",
                    json={
                        'session_id': session_id,
                        'user_id': 'client_0'
                    },
                    timeout=10
                )

            # Wait for typing indicators to propagate
            await asyncio.sleep(2)

            # Get client results
            client_results = await asyncio.gather(*client_tasks, return_exceptions=True)

            # Analyze typing events
            successful_clients = [r for r in client_results if isinstance(r, dict) and r.get('typing_events', 0) > 0]
            total_typing_events = sum(r.get('typing_events', 0) for r in client_results if isinstance(r, dict))

            typing_working = len(successful_clients) >= 1 and total_typing_events >= 2  # At least start and stop events

            return {
                'success': typing_working,
                'num_clients': num_clients,
                'successful_clients': len(successful_clients),
                'total_typing_events': total_typing_events,
                'typing_events': dict(typing_events),
                'message': f"Typing indicators working ({total_typing_events} events detected)" if typing_working else "Typing indicators need improvement"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_game_state_updates(self) -> Dict[str, Any]:
        """Test real-time game state updates"""
        try:
            session_id = f"game_state_test_{uuid.uuid4().hex[:8]}"
            state_updates = []

            async def game_state_client():
                try:
                    uri = f"{self.websocket_url}/ws/game_state/{session_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for game state updates
                        for _ in range(10):  # Expect multiple state updates
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                message_data = json.loads(message)

                                if message_data.get('type') == 'game_state_update':
                                    state_updates.append({
                                        'state': message_data.get('state'),
                                        'update_type': message_data.get('update_type'),
                                        'timestamp': message_data.get('timestamp')
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'updates_received': len(state_updates)}
                except Exception as e:
                    return {'error': str(e), 'updates_received': 0}

            # Start game state client
            client_task = asyncio.create_task(game_state_client())

            # Wait for connection
            await asyncio.sleep(1)

            # Simulate game state changes
            game_states = [
                {'scene': 'tavern', 'characters': ['player', 'tavern_keeper'], 'turn': 'player'},
                {'scene': 'combat', 'characters': ['player', 'goblin'], 'turn': 'enemy', 'health': {'player': 15, 'goblin': 8}},
                {'scene': 'victory', 'characters': ['player'], 'turn': 'player', 'loot': ['gold', 'sword']}
            ]

            async with aiohttp.ClientSession() as session:
                for i, state in enumerate(game_states):
                    await session.post(
                        f"{self.base_url}/api/sessions/{session_id}/game_state",
                        json={
                            'game_state': state,
                            'update_type': f'state_change_{i}',
                            'timestamp': datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.5)

            # Wait for all updates to be received
            await asyncio.sleep(3)

            # Get client result
            client_result = await client_task

            if isinstance(client_result, dict):
                updates_received = client_result.get('updates_received', 0)
                state_working = updates_received >= len(game_states) - 1  # Allow for 1 missed update

                return {
                    'success': state_working,
                    'expected_states': len(game_states),
                    'updates_received': updates_received,
                    'state_updates': state_updates,
                    'message': f"Game state updates working ({updates_received}/{len(game_states)} states received)" if state_working else "Game state updates need improvement"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to connect to game state client'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_notification_system(self) -> Dict[str, Any]:
        """Test real-time notification system"""
        try:
            user_id = f"notification_test_{uuid.uuid4().hex[:8]}"
            notifications_received = []

            async def notification_client():
                try:
                    uri = f"{self.websocket_url}/ws/notifications/{user_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for notifications
                        for _ in range(5):  # Expect 5 notifications
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                notification_data = json.loads(message)

                                if notification_data.get('type') == 'notification':
                                    notifications_received.append({
                                        'title': notification_data.get('title'),
                                        'message': notification_data.get('message'),
                                        'priority': notification_data.get('priority'),
                                        'timestamp': notification_data.get('timestamp')
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'notifications_received': len(notifications_received)}
                except Exception as e:
                    return {'error': str(e), 'notifications_received': 0}

            # Start notification client
            client_task = asyncio.create_task(notification_client())

            # Wait for connection
            await asyncio.sleep(1)

            # Send test notifications
            test_notifications = [
                {'title': 'Welcome!', 'message': 'Welcome to DMLogn8n', 'priority': 'info'},
                {'title': 'New Message', 'message': 'You have a new message from your DM', 'priority': 'normal'},
                {'title': 'Game Update', 'message': 'Your game session has been updated', 'priority': 'success'},
                {'title': 'System Alert', 'message': 'Scheduled maintenance in 1 hour', 'priority': 'warning'},
                {'title': 'Achievement!', 'message': 'You completed your first adventure!', 'priority': 'achievement'}
            ]

            async with aiohttp.ClientSession() as session:
                for notification in test_notifications:
                    await session.post(
                        f"{self.base_url}/api/notifications/send",
                        json={
                            'user_id': user_id,
                            **notification,
                            'timestamp': datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.3)

            # Wait for all notifications to be received
            await asyncio.sleep(3)

            # Get client result
            client_result = await client_task

            if isinstance(client_result, dict):
                received_count = client_result.get('notifications_received', 0)
                notification_working = received_count >= len(test_notifications) - 1  # Allow for 1 missed notification

                return {
                    'success': notification_working,
                    'expected_notifications': len(test_notifications),
                    'received_notifications': received_count,
                    'notifications': notifications_received,
                    'message': f"Notification system working ({received_count}/{len(test_notifications)} notifications received)" if notification_working else "Notification system needs improvement"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to connect to notification client'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_event_broadcasting(self) -> Dict[str, Any]:
        """Test event broadcasting to multiple subscribers"""
        try:
            event_channel = f"event_test_{uuid.uuid4().hex[:8]}"
            num_subscribers = 3
            received_events = defaultdict(list)

            async def event_subscriber(subscriber_id):
                try:
                    uri = f"{self.websocket_url}/ws/events/{event_channel}?subscriber_id={subscriber_id}"
                    async with websockets.connect(uri, timeout=10) as websocket:

                        # Listen for events
                        for _ in range(8):  # Expect 8 events
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=6)
                                event_data = json.loads(message)

                                if event_data.get('type') == 'event':
                                    received_events[subscriber_id].append({
                                        'event_type': event_data.get('event_type'),
                                        'data': event_data.get('data'),
                                        'timestamp': event_data.get('timestamp')
                                    })
                            except asyncio.TimeoutError:
                                break

                        return {'subscriber_id': subscriber_id, 'events_received': len(received_events[subscriber_id])}
                except Exception as e:
                    return {'subscriber_id': subscriber_id, 'error': str(e), 'events_received': 0}

            # Start subscribers
            subscriber_tasks = [event_subscriber(f"subscriber_{i}") for i in range(num_subscribers)]

            # Wait for connections
            await asyncio.sleep(1)

            # Broadcast events
            test_events = [
                {'event_type': 'user_joined', 'data': {'user_id': 'user123', 'username': 'TestUser'}},
                {'event_type': 'message_sent', 'data': {'sender': 'user123', 'message': 'Hello everyone!'}},
                {'event_type': 'game_started', 'data': {'session_id': 'sess456', 'scenario': 'tavern'}},
                {'event_type': 'character_updated', 'data': {'character_id': 'char789', 'level': 2}},
                {'event_type': 'achievement_unlocked', 'data': {'user_id': 'user123', 'achievement': 'first_game'}},
                {'event_type': 'user_left', 'data': {'user_id': 'user123', 'reason': 'logout'}},
                {'event_type': 'system_maintenance', 'data': {'scheduled_at': '2024-01-01T02:00:00Z'}},
                {'event_type': 'feature_announcement', 'data': {'feature': 'new_chat_system', 'description': 'Improved chat functionality'}}
            ]

            async with aiohttp.ClientSession() as session:
                for event in test_events:
                    await session.post(
                        f"{self.base_url}/api/events/broadcast",
                        json={
                            'channel': event_channel,
                            **event,
                            'timestamp': datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    await asyncio.sleep(0.2)

            # Wait for all events to be received
            await asyncio.sleep(3)

            # Get subscriber results
            subscriber_results = await asyncio.gather(*subscriber_tasks, return_exceptions=True)

            # Analyze event broadcasting
            successful_subscribers = [r for r in subscriber_results if isinstance(r, dict) and r.get('events_received', 0) >= 6]
            total_events_received = sum(r.get('events_received', 0) for r in subscriber_results if isinstance(r, dict))

            broadcasting_working = (
                len(successful_subscribers) >= num_subscribers - 1 and  # Allow for 1 failed subscriber
                total_events_received >= (num_subscribers - 1) * len(test_events) * 0.8  # 80% delivery rate
            )

            return {
                'success': broadcasting_working,
                'num_subscribers': num_subscribers,
                'successful_subscribers': len(successful_subscribers),
                'total_events': len(test_events),
                'total_events_received': total_events_received,
                'delivery_rate': total_events_received / (num_subscribers * len(test_events)) if num_subscribers * len(test_events) > 0 else 0,
                'received_events': dict(received_events),
                'message': f"Event broadcasting working ({total_events_received}/{num_subscribers * len(test_events)} events delivered)" if broadcasting_working else "Event broadcasting needs improvement"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup(self):
        """Clean up real-time testing resources"""
        try:
            # Close any active connections
            for connection in self.active_connections:
                try:
                    if hasattr(connection, 'close'):
                        asyncio.create_task(connection.close())
                except Exception as e:
                    self.logger.warning(f"Failed to close connection: {e}")

            # Clear test data
            self.active_connections.clear()
            self.test_sessions.clear()
            self.message_sequences.clear()
            self.performance_metrics.clear()
            self.message_latencies.clear()

            self.logger.info("Real-time testing cleanup completed")

        except Exception as e:
            self.logger.error(f"Real-time testing cleanup failed: {e}")