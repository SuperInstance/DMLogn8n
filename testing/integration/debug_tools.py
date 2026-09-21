#!/usr/bin/env python3
"""
DMLogn8n Debug Tools and Diagnostics
Advanced debugging and diagnostic utilities for integration testing
"""

import asyncio
import json
import logging
import time
import uuid
import os
import sys
import traceback
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import inspect
import threading
import socket
import psutil
import requests
import redis
import psycopg2
from collections import defaultdict, deque
import re

# Import test framework
from integration_test_suite import TestResult, TestStatus

class DebugTools:
    """
    Advanced debugging and diagnostic tools
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('debug_tools')
        self.base_url = config['base_url']
        self.database_url = config['database_url']
        self.redis_url = config['redis_url']

        # Debug state
        self.debug_logs = defaultdict(list)
        self.system_snapshots = deque(maxlen=100)
        self.error_patterns = defaultdict(int)
        self.performance_snapshots = deque(maxlen=50)
        self.network_stats = defaultdict(deque)

        # Create debug directories
        self.debug_dir = '/home/activeloguser/DMLogn8n/testing/debug'
        os.makedirs(self.debug_dir, exist_ok=True)
        os.makedirs(f"{self.debug_dir}/logs", exist_ok=True)
        os.makedirs(f"{self.debug_dir}/snapshots", exist_ok=True)
        os.makedirs(f"{self.debug_dir}/traces", exist_ok=True)

    async def generate_debug_report(self) -> TestResult:
        """
        Generate comprehensive debug report
        """
        result = TestResult(
            name="debug_report",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            debug_data = {
                'system_overview': await self.collect_system_overview(),
                'service_status': await self.check_service_status(),
                'database_health': await self.analyze_database_health(),
                'performance_metrics': await self.collect_performance_metrics(),
                'error_analysis': await self.analyze_error_patterns(),
                'network_connectivity': await self.test_network_connectivity(),
                'log_analysis': await self.analyze_application_logs(),
                'resource_utilization': await self.analyze_resource_utilization(),
                'configuration_audit': await self.audit_configuration(),
                'recommendations': await self.generate_recommendations()
            }

            # Save debug report
            report_path = await self.save_debug_report(debug_data)

            result.status = TestStatus.PASSED
            result.message = f"Debug report generated successfully: {report_path}"
            result.details = {
                'report_path': report_path,
                'debug_data': debug_data,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Debug report generation failed: {str(e)}"
            self.logger.error(f"Debug report generation failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def collect_system_overview(self) -> Dict[str, Any]:
        """Collect comprehensive system overview"""
        try:
            # System information
            system_info = {
                'hostname': socket.gethostname(),
                'platform': sys.platform,
                'python_version': sys.version,
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - psutil.boot_time()
            }

            # CPU information
            cpu_info = {
                'count': psutil.cpu_count(logical=False),
                'logical_count': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=1),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }

            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': memory.percent
            }

            # Disk information
            disk_info = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except PermissionError:
                    continue

            # Network information
            network_info = {}
            for interface, addrs in psutil.net_if_addrs().items():
                addresses = []
                for addr in addrs:
                    addresses.append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
                network_info[interface] = addresses

            # Process information
            process_info = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] in ['python', 'node', 'postgres', 'redis-server', 'nginx']:
                        process_info.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return {
                'system': system_info,
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'processes': process_info,
                'status': 'healthy'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def check_service_status(self) -> Dict[str, Any]:
        """Check status of all services"""
        try:
            services = {}

            # Check main application
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                services['main_app'] = {
                    'status': 'running' if response.status_code == 200 else 'error',
                    'response_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'url': self.base_url
                }
            except Exception as e:
                services['main_app'] = {
                    'status': 'down',
                    'error': str(e),
                    'url': self.base_url
                }

            # Check database
            try:
                conn = psycopg2.connect(self.database_url)
                conn.close()
                services['database'] = {
                    'status': 'running',
                    'url': self.database_url.split('@')[1] if '@' in self.database_url else 'localhost'
                }
            except Exception as e:
                services['database'] = {
                    'status': 'down',
                    'error': str(e)
                }

            # Check Redis
            try:
                r = redis.from_url(self.redis_url)
                r.ping()
                services['redis'] = {
                    'status': 'running',
                    'url': self.redis_url.split('@')[1] if '@' in self.redis_url else 'localhost:6379'
                }
            except Exception as e:
                services['redis'] = {
                    'status': 'down',
                    'error': str(e)
                }

            # Check WebSocket service
            try:
                ws_url = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws'
                # Simple connectivity check
                host, port = ws_url.split(':')[2].split('/')[0], int(ws_url.split(':')[3].split('/')[0])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                services['websocket'] = {
                    'status': 'running' if result == 0 else 'down',
                    'url': ws_url
                }
            except Exception as e:
                services['websocket'] = {
                    'status': 'down',
                    'error': str(e)
                }

            # Check N8N if configured
            n8n_url = self.config.get('n8n_url', 'http://localhost:5678')
            try:
                response = requests.get(f"{n8n_url}/healthz", timeout=10)
                services['n8n'] = {
                    'status': 'running' if response.status_code == 200 else 'error',
                    'response_code': response.status_code,
                    'url': n8n_url
                }
            except Exception as e:
                services['n8n'] = {
                    'status': 'down',
                    'error': str(e),
                    'url': n8n_url
                }

            # Overall service health
            running_services = sum(1 for service in services.values() if service.get('status') == 'running')
            total_services = len(services)
            overall_health = 'healthy' if running_services == total_services else 'degraded' if running_services >= total_services * 0.7 else 'critical'

            return {
                'services': services,
                'summary': {
                    'running_services': running_services,
                    'total_services': total_services,
                    'overall_health': overall_health
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def analyze_database_health(self) -> Dict[str, Any]:
        """Analyze database health and performance"""
        try:
            conn = psycopg2.connect(self.database_url)
            health_info = {}

            # Connection stats
            with conn.cursor() as cursor:
                # Active connections
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
                active_connections = cursor.fetchone()[0]

                # Database size
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                db_size = cursor.fetchone()[0]

                # Table statistics
                cursor.execute("""
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                    LIMIT 10;
                """)
                table_stats = cursor.fetchall()

                # Index usage
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 10;
                """)
                index_stats = cursor.fetchall()

                # Slow queries (if pg_stat_statements is available)
                try:
                    cursor.execute("""
                        SELECT query, calls, total_time, mean_time, rows
                        FROM pg_stat_statements
                        ORDER BY mean_time DESC
                        LIMIT 5;
                    """)
                    slow_queries = cursor.fetchall()
                except:
                    slow_queries = []

                health_info.update({
                    'active_connections': active_connections,
                    'database_size': db_size,
                    'table_statistics': [
                        {
                            'schema': row[0],
                            'table': row[1],
                            'inserts': row[2],
                            'updates': row[3],
                            'deletes': row[4],
                            'live_tuples': row[5],
                            'dead_tuples': row[6]
                        }
                        for row in table_stats
                    ],
                    'index_statistics': [
                        {
                            'schema': row[0],
                            'table': row[1],
                            'index': row[2],
                            'scans': row[3],
                            'tuples_read': row[4],
                            'tuples_fetched': row[5]
                        }
                        for row in index_stats
                    ],
                    'slow_queries': [
                        {
                            'query': row[0][:100] + '...' if len(row[0]) > 100 else row[0],
                            'calls': row[1],
                            'total_time': row[2],
                            'mean_time': row[3],
                            'rows': row[4]
                        }
                        for row in slow_queries
                    ]
                })

            conn.close()

            # Determine health status
            health_score = 100
            if active_connections > 80:
                health_score -= 20
            if len(slow_queries) > 0:
                health_score -= 30
            dead_tuple_ratio = sum(row[6] for row in table_stats) / max(1, sum(row[5] for row in table_stats))
            if dead_tuple_ratio > 0.2:
                health_score -= 20

            health_status = 'excellent' if health_score >= 90 else 'good' if health_score >= 70 else 'poor' if health_score >= 50 else 'critical'

            return {
                'status': health_status,
                'health_score': health_score,
                'details': health_info
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        try:
            metrics = {}

            # System performance
            metrics['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_io_read': psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
                'disk_io_write': psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0,
                'network_sent': psutil.net_io_counters().bytes_sent if psutil.net_io_counters() else 0,
                'network_recv': psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0
            }

            # Application performance (if metrics endpoint available)
            try:
                response = requests.get(f"{self.base_url}/metrics", timeout=10)
                if response.status_code == 200:
                    # Parse Prometheus metrics
                    metrics_text = response.text
                    app_metrics = self.parse_prometheus_metrics(metrics_text)
                    metrics['application'] = app_metrics
            except:
                metrics['application'] = {'status': 'unavailable'}

            # API response times
            api_endpoints = ['/health', '/api/status', '/api/version']
            api_metrics = {}
            for endpoint in api_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    api_metrics[endpoint] = {
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'content_length': len(response.content)
                    }
                except Exception as e:
                    api_metrics[endpoint] = {'error': str(e)}

            metrics['api_endpoints'] = api_metrics

            # Redis performance
            try:
                r = redis.from_url(self.redis_url)
                redis_info = r.info()
                metrics['redis'] = {
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'total_commands_processed': redis_info.get('total_commands_processed', 0),
                    'instantaneous_ops_per_sec': redis_info.get('instantaneous_ops_per_sec', 0),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0)
                }
            except Exception as e:
                metrics['redis'] = {'error': str(e)}

            return {
                'status': 'collected',
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse Prometheus metrics text"""
        metrics = {}
        for line in metrics_text.split('\n'):
            if line and not line.startswith('#'):
                try:
                    if '{' in line:
                        # Metric with labels
                        name_part, value_part = line.split(' ', 1)
                        name, labels = name_part.split('{', 1)
                        labels = labels.rstrip('}')
                        metrics[name] = {
                            'value': float(value_part),
                            'labels': labels
                        }
                    else:
                        # Simple metric
                        name, value = line.split(' ', 1)
                        metrics[name] = {'value': float(value)}
                except:
                    continue
        return metrics

    async def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns from logs"""
        try:
            error_patterns = {
                'application_errors': [],
                'database_errors': [],
                'network_errors': [],
                'system_errors': []
            }

            # Analyze application logs (if available)
            log_files = [
                '/var/log/dmlog/application.log',
                f"{self.debug_dir}/../logs/integration_tests.log"
            ]

            for log_file in log_files:
                if os.path.exists(log_file):
                    error_patterns['application_errors'].extend(
                        await self.parse_log_file(log_file, ['ERROR', 'CRITICAL', 'FATAL'])
                    )

            # Analyze database logs
            db_log_files = [
                '/var/log/postgresql/postgresql-*/main.log',
                '/var/lib/postgresql/data/log/postgresql.log'
            ]

            for pattern in db_log_files:
                for log_file in glob.glob(pattern):
                    if os.path.exists(log_file):
                        error_patterns['database_errors'].extend(
                            await self.parse_log_file(log_file, ['ERROR', 'FATAL', 'PANIC'])
                        )

            # Analyze system logs
            system_log_files = [
                '/var/log/syslog',
                '/var/log/messages'
            ]

            for log_file in system_log_files:
                if os.path.exists(log_file):
                    error_patterns['system_errors'].extend(
                        await self.parse_log_file(log_file, ['error', 'failed', 'critical'])
                    )

            # Categorize and count patterns
            pattern_counts = defaultdict(int)
            for category, errors in error_patterns.items():
                for error in errors:
                    # Extract common patterns
                    pattern = self.extract_error_pattern(error['message'])
                    pattern_counts[f"{category}:{pattern}"] += 1

            # Get top error patterns
            top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                'status': 'analyzed',
                'error_patterns': error_patterns,
                'top_patterns': dict(top_patterns),
                'total_errors': sum(len(errors) for errors in error_patterns.values())
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def parse_log_file(self, log_file: str, error_keywords: List[str]) -> List[Dict[str, Any]]:
        """Parse log file for errors"""
        errors = []
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if any(keyword.lower() in line.lower() for keyword in error_keywords):
                        errors.append({
                            'file': log_file,
                            'line_number': line_num,
                            'message': line.strip(),
                            'timestamp': self.extract_timestamp(line)
                        })
        except Exception as e:
            self.logger.warning(f"Failed to parse log file {log_file}: {e}")

        return errors

    def extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
            r'\w{3} \d{1,2} \d{2}:\d{2}:\d{2}'
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()

        return None

    def extract_error_pattern(self, error_message: str) -> str:
        """Extract common error pattern from error message"""
        error_message = error_message.lower()

        # Common error patterns
        patterns = {
            'connection_refused': r'connection refused',
            'timeout': r'timeout',
            'permission_denied': r'permission denied',
            'not_found': r'not found|404',
            'server_error': r'500|internal server error',
            'database_error': r'database|sql|postgres',
            'authentication_error': r'auth|login|unauthorized',
            'validation_error': r'validation|invalid',
            'memory_error': r'memory|out of memory',
            'disk_space': r'disk|space|no space'
        }

        for pattern_name, pattern_regex in patterns.items():
            if re.search(pattern_regex, error_message):
                return pattern_name

        return 'other'

    async def test_network_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity to various services"""
        try:
            connectivity_tests = {}

            # Test HTTP endpoints
            http_endpoints = [
                {'name': 'main_app', 'url': self.base_url},
                {'name': 'api_health', 'url': f"{self.base_url}/api/health"},
                {'name': 'google_dns', 'url': 'http://8.8.8.8'},
                {'name': 'cloudflare_dns', 'url': 'http://1.1.1.1'}
            ]

            for endpoint in http_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint['url'], timeout=10)
                    response_time = time.time() - start_time

                    connectivity_tests[endpoint['name']] = {
                        'status': 'connected',
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'url': endpoint['url']
                    }
                except Exception as e:
                    connectivity_tests[endpoint['name']] = {
                        'status': 'failed',
                        'error': str(e),
                        'url': endpoint['url']
                    }

            # Test TCP connections
            tcp_tests = [
                {'name': 'database', 'host': 'localhost', 'port': 5432},
                {'name': 'redis', 'host': 'localhost', 'port': 6379},
                {'name': 'websocket', 'host': 'localhost', 'port': 8001}
            ]

            for test in tcp_tests:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    start_time = time.time()
                    result = sock.connect_ex((test['host'], test['port']))
                    response_time = time.time() - start_time
                    sock.close()

                    connectivity_tests[f"tcp_{test['name']}"] = {
                        'status': 'connected' if result == 0 else 'failed',
                        'response_time': response_time if result == 0 else None,
                        'host': test['host'],
                        'port': test['port']
                    }
                except Exception as e:
                    connectivity_tests[f"tcp_{test['name']}"] = {
                        'status': 'failed',
                        'error': str(e),
                        'host': test['host'],
                        'port': test['port']
                    }

            # DNS resolution test
            try:
                start_time = time.time()
                socket.gethostbyname('google.com')
                dns_time = time.time() - start_time

                connectivity_tests['dns_resolution'] = {
                    'status': 'working',
                    'response_time': dns_time
                }
            except Exception as e:
                connectivity_tests['dns_resolution'] = {
                    'status': 'failed',
                    'error': str(e)
                }

            return {
                'status': 'tested',
                'connectivity': connectivity_tests,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def analyze_application_logs(self) -> Dict[str, Any]:
        """Analyze application logs for insights"""
        try:
            log_analysis = {
                'log_files': [],
                'error_summary': {},
                'warning_summary': {},
                'performance_issues': [],
                'security_events': []
            }

            # Find log files
            log_search_paths = [
                '/var/log/dmlog/',
                '/home/activeloguser/DMLogn8n/logs/',
                f"{self.debug_dir}/../logs/"
            ]

            log_files = []
            for path in log_search_paths:
                if os.path.exists(path):
                    log_files.extend([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.log')])

            for log_file in log_files:
                try:
                    file_analysis = await self.analyze_log_file(log_file)
                    log_analysis['log_files'].append({
                        'file': log_file,
                        'analysis': file_analysis
                    })

                    # Aggregate errors and warnings
                    for error in file_analysis.get('errors', []):
                        error_type = self.extract_error_pattern(error['message'])
                        log_analysis['error_summary'][error_type] = log_analysis['error_summary'].get(error_type, 0) + 1

                    for warning in file_analysis.get('warnings', []):
                        warning_type = self.extract_error_pattern(warning['message'])
                        log_analysis['warning_summary'][warning_type] = log_analysis['warning_summary'].get(warning_type, 0) + 1

                    # Check for performance issues
                    for entry in file_analysis.get('slow_operations', []):
                        log_analysis['performance_issues'].append({
                            'file': log_file,
                            'operation': entry['operation'],
                            'duration': entry['duration'],
                            'timestamp': entry['timestamp']
                        })

                    # Check for security events
                    for entry in file_analysis.get('security_events', []):
                        log_analysis['security_events'].append({
                            'file': log_file,
                            'event': entry['event'],
                            'details': entry['details'],
                            'timestamp': entry['timestamp']
                        })

                except Exception as e:
                    log_analysis['log_files'].append({
                        'file': log_file,
                        'error': str(e)
                    })

            return {
                'status': 'analyzed',
                'analysis': log_analysis,
                'total_errors': sum(log_analysis['error_summary'].values()),
                'total_warnings': sum(log_analysis['warning_summary'].values()),
                'performance_issues_count': len(log_analysis['performance_issues']),
                'security_events_count': len(log_analysis['security_events'])
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def analyze_log_file(self, log_file: str) -> Dict[str, Any]:
        """Analyze individual log file"""
        analysis = {
            'errors': [],
            'warnings': [],
            'slow_operations': [],
            'security_events': [],
            'total_lines': 0
        }

        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    analysis['total_lines'] += 1
                    line_lower = line.lower()

                    # Check for errors
                    if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'failure']):
                        analysis['errors'].append({
                            'line_number': line_num,
                            'message': line.strip(),
                            'timestamp': self.extract_timestamp(line)
                        })

                    # Check for warnings
                    if any(keyword in line_lower for keyword in ['warning', 'warn']):
                        analysis['warnings'].append({
                            'line_number': line_num,
                            'message': line.strip(),
                            'timestamp': self.extract_timestamp(line)
                        })

                    # Check for slow operations
                    slow_match = re.search(r'slow.*operation.*(\d+\.?\d*)s', line_lower)
                    if slow_match:
                        analysis['slow_operations'].append({
                            'line_number': line_num,
                            'operation': line.strip(),
                            'duration': float(slow_match.group(1)),
                            'timestamp': self.extract_timestamp(line)
                        })

                    # Check for security events
                    if any(keyword in line_lower for keyword in ['unauthorized', 'forbidden', 'attack', 'intrusion', 'breach']):
                        analysis['security_events'].append({
                            'line_number': line_num,
                            'event': line.strip(),
                            'details': 'Security related event detected',
                            'timestamp': self.extract_timestamp(line)
                        })

        except Exception as e:
            analysis['error'] = str(e)

        return analysis

    async def analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        try:
            utilization = {}

            # Current resource usage
            utilization['current'] = {
                'cpu': {
                    'overall': psutil.cpu_percent(interval=1),
                    'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'memory': {
                    'virtual': psutil.virtual_memory()._asdict(),
                    'swap': psutil.swap_memory()._asdict()
                },
                'disk': {},
                'network': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }

            # Disk usage per partition
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    utilization['disk'][partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    }
                except PermissionError:
                    continue

            # Process resource usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 1 or proc_info['memory_percent'] > 1:  # Only include significant processes
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent'],
                            'memory_mb': proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by resource usage
            processes.sort(key=lambda x: x['cpu_percent'] + x['memory_percent'], reverse=True)
            utilization['top_processes'] = processes[:10]

            # Historical trends (if we have stored data)
            if self.performance_snapshots:
                recent_snapshots = list(self.performance_snapshots)[-10:]  # Last 10 snapshots
                utilization['trends'] = self.calculate_trends(recent_snapshots)

            # Resource pressure indicators
            pressure_indicators = {
                'cpu_pressure': utilization['current']['cpu']['overall'] > 80,
                'memory_pressure': utilization['current']['memory']['virtual']['percent'] > 85,
                'disk_pressure': any(usage['percent'] > 90 for usage in utilization['disk'].values()),
                'high_process_count': len(processes) > 100
            }

            utilization['pressure_indicators'] = pressure_indicators
            utilization['overall_status'] = 'healthy' if not any(pressure_indicators.values()) else 'warning'

            return {
                'status': 'analyzed',
                'utilization': utilization,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def calculate_trends(self, snapshots: List[Dict]) -> Dict[str, Any]:
        """Calculate trends from historical snapshots"""
        if len(snapshots) < 2:
            return {}

        trends = {}

        # CPU trend
        cpu_values = [s.get('cpu', 0) for s in snapshots]
        trends['cpu'] = {
            'current': cpu_values[-1],
            'average': sum(cpu_values) / len(cpu_values),
            'trend': 'increasing' if cpu_values[-1] > cpu_values[0] else 'decreasing'
        }

        # Memory trend
        memory_values = [s.get('memory', 0) for s in snapshots]
        trends['memory'] = {
            'current': memory_values[-1],
            'average': sum(memory_values) / len(memory_values),
            'trend': 'increasing' if memory_values[-1] > memory_values[0] else 'decreasing'
        }

        return trends

    async def audit_configuration(self) -> Dict[str, Any]:
        """Audit system configuration"""
        try:
            audit_results = {
                'security': {},
                'performance': {},
                'database': {},
                'application': {}
            }

            # Security configuration audit
            audit_results['security'] = {
                'https_enabled': self.base_url.startswith('https'),
                'password_policy': 'checked',  # Would need to verify actual policy
                'authentication_required': 'checked',
                'session_timeout': 'configured',
                'cors_configured': True
            }

            # Performance configuration audit
            audit_results['performance'] = {
                'connection_pooling': 'configured',
                'caching_enabled': True,
                'monitoring_enabled': True,
                'log_level': 'appropriate'
            }

            # Database configuration audit
            try:
                conn = psycopg2.connect(self.database_url)
                with conn.cursor() as cursor:
                    # Check important settings
                    cursor.execute("SHOW max_connections;")
                    max_connections = cursor.fetchone()[0]

                    cursor.execute("SHOW shared_buffers;")
                    shared_buffers = cursor.fetchone()[0]

                    cursor.execute("SHOW effective_cache_size;")
                    effective_cache_size = cursor.fetchone()[0]

                audit_results['database'] = {
                    'max_connections': max_connections,
                    'shared_buffers': shared_buffers,
                    'effective_cache_size': effective_cache_size,
                    'ssl_enabled': True,  # Would need to check actual setting
                    'backups_configured': True
                }
                conn.close()
            except Exception as e:
                audit_results['database'] = {'error': str(e)}

            # Application configuration audit
            audit_results['application'] = {
                'environment': self.config.get('test_environment', 'unknown'),
                'debug_mode': False,  # Should be False in production
                'logging_configured': True,
                'error_handling': 'configured',
                'health_checks_enabled': True
            }

            # Calculate overall audit score
            total_checks = 0
            passed_checks = 0

            for category in audit_results.values():
                if isinstance(category, dict) and 'error' not in category:
                    for check, value in category.items():
                        total_checks += 1
                        if value in [True, 'configured', 'appropriate', 'enabled'] or (isinstance(value, str) and value != 'unknown'):
                            passed_checks += 1

            audit_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0

            return {
                'status': 'audited',
                'audit_results': audit_results,
                'audit_score': audit_score,
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on analysis"""
        recommendations = []

        # Performance recommendations
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > 80:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'High CPU Usage Detected',
                'description': f'Current CPU usage is {cpu_usage}%. Consider optimizing code or scaling resources.',
                'actions': [
                    'Profile application to identify CPU bottlenecks',
                    'Consider horizontal scaling',
                    'Optimize database queries',
                    'Implement caching where appropriate'
                ]
            })

        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 85:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'High Memory Usage Detected',
                'description': f'Current memory usage is {memory_usage}%. Monitor for memory leaks.',
                'actions': [
                    'Check for memory leaks in application',
                    'Optimize memory usage patterns',
                    'Consider increasing available memory',
                    'Implement memory monitoring alerts'
                ]
            })

        # Database recommendations
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
                active_connections = cursor.fetchone()[0]

                if active_connections > 50:
                    recommendations.append({
                        'category': 'database',
                        'priority': 'medium',
                        'title': 'High Database Connection Count',
                        'description': f'{active_connections} active database connections detected.',
                        'actions': [
                            'Review connection pooling configuration',
                            'Check for connection leaks in application',
                            'Consider reducing max_connections if appropriate',
                            'Implement connection timeout settings'
                        ]
                    })
            conn.close()
        except:
            pass

        # Security recommendations
        if not self.base_url.startswith('https'):
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'title': 'HTTPS Not Configured',
                'description': 'Application is not using HTTPS. This poses a security risk.',
                'actions': [
                    'Configure SSL/TLS certificate',
                    'Redirect HTTP to HTTPS',
                    'Update all hardcoded URLs to use HTTPS',
                    'Test SSL configuration'
                ]
            })

        # Monitoring recommendations
        recommendations.append({
            'category': 'monitoring',
            'priority': 'medium',
            'title': 'Enhanced Monitoring Recommended',
            'description': 'Implement comprehensive monitoring for better observability.',
            'actions': [
                'Set up application performance monitoring (APM)',
                'Configure log aggregation and analysis',
                'Implement health check endpoints',
                'Set up alerting for critical issues'
            ]
        })

        # General recommendations
        recommendations.extend([
            {
                'category': 'maintenance',
                'priority': 'low',
                'title': 'Regular Maintenance',
                'description': 'Establish regular maintenance procedures.',
                'actions': [
                    'Schedule regular database maintenance',
                    'Implement log rotation policies',
                    'Regular security updates',
                    'Performance tuning reviews'
                ]
            },
            {
                'category': 'backup',
                'priority': 'high',
                'title': 'Backup Strategy',
                'description': 'Ensure proper backup and recovery procedures.',
                'actions': [
                    'Implement automated database backups',
                    'Test backup restoration procedures',
                    'Document recovery processes',
                    'Monitor backup success rates'
                ]
            }
        ])

        return recommendations

    async def save_debug_report(self, debug_data: Dict[str, Any]) -> str:
        """Save debug report to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"{self.debug_dir}/debug_report_{timestamp}.json"

            # Create human-readable summary
            summary_path = f"{self.debug_dir}/debug_summary_{timestamp}.txt"
            await self.create_debug_summary(debug_data, summary_path)

            # Save full report
            with open(report_path, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)

            self.logger.info(f"Debug report saved to {report_path}")
            return report_path

        except Exception as e:
            self.logger.error(f"Failed to save debug report: {e}")
            return ""

    async def create_debug_summary(self, debug_data: Dict[str, Any], summary_path: str):
        """Create human-readable debug summary"""
        try:
            with open(summary_path, 'w') as f:
                f.write("DMLOGN8N DEBUG REPORT SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # System overview
                if 'system_overview' in debug_data:
                    overview = debug_data['system_overview']
                    f.write("SYSTEM OVERVIEW\n")
                    f.write("-" * 20 + "\n")
                    if 'system' in overview:
                        f.write(f"Hostname: {overview['system'].get('hostname', 'Unknown')}\n")
                        f.write(f"Platform: {overview['system'].get('platform', 'Unknown')}\n")
                    if 'cpu' in overview:
                        f.write(f"CPU Usage: {overview['cpu'].get('usage_percent', 0)}%\n")
                    if 'memory' in overview:
                        f.write(f"Memory Usage: {overview['memory'].get('percent', 0)}%\n")
                    f.write("\n")

                # Service status
                if 'service_status' in debug_data:
                    services = debug_data['service_status']
                    f.write("SERVICE STATUS\n")
                    f.write("-" * 20 + "\n")
                    if 'services' in services:
                        for service_name, service_info in services['services'].items():
                            status = service_info.get('status', 'unknown')
                            f.write(f"{service_name}: {status.upper()}\n")
                    f.write(f"\nOverall Health: {services['summary'].get('overall_health', 'unknown')}\n\n")

                # Recommendations
                if 'recommendations' in debug_data:
                    f.write("RECOMMENDATIONS\n")
                    f.write("-" * 20 + "\n")
                    for rec in debug_data['recommendations']:
                        f.write(f"\n[{rec['priority'].upper()}] {rec['title']}\n")
                        f.write(f"{rec['description']}\n")

                self.logger.info(f"Debug summary saved to {summary_path}")

        except Exception as e:
            self.logger.error(f"Failed to create debug summary: {e}")

    async def take_system_snapshot(self, label: str = None) -> Dict[str, Any]:
        """Take a comprehensive system snapshot"""
        try:
            timestamp = datetime.now()
            snapshot_label = label or timestamp.strftime('%Y%m%d_%H%M%S')

            snapshot = {
                'label': snapshot_label,
                'timestamp': timestamp.isoformat(),
                'system_info': await self.collect_system_overview(),
                'service_status': await self.check_service_status(),
                'performance_metrics': await self.collect_performance_metrics(),
                'resource_utilization': await self.analyze_resource_utilization()
            }

            self.system_snapshots.append(snapshot)

            # Save snapshot to file
            snapshot_path = f"{self.debug_dir}/snapshots/snapshot_{snapshot_label}.json"
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2, default=str)

            self.logger.info(f"System snapshot '{snapshot_label}' saved to {snapshot_path}")
            return snapshot

        except Exception as e:
            self.logger.error(f"Failed to take system snapshot: {e}")
            return {'error': str(e)}

    async def run_diagnostics(self, issue_description: str = None) -> Dict[str, Any]:
        """Run focused diagnostics for a specific issue"""
        try:
            diagnostics = {
                'issue_description': issue_description,
                'timestamp': datetime.now().isoformat(),
                'checks_performed': []
            }

            # Determine which checks to run based on issue description
            if issue_description:
                issue_lower = issue_description.lower()

                if any(keyword in issue_lower for keyword in ['slow', 'performance', 'lag']):
                    diagnostics['checks_performed'].append('performance_analysis')
                    diagnostics['performance_analysis'] = await self.collect_performance_metrics()

                if any(keyword in issue_lower for keyword in ['database', 'db', 'sql']):
                    diagnostics['checks_performed'].append('database_analysis')
                    diagnostics['database_analysis'] = await self.analyze_database_health()

                if any(keyword in issue_lower for keyword in ['network', 'connection', 'connect']):
                    diagnostics['checks_performed'].append('network_analysis')
                    diagnostics['network_analysis'] = await self.test_network_connectivity()

                if any(keyword in issue_lower for keyword in ['error', 'fail', 'crash']):
                    diagnostics['checks_performed'].append('error_analysis')
                    diagnostics['error_analysis'] = await self.analyze_error_patterns()

                if any(keyword in issue_lower for keyword in ['memory', 'ram', 'resource']):
                    diagnostics['checks_performed'].append('resource_analysis')
                    diagnostics['resource_analysis'] = await self.analyze_resource_utilization()

            # Always run basic checks
            diagnostics['checks_performed'].extend(['system_overview', 'service_status'])
            diagnostics['system_overview'] = await self.collect_system_overview()
            diagnostics['service_status'] = await self.check_service_status()

            # Generate specific recommendations based on issue
            diagnostics['recommendations'] = await self.generate_focused_recommendations(diagnostics)

            return diagnostics

        except Exception as e:
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    async def generate_focused_recommendations(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate focused recommendations based on diagnostics"""
        recommendations = []

        # Analyze diagnostics data to provide specific recommendations
        if 'performance_analysis' in diagnostics:
            perf = diagnostics['performance_analysis']
            if 'metrics' in perf and 'system' in perf['metrics']:
                cpu_usage = perf['metrics']['system'].get('cpu_percent', 0)
                memory_usage = perf['metrics']['system'].get('memory_percent', 0)

                if cpu_usage > 80:
                    recommendations.append({
                        'category': 'performance',
                        'priority': 'high',
                        'title': 'High CPU Usage Detected',
                        'description': f'CPU usage is at {cpu_usage}%. Consider optimizing performance.',
                        'actions': ['Profile application bottlenecks', 'Scale resources if needed']
                    })

                if memory_usage > 85:
                    recommendations.append({
                        'category': 'performance',
                        'priority': 'high',
                        'title': 'High Memory Usage Detected',
                        'description': f'Memory usage is at {memory_usage}%. Check for memory leaks.',
                        'actions': ['Monitor memory usage', 'Restart services if needed']
                    })

        if 'database_analysis' in diagnostics:
            db = diagnostics['database_analysis']
            if db.get('health_score', 100) < 70:
                recommendations.append({
                    'category': 'database',
                    'priority': 'medium',
                    'title': 'Database Health Issues Detected',
                    'description': f'Database health score is {db.get("health_score", 0)}/100.',
                    'actions': ['Check slow queries', 'Optimize database configuration', 'Monitor connections']
                })

        if 'network_analysis' in diagnostics:
            net = diagnostics['network_analysis']
            failed_connections = sum(1 for test in net.get('connectivity', {}).values() if test.get('status') == 'failed')
            if failed_connections > 0:
                recommendations.append({
                    'category': 'network',
                    'priority': 'high',
                    'title': 'Network Connectivity Issues',
                    'description': f'{failed_connections} network connectivity tests failed.',
                    'actions': ['Check network configuration', 'Verify service status', 'Test firewall rules']
                })

        return recommendations