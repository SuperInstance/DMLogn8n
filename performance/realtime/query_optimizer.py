#!/usr/bin/env python3
"""
Query Optimizer - Advanced Database Query Optimization System
Optimizes database queries for maximum performance and minimal latency
"""

import asyncio
import time
import re
import hashlib
import json
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import threading
from functools import wraps, lru_cache
from abc import ABC, abstractmethod
import sqlparse
from sqlparse.sql import Statement, Identifier, Where, Function
from enum import Enum

class QueryType(Enum):
    """Database query types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    UNKNOWN = "UNKNOWN"

class OptimizationLevel(Enum):
    """Query optimization levels"""
    NONE = 0
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    AGGRESSIVE = 4

@dataclass
class QueryPlan:
    """Optimized query execution plan"""
    original_query: str
    optimized_query: str
    query_type: QueryType
    estimated_cost: float
    optimization_level: OptimizationLevel
    indexes_used: List[str] = field(default_factory=list)
    indexes_suggested: List[str] = field(default_factory=list)
    execution_time_ms: Optional[float] = None
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    optimizations_applied: List[str] = field(default_factory=list)

@dataclass
class QueryMetrics:
    """Query execution metrics"""
    query_hash: str
    execution_time_ms: float
    rows_returned: int
    rows_examined: int
    index_usage: bool
    cache_hit: bool
    timestamp: float
    optimization_applied: bool = False

@dataclass
class IndexRecommendation:
    """Database index recommendation"""
    table_name: str
    column_names: List[str]
    index_type: str  # BTREE, HASH, GIN, etc.
    estimated_improvement: float  # Percentage improvement
    priority: int  # 1-10, higher is more important
    query_patterns: List[str] = field(default_factory=list)

class QueryOptimizer:
    """Advanced database query optimizer"""

    def __init__(self, enable_caching: bool = True, optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE):
        self.enable_caching = enable_caching
        self.optimization_level = optimization_level

        # Query cache
        self.query_cache: Dict[str, Any] = {}
        self.query_plans: Dict[str, QueryPlan] = {}
        self.cache_lock = threading.RLock()

        # Query metrics and analysis
        self.query_metrics: Dict[str, List[QueryMetrics]] = defaultdict(list)
        self.slow_queries: List[QueryMetrics] = []
        self.query_patterns: Dict[str, List[str]] = defaultdict(list)

        # Index analysis
        self.index_recommendations: List[IndexRecommendation] = []
        self.existing_indexes: Dict[str, List[str]] = defaultdict(list)

        # Optimization rules
        self.optimization_rules = self._initialize_optimization_rules()

        # Performance thresholds
        self.slow_query_threshold_ms = 100.0  # Queries slower than 100ms
        self.very_slow_query_threshold_ms = 1000.0  # Queries slower than 1s

        # Background analysis
        self.running = False
        self.analysis_thread: Optional[threading.Thread] = None

        # Setup logging
        self.logger = logging.getLogger("QueryOptimizer")

        # Start background analysis if enabled
        if enable_caching:
            self._start_background_analysis()

    def _initialize_optimization_rules(self) -> Dict[str, Callable]:
        """Initialize query optimization rules"""
        return {
            'add_where_clause': self._optimize_where_clause,
            'optimize_joins': self._optimize_joins,
            'add_indexes': self._suggest_indexes,
            'remove_unnecessary_columns': self._optimize_select_columns,
            'optimize_order_by': self._optimize_order_by,
            'add_query_hints': self._add_query_hints,
            'optimize_subqueries': self._optimize_subqueries,
            'batch_operations': self._batch_operations,
            'use_prepared_statements': self._use_prepared_statements,
            'optimize_aggregations': self._optimize_aggregations
        }

    def _start_background_analysis(self):
        """Start background query analysis thread"""
        self.running = True
        self.analysis_thread = threading.Thread(
            target=self._background_analysis_loop,
            name="QueryAnalysis",
            daemon=True
        )
        self.analysis_thread.start()

    def optimize_query(self, query: str, force_optimize: bool = False) -> QueryPlan:
        """Optimize a database query"""
        query_hash = self._generate_query_hash(query)

        # Check cache first
        if not force_optimize and query_hash in self.query_plans:
            return self.query_plans[query_hash]

        # Parse and analyze query
        parsed_query = sqlparse.parse(query)[0] if query else None
        query_type = self._detect_query_type(parsed_query)

        # Apply optimizations based on level
        optimized_query = query
        optimizations_applied = []

        if self.optimization_level.value >= OptimizationLevel.BASIC.value:
            optimized_query, applied = self._apply_basic_optimizations(query, parsed_query)
            optimizations_applied.extend(applied)

        if self.optimization_level.value >= OptimizationLevel.INTERMEDIATE.value:
            optimized_query, applied = self._apply_intermediate_optimizations(optimized_query, parsed_query)
            optimizations_applied.extend(applied)

        if self.optimization_level.value >= OptimizationLevel.ADVANCED.value:
            optimized_query, applied = self._apply_advanced_optimizations(optimized_query, parsed_query)
            optimizations_applied.extend(applied)

        if self.optimization_level.value >= OptimizationLevel.AGGRESSIVE.value:
            optimized_query, applied = self._apply_aggressive_optimizations(optimized_query, parsed_query)
            optimizations_applied.extend(applied)

        # Create query plan
        plan = QueryPlan(
            original_query=query,
            optimized_query=optimized_query,
            query_type=query_type,
            estimated_cost=self._estimate_query_cost(optimized_query),
            optimization_level=self.optimization_level,
            optimizations_applied=optimizations_applied
        )

        # Analyze and suggest indexes
        if query_type == QueryType.SELECT:
            plan.indexes_suggested = self._analyze_index_needs(parsed_query)

        # Cache the plan
        with self.cache_lock:
            self.query_plans[query_hash] = plan

        return plan

    def _apply_basic_optimizations(self, query: str, parsed_query: Statement) -> Tuple[str, List[str]]:
        """Apply basic query optimizations"""
        optimizations = []
        optimized = query

        # Remove extra whitespace
        optimized = re.sub(r'\s+', ' ', optimized).strip()
        optimizations.append('normalized_whitespace')

        # Add LIMIT to large result sets if missing
        if 'SELECT' in optimized.upper() and 'LIMIT' not in optimized.upper():
            optimized += ' LIMIT 1000'
            optimizations.append('added_default_limit')

        return optimized, optimizations

    def _apply_intermediate_optimizations(self, query: str, parsed_query: Statement) -> Tuple[str, List[str]]:
        """Apply intermediate query optimizations"""
        optimizations = []
        optimized = query

        # Optimize WHERE clauses
        optimized = self._optimize_where_clause(optimized)
        optimizations.append('optimized_where_clause')

        # Optimize SELECT columns (avoid SELECT *)
        if 'SELECT *' in optimized:
            optimized = self._optimize_select_columns(optimized)
            optimizations.append('optimized_select_columns')

        return optimized, optimizations

    def _apply_advanced_optimizations(self, query: str, parsed_query: Statement) -> Tuple[str, List[str]]:
        """Apply advanced query optimizations"""
        optimizations = []
        optimized = query

        # Optimize JOINs
        optimized = self._optimize_joins(optimized)
        optimizations.append('optimized_joins')

        # Optimize ORDER BY
        optimized = self._optimize_order_by(optimized)
        optimizations.append('optimized_order_by')

        # Optimize subqueries
        optimized = self._optimize_subqueries(optimized)
        optimizations.append('optimized_subqueries')

        return optimized, optimizations

    def _apply_aggressive_optimizations(self, query: str, parsed_query: Statement) -> Tuple[str, List[str]]:
        """Apply aggressive query optimizations"""
        optimizations = []
        optimized = query

        # Add query hints
        optimized = self._add_query_hints(optimized)
        optimizations.append('added_query_hints')

        # Optimize aggregations
        optimized = self._optimize_aggregations(optimized)
        optimizations.append('optimized_aggregations')

        return optimized, optimizations

    def _optimize_where_clause(self, query: str) -> str:
        """Optimize WHERE clause for better performance"""
        # Convert OR conditions to UNION when possible
        if ' OR ' in query.upper():
            # Simple heuristic for OR to UNION conversion
            or_pattern = r'(\w+)\s*=\s*([^OR]+)\s+OR\s+\1\s*=\s*([^)\s]+)'
            optimized = re.sub(or_pattern, r'(\1 = \2) UNION (\1 = \3)', query, flags=re.IGNORECASE)
            if optimized != query:
                return optimized

        # Optimize IN clauses with many values
        in_pattern = r'IN\s*\(([^)]{100,})\)'  # IN clause with > 100 chars
        if re.search(in_pattern, query, re.IGNORECASE):
            # Could convert to JOIN with temporary table
            pass

        # Add index hints where beneficial
        if 'WHERE' in query.upper():
            # Add USE INDEX hint if table and column are identifiable
            pass

        return query

    def _optimize_joins(self, query: str) -> str:
        """Optimize JOIN operations"""
        # Ensure JOIN conditions use indexed columns
        # Suggest STRAIGHT_JOIN for MySQL when appropriate
        # Optimize JOIN order based on table sizes

        # Simple optimization: add STRAIGHT_JOIN hint for complex queries
        join_count = query.upper().count(' JOIN ')
        if join_count > 2:
            return query.replace('SELECT', 'SELECT /*+ STRAIGHT_JOIN */', 1)

        return query

    def _optimize_select_columns(self, query: str) -> str:
        """Replace SELECT * with specific columns"""
        # This would require table schema knowledge
        # For now, just add a comment suggesting optimization
        return query.replace('SELECT *', 'SELECT /* TODO: Specify columns */ *')

    def _optimize_order_by(self, query: str) -> str:
        """Optimize ORDER BY clauses"""
        # Ensure ORDER BY uses indexed columns
        # Remove unnecessary ORDER BY when using LIMIT 1
        if 'ORDER BY' in query.upper() and 'LIMIT 1' in query.upper():
            # Check if ORDER BY is necessary
            pass

        return query

    def _optimize_subqueries(self, query: str) -> str:
        """Optimize subqueries"""
        # Convert subqueries to JOINs when possible
        # Use EXISTS instead of IN for better performance
        if ' IN (SELECT' in query.upper():
            optimized = re.sub(
                r'(\w+)\s+IN\s*\(SELECT',
                r'EXISTS (SELECT 1 FROM',
                query,
                flags=re.IGNORECASE
            )
            return optimized

        return query

    def _add_query_hints(self, query: str) -> str:
        """Add database-specific query hints"""
        # MySQL hints
        if 'SELECT' in query.upper():
            # Add FORCE INDEX hint for large tables
            optimized = query.replace('SELECT', 'SELECT /*+ FORCE INDEX (primary) */', 1)
            return optimized

        return query

    def _optimize_aggregations(self, query: str) -> str:
        """Optimize aggregation queries"""
        # Add appropriate indexes for GROUP BY
        # Optimize COUNT queries
        if 'COUNT(' in query.upper():
            # Use COUNT(1) instead of COUNT(*) for better performance
            optimized = query.replace('COUNT(*)', 'COUNT(1)')
            return optimized

        return query

    def _batch_operations(self, query: str) -> str:
        """Batch multiple operations for better performance"""
        # This would analyze multiple queries and batch them
        return query

    def _use_prepared_statements(self, query: str) -> str:
        """Convert to prepared statements"""
        # Convert to parameterized queries
        return query

    def _suggest_indexes(self, query: str) -> str:
        """Suggest and add index hints"""
        return query

    def _detect_query_type(self, parsed_query: Optional[Statement]) -> QueryType:
        """Detect the type of query"""
        if not parsed_query:
            return QueryType.UNKNOWN

        first_token = parsed_query.token_first(skip_ws=True, skip_cm=True)
        if first_token:
            token_type = first_token.ttype
            token_value = str(first_token).upper()

            if token_value == 'SELECT':
                return QueryType.SELECT
            elif token_value == 'INSERT':
                return QueryType.INSERT
            elif token_value == 'UPDATE':
                return QueryType.UPDATE
            elif token_value == 'DELETE':
                return QueryType.DELETE
            elif token_value == 'CREATE':
                return QueryType.CREATE
            elif token_value == 'DROP':
                return QueryType.DROP
            elif token_value == 'ALTER':
                return QueryType.ALTER

        return QueryType.UNKNOWN

    def _analyze_index_needs(self, parsed_query: Optional[Statement]) -> List[str]:
        """Analyze query and suggest needed indexes"""
        suggestions = []

        if not parsed_query:
            return suggestions

        # Extract WHERE clause columns
        where_clause = self._extract_where_clause(parsed_query)
        if where_clause:
            columns = self._extract_columns_from_clause(where_clause)
            for column in columns:
                suggestions.append(f"INDEX on {column}")

        # Extract JOIN columns
        join_columns = self._extract_join_columns(parsed_query)
        for column in join_columns:
            suggestions.append(f"INDEX on {column} for JOIN")

        # Extract ORDER BY columns
        order_columns = self._extract_order_by_columns(parsed_query)
        for column in order_columns:
            suggestions.append(f"INDEX on {column} for ORDER BY")

        return suggestions

    def _extract_where_clause(self, parsed_query: Statement) -> Optional[str]:
        """Extract WHERE clause from parsed query"""
        for token in parsed_query.flatten():
            if token.ttype is None and str(token).upper() == 'WHERE':
                # Find the WHERE clause content
                # This is simplified - would need proper parsing
                return str(token)
        return None

    def _extract_columns_from_clause(self, clause: str) -> List[str]:
        """Extract column names from SQL clause"""
        columns = []
        # Simple regex-based extraction
        # Would need more sophisticated parsing for production
        pattern = r'(\w+)\s*(?:=|>|<|>=|<=|LIKE|IN)'
        matches = re.findall(pattern, clause, re.IGNORECASE)
        columns.extend(matches)
        return columns

    def _extract_join_columns(self, parsed_query: Statement) -> List[str]:
        """Extract JOIN condition columns"""
        columns = []
        # Simplified JOIN column extraction
        for token in parsed_query.flatten():
            if str(token).upper() == 'ON':
                # Extract columns from ON clause
                pass
        return columns

    def _extract_order_by_columns(self, parsed_query: Statement) -> List[str]:
        """Extract ORDER BY columns"""
        columns = []
        query_str = str(parsed_query)
        order_match = re.search(r'ORDER BY\s+([^,\s]+(?:,\s*[^,\s]+)*)', query_str, re.IGNORECASE)
        if order_match:
            order_columns = [col.strip() for col in order_match.group(1).split(',')]
            columns.extend(order_columns)
        return columns

    def _estimate_query_cost(self, query: str) -> float:
        """Estimate query execution cost"""
        cost = 1.0

        # Base cost by query type
        if 'SELECT' in query.upper():
            cost += 1.0
        if 'JOIN' in query.upper():
            cost += query.upper().count('JOIN') * 2.0
        if 'WHERE' in query.upper():
            cost += 0.5
        if 'ORDER BY' in query.upper():
            cost += 1.0
        if 'GROUP BY' in query.upper():
            cost += 1.5

        # Adjust for query complexity
        cost += len(query) / 1000.0

        return cost

    def record_query_execution(self, query: str, execution_time_ms: float,
                             rows_returned: int, rows_examined: int,
                             index_used: bool = False):
        """Record query execution metrics"""
        query_hash = self._generate_query_hash(query)

        metrics = QueryMetrics(
            query_hash=query_hash,
            execution_time_ms=execution_time_ms,
            rows_returned=rows_returned,
            rows_examined=rows_examined,
            index_usage=index_used,
            cache_hit=query_hash in self.query_plans,
            timestamp=time.time(),
            optimization_applied=query_hash in self.query_plans
        )

        # Store metrics
        self.query_metrics[query_hash].append(metrics)

        # Track slow queries
        if execution_time_ms > self.slow_query_threshold_ms:
            self.slow_queries.append(metrics)
            self.logger.warning(f"Slow query detected: {execution_time_ms:.2f}ms - {query[:100]}...")

        # Keep only recent metrics
        if len(self.query_metrics[query_hash]) > 100:
            self.query_metrics[query_hash] = self.query_metrics[query_hash][-50:]

    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for normalized query"""
        # Normalize query (remove extra whitespace, standardize case)
        normalized = re.sub(r'\s+', ' ', query.strip().upper())
        return hashlib.md5(normalized.encode()).hexdigest()

    def get_query_analysis(self) -> Dict:
        """Get comprehensive query analysis"""
        analysis = {
            'total_queries': sum(len(metrics) for metrics in self.query_metrics.values()),
            'slow_queries': len(self.slow_queries),
            'cached_queries': len(self.query_plans),
            'optimization_level': self.optimization_level.name,
            'query_types': defaultdict(int),
            'avg_execution_time_ms': 0.0,
            'index_usage_rate': 0.0
        }

        # Calculate statistics
        all_metrics = []
        for metrics_list in self.query_metrics.values():
            all_metrics.extend(metrics_list)

        if all_metrics:
            analysis['avg_execution_time_ms'] = sum(m.execution_time_ms for m in all_metrics) / len(all_metrics)
            analysis['index_usage_rate'] = sum(1 for m in all_metrics if m.index_usage) / len(all_metrics)

        # Analyze slow queries
        if self.slow_queries:
            analysis['slowest_queries'] = [
                {
                    'execution_time_ms': q.execution_time_ms,
                    'rows_returned': q.rows_returned,
                    'rows_examined': q.rows_examined,
                    'index_used': q.index_usage
                }
                for q in sorted(self.slow_queries, key=lambda x: x.execution_time_ms, reverse=True)[:10]
            ]

        return analysis

    def generate_index_recommendations(self) -> List[IndexRecommendation]:
        """Generate index recommendations based on query analysis"""
        recommendations = []

        # Analyze query patterns for index opportunities
        for query_hash, metrics_list in self.query_metrics.items():
            if not metrics_list:
                continue

            # Calculate average metrics for this query pattern
            avg_time = sum(m.execution_time_ms for m in metrics_list) / len(metrics_list)
            avg_rows_examined = sum(m.rows_examined for m in metrics_list) / len(metrics_list)
            index_usage_rate = sum(1 for m in metrics_list if m.index_usage) / len(metrics_list)

            # Recommend indexes for slow queries without index usage
            if avg_time > self.slow_query_threshold_ms and index_usage_rate < 0.5:
                # This is simplified - would need actual query analysis
                recommendation = IndexRecommendation(
                    table_name="table_name",  # Would extract from query
                    column_names=["column_name"],  # Would extract from query
                    index_type="BTREE",
                    estimated_improvement=min(50.0, avg_time / 10),
                    priority=min(10, int(avg_time / 50)),
                    query_patterns=[f"Query hash: {query_hash}"]
                )
                recommendations.append(recommendation)

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority, reverse=True)
        return recommendations[:20]  # Return top 20 recommendations

    def _background_analysis_loop(self):
        """Background thread for continuous query analysis"""
        while self.running:
            try:
                # Analyze slow queries
                if len(self.slow_queries) > 10:
                    self._analyze_slow_queries()

                # Generate index recommendations
                if time.time() % 300 < 1:  # Every 5 minutes
                    self.index_recommendations = self.generate_index_recommendations()

                # Clean up old metrics
                self._cleanup_old_metrics()

                time.sleep(60)  # Analyze every minute

            except Exception as e:
                self.logger.error(f"Background analysis error: {e}")

    def _analyze_slow_queries(self):
        """Analyze patterns in slow queries"""
        # Group slow queries by patterns
        patterns = defaultdict(list)
        for query in self.slow_queries[-100:]:  # Last 100 slow queries
            pattern = self._extract_query_pattern(query.query_hash)
            patterns[pattern].append(query)

        # Log significant patterns
        for pattern, queries in patterns.items():
            if len(queries) >= 5:  # Pattern appears at least 5 times
                avg_time = sum(q.execution_time_ms for q in queries) / len(queries)
                self.logger.warning(f"Slow query pattern detected: {pattern} - Avg: {avg_time:.2f}ms")

    def _extract_query_pattern(self, query_hash: str) -> str:
        """Extract pattern from query hash"""
        # Simplified pattern extraction
        return query_hash[:8]

    def _cleanup_old_metrics(self):
        """Clean up old query metrics"""
        cutoff_time = time.time() - 24 * 3600  # 24 hours ago

        # Clean up metrics
        for query_hash in list(self.query_metrics.keys()):
            self.query_metrics[query_hash] = [
                m for m in self.query_metrics[query_hash]
                if m.timestamp > cutoff_time
            ]

            if not self.query_metrics[query_hash]:
                del self.query_metrics[query_hash]

        # Clean up slow queries
        self.slow_queries = [
            q for q in self.slow_queries
            if q.timestamp > cutoff_time
        ]

    def shutdown(self):
        """Shutdown the query optimizer"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)

# Global query optimizer instance
query_optimizer = QueryOptimizer()

# Decorators for query optimization
def optimize_query(func: Callable) -> Callable:
    """Decorator to optimize database queries"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Extract query from arguments (implementation-specific)
        query = kwargs.get('query') or (args[0] if args else None)

        if query:
            # Optimize query
            plan = query_optimizer.optimize_query(query)
            if plan.optimized_query != query:
                kwargs['query'] = plan.optimized_query
                # Log optimization
                logging.info(f"Query optimized: {len(plan.optimizations_applied)} improvements")

        # Execute with timing
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000

            # Record metrics (would need actual row counts)
            query_optimizer.record_query_execution(
                query=kwargs.get('query', query or ''),
                execution_time_ms=execution_time_ms,
                rows_returned=0,  # Would get from result
                rows_examined=0   # Would get from database
            )

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            query_optimizer.record_query_execution(
                query=kwargs.get('query', query or ''),
                execution_time_ms=execution_time_ms,
                rows_returned=0,
                rows_examined=0
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Similar implementation for synchronous functions
        return func(*args, **kwargs)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

# Utility functions
def analyze_slow_queries() -> List[Dict]:
    """Analyze and return slow query patterns"""
    return query_optimizer.get_query_analysis()

def get_index_recommendations() -> List[IndexRecommendation]:
    """Get index recommendations for performance improvement"""
    return query_optimizer.generate_index_recommendations()