#!/usr/bin/env python3
"""
WebSocket Optimizer - Advanced Real-time Communication System
Optimizes WebSocket connections for instant, reliable real-time updates
"""

import asyncio
import json
import time
import threading
import zlib
import hashlib
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import weakref
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

class MessageType(Enum):
    """WebSocket message types"""
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    MULTICAST = "multicast"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    ERROR = "error"

class CompressionType(Enum):
    """Message compression types"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"  # Fast compression for real-time

@dataclass
class WebSocketMessage:
    """Optimized WebSocket message structure"""
    type: MessageType
    data: Any
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default="")
    compression: CompressionType = CompressionType.NONE
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    requires_ack: bool = False
    target_clients: Optional[Set[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.message_id:
            self.message_id = f"msg_{int(self.timestamp * 1000000)}_{id(self)}"

@dataclass
class ClientConnection:
    """Client connection with optimization metadata"""
    websocket: WebSocketServerProtocol
    client_id: str
    connected_time: float
    last_activity: float
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    ping_pong_time: float = 0.0
    compression_enabled: bool = True
    subscribed_channels: Set[str] = field(default_factory=set)
    priority_queue: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return (time.time() - self.last_activity) < 300  # 5 minutes timeout

    @property
    def latency_ms(self) -> float:
        return self.ping_pong_time * 1000

@dataclass
class WebSocketConfig:
    """WebSocket optimization configuration"""
    # Connection settings
    max_connections: int = 1000
    connection_timeout: float = 300.0  # 5 minutes
    heartbeat_interval: float = 30.0  # 30 seconds
    ping_timeout: float = 10.0  # 10 seconds

    # Message optimization
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress messages > 1KB
    default_compression: CompressionType = CompressionType.GZIP
    message_queue_size: int = 1000

    # Performance settings
    enable_batching: bool = True
    batch_size: int = 10
    batch_timeout: float = 0.01  # 10ms
    enable_priority_queue: bool = True

    # Reliability settings
    enable_ack: bool = False
    ack_timeout: float = 5.0
    max_retries: int = 3

    # Rate limiting
    rate_limit_per_second: int = 100
    rate_limit_burst: int = 200

class WebSocketOptimizer:
    """Advanced WebSocket optimization system"""

    def __init__(self, config: Optional[WebSocketConfig] = None):
        self.config = config or WebSocketConfig()

        # Connection management
        self.connections: Dict[str, ClientConnection] = {}
        self.connection_lock = asyncio.Lock()

        # Message queuing and batching
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.message_queue_size)
        self.priority_queue: asyncio.PriorityQueue = asyncio.Queue()
        self.batch_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.batch_lock = asyncio.Lock()

        # Channel management
        self.channels: Dict[str, Set[str]] = defaultdict(set)  # channel -> client_ids
        self.channel_lock = asyncio.Lock()

        # Performance tracking
        self.metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'avg_latency_ms': 0.0,
            'compression_ratio': 0.0,
            'queue_size': 0,
            'dropped_messages': 0
        }

        # Rate limiting
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.rate_limit_burst))

        # Message acknowledgments
        self.pending_acks: Dict[str, WebSocketMessage] = {}
        self.ack_timeout_task: Optional[asyncio.Task] = None

        # Background tasks
        self.running = False
        self.background_tasks: List[asyncio.Task] = []

        # Setup logging
        self.logger = logging.getLogger("WebSocketOptimizer")

    async def start(self):
        """Start the WebSocket optimizer"""
        if self.running:
            return

        self.running = True

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._message_processor()),
            asyncio.create_task(self._heartbeat_sender()),
            asyncio.create_task(self._connection_monitor()),
            asyncio.create_task(self._batch_processor()),
            asyncio.create_task(self._metrics_collector()),
        ]

        if self.config.enable_ack:
            self.background_tasks.append(
                asyncio.create_task(self._ack_timeout_handler())
            )

        self.logger.info("WebSocket optimizer started")

    async def stop(self):
        """Stop the WebSocket optimizer"""
        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Close all connections
        for client in list(self.connections.values()):
            try:
                await client.websocket.close()
            except:
                pass

        self.connections.clear()
        self.logger.info("WebSocket optimizer stopped")

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        client_id = f"client_{int(time.time() * 1000000)}_{id(websocket)}"

        # Create client connection
        client = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            connected_time=time.time(),
            last_activity=time.time()
        )

        async with self.connection_lock:
            self.connections[client_id] = client
            self.metrics['total_connections'] += 1
            self.metrics['active_connections'] += 1

        self.logger.info(f"New client connected: {client_id}")

        try:
            # Send welcome message
            await self.send_to_client(client_id, {
                'type': 'welcome',
                'client_id': client_id,
                'server_time': time.time()
            })

            # Handle messages
            async for message in websocket:
                await self._handle_message(client, message)

        except ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"Connection error for {client_id}: {e}")
        finally:
            await self._cleanup_connection(client_id)

    async def _handle_message(self, client: ClientConnection, raw_message: str):
        """Handle incoming message from client"""
        try:
            # Update activity
            client.last_activity = time.time()
            client.message_count += 1
            client.bytes_received += len(raw_message)

            # Parse message
            try:
                message_data = json.loads(raw_message)
            except json.JSONDecodeError:
                await self.send_error(client.client_id, "Invalid JSON format")
                return

            # Handle different message types
            msg_type = message_data.get('type', 'unknown')

            if msg_type == 'ping':
                await self._handle_ping(client)
            elif msg_type == 'subscribe':
                await self._handle_subscribe(client, message_data)
            elif msg_type == 'unsubscribe':
                await self._handle_unsubscribe(client, message_data)
            elif msg_type == 'message':
                await self._handle_client_message(client, message_data)
            elif msg_type == 'ack':
                await self._handle_ack(client, message_data)
            else:
                self.logger.warning(f"Unknown message type: {msg_type}")

            self.metrics['messages_received'] += 1

        except Exception as e:
            self.logger.error(f"Message handling error: {e}")
            await self.send_error(client.client_id, str(e))

    async def _handle_ping(self, client: ClientConnection):
        """Handle ping message"""
        start_time = time.time()
        await self.send_to_client(client.client_id, {
            'type': 'pong',
            'timestamp': start_time
        }, requires_ack=False)
        client.ping_pong_time = time.time() - start_time

    async def _handle_subscribe(self, client: ClientConnection, message_data: Dict):
        """Handle channel subscription"""
        channel = message_data.get('channel')
        if channel:
            async with self.channel_lock:
                self.channels[channel].add(client.client_id)
                client.subscribed_channels.add(channel)

            await self.send_to_client(client.client_id, {
                'type': 'subscribed',
                'channel': channel
            })

    async def _handle_unsubscribe(self, client: ClientConnection, message_data: Dict):
        """Handle channel unsubscription"""
        channel = message_data.get('channel')
        if channel:
            async with self.channel_lock:
                self.channels[channel].discard(client.client_id)
                client.subscribed_channels.discard(channel)

            await self.send_to_client(client.client_id, {
                'type': 'unsubscribed',
                'channel': channel
            })

    async def _handle_client_message(self, client: ClientConnection, message_data: Dict):
        """Handle client message for broadcasting"""
        channel = message_data.get('channel')
        data = message_data.get('data')

        if channel and data:
            # Broadcast to channel (excluding sender)
            await self.broadcast_to_channel(channel, data, exclude_client=client.client_id)

    async def _handle_ack(self, client: ClientConnection, message_data: Dict):
        """Handle message acknowledgment"""
        message_id = message_data.get('message_id')
        if message_id in self.pending_acks:
            del self.pending_acks[message_id]

    async def send_to_client(self, client_id: str, data: Any, priority: int = 0,
                           requires_ack: Optional[bool] = None) -> bool:
        """Send message to specific client"""
        client = self.connections.get(client_id)
        if not client:
            return False

        # Rate limiting
        if not self._check_rate_limit(client_id):
            self.logger.warning(f"Rate limit exceeded for client {client_id}")
            return False

        # Create message
        message = WebSocketMessage(
            type=MessageType.UNICAST,
            data=data,
            priority=priority,
            requires_ack=requires_ack if requires_ack is not None else self.config.enable_ack,
            target_clients={client_id}
        )

        # Queue for sending
        if priority > 0 and self.config.enable_priority_queue:
            await self.priority_queue.put((priority, message))
        else:
            await self.message_queue.put(message)

        return True

    async def broadcast_to_channel(self, channel: str, data: Any, priority: int = 0,
                                  exclude_client: Optional[str] = None) -> int:
        """Broadcast message to all clients in a channel"""
        async with self.channel_lock:
            target_clients = self.channels.get(channel, set()).copy()

        if exclude_client:
            target_clients.discard(exclude_client)

        if not target_clients:
            return 0

        message = WebSocketMessage(
            type=MessageType.MULTICAST,
            data=data,
            priority=priority,
            target_clients=target_clients,
            metadata={'channel': channel}
        )

        if priority > 0 and self.config.enable_priority_queue:
            await self.priority_queue.put((priority, message))
        else:
            await self.message_queue.put(message)

        return len(target_clients)

    async def broadcast_to_all(self, data: Any, priority: int = 0) -> int:
        """Broadcast message to all connected clients"""
        async with self.connection_lock:
            target_clients = set(self.connections.keys())

        message = WebSocketMessage(
            type=MessageType.BROADCAST,
            data=data,
            priority=priority,
            target_clients=target_clients
        )

        if priority > 0 and self.config.enable_priority_queue:
            await self.priority_queue.put((priority, message))
        else:
            await self.message_queue.put(message)

        return len(target_clients)

    async def _message_processor(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Process priority queue first
                priority_message = None
                try:
                    _, priority_message = self.priority_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

                if priority_message:
                    await self._process_message(priority_message)
                else:
                    # Process normal queue
                    try:
                        message = await asyncio.wait_for(
                            self.message_queue.get(),
                            timeout=0.1
                        )
                        await self._process_message(message)
                    except asyncio.TimeoutError:
                        continue

            except Exception as e:
                self.logger.error(f"Message processor error: {e}")

    async def _process_message(self, message: WebSocketMessage):
        """Process and send individual message"""
        if not message.target_clients:
            return

        # Prepare message data
        message_data = {
            'type': message.type.value,
            'data': message.data,
            'timestamp': message.timestamp,
            'message_id': message.message_id,
            **message.metadata
        }

        # Add acknowledgment requirement
        if message.requires_ack:
            message_data['requires_ack'] = True
            self.pending_acks[message.message_id] = message

        # Serialize and compress
        serialized = json.dumps(message_data)
        compressed_data = await self._compress_message(serialized)

        # Send to target clients
        sent_count = 0
        failed_clients = set()

        for client_id in message.target_clients:
            client = self.connections.get(client_id)
            if not client or not client.is_active:
                failed_clients.add(client_id)
                continue

            try:
                await client.websocket.send(compressed_data)
                client.bytes_sent += len(compressed_data)
                sent_count += 1

                # Update metrics
                self.metrics['messages_sent'] += 1
                self.metrics['bytes_sent'] += len(compressed_data)

            except ConnectionClosed:
                failed_clients.add(client_id)
            except Exception as e:
                self.logger.error(f"Send error to {client_id}: {e}")
                failed_clients.add(client_id)

        # Handle failed clients
        for client_id in failed_clients:
            await self._cleanup_connection(client_id)

        # Update compression ratio
        if len(serialized) > 0:
            compression_ratio = (1 - len(compressed_data) / len(serialized)) * 100
            self.metrics['compression_ratio'] = (
                self.metrics['compression_ratio'] * 0.9 + compression_ratio * 0.1
            )

    async def _compress_message(self, data: str) -> Union[str, bytes]:
        """Compress message if beneficial"""
        if not self.config.enable_compression:
            return data

        if len(data) < self.config.compression_threshold:
            return data

        try:
            if self.config.default_compression == CompressionType.GZIP:
                compressed = zlib.compress(data.encode('utf-8'), level=1)
                # Return compressed data with prefix
                return b'COMP:' + compressed
        except Exception as e:
            self.logger.error(f"Compression error: {e}")

        return data

    async def _heartbeat_sender(self):
        """Send periodic heartbeat messages"""
        while self.running:
            try:
                heartbeat_data = {
                    'type': 'heartbeat',
                    'timestamp': time.time(),
                    'server_id': 'dmlogn8n_server'
                }

                await self.broadcast_to_all(heartbeat_data, priority=10)
                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")

    async def _connection_monitor(self):
        """Monitor and cleanup inactive connections"""
        while self.running:
            try:
                current_time = time.time()
                inactive_clients = []

                async with self.connection_lock:
                    for client_id, client in self.connections.items():
                        if not client.is_active:
                            inactive_clients.append(client_id)
                        elif current_time - client.last_activity > self.config.connection_timeout:
                            inactive_clients.append(client_id)

                # Cleanup inactive connections
                for client_id in inactive_clients:
                    await self._cleanup_connection(client_id)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Connection monitor error: {e}")

    async def _batch_processor(self):
        """Batch message processing for better performance"""
        while self.running and self.config.enable_batching:
            try:
                await asyncio.sleep(self.config.batch_timeout)

                async with self.batch_lock:
                    # Process batches
                    for client_id, messages in list(self.batch_messages.items()):
                        if len(messages) >= self.config.batch_size:
                            await self._send_batch(client_id, messages)
                            self.batch_messages[client_id] = []

                    # Check old messages
                    current_time = time.time()
                    for client_id, messages in list(self.batch_messages.items()):
                        if messages and (current_time - messages[0].timestamp) > 0.1:  # 100ms old
                            await self._send_batch(client_id, messages)
                            self.batch_messages[client_id] = []

            except Exception as e:
                self.logger.error(f"Batch processor error: {e}")

    async def _send_batch(self, client_id: str, messages: List[WebSocketMessage]):
        """Send batch of messages to client"""
        client = self.connections.get(client_id)
        if not client:
            return

        try:
            batch_data = {
                'type': 'batch',
                'messages': [
                    {
                        'type': msg.type.value,
                        'data': msg.data,
                        'timestamp': msg.timestamp,
                        'message_id': msg.message_id,
                        **msg.metadata
                    }
                    for msg in messages
                ]
            }

            serialized = json.dumps(batch_data)
            compressed_data = await self._compress_message(serialized)

            await client.websocket.send(compressed_data)
            client.bytes_sent += len(compressed_data)

            # Update metrics
            self.metrics['messages_sent'] += len(messages)
            self.metrics['bytes_sent'] += len(compressed_data)

        except Exception as e:
            self.logger.error(f"Batch send error to {client_id}: {e}")

    async def _metrics_collector(self):
        """Collect and update performance metrics"""
        while self.running:
            try:
                # Update active connections
                active_count = sum(1 for client in self.connections.values() if client.is_active)
                self.metrics['active_connections'] = active_count

                # Calculate average latency
                if self.connections:
                    latencies = [client.latency_ms for client in self.connections.values() if client.latency_ms > 0]
                    if latencies:
                        self.metrics['avg_latency_ms'] = sum(latencies) / len(latencies)

                # Update queue size
                self.metrics['queue_size'] = self.message_queue.qsize()

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")

    async def _ack_timeout_handler(self):
        """Handle acknowledgment timeouts"""
        while self.running:
            try:
                current_time = time.time()
                timed_out_messages = []

                for message_id, message in list(self.pending_acks.items()):
                    if current_time - message.timestamp > self.config.ack_timeout:
                        timed_out_messages.append((message_id, message))

                # Handle timed out messages
                for message_id, message in timed_out_messages:
                    if message.retry_count < message.max_retries:
                        # Retry message
                        message.retry_count += 1
                        message.timestamp = current_time
                        await self.message_queue.put(message)
                        self.logger.info(f"Retrying message {message_id} (attempt {message.retry_count})")
                    else:
                        # Give up on message
                        del self.pending_acks[message_id]
                        self.metrics['dropped_messages'] += 1
                        self.logger.warning(f"Message {message_id} dropped after {message.max_retries} retries")

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                self.logger.error(f"ACK timeout handler error: {e}")

    async def _cleanup_connection(self, client_id: str):
        """Clean up client connection"""
        async with self.connection_lock:
            client = self.connections.pop(client_id, None)
            if client:
                # Remove from channels
                async with self.channel_lock:
                    for channel in client.subscribed_channels:
                        self.channels[channel].discard(client_id)

                # Close websocket
                try:
                    await client.websocket.close()
                except:
                    pass

                self.metrics['active_connections'] -= 1
                self.logger.info(f"Cleaned up connection: {client_id}")

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client exceeds rate limit"""
        current_time = time.time()
        client_times = self.rate_limiters[client_id]

        # Remove old timestamps
        while client_times and current_time - client_times[0] > 1.0:
            client_times.popleft()

        # Check if under limit
        if len(client_times) < self.config.rate_limit_per_second:
            client_times.append(current_time)
            return True

        return False

    async def send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        await self.send_to_client(client_id, {
            'type': 'error',
            'error': error_message,
            'timestamp': time.time()
        }, priority=5)

    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        return {
            **self.metrics,
            'channels_count': len(self.channels),
            'pending_acks': len(self.pending_acks),
            'rate_limiters_active': len(self.rate_limiters),
            'config': {
                'max_connections': self.config.max_connections,
                'heartbeat_interval': self.config.heartbeat_interval,
                'enable_compression': self.config.enable_compression,
                'enable_batching': self.config.enable_batching
            }
        }

    def get_connection_details(self) -> List[Dict]:
        """Get detailed information about all connections"""
        return [
            {
                'client_id': client.client_id,
                'connected_time': client.connected_time,
                'last_activity': client.last_activity,
                'message_count': client.message_count,
                'bytes_sent': client.bytes_sent,
                'bytes_received': client.bytes_received,
                'latency_ms': client.latency_ms,
                'subscribed_channels': list(client.subscribed_channels),
                'is_active': client.is_active
            }
            for client in self.connections.values()
        ]

# Global WebSocket optimizer instance
websocket_optimizer = WebSocketOptimizer()

# Utility functions
async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """Start optimized WebSocket server"""
    await websocket_optimizer.start()

    server = await websockets.serve(
        websocket_optimizer.handle_connection,
        host,
        port,
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    )

    logging.info(f"WebSocket server started on {host}:{port}")
    return server

# Decorators for WebSocket operations
def websocket_handler(func: Callable) -> Callable:
    """Decorator for WebSocket message handlers"""
    @wraps(func)
    async def wrapper(client: ClientConnection, message_data: Dict):
        try:
            await func(client, message_data)
        except Exception as e:
            logging.error(f"WebSocket handler error: {e}")
            await websocket_optimizer.send_error(client.client_id, str(e))
    return wrapper