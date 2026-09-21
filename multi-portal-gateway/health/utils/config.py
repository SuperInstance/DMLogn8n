"""
Health System Configuration

Configuration management for the health monitoring system.
"""

import json
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class HealthConfig:
    """Health system configuration"""

    # Main configuration
    max_workers: int = 10
    config_path: Optional[str] = None

    # Check configurations
    checks: Dict[str, Any] = field(default_factory=dict)

    # Healing configurations
    healing: Dict[str, Any] = field(default_factory=dict)

    # Scoring configuration
    scoring: Dict[str, Any] = field(default_factory=dict)

    # Storage configuration
    storage: Dict[str, Any] = field(default_factory=dict)

    # Alerting configuration
    alerting: Dict[str, Any] = field(default_factory=dict)

    # SLA configuration
    sla: Dict[str, Any] = field(default_factory=dict)

    # Performance thresholds
    performance: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.load_configuration()

    def load_configuration(self):
        """Load configuration from file or use defaults"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)

                self._apply_configuration(config_data)

            except Exception as e:
                print(f"Failed to load configuration from {self.config_path}: {e}")
                self._load_default_configuration()
        else:
            self._load_default_configuration()

    def _apply_configuration(self, config_data: Dict[str, Any]):
        """Apply configuration data"""
        self.max_workers = config_data.get('max_workers', 10)
        self.checks = config_data.get('checks', {})
        self.healing = config_data.get('healing', {})
        self.scoring = config_data.get('scoring', {})
        self.storage = config_data.get('storage', {})
        self.alerting = config_data.get('alerting', {})
        self.sla = config_data.get('sla', {})
        self.performance = config_data.get('performance', {})

    def _load_default_configuration(self):
        """Load default configuration"""
        self.checks = {
            'component': {
                'database': {
                    'connection_string': os.getenv('DATABASE_URL', 'postgresql://localhost:5432/dmlogn8n')
                },
                'cache': {
                    'host': os.getenv('CACHE_HOST', 'localhost'),
                    'port': int(os.getenv('CACHE_PORT', '6379')),
                    'password': os.getenv('CACHE_PASSWORD')
                },
                'message_queue': {
                    'host': os.getenv('MQ_HOST', 'localhost'),
                    'port': int(os.getenv('MQ_PORT', '15672')),
                    'username': os.getenv('MQ_USERNAME', 'guest'),
                    'password': os.getenv('MQ_PASSWORD', 'guest')
                },
                'filesystem': {
                    'mount_points': ['/']
                },
                'ssl_certificates': {
                    'certificates': []
                },
                'network': {
                    'endpoints': [
                        {'name': 'google-dns', 'host': '8.8.8.8', 'port': 53},
                        {'name': 'cloudflare-dns', 'host': '1.1.1.1', 'port': 53}
                    ]
                },
                'http_components': {}
            },
            'service': {
                'api_gateway': {
                    'base_url': os.getenv('API_GATEWAY_URL', 'http://localhost:8080'),
                    'health_endpoint': '/health',
                    'timeout': 10
                },
                'character_portal': {
                    'base_url': os.getenv('CHARACTER_PORTAL_URL', 'http://localhost:8081'),
                    'health_endpoint': '/health',
                    'timeout': 10
                },
                'dialogue_service': {
                    'base_url': os.getenv('DIALOGUE_SERVICE_URL', 'http://localhost:8082'),
                    'health_endpoint': '/health',
                    'timeout': 10
                },
                'n8n_workflow': {
                    'base_url': os.getenv('N8N_URL', 'http://localhost:5678'),
                    'health_endpoint': '/healthz',
                    'timeout': 10,
                    'api_key': os.getenv('N8N_API_KEY')
                }
            },
            'system': {
                'cpu_thresholds': {
                    'warning': 75,
                    'critical': 90
                },
                'memory_thresholds': {
                    'warning': 80,
                    'critical': 95
                },
                'disk_thresholds': {
                    'warning': 80,
                    'critical': 95
                }
            },
            'business': {
                'user_activity': {
                    'api_endpoint': os.getenv('USER_ACTIVITY_API'),
                    'timeout': 10
                },
                'game_sessions': {
                    'api_endpoint': os.getenv('GAME_SESSIONS_API'),
                    'timeout': 10
                },
                'error_rates': {
                    'api_endpoint': os.getenv('ERROR_RATES_API'),
                    'timeout': 10
                },
                'response_times': {
                    'api_endpoint': os.getenv('RESPONSE_TIMES_API'),
                    'timeout': 10
                }
            }
        }

        self.healing = {
            'service': {
                'cooldown_minutes': 5,
                'max_retries': 3,
                'services': {}
            },
            'resource': {
                'cleanup_thresholds': {
                    'disk_usage': 90,
                    'memory_usage': 95
                }
            },
            'data': {
                'backup_enabled': True,
                'corruption_detection': True
            }
        }

        self.scoring = {
            'weights': {
                'component': 0.3,
                'service': 0.3,
                'system': 0.2,
                'business': 0.2
            },
            'thresholds': {
                'healthy': 90,
                'warning': 70,
                'degraded': 50
            }
        }

        self.storage = {
            'type': 'file',
            'file': {
                'path': '/tmp/health_data',
                'retention_days': 30
            },
            'database': {
                'connection_string': os.getenv('HEALTH_DB_URL')
            }
        }

        self.alerting = {
            'enabled': True,
            'channels': {
                'email': {
                    'enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
                    'smtp_server': os.getenv('SMTP_SERVER'),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'username': os.getenv('SMTP_USERNAME'),
                    'password': os.getenv('SMTP_PASSWORD'),
                    'recipients': os.getenv('ALERT_RECIPIENTS', '').split(',')
                },
                'slack': {
                    'enabled': os.getenv('SLACK_ENABLED', 'false').lower() == 'true',
                    'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                    'channel': os.getenv('SLACK_CHANNEL', '#alerts')
                },
                'webhook': {
                    'enabled': os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true',
                    'url': os.getenv('WEBHOOK_URL')
                }
            }
        }

        self.sla = {
            'min_uptime_percentage': 99.9,
            'max_response_time_ms': 1000,
            'max_error_rate_percentage': 1.0
        }

        self.performance = {
            'thresholds': {
                'slow_response_ms': 1000,
                'very_slow_response_ms': 5000
            }
        }