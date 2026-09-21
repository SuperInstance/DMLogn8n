"""
Database Persistence Service
Multi-database support with connection pooling and caching
"""

import asyncio
import asyncpg
import aioredis
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, BatchStatement
from neo4j import GraphDatabase
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import elasticsearch
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import uuid
import numpy as np
from contextlib import asynccontextmanager
import redis

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    CASSANDRA = "cassandra"
    NEO4J = "neo4j"
    INFLUXDB = "influxdb"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"


@dataclass
class DatabaseConfig:
    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    connection_timeout: int = 10
    command_timeout: int = 5


@dataclass
class QueryResult:
    """Query result wrapper"""
    success: bool
    data: Union[List[Dict], Dict, None] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    rows_affected: int = 0
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class DatabaseService:
    """Multi-database persistence service"""

    def __init__(self):
        self.connections: Dict[DatabaseType, Any] = {}
        self.pools: Dict[DatabaseType, Any] = {}
        self.configs: Dict[DatabaseType, DatabaseConfig] = {}
        self.query_cache = {}
        self.performance_metrics = {
            "queries_executed": 0,
            "total_execution_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }

    async def initialize(self):
        """Initialize all database connections"""
        logger.info("Initializing database service")

        # PostgreSQL
        await self._init_postgresql()

        # Redis
        await self._init_redis()

        # Cassandra
        await self._init_cassandra()

        # Neo4j
        await self._init_neo4j()

        # InfluxDB
        await self._init_influxdb()

        # MongoDB
        await self._init_mongodb()

        # Elasticsearch
        await self._init_elasticsearch()

        logger.info("Database service initialized")

    async def _init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="dmlogn8n",
            username="dmlogn8n_user",
            password="your_postgres_password",
            pool_size=20,
            max_overflow=30
        )

        self.configs[DatabaseType.POSTGRESQL] = config

        pool = await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            min_size=5,
            max_size=config.pool_size,
            command_timeout=config.command_timeout
        )

        self.pools[DatabaseType.POSTGRESQL] = pool

        # Create tables
        await self._create_postgresql_tables()

    async def _create_postgresql_tables(self):
        """Create PostgreSQL tables"""
        pool = self.pools[DatabaseType.POSTGRESQL]

        async with pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Characters table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    character_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(user_id),
                    name VARCHAR(100) NOT NULL,
                    class VARCHAR(50),
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Games table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    game_master_id UUID REFERENCES users(user_id),
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    game_id UUID REFERENCES games(game_id),
                    session_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
                CREATE INDEX IF NOT EXISTS idx_games_game_master_id ON games(game_master_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_game_id ON game_sessions(game_id);
            """)

    async def _init_redis(self):
        """Initialize Redis connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.REDIS,
            host="localhost",
            port=6379,
            database=0
        )

        self.configs[DatabaseType.REDIS] = config

        # Redis for caching
        redis_cache = aioredis.from_url(
            f"redis://{config.host}:{config.port}/{config.database}",
            encoding="utf-8",
            decode_responses=True
        )

        # Redis for sessions
        redis_sessions = aioredis.from_url(
            f"redis://{config.host}:{config.port}/1",
            encoding="utf-8",
            decode_responses=True
        )

        # Redis for pub/sub
        redis_pubsub = aioredis.from_url(
            f"redis://{config.host}:{config.port}/2",
            encoding="utf-8",
            decode_responses=True
        )

        self.connections[DatabaseType.REDIS] = {
            "cache": redis_cache,
            "sessions": redis_sessions,
            "pubsub": redis_pubsub
        }

    async def _init_cassandra(self):
        """Initialize Cassandra connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.CASSANDRA,
            host="localhost",
            port=9042,
            database="dmlogn8n"
        )

        self.configs[DatabaseType.CASSANDRA] = config

        cluster = Cluster([config.host], port=config.port)
        session = cluster.connect()

        # Create keyspace
        await session.execute("""
            CREATE KEYSPACE IF NOT EXISTS dmlogn8n
            WITH REPLICATION = {
                'class': 'SimpleStrategy',
                'replication_factor': 3
            };
        """)

        session.set_keyspace('dmlogn8n')

        # Create tables
        await session.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id UUID PRIMARY KEY,
                event_type TEXT,
                event_data TEXT,
                timestamp TIMESTAMP,
                source_id UUID
            );
        """)

        await session.execute("""
            CREATE TABLE IF NOT EXISTS time_series_data (
                metric_id UUID,
                timestamp TIMESTAMP,
                value DOUBLE,
                tags MAP<TEXT, TEXT>,
                PRIMARY KEY (metric_id, timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC);
        """)

        self.connections[DatabaseType.CASSANDRA] = session

    async def _init_neo4j(self):
        """Initialize Neo4j connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.NEO4J,
            host="localhost",
            port=7687,
            database="neo4j",
            username="neo4j",
            password="your_neo4j_password"
        )

        self.configs[DatabaseType.NEO4J] = config

        driver = GraphDatabase.driver(
            f"bolt://{config.host}:{config.port}",
            auth=(config.username, config.password)
        )

        self.connections[DatabaseType.NEO4J] = driver

        # Create constraints
        with driver.session() as session:
            session.run("""
                CREATE CONSTRAINT user_id_unique IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT character_id_unique IF NOT EXISTS
                FOR (c:Character) REQUIRE c.id IS UNIQUE
            """)

    async def _init_influxdb(self):
        """Initialize InfluxDB connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.INFLUXDB,
            host="localhost",
            port=8086,
            database="dmlogn8n_metrics",
            token="your-influxdb-token"
        )

        self.configs[DatabaseType.INFLUXDB] = config

        client = InfluxDBClient(
            url=f"http://{config.host}:{config.port}",
            token=config.token,
            org="dmlogn8n"
        )

        self.connections[DatabaseType.INFLUXDB] = client

        # Create bucket
        buckets_api = client.buckets_api()
        if not buckets_api.find_bucket_by_name("dmlogn8n"):
            buckets_api.create_bucket(
                bucket_name="dmlogn8n",
                org="dmlogn8n",
                retention_rules=[
                    {
                        "type": "expire",
                        "every_seconds": 2592000  # 30 days
                    }
                ]
            )

    async def _init_mongodb(self):
        """Initialize MongoDB connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            database="dmlogn8n"
        )

        self.configs[DatabaseType.MONGODB] = config

        client = AsyncIOMotorClient(
            f"mongodb://{config.host}:{config.port}",
            maxPoolSize=config.pool_size
        )

        db = client[config.database]

        # Create collections and indexes
        await db.characters.create_index("user_id")
        await db.characters.create_index("name")
        await db.games.create_index("game_master_id")
        await db.chat_logs.create_index([("session_id", 1), ("timestamp", -1)])

        self.connections[DatabaseType.MONGODB] = db

    async def _init_elasticsearch(self):
        """Initialize Elasticsearch connection"""
        config = DatabaseConfig(
            db_type=DatabaseType.ELASTICSEARCH,
            host="localhost",
            port=9200
        )

        self.configs[DatabaseType.ELASTICSEARCH] = config

        es = elasticsearch.Elasticsearch([{
            "host": config.host,
            "port": config.port
        }])

        # Create indices
        if not es.indices.exists(index="characters"):
            es.indices.create(
                index="characters",
                body={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "class": {"type": "keyword"},
                            "level": {"type": "integer"},
                            "description": {"type": "text"}
                        }
                    }
                }
            )

        if not es.indices.exists(index="chat_logs"):
            es.indices.create(
                index="chat_logs",
                body={
                    "mappings": {
                        "properties": {
                            "session_id": {"type": "keyword"},
                            "character_id": {"type": "keyword"},
                            "message": {"type": "text"},
                            "timestamp": {"type": "date"}
                        }
                    }
                }
            )

        self.connections[DatabaseType.ELASTICSEARCH] = es

    # PostgreSQL operations
    async def execute_postgresql_query(self,
                                     query: str,
                                     params: Optional[tuple] = None,
                                     fetch: str = "all") -> QueryResult:
        """Execute PostgreSQL query"""
        start_time = datetime.now()

        try:
            pool = self.pools[DatabaseType.POSTGRESQL]

            async with pool.acquire() as conn:
                if fetch == "all":
                    result = await conn.fetch(query, *params if params else ())
                    data = [dict(row) for row in result]
                elif fetch == "one":
                    result = await conn.fetchrow(query, *params if params else ())
                    data = dict(result) if result else None
                elif fetch == "val":
                    result = await conn.fetchval(query, *params if params else ())
                    data = result
                else:
                    result = await conn.execute(query, *params if params else ())
                    data = None

            execution_time = (datetime.now() - start_time).total_seconds()

            self.performance_metrics["queries_executed"] += 1
            self.performance_metrics["total_execution_time"] += execution_time

            return QueryResult(
                success=True,
                data=data,
                execution_time=execution_time,
                rows_affected=len(data) if isinstance(data, list) else 1
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["errors"] += 1

            logger.error(f"PostgreSQL query error: {e}")
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    # Redis operations
    async def redis_set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set Redis value"""
        try:
            redis_client = self.connections[DatabaseType.REDIS]["cache"]
            serialized_value = json.dumps(value) if not isinstance(value, str) else value

            if expire:
                await redis_client.setex(key, expire, serialized_value)
            else:
                await redis_client.set(key, serialized_value)

            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def redis_get(self, key: str) -> Optional[Any]:
        """Get Redis value"""
        try:
            redis_client = self.connections[DatabaseType.REDIS]["cache"]
            value = await redis_client.get(key)

            if value:
                try:
                    return json.loads(value)
                except:
                    return value

            return None

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def redis_delete(self, key: str) -> bool:
        """Delete Redis key"""
        try:
            redis_client = self.connections[DatabaseType.REDIS]["cache"]
            await redis_client.delete(key)
            return True

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    # MongoDB operations
    async def mongodb_insert(self, collection: str, document: Dict) -> str:
        """Insert document into MongoDB"""
        try:
            db = self.connections[DatabaseType.MONGODB]
            result = await db[collection].insert_one(document)
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"MongoDB insert error: {e}")
            return ""

    async def mongodb_find(self,
                         collection: str,
                         query: Optional[Dict] = None,
                         limit: int = 100) -> List[Dict]:
        """Find documents in MongoDB"""
        try:
            db = self.connections[DatabaseType.MONGODB]
            cursor = db[collection].find(query or {}).limit(limit)
            documents = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            return documents

        except Exception as e:
            logger.error(f"MongoDB find error: {e}")
            return []

    async def mongodb_update(self,
                           collection: str,
                           query: Dict,
                           update: Dict,
                           upsert: bool = False) -> int:
        """Update documents in MongoDB"""
        try:
            db = self.connections[DatabaseType.MONGODB]
            result = await db[collection].update_many(
                query,
                {"$set": update},
                upsert=upsert
            )
            return result.modified_count

        except Exception as e:
            logger.error(f"MongoDB update error: {e}")
            return 0

    # Neo4j operations
    async def neo4j_create_node(self, label: str, properties: Dict) -> str:
        """Create node in Neo4j"""
        try:
            driver = self.connections[DatabaseType.NEO4J]

            with driver.session() as session:
                result = session.run(
                    f"CREATE (n:{label} $props) RETURN n.id as id",
                    props=properties
                )
                record = result.single()
                return record["id"]

        except Exception as e:
            logger.error(f"Neo4j create node error: {e}")
            return ""

    async def neo4j_create_relationship(self,
                                      from_node: str,
                                      to_node: str,
                                      relationship: str,
                                      properties: Optional[Dict] = None) -> bool:
        """Create relationship in Neo4j"""
        try:
            driver = self.connections[DatabaseType.NEO4J]

            with driver.session() as session:
                session.run(
                    """
                    MATCH (a), (b)
                    WHERE a.id = $from_id AND b.id = $to_id
                    CREATE (a)-[r:%s $props]->(b)
                    RETURN r
                    """ % relationship,
                    from_id=from_node,
                    to_id=to_node,
                    props=properties or {}
                )

                return True

        except Exception as e:
            logger.error(f"Neo4j create relationship error: {e}")
            return False

    async def neo4j_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute Neo4j query"""
        try:
            driver = self.connections[DatabaseType.NEO4J]

            with driver.session() as session:
                result = session.run(query, params or {})
                records = [dict(record) for record in result]

                return records

        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []

    # Elasticsearch operations
    async def elasticsearch_index(self,
                                 index: str,
                                 document: Dict,
                                 doc_id: Optional[str] = None) -> str:
        """Index document in Elasticsearch"""
        try:
            es = self.connections[DatabaseType.ELASTICSEARCH]

            result = es.index(
                index=index,
                id=doc_id,
                body=document
            )

            return result["_id"]

        except Exception as e:
            logger.error(f"Elasticsearch index error: {e}")
            return ""

    async def elasticsearch_search(self,
                                 index: str,
                                 query: Dict,
                                 size: int = 100) -> List[Dict]:
        """Search documents in Elasticsearch"""
        try:
            es = self.connections[DatabaseType.ELASTICSEARCH]

            result = es.search(
                index=index,
                body=query,
                size=size
            )

            hits = result["hits"]["hits"]
            documents = [hit["_source"] for hit in hits]

            return documents

        except Exception as e:
            logger.error(f"Elasticsearch search error: {e}")
            return []

    # InfluxDB operations
    async def influxdb_write(self, measurement: str, data: Dict, tags: Dict) -> bool:
        """Write data point to InfluxDB"""
        try:
            client = self.connections[DatabaseType.INFLUXDB]
            write_api = client.write_api(write_options=SYNCHRONOUS)

            point = Point(measurement)
            for field, value in data.items():
                point.field(field, value)
            for tag, value in tags.items():
                point.tag(tag, value)

            write_api.write(bucket="dmlogn8n", record=point)
            return True

        except Exception as e:
            logger.error(f"InfluxDB write error: {e}")
            return False

    async def influxdb_query(self, query: str) -> List[Dict]:
        """Query InfluxDB"""
        try:
            client = self.connections[DatabaseType.INFLUXDB]
            query_api = client.query_api()

            result = query_api.query(query)

            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "field": record.get_field(),
                        "measurement": record.get_measurement()
                    })

            return records

        except Exception as e:
            logger.error(f"InfluxDB query error: {e}")
            return []

    # Cassandra operations
    async def cassandra_execute(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute Cassandra query"""
        try:
            session = self.connections[DatabaseType.CASSANDRA]

            if params:
                session.execute(query, params)
            else:
                session.execute(query)

            return True

        except Exception as e:
            logger.error(f"Cassandra execute error: {e}")
            return False

    async def cassandra_select(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Select from Cassandra"""
        try:
            session = self.connections[DatabaseType.CASSANDRA]

            if params:
                rows = session.execute(query, params)
            else:
                rows = session.execute(query)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Cassandra select error: {e}")
            return []

    # Cache operations
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        if key in self.query_cache:
            self.performance_metrics["cache_hits"] += 1
            return self.query_cache[key]

        # Try Redis
        value = await self.redis_get(f"query_cache:{key}")
        if value:
            self.query_cache[key] = value
            self.performance_metrics["cache_hits"] += 1
            return value

        self.performance_metrics["cache_misses"] += 1
        return None

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set in cache"""
        self.query_cache[key] = value
        await self.redis_set(f"query_cache:{key}", value, ttl)

    # Health checks
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections"""
        health_status = {}

        # PostgreSQL
        try:
            await self.execute_postgresql_query("SELECT 1")
            health_status["postgresql"] = True
        except:
            health_status["postgresql"] = False

        # Redis
        try:
            await self.redis_set("health_check", "ok", 10)
            await self.redis_get("health_check")
            health_status["redis"] = True
        except:
            health_status["redis"] = False

        # MongoDB
        try:
            await self.mongodb_find("health_check", {}, 1)
            health_status["mongodb"] = True
        except:
            health_status["mongodb"] = False

        # Neo4j
        try:
            await self.neo4j_query("RETURN 1")
            health_status["neo4j"] = True
        except:
            health_status["neo4j"] = False

        # Elasticsearch
        try:
            await self.elasticsearch_search("health_check", {"query": {"match_all": {}}}, 1)
            health_status["elasticsearch"] = True
        except:
            health_status["elasticsearch"] = False

        # InfluxDB
        try:
            await self.influxdb_query('buckets() |> limit(1)')
            health_status["influxdb"] = True
        except:
            health_status["influxdb"] = False

        # Cassandra
        try:
            await self.cassandra_select("SELECT * FROM system.local LIMIT 1")
            health_status["cassandra"] = True
        except:
            health_status["cassandra"] = False

        return health_status

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_execution_time = (
            self.performance_metrics["total_execution_time"] /
            max(1, self.performance_metrics["queries_executed"])
        )

        cache_hit_rate = (
            self.performance_metrics["cache_hits"] /
            max(1, self.performance_metrics["cache_hits"] + self.performance_metrics["cache_misses"])
        )

        return {
            "queries_executed": self.performance_metrics["queries_executed"],
            "average_execution_time": avg_execution_time,
            "cache_hit_rate": cache_hit_rate,
            "errors": self.performance_metrics["errors"],
            "active_connections": len(self.connections),
            "health_status": await self.health_check()
        }

    async def close(self):
        """Close all database connections"""
        # PostgreSQL
        if DatabaseType.POSTGRESQL in self.pools:
            await self.pools[DatabaseType.POSTGRESQL].close()

        # Redis
        if DatabaseType.REDIS in self.connections:
            for redis_client in self.connections[DatabaseType.REDIS].values():
                await redis_client.close()

        # Cassandra
        if DatabaseType.CASSANDRA in self.connections:
            self.connections[DatabaseType.CASSANDRA].shutdown()

        # Neo4j
        if DatabaseType.NEO4J in self.connections:
            self.connections[DatabaseType.NEO4J].close()

        # InfluxDB
        if DatabaseType.INFLUXDB in self.connections:
            self.connections[DatabaseType.INFLUXDB].close()

        # MongoDB
        if DatabaseType.MONGODB in self.connections:
            self.connections[DatabaseType.MONGODB].client.close()

        # Elasticsearch
        if DatabaseType.ELASTICSEARCH in self.connections:
            self.connections[DatabaseType.ELASTICSEARCH].close()

        logger.info("All database connections closed")


# Initialize global database service
db_service = DatabaseService()