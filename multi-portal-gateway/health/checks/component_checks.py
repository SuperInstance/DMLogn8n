"""
Component-Level Health Checks

Implements health checks for individual system components like databases,
caches, message queues, and external services.
"""

import asyncio
import aiohttp
import asyncpg
import redis.asyncio as redis
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..health_service import HealthCheckResult, HealthStatus

class ComponentChecker:
    """Component-level health checker"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_health(self, component_id: str) -> HealthCheckResult:
        """Check health of a specific component"""
        check_method = getattr(self, f"_check_{component_id.replace('-', '_')}", None)

        if check_method:
            return await check_method()
        else:
            # Generic HTTP health check
            return await self._check_http_component(component_id)

    async def _check_database(self) -> HealthCheckResult:
        """Check database health"""
        start_time = datetime.now()

        try:
            # Database configuration
            db_config = self.config.get("database", {})
            connection_string = db_config.get("connection_string")

            if not connection_string:
                return HealthCheckResult(
                    check_id="database",
                    check_name="Database Component",
                    level="component",
                    status=HealthStatus.CRITICAL,
                    message="Database connection string not configured"
                )

            # Test database connection
            conn = await asyncpg.connect(connection_string)

            # Run basic health query
            result = await conn.fetchval("SELECT 1")

            # Get database stats
            db_stats = await self._get_database_stats(conn)

            await conn.close()

            if result == 1:
                # Calculate health score based on performance metrics
                score = self._calculate_database_score(db_stats)

                return HealthCheckResult(
                    check_id="database",
                    check_name="Database Component",
                    level="component",
                    status=HealthStatus.HEALTHY if score > 80 else HealthStatus.WARNING,
                    message="Database connection successful",
                    details=db_stats,
                    metrics={
                        "score": score,
                        "connection_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                    },
                    timestamp=start_time,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
            else:
                return HealthCheckResult(
                    check_id="database",
                    check_name="Database Component",
                    level="component",
                    status=HealthStatus.CRITICAL,
                    message="Database query failed",
                    timestamp=start_time,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )

        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                check_id="database",
                check_name="Database Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _get_database_stats(self, conn) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            stats = {}

            # Get connection count
            stats["active_connections"] = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )

            # Get database size
            stats["database_size_mb"] = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )

            # Get slow queries count (queries taking more than 1 second)
            stats["slow_queries"] = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_statements WHERE mean_time > 1000"
            )

            # Get cache hit ratio
            cache_hit_ratio = await conn.fetchval(
                "SELECT round(sum(blks_hit)::numeric / sum(blks_hit + blks_read), 4) * 100 "
                "FROM pg_stat_database WHERE datname = current_database()"
            )
            stats["cache_hit_ratio_percent"] = cache_hit_ratio or 0

            return stats

        except Exception as e:
            self.logger.warning(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    def _calculate_database_score(self, stats: Dict[str, Any]) -> float:
        """Calculate database health score based on statistics"""
        score = 100.0

        # Penalize high connection count
        active_connections = stats.get("active_connections", 0)
        if active_connections > 80:
            score -= 20
        elif active_connections > 50:
            score -= 10

        # Penalize slow queries
        slow_queries = stats.get("slow_queries", 0)
        if slow_queries > 10:
            score -= 20
        elif slow_queries > 5:
            score -= 10

        # Reward good cache hit ratio
        cache_hit_ratio = stats.get("cache_hit_ratio_percent", 0)
        if cache_hit_ratio > 95:
            score += 5
        elif cache_hit_ratio < 80:
            score -= 15

        return max(0, min(100, score))

    async def _check_cache(self) -> HealthCheckResult:
        """Check Redis cache health"""
        start_time = datetime.now()

        try:
            cache_config = self.config.get("cache", {})
            host = cache_config.get("host", "localhost")
            port = cache_config.get("port", 6379)
            password = cache_config.get("password")

            # Connect to Redis
            redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True
            )

            # Test Redis connection
            await redis_client.ping()

            # Get Redis info
            info = await redis_client.info()

            # Calculate memory usage percentage
            max_memory = info.get("maxmemory", 0)
            used_memory = info.get("used_memory", 0)
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0

            # Get connection count
            connected_clients = info.get("connected_clients", 0)

            # Calculate hit rate
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0

            await redis_client.close()

            # Determine health status
            score = 100.0

            if memory_usage_percent > 90:
                score -= 30
            elif memory_usage_percent > 80:
                score -= 15

            if connected_clients > 100:
                score -= 20
            elif connected_clients > 50:
                score -= 10

            if hit_rate < 70:
                score -= 20
            elif hit_rate < 85:
                score -= 10

            status = HealthStatus.HEALTHY if score > 80 else HealthStatus.WARNING if score > 60 else HealthStatus.DEGRADED

            return HealthCheckResult(
                check_id="cache",
                check_name="Cache Component",
                level="component",
                status=status,
                message=f"Cache operational - Hit rate: {hit_rate:.1f}%",
                details={
                    "memory_usage_percent": memory_usage_percent,
                    "connected_clients": connected_clients,
                    "hit_rate_percent": hit_rate,
                    "total_commands_processed": info.get("total_commands_processed", 0)
                },
                metrics={
                    "score": score,
                    "memory_usage": memory_usage_percent,
                    "hit_rate": hit_rate,
                    "connections": connected_clients
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Cache health check failed: {e}")
            return HealthCheckResult(
                check_id="cache",
                check_name="Cache Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"Cache connection failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_message_queue(self) -> HealthCheckResult:
        """Check message queue (RabbitMQ) health"""
        start_time = datetime.now()

        try:
            mq_config = self.config.get("message_queue", {})
            host = mq_config.get("host", "localhost")
            port = mq_config.get("port", 15672)
            username = mq_config.get("username", "guest")
            password = mq_config.get("password", "guest")

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Check RabbitMQ management API
            url = f"http://{host}:{port}/api/overview"
            auth = aiohttp.BasicAuth(username, password)

            async with self.session.get(url, auth=auth) as response:
                if response.status != 200:
                    raise Exception(f"RabbitMQ API returned status {response.status}")

                overview = await response.json()

            # Get queue details
            queues_url = f"http://{host}:{port}/api/queues"
            async with self.session.get(queues_url, auth=auth) as response:
                if response.status == 200:
                    queues = await response.json()
                else:
                    queues = []

            # Calculate health metrics
            total_messages = sum(q.get("messages", 0) for q in queues)
            total_connections = overview.get("object_totals", {}).get("connections", 0)
            total_channels = overview.get("object_totals", {}).get("channels", 0)

            # Check for queue depth issues
            queue_depths = {q["name"]: q.get("messages", 0) for q in queues}
            max_queue_depth = max(queue_depths.values()) if queue_depths else 0

            # Calculate health score
            score = 100.0

            if total_messages > 10000:
                score -= 25
            elif total_messages > 5000:
                score -= 15

            if total_connections > 100:
                score -= 15
            elif total_connections > 50:
                score -= 5

            if max_queue_depth > 1000:
                score -= 20
            elif max_queue_depth > 500:
                score -= 10

            status = HealthStatus.HEALTHY if score > 85 else HealthStatus.WARNING if score > 70 else HealthStatus.DEGRADED

            return HealthCheckResult(
                check_id="message-queue",
                check_name="Message Queue Component",
                level="component",
                status=status,
                message=f"Message queue operational - {total_messages} total messages",
                details={
                    "total_messages": total_messages,
                    "total_connections": total_connections,
                    "total_channels": total_channels,
                    "queue_count": len(queues),
                    "queue_depths": queue_depths,
                    "node_status": overview.get("rabbitmq_version", "unknown")
                },
                metrics={
                    "score": score,
                    "total_messages": total_messages,
                    "connections": total_connections,
                    "max_queue_depth": max_queue_depth
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Message queue health check failed: {e}")
            return HealthCheckResult(
                check_id="message-queue",
                check_name="Message Queue Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"Message queue check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_filesystem(self) -> HealthCheckResult:
        """Check filesystem health"""
        start_time = datetime.now()

        try:
            fs_config = self.config.get("filesystem", {})
            mount_points = fs_config.get("mount_points", ["/"])

            results = []
            total_score = 0

            for mount_point in mount_points:
                try:
                    usage = psutil.disk_usage(mount_point)
                    used_percent = (usage.used / usage.total) * 100

                    # Check disk I/O
                    disk_io = psutil.disk_io_counters()
                    io_score = 100.0

                    if disk_io:
                        # Simple I/O health check based on activity
                        read_time = disk_io.read_time
                        write_time = disk_io.write_time
                        total_time = read_time + write_time

                        if total_time > 1000:  # More than 1 second of I/O wait
                            io_score = max(0, 100 - (total_time / 100))

                    # Calculate individual mount point score
                    mount_score = 100.0

                    if used_percent > 95:
                        mount_score -= 40
                    elif used_percent > 90:
                        mount_score -= 25
                    elif used_percent > 80:
                        mount_score -= 10

                    mount_score = min(mount_score, io_score)
                    total_score += mount_score

                    results.append({
                        "mount_point": mount_point,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "used_percent": round(used_percent, 2),
                        "score": mount_score,
                        "io_score": io_score
                    })

                except Exception as e:
                    results.append({
                        "mount_point": mount_point,
                        "error": str(e),
                        "score": 0
                    })

            # Calculate overall filesystem score
            overall_score = total_score / len(results) if results else 0

            # Determine status
            status = HealthStatus.HEALTHY if overall_score > 85 else HealthStatus.WARNING if overall_score > 70 else HealthStatus.DEGRADED

            return HealthCheckResult(
                check_id="filesystem",
                check_name="Filesystem Component",
                level="component",
                status=status,
                message=f"Filesystem check completed - Average score: {overall_score:.1f}%",
                details={
                    "mount_points": results,
                    "total_mount_points": len(results)
                },
                metrics={
                    "score": overall_score,
                    "mount_points_checked": len(results)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Filesystem health check failed: {e}")
            return HealthCheckResult(
                check_id="filesystem",
                check_name="Filesystem Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"Filesystem check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_ssl_certificates(self) -> HealthCheckResult:
        """Check SSL certificate expiry"""
        start_time = datetime.now()

        try:
            ssl_config = self.config.get("ssl_certificates", {})
            certificates = ssl_config.get("certificates", [])

            if not certificates:
                return HealthCheckResult(
                    check_id="ssl-certificates",
                    check_name="SSL Certificates Component",
                    level="component",
                    status=HealthStatus.HEALTHY,
                    message="No SSL certificates configured for monitoring"
                )

            results = []
            total_score = 0
            now = datetime.now()

            for cert_config in certificates:
                try:
                    hostname = cert_config["hostname"]
                    port = cert_config.get("port", 443)

                    # Check SSL certificate
                    import ssl
                    import socket

                    context = ssl.create_default_context()
                    with socket.create_connection((hostname, port), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                            cert = ssock.getpeercert()
                            expiry_date = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                            days_until_expiry = (expiry_date - now).days

                            # Calculate score based on expiry
                            cert_score = 100.0

                            if days_until_expiry < 7:
                                cert_score = 0  # Critical
                            elif days_until_expiry < 30:
                                cert_score = 30  # Warning
                            elif days_until_expiry < 90:
                                cert_score = 70  # Caution

                            total_score += cert_score

                            results.append({
                                "hostname": hostname,
                                "port": port,
                                "expiry_date": expiry_date.isoformat(),
                                "days_until_expiry": days_until_expiry,
                                "issuer": cert.get("issuer"),
                                "score": cert_score
                            })

                except Exception as e:
                    results.append({
                        "hostname": hostname,
                        "error": str(e),
                        "score": 0
                    })

            # Calculate overall score
            overall_score = total_score / len(results) if results else 0

            # Determine status
            if overall_score == 100:
                status = HealthStatus.HEALTHY
            elif overall_score >= 70:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="ssl-certificates",
                check_name="SSL Certificates Component",
                level="component",
                status=status,
                message=f"SSL certificate check completed - Score: {overall_score:.1f}%",
                details={
                    "certificates": results,
                    "total_certificates": len(certificates)
                },
                metrics={
                    "score": overall_score,
                    "certificates_checked": len(certificates)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"SSL certificate check failed: {e}")
            return HealthCheckResult(
                check_id="ssl-certificates",
                check_name="SSL Certificates Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"SSL certificate check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity to external services"""
        start_time = datetime.now()

        try:
            network_config = self.config.get("network", {})
            endpoints = network_config.get("endpoints", [
                {"name": "google-dns", "host": "8.8.8.8", "port": 53},
                {"name": "cloudflare-dns", "host": "1.1.1.1", "port": 53}
            ])

            results = []
            total_score = 0

            for endpoint in endpoints:
                try:
                    host = endpoint["host"]
                    port = endpoint.get("port", 80)
                    timeout = endpoint.get("timeout", 5)

                    # Test connectivity
                    start = datetime.now()
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port),
                        timeout=timeout
                    )

                    connection_time = (datetime.now() - start).total_seconds() * 1000
                    writer.close()
                    await writer.wait_closed()

                    # Calculate score based on response time
                    endpoint_score = 100.0

                    if connection_time > 1000:
                        endpoint_score -= 30
                    elif connection_time > 500:
                        endpoint_score -= 15
                    elif connection_time > 200:
                        endpoint_score -= 5

                    total_score += endpoint_score

                    results.append({
                        "name": endpoint["name"],
                        "host": host,
                        "port": port,
                        "connection_time_ms": round(connection_time, 2),
                        "connected": True,
                        "score": endpoint_score
                    })

                except Exception as e:
                    results.append({
                        "name": endpoint["name"],
                        "host": host,
                        "port": port,
                        "connected": False,
                        "error": str(e),
                        "score": 0
                    })

            # Calculate overall score
            overall_score = total_score / len(results) if results else 0

            # Determine status
            status = HealthStatus.HEALTHY if overall_score > 90 else HealthStatus.WARNING if overall_score > 75 else HealthStatus.DEGRADED

            return HealthCheckResult(
                check_id="network-connectivity",
                check_name="Network Connectivity Component",
                level="component",
                status=status,
                message=f"Network connectivity check completed - Score: {overall_score:.1f}%",
                details={
                    "endpoints": results,
                    "total_endpoints": len(endpoints)
                },
                metrics={
                    "score": overall_score,
                    "endpoints_checked": len(endpoints)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Network connectivity check failed: {e}")
            return HealthCheckResult(
                check_id="network-connectivity",
                check_name="Network Connectivity Component",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"Network connectivity check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_http_component(self, component_id: str) -> HealthCheckResult:
        """Generic HTTP component health check"""
        start_time = datetime.now()

        try:
            component_config = self.config.get("http_components", {}).get(component_id, {})
            if not component_config:
                return HealthCheckResult(
                    check_id=component_id,
                    check_name=f"HTTP Component: {component_id}",
                    level="component",
                    status=HealthStatus.UNKNOWN,
                    message=f"No configuration found for component: {component_id}"
                )

            url = component_config["url"]
            expected_status = component_config.get("expected_status", 200)
            timeout = component_config.get("timeout", 10)

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Make HTTP request
            start_request = datetime.now()
            async with self.session.get(url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000
                status_code = response.status

                # Try to get response content
                try:
                    content = await response.text()
                    content_length = len(content)
                except:
                    content_length = 0

            # Calculate health score
            score = 100.0

            if status_code != expected_status:
                score -= 50

            if response_time > 5000:
                score -= 30
            elif response_time > 2000:
                score -= 15
            elif response_time > 1000:
                score -= 5

            # Determine status
            if score >= 90:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id=component_id,
                check_name=f"HTTP Component: {component_id}",
                level="component",
                status=status,
                message=f"HTTP check completed - Status: {status_code}, Time: {response_time:.1f}ms",
                details={
                    "url": url,
                    "status_code": status_code,
                    "expected_status": expected_status,
                    "response_time_ms": round(response_time, 2),
                    "content_length": content_length,
                    "headers": dict(response.headers)
                },
                metrics={
                    "score": score,
                    "response_time": response_time,
                    "status_code": status_code
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"HTTP component {component_id} health check failed: {e}")
            return HealthCheckResult(
                check_id=component_id,
                check_name=f"HTTP Component: {component_id}",
                level="component",
                status=HealthStatus.CRITICAL,
                message=f"HTTP check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )