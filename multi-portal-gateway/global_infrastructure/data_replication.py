#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure - Cross-Region Data Synchronization
Provides multi-region data replication, synchronization, and consistency management
"""

import asyncio
import json
import logging
import time
import hashlib
import uuid
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import aiofiles
import boto3
from botocore.exceptions import ClientError
import redis
import psycopg2
from pymongo import MongoClient
import elasticsearch

class ReplicationType(Enum):
    """Types of data replication"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    SEMI_SYNCHRONOUS = "semi_synchronous"
    EVENTUAL = "eventual"

class ConsistencyLevel(Enum):
    """Data consistency levels"""
    STRONG = "strong"
    CAUSAL = "causal"
    SESSION = "session"
    MONOTONIC_READ = "monotonic_read"
    MONOTONIC_WRITE = "monotonic_write"
    READ_YOUR_WRITES = "read_your_writes"
    EVENTUAL = "eventual"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    LAST_WRITER_WINS = "last_writer_wins"
    FIRST_WRITER_WINS = "first_writer_wins"
    TIMESTAMP_BASED = "timestamp_based"
    VECTOR_CLOCK = "vector_clock"
    MERGE = "merge"
    MANUAL = "manual"

class DataType(Enum):
    """Types of data to replicate"""
    DATABASE = "database"
    FILES = "files"
    CACHE = "cache"
    SEARCH_INDEX = "search_index"
    MESSAGE_QUEUE = "message_queue"
    BLOB_STORAGE = "blob_storage"

