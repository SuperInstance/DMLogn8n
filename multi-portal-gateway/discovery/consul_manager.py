#!/usr/bin/env python3
"""
Consul Integration Manager for DMLogn8n Multi-Agent Platform

This module provides comprehensive Consul integration including:
- Consul client management and connection pooling
- Multi-datacenter support
- Session management for distributed locks
- Event handling and service mesh integration
- Backup and recovery operations
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp
import consul.aio
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConsulConfig:
    """Consul configuration parameters"""
    host: str = 'localhost'
    port: int = 8500
    token: Optional[str] = None
    datacenter: str = 'dc1'
    scheme: str = 'http'
    verify: bool = True
    consistency: str = 'default'  # default, consistent, stale
    namespace: Optional[str] = None
    partition: Optional[str] = None

@dataclass
class DatacenterConfig:
    """Multi-datacenter configuration"""
    name: str
    primary_consul: ConsulConfig
    secondary_consuls: List[ConsulConfig]
    wan_join_token: Optional[str] = None
    replication_enabled: bool = True
    latency_threshold_ms: int = 100

class ConsulManager:
    """
    Main Consul integration manager for DMLogn8n platform
    """

    def __init__(self, config: ConsulConfig):
        self.config = config
        self.consul = None
        self.session_id = None
        self.datacenters = {}
        self.event_handlers = {}
        self.service_watchers = {}
        self.locks = {}
        self._connected = False
        self._connection_pool = []
        self._max_connections = 10

    async def initialize(self) -> bool:
        """Initialize Consul connection and setup manager"""
        try:
            # Initialize Consul client
            self.consul = consul.aio.Consul(
                host=self.config.host,
                port=self.config.port,
                token=self.config.token,
                datacenter=self.config.datacenter,
                scheme=self.config.scheme,
                verify=self.config.verify,
                consistency=self.config.consistency,
                namespace=self.config.namespace,
                partition=self.config.partition
            )

            # Test connection
            await self._test_connection()

            # Create session for distributed operations
            await self._create_session()

            # Setup service mesh integration if available
            await self._setup_service_mesh()

            # Start background tasks
            asyncio.create_task(self._maintain_session())
            asyncio.create_task(self._monitor_consul_health())

            self._connected = True
            logger.info(f"Consul manager initialized successfully for datacenter {self.config.datacenter}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Consul manager: {e}")
            return False

    async def _test_connection(self) -> bool:
        """Test Consul connection and get cluster info"""
        try:
            # Test basic connection
            leader_info = await self.consul.status.leader()
            if not leader_info:
                raise Exception("No Consul leader available")

            # Get cluster info
            agents = await self.consul.agent.members()
            logger.info(f"Connected to Consul cluster. Leader: {leader_info}")
            logger.info(f"Cluster members: {len(agents)}")

            # Test KV store
            test_key = "dmlogn8n/system/health_check"
            await self.consul.kv.put(test_key, "ok", acquire=self.session_id)
            _, data = await self.consul.kv.get(test_key)
            if not data:
                raise Exception("KV store test failed")
            await self.consul.kv.delete(test_key)

            return True

        except Exception as e:
            logger.error(f"Consul connection test failed: {e}")
            raise

    async def _create_session(self) -> str:
        """Create Consul session for distributed operations"""
        try:
            session_config = {
                'name': 'dmlogn8n-discovery-manager',
                'ttl': '30s',
                'lock_delay': '0s',
                'behavior': 'release'
            }

            self.session_id = await self.consul.session.create(**session_config)
            logger.info(f"Created Consul session: {self.session_id}")
            return self.session_id

        except Exception as e:
            logger.error(f"Failed to create Consul session: {e}")
            raise

    async def _maintain_session(self):
        """Maintain Consul session with periodic renewal"""
        while self._connected:
            try:
                if self.session_id:
                    await self.consul.session.renew(self.session_id)
                    logger.debug("Consul session renewed")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Failed to renew session: {e}")
                # Try to recreate session
                try:
                    await self._create_session()
                except Exception as e2:
                    logger.error(f"Failed to recreate session: {e2}")
                    await asyncio.sleep(5)

    async def _monitor_consul_health(self):
        """Monitor Consul cluster health and handle failover"""
        while self._connected:
            try:
                # Check leader status
                leader = await self.consul.status.leader()
                if not leader:
                    logger.warning("No Consul leader available")

                # Check cluster health
                agents = await self.consul.agent.members()
                healthy_agents = sum(1 for agent in agents.values() if agent.get('Status') == 1)

                if healthy_agents < len(agents) // 2:
                    logger.warning(f"Cluster degraded: {healthy_agents}/{len(agents)} agents healthy")

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(10)

    async def _setup_service_mesh_integration(self):
        """Setup service mesh integration capabilities"""
        try:
            # Create service mesh configuration
            mesh_config = {
                'enabled': True,
                'transparent_proxy': {
                    'inbound_port': 20000,
                    'outbound_port': 21000
                },
                'gateways': {
                    'api_gateway': {
                        'port': 8443,
                        'protocol': 'http'
                    }
                }
            }

            # Store mesh config in KV
            await self.consul.kv.put(
                'dmlogn8n/mesh/config',
                json.dumps(mesh_config)
            )

            logger.info("Service mesh integration configured")

        except Exception as e:
            logger.error(f"Service mesh setup failed: {e}")

    async def add_datacenter(self, dc_config: DatacenterConfig):
        """Add secondary datacenter for multi-DC support"""
        try:
            self.datacenters[dc_config.name] = dc_config

            # Setup WAN federation if token provided
            if dc_config.wan_join_token:
                await self._setup_wan_federation(dc_config)

            logger.info(f"Added datacenter: {dc_config.name}")

        except Exception as e:
            logger.error(f"Failed to add datacenter {dc_config.name}: {e}")

    async def _setup_wan_federation(self, dc_config: DatacenterConfig):
        """Setup WAN federation between datacenters"""
        try:
            # Join WAN using token
            join_url = f"{self.config.scheme}://{self.config.host}:{self.config.port}/v1/agent/wan/join"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    join_url,
                    headers={'X-Consul-Token': dc_config.wan_join_token},
                    json={'address': dc_config.primary_consul.host}
                ) as response:
                    if response.status == 200:
                        logger.info(f"WAN federation established with {dc_config.name}")
                    else:
                        logger.error(f"WAN federation failed: {response.status}")

        except Exception as e:
            logger.error(f"WAN federation setup error: {e}")

    async def create_distributed_lock(self, lock_key: str, timeout: int = 30) -> bool:
        """Create distributed lock using Consul session"""
        try:
            lock_path = f"dmlogn8n/locks/{lock_key}"

            # Try to acquire lock
            success = await self.consul.kv.put(
                lock_path,
                self.session_id,
                acquire=self.session_id
            )

            if success:
                self.locks[lock_key] = {
                    'session_id': self.session_id,
                    'acquired_at': datetime.now(),
                    'timeout': timeout
                }
                logger.info(f"Acquired distributed lock: {lock_key}")

                # Setup automatic lock release
                asyncio.create_task(self._auto_release_lock(lock_key, timeout))

            return success

        except Exception as e:
            logger.error(f"Failed to create lock {lock_key}: {e}")
            return False

    async def release_distributed_lock(self, lock_key: str) -> bool:
        """Release distributed lock"""
        try:
            if lock_key not in self.locks:
                return False

            lock_path = f"dmlogn8n/locks/{lock_key}"

            # Release lock by deleting the key
            await self.consul.kv.delete(lock_path)

            del self.locks[lock_key]
            logger.info(f"Released distributed lock: {lock_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
            return False

    async def _auto_release_lock(self, lock_key: str, timeout: int):
        """Automatically release lock after timeout"""
        await asyncio.sleep(timeout)
        await self.release_distributed_lock(lock_key)

    async def watch_service_changes(self, service_name: str, callback):
        """Watch for changes in a specific service"""
        try:
            index = None

            while self._connected:
                try:
                    # Get service with blocking query
                    index, services = await self.consul.health.service(
                        service_name,
                        index=index,
                        wait='30s'
                    )

                    # Call callback with service changes
                    if callback:
                        await callback(services)

                except Exception as e:
                    logger.error(f"Service watch error for {service_name}: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Failed to watch service {service_name}: {e}")

    async def emit_event(self, event_name: str, payload: Any = None, node_filter: Optional[str] = None):
        """Emit custom event through Consul"""
        try:
            event_payload = json.dumps(payload) if payload else ""

            await self.consul.event.fire(
                event_name,
                event_payload,
                node_filter=node_filter
            )

            logger.info(f"Emitted event: {event_name}")

        except Exception as e:
            logger.error(f"Failed to emit event {event_name}: {e}")

    async def register_event_handler(self, event_name: str, handler):
        """Register handler for specific events"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []

        self.event_handlers[event_name].append(handler)

        # Start event listener for this event type
        asyncio.create_task(self._listen_for_events(event_name))

    async def _listen_for_events(self, event_name: str):
        """Listen for events of specific type"""
        try:
            index = None

            while self._connected:
                try:
                    index, events = await self.consul.event.list(
                        name=event_name,
                        index=index,
                        wait='30s'
                    )

                    # Process events
                    for event in events:
                        if event_name in self.event_handlers:
                            for handler in self.event_handlers[event_name]:
                                try:
                                    await handler(event)
                                except Exception as e:
                                    logger.error(f"Event handler error: {e}")

                except Exception as e:
                    logger.error(f"Event listening error: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Failed to listen for events {event_name}: {e}")

    async def backup_kv_store(self, backup_path: str, prefix: str = "") -> Dict[str, Any]:
        """Backup Consul KV store"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'datacenter': self.config.datacenter,
                'prefix': prefix,
                'keys': {}
            }

            # Get all keys with prefix
            index, keys = await self.consul.kv.get(prefix, recurse=True, keys=True)

            if keys:
                for key in keys:
                    _, value = await self.consul.kv.get(key)
                    if value:
                        backup_data['keys'][key] = {
                            'value': value['Value'].decode('utf-8') if value['Value'] else None,
                            'flags': value.get('Flags', 0),
                            'session': value.get('Session'),
                            'lock_index': value.get('LockIndex', 0),
                            'create_index': value.get('CreateIndex', 0),
                            'modify_index': value.get('ModifyIndex', 0)
                        }

            # Save backup to file
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"KV store backup completed: {backup_path}")
            return backup_data

        except Exception as e:
            logger.error(f"KV backup failed: {e}")
            raise

    async def restore_kv_store(self, backup_path: str, overwrite: bool = False) -> bool:
        """Restore Consul KV store from backup"""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            restored_count = 0

            for key, data in backup_data['keys'].items():
                try:
                    # Check if key exists and overwrite is False
                    if not overwrite:
                        _, existing = await self.consul.kv.get(key)
                        if existing:
                            continue

                    # Restore key
                    await self.consul.kv.put(
                        key,
                        data['value'],
                        flags=data['flags'],
                        acquire=self.session_id if data['session'] else None
                    )

                    restored_count += 1

                except Exception as e:
                    logger.error(f"Failed to restore key {key}: {e}")

            logger.info(f"KV store restored: {restored_count} keys")
            return True

        except Exception as e:
            logger.error(f"KV restore failed: {e}")
            return False

    async def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status"""
        try:
            status = {
                'datacenter': self.config.datacenter,
                'timestamp': datetime.now().isoformat(),
                'leader': await self.consul.status.leader(),
                'peers': await self.consul.status.peers(),
                'services': {},
                'nodes': {},
                'health_summary': {}
            }

            # Get service status
            services = await self.consul.agent.services()
            status['services'] = {
                'count': len(services),
                'names': list(services.keys())
            }

            # Get node status
            agents = await self.consul.agent.members()
            status['nodes'] = {
                'total': len(agents),
                'healthy': sum(1 for agent in agents.values() if agent.get('Status') == 1),
                'unhealthy': sum(1 for agent in agents.values() if agent.get('Status') != 1)
            }

            # Get health summary
            _, checks = await self.consul.health.state('any')
            status['health_summary'] = {
                'passing': sum(1 for check in checks if check['Status'] == 'passing'),
                'warning': sum(1 for check in checks if check['Status'] == 'warning'),
                'critical': sum(1 for check in checks if check['Status'] == 'critical')
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            return {}

    async def cleanup(self):
        """Cleanup resources and close connections"""
        try:
            self._connected = False

            # Release all locks
            for lock_key in list(self.locks.keys()):
                await self.release_distributed_lock(lock_key)

            # Destroy session
            if self.session_id:
                await self.consul.session.destroy(self.session_id)

            # Close connections
            for conn in self._connection_pool:
                conn.close()

            logger.info("Consul manager cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    @asynccontextmanager
    async def get_connection(self):
        """Get Consul connection from pool"""
        if self._connection_pool:
            conn = self._connection_pool.pop()
        else:
            conn = consul.aio.Consul(
                host=self.config.host,
                port=self.config.port,
                token=self.config.token,
                datacenter=self.config.datacenter
            )

        try:
            yield conn
        finally:
            if len(self._connection_pool) < self._max_connections:
                self._connection_pool.append(conn)

# Export main classes
__all__ = [
    'ConsulManager',
    'ConsulConfig',
    'DatacenterConfig'
]