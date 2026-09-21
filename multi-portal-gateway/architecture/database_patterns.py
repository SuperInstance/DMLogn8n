"""
Advanced Database Optimization and Sharding Strategies
Cutting-edge database patterns with intelligent sharding,
connection pooling, query optimization, and performance tuning.

This module implements:
- Intelligent database sharding and partitioning
- Advanced connection pooling with load balancing
- Query optimization and caching strategies
- Database replication and failover mechanisms
- Multi-database transaction coordination
- Performance monitoring and analytics
- Automatic scaling and resource management
- Data migration and schema evolution
"""

import asyncio
import time
import json
import hashlib
import struct
from abc import ABC, abstractmethod
from typing import (
    Dict, List, Optional, Any, Callable, Union,
    TypeVar, Generic, Tuple, Set, AsyncGenerator,
    NamedTuple
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import structlog
import asyncpg
import aioredis
import aiomysql
import motor.motor_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect
import prometheus_client as prom
import numpy as np
from sklearn.cluster import KMeans
import yaml

# Configure structured logging
logger = structlog.get_logger()

# Type variables
T = TypeVar('T')
RecordType = TypeVar('RecordType')

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"

class ShardingStrategy(Enum):
    """Sharding strategies"""
    HASH = "hash"                    # Consistent hash sharding
    RANGE = "range"                  # Range-based sharding
    DIRECTORY = "directory"          # Directory-based sharding
    GEOGRAPHIC = "geographic"        # Geographic sharding
    TENANT = "tenant"                # Tenant-based sharding
    TIME_SERIES = "time_series"      # Time-series sharding

class ReplicationRole(Enum):
    """Database replication roles"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ARBITER = "arbiter"

@dataclass
class DatabaseNode:
    """Database node configuration"""
    node_id: str
    host: str
    port: int
    database: str
    username: str
    password: str
    db_type: DatabaseType
    role: ReplicationRole = ReplicationRole.SECONDARY
    weight: int = 1
    max_connections: int = 100
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None

@dataclass
class ShardingConfig:
    """Sharding configuration"""
    strategy: ShardingStrategy
    shard_count: int
    shard_key: str
    hash_function: Optional[str] = None
    ranges: Optional[List[Tuple[Any, Any]]] = None
    directory_service: Optional[str] = None

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_id: str
    query_hash: str
    execution_time: float
    rows_affected: int
    database: str
    table: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

class ConnectionPool:
    """Advanced database connection pool with health monitoring"""

    def __init__(self, node: DatabaseNode, min_size: int = 5, max_size: int = 20):
        self.node = node
        self.min_size = min_size
        self.max_size = max_size
        self.pool: List[Any] = []
        self.active_connections: Set[Any] = set()
        self.semaphore = asyncio.Semaphore(max_size)
        self.pool_lock = asyncio.Lock()
        self.health_check_interval = 30.0
        self.last_health_check = datetime.utcnow()

        # Metrics
        self.pool_size_gauge = prom.Gauge(
            f'db_pool_size_{node.node_id}',
            f'Database pool size for {node.node_id}'
        )
        self.active_connections_gauge = prom.Gauge(
            f'db_active_connections_{node.node_id}',
            f'Active connections for {node.node_id}'
        )
        self.pool_hits_counter = prom.Counter(
            f'db_pool_hits_{node.node_id}',
            f'Connection pool hits for {node.node_id}'
        )

    async def initialize(self):
        """Initialize connection pool"""
        await self._create_min_connections()
        # Start health monitoring
        asyncio.create_task(self._health_monitor())

    async def acquire(self) -> Any:
        """Acquire connection from pool"""
        await self.semaphore.acquire()

        async with self.pool_lock:
            if self.pool:
                connection = self.pool.pop()
                self.active_connections.add(connection)
                self.pool_hits_counter.inc()
            else:
                # Create new connection
                connection = await self._create_connection()
                self.active_connections.add(connection)

            self._update_metrics()
            return connection

    async def release(self, connection):
        """Release connection back to pool"""
        async with self.pool_lock:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

                # Check if connection is healthy
                if await self._is_connection_healthy(connection):
                    self.pool.append(connection)
                else:
                    await self._close_connection(connection)

            self.semaphore.release()
            self._update_metrics()

    async def _create_connection(self):
        """Create new database connection"""
        if self.node.db_type == DatabaseType.POSTGRESQL:
            return await asyncpg.connect(
                host=self.node.host,
                port=self.node.port,
                database=self.node.database,
                user=self.node.username,
                password=self.node.password,
                min_size=self.min_size,
                max_size=self.max_size
            )
        elif self.node.db_type == DatabaseType.MYSQL:
            return await aiomysql.connect(
                host=self.node.host,
                port=self.node.port,
                db=self.node.database,
                user=self.node.username,
                password=self.node.password,
                minsize=self.min_size,
                maxsize=self.max_size
            )
        elif self.node.db_type == DatabaseType.MONGODB:
            client = motor.motor_asyncio.AsyncIOMotorClient(
                f"mongodb://{self.node.username}:{self.node.password}@{self.node.host}:{self.node.port}/{self.node.database}"
            )
            return client[self.node.database]
        else:
            raise ValueError(f"Unsupported database type: {self.node.db_type}")

    async def _close_connection(self, connection):
        """Close database connection"""
        try:
            if hasattr(connection, 'close'):
                await connection.close()
            elif hasattr(connection, 'aclose'):
                await connection.aclose()
        except Exception as e:
            logger.error("Error closing connection", error=str(e))

    async def _create_min_connections(self):
        """Create minimum connections for pool"""
        for _ in range(self.min_size):
            try:
                connection = await self._create_connection()
                self.pool.append(connection)
            except Exception as e:
                logger.error("Error creating initial connection", error=str(e))

    async def _is_connection_healthy(self, connection) -> bool:
        """Check if connection is healthy"""
        try:
            if self.node.db_type == DatabaseType.POSTGRESQL:
                await connection.execute("SELECT 1")
            elif self.node.db_type == DatabaseType.MYSQL:
                await connection.ping()
            elif self.node.db_type == DatabaseType.MONGODB:
                await connection.command('ping')
            return True
        except Exception:
            return False

    async def _health_monitor(self):
        """Monitor connection pool health"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_pool_health()
            except Exception as e:
                logger.error("Pool health monitoring error", error=str(e))

    async def _check_pool_health(self):
        """Check health of all connections in pool"""
        async with self.pool_lock:
            unhealthy_connections = []

            # Check idle connections
            for connection in self.pool:
                if not await self._is_connection_healthy(connection):
                    unhealthy_connections.append(connection)

            # Remove unhealthy connections
            for connection in unhealthy_connections:
                self.pool.remove(connection)
                await self._close_connection(connection)

            # Replenish pool if needed
            while len(self.pool) < self.min_size:
                try:
                    connection = await self._create_connection()
                    self.pool.append(connection)
                except Exception as e:
                    logger.error("Error replenishing pool", error=str(e))
                    break

        self.last_health_check = datetime.utcnow()

    def _update_metrics(self):
        """Update pool metrics"""
        self.pool_size_gauge.set(len(self.pool))
        self.active_connections_gauge.set(len(self.active_connections))

class ShardRouter:
    """Intelligent shard routing with multiple strategies"""

    def __init__(self, config: ShardingConfig):
        self.config = config
        self.shard_nodes: Dict[str, DatabaseNode] = {}
        self.shard_mappings: Dict[str, str] = {}
        self.hash_ring = None

        if config.strategy == ShardingStrategy.HASH:
            self._init_hash_ring()
        elif config.strategy == ShardingStrategy.RANGE:
            self._init_range_mappings()

    def add_shard(self, shard_id: str, node: DatabaseNode):
        """Add shard node"""
        self.shard_nodes[shard_id] = node

        if self.config.strategy == ShardingStrategy.HASH:
            self._add_to_hash_ring(shard_id)

    def get_shard(self, key: Any) -> Optional[str]:
        """Get shard ID for given key"""
        if self.config.strategy == ShardingStrategy.HASH:
            return self._hash_shard(key)
        elif self.config.strategy == ShardingStrategy.RANGE:
            return self._range_shard(key)
        elif self.config.strategy == ShardingStrategy.DIRECTORY:
            return self._directory_shard(key)
        elif self.config.strategy == ShardingStrategy.TENANT:
            return self._tenant_shard(key)
        elif self.config.strategy == ShardingStrategy.TIME_SERIES:
            return self._time_series_shard(key)
        else:
            return list(self.shard_nodes.keys())[0]  # Default to first shard

    def _init_hash_ring(self):
        """Initialize consistent hash ring"""
        self.hash_ring = {}
        for i in range(self.config.shard_count):
            shard_id = f"shard_{i}"
            for replica in range(150):  # Virtual nodes
                key = f"{shard_id}:{replica}"
                hash_value = self._hash_function(key)
                self.hash_ring[hash_value] = shard_id

        # Sort hash values
        self.sorted_hashes = sorted(self.hash_ring.keys())

    def _add_to_hash_ring(self, shard_id: str):
        """Add shard to hash ring"""
        for replica in range(150):
            key = f"{shard_id}:{replica}"
            hash_value = self._hash_function(key)
            self.hash_ring[hash_value] = shard_id

        self.sorted_hashes = sorted(self.hash_ring.keys())

    def _hash_function(self, key: str) -> int:
        """Hash function for consistent hashing"""
        if self.config.hash_function == "md5":
            return int(hashlib.md5(key.encode()).hexdigest(), 16)
        elif self.config.hash_function == "sha1":
            return int(hashlib.sha1(key.encode()).hexdigest(), 16)
        else:
            # Default to built-in hash
            return hash(key)

    def _hash_shard(self, key: Any) -> str:
        """Get shard using consistent hashing"""
        key_str = str(key)
        hash_value = self._hash_function(key_str)

        # Find first hash value >= target
        for ring_hash in self.sorted_hashes:
            if ring_hash >= hash_value:
                return self.hash_ring[ring_hash]

        # Wrap around
        return self.hash_ring[self.sorted_hashes[0]]

    def _init_range_mappings(self):
        """Initialize range-based mappings"""
        if self.config.ranges:
            for i, (start, end) in enumerate(self.config.ranges):
                shard_id = f"shard_{i}"
                self.shard_mappings[shard_id] = (start, end)

    def _range_shard(self, key: Any) -> str:
        """Get shard using range-based routing"""
        for shard_id, (start, end) in self.shard_mappings.items():
            if start <= key < end:
                return shard_id
        return list(self.shard_nodes.keys())[0]

    def _directory_shard(self, key: Any) -> str:
        """Get shard using directory-based routing"""
        # This would typically query a directory service
        key_str = str(key)
        if key_str in self.shard_mappings:
            return self.shard_mappings[key_str]
        return list(self.shard_nodes.keys())[0]

    def _tenant_shard(self, key: Any) -> str:
        """Get shard using tenant-based routing"""
        tenant_id = str(key)
        # Use consistent hashing for tenant distribution
        return self._hash_shard(tenant_id)

    def _time_series_shard(self, key: Any) -> str:
        """Get shard using time-series routing"""
        # Assume key is timestamp or time-based
        if isinstance(key, datetime):
            timestamp = key
        else:
            timestamp = datetime.fromisoformat(str(key))

        # Shard by day/month/year
        shard_key = f"{timestamp.year}_{timestamp.month}"
        return self._hash_shard(shard_key)

class QueryOptimizer:
    """Advanced query optimization with caching and analysis"""

    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.query_patterns: Dict[str, List[QueryMetrics]] = defaultdict(list)
        self.index_suggestions: Dict[str, List[str]] = defaultdict(list)
        self.performance_threshold = 1.0  # seconds

        # Metrics
        self.query_cache_hits = prom.Counter('query_cache_hits_total', 'Query cache hits')
        self.query_cache_misses = prom.Counter('query_cache_misses_total', 'Query cache misses')
        self.slow_queries = prom.Counter('slow_queries_total', 'Slow queries', ['database', 'table'])

    async def optimize_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Optimize SQL query"""
        query_hash = self._hash_query(query, params)

        # Check cache first
        if query_hash in self.query_cache:
            self.query_cache_hits.inc()
            return self.query_cache[query_hash]

        self.query_cache_misses.inc()

        # Apply optimizations
        optimized_query = await self._apply_optimizations(query, params)

        # Cache result
        self.query_cache[query_hash] = optimized_query

        return optimized_query

    async def _apply_optimizations(self, query: str, params: Dict[str, Any] = None) -> str:
        """Apply various query optimizations"""
        optimized = query

        # Add appropriate hints based on query patterns
        if self._should_use_parallel_hint(query):
            optimized = f"/*+ PARALLEL */ {optimized}"

        # Add index hints if available
        table_name = self._extract_table_name(query)
        if table_name and table_name in self.index_suggestions:
            indexes = self.index_suggestions[table_name]
            if indexes:
                index_hint = f"USE INDEX ({', '.join(indexes)})"
                optimized = optimized.replace(f"FROM {table_name}", f"FROM {table_name} {index_hint}")

        return optimized

    def _hash_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Create hash for query with parameters"""
        query_data = {"query": query, "params": params or {}}
        query_str = json.dumps(query_data, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()

    def _should_use_parallel_hint(self, query: str) -> bool:
        """Determine if query should use parallel execution"""
        # Simple heuristic: large scans and joins benefit from parallelism
        query_lower = query.lower()
        return ("join" in query_lower and
                ("large" in query_lower or "scan" in query_lower))

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract main table name from query"""
        # Simple table extraction - could be enhanced with proper SQL parsing
        query_lower = query.lower()
        if "from" in query_lower:
            from_part = query_lower.split("from")[1].split()[0]
            return from_part.strip("`\"[]")
        return None

    async def analyze_query_performance(self, metrics: QueryMetrics):
        """Analyze query performance and suggest optimizations"""
        if metrics.execution_time > self.performance_threshold:
            self.slow_queries.labels(
                database=metrics.database,
                table=metrics.table
            ).inc()

            # Analyze query pattern
            self.query_patterns[metrics.query_hash].append(metrics)

            # Suggest indexes based on patterns
            await self._suggest_indexes(metrics)

    async def _suggest_indexes(self, metrics: QueryMetrics):
        """Suggest indexes based on query analysis"""
        # This would analyze query patterns and suggest optimal indexes
        # Simplified implementation
        if "WHERE" in metrics.query_hash and metrics.execution_time > 2.0:
            table = metrics.table
            if table not in self.index_suggestions:
                self.index_suggestions[table] = []

            # Add generic index suggestion
            suggestion = f"idx_{table}_performance"
            if suggestion not in self.index_suggestions[table]:
                self.index_suggestions[table].append(suggestion)

class DatabaseCluster:
    """Database cluster with sharding and replication"""

    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.nodes: Dict[str, DatabaseNode] = {}
        self.pools: Dict[str, ConnectionPool] = {}
        self.shard_router: Optional[ShardRouter] = None
        self.query_optimizer = QueryOptimizer()
        self.health_checker = HealthChecker()
        self.load_balancer = LoadBalancer()

        # Metrics
        self.cluster_queries = prom.Counter('cluster_queries_total', 'Cluster queries', ['status'])
        self.cluster_latency = prom.Histogram('cluster_query_latency_seconds', 'Query latency')

    async def add_node(self, node: DatabaseNode, is_primary: bool = False):
        """Add database node to cluster"""
        if is_primary:
            node.role = ReplicationRole.PRIMARY

        self.nodes[node.node_id] = node

        # Create connection pool
        pool = ConnectionPool(node)
        await pool.initialize()
        self.pools[node.node_id] = pool

        logger.info("Database node added",
                   cluster_id=self.cluster_id,
                   node_id=node.node_id,
                   role=node.role.value)

    async def configure_sharding(self, config: ShardingConfig):
        """Configure sharding for the cluster"""
        self.shard_router = ShardRouter(config)

        # Assign shards to nodes
        available_nodes = list(self.nodes.keys())
        for i in range(config.shard_count):
            shard_id = f"shard_{i}"
            node_id = available_nodes[i % len(available_nodes)]
            self.shard_router.add_shard(shard_id, self.nodes[node_id])

        logger.info("Sharding configured",
                   cluster_id=self.cluster_id,
                   strategy=config.strategy.value,
                   shard_count=config.shard_count)

    async def execute_query(self, query: str, params: Dict[str, Any] = None,
                          shard_key: Any = None, read_only: bool = False) -> Any:
        """Execute query with routing and optimization"""
        start_time = time.time()

        try:
            # Optimize query
            optimized_query = await self.query_optimizer.optimize_query(query, params)

            # Route to appropriate shard
            if shard_key and self.shard_router:
                shard_id = self.shard_router.get_shard(shard_key)
                node = self._get_node_for_shard(shard_id, read_only)
            else:
                node = await self.load_balancer.get_node(self.nodes, read_only)

            if not node:
                raise Exception("No available database nodes")

            # Execute query
            pool = self.pools[node.node_id]
            connection = await pool.acquire()

            try:
                result = await self._execute_on_connection(connection, optimized_query, params)

                # Record metrics
                execution_time = time.time() - start_time
                self.cluster_queries.labels(status='success').inc()
                self.cluster_latency.observe(execution_time)

                # Analyze performance
                await self.query_optimizer.analyze_query_performance(
                    QueryMetrics(
                        query_id=str(uuid.uuid4()),
                        query_hash=self.query_optimizer._hash_query(query, params),
                        execution_time=execution_time,
                        rows_affected=len(result) if isinstance(result, list) else 0,
                        database=node.database,
                        table=self.query_optimizer._extract_table_name(query),
                        timestamp=datetime.utcnow(),
                        success=True
                    )
                )

                return result

            finally:
                await pool.release(connection)

        except Exception as e:
            execution_time = time.time() - start_time
            self.cluster_queries.labels(status='error').inc()
            self.cluster_latency.observe(execution_time)

            logger.error("Query execution failed",
                        cluster_id=self.cluster_id,
                        query=query,
                        error=str(e))
            raise

    async def _execute_on_connection(self, connection, query: str, params: Dict[str, Any] = None):
        """Execute query on specific connection"""
        if isinstance(connection, asyncpg.Connection):
            if params:
                return await connection.fetch(query, *params.values())
            else:
                return await connection.fetch(query)
        elif isinstance(connection, aiomysql.Connection):
            async with connection.cursor() as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                return await cursor.fetchall()
        elif hasattr(connection, 'find'):  # MongoDB
            collection = connection  # This would need proper collection handling
            return await collection.find(params or {}).to_list(None)
        else:
            raise ValueError(f"Unsupported connection type: {type(connection)}")

    def _get_node_for_shard(self, shard_id: str, read_only: bool) -> Optional[DatabaseNode]:
        """Get database node for shard"""
        # This would map shard to specific node
        # Simplified implementation
        available_nodes = [node for node in self.nodes.values()
                          if node.role == ReplicationRole.PRIMARY or read_only]

        return available_nodes[0] if available_nodes else None

class HealthChecker:
    """Database health checking and monitoring"""

    def __init__(self):
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.check_interval = 30.0

    async def start_monitoring(self, nodes: Dict[str, DatabaseNode]):
        """Start health monitoring for nodes"""
        while True:
            try:
                for node_id, node in nodes.items():
                    await self._check_node_health(node_id, node)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(10)

    async def _check_node_health(self, node_id: str, node: DatabaseNode):
        """Check health of individual node"""
        start_time = time.time()
        is_healthy = False
        error_message = None

        try:
            # Simple health check query
            if node.db_type == DatabaseType.POSTGRESQL:
                conn = await asyncpg.connect(
                    host=node.host, port=node.port,
                    database=node.database,
                    user=node.username, password=node.password
                )
                await conn.execute("SELECT 1")
                await conn.close()
                is_healthy = True
            elif node.db_type == DatabaseType.MYSQL:
                conn = await aiomysql.connect(
                    host=node.host, port=node.port,
                    db=node.database,
                    user=node.username, password=node.password
                )
                await conn.ping()
                conn.close()
                is_healthy = True

            response_time = time.time() - start_time

        except Exception as e:
            error_message = str(e)
            response_time = time.time() - start_time

        self.health_status[node_id] = {
            'healthy': is_healthy,
            'response_time': response_time,
            'last_check': datetime.utcnow(),
            'error': error_message
        }

        node.health_status = 'healthy' if is_healthy else 'unhealthy'
        node.last_health_check = datetime.utcnow()

class LoadBalancer:
    """Database load balancer with multiple strategies"""

    def __init__(self):
        self.strategy = "least_connections"

    async def get_node(self, nodes: Dict[str, DatabaseNode], read_only: bool = False) -> Optional[DatabaseNode]:
        """Get best node for query"""
        # Filter by role and health
        available_nodes = [node for node in nodes.values()
                          if ((node.role == ReplicationRole.PRIMARY) or
                              (read_only and node.role == ReplicationRole.SECONDARY))
                          and node.health_status == 'healthy']

        if not available_nodes:
            return None

        if self.strategy == "least_connections":
            return self._least_connections(available_nodes)
        elif self.strategy == "round_robin":
            return self._round_robin(available_nodes)
        elif self.strategy == "weighted":
            return self._weighted(available_nodes)
        else:
            return available_nodes[0]

    def _least_connections(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """Select node with least connections"""
        # This would require tracking active connections per node
        # Simplified implementation
        return min(nodes, key=lambda n: n.weight)

    def _round_robin(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """Round-robin selection"""
        # This would require maintaining round-robin state
        return nodes[0]  # Simplified

    def _weighted(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """Weighted selection"""
        total_weight = sum(node.weight for node in nodes)
        if total_weight == 0:
            return nodes[0]

        import random
        r = random.uniform(0, total_weight)
        current_weight = 0

        for node in nodes:
            current_weight += node.weight
            if r <= current_weight:
                return node

        return nodes[-1]

class MigrationManager:
    """Database migration and schema evolution manager"""

    def __init__(self):
        self.migrations: List[Dict[str, Any]] = []
        self.applied_migrations: Set[str] = set()

    async def add_migration(self, migration_id: str, up_script: str,
                          down_script: str, dependencies: List[str] = None):
        """Add migration to manager"""
        migration = {
            'id': migration_id,
            'up_script': up_script,
            'down_script': down_script,
            'dependencies': dependencies or [],
            'created_at': datetime.utcnow()
        }
        self.migrations.append(migration)

    async def migrate_up(self, cluster: DatabaseCluster):
        """Apply pending migrations"""
        # Sort migrations by dependencies
        sorted_migrations = self._sort_migrations_by_dependencies()

        for migration in sorted_migrations:
            if migration['id'] not in self.applied_migrations:
                await self._apply_migration(cluster, migration, 'up')

    async def migrate_down(self, cluster: DatabaseCluster, target_version: str):
        """Rollback to target version"""
        # Find migrations to rollback
        to_rollback = [m for m in reversed(self.migrations)
                      if m['id'] in self.applied_migrations and
                      m['id'] > target_version]

        for migration in to_rollback:
            await self._apply_migration(cluster, migration, 'down')

    async def _apply_migration(self, cluster: DatabaseCluster,
                             migration: Dict[str, Any], direction: str):
        """Apply single migration"""
        script = migration[f'{direction}_script']

        # Execute migration on primary node
        primary_nodes = [node for node in cluster.nodes.values()
                        if node.role == ReplicationRole.PRIMARY]

        if primary_nodes:
            await cluster.execute_query(script, shard_key="migration")
            self.applied_migrations.add(migration['id'])
            logger.info("Migration applied",
                       migration_id=migration['id'],
                       direction=direction)

    def _sort_migrations_by_dependencies(self) -> List[Dict[str, Any]]:
        """Sort migrations by dependencies"""
        # Topological sort based on dependencies
        # Simplified implementation
        return sorted(self.migrations, key=lambda m: len(m['dependencies']))

# Initialize database patterns system
async def initialize_database_cluster(cluster_id: str,
                                    nodes: List[DatabaseNode]) -> DatabaseCluster:
    """Initialize complete database cluster architecture"""

    cluster = DatabaseCluster(cluster_id)

    # Add nodes to cluster
    for i, node_config in enumerate(nodes):
        is_primary = (i == 0)  # First node is primary
        await cluster.add_node(node_config, is_primary=is_primary)

    # Start health monitoring
    health_checker = HealthChecker()
    asyncio.create_task(health_checker.start_monitoring(cluster.nodes))

    logger.info("Database cluster initialized",
               cluster_id=cluster_id,
               node_count=len(nodes))

    return cluster

# Export main classes and functions
__all__ = [
    'DatabaseCluster',
    'ConnectionPool',
    'ShardRouter',
    'QueryOptimizer',
    'HealthChecker',
    'LoadBalancer',
    'MigrationManager',
    'DatabaseNode',
    'ShardingConfig',
    'QueryMetrics',
    'DatabaseType',
    'ShardingStrategy',
    'ReplicationRole',
    'initialize_database_cluster'
]