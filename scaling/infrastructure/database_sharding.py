#!/usr/bin/env python3
"""
Advanced Database Sharding and Optimization System
Multi-database sharding, connection pooling, query optimization, and caching
"""

import asyncio
import json
import logging
import hashlib
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
import asyncpg
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2 import pool
import pymongo
import cassandra.cluster
import clickhouse_driver
from collections import defaultdict
import statistics
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShardStrategy(Enum):
    HASH = "hash"
    RANGE = "range"
    DIRECTORY = "directory"
    GEOGRAPHIC = "geographic"
    CONSISTENT_HASH = "consistent_hash"
    TIME_SERIES = "time_series"

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    CASSANDRA = "cassandra"
    CLICKHOUSE = "clickhouse"
    REDIS = "redis"

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"

@dataclass
class DatabaseShard:
    """Database shard configuration"""
    shard_id: str
    shard_name: str
    host: str
    port: int
    database: str
    username: str
    password: str
    database_type: DatabaseType
    region: str
    capacity: float  # Current capacity usage (0-1)
    max_connections: int
    current_connections: int
    read_weight: float
    write_weight: float
    is_primary: bool
    is_active: bool
    last_health_check: datetime
    connection_string: str

@dataclass
class QueryMetrics:
    """Query execution metrics"""
    query_id: str
    query_type: QueryType
    shard_id: str
    execution_time: float
    rows_affected: int
    bytes_transferred: int
    timestamp: datetime
    success: bool
    error_message: Optional[str]
    cache_hit: bool

@dataclass
class ShardingRule:
    """Database sharding rule"""
    table_name: str
    shard_key: str
    strategy: ShardStrategy
    shard_count: int
    replication_factor: int
    shard_mapping: Dict[str, List[str]]  # key -> shard_ids

