#!/usr/bin/env python3
"""
Advanced Database Query Optimizer
Optimizes SQL and NoSQL queries for sub-100ms performance across multiple database types.
"""

import asyncio
import json
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict
import psycopg2
import psycopg2.extras
import pymongo
import redis
from asyncpg import create_pool
from aioredis import create_redis_pool
import sqlparse
from sqlparse.sql import Identifier, Function
from sqlparse.tokens import Keyword, DML

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    SUBQUERY = "SUBQUERY"
    NOSQL_FIND = "NOSQL_FIND"
    NOSQL_AGGREGATE = "NOSQL_AGGREGATE"

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"

@dataclass
class QueryPlan:
    query: str
    database_type: DatabaseType
    execution_time: float
    plan_details: Dict[str, Any]
    cost: float
    rows_examined: int
    indexes_used: List[str]
    bottlenecks: List[str]
    recommendations: List[str]

@dataclass
class QueryOptimization:
    original_query: str
    optimized_query: str
    estimated_improvement: float
    changes_made: List[str]
    new_indexes: List[Dict[str, Any]]
    parameterized_query: str

class QueryOptimizer:
    """Advanced query optimization system for multiple database types"""

    def __init__(self):
        self.query_cache = {}
        self.optimization_history = []
        self.index_recommendations = defaultdict(list)
        self.query_patterns = {}
        self.performance_benchmarks = {}

        # Optimization thresholds
        self.SLOW_QUERY_THRESHOLD = 100  # milliseconds
        self.HIGH_COST_THRESHOLD = 1000
        self.INDEX_USAGE_THRESHOLD = 0.8
        self.CACHE_HIT_TARGET = 0.95

        # Query pattern analysis
        self.frequent_queries = defaultdict(int)
        self.query_signatures = {}

    async def analyze_query_plan(self, query: str, database_type: DatabaseType,
                                connection_params: Dict[str, Any]) -> QueryPlan:
        """Analyze query execution plan and identify bottlenecks"""

        start_time = time.time()

        try:
            if database_type == DatabaseType.POSTGRESQL:
                return await self._analyze_postgresql_plan(query, connection_params)
            elif database_type == DatabaseType.MONGODB:
                return await self._analyze_mongodb_plan(query, connection_params)
            elif database_type == DatabaseType.REDIS:
                return await self._analyze_redis_plan(query, connection_params)
            else:
                raise ValueError(f"Unsupported database type: {database_type}")

        except Exception as e:
            logger.error(f"Error analyzing query plan: {e}")
            return QueryPlan(
                query=query,
                database_type=database_type,
                execution_time=time.time() - start_time,
                plan_details={},
                cost=float('inf'),
                rows_examined=0,
                indexes_used=[],
                bottlenecks=[f"Analysis failed: {str(e)}"],
                recommendations=["Query analysis failed - check syntax and permissions"]
            )

    async def _analyze_postgresql_plan(self, query: str, connection_params: Dict[str, Any]) -> QueryPlan:
        """Analyze PostgreSQL query execution plan"""

        try:
            # Connect to PostgreSQL
            conn = await create_pool(**connection_params)

            async with conn.acquire() as connection:
                # Get EXPLAIN ANALYZE output
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

                async with connection.transaction():
                    result = await connection.fetchval(explain_query)
                    plan_data = json.loads(result)[0]["Plan"]

                # Extract plan details
                execution_time = plan_data.get("Execution Time", 0)
                total_cost = plan_data.get("Total Cost", 0)
                plan_rows = plan_data.get("Plan Rows", 0)

                # Analyze indexes used
                indexes_used = self._extract_postgresql_indexes(plan_data)

                # Identify bottlenecks
                bottlenecks = self._identify_postgresql_bottlenecks(plan_data, execution_time)

                # Generate recommendations
                recommendations = self._generate_postgresql_recommendations(
                    plan_data, bottlenecks, query
                )

                return QueryPlan(
                    query=query,
                    database_type=DatabaseType.POSTGRESQL,
                    execution_time=execution_time,
                    plan_details=plan_data,
                    cost=total_cost,
                    rows_examined=plan_rows,
                    indexes_used=indexes_used,
                    bottlenecks=bottlenecks,
                    recommendations=recommendations
                )

        except Exception as e:
            logger.error(f"PostgreSQL plan analysis failed: {e}")
            raise

    async def _analyze_mongodb_plan(self, query: str, connection_params: Dict[str, Any]) -> QueryPlan:
        """Analyze MongoDB query execution plan"""

        try:
            # Connect to MongoDB
            client = pymongo.MongoClient(**connection_params)
            db_name = connection_params.get('database', 'test')
            collection_name = self._extract_mongodb_collection(query)

            if not collection_name:
                raise ValueError("Could not extract collection name from MongoDB query")

            db = client[db_name]
            collection = db[collection_name]

            # Parse query and options
            query_dict = self._parse_mongodb_query(query)

            # Get execution stats
            start_time = time.time()
            cursor = collection.find(query_dict.get('filter', {}))

            # Use explain() to get execution plan
            explain_result = collection.find(query_dict.get('filter', {})).explain()

            execution_time = explain_result.get('executionStats', {}).get('executionTimeMillis', 0)
            docs_examined = explain_result.get('executionStats', {}).get('totalDocsExamined', 0)

            # Analyze index usage
            indexes_used = []
            if 'winningPlan' in explain_result.get('queryPlanner', {}):
                winning_plan = explain_result['queryPlanner']['winningPlan']
                indexes_used = self._extract_mongodb_indexes(winning_plan)

            # Identify bottlenecks
            bottlenecks = self._identify_mongodb_bottlenecks(explain_result)

            # Generate recommendations
            recommendations = self._generate_mongodb_recommendations(explain_result, query_dict)

            return QueryPlan(
                query=query,
                database_type=DatabaseType.MONGODB,
                execution_time=execution_time,
                plan_details=explain_result,
                cost=docs_examined,
                rows_examined=docs_examined,
                indexes_used=indexes_used,
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"MongoDB plan analysis failed: {e}")
            raise

    async def _analyze_redis_plan(self, query: str, connection_params: Dict[str, Any]) -> QueryPlan:
        """Analyze Redis query performance"""

        try:
            # Connect to Redis
            redis_client = await create_redis_pool(**connection_params)

            # Parse Redis command
            command_parts = query.split()
            command = command_parts[0].upper()

            start_time = time.time()

            # Execute command and measure performance
            if command == 'GET':
                result = await redis_client.get(command_parts[1])
            elif command == 'SET':
                result = await redis_client.set(command_parts[1], command_parts[2])
            elif command == 'HGET':
                result = await redis_client.hget(command_parts[1], command_parts[2])
            elif command == 'HSET':
                result = await redis_client.hset(command_parts[1], command_parts[2], command_parts[3])
            else:
                result = await redis_client.execute_command(*command_parts)

            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Get Redis info for analysis
            info = await redis_client.info()

            # Analyze bottlenecks
            bottlenecks = []
            if execution_time > self.SLOW_QUERY_THRESHOLD:
                bottlenecks.append(f"Slow Redis operation: {execution_time:.2f}ms")

            if info.get('used_memory', 0) > 1024 * 1024 * 1024:  # 1GB
                bottlenecks.append("High memory usage detected")

            # Generate recommendations
            recommendations = []
            if execution_time > self.SLOW_QUERY_THRESHOLD:
                recommendations.append("Consider using Redis pipelines for batch operations")

            if command in ['KEYS', 'SMEMBERS']:
                recommendations.append(f"Consider using SCAN instead of {command} for large datasets")

            return QueryPlan(
                query=query,
                database_type=DatabaseType.REDIS,
                execution_time=execution_time,
                plan_details={'redis_info': info, 'command': command},
                cost=execution_time,
                rows_examined=1,
                indexes_used=[],
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Redis plan analysis failed: {e}")
            raise

    async def optimize_query(self, query_plan: QueryPlan) -> QueryOptimization:
        """Generate optimized query based on analysis"""

        original_query = query_plan.query
        database_type = query_plan.database_type

        if database_type == DatabaseType.POSTGRESQL:
            return await self._optimize_postgresql_query(query_plan)
        elif database_type == DatabaseType.MONGODB:
            return await self._optimize_mongodb_query(query_plan)
        elif database_type == DatabaseType.REDIS:
            return await self._optimize_redis_query(query_plan)
        else:
            raise ValueError(f"Unsupported database type for optimization: {database_type}")

    async def _optimize_postgresql_query(self, query_plan: QueryPlan) -> QueryOptimization:
        """Optimize PostgreSQL query"""

        query = query_plan.query
        changes_made = []
        new_indexes = []
        estimated_improvement = 0.0

        try:
            # Parse SQL query
            parsed = sqlparse.parse(query)[0]

            # Optimization 1: Add LIMIT if missing and appropriate
            if not any(token.ttype is Keyword and token.value.upper() == 'LIMIT'
                      for token in parsed.flatten()):
                if query_plan.rows_examined > 1000:
                    optimized_query = f"{query} LIMIT 1000"
                    changes_made.append("Added LIMIT clause to prevent full table scans")
                    estimated_improvement += 0.3
                else:
                    optimized_query = query
            else:
                optimized_query = query

            # Optimization 2: Rewrite subqueries as JOINs when beneficial
            if 'EXISTS' in query.upper() or 'IN' in query.upper():
                optimized_query, join_changes = self._rewrite_subqueries_as_joins(optimized_query)
                changes_made.extend(join_changes)
                if join_changes:
                    estimated_improvement += 0.4

            # Optimization 3: Optimize JOIN order
            if 'JOIN' in optimized_query.upper():
                optimized_query, join_changes = self._optimize_join_order(optimized_query, query_plan)
                changes_made.extend(join_changes)
                if join_changes:
                    estimated_improvement += 0.2

            # Optimization 4: Suggest composite indexes
            if query_plan.bottlenecks:
                index_suggestions = self._suggest_composite_indexes(query_plan)
                new_indexes.extend(index_suggestions)
                estimated_improvement += 0.5 * len(index_suggestions)

            # Optimization 5: Parameterize query for prepared statements
            parameterized_query = self._parameterize_query(optimized_query)

            return QueryOptimization(
                original_query=query,
                optimized_query=optimized_query,
                estimated_improvement=min(estimated_improvement, 0.95),  # Cap at 95%
                changes_made=changes_made,
                new_indexes=new_indexes,
                parameterized_query=parameterized_query
            )

        except Exception as e:
            logger.error(f"PostgreSQL query optimization failed: {e}")
            return QueryOptimization(
                original_query=query,
                optimized_query=query,
                estimated_improvement=0.0,
                changes_made=[f"Optimization failed: {str(e)}"],
                new_indexes=[],
                parameterized_query=query
            )

    async def _optimize_mongodb_query(self, query_plan: QueryPlan) -> QueryOptimization:
        """Optimize MongoDB query"""

        query = query_plan.query
        changes_made = []
        new_indexes = []
        estimated_improvement = 0.0

        try:
            # Parse MongoDB query
            query_dict = self._parse_mongodb_query(query)

            # Optimization 1: Add projection to limit returned fields
            if 'projection' not in query_dict:
                query_dict['projection'] = {'_id': 0}
                changes_made.append("Added projection to limit returned fields")
                estimated_improvement += 0.2

            # Optimization 2: Add sort optimization
            if 'sort' in query_dict:
                sort_fields = list(query_dict['sort'].keys())
                if sort_fields:
                    new_indexes.append({
                        'collection': self._extract_mongodb_collection(query),
                        'fields': [(field, 1) for field in sort_fields],
                        'type': 'sort_index'
                    })
                    estimated_improvement += 0.4

            # Optimization 3: Optimize filter for index usage
            if 'filter' in query_dict:
                filter_dict = query_dict['filter']
                if '$or' in filter_dict:
                    # Split $or into multiple queries when possible
                    changes_made.append("Consider splitting $or query into multiple queries")
                    estimated_improvement += 0.3

                # Suggest indexes on filter fields
                filter_fields = self._extract_filter_fields(filter_dict)
                if filter_fields:
                    new_indexes.append({
                        'collection': self._extract_mongodb_collection(query),
                        'fields': [(field, 1) for field in filter_fields],
                        'type': 'filter_index'
                    })
                    estimated_improvement += 0.5

            # Generate optimized query
            optimized_query = json.dumps(query_dict, indent=2)

            return QueryOptimization(
                original_query=query,
                optimized_query=optimized_query,
                estimated_improvement=min(estimated_improvement, 0.95),
                changes_made=changes_made,
                new_indexes=new_indexes,
                parameterized_query=optimized_query
            )

        except Exception as e:
            logger.error(f"MongoDB query optimization failed: {e}")
            return QueryOptimization(
                original_query=query,
                optimized_query=query,
                estimated_improvement=0.0,
                changes_made=[f"Optimization failed: {str(e)}"],
                new_indexes=[],
                parameterized_query=query
            )

    async def _optimize_redis_query(self, query_plan: QueryPlan) -> QueryOptimization:
        """Optimize Redis query"""

        query = query_plan.query
        changes_made = []
        estimated_improvement = 0.0

        try:
            command_parts = query.split()
            command = command_parts[0].upper()

            optimized_query = query

            # Optimization 1: Use pipelines for multiple operations
            if command in ['GET', 'SET', 'HGET', 'HSET']:
                changes_made.append("Consider using Redis pipelines for batch operations")
                estimated_improvement += 0.3

            # Optimization 2: Use appropriate data structures
            if command == 'KEYS':
                optimized_query = query.replace('KEYS', 'SCAN')
                changes_made.append("Replaced KEYS with SCAN for better performance")
                estimated_improvement += 0.8

            # Optimization 3: Use Lua scripts for complex operations
            if len(command_parts) > 3:
                changes_made.append("Consider using Lua scripts for complex operations")
                estimated_improvement += 0.4

            return QueryOptimization(
                original_query=query,
                optimized_query=optimized_query,
                estimated_improvement=estimated_improvement,
                changes_made=changes_made,
                new_indexes=[],
                parameterized_query=optimized_query
            )

        except Exception as e:
            logger.error(f"Redis query optimization failed: {e}")
            return QueryOptimization(
                original_query=query,
                optimized_query=query,
                estimated_improvement=0.0,
                changes_made=[f"Optimization failed: {str(e)}"],
                new_indexes=[],
                parameterized_query=query
            )

    def _extract_postgresql_indexes(self, plan_data: Dict[str, Any]) -> List[str]:
        """Extract indexes used from PostgreSQL plan"""
        indexes = []

        def traverse_plan(node):
            if isinstance(node, dict):
                if 'Relation Name' in node:
                    relation_name = node['Relation Name']
                    if 'Index Name' in node:
                        indexes.append(f"{relation_name}.{node['Index Name']}")

                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse_plan(value)
            elif isinstance(node, list):
                for item in node:
                    traverse_plan(item)

        traverse_plan(plan_data)
        return indexes

    def _identify_postgresql_bottlenecks(self, plan_data: Dict[str, Any], execution_time: float) -> List[str]:
        """Identify performance bottlenecks in PostgreSQL plan"""
        bottlenecks = []

        def traverse_plan(node):
            if isinstance(node, dict):
                # Check for sequential scans
                if node.get('Node Type') == 'Seq Scan':
                    if node.get('Plan Rows', 0) > 1000:
                        bottlenecks.append(f"Sequential scan on {node.get('Relation Name', 'unknown table')} - consider adding index")

                # Check for hash joins without proper indexes
                if node.get('Node Type') == 'Hash Join':
                    if node.get('Actual Rows', 0) > 10000:
                        bottlenecks.append("Large hash join - ensure proper indexes on join columns")

                # Check for sort operations
                if node.get('Node Type') == 'Sort':
                    if node.get('Plan Rows', 0) > 10000:
                        bottlenecks.append("Large sort operation - consider adding index for ORDER BY")

                # Check nested loops
                if node.get('Node Type') == 'Nested Loop':
                    if node.get('Actual Rows', 0) > 1000:
                        bottlenecks.append("Nested loop with many rows - consider query rewrite")

                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse_plan(value)
            elif isinstance(node, list):
                for item in node:
                    traverse_plan(item)

        traverse_plan(plan_data)

        # Add execution time bottleneck
        if execution_time > self.SLOW_QUERY_THRESHOLD:
            bottlenecks.append(f"Slow execution time: {execution_time:.2f}ms")

        return bottlenecks

    def _generate_postgresql_recommendations(self, plan_data: Dict[str, Any],
                                          bottlenecks: List[str], query: str) -> List[str]:
        """Generate optimization recommendations for PostgreSQL"""
        recommendations = []

        # Analyze query structure
        if 'JOIN' in query.upper():
            recommendations.append("Ensure foreign key columns are indexed")

        if 'ORDER BY' in query.upper():
            recommendations.append("Consider adding indexes on ORDER BY columns")

        if 'WHERE' in query.upper():
            recommendations.append("Ensure WHERE clause columns are indexed")

        # Analyze bottlenecks
        for bottleneck in bottlenecks:
            if 'Sequential scan' in bottleneck:
                recommendations.append("Add appropriate indexes to avoid full table scans")
            elif 'Hash join' in bottleneck:
                recommendations.append("Consider increasing work_mem for larger hash joins")
            elif 'Sort operation' in bottleneck:
                recommendations.append("Add index to support ORDER BY without sorting")

        # General recommendations
        if not bottlenecks and plan_data.get('Total Cost', 0) > self.HIGH_COST_THRESHOLD:
            recommendations.append("Consider query rewriting or partitioning for large tables")

        return recommendations

    def _extract_mongodb_collection(self, query: str) -> Optional[str]:
        """Extract collection name from MongoDB query"""
        try:
            # Try to parse as JSON first
            if query.strip().startswith('{'):
                query_dict = json.loads(query)
                return query_dict.get('collection', 'unknown')
            else:
                # Extract from common patterns
                patterns = [
                    r'collection\("([^"]+)"\)',
                    r'\.([a-zA-Z_][a-zA-Z0-9_]*)\.',
                    r'collection\s*=\s*["\']([^"\']+)["\']'
                ]

                for pattern in patterns:
                    match = re.search(pattern, query)
                    if match:
                        return match.group(1)

                return 'unknown'
        except:
            return 'unknown'

    def _parse_mongodb_query(self, query: str) -> Dict[str, Any]:
        """Parse MongoDB query string into components"""
        try:
            if query.strip().startswith('{'):
                return json.loads(query)
            else:
                # Basic parsing for non-JSON queries
                return {
                    'collection': self._extract_mongodb_collection(query),
                    'filter': {},
                    'options': {}
                }
        except:
            return {
                'collection': 'unknown',
                'filter': {},
                'options': {}
            }

    def _extract_mongodb_indexes(self, winning_plan: Dict[str, Any]) -> List[str]:
        """Extract indexes used from MongoDB plan"""
        indexes = []

        def traverse_plan(node):
            if isinstance(node, dict):
                if 'indexName' in node:
                    indexes.append(node['indexName'])

                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse_plan(value)
            elif isinstance(node, list):
                for item in node:
                    traverse_plan(item)

        traverse_plan(winning_plan)
        return indexes

    def _identify_mongodb_bottlenecks(self, explain_result: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks in MongoDB plan"""
        bottlenecks = []

        execution_stats = explain_result.get('executionStats', {})

        # Check for collection scans
        if execution_stats.get('totalDocsExamined', 0) > execution_stats.get('nReturned', 0) * 10:
            bottlenecks.append("Collection scan detected - consider adding indexes")

        # Check for slow execution
        execution_time = execution_stats.get('executionTimeMillis', 0)
        if execution_time > self.SLOW_QUERY_THRESHOLD:
            bottlenecks.append(f"Slow execution time: {execution_time}ms")

        # Check for in-memory sorting
        if execution_stats.get('totalDocsExamined', 0) > 10000:
            bottlenecks.append("Large document set examined - consider query optimization")

        return bottlenecks

    def _generate_mongodb_recommendations(self, explain_result: Dict[str, Any],
                                        query_dict: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations for MongoDB"""
        recommendations = []

        execution_stats = explain_result.get('executionStats', {})

        # Check index usage
        if execution_stats.get('totalDocsExamined', 0) > execution_stats.get('nReturned', 0):
            recommendations.append("Add indexes on query filter fields")

        # Check for $or usage
        if 'filter' in query_dict and '$or' in str(query_dict['filter']):
            recommendations.append("Consider splitting $or queries or using $in")

        # Check for sort without index
        if 'sort' in query_dict and execution_stats.get('executionTimeMillis', 0) > 100:
            recommendations.append("Add indexes to support sort operations")

        # Check for large result sets
        if execution_stats.get('nReturned', 0) > 1000 and 'limit' not in query_dict:
            recommendations.append("Consider adding limit() to reduce result set size")

        return recommendations

    def _rewrite_subqueries_as_joins(self, query: str) -> Tuple[str, List[str]]:
        """Rewrite subqueries as JOINs for better performance"""
        changes = []

        # This is a simplified implementation
        # In practice, you'd use more sophisticated SQL parsing

        if 'EXISTS' in query.upper() or 'IN' in query.upper():
            # Basic pattern detection
            changes.append("Consider rewriting subquery as JOIN")

        return query, changes

    def _optimize_join_order(self, query: str, query_plan: QueryPlan) -> Tuple[str, List[str]]:
        """Optimize JOIN order based on table sizes"""
        changes = []

        # This would analyze table statistics and reorder JOINs
        # Simplified implementation for demonstration

        if 'JOIN' in query.upper():
            changes.append("JOIN order optimization recommended")

        return query, changes

    def _suggest_composite_indexes(self, query_plan: QueryPlan) -> List[Dict[str, Any]]:
        """Suggest composite indexes for query optimization"""
        indexes = []

        # Analyze query to suggest composite indexes
        query = query_plan.query.upper()

        # Find WHERE clause columns
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', query)
        if where_match:
            where_clause = where_match.group(1)
            columns = re.findall(r'(\w+)\s*[=<>!]', where_clause)
            if len(columns) > 1:
                indexes.append({
                    'table': 'unknown',  # Would be extracted from query
                    'columns': columns,
                    'type': 'composite',
                    'reason': 'Multi-column WHERE clause'
                })

        return indexes

    def _parameterize_query(self, query: str) -> str:
        """Convert query to parameterized form for prepared statements"""
        # Basic parameterization - replace literal values with parameters
        parameterized = re.sub(r"'([^']*)'", "$1", query)
        parameterized = re.sub(r'\b(\d+)\b', "$1", parameterized)
        return parameterized

    def _extract_filter_fields(self, filter_dict: Dict[str, Any]) -> List[str]:
        """Extract field names from MongoDB filter"""
        fields = []

        def extract_fields(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if not key.startswith('$'):
                        field_name = f"{prefix}.{key}" if prefix else key
                        fields.append(field_name)
                    elif key in ['$eq', '$gt', '$lt', '$gte', '$lte', '$in']:
                        if prefix:
                            fields.append(prefix)
                    elif isinstance(value, (dict, list)):
                        extract_fields(value, key)

        extract_fields(filter_dict)
        return list(set(fields))

    async def benchmark_query_performance(self, queries: List[str],
                                        database_type: DatabaseType,
                                        connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Benchmark multiple queries and compare performance"""

        results = {
            'database_type': database_type.value,
            'total_queries': len(queries),
            'benchmarks': [],
            'summary': {}
        }

        for query in queries:
            try:
                # Analyze original query
                plan = await self.analyze_query_plan(query, database_type, connection_params)

                # Get optimized query
                optimization = await self.optimize_query(plan)

                # Benchmark optimized query if different
                optimized_plan = None
                if optimization.optimized_query != query:
                    optimized_plan = await self.analyze_query_plan(
                        optimization.optimized_query, database_type, connection_params
                    )

                benchmark = {
                    'query': query,
                    'original_plan': asdict(plan),
                    'optimization': asdict(optimization)
                }

                if optimized_plan:
                    benchmark['optimized_plan'] = asdict(optimized_plan)
                    improvement = (plan.execution_time - optimized_plan.execution_time) / plan.execution_time
                    benchmark['actual_improvement'] = improvement

                results['benchmarks'].append(benchmark)

            except Exception as e:
                logger.error(f"Error benchmarking query: {e}")
                results['benchmarks'].append({
                    'query': query,
                    'error': str(e)
                })

        # Calculate summary statistics
        successful_benchmarks = [b for b in results['benchmarks'] if 'error' not in b]
        if successful_benchmarks:
            avg_original_time = sum(b['original_plan']['execution_time'] for b in successful_benchmarks) / len(successful_benchmarks)
            results['summary'] = {
                'average_execution_time': avg_original_time,
                'queries_analyzed': len(successful_benchmarks),
                'optimizations_suggested': sum(1 for b in successful_benchmarks if b['optimization']['changes_made'])
            }

        return results

    def generate_query_signatures(self, queries: List[str]) -> Dict[str, int]:
        """Generate signatures for query pattern analysis"""
        signatures = {}

        for query in queries:
            # Create normalized signature by removing literals
            signature = re.sub(r"'[^']*'", "'?'", query)  # Replace string literals
            signature = re.sub(r'\b\d+\b', "?", signature)  # Replace numbers
            signature = re.sub(r'\s+', " ", signature).strip()  # Normalize whitespace

            signatures[signature] = signatures.get(signature, 0) + 1

        return signatures

    async def get_optimization_report(self, database_type: DatabaseType,
                                    connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""

        report = {
            'database_type': database_type.value,
            'generated_at': time.time(),
            'optimization_stats': {
                'total_queries_analyzed': len(self.optimization_history),
                'average_improvement': 0.0,
                'slow_queries': 0,
                'index_recommendations': len(self.index_recommendations)
            },
            'top_bottlenecks': [],
            'recommendations': [],
            'performance_trends': {}
        }

        if self.optimization_history:
            # Calculate statistics
            improvements = [opt.get('estimated_improvement', 0) for opt in self.optimization_history]
            report['optimization_stats']['average_improvement'] = sum(improvements) / len(improvements)

            slow_queries = [h for h in self.optimization_history if h.get('original_execution_time', 0) > self.SLOW_QUERY_THRESHOLD]
            report['optimization_stats']['slow_queries'] = len(slow_queries)

            # Analyze bottlenecks
            bottleneck_counts = defaultdict(int)
            for history_item in self.optimization_history:
                for bottleneck in history_item.get('bottlenecks', []):
                    bottleneck_counts[bottleneck] += 1

            report['top_bottlenecks'] = sorted(
                bottleneck_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

        return report

# Example usage and testing
async def main():
    """Example usage of the QueryOptimizer"""

    optimizer = QueryOptimizer()

    # PostgreSQL example
    pg_connection_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'test_db'
    }

    slow_query = """
    SELECT u.name, p.title, c.content
    FROM users u
    JOIN posts p ON u.id = p.user_id
    JOIN comments c ON p.id = c.post_id
    WHERE u.created_at > '2023-01-01'
    ORDER BY p.created_at DESC
    """

    try:
        # Analyze query
        plan = await optimizer.analyze_query_plan(
            slow_query, DatabaseType.POSTGRESQL, pg_connection_params
        )

        print(f"Query execution time: {plan.execution_time:.2f}ms")
        print(f"Bottlenecks: {plan.bottlenecks}")
        print(f"Recommendations: {plan.recommendations}")

        # Optimize query
        optimization = await optimizer.optimize_query(plan)

        print(f"\nOptimization changes: {optimization.changes_made}")
        print(f"Estimated improvement: {optimization.estimated_improvement:.1%}")
        print(f"Optimized query:\n{optimization.optimized_query}")

        # Generate report
        report = await optimizer.get_optimization_report(DatabaseType.POSTGRESQL, pg_connection_params)
        print(f"\nOptimization report: {json.dumps(report, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())