class StorageBackend(Enum):
    """Storage backend types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"

@dataclass
class ReplicationEndpoint:
    """Replication endpoint configuration"""
    id: str
    name: str
    region: str
    backend: StorageBackend
    connection_string: str
    is_primary: bool
    is_read_only: bool
    priority: int
    latency_threshold_ms: int
    bandwidth_limit_mbps: int
    encryption_enabled: bool
    compression_enabled: bool
    status: str
    last_sync: float
    created_at: float

@dataclass
class ReplicationRule:
    """Data replication rule"""
    id: str
    name: str
    source_endpoint: str
    target_endpoints: List[str]
    data_type: DataType
    replication_type: ReplicationType
    consistency_level: ConsistencyLevel
    conflict_resolution: ConflictResolution
    filter_criteria: Dict[str, Any]
    transformation_rules: List[Dict[str, Any]]
    schedule: str
    enabled: bool
    created_at: float

@dataclass
class ReplicationTask:
    """Replication task execution"""
    id: str
    rule_id: str
    status: str
    source_endpoint: str
    target_endpoint: str
    start_time: float
    end_time: Optional[float]
    items_processed: int
    items_failed: int
    bytes_transferred: int
    error_message: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class DataConflict:
    """Data conflict information"""
    id: str
    rule_id: str
    item_id: str
    conflict_type: str
    source_data: Dict[str, Any]
    target_data: Dict[str, Any]
    timestamp: float
    resolution: Optional[str]
    resolved_at: Optional[float]

@dataclass
class ConsistencyCheck:
    """Consistency check result"""
    id: str
    rule_id: str
    endpoint: str
    check_type: str
    inconsistencies_found: int
    items_checked: int
    timestamp: float
    details: Dict[str, Any]

class DataReplicationManager:
    """Multi-region data replication and synchronization manager"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.endpoints: Dict[str, ReplicationEndpoint] = {}
        self.replication_rules: Dict[str, ReplicationRule] = {}
        self.active_tasks: Dict[str, ReplicationTask] = {}
        self.completed_tasks: List[ReplicationTask] = []
        self.conflicts: Dict[str, DataConflict] = {}
        self.consistency_checks: List[ConsistencyCheck] = []
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Connection pools
        self.db_connections: Dict[str, Any] = {}
        self.cache_connections: Dict[str, Any] = {}

        # Replication metrics
        self.metrics = {
            'total_replications': 0,
            'successful_replications': 0,
            'failed_replications': 0,
            'total_bytes_transferred': 0,
            'average_latency_ms': 0,
            'active_tasks': 0,
            'conflicts_detected': 0,
            'consistency_score': 100.0
        }

        # Initialize configuration
        if config_path:
            self._load_configuration(config_path)
        else:
            self._initialize_default_configuration()

    def _initialize_default_configuration(self):
        """Initialize default replication configuration"""
        # Default endpoints
        default_endpoints = [
            ReplicationEndpoint(
                id="primary-db-us-east",
                name="Primary Database US East",
                region="us-east-1",
                backend=StorageBackend.POSTGRESQL,
                connection_string="postgresql://user:pass@primary-us-east.db.dmlogn8n.com:5432/dmlogn8n",
                is_primary=True,
                is_read_only=False,
                priority=1,
                latency_threshold_ms=100,
                bandwidth_limit_mbps=1000,
                encryption_enabled=True,
                compression_enabled=True,
                status="active",
                last_sync=time.time(),
                created_at=time.time()
            ),
            ReplicationEndpoint(
                id="secondary-db-eu-west",
                name="Secondary Database EU West",
                region="eu-west-1",
                backend=StorageBackend.POSTGRESQL,
                connection_string="postgresql://user:pass@secondary-eu-west.db.dmlogn8n.com:5432/dmlogn8n",
                is_primary=False,
                is_read_only=True,
                priority=2,
                latency_threshold_ms=150,
                bandwidth_limit_mbps=500,
                encryption_enabled=True,
                compression_enabled=True,
                status="active",
                last_sync=time.time(),
                created_at=time.time()
            ),
            ReplicationEndpoint(
                id="cache-us-west",
                name="Cache US West",
                region="us-west-2",
                backend=StorageBackend.REDIS,
                connection_string="redis://cache-us-west.dmlogn8n.com:6379",
                is_primary=False,
                is_read_only=False,
                priority=3,
                latency_threshold_ms=50,
                bandwidth_limit_mbps=200,
                encryption_enabled=True,
                compression_enabled=False,
                status="active",
                last_sync=time.time(),
                created_at=time.time()
            ),
            ReplicationEndpoint(
                id="search-ap-southeast",
                name="Search Index AP Southeast",
                region="ap-southeast-1",
                backend=StorageBackend.ELASTICSEARCH,
                connection_string="https://search-ap-southeast.dmlogn8n.com:9200",
                is_primary=False,
                is_read_only=False,
                priority=4,
                latency_threshold_ms=200,
                bandwidth_limit_mbps=300,
                encryption_enabled=True,
                compression_enabled=True,
                status="active",
                last_sync=time.time(),
                created_at=time.time()
            )
        ]

        for endpoint in default_endpoints:
            self.endpoints[endpoint.id] = endpoint

        # Default replication rules
        default_rules = [
            ReplicationRule(
                id="primary-to-secondary-db",
                name="Primary to Secondary Database Replication",
                source_endpoint="primary-db-us-east",
                target_endpoints=["secondary-db-eu-west"],
                data_type=DataType.DATABASE,
                replication_type=ReplicationType.ASYNCHRONOUS,
                consistency_level=ConsistencyLevel.EVENTUAL,
                conflict_resolution=ConflictResolution.LAST_WRITER_WINS,
                filter_criteria={"table_patterns": ["users_*", "workflows_*", "executions_*"]},
                transformation_rules=[{"type": "data_masking", "fields": ["ssn", "credit_card"]}],
                schedule="*/5 * * * *",  # Every 5 minutes
                enabled=True,
                created_at=time.time()
            ),
            ReplicationRule(
                id="cache-replication",
                name="Cache Replication",
                source_endpoint="cache-us-west",
                target_endpoints=["cache-us-east"],
                data_type=DataType.CACHE,
                replication_type=ReplicationType.SYNCHRONOUS,
                consistency_level=ConsistencyLevel.STRONG,
                conflict_resolution=ConflictResolution.LAST_WRITER_WINS,
                filter_criteria={"key_patterns": ["session:*", "user:*"]},
                transformation_rules=[],
                schedule="* * * * *",  # Every minute
                enabled=True,
                created_at=time.time()
            ),
            ReplicationRule(
                id="search-index-sync",
                name="Search Index Synchronization",
                source_endpoint="primary-db-us-east",
                target_endpoints=["search-ap-southeast"],
                data_type=DataType.SEARCH_INDEX,
                replication_type=ReplicationType.ASYNCHRONOUS,
                consistency_level=ConsistencyLevel.EVENTUAL,
                conflict_resolution=ConflictResolution.MERGE,
                filter_criteria={"indexed_tables": ["workflows", "executions"]},
                transformation_rules=[{"type": "field_mapping", "mappings": {"workflow_name": "title"}}],
                schedule="*/10 * * * *",  # Every 10 minutes
                enabled=True,
                created_at=time.time()
            )
        ]

        for rule in default_rules:
            self.replication_rules[rule.id] = rule

    async def initialize(self):
        """Initialize the data replication manager"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=50)
        )

        # Initialize connections to all endpoints
        await self._initialize_endpoint_connections()

        # Start background tasks
        asyncio.create_task(self._replication_scheduler_loop())
        asyncio.create_task(self._task_monitoring_loop())
        asyncio.create_task(self._consistency_checking_loop())
        asyncio.create_task(self._metrics_collection_loop())

    async def _initialize_endpoint_connections(self):
        """Initialize connections to all endpoints"""
        for endpoint_id, endpoint in self.endpoints.items():
            try:
                if endpoint.backend == StorageBackend.POSTGRESQL:
                    await self._connect_postgresql(endpoint_id, endpoint)
                elif endpoint.backend == StorageBackend.MONGODB:
                    await self._connect_mongodb(endpoint_id, endpoint)
                elif endpoint.backend == StorageBackend.REDIS:
                    await self._connect_redis(endpoint_id, endpoint)
                elif endpoint.backend == StorageBackend.ELASTICSEARCH:
                    await self._connect_elasticsearch(endpoint_id, endpoint)

                self.logger.info(f"Connected to endpoint: {endpoint_id}")

            except Exception as e:
                self.logger.error(f"Failed to connect to endpoint {endpoint_id}: {e}")
                endpoint.status = "failed"

    async def _connect_postgresql(self, endpoint_id: str, endpoint: ReplicationEndpoint):
        """Connect to PostgreSQL endpoint"""
        try:
            # Parse connection string and create connection
            conn = psycopg2.connect(endpoint.connection_string)
            self.db_connections[endpoint_id] = conn
        except Exception as e:
            self.logger.error(f"PostgreSQL connection failed for {endpoint_id}: {e}")
            raise

    async def _connect_mongodb(self, endpoint_id: str, endpoint: ReplicationEndpoint):
        """Connect to MongoDB endpoint"""
        try:
            client = MongoClient(endpoint.connection_string)
            self.db_connections[endpoint_id] = client
        except Exception as e:
            self.logger.error(f"MongoDB connection failed for {endpoint_id}: {e}")
            raise

    async def _connect_redis(self, endpoint_id: str, endpoint: ReplicationEndpoint):
        """Connect to Redis endpoint"""
        try:
            # Parse connection string
            host = endpoint.connection_string.split("://")[1].split(":")[0]
            port = int(endpoint.connection_string.split(":")[2])

            client = redis.Redis(host=host, port=port, decode_responses=True)
            self.cache_connections[endpoint_id] = client
        except Exception as e:
            self.logger.error(f"Redis connection failed for {endpoint_id}: {e}")
            raise

    async def _connect_elasticsearch(self, endpoint_id: str, endpoint: ReplicationEndpoint):
        """Connect to Elasticsearch endpoint"""
        try:
            client = elasticsearch.Elasticsearch([endpoint.connection_string])
            self.db_connections[endpoint_id] = client
        except Exception as e:
            self.logger.error(f"Elasticsearch connection failed for {endpoint_id}: {e}")
            raise

    async def create_endpoint(self, endpoint: ReplicationEndpoint) -> bool:
        """Create a new replication endpoint"""
        try:
            # Test connection
            if await self._test_endpoint_connection(endpoint):
                self.endpoints[endpoint.id] = endpoint
                await self._initialize_endpoint_connections()
                self.logger.info(f"Created replication endpoint: {endpoint.id}")
                return True
            else:
                self.logger.error(f"Connection test failed for endpoint: {endpoint.id}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating endpoint {endpoint.id}: {e}")
            return False

    async def _test_endpoint_connection(self, endpoint: ReplicationEndpoint) -> bool:
        """Test connection to an endpoint"""
        try:
            if endpoint.backend == StorageBackend.POSTGRESQL:
                conn = psycopg2.connect(endpoint.connection_string)
                conn.close()
                return True
            elif endpoint.backend == StorageBackend.REDIS:
                host = endpoint.connection_string.split("://")[1].split(":")[0]
                port = int(endpoint.connection_string.split(":")[2])
                client = redis.Redis(host=host, port=port)
                client.ping()
                client.close()
                return True
            # Add other backend tests
            return False
        except Exception:
            return False

    async def create_replication_rule(self, rule: ReplicationRule) -> bool:
        """Create a new replication rule"""
        try:
            # Validate rule
            if not await self._validate_replication_rule(rule):
                return False

            self.replication_rules[rule.id] = rule
            self.logger.info(f"Created replication rule: {rule.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating replication rule {rule.id}: {e}")
            return False

    async def _validate_replication_rule(self, rule: ReplicationRule) -> bool:
        """Validate replication rule"""
        # Check if source endpoint exists
        if rule.source_endpoint not in self.endpoints:
            self.logger.error(f"Source endpoint {rule.source_endpoint} not found")
            return False

        # Check if target endpoints exist
        for target_endpoint in rule.target_endpoints:
            if target_endpoint not in self.endpoints:
                self.logger.error(f"Target endpoint {target_endpoint} not found")
                return False

        # Check if source and target endpoints are compatible
        source_backend = self.endpoints[rule.source_endpoint].backend
        for target_endpoint in rule.target_endpoints:
            target_backend = self.endpoints[target_endpoint].backend
            if not await self._check_backend_compatibility(source_backend, target_backend, rule.data_type):
                self.logger.error(f"Backend incompatibility between {source_backend} and {target_backend}")
                return False

        return True

    async def _check_backend_compatibility(self, source: StorageBackend,
                                         target: StorageBackend,
                                         data_type: DataType) -> bool:
        """Check if source and target backends are compatible for the data type"""
        # Simplified compatibility matrix
        compatibility_matrix = {
            (StorageBackend.POSTGRESQL, StorageBackend.POSTGRESQL): [DataType.DATABASE],
            (StorageBackend.POSTGRESQL, StorageBackend.MONGODB): [DataType.DATABASE],
            (StorageBackend.POSTGRESQL, StorageBackend.ELASTICSEARCH): [DataType.SEARCH_INDEX],
            (StorageBackend.REDIS, StorageBackend.REDIS): [DataType.CACHE],
            (StorageBackend.MONGODB, StorageBackend.MONGODB): [DataType.DATABASE],
            (StorageBackend.MONGODB, StorageBackend.ELASTICSEARCH): [DataType.SEARCH_INDEX],
        }

        compatible_types = compatibility_matrix.get((source, target), [])
        return data_type in compatible_types

    async def execute_replication(self, rule_id: str) -> Optional[str]:
        """Manually execute a replication rule"""
        try:
            if rule_id not in self.replication_rules:
                raise ValueError(f"Replication rule {rule_id} not found")

            rule = self.replication_rules[rule_id]
            if not rule.enabled:
                self.logger.warning(f"Replication rule {rule_id} is disabled")
                return None

            # Create replication task for each target
            task_ids = []
            for target_endpoint in rule.target_endpoints:
                task_id = await self._create_replication_task(rule_id, rule.source_endpoint, target_endpoint)
                if task_id:
                    task_ids.append(task_id)

            # Execute tasks
            for task_id in task_ids:
                asyncio.create_task(self._execute_replication_task(task_id))

            return task_ids[0] if task_ids else None

        except Exception as e:
            self.logger.error(f"Error executing replication {rule_id}: {e}")
            return None

    async def _create_replication_task(self, rule_id: str, source_endpoint: str,
                                    target_endpoint: str) -> Optional[str]:
        """Create a replication task"""
        try:
            task_id = str(uuid.uuid4())
            task = ReplicationTask(
                id=task_id,
                rule_id=rule_id,
                status="pending",
                source_endpoint=source_endpoint,
                target_endpoint=target_endpoint,
                start_time=time.time(),
                end_time=None,
                items_processed=0,
                items_failed=0,
                bytes_transferred=0,
                error_message=None,
                metadata={}
            )

            self.active_tasks[task_id] = task
            self.metrics['active_tasks'] += 1

            return task_id

        except Exception as e:
            self.logger.error(f"Error creating replication task: {e}")
            return None

    async def _execute_replication_task(self, task_id: str):
        """Execute a replication task"""
        try:
            task = self.active_tasks[task_id]
            rule = self.replication_rules[task.rule_id]

            task.status = "running"
            start_time = time.time()

            # Get data from source
            source_data = await self._extract_data(task.source_endpoint, rule)

            # Transform data if needed
            transformed_data = await self._transform_data(source_data, rule)

            # Load data to target
            result = await self._load_data(task.target_endpoint, transformed_data, rule)

            # Update task status
            task.items_processed = result.get('items_processed', 0)
            task.items_failed = result.get('items_failed', 0)
            task.bytes_transferred = result.get('bytes_transferred', 0)
            task.end_time = time.time()
            task.status = "completed" if task.items_failed == 0 else "completed_with_errors"

            # Update metrics
            self._update_replication_metrics(task, rule)

            # Move task to completed
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            self.metrics['active_tasks'] -= 1

            self.logger.info(f"Replication task {task_id} completed: {task.items_processed} items, {task.items_failed} failed")

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.end_time = time.time()

            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            self.metrics['active_tasks'] -= 1
            self.metrics['failed_replications'] += 1

            self.logger.error(f"Replication task {task_id} failed: {e}")

    async def _extract_data(self, endpoint_id: str, rule: ReplicationRule) -> List[Dict[str, Any]]:
        """Extract data from source endpoint"""
        try:
            endpoint = self.endpoints[endpoint_id]

            if endpoint.backend == StorageBackend.POSTGRESQL:
                return await self._extract_from_postgresql(endpoint_id, rule)
            elif endpoint.backend == StorageBackend.MONGODB:
                return await self._extract_from_mongodb(endpoint_id, rule)
            elif endpoint.backend == StorageBackend.REDIS:
                return await self._extract_from_redis(endpoint_id, rule)
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error extracting data from {endpoint_id}: {e}")
            raise

    async def _extract_from_postgresql(self, endpoint_id: str, rule: ReplicationRule) -> List[Dict[str, Any]]:
        """Extract data from PostgreSQL"""
        try:
            conn = self.db_connections[endpoint_id]
            cursor = conn.cursor()

            data = []
            filter_criteria = rule.filter_criteria

            # Extract data based on filter criteria
            if 'table_patterns' in filter_criteria:
                for table_pattern in filter_criteria['table_patterns']:
                    # Get tables matching pattern
                    cursor.execute("""
                        SELECT tablename FROM pg_tables
                        WHERE tablename LIKE %s AND schemaname = 'public'
                    """, (table_pattern.replace('*', '%'),))

                    tables = cursor.fetchall()
                    for (table_name,) in tables:
                        # Extract data from table
                        cursor.execute(f"SELECT * FROM {table_name}")
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()

                        for row in rows:
                            record = dict(zip(columns, row))
                            record['_table'] = table_name
                            record['_source'] = endpoint_id
                            record['_timestamp'] = time.time()
                            data.append(record)

            cursor.close()
            return data

        except Exception as e:
            self.logger.error(f"Error extracting from PostgreSQL {endpoint_id}: {e}")
            raise

    async def _extract_from_mongodb(self, endpoint_id: str, rule: ReplicationRule) -> List[Dict[str, Any]]:
        """Extract data from MongoDB"""
        try:
            client = self.db_connections[endpoint_id]
            db = client.dmlogn8n

            data = []
            filter_criteria = rule.filter_criteria

            # Extract collections based on filter criteria
            if 'collection_patterns' in filter_criteria:
                for collection_pattern in filter_criteria['collection_patterns']:
                    collections = db.list_collection_names()
                    matching_collections = [c for c in collections if collection_pattern.replace('*', '') in c]

                    for collection_name in matching_collections:
                        collection = db[collection_name]
                        documents = collection.find({})

                        for doc in documents:
                            doc['_collection'] = collection_name
                            doc['_source'] = endpoint_id
                            doc['_timestamp'] = time.time()
                            data.append(doc)

            return data

        except Exception as e:
            self.logger.error(f"Error extracting from MongoDB {endpoint_id}: {e}")
            raise

    async def _extract_from_redis(self, endpoint_id: str, rule: ReplicationRule) -> List[Dict[str, Any]]:
        """Extract data from Redis"""
        try:
            client = self.cache_connections[endpoint_id]
            data = []
            filter_criteria = rule.filter_criteria

            # Extract keys based on filter criteria
            if 'key_patterns' in filter_criteria:
                for pattern in filter_criteria['key_patterns']:
                    keys = client.keys(pattern.replace('*', '*'))

                    for key in keys:
                        value = client.get(key)
                        data.append({
                            '_key': key,
                            '_value': value,
                            '_source': endpoint_id,
                            '_timestamp': time.time()
                        })

            return data

        except Exception as e:
            self.logger.error(f"Error extracting from Redis {endpoint_id}: {e}")
            raise

    async def _transform_data(self, data: List[Dict[str, Any]], rule: ReplicationRule) -> List[Dict[str, Any]]:
        """Transform data according to transformation rules"""
        try:
            if not rule.transformation_rules:
                return data

            transformed_data = []
            for item in data:
                transformed_item = item.copy()

                for transform_rule in rule.transformation_rules:
                    if transform_rule['type'] == 'data_masking':
                        transformed_item = await self._apply_data_masking(transformed_item, transform_rule)
                    elif transform_rule['type'] == 'field_mapping':
                        transformed_item = await self._apply_field_mapping(transformed_item, transform_rule)
                    elif transform_rule['type'] == 'data_filtering':
                        transformed_item = await self._apply_data_filtering(transformed_item, transform_rule)

                transformed_data.append(transformed_item)

            return transformed_data

        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            return data

    async def _apply_data_masking(self, item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data masking transformation"""
        try:
            fields_to_mask = rule.get('fields', [])
            for field in fields_to_mask:
                if field in item:
                    item[field] = '***MASKED***'
            return item
        except Exception as e:
            self.logger.error(f"Error applying data masking: {e}")
            return item

    async def _apply_field_mapping(self, item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mapping transformation"""
        try:
            mappings = rule.get('mappings', {})
            for source_field, target_field in mappings.items():
                if source_field in item:
                    item[target_field] = item[source_field]
                    if source_field != target_field:
                        del item[source_field]
            return item
        except Exception as e:
            self.logger.error(f"Error applying field mapping: {e}")
            return item

    async def _apply_data_filtering(self, item: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data filtering transformation"""
        try:
            filters = rule.get('filters', {})
            for field, condition in filters.items():
                if field in item:
                    if condition['operator'] == 'equals' and item[field] != condition['value']:
                        return None
                    elif condition['operator'] == 'not_equals' and item[field] == condition['value']:
                        return None
            return item
        except Exception as e:
            self.logger.error(f"Error applying data filtering: {e}")
            return item

    async def _load_data(self, endpoint_id: str, data: List[Dict[str, Any]],
                       rule: ReplicationRule) -> Dict[str, int]:
        """Load data to target endpoint"""
        try:
            endpoint = self.endpoints[endpoint_id]

            if endpoint.backend == StorageBackend.POSTGRESQL:
                return await self._load_to_postgresql(endpoint_id, data, rule)
            elif endpoint.backend == StorageBackend.MONGODB:
                return await self._load_to_mongodb(endpoint_id, data, rule)
            elif endpoint.backend == StorageBackend.REDIS:
                return await self._load_to_redis(endpoint_id, data, rule)
            elif endpoint.backend == StorageBackend.ELASTICSEARCH:
                return await self._load_to_elasticsearch(endpoint_id, data, rule)
            else:
                return {'items_processed': 0, 'items_failed': len(data), 'bytes_transferred': 0}

        except Exception as e:
            self.logger.error(f"Error loading data to {endpoint_id}: {e}")
            return {'items_processed': 0, 'items_failed': len(data), 'bytes_transferred': 0}

    async def _load_to_postgresql(self, endpoint_id: str, data: List[Dict[str, Any]],
                                rule: ReplicationRule) -> Dict[str, int]:
        """Load data to PostgreSQL"""
        try:
            conn = self.db_connections[endpoint_id]
            cursor = conn.cursor()

            items_processed = 0
            items_failed = 0
            bytes_transferred = 0

            for item in data:
                if item is None:  # Filtered out
                    continue

                try:
                    if '_table' in item:
                        table_name = item['_table']
                        # Remove metadata fields
                        clean_item = {k: v for k, v in item.items() if not k.startswith('_')}

                        # Upsert data
                        columns = list(clean_item.keys())
                        placeholders = ', '.join(['%s'] * len(columns))
                        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns])

                        query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES ({placeholders})
                            ON CONFLICT (id) DO UPDATE SET {update_clause}
                        """

                        cursor.execute(query, list(clean_item.values()))
                        items_processed += 1
                        bytes_transferred += len(str(clean_item))

                except Exception as e:
                    items_failed += 1
                    self.logger.error(f"Error loading item to PostgreSQL: {e}")

            conn.commit()
            cursor.close()

            return {
                'items_processed': items_processed,
                'items_failed': items_failed,
                'bytes_transferred': bytes_transferred
            }

        except Exception as e:
            self.logger.error(f"Error loading to PostgreSQL {endpoint_id}: {e}")
            raise

    async def _load_to_mongodb(self, endpoint_id: str, data: List[Dict[str, Any]],
                              rule: ReplicationRule) -> Dict[str, int]:
        """Load data to MongoDB"""
        try:
            client = self.db_connections[endpoint_id]
            db = client.dmlogn8n

            items_processed = 0
            items_failed = 0
            bytes_transferred = 0

            for item in data:
                if item is None:
                    continue

                try:
                    if '_collection' in item:
                        collection_name = item['_collection']
                        collection = db[collection_name]

                        # Remove metadata fields
                        clean_item = {k: v for k, v in item.items() if not k.startswith('_')}

                        # Upsert data
                        if '_id' in clean_item:
                            collection.replace_one({'_id': clean_item['_id']}, clean_item, upsert=True)
                        else:
                            collection.insert_one(clean_item)

                        items_processed += 1
                        bytes_transferred += len(str(clean_item))

                except Exception as e:
                    items_failed += 1
                    self.logger.error(f"Error loading item to MongoDB: {e}")

            return {
                'items_processed': items_processed,
                'items_failed': items_failed,
                'bytes_transferred': bytes_transferred
            }

        except Exception as e:
            self.logger.error(f"Error loading to MongoDB {endpoint_id}: {e}")
            raise

    async def _load_to_redis(self, endpoint_id: str, data: List[Dict[str, Any]],
                           rule: ReplicationRule) -> Dict[str, int]:
        """Load data to Redis"""
        try:
            client = self.cache_connections[endpoint_id]

            items_processed = 0
            items_failed = 0
            bytes_transferred = 0

            for item in data:
                if item is None:
                    continue

                try:
                    if '_key' in item and '_value' in item:
                        client.set(item['_key'], item['_value'])
                        items_processed += 1
                        bytes_transferred += len(item['_value'])

                except Exception as e:
                    items_failed += 1
                    self.logger.error(f"Error loading item to Redis: {e}")

            return {
                'items_processed': items_processed,
                'items_failed': items_failed,
                'bytes_transferred': bytes_transferred
            }

        except Exception as e:
            self.logger.error(f"Error loading to Redis {endpoint_id}: {e}")
            raise

    async def _load_to_elasticsearch(self, endpoint_id: str, data: List[Dict[str, Any]],
                                   rule: ReplicationRule) -> Dict[str, int]:
        """Load data to Elasticsearch"""
        try:
            client = self.db_connections[endpoint_id]

            items_processed = 0
            items_failed = 0
            bytes_transferred = 0

            for item in data:
                if item is None:
                    continue

                try:
                    index_name = 'dmlogn8n_data'

                    # Remove metadata fields
                    clean_item = {k: v for k, v in item.items() if not k.startswith('_')}

                    # Index document
                    doc_id = clean_item.get('id', str(uuid.uuid4()))
                    client.index(index=index_name, id=doc_id, body=clean_item)

                    items_processed += 1
                    bytes_transferred += len(str(clean_item))

                except Exception as e:
                    items_failed += 1
                    self.logger.error(f"Error loading item to Elasticsearch: {e}")

            return {
                'items_processed': items_processed,
                'items_failed': items_failed,
                'bytes_transferred': bytes_transferred
            }

        except Exception as e:
            self.logger.error(f"Error loading to Elasticsearch {endpoint_id}: {e}")
            raise

    def _update_replication_metrics(self, task: ReplicationTask, rule: ReplicationRule):
        """Update replication metrics"""
        self.metrics['total_replications'] += 1
        if task.status == "completed":
            self.metrics['successful_replications'] += 1
        else:
            self.metrics['failed_replications'] += 1

        self.metrics['total_bytes_transferred'] += task.bytes_transferred

    async def _replication_scheduler_loop(self):
        """Schedule replication tasks based on rules"""
        while True:
            try:
                current_time = time.time()

                for rule_id, rule in self.replication_rules.items():
                    if not rule.enabled:
                        continue

                    # Check if it's time to run this rule
                    if await self._should_run_rule(rule, current_time):
                        self.logger.info(f"Scheduling replication for rule: {rule_id}")
                        await self.execute_replication(rule_id)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in replication scheduler loop: {e}")
                await asyncio.sleep(60)

    async def _should_run_rule(self, rule: ReplicationRule, current_time: float) -> bool:
        """Check if a rule should be run based on its schedule"""
        # Simplified scheduling - in production use proper cron parsing
        if rule.schedule == "* * * * *":  # Every minute
            return True
        elif rule.schedule == "*/5 * * * *":  # Every 5 minutes
            return int(current_time / 60) % 5 == 0
        elif rule.schedule == "*/10 * * * *":  # Every 10 minutes
            return int(current_time / 60) % 10 == 0

        return False

    async def _task_monitoring_loop(self):
        """Monitor active replication tasks"""
        while True:
            try:
                current_time = time.time()

                # Check for long-running tasks
                for task_id, task in list(self.active_tasks.items()):
                    if current_time - task.start_time > 3600:  # > 1 hour
                        self.logger.warning(f"Long-running task detected: {task_id}")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in task monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _consistency_checking_loop(self):
        """Perform consistency checks across endpoints"""
        while True:
            try:
                for rule_id, rule in self.replication_rules.items():
                    if not rule.enabled:
                        continue

                    # Perform consistency check
                    await self._perform_consistency_check(rule_id, rule)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                self.logger.error(f"Error in consistency checking loop: {e}")
                await asyncio.sleep(3600)

    async def _perform_consistency_check(self, rule_id: str, rule: ReplicationRule):
        """Perform consistency check for a replication rule"""
        try:
            source_endpoint = rule.source_endpoint
            target_endpoints = rule.target_endpoints

            for target_endpoint in target_endpoints:
                # Get data counts from source and target
                source_count = await self._get_data_count(source_endpoint, rule)
                target_count = await self._get_data_count(target_endpoint, rule)

                # Calculate consistency score
                total_items = max(source_count, target_count)
                if total_items > 0:
                    consistency_score = min(source_count, target_count) / total_items * 100
                else:
                    consistency_score = 100

                # Create consistency check record
                check = ConsistencyCheck(
                    id=str(uuid.uuid4()),
                    rule_id=rule_id,
                    endpoint=target_endpoint,
                    check_type="data_count",
                    inconsistencies_found=abs(source_count - target_count),
                    items_checked=source_count + target_count,
                    timestamp=time.time(),
                    details={
                        'source_count': source_count,
                        'target_count': target_count,
                        'consistency_score': consistency_score
                    }
                )

                self.consistency_checks.append(check)

                # Update global consistency score
                self.metrics['consistency_score'] = consistency_score

                if consistency_score < 95:
                    self.logger.warning(f"Low consistency detected for rule {rule_id}: {consistency_score:.1f}%")

        except Exception as e:
            self.logger.error(f"Error performing consistency check for rule {rule_id}: {e}")

    async def _get_data_count(self, endpoint_id: str, rule: ReplicationRule) -> int:
        """Get data count from an endpoint"""
        try:
            endpoint = self.endpoints[endpoint_id]

            if endpoint.backend == StorageBackend.POSTGRESQL:
                return await self._get_postgresql_count(endpoint_id, rule)
            elif endpoint.backend == StorageBackend.MONGODB:
                return await self._get_mongodb_count(endpoint_id, rule)
            elif endpoint.backend == StorageBackend.REDIS:
                return await self._get_redis_count(endpoint_id, rule)
            else:
                return 0

        except Exception as e:
            self.logger.error(f"Error getting data count from {endpoint_id}: {e}")
            return 0

    async def _get_postgresql_count(self, endpoint_id: str, rule: ReplicationRule) -> int:
        """Get data count from PostgreSQL"""
        try:
            conn = self.db_connections[endpoint_id]
            cursor = conn.cursor()

            total_count = 0
            filter_criteria = rule.filter_criteria

            if 'table_patterns' in filter_criteria:
                for table_pattern in filter_criteria['table_patterns']:
                    cursor.execute("""
                        SELECT tablename FROM pg_tables
                        WHERE tablename LIKE %s AND schemaname = 'public'
                    """, (table_pattern.replace('*', '%'),))

                    tables = cursor.fetchall()
                    for (table_name,) in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        total_count += count

            cursor.close()
            return total_count

        except Exception as e:
            self.logger.error(f"Error getting PostgreSQL count: {e}")
            return 0

    async def _get_mongodb_count(self, endpoint_id: str, rule: ReplicationRule) -> int:
        """Get data count from MongoDB"""
        try:
            client = self.db_connections[endpoint_id]
            db = client.dmlogn8n

            total_count = 0
            filter_criteria = rule.filter_criteria

            if 'collection_patterns' in filter_criteria:
                collections = db.list_collection_names()
                for pattern in filter_criteria['collection_patterns']:
                    matching_collections = [c for c in collections if pattern.replace('*', '') in c]
                    for collection_name in matching_collections:
                        collection = db[collection_name]
                        count = collection.count_documents({})
                        total_count += count

            return total_count

        except Exception as e:
            self.logger.error(f"Error getting MongoDB count: {e}")
            return 0

    async def _get_redis_count(self, endpoint_id: str, rule: ReplicationRule) -> int:
        """Get data count from Redis"""
        try:
            client = self.cache_connections[endpoint_id]

            total_count = 0
            filter_criteria = rule.filter_criteria

            if 'key_patterns' in filter_criteria:
                for pattern in filter_criteria['key_patterns']:
                    keys = client.keys(pattern.replace('*', '*'))
                    total_count += len(keys)

            return total_count

        except Exception as e:
            self.logger.error(f"Error getting Redis count: {e}")
            return 0

    async def _metrics_collection_loop(self):
        """Collect replication metrics"""
        while True:
            try:
                await self._collect_replication_metrics()
                await asyncio.sleep(300)  # Collect every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(300)

    async def _collect_replication_metrics(self):
        """Collect detailed replication metrics"""
        try:
            # Calculate average latency
            recent_tasks = self.completed_tasks[-100:] if self.completed_tasks else []
            if recent_tasks:
                total_latency = sum(task.end_time - task.start_time for task in recent_tasks if task.end_time)
                self.metrics['average_latency_ms'] = (total_latency / len(recent_tasks)) * 1000

        except Exception as e:
            self.logger.error(f"Error collecting replication metrics: {e}")

    async def get_replication_metrics(self) -> Dict[str, Any]:
        """Get replication performance metrics"""
        metrics = self.metrics.copy()

        # Add additional metrics
        metrics['endpoints'] = {
            'total': len(self.endpoints),
            'active': sum(1 for e in self.endpoints.values() if e.status == "active"),
            'failed': sum(1 for e in self.endpoints.values() if e.status == "failed")
        }

        metrics['rules'] = {
            'total': len(self.replication_rules),
            'enabled': sum(1 for r in self.replication_rules.values() if r.enabled),
            'disabled': sum(1 for r in self.replication_rules.values() if not r.enabled)
        }

        metrics['recent_activity'] = []
        for task in self.completed_tasks[-10:]:
            metrics['recent_activity'].append({
                'task_id': task.id,
                'rule_id': task.rule_id,
                'status': task.status,
                'items_processed': task.items_processed,
                'items_failed': task.items_failed,
                'duration_seconds': task.end_time - task.start_time if task.end_time else 0
            })

        return metrics

    def _load_configuration(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load endpoints
            if 'endpoints' in config:
                for endpoint_config in config['endpoints']:
                    endpoint_config['backend'] = StorageBackend(endpoint_config['backend'])
                    endpoint = ReplicationEndpoint(**endpoint_config)
                    self.endpoints[endpoint.id] = endpoint

            # Load replication rules
            if 'replication_rules' in config:
                for rule_config in config['replication_rules']:
                    rule_config['data_type'] = DataType(rule_config['data_type'])
                    rule_config['replication_type'] = ReplicationType(rule_config['replication_type'])
                    rule_config['consistency_level'] = ConsistencyLevel(rule_config['consistency_level'])
                    rule_config['conflict_resolution'] = ConflictResolution(rule_config['conflict_resolution'])
                    rule = ReplicationRule(**rule_config)
                    self.replication_rules[rule.id] = rule

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

    def save_configuration(self, config_path: str):
        """Save current configuration to file"""
        config = {
            'endpoints': [
                {
                    **asdict(endpoint),
                    'backend': endpoint.backend.value
                }
                for endpoint in self.endpoints.values()
            ],
            'replication_rules': [
                {
                    **asdict(rule),
                    'data_type': rule.data_type.value,
                    'replication_type': rule.replication_type.value,
                    'consistency_level': rule.consistency_level.value,
                    'conflict_resolution': rule.conflict_resolution.value
                }
                for rule in self.replication_rules.values()
            ]
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

        # Close database connections
        for conn in self.db_connections.values():
            try:
                if hasattr(conn, 'close'):
                    conn.close()
            except:
                pass

        # Close cache connections
        for client in self.cache_connections.values():
            try:
                client.close()
            except:
                pass

        self.executor.shutdown(wait=True)


async def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)

    replication_manager = DataReplicationManager()
    await replication_manager.initialize()

    # Execute a test replication
    print("Executing test replication...")
    task_id = await replication_manager.execute_replication("primary-to-secondary-db")
    print(f"Replication task started: {task_id}")

    # Wait a bit and check status
    await asyncio.sleep(5)
    metrics = await replication_manager.get_replication_metrics()

    print(f"\nReplication Metrics:")
    print(f"  Total Replications: {metrics['total_replications']}")
    print(f"  Success Rate: {metrics['successful_replications'] / max(1, metrics['total_replications']) * 100:.1f}%")
    print(f"  Average Latency: {metrics['average_latency_ms']:.1f}ms")
    print(f"  Active Tasks: {metrics['active_tasks']}")
    print(f"  Consistency Score: {metrics['consistency_score']:.1f}%")
    print(f"  Active Endpoints: {metrics['endpoints']['active']}/{metrics['endpoints']['total']}")
    print(f"  Enabled Rules: {metrics['rules']['enabled']}/{metrics['rules']['total']}")

    await replication_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())