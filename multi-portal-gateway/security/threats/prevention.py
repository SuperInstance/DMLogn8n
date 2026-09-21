#!/usr/bin/env python3
"""
DMLogn8n Threat Prevention System
Automated threat prevention and response actions
"""

import json
import logging
import asyncio
import time
import ipaddress
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis
import yaml
import aiohttp
from fastapi import Request, Response
import uuid

from .detector import ThreatAlert, ThreatType, ThreatSeverity

logger = logging.getLogger(__name__)

class PreventionAction(Enum):
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    REQUIRE_AUTH = "require_auth"
    CHALLENGE = "challenge"
    LOG_AND_MONITOR = "log_and_monitor"
    QUARANTINE = "quarantine"
    NOTIFY_ADMIN = "notify_admin"
    BLOCK_USER = "block_user"
    RESET_SESSION = "reset_session"
    ISOLATE_SYSTEM = "isolate_system"

class PreventionLevel(Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    AGGRESSIVE = "aggressive"

@dataclass
class PreventionRule:
    rule_id: str
    name: str
    threat_types: List[ThreatType]
    min_severity: ThreatSeverity
    actions: List[PreventionAction]
    conditions: Dict[str, Any]
    prevention_level: PreventionLevel
    duration_minutes: int
    auto_recovery: bool = True
    notification_required: bool = True

@dataclass
class PreventionAction:
    action_id: str
    action_type: PreventionAction
    target: str  # IP, user, system, etc.
    parameters: Dict[str, Any]
    executed_at: datetime
    expires_at: Optional[datetime]
    status: str = "active"
    result: Optional[str] = None

class ThreatPrevention:
    """
    Automated threat prevention and response system
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.active_rules = {}
        self.active_actions = {}
        self.blocked_ips = set()
        self.blocked_users = set()
        self.quarantined_systems = set()
        self.action_history = defaultdict(list)

        # Prevention settings
        self.prevention_level = PreventionLevel(self.config.get('prevention_level', 'active'))
        self.auto_block_threshold = self.config.get('auto_block_threshold', 3)
        self.block_duration_hours = self.config.get('block_duration_hours', 24)
        self.enable_auto_recovery = self.config.get('enable_auto_recovery', True)

        # Initialize default prevention rules
        self._initialize_default_rules()

    async def initialize(self):
        """Initialize threat prevention components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=7,  # Threat prevention specific DB
                decode_responses=True
            )

            # Load existing rules
            await self._load_prevention_rules()

            # Load active actions
            await self._load_active_actions()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("Threat Prevention System initialized")

        except Exception as e:
            logger.error(f"Threat Prevention System initialization failed: {e}")
            raise

    async def apply_measures(self, threat_alert: ThreatAlert) -> List[PreventionAction]:
        """
        Apply prevention measures based on threat alert
        """
        actions = []

        try:
            # Get applicable prevention rules
            applicable_rules = self._get_applicable_rules(threat_alert)

            for rule in applicable_rules:
                # Check if rule conditions are met
                if await self._evaluate_rule_conditions(rule, threat_alert):
                    # Apply prevention actions
                    rule_actions = await self._apply_prevention_rule(rule, threat_alert)
                    actions.extend(rule_actions)

            # Store actions
            for action in actions:
                await self._store_prevention_action(action)

            # Log prevention actions
            if actions:
                await self._log_prevention_actions(threat_alert, actions)

            return actions

        except Exception as e:
            logger.error(f"Prevention measures application error: {e}")
            return []

    async def block_ip_address(self, ip_address: str, reason: str,
                              duration_hours: int = None, source: str = "manual") -> bool:
        """
        Block IP address
        """
        try:
            if duration_hours is None:
                duration_hours = self.block_duration_hours

            # Validate IP address
            try:
                ip_obj = ipaddress.ip_address(ip_address)
            except ValueError:
                logger.error(f"Invalid IP address: {ip_address}")
                return False

            # Add to blocked IPs
            self.blocked_ips.add(ip_address)

            # Store in Redis with expiry
            if self.redis_client:
                block_data = {
                    'ip_address': ip_address,
                    'reason': reason,
                    'blocked_at': datetime.now().isoformat(),
                    'duration_hours': duration_hours,
                    'source': source
                }

                await self.redis_client.setex(
                    f"blocked_ip:{ip_address}",
                    duration_hours * 3600,
                    json.dumps(block_data)
                )

                # Add to global blocked IPs set
                await self.redis_client.sadd("global_blocked_ips", ip_address)

            # Create prevention action record
            action = PreventionAction(
                action_id=str(uuid.uuid4()),
                action_type=PreventionAction.BLOCK_IP,
                target=ip_address,
                parameters={
                    'reason': reason,
                    'duration_hours': duration_hours,
                    'source': source
                },
                executed_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=duration_hours)
            )

            await self._store_prevention_action(action)

            logger.warning(f"IP address blocked: {ip_address} - {reason}")
            return True

        except Exception as e:
            logger.error(f"IP blocking error: {e}")
            return False

    async def unblock_ip_address(self, ip_address: str) -> bool:
        """
        Unblock IP address
        """
        try:
            # Remove from blocked IPs
            self.blocked_ips.discard(ip_address)

            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(f"blocked_ip:{ip_address}")
                await self.redis_client.srem("global_blocked_ips", ip_address)

            # Expire related prevention actions
            for action_id, action in list(self.active_actions.items()):
                if (action.action_type == PreventionAction.BLOCK_IP and
                    action.target == ip_address):
                    action.status = "expired"
                    action.result = "manually_unblocked"
                    await self._update_prevention_action(action)

            logger.info(f"IP address unblocked: {ip_address}")
            return True

        except Exception as e:
            logger.error(f"IP unblocking error: {e}")
            return False

    async def block_user(self, user_id: str, reason: str,
                        duration_hours: int = None, source: str = "manual") -> bool:
        """
        Block user account
        """
        try:
            if duration_hours is None:
                duration_hours = self.block_duration_hours

            # Add to blocked users
            self.blocked_users.add(user_id)

            # Store in Redis
            if self.redis_client:
                block_data = {
                    'user_id': user_id,
                    'reason': reason,
                    'blocked_at': datetime.now().isoformat(),
                    'duration_hours': duration_hours,
                    'source': source
                }

                await self.redis_client.setex(
                    f"blocked_user:{user_id}",
                    duration_hours * 3600,
                    json.dumps(block_data)
                )

            # Create prevention action record
            action = PreventionAction(
                action_id=str(uuid.uuid4()),
                action_type=PreventionAction.BLOCK_USER,
                target=user_id,
                parameters={
                    'reason': reason,
                    'duration_hours': duration_hours,
                    'source': source
                },
                executed_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=duration_hours)
            )

            await self._store_prevention_action(action)

            logger.warning(f"User blocked: {user_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"User blocking error: {e}")
            return False

    async def apply_rate_limit(self, target: str, limit: int, window_seconds: int,
                             reason: str, duration_minutes: int = 60) -> bool:
        """
        Apply rate limiting to target
        """
        try:
            # Store rate limit rule
            rate_limit_data = {
                'target': target,
                'limit': limit,
                'window_seconds': window_seconds,
                'reason': reason,
                'applied_at': datetime.now().isoformat(),
                'duration_minutes': duration_minutes
            }

            if self.redis_client:
                await self.redis_client.setex(
                    f"rate_limit:{target}",
                    duration_minutes * 60,
                    json.dumps(rate_limit_data)
                )

            # Create prevention action record
            action = PreventionAction(
                action_id=str(uuid.uuid4()),
                action_type=PreventionAction.RATE_LIMIT,
                target=target,
                parameters={
                    'limit': limit,
                    'window_seconds': window_seconds,
                    'reason': reason
                },
                executed_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=duration_minutes)
            )

            await self._store_prevention_action(action)

            logger.info(f"Rate limit applied to {target}: {limit}/{window_seconds}s - {reason}")
            return True

        except Exception as e:
            logger.error(f"Rate limiting application error: {e}")
            return False

    async def quarantine_system(self, system_id: str, reason: str,
                              duration_hours: int = None) -> bool:
        """
        Quarantine system from network
        """
        try:
            if duration_hours is None:
                duration_hours = self.block_duration_hours

            # Add to quarantined systems
            self.quarantined_systems.add(system_id)

            # Store in Redis
            if self.redis_client:
                quarantine_data = {
                    'system_id': system_id,
                    'reason': reason,
                    'quarantined_at': datetime.now().isoformat(),
                    'duration_hours': duration_hours
                }

                await self.redis_client.setex(
                    f"quarantined_system:{system_id}",
                    duration_hours * 3600,
                    json.dumps(quarantine_data)
                )

            # Create prevention action record
            action = PreventionAction(
                action_id=str(uuid.uuid4()),
                action_type=PreventionAction.QUARANTINE,
                target=system_id,
                parameters={
                    'reason': reason,
                    'duration_hours': duration_hours
                },
                executed_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=duration_hours)
            )

            await self._store_prevention_action(action)

            logger.warning(f"System quarantined: {system_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"System quarantine error: {e}")
            return False

    async def reset_user_sessions(self, user_id: str, reason: str) -> bool:
        """
        Reset all active sessions for user
        """
        try:
            # Remove user sessions from Redis
            if self.redis_client:
                session_keys = await self.redis_client.keys(f"session:*")
                for session_key in session_keys:
                    session_data = await self.redis_client.get(session_key)
                    if session_data:
                        session = json.loads(session_data)
                        if session.get('user_id') == user_id:
                            await self.redis_client.delete(session_key)

            # Create prevention action record
            action = PreventionAction(
                action_id=str(uuid.uuid4()),
                action_type=PreventionAction.RESET_SESSION,
                target=user_id,
                parameters={'reason': reason},
                executed_at=datetime.now(),
                expires_at=None
            )

            await self._store_prevention_action(action)

            logger.info(f"Sessions reset for user: {user_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Session reset error: {e}")
            return False

    async def notify_administrators(self, alert: ThreatAlert, message: str) -> bool:
        """
        Send notification to administrators
        """
        try:
            notification_data = {
                'alert_id': alert.alert_id,
                'threat_type': alert.threat_type.value,
                'severity': alert.severity.name,
                'source_ip': alert.source_ip,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }

            # Store notification
            if self.redis_client:
                await self.redis_client.lpush(
                    "admin_notifications",
                    json.dumps(notification_data)
                )
                await self.redis_client.ltrim("admin_notifications", 0, 1000)

            # Send email/SMS (placeholder - implement actual notification)
            await self._send_admin_notification(notification_data)

            logger.warning(f"Admin notification sent for threat: {alert.threat_type.value}")
            return True

        except Exception as e:
            logger.error(f"Admin notification error: {e}")
            return False

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips

    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users

    def is_system_quarantined(self, system_id: str) -> bool:
        """Check if system is quarantined"""
        return system_id in self.quarantined_systems

    async def get_prevention_status(self) -> Dict[str, Any]:
        """Get current prevention status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'prevention_level': self.prevention_level.value,
                'blocked_ips_count': len(self.blocked_ips),
                'blocked_users_count': len(self.blocked_users),
                'quarantined_systems_count': len(self.quarantined_systems),
                'active_rules_count': len(self.active_rules),
                'active_actions_count': len(self.active_actions),
                'recent_actions': []
            }

            # Get recent actions
            recent_actions = sorted(
                self.active_actions.values(),
                key=lambda x: x.executed_at,
                reverse=True
            )[:10]

            for action in recent_actions:
                status['recent_actions'].append({
                    'action_id': action.action_id,
                    'action_type': action.action_type.value,
                    'target': action.target,
                    'executed_at': action.executed_at.isoformat(),
                    'status': action.status,
                    'expires_at': action.expires_at.isoformat() if action.expires_at else None
                })

            return status

        except Exception as e:
            logger.error(f"Prevention status retrieval error: {e}")
            return {'error': str(e)}

    # Private methods
    def _get_applicable_rules(self, threat_alert: ThreatAlert) -> List[PreventionRule]:
        """Get prevention rules applicable to threat alert"""
        applicable_rules = []

        for rule in self.active_rules.values():
            # Check threat type match
            if threat_alert.threat_type not in rule.threat_types:
                continue

            # Check severity threshold
            if threat_alert.severity.value < rule.min_severity.value:
                continue

            # Check prevention level
            if not self._is_prevention_level_applicable(rule.prevention_level):
                continue

            applicable_rules.append(rule)

        # Sort by priority (severity)
        applicable_rules.sort(key=lambda r: r.min_severity.value, reverse=True)

        return applicable_rules

    async def _evaluate_rule_conditions(self, rule: PreventionRule, threat_alert: ThreatAlert) -> bool:
        """Evaluate if rule conditions are met"""
        try:
            conditions = rule.conditions

            # Check confidence threshold
            if 'min_confidence' in conditions:
                if threat_alert.confidence < conditions['min_confidence']:
                    return False

            # Check source IP reputation
            if 'block_suspicious_ips' in conditions and conditions['block_suspicious_ips']:
                if await self._is_suspicious_ip(threat_alert.source_ip):
                    return True

            # Check repeat offenses
            if 'max_offenses' in conditions:
                offense_count = await self._get_offense_count(threat_alert.source_ip, threat_alert.threat_type)
                if offense_count >= conditions['max_offenses']:
                    return True

            # Check time-based conditions
            if 'business_hours_only' in conditions and conditions['business_hours_only']:
                current_hour = datetime.now().hour
                if current_hour < 9 or current_hour > 17:
                    return False

            return True

        except Exception as e:
            logger.error(f"Rule condition evaluation error: {e}")
            return False

    async def _apply_prevention_rule(self, rule: PreventionRule, threat_alert: ThreatAlert) -> List[PreventionAction]:
        """Apply prevention actions from rule"""
        actions = []

        try:
            for action_type in rule.actions:
                action = await self._execute_prevention_action(
                    action_type, threat_alert, rule
                )
                if action:
                    actions.append(action)

        except Exception as e:
            logger.error(f"Prevention rule application error: {e}")

        return actions

    async def _execute_prevention_action(self, action_type: PreventionAction,
                                       threat_alert: ThreatAlert,
                                       rule: PreventionRule) -> Optional[PreventionAction]:
        """Execute specific prevention action"""
        try:
            action = None

            if action_type == PreventionAction.BLOCK_IP:
                success = await self.block_ip_address(
                    threat_alert.source_ip,
                    f"Auto-block for {threat_alert.threat_type.value}",
                    rule.duration_minutes // 60,
                    f"rule:{rule.rule_id}"
                )
                if success:
                    action = PreventionAction(
                        action_id=str(uuid.uuid4()),
                        action_type=action_type,
                        target=threat_alert.source_ip,
                        parameters={'rule_id': rule.rule_id},
                        executed_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(minutes=rule.duration_minutes)
                    )

            elif action_type == PreventionAction.RATE_LIMIT:
                success = await self.apply_rate_limit(
                    threat_alert.source_ip,
                    10,  # 10 requests per minute
                    60,
                    f"Rate limit for {threat_alert.threat_type.value}",
                    rule.duration_minutes
                )
                if success:
                    action = PreventionAction(
                        action_id=str(uuid.uuid4()),
                        action_type=action_type,
                        target=threat_alert.source_ip,
                        parameters={
                            'rule_id': rule.rule_id,
                            'limit': 10,
                            'window': 60
                        },
                        executed_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(minutes=rule.duration_minutes)
                    )

            elif action_type == PreventionAction.REQUIRE_AUTH:
                # Store requirement for additional authentication
                if self.redis_client:
                    await self.redis_client.setex(
                        f"require_auth:{threat_alert.source_ip}",
                        rule.duration_minutes * 60,
                        json.dumps({
                            'reason': threat_alert.threat_type.value,
                            'rule_id': rule.rule_id
                        })
                    )

                action = PreventionAction(
                    action_id=str(uuid.uuid4()),
                    action_type=action_type,
                    target=threat_alert.source_ip,
                    parameters={'rule_id': rule.rule_id},
                    executed_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(minutes=rule.duration_minutes)
                )

            elif action_type == PreventionAction.CHALLENGE:
                # Store challenge requirement
                if self.redis_client:
                    await self.redis_client.setex(
                        f"challenge:{threat_alert.source_ip}",
                        rule.duration_minutes * 60,
                        json.dumps({
                            'reason': threat_alert.threat_type.value,
                            'rule_id': rule.rule_id
                        })
                    )

                action = PreventionAction(
                    action_id=str(uuid.uuid4()),
                    action_type=action_type,
                    target=threat_alert.source_ip,
                    parameters={'rule_id': rule.rule_id},
                    executed_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(minutes=rule.duration_minutes)
                )

            elif action_type == PreventionAction.LOG_AND_MONITOR:
                action = PreventionAction(
                    action_id=str(uuid.uuid4()),
                    action_type=action_type,
                    target=threat_alert.source_ip,
                    parameters={'rule_id': rule.rule_id},
                    executed_at=datetime.now(),
                    expires_at=None
                )

            elif action_type == PreventionAction.NOTIFY_ADMIN:
                message = f"Threat detected: {threat_alert.threat_type.value} from {threat_alert.source_ip}"
                await self.notify_administrators(threat_alert, message)

                action = PreventionAction(
                    action_id=str(uuid.uuid4()),
                    action_type=action_type,
                    target="administrators",
                    parameters={
                        'rule_id': rule.rule_id,
                        'message': message
                    },
                    executed_at=datetime.now(),
                    expires_at=None
                )

            return action

        except Exception as e:
            logger.error(f"Prevention action execution error: {e}")
            return None

    def _is_prevention_level_applicable(self, rule_level: PreventionLevel) -> bool:
        """Check if prevention rule level is applicable"""
        level_hierarchy = {
            PreventionLevel.PASSIVE: 1,
            PreventionLevel.ACTIVE: 2,
            PreventionLevel.AGGRESSIVE: 3
        }

        current_level = level_hierarchy.get(self.prevention_level, 2)
        rule_level_value = level_hierarchy.get(rule_level, 2)

        return current_level >= rule_level_value

    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        try:
            # Check against threat intelligence (placeholder)
            # Check Tor exit nodes, known malicious IPs, etc.
            return False  # Placeholder implementation

        except Exception as e:
            logger.error(f"Suspicious IP check error: {e}")
            return False

    async def _get_offense_count(self, source_ip: str, threat_type: ThreatType) -> int:
        """Get offense count for IP and threat type"""
        try:
            if not self.redis_client:
                return 0

            # Get recent threats for this IP
            key = f"offenses:{source_ip}:{threat_type.value}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0

        except Exception as e:
            logger.error(f"Offense count retrieval error: {e})
            return 0

    async def _store_prevention_action(self, action: PreventionAction):
        """Store prevention action"""
        try:
            self.active_actions[action.action_id] = action

            # Store in Redis
            if self.redis_client:
                action_data = asdict(action)
                action_data['executed_at'] = action.executed_at.isoformat()
                if action.expires_at:
                    action_data['expires_at'] = action.expires_at.isoformat()

                expiry_seconds = None
                if action.expires_at:
                    expiry_seconds = int((action.expires_at - datetime.now()).total_seconds())

                if expiry_seconds and expiry_seconds > 0:
                    await self.redis_client.setex(
                        f"prevention_action:{action.action_id}",
                        expiry_seconds,
                        json.dumps(action_data)
                    )
                else:
                    await self.redis_client.set(
                        f"prevention_action:{action.action_id}",
                        json.dumps(action_data)
                    )

        except Exception as e:
            logger.error(f"Prevention action storage error: {e}")

    async def _update_prevention_action(self, action: PreventionAction):
        """Update prevention action"""
        try:
            if self.redis_client:
                action_data = asdict(action)
                action_data['executed_at'] = action.executed_at.isoformat()
                if action.expires_at:
                    action_data['expires_at'] = action.expires_at.isoformat()

                await self.redis_client.set(
                    f"prevention_action:{action.action_id}",
                    json.dumps(action_data)
                )

        except Exception as e:
            logger.error(f"Prevention action update error: {e}")

    async def _log_prevention_actions(self, threat_alert: ThreatAlert, actions: List[PreventionAction]):
        """Log prevention actions"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'threat_alert_id': threat_alert.alert_id,
                'threat_type': threat_alert.threat_type.value,
                'source_ip': threat_alert.source_ip,
                'actions_taken': [
                    {
                        'action_id': action.action_id,
                        'action_type': action.action_type.value,
                        'target': action.target,
                        'parameters': action.parameters
                    }
                    for action in actions
                ]
            }

            if self.redis_client:
                await self.redis_client.lpush(
                    "prevention_actions_log",
                    json.dumps(log_entry)
                )
                await self.redis_client.ltrim("prevention_actions_log", 0, 10000)

        except Exception as e:
            logger.error(f"Prevention actions logging error: {e}")

    async def _send_admin_notification(self, notification_data: Dict[str, Any]):
        """Send notification to administrators"""
        try:
            # Placeholder for actual notification implementation
            # Could send email, SMS, Slack message, etc.
            logger.info(f"Admin notification: {notification_data['message']}")

        except Exception as e:
            logger.error(f"Admin notification sending error: {e}")

    def _initialize_default_rules(self):
        """Initialize default prevention rules"""
        rules = [
            PreventionRule(
                rule_id="critical_ip_block",
                name="Block IP for Critical Threats",
                threat_types=[ThreatType.SQL_INJECTION, ThreatType.COMMAND_INJECTION, ThreatType.ZERO_DAY],
                min_severity=ThreatSeverity.CRITICAL,
                actions=[PreventionAction.BLOCK_IP, PreventionAction.NOTIFY_ADMIN],
                conditions={'min_confidence': 0.8},
                prevention_level=PreventionLevel.ACTIVE,
                duration_minutes=1440,  # 24 hours
                auto_recovery=True,
                notification_required=True
            ),
            PreventionRule(
                rule_id="high_severity_rate_limit",
                name="Rate Limit High Severity Threats",
                threat_types=[ThreatType.XSS, ThreatType.PATH_TRAVERSAL, ThreatType.BRUTE_FORCE],
                min_severity=ThreatSeverity.HIGH,
                actions=[PreventionAction.RATE_LIMIT, PreventionAction.NOTIFY_ADMIN],
                conditions={'min_confidence': 0.7},
                prevention_level=PreventionLevel.ACTIVE,
                duration_minutes=360,  # 6 hours
                auto_recovery=True,
                notification_required=True
            ),
            PreventionRule(
                rule_id="medium_severity_monitor",
                name="Monitor Medium Severity Threats",
                threat_types=[ThreatType.SCANNER, ThreatType.ANOMALOUS_BEHAVIOR],
                min_severity=ThreatSeverity.MEDIUM,
                actions=[PreventionAction.LOG_AND_MONITOR],
                conditions={'min_confidence': 0.6},
                prevention_level=PreventionLevel.PASSIVE,
                duration_minutes=180,  # 3 hours
                auto_recovery=True,
                notification_required=False
            ),
            PreventionRule(
                rule_id="repeat_offender_block",
                name="Block Repeat Offenders",
                threat_types=list(ThreatType),
                min_severity=ThreatSeverity.MEDIUM,
                actions=[PreventionAction.BLOCK_IP, PreventionAction.NOTIFY_ADMIN],
                conditions={'max_offenses': 3, 'min_confidence': 0.6},
                prevention_level=PreventionLevel.ACTIVE,
                duration_minutes=4320,  # 72 hours
                auto_recovery=True,
                notification_required=True
            ),
            PreventionRule(
                rule_id="ddos_response",
                name="DDoS Attack Response",
                threat_types=[ThreatType.DDOS],
                min_severity=ThreatSeverity.HIGH,
                actions=[PreventionAction.BLOCK_IP, PreventionAction.RATE_LIMIT],
                conditions={'min_confidence': 0.9},
                prevention_level=PreventionLevel.AGGRESSIVE,
                duration_minutes=180,  # 3 hours
                auto_recovery=True,
                notification_required=True
            )
        ]

        for rule in rules:
            self.active_rules[rule.rule_id] = rule

    async def _load_prevention_rules(self):
        """Load prevention rules from configuration"""
        try:
            rules_config = self.config.get('prevention_rules', {})
            for rule_id, rule_config in rules_config.items():
                rule = PreventionRule(
                    rule_id=rule_id,
                    name=rule_config.get('name', ''),
                    threat_types=[ThreatType(tt) for tt in rule_config.get('threat_types', [])],
                    min_severity=ThreatSeverity(rule_config.get('min_severity', 2)),
                    actions=[PreventionAction(action) for action in rule_config.get('actions', [])],
                    conditions=rule_config.get('conditions', {}),
                    prevention_level=PreventionLevel(rule_config.get('prevention_level', 'active')),
                    duration_minutes=rule_config.get('duration_minutes', 360),
                    auto_recovery=rule_config.get('auto_recovery', True),
                    notification_required=rule_config.get('notification_required', True)
                )
                self.active_rules[rule_id] = rule

            logger.info(f"Loaded {len(self.active_rules)} prevention rules")

        except Exception as e:
            logger.error(f"Prevention rules loading error: {e}")

    async def _load_active_actions(self):
        """Load active prevention actions from Redis"""
        try:
            if not self.redis_client:
                return

            # Load blocked IPs
            blocked_ip_keys = await self.redis_client.keys("blocked_ip:*")
            for key in blocked_ip_keys:
                ip_address = key.split(':')[-1]
                self.blocked_ips.add(ip_address)

            # Load blocked users
            blocked_user_keys = await self.redis_client.keys("blocked_user:*")
            for key in blocked_user_keys:
                user_id = key.split(':')[-1]
                self.blocked_users.add(user_id)

            # Load quarantined systems
            quarantined_keys = await self.redis_client.keys("quarantined_system:*")
            for key in quarantined_keys:
                system_id = key.split(':')[-1]
                self.quarantined_systems.add(system_id)

            # Load prevention actions
            action_keys = await self.redis_client.keys("prevention_action:*")
            for key in action_keys:
                action_data = await self.redis_client.get(key)
                if action_data:
                    action_dict = json.loads(action_data)
                    action = PreventionAction(
                        action_id=action_dict['action_id'],
                        action_type=PreventionAction(action_dict['action_type']),
                        target=action_dict['target'],
                        parameters=action_dict['parameters'],
                        executed_at=datetime.fromisoformat(action_dict['executed_at']),
                        expires_at=datetime.fromisoformat(action_dict['expires_at']) if action_dict.get('expires_at') else None,
                        status=action_dict.get('status', 'active'),
                        result=action_dict.get('result')
                    )
                    self.active_actions[action.action_id] = action

            logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs, {len(self.blocked_users)} blocked users, {len(self.quarantined_systems)} quarantined systems")

        except Exception as e:
            logger.error(f"Active actions loading error: {e}")

    async def _start_background_tasks(self):
        """Start background tasks for prevention system"""
        try:
            # Cleanup expired actions
            asyncio.create_task(self._cleanup_expired_actions())

            # Update offense counts
            asyncio.create_task(self._update_offense_counts())

            # Auto-recovery
            if self.enable_auto_recovery:
                asyncio.create_task(self._auto_recovery())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _cleanup_expired_actions(self):
        """Clean up expired prevention actions"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                current_time = datetime.now()
                expired_actions = []

                for action_id, action in list(self.active_actions.items()):
                    if action.expires_at and current_time >= action.expires_at:
                        expired_actions.append(action_id)

                # Remove expired actions
                for action_id in expired_actions:
                    action = self.active_actions.pop(action_id, None)
                    if action:
                        # Handle action expiry
                        await self._handle_action_expiry(action)

                if expired_actions:
                    logger.info(f"Cleaned up {len(expired_actions)} expired prevention actions")

            except Exception as e:
                logger.error(f"Action cleanup error: {e}")
                await asyncio.sleep(60)

    async def _update_offense_counts(self):
        """Update offense counts for IPs"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                # Decay offense counts
                if self.redis_client:
                    keys = await self.redis_client.keys("offenses:*")
                    for key in keys:
                        count = await self.redis_client.get(key)
                        if count and int(count) > 0:
                            new_count = max(0, int(count) - 1)
                            if new_count == 0:
                                await self.redis_client.delete(key)
                            else:
                                await self.redis_client.set(key, new_count, ex=86400 * 7)  # 7 days expiry

            except Exception as e:
                logger.error(f"Offense count update error: {e}")
                await asyncio.sleep(300)

    async def _auto_recovery(self):
        """Automatic recovery from prevention actions"""
        while True:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes

                # Check for conditions to auto-recover
                await self._check_auto_recovery_conditions()

            except Exception as e:
                logger.error(f"Auto-recovery error: {e}")
                await asyncio.sleep(300)

    async def _handle_action_expiry(self, action: PreventionAction):
        """Handle expired prevention action"""
        try:
            action.status = "expired"

            if action.action_type == PreventionAction.BLOCK_IP:
                self.blocked_ips.discard(action.target)
                if self.redis_client:
                    await self.redis_client.delete(f"blocked_ip:{action.target}")
                    await self.redis_client.srem("global_blocked_ips", action.target)

            elif action.action_type == PreventionAction.BLOCK_USER:
                self.blocked_users.discard(action.target)
                if self.redis_client:
                    await self.redis_client.delete(f"blocked_user:{action.target}")

            elif action.action_type == PreventionAction.QUARANTINE:
                self.quarantined_systems.discard(action.target)
                if self.redis_client:
                    await self.redis_client.delete(f"quarantined_system:{action.target}")

            # Update action in Redis
            await self._update_prevention_action(action)

            logger.info(f"Prevention action expired: {action.action_id} - {action.action_type.value} on {action.target}")

        except Exception as e:
            logger.error(f"Action expiry handling error: {e}")

    async def _check_auto_recovery_conditions(self):
        """Check conditions for automatic recovery"""
        try:
            # Check if threat levels have decreased
            # If no new threats detected for certain period, consider easing restrictions

            if self.redis_client:
                # Get recent threat alerts
                recent_alerts = await self.redis_client.lrange("threat_alerts", 0, 100)
                if len(recent_alerts) < 5:  # Low threat activity
                    # Consider reducing some restrictions
                    logger.info("Low threat activity detected, considering easing restrictions")

        except Exception as e:
            logger.error(f"Auto-recovery condition check error: {e}")