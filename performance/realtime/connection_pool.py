#!/usr/bin/env python3
"""
Connection Pool - Intelligent Database and Service Connection Management
Optimizes connection reuse, reduces overhead, and ensures high availability
"""

import asyncio
import threading
import time
import socket
import ssl
import queue
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import logging
import weakref
from abc import ABC, abstractmethod

@dataclass
class ConnectionConfig:
    """Configuration for connection pools"""
    min_connections: int = 2
    max_connections: int = 20
    connection_timeout: float = 5.0
    idle_timeout: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    health_check_interval: float = 30.0  # 30 seconds
    retry_attempts: int = 3
    retry_delay: float = 0.1
    enable_ssl: bool = False
    ssl_verify: bool = True

@dataclass
class ConnectionMetrics:
    """Metrics for connection tracking"""
    created_time: float
    last_used_time: float
    usage_count: int = 0
    error_count: int = 0
    is_healthy: bool = True
    current_query: Optional[str] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))

class PooledConnection:
    """Base class for pooled connections"""

    def __init__(self, connection_id: str, config: ConnectionConfig):
        self.connection_id = connection_id
        self.config = config
        self.metrics = ConnectionMetrics(
            created_time=time.time(),
            last_used_time=time.time()
        )
        self._connection = None
        self._in_use = False
        self._lock = threading.Lock()

    @abstractmethod
    async def connect(self) -> bool:
        """Establish the actual connection"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close the connection"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if connection is healthy"""
        pass

    @abstractmethod
    async def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute operation on connection"""
        pass

    @property
    def in_use(self) -> bool:
        return self._in_use

    @in_use.setter
    def in_use(self, value: bool):
        with self._lock:
            self._in_use = value
            if value:
                self.metrics.last_used_time = time.time()
                self.metrics.usage_count += 1

    @property
    def age(self) -> float:
        return time.time() - self.metrics.created_time

    @property
    def idle_time(self) -> float:
        return time.time() - self.metrics.last_used_time

    @property
    def is_expired(self) -> bool:
        return self.age > self.config.max_lifetime

    @property
    def is_idle_too_long(self) -> bool:
        return self.idle_time > self.config.idle_timeout

class DatabaseConnection(PooledConnection):
    """Database connection implementation"""

    def __init__(self, connection_id: str, dsn: str, config: ConnectionConfig):
        super().__init__(connection_id, config)
        self.dsn = dsn
        self._connection = None

    async def connect(self) -> bool:
        try:
            # Implementation would use appropriate database driver
            # For example: asyncpg, aiomysql, etc.
            start_time = time.time()

            # Simulate connection
            await asyncio.sleep(0.01)  # Simulate connection time

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            self.metrics.is_healthy = True
            return True

        except Exception as e:
            self.metrics.error_count += 1
            self.metrics.is_healthy = False
            return False

    async def disconnect(self):
        if self._connection:
            try:
                # Close database connection
                self._connection = None
            except Exception:
                pass

    async def health_check(self) -> bool:
        try:
            start_time = time.time()

            # Execute simple health check query
            # await self._connection.fetchval("SELECT 1")
            await asyncio.sleep(0.001)  # Simulate query

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            return True
        except Exception:
            self.metrics.error_count += 1
            self.metrics.is_healthy = False
            return False

    async def execute(self, operation: str, *args, **kwargs) -> Any:
        if not self._connection or not self.metrics.is_healthy:
            raise ConnectionError("Connection not available")

        self.metrics.current_query = operation
        start_time = time.time()

        try:
            # Execute database operation
            # result = await self._connection.fetch(operation, *args, **kwargs)
            await asyncio.sleep(0.002)  # Simulate query time
            result = f"Result for {operation}"

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            return result

        except Exception as e:
            self.metrics.error_count += 1
            raise
        finally:
            self.metrics.current_query = None

class HTTPConnection(PooledConnection):
    """HTTP connection implementation"""

    def __init__(self, connection_id: str, base_url: str, config: ConnectionConfig):
        super().__init__(connection_id, config)
        self.base_url = base_url
        self._session = None

    async def connect(self) -> bool:
        try:
            # Implementation would use aiohttp or httpx
            start_time = time.time()

            # Simulate HTTP session creation
            await asyncio.sleep(0.005)

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            self.metrics.is_healthy = True
            return True

        except Exception as e:
            self.metrics.error_count += 1
            self.metrics.is_healthy = False
            return False

    async def disconnect(self):
        if self._session:
            try:
                await self._session.close()
                self._session = None
            except Exception:
                pass

    async def health_check(self) -> bool:
        try:
            start_time = time.time()

            # Execute simple health check request
            # async with self._session.get(f"{self.base_url}/health") as response:
            #     return response.status == 200
            await asyncio.sleep(0.001)

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            return True
        except Exception:
            self.metrics.error_count += 1
            self.metrics.is_healthy = False
            return False

    async def execute(self, operation: str, *args, **kwargs) -> Any:
        if not self._session or not self.metrics.is_healthy:
            raise ConnectionError("HTTP session not available")

        self.metrics.current_query = operation
        start_time = time.time()

        try:
            # Execute HTTP request
            # method, path = operation.split()
            # url = f"{self.base_url}{path}"
            # async with self._session.request(method, url, *args, **kwargs) as response:
            #     return await response.json()
            await asyncio.sleep(0.003)
            result = f"HTTP response for {operation}"

            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            return result

        except Exception as e:
            self.metrics.error_count += 1
            raise
        finally:
            self.metrics.current_query = None

class ConnectionPool:
    """Intelligent connection pool manager"""

    def __init__(self, connection_type: str, connection_config: ConnectionConfig):
        self.connection_type = connection_type
        self.config = connection_config

        # Connection management
        self._available_connections: queue.Queue = queue.Queue()
        self._all_connections: Dict[str, PooledConnection] = {}
        self._connection_counter = 0

        # Pool statistics
        self.stats = {
            'total_created': 0,
            'total_destroyed': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0
        }

        # Threading and synchronization
        self._pool_lock = threading.RLock()
        self._maintenance_thread = None
        self._running = True

        # Setup logging
        self.logger = logging.getLogger(f"ConnectionPool-{connection_type}")

        # Start maintenance thread
        self._start_maintenance()

    def _start_maintenance(self):
        """Start background maintenance thread"""
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            name=f"PoolMaintenance-{self.connection_type}",
            daemon=True
        )
        self._maintenance_thread.start()

    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """Get a connection from the pool"""
        connection = None
        try:
            connection = self._acquire_connection(timeout)
            yield connection
        finally:
            if connection:
                self._release_connection(connection)

    async def get_connection_async(self, timeout: Optional[float] = None):
        """Get a connection from the pool asynchronously"""
        return await self._acquire_connection_async(timeout)

    def _acquire_connection(self, timeout: Optional[float] = None) -> PooledConnection:
        """Acquire a connection from the pool"""
        timeout = timeout or self.config.connection_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Try to get existing connection
                connection = self._available_connections.get_nowait()

                # Validate connection
                if self._is_connection_valid(connection):
                    connection.in_use = True
                    self.stats['pool_hits'] += 1
                    return connection
                else:
                    # Invalid connection, remove it
                    self._remove_connection(connection)
                    continue

            except queue.Empty:
                # No available connections, try to create new one
                connection = self._create_connection()
                if connection:
                    connection.in_use = True
                    self.stats['pool_misses'] += 1
                    return connection

            # Brief pause before retry
            time.sleep(0.001)

        raise ConnectionError(f"Failed to acquire {self.connection_type} connection within timeout")

    async def _acquire_connection_async(self, timeout: Optional[float] = None) -> PooledConnection:
        """Acquire a connection asynchronously"""
        timeout = timeout or self.config.connection_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Try to get existing connection
                connection = self._available_connections.get_nowait()

                # Validate connection asynchronously
                if await self._is_connection_valid_async(connection):
                    connection.in_use = True
                    self.stats['pool_hits'] += 1
                    return connection
                else:
                    # Invalid connection, remove it
                    await self._remove_connection_async(connection)
                    continue

            except queue.Empty:
                # No available connections, try to create new one
                connection = await self._create_connection_async()
                if connection:
                    connection.in_use = True
                    self.stats['pool_misses'] += 1
                    return connection

            # Brief pause before retry
            await asyncio.sleep(0.001)

        raise ConnectionError(f"Failed to acquire {self.connection_type} connection within timeout")

    def _release_connection(self, connection: PooledConnection):
        """Release a connection back to the pool"""
        if not connection:
            return

        try:
            connection.in_use = False

            # Check if connection is still valid
            if self._is_connection_valid(connection):
                self._available_connections.put(connection)
            else:
                self._remove_connection(connection)

        except Exception as e:
            self.logger.error(f"Error releasing connection: {e}")
            self._remove_connection(connection)

    async def _release_connection_async(self, connection: PooledConnection):
        """Release a connection back to the pool asynchronously"""
        if not connection:
            return

        try:
            connection.in_use = False

            # Check if connection is still valid
            if await self._is_connection_valid_async(connection):
                self._available_connections.put(connection)
            else:
                await self._remove_connection_async(connection)

        except Exception as e:
            self.logger.error(f"Error releasing connection: {e}")
            await self._remove_connection_async(connection)

    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new connection"""
        with self._pool_lock:
            if len(self._all_connections) >= self.config.max_connections:
                return None

            connection_id = f"{self.connection_type}_{self._connection_counter}"
            self._connection_counter += 1

            # Create connection based on type
            if self.connection_type == "database":
                connection = DatabaseConnection(connection_id, "dsn_placeholder", self.config)
            elif self.connection_type == "http":
                connection = HTTPConnection(connection_id, "http://localhost", self.config)
            else:
                return None

            # Try to connect
            if asyncio.run(connection.connect()):
                self._all_connections[connection_id] = connection
                self.stats['total_created'] += 1
                self.stats['active_connections'] += 1
                return connection
            else:
                self.stats['connection_errors'] += 1
                return None

    async def _create_connection_async(self) -> Optional[PooledConnection]:
        """Create a new connection asynchronously"""
        with self._pool_lock:
            if len(self._all_connections) >= self.config.max_connections:
                return None

            connection_id = f"{self.connection_type}_{self._connection_counter}"
            self._connection_counter += 1

            # Create connection based on type
            if self.connection_type == "database":
                connection = DatabaseConnection(connection_id, "dsn_placeholder", self.config)
            elif self.connection_type == "http":
                connection = HTTPConnection(connection_id, "http://localhost", self.config)
            else:
                return None

            # Try to connect
            if await connection.connect():
                self._all_connections[connection_id] = connection
                self.stats['total_created'] += 1
                self.stats['active_connections'] += 1
                return connection
            else:
                self.stats['connection_errors'] += 1
                return None

    def _is_connection_valid(self, connection: PooledConnection) -> bool:
        """Check if connection is valid for reuse"""
        # Check if connection is expired
        if connection.is_expired or connection.is_idle_too_long:
            return False

        # Check health
        if not connection.metrics.is_healthy:
            return False

        # Check error rate
        if connection.metrics.usage_count > 0:
            error_rate = connection.metrics.error_count / connection.metrics.usage_count
            if error_rate > 0.1:  # 10% error rate threshold
                return False

        return True

    async def _is_connection_valid_async(self, connection: PooledConnection) -> bool:
        """Check if connection is valid for reuse asynchronously"""
        # Check if connection is expired
        if connection.is_expired or connection.is_idle_too_long:
            return False

        # Check health
        if not connection.metrics.is_healthy:
            return False

        # Perform health check
        if not await connection.health_check():
            return False

        # Check error rate
        if connection.metrics.usage_count > 0:
            error_rate = connection.metrics.error_count / connection.metrics.usage_count
            if error_rate > 0.1:  # 10% error rate threshold
                return False

        return True

    def _remove_connection(self, connection: PooledConnection):
        """Remove a connection from the pool"""
        try:
            asyncio.run(connection.disconnect())
            self._all_connections.pop(connection.connection_id, None)
            self.stats['total_destroyed'] += 1
            self.stats['active_connections'] -= 1
        except Exception as e:
            self.logger.error(f"Error removing connection: {e}")

    async def _remove_connection_async(self, connection: PooledConnection):
        """Remove a connection from the pool asynchronously"""
        try:
            await connection.disconnect()
            self._all_connections.pop(connection.connection_id, None)
            self.stats['total_destroyed'] += 1
            self.stats['active_connections'] -= 1
        except Exception as e:
            self.logger.error(f"Error removing connection: {e}")

    def _maintenance_loop(self):
        """Background maintenance loop"""
        while self._running:
            try:
                self._perform_maintenance()
                time.sleep(self.config.health_check_interval)
            except Exception as e:
                self.logger.error(f"Maintenance error: {e}")

    def _perform_maintenance(self):
        """Perform connection pool maintenance"""
        current_time = time.time()
        connections_to_remove = []

        with self._pool_lock:
            for connection in list(self._all_connections.values()):
                # Remove expired connections
                if connection.is_expired:
                    connections_to_remove.append(connection)
                    continue

                # Remove idle connections (but keep minimum)
                if (connection.is_idle_too_long and
                    len(self._all_connections) > self.config.min_connections):
                    connections_to_remove.append(connection)
                    continue

                # Health check for idle connections
                if not connection.in_use:
                    try:
                        # Run health check in background
                        threading.Thread(
                            target=self._health_check_connection,
                            args=(connection,),
                            daemon=True
                        ).start()
                    except Exception as e:
                        self.logger.error(f"Health check error: {e}")

            # Remove marked connections
            for connection in connections_to_remove:
                self._remove_connection(connection)

            # Ensure minimum connections
            self._ensure_minimum_connections()

    def _health_check_connection(self, connection: PooledConnection):
        """Perform health check on connection"""
        try:
            is_healthy = asyncio.run(connection.health_check())
            if not is_healthy:
                self._remove_connection(connection)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self._remove_connection(connection)

    def _ensure_minimum_connections(self):
        """Ensure minimum number of connections in pool"""
        current_count = len(self._all_connections)
        needed = max(0, self.config.min_connections - current_count)

        for _ in range(needed):
            connection = self._create_connection()
            if connection:
                connection.in_use = False
                self._available_connections.put(connection)

    def get_pool_stats(self) -> Dict:
        """Get comprehensive pool statistics"""
        stats = self.stats.copy()
        stats.update({
            'connection_type': self.connection_type,
            'total_connections': len(self._all_connections),
            'available_connections': self._available_connections.qsize(),
            'active_connections': len([c for c in self._all_connections.values() if c.in_use]),
            'pool_efficiency': (stats['pool_hits'] / max(1, stats['pool_hits'] + stats['pool_misses'])) * 100,
            'error_rate': (stats['connection_errors'] / max(1, stats['total_created'])) * 100
        })

        # Add connection-specific metrics
        if self._all_connections:
            response_times = []
            for conn in self._all_connections.values():
                response_times.extend(conn.metrics.response_times)

            if response_times:
                stats['avg_response_time_ms'] = sum(response_times) / len(response_times) * 1000
                stats['max_response_time_ms'] = max(response_times) * 1000
                stats['min_response_time_ms'] = min(response_times) * 1000

        return stats

    def close(self):
        """Close connection pool and all connections"""
        self._running = False

        with self._pool_lock:
            for connection in list(self._all_connections.values()):
                asyncio.run(connection.disconnect())

            self._all_connections.clear()

            # Clear queue
            while not self._available_connections.empty():
                try:
                    self._available_connections.get_nowait()
                except queue.Empty:
                    break

        self.stats['active_connections'] = 0

