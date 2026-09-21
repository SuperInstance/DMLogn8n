#!/usr/bin/env python3
"""
Intelligent Index Creation and Management System
Automatically manages database indexes for optimal query performance across multiple database types.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, Counter
import re
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
import pymongo
from asyncpg import create_pool
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexType(Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    SPGIST = "spgist"
    BRIN = "brin"
    TEXT = "text"
    COMPOSITE = "composite"
    PARTIAL = "partial"
    UNIQUE = "unique"
    FULLTEXT = "fulltext"

class IndexStatus(Enum):
    ACTIVE = "active"
    BUILDING = "building"
    INVALID = "invalid"
    UNUSED = "unused"
    DUPLICATE = "duplicate"

@dataclass
class IndexDefinition:
    name: str
    table: str
    columns: List[str]
    index_type: IndexType
    status: IndexStatus
    size_bytes: int
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    selectivity: float
    cardinality: int
    conditions: Optional[str] = None  # For partial indexes
    is_unique: bool = False
    is_concurrent: bool = True

@dataclass
class IndexRecommendation:
    table: str
    columns: List[str]
    index_type: IndexType
    estimated_impact: float
    reason: str
    query_patterns: List[str]
    priority: int  # 1-10, 1 being highest
    estimated_size_mb: float
    conditions: Optional[str] = None

@dataclass
class IndexAnalysisResult:
    total_indexes: int
    unused_indexes: List[IndexDefinition]
    duplicate_indexes: List[Tuple[IndexDefinition, List[IndexDefinition]]]
    recommended_indexes: List[IndexRecommendation]
    index_efficiency_score: float
    storage_waste_mb: float

class IndexManager:
    """Intelligent index management system for optimal database performance"""

    def __init__(self):
        self.index_cache = {}
        self.query_history = defaultdict(list)
        self.index_stats = {}
        self.recommendation_history = []

        # Configuration thresholds
        self.UNUSED_INDEX_THRESHOLD_DAYS = 30
        self.LOW_SELECTIVITY_THRESHOLD = 0.1
        self.HIGH_CARDINALITY_THRESHOLD = 10000
        self.INDEX_SIZE_LIMIT_MB = 1000
        self.RECOMMENDATION_PRIORITY_THRESHOLD = 7

        # Performance targets
        self.TARGET_INDEX_EFFICIENCY = 0.8
        self.MAX_UNUSED_INDEXES = 5
        self.TARGET_INDEX_COVERAGE = 0.95

    async def analyze_existing_indexes(self, database_type: str,
                                      connection_params: Dict[str, Any]) -> Dict[str, List[IndexDefinition]]:
        """Analyze all existing indexes in the database"""

        try:
            if database_type.lower() == 'postgresql':
                return await self._analyze_postgresql_indexes(connection_params)
            elif database_type.lower() == 'mongodb':
                return await self._analyze_mongodb_indexes(connection_params)
            else:
                raise ValueError(f"Unsupported database type: {database_type}")

        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            return {}

    async def _analyze_postgresql_indexes(self, connection_params: Dict[str, Any]) -> Dict[str, List[IndexDefinition]]:
        """Analyze PostgreSQL indexes"""

        indexes_by_table = defaultdict(list)

        try:
            conn = await create_pool(**connection_params)

            async with conn.acquire() as connection:
                # Get comprehensive index information
                query = """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef,
                    indexsize::bigint,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    CASE WHEN indisunique THEN 'unique' ELSE 'non-unique' END as uniqueness,
                    CASE WHEN indisvalid THEN 'valid' ELSE 'invalid' END as validity,
                    pg_stat_get_last_vacuum_time(c.oid) as last_vacuum
                FROM pg_stat_user_indexes
                JOIN pg_class c ON c.relname = indexrelname
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename, indexname;
                """

                rows = await connection.fetch(query)

                for row in rows:
                    # Parse index definition
                    index_def = self._parse_postgresql_index_def(row['indexdef'])

                    # Get column statistics
                    column_stats = await self._get_postgresql_column_stats(
                        connection, row['schemaname'], row['tablename'], index_def['columns']
                    )

                    # Determine index type
                    index_type = self._determine_postgresql_index_type(row['indexdef'])

                    # Determine status
                    status = IndexStatus.ACTIVE
                    if row['validity'] == 'invalid':
                        status = IndexStatus.INVALID
                    elif row['idx_scan'] == 0:
                        status = IndexStatus.UNUSED

                    index = IndexDefinition(
                        name=row['indexname'],
                        table=f"{row['schemaname']}.{row['tablename']}",
                        columns=index_def['columns'],
                        index_type=index_type,
                        status=status,
                        size_bytes=row['indexsize'],
                        created_at=datetime.now(),  # Would get from pg_class
                        last_used=None,  # Would get from stats
                        usage_count=row['idx_scan'],
                        selectivity=column_stats.get('selectivity', 0.0),
                        cardinality=column_stats.get('cardinality', 0),
                        conditions=index_def.get('conditions'),
                        is_unique=row['uniqueness'] == 'unique',
                        is_concurrent='CONCURRENTLY' in row['indexdef']
                    )

                    indexes_by_table[row['tablename']].append(index)

                # Get index usage statistics
                await self._update_postgresql_index_usage(connection, indexes_by_table)

        except Exception as e:
            logger.error(f"PostgreSQL index analysis failed: {e}")
            raise

        return dict(indexes_by_table)

    async def _analyze_mongodb_indexes(self, connection_params: Dict[str, Any]) -> Dict[str, List[IndexDefinition]]:
        """Analyze MongoDB indexes"""

        indexes_by_collection = defaultdict(list)

        try:
            client = pymongo.MongoClient(**connection_params)
            db_name = connection_params.get('database', 'test')
            db = client[db_name]

            # Get all collections
            collections = db.list_collection_names()

            for collection_name in collections:
                collection = db[collection_name]

                # Get index information
                index_info = collection.index_information()

                for index_name, index_details in index_info.items():
                    if index_name == '_id_':  # Skip default _id index
                        continue

                    # Parse index keys
                    columns = []
                    for key, direction in index_details['key']:
                        columns.append(key)

                    # Get index stats
                    stats = db.command("collStats", collection_name, indexDetails=True)
                    index_stats = stats.get('indexDetails', {}).get(index_name, {})

                    # Get usage statistics
                    usage_stats = db.command(
                        "$indexStats",
                        collection=collection_name
                    )

                    usage_count = 0
                    for stat in usage_stats:
                        if stat.get('name') == index_name:
                            usage_count = stat.get('accesses', {}).get('ops', 0)
                            break

                    # Determine index type
                    index_type = self._determine_mongodb_index_type(index_details)

                    # Get collection statistics for selectivity
                    collection_stats = db.command("collStats", collection_name)
                    total_docs = collection_stats.get('count', 0)
                    cardinality = await self._estimate_mongodb_cardinality(
                        collection, columns[0] if columns else None
                    )

                    index = IndexDefinition(
                        name=index_name,
                        table=collection_name,
                        columns=columns,
                        index_type=index_type,
                        status=IndexStatus.ACTIVE if usage_count > 0 else IndexStatus.UNUSED,
                        size_bytes=index_stats.get('size', 0),
                        created_at=datetime.now(),  # Would get from index creation time
                        last_used=None,  # MongoDB doesn't track this directly
                        usage_count=usage_count,
                        selectivity=cardinality / total_docs if total_docs > 0 else 0,
                        cardinality=cardinality,
                        conditions=None,  # MongoDB partial indexes
                        is_unique=index_details.get('unique', False),
                        is_concurrent=True  # MongoDB indexes are built concurrently
                    )

                    indexes_by_collection[collection_name].append(index)

        except Exception as e:
            logger.error(f"MongoDB index analysis failed: {e}")
            raise

        return dict(indexes_by_collection)

    async def recommend_indexes(self, query_patterns: List[Dict[str, Any]],
                              existing_indexes: Dict[str, List[IndexDefinition]],
                              database_type: str) -> List[IndexRecommendation]:
        """Generate index recommendations based on query patterns"""

        recommendations = []

        try:
            if database_type.lower() == 'postgresql':
                recommendations = await self._recommend_postgresql_indexes(
                    query_patterns, existing_indexes
                )
            elif database_type.lower() == 'mongodb':
                recommendations = await self._recommend_mongodb_indexes(
                    query_patterns, existing_indexes
                )

            # Filter and prioritize recommendations
            filtered_recommendations = self._filter_recommendations(recommendations, existing_indexes)
            prioritized_recommendations = self._prioritize_recommendations(filtered_recommendations)

            return prioritized_recommendations

        except Exception as e:
            logger.error(f"Error generating index recommendations: {e}")
            return []

    async def _recommend_postgresql_indexes(self, query_patterns: List[Dict[str, Any]],
                                         existing_indexes: Dict[str, List[IndexDefinition]]) -> List[IndexRecommendation]:
        """Generate PostgreSQL index recommendations"""

        recommendations = []

        # Analyze query patterns
        for pattern in query_patterns:
            query = pattern.get('query', '')
            table = pattern.get('table', '')
            frequency = pattern.get('frequency', 1)
            avg_execution_time = pattern.get('avg_execution_time', 0)

            if not table:
                continue

            # Extract WHERE clause columns
            where_columns = self._extract_where_columns(query)

            # Extract ORDER BY columns
            order_columns = self._extract_order_columns(query)

            # Extract JOIN columns
            join_columns = self._extract_join_columns(query)

            # Generate recommendations for different column combinations
            all_columns = list(set(where_columns + order_columns + join_columns))

            if not all_columns:
                continue

            # Check if index already exists
            existing_table_indexes = existing_indexes.get(table, [])
            existing_index_columns = set()
            for idx in existing_table_indexes:
                existing_index_columns.update(tuple(idx.columns))

            # Single column indexes
            for column in all_columns:
                if tuple([column]) not in existing_index_columns:
                    impact = self._estimate_index_impact(column, frequency, avg_execution_time)

                    recommendation = IndexRecommendation(
                        table=table,
                        columns=[column],
                        index_type=IndexType.BTREE,
                        estimated_impact=impact,
                        reason=f"Frequent WHERE clause on {column}",
                        query_patterns=[query],
                        priority=self._calculate_priority(impact, frequency),
                        estimated_size_mb=self._estimate_index_size(table, [column])
                    )
                    recommendations.append(recommendation)

            # Composite indexes for multi-column queries
            if len(all_columns) > 1:
                # Best column order based on selectivity
                sorted_columns = self._order_columns_by_selectivity(all_columns, existing_indexes)

                for i in range(2, min(4, len(sorted_columns) + 1)):  # 2-3 column indexes
                    column_combo = sorted_columns[:i]

                    if tuple(column_combo) not in existing_index_columns:
                        impact = self._estimate_composite_index_impact(
                            column_combo, frequency, avg_execution_time
                        )

                        recommendation = IndexRecommendation(
                            table=table,
                            columns=column_combo,
                            index_type=IndexType.COMPOSITE,
                            estimated_impact=impact,
                            reason=f"Frequent multi-column query on {', '.join(column_combo)}",
                            query_patterns=[query],
                            priority=self._calculate_priority(impact, frequency),
                            estimated_size_mb=self._estimate_index_size(table, column_combo)
                        )
                        recommendations.append(recommendation)

            # Specialized indexes
            await self._recommend_specialized_indexes(query, table, existing_table_indexes, recommendations)

        return recommendations

    async def _recommend_mongodb_indexes(self, query_patterns: List[Dict[str, Any]],
                                       existing_indexes: Dict[str, List[IndexDefinition]]) -> List[IndexRecommendation]:
        """Generate MongoDB index recommendations"""

        recommendations = []

        for pattern in query_patterns:
            query_doc = pattern.get('query_doc', {})
            collection = pattern.get('collection', '')
            frequency = pattern.get('frequency', 1)
            avg_execution_time = pattern.get('avg_execution_time', 0)

            if not collection:
                continue

            # Extract query fields
            query_fields = self._extract_mongodb_query_fields(query_doc)

            # Extract sort fields
            sort_fields = pattern.get('sort', {}).keys() if pattern.get('sort') else []

            all_fields = list(set(query_fields + list(sort_fields)))

            if not all_fields:
                continue

            # Check existing indexes
            existing_collection_indexes = existing_indexes.get(collection, [])
            existing_index_fields = set()
            for idx in existing_collection_indexes:
                existing_index_fields.update(tuple(idx.columns))

            # Generate recommendations
            for field in all_fields:
                if tuple([field]) not in existing_index_fields:
                    impact = self._estimate_mongodb_index_impact(field, frequency, avg_execution_time)

                    # Determine index type
                    index_type = IndexType.BTREE
                    if pattern.get('text_search'):
                        index_type = IndexType.TEXT
                    elif pattern.get('geo_near'):
                        index_type = IndexType.GIST

                    recommendation = IndexRecommendation(
                        table=collection,
                        columns=[field],
                        index_type=index_type,
                        estimated_impact=impact,
                        reason=f"Frequent query on {field}",
                        query_patterns=[str(query_doc)],
                        priority=self._calculate_priority(impact, frequency),
                        estimated_size_mb=self._estimate_mongodb_index_size(collection, [field])
                    )
                    recommendations.append(recommendation)

            # Compound indexes for multi-field queries
            if len(all_fields) > 1:
                # ESR rule: Equality, Sort, Range
                sorted_fields = self._order_mongodb_fields_esr(all_fields, query_doc, pattern.get('sort', {}))

                if len(sorted_fields) > 1:
                    field_combo = sorted_fields[:min(3, len(sorted_fields))]

                    if tuple(field_combo) not in existing_index_fields:
                        impact = self._estimate_mongodb_composite_impact(field_combo, frequency, avg_execution_time)

                        recommendation = IndexRecommendation(
                            table=collection,
                            columns=field_combo,
                            index_type=IndexType.COMPOSITE,
                            estimated_impact=impact,
                            reason=f"Compound index for multi-field query",
                            query_patterns=[str(query_doc)],
                            priority=self._calculate_priority(impact, frequency),
                            estimated_size_mb=self._estimate_mongodb_index_size(collection, field_combo)
                        )
                        recommendations.append(recommendation)

        return recommendations

    async def create_index(self, recommendation: IndexRecommendation,
                          database_type: str, connection_params: Dict[str, Any],
                          dry_run: bool = False) -> Dict[str, Any]:
        """Create a new index based on recommendation"""

        result = {
            'success': False,
            'index_name': '',
            'execution_time': 0,
            'error': None,
            'dry_run': dry_run
        }

        try:
            start_time = time.time()

            if database_type.lower() == 'postgresql':
                result = await self._create_postgresql_index(
                    recommendation, connection_params, dry_run
                )
            elif database_type.lower() == 'mongodb':
                result = await self._create_mongodb_index(
                    recommendation, connection_params, dry_run
                )

            result['execution_time'] = time.time() - start_time

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            result['error'] = str(e)

        return result

    async def _create_postgresql_index(self, recommendation: IndexRecommendation,
                                     connection_params: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Create PostgreSQL index"""

        result = {'success': False, 'index_name': '', 'error': None}

        try:
            conn = await create_pool(**connection_params)

            async with conn.acquire() as connection:
                # Generate index name
                index_name = f"idx_{recommendation.table.replace('.', '_')}_{'_'.join(recommendation.columns)}"

                # Build CREATE INDEX statement
                sql_parts = ["CREATE"]

                if recommendation.is_unique:
                    sql_parts.append("UNIQUE")

                sql_parts.extend(["INDEX"])

                if recommendation.is_concurrent and not dry_run:
                    sql_parts.append("CONCURRENTLY")

                sql_parts.extend([index_name, f"ON {recommendation.table}"])

                # Add index type
                if recommendation.index_type != IndexType.BTREE:
                    sql_parts.append(f"USING {recommendation.index_type.value}")

                # Add columns
                columns_str = ", ".join(recommendation.columns)
                sql_parts.append(f"({columns_str})")

                # Add conditions for partial index
                if recommendation.conditions:
                    sql_parts.append(f"WHERE {recommendation.conditions}")

                create_sql = " ".join(sql_parts)

                if dry_run:
                    result['success'] = True
                    result['index_name'] = index_name
                    result['sql'] = create_sql
                    logger.info(f"DRY RUN: Would create index: {create_sql}")
                else:
                    async with connection.transaction():
                        await connection.execute(create_sql)

                        result['success'] = True
                        result['index_name'] = index_name
                        logger.info(f"Successfully created index: {index_name}")

        except Exception as e:
            logger.error(f"PostgreSQL index creation failed: {e}")
            result['error'] = str(e)

        return result

    async def _create_mongodb_index(self, recommendation: IndexRecommendation,
                                  connection_params: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Create MongoDB index"""

        result = {'success': False, 'index_name': '', 'error': None}

        try:
            client = pymongo.MongoClient(**connection_params)
            db_name = connection_params.get('database', 'test')
            db = client[db_name]
            collection = db[recommendation.table]

            # Build index specification
            index_spec = {}
            for column in recommendation.columns:
                index_spec[column] = 1  # Ascending order

            # Set index options
            index_options = {
                'name': f"idx_{'_'.join(recommendation.columns)}",
                'background': True
            }

            if recommendation.is_unique:
                index_options['unique'] = True

            if recommendation.conditions:
                index_options['partialFilterExpression'] = json.loads(recommendation.conditions)

            if dry_run:
                result['success'] = True
                result['index_name'] = index_options['name']
                result['spec'] = index_spec
                result['options'] = index_options
                logger.info(f"DRY RUN: Would create MongoDB index: {index_spec} with options {index_options}")
            else:
                # Create index
                index_name = collection.create_index(index_spec, **index_options)

                result['success'] = True
                result['index_name'] = index_name
                logger.info(f"Successfully created MongoDB index: {index_name}")

        except Exception as e:
            logger.error(f"MongoDB index creation failed: {e}")
            result['error'] = str(e)

        return result

    async def drop_unused_indexes(self, database_type: str, connection_params: Dict[str, Any],
                                 dry_run: bool = True) -> Dict[str, Any]:
        """Drop indexes that haven't been used recently"""

        result = {
            'success': False,
            'indexes_dropped': [],
            'space_freed_mb': 0,
            'errors': [],
            'dry_run': dry_run
        }

        try:
            # Analyze existing indexes
            existing_indexes = await self.analyze_existing_indexes(database_type, connection_params)

            # Find unused indexes
            unused_indexes = []
            cutoff_date = datetime.now() - timedelta(days=self.UNUSED_INDEX_THRESHOLD_DAYS)

            for table, indexes in existing_indexes.items():
                for index in indexes:
                    if (index.status == IndexStatus.UNUSED or
                        (index.last_used and index.last_used < cutoff_date) or
                        (index.usage_count == 0 and index.created_at < cutoff_date)):

                        # Don't drop primary key or unique constraints
                        if not self._is_critical_index(index):
                            unused_indexes.append(index)

            total_space_freed = 0

            for index in unused_indexes:
                try:
                    if database_type.lower() == 'postgresql':
                        drop_result = await self._drop_postgresql_index(
                            index, connection_params, dry_run
                        )
                    elif database_type.lower() == 'mongodb':
                        drop_result = await self._drop_mongodb_index(
                            index, connection_params, dry_run
                        )

                    if drop_result['success']:
                        result['indexes_dropped'].append({
                            'name': index.name,
                            'table': index.table,
                            'size_mb': index.size_bytes / (1024 * 1024)
                        })
                        total_space_freed += index.size_bytes / (1024 * 1024)

                except Exception as e:
                    result['errors'].append(f"Error dropping {index.name}: {str(e)}")

            result['success'] = True
            result['space_freed_mb'] = total_space_freed

        except Exception as e:
            logger.error(f"Error dropping unused indexes: {e}")
            result['errors'].append(str(e))

        return result

    async def _drop_postgresql_index(self, index: IndexDefinition, connection_params: Dict[str, Any],
                                   dry_run: bool) -> Dict[str, Any]:
        """Drop PostgreSQL index"""

        result = {'success': False, 'error': None}

        try:
            conn = await create_pool(**connection_params)

            async with conn.acquire() as connection:
                drop_sql = f"DROP INDEX IF EXISTS {index.name}"

                if dry_run:
                    logger.info(f"DRY RUN: Would drop index: {drop_sql}")
                    result['success'] = True
                else:
                    async with connection.transaction():
                        await connection.execute(drop_sql)
                        logger.info(f"Dropped index: {index.name}")
                        result['success'] = True

        except Exception as e:
            logger.error(f"Error dropping PostgreSQL index {index.name}: {e}")
            result['error'] = str(e)

        return result

    async def _drop_mongodb_index(self, index: IndexDefinition, connection_params: Dict[str, Any],
                                 dry_run: bool) -> Dict[str, Any]:
        """Drop MongoDB index"""

        result = {'success': False, 'error': None}

        try:
            client = pymongo.MongoClient(**connection_params)
            db_name = connection_params.get('database', 'test')
            db = client[db_name]
            collection = db[index.table]

            if dry_run:
                logger.info(f"DRY RUN: Would drop MongoDB index: {index.name}")
                result['success'] = True
            else:
                collection.drop_index(index.name)
                logger.info(f"Dropped MongoDB index: {index.name}")
                result['success'] = True

        except Exception as e:
            logger.error(f"Error dropping MongoDB index {index.name}: {e}")
            result['error'] = str(e)

        return result

    async def rebuild_indexes(self, database_type: str, connection_params: Dict[str, Any],
                            tables: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Rebuild fragmented indexes for better performance"""

        result = {
            'success': False,
            'indexes_rebuilt': [],
            'errors': [],
            'dry_run': dry_run
        }

        try:
            if database_type.lower() == 'postgresql':
                result = await self._rebuild_postgresql_indexes(
                    connection_params, tables, dry_run
                )
            elif database_type.lower() == 'mongodb':
                result = await self._rebuild_mongodb_indexes(
                    connection_params, tables, dry_run
                )

        except Exception as e:
            logger.error(f"Error rebuilding indexes: {e}")
            result['errors'].append(str(e))

        return result

    async def _rebuild_postgresql_indexes(self, connection_params: Dict[str, Any],
                                        tables: Optional[List[str]], dry_run: bool) -> Dict[str, Any]:
        """Rebuild PostgreSQL indexes using REINDEX"""

        result = {'success': False, 'indexes_rebuilt': [], 'errors': []}

        try:
            conn = await create_pool(**connection_params)

            async with conn.acquire() as connection:
                if tables:
                    # Rebuild indexes for specific tables
                    for table in tables:
                        try:
                            reindex_sql = f"REINDEX TABLE {table}"

                            if dry_run:
                                logger.info(f"DRY RUN: Would rebuild indexes for table: {table}")
                                result['indexes_rebuilt'].append({'table': table})
                            else:
                                async with connection.transaction():
                                    await connection.execute(reindex_sql)
                                    logger.info(f"Rebuilt indexes for table: {table}")
                                    result['indexes_rebuilt'].append({'table': table})

                        except Exception as e:
                            result['errors'].append(f"Error rebuilding {table}: {str(e)}")
                else:
                    # Rebuild all indexes in database
                    reindex_sql = "REINDEX DATABASE"

                    if dry_run:
                        logger.info("DRY RUN: Would rebuild all database indexes")
                        result['success'] = True
                    else:
                        async with connection.transaction():
                            await connection.execute(reindex_sql)
                            logger.info("Rebuilt all database indexes")
                            result['success'] = True

        except Exception as e:
            logger.error(f"PostgreSQL index rebuild failed: {e}")
            result['errors'].append(str(e))

        return result

    async def _rebuild_mongodb_indexes(self, connection_params: Dict[str, Any],
                                     tables: Optional[List[str]], dry_run: bool) -> Dict[str, Any]:
        """Rebuild MongoDB indexes by dropping and recreating"""

        result = {'success': False, 'indexes_rebuilt': [], 'errors': []}

        try:
            client = pymongo.MongoClient(**connection_params)
            db_name = connection_params.get('database', 'test')
            db = client[db_name]

            collections = tables if tables else db.list_collection_names()

            for collection_name in collections:
                try:
                    collection = db[collection_name]

                    # Get existing indexes
                    index_info = collection.index_information()

                    for index_name, index_details in index_info.items():
                        if index_name == '_id_':  # Skip default index
                            continue

                        # Rebuild index
                        if dry_run:
                            logger.info(f"DRY RUN: Would rebuild MongoDB index: {index_name}")
                            result['indexes_rebuilt'].append({
                                'collection': collection_name,
                                'index': index_name
                            })
                        else:
                            # Drop and recreate index
                            collection.drop_index(index_name)

                            # Recreate with same definition
                            collection.create_index(
                                index_details['key'],
                                name=index_name,
                                **{k: v for k, v in index_details.items() if k != 'key'}
                            )

                            logger.info(f"Rebuilt MongoDB index: {index_name}")
                            result['indexes_rebuilt'].append({
                                'collection': collection_name,
                                'index': index_name
                            })

                except Exception as e:
                    result['errors'].append(f"Error rebuilding {collection_name}: {str(e)}")

            if result['indexes_rebuilt']:
                result['success'] = True

        except Exception as e:
            logger.error(f"MongoDB index rebuild failed: {e}")
            result['errors'].append(str(e))

        return result

    def _parse_postgresql_index_def(self, index_def: str) -> Dict[str, Any]:
        """Parse PostgreSQL index definition"""

        result = {
            'columns': [],
            'conditions': None,
            'type': 'btree'
        }

        # Extract columns
        column_match = re.search(r'\(([^)]+)\)', index_def)
        if column_match:
            columns_str = column_match.group(1)
            result['columns'] = [col.strip() for col in columns_str.split(',')]

        # Extract conditions for partial indexes
        where_match = re.search(r'WHERE\s+(.+)$', index_def, re.IGNORECASE)
        if where_match:
            result['conditions'] = where_match.group(1).strip()

        # Extract index type
        type_match = re.search(r'USING\s+(\w+)', index_def, re.IGNORECASE)
        if type_match:
            result['type'] = type_match.group(1).lower()

        return result

    def _determine_postgresql_index_type(self, index_def: str) -> IndexType:
        """Determine PostgreSQL index type from definition"""

        if 'USING GIN' in index_def.upper():
            return IndexType.GIN
        elif 'USING GIST' in index_def.upper():
            return IndexType.GIST
        elif 'USING HASH' in index_def.upper():
            return IndexType.HASH
        elif 'USING BRIN' in index_def.upper():
            return IndexType.BRIN
        elif 'USING SPGIST' in index_def.upper():
            return IndexType.SPGIST
        else:
            return IndexType.BTREE

    def _determine_mongodb_index_type(self, index_details: Dict[str, Any]) -> IndexType:
        """Determine MongoDB index type from definition"""

        if 'textIndexVersion' in index_details:
            return IndexType.TEXT
        elif '2dsphere' in str(index_details.get('key', [])):
            return IndexType.GIST
        elif 'hashed' in str(index_details.get('key', [])):
            return IndexType.HASH
        else:
            return IndexType.BTREE

    def _extract_where_columns(self, query: str) -> List[str]:
        """Extract columns from WHERE clause"""
        columns = []

        # Find WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', query, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)

            # Extract column names from conditions
            column_matches = re.findall(r'\b(\w+)\s*[=<>!]', where_clause)
            columns.extend(column_matches)

            # Extract from IN clauses
            in_matches = re.findall(r'\b(\w+)\s+IN\s*\(', where_clause, re.IGNORECASE)
            columns.extend(in_matches)

        return list(set(columns))

    def _extract_order_columns(self, query: str) -> List[str]:
        """Extract columns from ORDER BY clause"""
        columns = []

        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', query, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            column_matches = re.findall(r'\b(\w+)\b', order_clause)
            columns.extend(column_matches)

        return list(set(columns))

    def _extract_join_columns(self, query: str) -> List[str]:
        """Extract columns from JOIN conditions"""
        columns = []

        # Find JOIN conditions
        join_matches = re.findall(r'JOIN\s+\w+\s+ON\s+(.+?)(?:\s+JOIN|$)', query, re.IGNORECASE)
        for join_condition in join_matches:
            column_matches = re.findall(r'\b(\w+)\.\b(\w+)\b', join_condition)
            for table, column in column_matches:
                columns.append(column)

        return list(set(columns))

    def _estimate_index_impact(self, column: str, frequency: int, avg_execution_time: float) -> float:
        """Estimate performance impact of creating an index"""

        # Base impact calculation
        base_impact = min(frequency * avg_execution_time / 1000, 0.8)

        # Adjust based on column characteristics
        if column.lower().endswith(('_id', 'id')):
            base_impact *= 1.2  # ID columns benefit more
        elif column.lower().endswith(('_at', '_date', '_time')):
            base_impact *= 0.9  # Date columns have moderate benefit

        return min(base_impact, 0.95)

    def _calculate_priority(self, impact: float, frequency: int) -> int:
        """Calculate priority for index recommendation"""

        if impact > 0.7 and frequency > 100:
            return 1  # Highest priority
        elif impact > 0.5 and frequency > 50:
            return 3
        elif impact > 0.3 and frequency > 20:
            return 5
        elif impact > 0.2:
            return 7
        else:
            return 10  # Lowest priority

    def _filter_recommendations(self, recommendations: List[IndexRecommendation],
                              existing_indexes: Dict[str, List[IndexDefinition]]) -> List[IndexRecommendation]:
        """Filter and deduplicate recommendations"""

        filtered = []
        seen_combinations = set()

        for rec in recommendations:
            # Create unique key for table+columns combination
            key = (rec.table, tuple(rec.columns))

            if key not in seen_combinations and rec.estimated_impact > 0.1:
                seen_combinations.add(key)
                filtered.append(rec)

        return filtered

    def _prioritize_recommendations(self, recommendations: List[IndexRecommendation]) -> List[IndexRecommendation]:
        """Sort recommendations by priority and impact"""

        return sorted(
            recommendations,
            key=lambda x: (x.priority, -x.estimated_impact)
        )

    def _is_critical_index(self, index: IndexDefinition) -> bool:
        """Check if index is critical and should not be dropped"""

        # Don't drop primary key indexes
        if index.name.lower() in ['primary', 'pkey'] or 'primary' in index.name.lower():
            return True

        # Don't drop unique constraints
        if index.is_unique:
            return True

        # Don't drop indexes on foreign key columns
        if any(col.lower().endswith('_id') for col in index.columns):
            return True

        return False

    # Additional helper methods would be implemented here...
    async def _get_postgresql_column_stats(self, connection, schema: str, table: str, columns: List[str]) -> Dict[str, Any]:
        """Get column statistics for PostgreSQL"""
        return {'selectivity': 0.5, 'cardinality': 1000}  # Simplified

    def _order_columns_by_selectivity(self, columns: List[str], existing_indexes: Dict[str, List[IndexDefinition]]) -> List[str]:
        """Order columns by selectivity for optimal index performance"""
        return columns  # Simplified

    def _estimate_index_size(self, table: str, columns: List[str]) -> float:
        """Estimate index size in MB"""
        return len(columns) * 10.0  # Simplified

    async def _update_postgresql_index_usage(self, connection, indexes_by_table: Dict[str, List[IndexDefinition]]):
        """Update PostgreSQL index usage statistics"""
        pass  # Implementation would update last_used and usage_count

    async def _recommend_specialized_indexes(self, query: str, table: str, existing_indexes: List[IndexDefinition], recommendations: List[IndexRecommendation]):
        """Recommend specialized indexes (full-text, geometric, etc.)"""
        pass  # Implementation for specialized index types

    def _estimate_composite_index_impact(self, columns: List[str], frequency: int, avg_execution_time: float) -> float:
        """Estimate impact of composite index"""
        return self._estimate_index_impact(columns[0], frequency, avg_execution_time) * 1.2

    def _extract_mongodb_query_fields(self, query_doc: Dict[str, Any]) -> List[str]:
        """Extract fields from MongoDB query document"""
        return list(query_doc.keys()) if isinstance(query_doc, dict) else []

    def _estimate_mongodb_index_impact(self, field: str, frequency: int, avg_execution_time: float) -> float:
        """Estimate MongoDB index impact"""
        return self._estimate_index_impact(field, frequency, avg_execution_time)

    def _estimate_mongodb_composite_impact(self, fields: List[str], frequency: int, avg_execution_time: float) -> float:
        """Estimate MongoDB composite index impact"""
        return self._estimate_index_impact(fields[0], frequency, avg_execution_time) * 1.3

    def _order_mongodb_fields_esr(self, fields: List[str], query_doc: Dict[str, Any], sort_doc: Dict[str, Any]) -> List[str]:
        """Order MongoDB fields using ESR rule (Equality, Sort, Range)"""
        equality_fields = []
        sort_fields = []
        range_fields = []

        for field in fields:
            if field in query_doc and isinstance(query_doc[field], (str, int, bool)):
                equality_fields.append(field)
            elif field in sort_doc:
                sort_fields.append(field)
            else:
                range_fields.append(field)

        return equality_fields + sort_fields + range_fields

    def _estimate_mongodb_index_size(self, collection: str, fields: List[str]) -> float:
        """Estimate MongoDB index size in MB"""
        return len(fields) * 8.0  # Simplified

    async def _estimate_mongodb_cardinality(self, collection, field: Optional[str]) -> int:
        """Estimate cardinality for MongoDB field"""
        return 1000  # Simplified

# Example usage
async def main():
    """Example usage of the IndexManager"""

    manager = IndexManager()

    # PostgreSQL example
    pg_connection_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'test_db'
    }

    try:
        # Analyze existing indexes
        existing_indexes = await manager.analyze_existing_indexes('postgresql', pg_connection_params)
        print(f"Found indexes for {len(existing_indexes)} tables")

        # Sample query patterns
        query_patterns = [
            {
                'query': 'SELECT * FROM users WHERE email = ?',
                'table': 'users',
                'frequency': 1000,
                'avg_execution_time': 150
            },
            {
                'query': 'SELECT * FROM orders WHERE user_id = ? AND created_at > ? ORDER BY created_at DESC',
                'table': 'orders',
                'frequency': 500,
                'avg_execution_time': 200
            }
        ]

        # Generate recommendations
        recommendations = await manager.recommend_indexes(query_patterns, existing_indexes, 'postgresql')
        print(f"Generated {len(recommendations)} index recommendations")

        for rec in recommendations[:3]:  # Show top 3
            print(f"Recommendation: {rec.table}({', '.join(rec.columns)}) - Impact: {rec.estimated_impact:.1%}")

        # Create an index (dry run)
        if recommendations:
            result = await manager.create_index(recommendations[0], 'postgresql', pg_connection_params, dry_run=True)
            print(f"Index creation result: {result}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())