class ConnectionPool:
    """Advanced database connection pool"""

    def __init__(self, shard: DatabaseShard, pool_size: int = 20):
        self.shard = shard
        self.pool_size = pool_size
        self.active_connections = 0
        self.pool = asyncio.Queue(maxsize=pool_size)
        self.semaphore = asyncio.Semaphore(pool_size)
        self.connection_cache = {}

    async def initialize(self):
        """Initialize connection pool"""
        try:
            if self.shard.database_type == DatabaseType.POSTGRESQL:
                await self._init_postgresql_pool()
            elif self.shard.database_type == DatabaseType.MONGODB:
                await self._init_mongodb_pool()
            elif self.shard.database_type == DatabaseType.REDIS:
                await self._init_redis_pool()
            # Add other database types as needed

            logger.info(f"Initialized connection pool for {self.shard.shard_id}")

        except Exception as e:
            logger.error(f"Failed to initialize pool for {self.shard.shard_id}: {e}")
            raise

    async def _init_postgresql_pool(self):
        """Initialize PostgreSQL connection pool"""
        for _ in range(self.pool_size):
            conn = await asyncpg.connect(
                host=self.shard.host,
                port=self.shard.port,
                database=self.shard.database,
                user=self.shard.username,
                password=self.shard.password,
                min_size=5,
                max_size=self.pool_size
            )
            await self.pool.put(conn)

    async def _init_mongodb_pool(self):
        """Initialize MongoDB connection pool"""
        client = pymongo.MongoClient(
            f"mongodb://{self.shard.username}:{self.shard.password}@{self.shard.host}:{self.shard.port}/{self.shard.database}",
            maxPoolSize=self.pool_size
        )
        await self.pool.put(client)

    async def _init_redis_pool(self):
        """Initialize Redis connection pool"""
        pool = redis.ConnectionPool(
            host=self.shard.host,
            port=self.shard.port,
            password=self.shard.password,
            db=int(self.shard.database),
            max_connections=self.pool_size
        )
        redis_client = redis.Redis(connection_pool=pool)
        await self.pool.put(redis_client)

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        async with self.semaphore:
            try:
                conn = await self.pool.get()
                self.active_connections += 1
                yield conn
            finally:
                await self.pool.put(conn)
                self.active_connections -= 1

    async def close(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            conn = await self.pool.get()
            if hasattr(conn, 'close'):
                await conn.close()

class QueryOptimizer:
    """Query optimization and analysis"""

    def __init__(self):
        self.query_stats = defaultdict(list)
        self.query_plans = {}
        self.optimization_rules = {
            'add_indexes': self._suggest_indexes,
            'optimize_joins': self._optimize_joins,
            'rewrite_subqueries': self._rewrite_subqueries,
            'partition_hints': self._add_partition_hints
        }

    def analyze_query(self, query: str, query_type: QueryType) -> Dict[str, Any]:
        """Analyze a query for optimization opportunities"""
        analysis = {
            'query': query,
            'query_type': query_type.value,
            'complexity': self._calculate_complexity(query),
            'estimated_cost': self._estimate_cost(query),
            'optimizations': [],
            'indexes_needed': [],
            'warnings': []
        }

        # Apply optimization rules
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                suggestions = rule_func(query)
                if suggestions:
                    analysis['optimizations'].extend(suggestions)
            except Exception as e:
                logger.warning(f"Error applying optimization rule {rule_name}: {e}")

        return analysis

    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity score"""
        complexity = 0
        query_upper = query.upper()

        # Count complex operations
        complexity += query_upper.count(' JOIN ') * 2
        complexity += query_upper.count(' SUBQUERY ') * 3
        complexity += query_upper.count(' UNION ') * 2
        complexity += query_upper.count(' GROUP BY ') * 1
        complexity += query_upper.count(' ORDER BY ') * 1
        complexity += query_upper.count(' HAVING ') * 2
        complexity += query_upper.count(' CASE ') * 1

        # Check for window functions
        if ' OVER (' in query_upper:
            complexity += 3

        return complexity

    def _estimate_cost(self, query: str) -> float:
        """Estimate query execution cost"""
        # Simplified cost estimation
        cost = self._calculate_complexity(query) * 10.0

        # Add cost for table scans (estimated)
        if ' WHERE ' not in query.upper():
            cost *= 5.0

        return cost

    def _suggest_indexes(self, query: str) -> List[str]:
        """Suggest indexes for query optimization"""
        suggestions = []
        query_upper = query.upper()

        # Find WHERE clause columns
        if ' WHERE ' in query_upper:
            where_clause = query_upper.split(' WHERE ')[1].split(' GROUP BY ')[0].split(' ORDER BY ')[0]
            # Simple regex to find column references
            import re
            columns = re.findall(r'(\w+)\s*=', where_clause)
            for col in columns:
                suggestions.append(f"Consider adding index on column: {col}")

        return suggestions

    def _optimize_joins(self, query: str) -> List[str]:
        """Suggest join optimizations"""
        suggestions = []
        query_upper = query.upper()

        if ' JOIN ' in query_upper:
            join_count = query_upper.count(' JOIN ')
            if join_count > 3:
                suggestions.append("Consider breaking down complex joins into multiple queries")

        return suggestions

    def _rewrite_subqueries(self, query: str) -> List[str]:
        """Suggest subquery rewrites"""
        suggestions = []

        if 'SELECT' in query.upper() and ' FROM (' in query:
            suggestions.append("Consider rewriting subqueries as JOINs for better performance")

        return suggestions

    def _add_partition_hints(self, query: str) -> List[str]:
        """Add partitioning hints for time-series data"""
        suggestions = []

        if 'created_at' in query.lower() or 'timestamp' in query.lower():
            suggestions.append("Consider adding time-based partitioning for this table")

        return suggestions

    def record_query_execution(self, metrics: QueryMetrics):
        """Record query execution metrics"""
        self.query_stats[metrics.query_type.value].append({
            'execution_time': metrics.execution_time,
            'rows_affected': metrics.rows_affected,
            'success': metrics.success,
            'cache_hit': metrics.cache_hit,
            'timestamp': metrics.timestamp
        })

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        stats = {}

        for query_type, executions in self.query_stats.items():
            if executions:
                execution_times = [e['execution_time'] for e in executions if e['success']]
                success_rate = sum(1 for e in executions if e['success']) / len(executions)
                cache_hit_rate = sum(1 for e in executions if e['cache_hit']) / len(executions)

                stats[query_type] = {
                    'total_executions': len(executions),
                    'success_rate': success_rate * 100,
                    'cache_hit_rate': cache_hit_rate * 100,
                    'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
                    'median_execution_time': statistics.median(execution_times) if execution_times else 0,
                    'max_execution_time': max(execution_times) if execution_times else 0
                }

        return stats

class ConsistentHashRing:
    """Consistent hashing ring for shard distribution"""

    def __init__(self, replicas: int = 150):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []

    def add_shard(self, shard_id: str):
        """Add a shard to the hash ring"""
        for i in range(self.replicas):
            key = self._hash(f"{shard_id}:{i}")
            self.ring[key] = shard_id
        self.sorted_keys = sorted(self.ring.keys())

    def remove_shard(self, shard_id: str):
        """Remove a shard from the hash ring"""
        for i in range(self.replicas):
            key = self._hash(f"{shard_id}:{i}")
            if key in self.ring:
                del self.ring[key]
        self.sorted_keys = sorted(self.ring.keys())

    def get_shard(self, key: str) -> str:
        """Get the shard for a given key"""
        if not self.ring:
            raise ValueError("No shards available")

        hash_key = self._hash(key)

        # Find the first shard with key >= hash_key
        idx = bisect.bisect_right(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0

        return self.ring[self.sorted_keys[idx]]

    def _hash(self, key: str) -> int:
        """Hash function for consistent hashing"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

import bisect

class DatabaseShardingSystem:
    """Main database sharding and optimization system"""

    def __init__(self, config_path: str = "config/sharding_config.json"):
        self.config = self._load_config(config_path)
        self.shards = self._load_shards()
        self.sharding_rules = self._load_sharding_rules()
        self.connection_pools = {}
        self.query_optimizer = QueryOptimizer()
        self.consistent_hash = ConsistentHashRing()
        self.redis_cache = redis.Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            decode_responses=True
        )

        # Initialize connection pools
        asyncio.create_task(self._initialize_pools())

        # Setup consistent hashing
        self._setup_consistent_hashing()

        # Start background tasks
        asyncio.create_task(self._monitor_shard_health())
        asyncio.create_task(self._rebalance_shards())

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'redis_host': 'localhost',
                'redis_port': 6379,
                'health_check_interval': 60,
                'rebalance_interval': 300,
                'cache_ttl': 300,
                'max_query_time': 30.0
            }

    def _load_shards(self) -> List[DatabaseShard]:
        """Load database shard configurations"""
        shards = []

        # Default shard configurations
        default_shards = [
            {
                'shard_id': 'shard_0',
                'shard_name': 'US-East-Primary',
                'host': 'localhost',
                'port': 5432,
                'database': 'dmlogn8n_shard_0',
                'username': 'postgres',
                'password': 'password',
                'database_type': 'postgresql',
                'region': 'us-east-1',
                'capacity': 0.3,
                'max_connections': 100,
                'current_connections': 0,
                'read_weight': 1.0,
                'write_weight': 1.0,
                'is_primary': True,
                'is_active': True,
                'last_health_check': datetime.utcnow(),
                'connection_string': ''
            },
            {
                'shard_id': 'shard_1',
                'shard_name': 'US-West-Primary',
                'host': 'localhost',
                'port': 5433,
                'database': 'dmlogn8n_shard_1',
                'username': 'postgres',
                'password': 'password',
                'database_type': 'postgresql',
                'region': 'us-west-2',
                'capacity': 0.2,
                'max_connections': 100,
                'current_connections': 0,
                'read_weight': 1.0,
                'write_weight': 1.0,
                'is_primary': False,
                'is_active': True,
                'last_health_check': datetime.utcnow(),
                'connection_string': ''
            }
        ]

        for shard_config in default_shards:
            shard = DatabaseShard(**shard_config)
            shards.append(shard)

        return shards

    def _load_sharding_rules(self) -> List[ShardingRule]:
        """Load sharding rules"""
        rules = []

        default_rules = [
            {
                'table_name': 'workflows',
                'shard_key': 'user_id',
                'strategy': ShardStrategy.HASH,
                'shard_count': 2,
                'replication_factor': 2,
                'shard_mapping': {}
            },
            {
                'table_name': 'workflow_executions',
                'shard_key': 'workflow_id',
                'strategy': ShardStrategy.HASH,
                'shard_count': 2,
                'replication_factor': 2,
                'shard_mapping': {}
            },
            {
                'table_name': 'users',
                'shard_key': 'id',
                'strategy': ShardStrategy.CONSISTENT_HASH,
                'shard_count': 2,
                'replication_factor': 2,
                'shard_mapping': {}
            }
        ]

        for rule_config in default_rules:
            rule = ShardingRule(**rule_config)
            rules.append(rule)

        return rules

    async def _initialize_pools(self):
        """Initialize connection pools for all shards"""
        for shard in self.shards:
            if shard.is_active:
                try:
                    pool = ConnectionPool(shard)
                    await pool.initialize()
                    self.connection_pools[shard.shard_id] = pool
                    logger.info(f"Initialized connection pool for {shard.shard_id}")
                except Exception as e:
                    logger.error(f"Failed to initialize pool for {shard.shard_id}: {e}")

    def _setup_consistent_hashing(self):
        """Setup consistent hashing ring"""
        for shard in self.shards:
            if shard.is_active:
                self.consistent_hash.add_shard(shard.shard_id)

    def _get_sharding_rule(self, table_name: str) -> Optional[ShardingRule]:
        """Get sharding rule for a table"""
        for rule in self.sharding_rules:
            if rule.table_name == table_name:
                return rule
        return None

    def _determine_shard(self, table_name: str, shard_key_value: Any) -> List[str]:
        """Determine which shard(s) to use for a query"""
        rule = self._get_sharding_rule(table_name)
        if not rule:
            # No sharding rule, use primary shard
            return [s.shard_id for s in self.shards if s.is_primary]

        active_shards = [s.shard_id for s in self.shards if s.is_active]

        if rule.strategy == ShardStrategy.HASH:
            hash_value = hash(str(shard_key_value))
            shard_index = hash_value % rule.shard_count
            return [active_shards[shard_index]]

        elif rule.strategy == ShardStrategy.CONSISTENT_HASH:
            shard_id = self.consistent_hash.get_shard(str(shard_key_value))
            return [shard_id]

        elif rule.strategy == ShardStrategy.RANGE:
            # Implement range-based sharding logic
            return active_shards

        elif rule.strategy == ShardStrategy.DIRECTORY:
            # Use directory-based mapping
            return rule.shard_mapping.get(str(shard_key_value), active_shards)

        else:
            return active_shards

    async def execute_query(self, query: str, params: Dict = None,
                          table_name: str = None, shard_key_value: Any = None) -> Dict[str, Any]:
        """Execute a query on the appropriate shard(s)"""
        query_start = time.time()
        query_id = hashlib.md5(f"{query}{params}{time.time()}".encode()).hexdigest()[:16]

        # Determine query type
        query_type = self._get_query_type(query)

        # Check cache first for SELECT queries
        cache_key = None
        if query_type == QueryType.SELECT:
            cache_key = f"query_cache:{query_id}"
            cached_result = self.redis_cache.get(cache_key)
            if cached_result:
                metrics = QueryMetrics(
                    query_id=query_id,
                    query_type=query_type,
                    shard_id="cache",
                    execution_time=time.time() - query_start,
                    rows_affected=0,
                    bytes_transferred=len(cached_result),
                    timestamp=datetime.utcnow(),
                    success=True,
                    error_message=None,
                    cache_hit=True
                )
                self.query_optimizer.record_query_execution(metrics)
                return json.loads(cached_result)

        # Determine target shards
        target_shards = self._determine_shard(table_name, shard_key_value) if table_name else None

        if not target_shards:
            # No specific shard, query all active shards
            target_shards = [s.shard_id for s in self.shards if s.is_active]

        # Execute query on target shards
        results = []
        errors = []

        for shard_id in target_shards:
            try:
                pool = self.connection_pools.get(shard_id)
                if not pool:
                    errors.append(f"No connection pool for shard {shard_id}")
                    continue

                async with pool.get_connection() as conn:
                    if self.shards[0].database_type == DatabaseType.POSTGRESQL:
                        result = await self._execute_postgresql_query(conn, query, params)
                    else:
                        errors.append(f"Unsupported database type for shard {shard_id}")
                        continue

                    results.append(result)

            except Exception as e:
                errors.append(f"Error on shard {shard_id}: {str(e)}")

        # Combine results
        if results:
            if len(results) == 1:
                final_result = results[0]
            else:
                # Merge results from multiple shards
                final_result = self._merge_shard_results(results, query_type)

            # Cache SELECT results
            if query_type == QueryType.SELECT and cache_key:
                self.redis_cache.setex(cache_key, self.config['cache_ttl'], json.dumps(final_result))

            execution_time = time.time() - query_start
            metrics = QueryMetrics(
                query_id=query_id,
                query_type=query_type,
                shard_id=",".join(target_shards),
                execution_time=execution_time,
                rows_affected=len(final_result.get('data', [])) if 'data' in final_result else 0,
                bytes_transferred=len(json.dumps(final_result)),
                timestamp=datetime.utcnow(),
                success=not errors,
                error_message="; ".join(errors) if errors else None,
                cache_hit=False
            )
            self.query_optimizer.record_query_execution(metrics)

            return {
                'success': True,
                'data': final_result,
                'shards_queried': target_shards,
                'execution_time': execution_time,
                'rows_returned': len(final_result.get('data', [])) if 'data' in final_result else 0
            }
        else:
            return {
                'success': False,
                'error': '; '.join(errors),
                'shards_queried': target_shards,
                'execution_time': time.time() - query_start
            }

    def _get_query_type(self, query: str) -> QueryType:
        """Determine query type from SQL"""
        query_upper = query.strip().upper()

        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif 'GROUP BY' in query_upper or 'COUNT(' in query_upper or 'SUM(' in query_upper:
            return QueryType.AGGREGATE
        else:
            return QueryType.SELECT

    async def _execute_postgresql_query(self, conn, query: str, params: Dict = None) -> Dict:
        """Execute PostgreSQL query"""
        if params:
            result = await conn.fetch(query, *params.values())
        else:
            result = await conn.fetch(query)

        # Convert to dict format
        data = [dict(row) for row in result]

        return {
            'data': data,
            'row_count': len(data)
        }

    def _merge_shard_results(self, results: List[Dict], query_type: QueryType) -> Dict:
        """Merge results from multiple shards"""
        if query_type == QueryType.SELECT:
            # Combine data from all shards
            all_data = []
            total_rows = 0

            for result in results:
                if 'data' in result:
                    all_data.extend(result['data'])
                total_rows += result.get('row_count', 0)

            # Remove duplicates (if any)
            seen = set()
            unique_data = []
            for item in all_data:
                # Create a hash key from the item
                item_key = tuple(sorted(item.items()))
                if item_key not in seen:
                    seen.add(item_key)
                    unique_data.append(item)

            return {
                'data': unique_data,
                'row_count': len(unique_data)
            }

        elif query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]:
            # Sum affected rows
            total_affected = sum(result.get('affected_rows', 0) for result in results)
            return {
                'affected_rows': total_affected,
                'success': True
            }

        elif query_type == QueryType.AGGREGATE:
            # Merge aggregation results
            # This is complex and depends on the specific aggregation
            # For now, return the first result
            return results[0] if results else {}

        return results[0] if results else {}

    async def _monitor_shard_health(self):
        """Monitor health of all shards"""
        while True:
            try:
                for shard in self.shards:
                    if not shard.is_active:
                        continue

                    try:
                        pool = self.connection_pools.get(shard.shard_id)
                        if pool:
                            async with pool.get_connection() as conn:
                                # Simple health check
                                start_time = time.time()
                                if shard.database_type == DatabaseType.POSTGRESQL:
                                    await conn.fetchval("SELECT 1")

                                response_time = time.time() - start_time
                                shard.last_health_check = datetime.utcnow()

                                # Update capacity based on response time and connections
                                connection_ratio = pool.active_connections / pool.pool_size
                                shard.capacity = min(1.0, connection_ratio + (response_time / 10.0))
                                shard.current_connections = pool.active_connections

                    except Exception as e:
                        logger.warning(f"Health check failed for {shard.shard_id}: {e}")
                        shard.capacity = 1.0  # Mark as overloaded
                        shard.last_health_check = datetime.utcnow()

                await asyncio.sleep(self.config['health_check_interval'])

            except Exception as e:
                logger.error(f"Error in shard health monitoring: {e}")
                await asyncio.sleep(30)

    async def _rebalance_shards(self):
        """Rebalance load across shards"""
        while True:
            try:
                # Calculate average capacity
                active_shards = [s for s in self.shards if s.is_active]
                if not active_shards:
                    await asyncio.sleep(60)
                    continue

                avg_capacity = statistics.mean(s.capacity for s in active_shards)
                overloaded_shards = [s for s in active_shards if s.capacity > 0.8]
                underloaded_shards = [s for s in active_shards if s.capacity < 0.3]

                if overloaded_shards and underloaded_shards:
                    logger.info(f"Detected load imbalance - {len(overloaded_shards)} overloaded, {len(underloaded_shards)} underloaded")
                    # TODO: Implement data migration logic

                await asyncio.sleep(self.config['rebalance_interval'])

            except Exception as e:
                logger.error(f"Error in shard rebalancing: {e}")
                await asyncio.sleep(60)

    async def add_shard(self, shard_config: Dict) -> bool:
        """Add a new shard to the system"""
        try:
            shard = DatabaseShard(**shard_config)
            self.shards.append(shard)

            # Initialize connection pool
            pool = ConnectionPool(shard)
            await pool.initialize()
            self.connection_pools[shard.shard_id] = pool

            # Add to consistent hash ring
            self.consistent_hash.add_shard(shard.shard_id)

            logger.info(f"Added new shard: {shard.shard_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add shard: {e}")
            return False

    async def remove_shard(self, shard_id: str) -> bool:
        """Remove a shard from the system"""
        try:
            shard = next((s for s in self.shards if s.shard_id == shard_id), None)
            if not shard:
                return False

            # Drain connections
            pool = self.connection_pools.get(shard_id)
            if pool:
                await pool.close()
                del self.connection_pools[shard_id]

            # Remove from consistent hash ring
            self.consistent_hash.remove_shard(shard_id)

            # Mark as inactive
            shard.is_active = False
            self.shards.remove(shard)

            logger.info(f"Removed shard: {shard_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove shard: {e}")
            return False

    async def get_sharding_stats(self) -> Dict[str, Any]:
        """Get sharding system statistics"""
        stats = {
            'total_shards': len(self.shards),
            'active_shards': len([s for s in self.shards if s.is_active]),
            'primary_shards': len([s for s in self.shards if s.is_primary]),
            'shards': [],
            'connection_pools': {},
            'query_performance': self.query_optimizer.get_performance_stats()
        }

        for shard in self.shards:
            shard_stats = {
                'id': shard.shard_id,
                'name': shard.shard_name,
                'region': shard.region,
                'database_type': shard.database_type.value,
                'capacity': shard.capacity,
                'current_connections': shard.current_connections,
                'max_connections': shard.max_connections,
                'is_active': shard.is_active,
                'is_primary': shard.is_primary,
                'last_health_check': shard.last_health_check.isoformat()
            }
            stats['shards'].append(shard_stats)

        for shard_id, pool in self.connection_pools.items():
            stats['connection_pools'][shard_id] = {
                'active_connections': pool.active_connections,
                'pool_size': pool.pool_size,
                'utilization': (pool.active_connections / pool.pool_size) * 100
            }

        return stats

    async def optimize_query(self, query: str, table_name: str = None) -> Dict[str, Any]:
        """Analyze and optimize a query"""
        query_type = self._get_query_type(query)
        analysis = self.query_optimizer.analyze_query(query, query_type)

        # Add sharding-specific recommendations
        if table_name:
            rule = self._get_sharding_rule(table_name)
            if rule:
                analysis['sharding_strategy'] = rule.strategy.value
                analysis['shard_key'] = rule.shard_key
                analysis['shard_count'] = rule.shard_count

        return analysis

async def main():
    """Main entry point"""
    sharding_system = DatabaseShardingSystem()

    # Example usage
    while True:
        try:
            # Simulate some queries
            query = "SELECT * FROM workflows WHERE user_id = $1"
            result = await sharding_system.execute_query(query, {'user_id': '12345'}, 'workflows', '12345')
            print(f"Query result: {result['success']}, Rows: {result.get('rows_returned', 0)}")

            await asyncio.sleep(5)

        except KeyboardInterrupt:
            logger.info("Shutting down sharding system")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())