class ConnectionPoolManager:
    """Manages multiple connection pools"""

    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.logger = logging.getLogger("ConnectionPoolManager")

    def create_pool(self, pool_name: str, connection_type: str,
                   config: Optional[ConnectionConfig] = None) -> ConnectionPool:
        """Create a new connection pool"""
        if pool_name in self.pools:
            raise ValueError(f"Pool {pool_name} already exists")

        config = config or ConnectionConfig()
        pool = ConnectionPool(connection_type, config)
        self.pools[pool_name] = pool

        self.logger.info(f"Created connection pool: {pool_name} ({connection_type})")
        return pool

    def get_pool(self, pool_name: str) -> Optional[ConnectionPool]:
        """Get existing connection pool"""
        return self.pools.get(pool_name)

    def remove_pool(self, pool_name: str):
        """Remove and close a connection pool"""
        if pool_name in self.pools:
            pool = self.pools.pop(pool_name)
            pool.close()
            self.logger.info(f"Removed connection pool: {pool_name}")

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all pools"""
        return {name: pool.get_pool_stats() for name, pool in self.pools.items()}

    def close_all(self):
        """Close all connection pools"""
        for pool in self.pools.values():
            pool.close()
        self.pools.clear()

# Global connection pool manager
connection_pool_manager = ConnectionPoolManager()

# Pre-configured pools for common services
def setup_default_pools():
    """Setup default connection pools for DMLogn8n"""
    # Database pool
    db_config = ConnectionConfig(
        min_connections=5,
        max_connections=50,
        connection_timeout=3.0
    )
    connection_pool_manager.create_pool("database", "database", db_config)

    # HTTP API pool
    http_config = ConnectionConfig(
        min_connections=3,
        max_connections=30,
        connection_timeout=2.0
    )
    connection_pool_manager.create_pool("http", "http", http_config)

    # Cache pool
    cache_config = ConnectionConfig(
        min_connections=2,
        max_connections=20,
        connection_timeout=1.0
    )
    connection_pool_manager.create_pool("cache", "http", cache_config)

# Initialize default pools
setup_default_pools()