#!/usr/bin/env python3
"""
Advanced Database Optimizer for DMLogn8n Platform
Query optimization, indexing strategies, connection pooling, and performance tuning
"""

import asyncio
import json
import logging
import re
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import hashlib
import numpy as np
import pandas as pd

# Database libraries
try:
    import asyncpg
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import pymongo
    import motor.motor_asyncio
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import redis
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"
    MYSQL = "mysql"
    SQLITE = "sqlite"

class QueryType(Enum):
    """Query operation types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    INDEX = "INDEX"

@dataclass
class QueryMetrics:
    """Query execution metrics"""
    query_hash: str
    query_type: QueryType
    execution_time: float
    rows_returned: int
    rows_affected: int
    cpu_time: float
    io_time: float
    memory_usage: int
    index_usage: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    database: str = ""
    table: str = ""
    explain_plan: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IndexRecommendation:
    """Index optimization recommendation"""
    table: str
    columns: List[str]
    index_type: str
    estimated_impact: float
    current_size_mb: float
    estimated_size_mb: float
    priority: str
    reason: str

@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    ssl_mode: str = "prefer"
    connection_timeout: int = 10
    command_timeout: int = 30

class DatabaseOptimizer:
    """Advanced database optimization and performance tuning system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.connections = {}
        self.connection_pools = {}
        self.query_history = deque(maxlen=self.config.get('history_size', 10000))
        self.index_recommendations = {}
        self.query_patterns = defaultdict(list)
        self.slow_queries = deque(maxlen=1000)

        # Optimization settings
        self.auto_indexing = self.config.get('auto_indexing', True)
        self.query_caching = self.config.get('query_caching', True)
        self.connection_pooling = self.config.get('connection_pooling', True)
        self.auto_explain = self.config.get('auto_explain', True)

        # Performance thresholds
        self.slow_query_threshold = self.config.get('slow_query_threshold', 1.0)
        self.high_impact_threshold = self.config.get('high_impact_threshold', 100)
        self.index_usage_threshold = self.config.get('index_usage_threshold', 0.1)

        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        # Query cache
        self.query_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'size': 0
        }

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'history_size': 10000,
            'slow_query_threshold': 1.0,  # seconds
            'high_impact_threshold': 100,  # queries per minute
            'index_usage_threshold': 0.1,  # 10% usage
            'auto_indexing': True,
            'query_caching': True,
            'connection_pooling': True,
            'auto_explain': True,
            'monitoring_interval': 60.0,
            'optimization_interval': 300.0,
            'cache_ttl': 300,  # seconds
            'max_cache_size': 1000,
            'connection_pools': {
                'postgresql': {
                    'pool_size': 10,
                    'max_overflow': 20,
                    'pool_timeout': 30,
                    'pool_recycle': 3600
                },
                'mongodb': {
                    'maxPoolSize': 10,
                    'minPoolSize': 2,
                    'maxIdleTimeMS': 30000
                },
                'redis': {
                    'max_connections': 10,
                    'retry_on_timeout': True
                }
            }
        }

    async def initialize_connections(self, db_configs: List[DatabaseConfig]):
        """Initialize database connections and pools"""
        for db_config in db_configs:
            try:
                if db_config.db_type == DatabaseType.POSTGRESQL and POSTGRES_AVAILABLE:
                    await self._init_postgresql_pool(db_config)
                elif db_config.db_type == DatabaseType.MONGODB and MONGODB_AVAILABLE:
                    await self._init_mongodb_pool(db_config)
                elif db_config.db_type == DatabaseType.REDIS and REDIS_AVAILABLE:
                    await self._init_redis_pool(db_config)
                else:
                    logger.warning(f"Unsupported database type: {db_config.db_type}")

            except Exception as e:
                logger.error(f"Failed to initialize connection for {db_config.database}: {e}")

    async def _init_postgresql_pool(self, config: DatabaseConfig):
        """Initialize PostgreSQL connection pool"""
        try:
            pool_config = self.config['connection_pools']['postgresql']

            pool = await asyncpg.create_pool(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                min_size=2,
                max_size=pool_config['pool_size'],
                command_timeout=config.command_timeout,
                server_settings={
                    'application_name': 'dmlog_optimizer',
                    'jit': 'off'  # Disable JIT for consistent performance
                }
            )

            self.connection_pools[f"postgresql_{config.database}"] = pool
            logger.info(f"PostgreSQL pool initialized for {config.database}")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    async def _init_mongodb_pool(self, config: DatabaseConfig):
        """Initialize MongoDB connection pool"""
        try:
            pool_config = self.config['connection_pools']['mongodb']

            # MongoDB connection string
            connection_string = f"mongodb://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

            client = motor.motor_asyncio.AsyncIOMotorClient(
                connection_string,
                maxPoolSize=pool_config['maxPoolSize'],
                minPoolSize=pool_config['minPoolSize'],
                maxIdleTimeMS=pool_config['maxIdleTimeMS'],
                serverSelectionTimeoutMS=config.connection_timeout * 1000
            )

            self.connection_pools[f"mongodb_{config.database}"] = client
            logger.info(f"MongoDB pool initialized for {config.database}")

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB pool: {e}")
            raise

    async def _init_redis_pool(self, config: DatabaseConfig):
        """Initialize Redis connection pool"""
        try:
            pool_config = self.config['connection_pools']['redis']

            pool = aioredis.ConnectionPool.from_url(
                f"redis://{config.host}:{config.port}/{config.database}",
                password=config.password,
                max_connections=pool_config['max_connections'],
                retry_on_timeout=pool_config['retry_on_timeout']
            )

            client = aioredis.Redis(connection_pool=pool)
            self.connection_pools[f"redis_{config.database}"] = client
            logger.info(f"Redis pool initialized for {config.database}")

        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise

    def start_monitoring(self):
        """Start database performance monitoring"""
        if self.monitoring_active:
            logger.warning("Database monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Database monitoring started")

    def stop_monitoring(self):
        """Stop database monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Database monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Analyze query patterns
                self._analyze_query_patterns()

                # Check for slow queries
                self._identify_slow_queries()

                # Generate index recommendations
                if self.auto_indexing:
                    self._generate_index_recommendations()

                # Optimize connection pools
                self._optimize_connection_pools()

                # Clean up old data
                self._cleanup_old_data()

                time.sleep(self.config.get('monitoring_interval', 60.0))

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

    async def execute_query(self, database: str, query: str, params: List[Any] = None,
                          auto_explain: bool = None) -> Any:
        """Execute query with performance monitoring"""
        if auto_explain is None:
            auto_explain = self.auto_explain

        query_hash = self._generate_query_hash(query, params)
        start_time = time.time()

        # Check query cache
        if self.query_caching and query_hash in self.query_cache:
            cached_result = self.query_cache[query_hash]
            if time.time() - cached_result['timestamp'] < self.config.get('cache_ttl', 300):
                self.cache_stats['hits'] += 1
                return cached_result['result']

        self.cache_stats['misses'] += 1

        # Get connection pool
        pool_key = f"postgresql_{database}"
        if pool_key not in self.connection_pools:
            raise ValueError(f"No connection pool found for database: {database}")

        pool = self.connection_pools[pool_key]

        try:
            async with pool.acquire() as connection:
                # Record query start
                query_start = time.time()

                # Execute query
                if auto_explain and query.strip().upper().startswith('SELECT'):
                    # Get execution plan
                    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                    explain_result = await connection.fetchval(explain_query, *params or [])
                    explain_plan = json.loads(explain_result)[0]['Plan']
                else:
                    explain_plan = {}

                # Execute actual query
                if query.strip().upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
                    result = await connection.fetch(query, *params or [])
                    rows_returned = len(result)
                    rows_affected = 0
                else:
                    result = await connection.execute(query, *params or [])
                    rows_returned = 0
                    rows_affected = result.split()[-1] if result else 0
                    result = result

                execution_time = time.time() - query_start

                # Record metrics
                metrics = QueryMetrics(
                    query_hash=query_hash,
                    query_type=self._determine_query_type(query),
                    execution_time=execution_time,
                    rows_returned=rows_returned,
                    rows_affected=rows_affected,
                    cpu_time=0,  # Would need additional monitoring
                    io_time=0,   # Would need additional monitoring
                    memory_usage=0,  # Would need additional monitoring
                    index_usage=self._extract_index_usage(explain_plan),
                    database=database,
                    table=self._extract_table_name(query),
                    explain_plan=explain_plan
                )

                self.query_history.append(metrics)

                # Cache result if appropriate
                if self.query_caching and self._should_cache_query(metrics):
                    self._cache_query_result(query_hash, result)

                # Check if this is a slow query
                if execution_time > self.slow_query_threshold:
                    self.slow_queries.append({
                        'query': query,
                        'execution_time': execution_time,
                        'timestamp': datetime.now(),
                        'database': database,
                        'metrics': metrics
                    })

                return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def _generate_query_hash(self, query: str, params: List[Any] = None) -> str:
        """Generate hash for query identification"""
        # Normalize query (remove extra whitespace, standardize case)
        normalized_query = re.sub(r'\s+', ' ', query.strip().upper())

        # Include parameters in hash if provided
        query_data = f"{normalized_query}:{str(params) if params else ''}"
        return hashlib.md5(query_data.encode()).hexdigest()

    def _determine_query_type(self, query: str) -> QueryType:
        """Determine query type from SQL statement"""
        query_upper = query.strip().upper()

        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        elif query_upper.startswith('ALTER'):
            return QueryType.ALTER
        elif query_upper.startswith(('CREATE INDEX', 'CREATE UNIQUE INDEX')):
            return QueryType.INDEX
        else:
            return QueryType.SELECT  # Default

    def _extract_index_usage(self, explain_plan: Dict[str, Any]) -> List[str]:
        """Extract index usage information from explain plan"""
        indexes = []

        def extract_indexes(plan):
            if 'Index Name' in plan:
                indexes.append(plan['Index Name'])
            if 'Plans' in plan:
                for sub_plan in plan['Plans']:
                    extract_indexes(sub_plan)

        extract_indexes(explain_plan)
        return indexes

    def _extract_table_name(self, query: str) -> str:
        """Extract table name from query"""
        # Simple regex extraction - could be enhanced
        patterns = [
            r'FROM\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _should_cache_query(self, metrics: QueryMetrics) -> bool:
        """Determine if query result should be cached"""
        # Cache SELECT queries that are fast and return reasonable amount of data
        if metrics.query_type != QueryType.SELECT:
            return False

        if metrics.execution_time > self.slow_query_threshold:
            return False

        if metrics.rows_returned > 1000:  # Don't cache very large result sets
            return False

        return True

    def _cache_query_result(self, query_hash: str, result: Any):
        """Cache query result"""
        if len(self.query_cache) >= self.config.get('max_cache_size', 1000):
            # Remove oldest entry
            oldest_key = min(self.query_cache.keys(),
                           key=lambda k: self.query_cache[k]['timestamp'])
            del self.query_cache[oldest_key]

        self.query_cache[query_hash] = {
            'result': result,
            'timestamp': time.time()
        }
        self.cache_stats['size'] = len(self.query_cache)

    def _analyze_query_patterns(self):
        """Analyze query patterns for optimization opportunities"""
        # Group queries by hash and analyze frequency
        query_frequency = defaultdict(int)
        query_performance = defaultdict(list)

        for metrics in self.query_history:
            query_frequency[metrics.query_hash] += 1
            query_performance[metrics.query_hash].append(metrics.execution_time)

        # Identify frequently executed slow queries
        for query_hash, frequency in query_frequency.items():
            if frequency > self.high_impact_threshold:
                avg_time = np.mean(query_performance[query_hash])
                if avg_time > self.slow_query_threshold:
                    logger.warning(f"High-impact slow query detected: {query_hash} "
                                 f"(freq: {frequency}, avg_time: {avg_time:.3f}s)")

    def _identify_slow_queries(self):
        """Identify and analyze slow queries"""
        recent_slow = [q for q in self.slow_queries
                      if q['timestamp'] > datetime.now() - timedelta(hours=1)]

        if len(recent_slow) > 10:
            logger.warning(f"High number of slow queries detected: {len(recent_slow)} in the last hour")

    def _generate_index_recommendations(self):
        """Generate index recommendations based on query patterns"""
        # Analyze WHERE clauses and JOIN conditions
        where_patterns = defaultdict(int)
        join_patterns = defaultdict(int)

        for metrics in self.query_history:
            if metrics.query_type == QueryType.SELECT:
                # Extract WHERE clause patterns (simplified)
                if 'WHERE' in metrics.explain_plan.get('Query', ''):
                    # This would need actual SQL parsing
                    pass

        # Generate recommendations based on patterns
        recommendations = []

        for pattern, frequency in where_patterns.items():
            if frequency > 10:  # Threshold for recommendation
                rec = IndexRecommendation(
                    table=pattern.get('table', ''),
                    columns=pattern.get('columns', []),
                    index_type='btree',
                    estimated_impact=frequency * 0.1,  # Simplified impact calculation
                    current_size_mb=0,
                    estimated_size_mb=10,
                    priority='high' if frequency > 50 else 'medium',
                    reason=f"Frequent WHERE clause on columns: {pattern.get('columns', [])}"
                )
                recommendations.append(rec)

        self.index_recommendations = {f"{rec.table}_{rec.columns}": rec for rec in recommendations}

    def _optimize_connection_pools(self):
        """Optimize connection pool sizes based on usage"""
        for pool_key, pool in self.connection_pools.items():
            # Monitor pool usage and adjust size if needed
            # This would depend on the specific database library
            pass

    def _cleanup_old_data(self):
        """Clean up old performance data"""
        cutoff_time = datetime.now() - timedelta(days=7)

        # Clean up old query history
        self.query_history = deque(
            [m for m in self.query_history if m.timestamp > cutoff_time],
            maxlen=self.config.get('history_size', 10000)
        )

        # Clean up old slow queries
        self.slow_queries = deque(
            [q for q in self.slow_queries if q['timestamp'] > cutoff_time],
            maxlen=1000
        )

    def get_performance_report(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if time_window is None:
            time_window = timedelta(hours=24)

        cutoff_time = datetime.now() - time_window
        recent_queries = [q for q in self.query_history if q.timestamp > cutoff_time]

        if not recent_queries:
            return {"error": "No query data available for specified time window"}

        # Calculate statistics
        execution_times = [q.execution_time for q in recent_queries]
        query_types = defaultdict(int)
        database_usage = defaultdict(int)
        table_usage = defaultdict(int)

        for query in recent_queries:
            query_types[query.query_type.value] += 1
            database_usage[query.database] += 1
            if query.table:
                table_usage[query.table] += 1

        report = {
            'time_window': str(time_window),
            'total_queries': len(recent_queries),
            'query_types': dict(query_types),
            'database_usage': dict(database_usage),
            'table_usage': dict(table_usage),
            'performance_stats': {
                'avg_execution_time': np.mean(execution_times),
                'median_execution_time': np.median(execution_times),
                'max_execution_time': np.max(execution_times),
                'min_execution_time': np.min(execution_times),
                'std_execution_time': np.std(execution_times),
                'total_rows_returned': sum(q.rows_returned for q in recent_queries),
                'total_rows_affected': sum(q.rows_affected for q in recent_queries)
            },
            'slow_queries': len([q for q in recent_queries if q.execution_time > self.slow_query_threshold]),
            'index_recommendations': len(self.index_recommendations),
            'cache_stats': self.cache_stats.copy()
        }

        # Add optimization recommendations
        report['recommendations'] = self._generate_optimization_recommendations(recent_queries)

        return report

    def _generate_optimization_recommendations(self, queries: List[QueryMetrics]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Slow query recommendations
        slow_queries = [q for q in queries if q.execution_time > self.slow_query_threshold]
        if len(slow_queries) > len(queries) * 0.1:  # More than 10% slow queries
            recommendations.append("High percentage of slow queries detected. Consider query optimization and indexing.")

        # Missing indexes
        if self.index_recommendations:
            high_priority_recs = [r for r in self.index_recommendations.values() if r.priority == 'high']
            if high_priority_recs:
                recommendations.append(f"Consider creating {len(high_priority_recs)} high-priority indexes for improved performance.")

        # Query cache efficiency
        if self.cache_stats['hits'] + self.cache_stats['misses'] > 0:
            hit_rate = self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses'])
            if hit_rate < 0.5:
                recommendations.append("Low query cache hit rate. Consider adjusting cache TTL or size.")

        # Connection pool optimization
        # This would need actual pool metrics

        return recommendations

    async def create_recommended_indexes(self, database: str) -> List[str]:
        """Create recommended indexes"""
        created_indexes = []

        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL not available for index creation")
            return created_indexes

        pool_key = f"postgresql_{database}"
        if pool_key not in self.connection_pools:
            logger.error(f"No connection pool found for database: {database}")
            return created_indexes

        pool = self.connection_pools[pool_key]

        try:
            async with pool.acquire() as connection:
                for key, recommendation in self.index_recommendations.items():
                    if recommendation.priority == 'high':
                        try:
                            # Create index SQL
                            columns_str = ', '.join(recommendation.columns)
                            index_name = f"idx_{recommendation.table}_{'_'.join(recommendation.columns)}"

                            create_sql = f"""
                            CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                            ON {recommendation.table} ({columns_str})
                            """

                            await connection.execute(create_sql)
                            created_indexes.append(index_name)
                            logger.info(f"Created index: {index_name}")

                        except Exception as e:
                            logger.error(f"Failed to create index {index_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

        return created_indexes

    def get_index_recommendations(self) -> Dict[str, IndexRecommendation]:
        """Get current index recommendations"""
        return self.index_recommendations.copy()

    def clear_query_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'size': 0
        }
        logger.info("Query cache cleared")

    async def analyze_table(self, database: str, table: str) -> Dict[str, Any]:
        """Analyze table statistics and structure"""
        if not POSTGRES_AVAILABLE:
            return {"error": "PostgreSQL not available"}

        pool_key = f"postgresql_{database}"
        if pool_key not in self.connection_pools:
            return {"error": f"No connection pool found for database: {database}"}

        pool = self.connection_pools[pool_key]

        try:
            async with pool.acquire() as connection:
                # Get table statistics
                stats_query = """
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE tablename = $1
                """

                stats = await connection.fetch(stats_query, table)

                # Get index information
                index_query = """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = $1
                """

                indexes = await connection.fetch(index_query, table)

                # Get table size
                size_query = """
                SELECT
                    pg_size_pretty(pg_total_relation_size($1)) as total_size,
                    pg_size_pretty(pg_relation_size($1)) as table_size,
                    pg_size_pretty(pg_total_relation_size($1) - pg_relation_size($1)) as index_size
                """

                sizes = await connection.fetchrow(size_query, table)

                return {
                    'table': table,
                    'statistics': [dict(row) for row in stats],
                    'indexes': [dict(row) for row in indexes],
                    'sizes': dict(sizes) if sizes else {}
                }

        except Exception as e:
            logger.error(f"Failed to analyze table {table}: {e}")
            return {"error": str(e)}

    async def close_connections(self):
        """Close all database connections and pools"""
        for pool_key, pool in self.connection_pools.items():
            try:
                if pool_key.startswith('postgresql'):
                    await pool.close()
                elif pool_key.startswith('mongodb'):
                    pool.close()
                elif pool_key.startswith('redis'):
                    await pool.close()
                logger.info(f"Closed connection pool: {pool_key}")
            except Exception as e:
                logger.error(f"Failed to close pool {pool_key}: {e}")

        self.connection_pools.clear()
        logger.info("All database connections closed")

# Query optimization decorator
def optimize_query(optimizer: DatabaseOptimizer, database: str, auto_explain: bool = True):
    """Decorator for query optimization"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract query from function or use a different approach
            # This is a simplified implementation
            query = getattr(func, '__query__', None)

            if query:
                result = await optimizer.execute_query(database, query, auto_explain=auto_explain)
                return result
            else:
                # Fallback to original function
                return await func(*args, **kwargs)

        return wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize optimizer
        optimizer = DatabaseOptimizer({
            'slow_query_threshold': 0.5,
            'auto_indexing': True,
            'query_caching': True
        })

        # Database configuration
        db_config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="dmlog",
            username="postgres",
            password="password"
        )

        # Initialize connection
        await optimizer.initialize_connections([db_config])

        # Start monitoring
        optimizer.start_monitoring()

        # Example queries
        try:
            # Simple query
            result = await optimizer.execute_query(
                "dmlog",
                "SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '24 hours'"
            )
            print(f"Query result: {result}")

            # Get performance report
            report = optimizer.get_performance_report()
            print(f"Performance report: {json.dumps(report, indent=2, default=str)}")

            # Get index recommendations
            recommendations = optimizer.get_index_recommendations()
            print(f"Index recommendations: {len(recommendations)}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Cleanup
            optimizer.stop_monitoring()
            await optimizer.close_connections()

    # Run example
    asyncio.run(main())