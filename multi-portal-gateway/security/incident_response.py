"""
Incident Response System for DMLogn8n Security
Automated incident handling, escalation, and resolution
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import aiofiles
import redis.asyncio as redis
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IncidentStatus(Enum):
    """Incident status values"""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    UNDER_INVESTIGATION = "under_investigation"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"

class IncidentType(Enum):
    """Incident types"""
    SECURITY_BREACH = "security_breach"
    DDOS_ATTACK = "ddos_attack"
    MALWARE_DETECTION = "malware_detection"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_COMPROMISE = "system_compromise"
    VULNERABILITY_EXPLOITATION = "vulnerability_exploitation"
    PHISHING_ATTACK = "phishing_attack"
    INSIDER_THREAT = "insider_threat"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ANOMALOUS_ACTIVITY = "anomalous_activity"
    OTHER = "other"

class ResponseAction(Enum):
    """Automated response actions"""
    BLOCK_IP = "block_ip"
    BLOCK_USER = "block_user"
    ISOLATE_SYSTEM = "isolate_system"
    DISABLE_ACCOUNT = "disable_account"
    RESET_PASSWORDS = "reset_passwords"
    ROTATE_KEYS = "rotate_keys"
    BACKUP_DATA = "backup_data"
    SCAN_SYSTEM = "scan_system"
    UPDATE_FIREWALL = "update_firewall"
    NOTIFICATION = "notification"
    ESCALATE = "escalate"
    LOG_ONLY = "log_only"

@dataclass
class Incident:
    """Security incident data model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    incident_type: IncidentType = IncidentType.OTHER
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.NEW
    source: str = ""
    affected_assets: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert incident to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, (IncidentType, IncidentSeverity, IncidentStatus)):
                data[key] = value.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Incident':
        """Create incident from dictionary"""
        # Convert ISO format back to datetime
        for key, value in data.items():
            if key.endswith('_at') and value:
                if isinstance(value, str):
                    data[key] = datetime.fromisoformat(value)
            elif key in ['incident_type', 'severity', 'status'] and value:
                if key == 'incident_type':
                    data[key] = IncidentType(value)
                elif key == 'severity':
                    data[key] = IncidentSeverity(value)
                elif key == 'status':
                    data[key] = IncidentStatus(value)
        return cls(**data)

@dataclass
class ResponseAction:
    """Response action configuration"""
    name: ResponseAction
    description: str = ""
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # seconds

    def should_execute(self, incident: Incident) -> bool:
        """Check if action should be executed for incident"""
        if not self.enabled:
            return False

        # Check severity conditions
        if 'min_severity' in self.conditions:
            severity_order = [IncidentSeverity.INFO, IncidentSeverity.LOW,
                            IncidentSeverity.MEDIUM, IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]
            min_level = severity_order.index(IncidentSeverity(self.conditions['min_severity']))
            current_level = severity_order.index(incident.severity)
            if current_level < min_level:
                return False

        # Check incident type conditions
        if 'incident_types' in self.conditions:
            if incident.incident_type.value not in self.conditions['incident_types']:
                return False

        # Check custom conditions
        if 'custom_conditions' in self.conditions:
            for condition in self.conditions['custom_conditions']:
                if not self._evaluate_condition(condition, incident):
                    return False

        return True

    def _evaluate_condition(self, condition: Dict[str, Any], incident: Incident) -> bool:
        """Evaluate custom condition"""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        if not all([field, operator, value is not None]):
            return False

        incident_value = getattr(incident, field, None)
        if incident_value is None:
            return False

        if operator == 'equals':
            return incident_value == value
        elif operator == 'contains':
            return value in incident_value
        elif operator == 'in':
            return incident_value in value
        elif operator == 'greater_than':
            return incident_value > value
        elif operator == 'less_than':
            return incident_value < value

        return False

class IncidentResponse:
    """Automated incident response system"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.action_handlers: Dict[ResponseAction, Callable] = {}
        self.incident_templates: Dict[str, Template] = {}
        self.escalation_rules: List[Dict[str, Any]] = []
        self.notification_channels: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize incident response system"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

            # Load configuration
            await self.load_configuration()

            # Register action handlers
            self.register_action_handlers()

            # Load incident templates
            await self.load_templates()

            # Test Redis connection
            await self.redis_client.ping()
            logger.info("Incident response system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize incident response: {e}")
            raise

    async def load_configuration(self):
        """Load incident response configuration"""
        try:
            # Load escalation rules
            escalation_config = await self.load_config_file("escalation_rules.json")
            if escalation_config:
                self.escalation_rules = escalation_config.get("rules", [])

            # Load notification channels
            notification_config = await self.load_config_file("notification_channels.json")
            if notification_config:
                self.notification_channels = notification_config.get("channels", [])

            logger.info("Incident response configuration loaded")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    async def load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load configuration file"""
        try:
            config_path = Path(__file__).parent / "config" / filename
            if config_path.exists():
                async with aiofiles.open(config_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to load config file {filename}: {e}")
        return None

    def register_action_handlers(self):
        """Register automated response action handlers"""
        self.action_handlers = {
            ResponseAction.BLOCK_IP: self.handle_block_ip,
            ResponseAction.BLOCK_USER: self.handle_block_user,
            ResponseAction.ISOLATE_SYSTEM: self.handle_isolate_system,
            ResponseAction.DISABLE_ACCOUNT: self.handle_disable_account,
            ResponseAction.RESET_PASSWORDS: self.handle_reset_passwords,
            ResponseAction.ROTATE_KEYS: self.handle_rotate_keys,
            ResponseAction.BACKUP_DATA: self.handle_backup_data,
            ResponseAction.SCAN_SYSTEM: self.handle_scan_system,
            ResponseAction.UPDATE_FIREWALL: self.handle_update_firewall,
            ResponseAction.NOTIFICATION: self.handle_notification,
            ResponseAction.ESCALATE: self.handle_escalate,
            ResponseAction.LOG_ONLY: self.handle_log_only,
        }

    async def load_templates(self):
        """Load incident report templates"""
        templates = {
            "incident_report": """
Incident Report: {{ incident.title }}
================================
ID: {{ incident.id }}
Severity: {{ incident.severity.value.upper() }}
Type: {{ incident.incident_type.value }}
Status: {{ incident.status.value }}

Description:
{{ incident.description }}

Timeline:
{% for event in incident.timeline %}
- {{ event.timestamp }}: {{ event.description }}
{% endfor %}

Actions Taken:
{% for action in incident.actions_taken %}
- {{ action.timestamp }}: {{ action.description }}
{% endfor %}
""",
            "notification": """
Security Alert: {{ incident.title }}
Severity: {{ incident.severity.value }}
{{ incident.description }}
""",
        }

        for name, template_str in templates.items():
            self.incident_templates[name] = Template(template_str)

    async def create_incident(self,
                            title: str,
                            description: str,
                            incident_type: IncidentType,
                            severity: IncidentSeverity,
                            source: str = "",
                            affected_assets: List[str] = None,
                            metadata: Dict[str, Any] = None,
                            evidence: List[Dict[str, Any]] = None) -> Incident:
        """Create new security incident"""
        try:
            incident = Incident(
                title=title,
                description=description,
                incident_type=incident_type,
                severity=severity,
                source=source,
                affected_assets=affected_assets or [],
                metadata=metadata or {},
                evidence=evidence or []
            )

            # Add initial timeline entry
            incident.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "description": "Incident created",
                "type": "system",
                "details": {"source": source}
            })

            # Save incident to storage
            await self.save_incident(incident)

            # Trigger automated response
            await self.trigger_response(incident)

            logger.info(f"Created incident {incident.id}: {title}")
            return incident

        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            raise

    async def trigger_response(self, incident: Incident):
        """Trigger automated response for incident"""
        try:
            logger.info(f"Triggering response for incident {incident.id}")

            # Get applicable response actions
            actions = await self.get_applicable_actions(incident)

            # Execute actions in parallel
            tasks = []
            for action in actions:
                if action.should_execute(incident):
                    task = self.execute_action(action, incident)
                    tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log results
                for i, result in enumerate(results):
                    action = actions[i]
                    if isinstance(result, Exception):
                        logger.error(f"Action {action.name.value} failed: {result}")
                    else:
                        logger.info(f"Action {action.name.value} completed: {result}")

            # Check for escalation
            await self.check_escalation(incident)

        except Exception as e:
            logger.error(f"Failed to trigger response for incident {incident.id}: {e}")

    async def get_applicable_actions(self, incident: Incident) -> List[ResponseAction]:
        """Get applicable response actions for incident"""
        # Default action configurations
        default_actions = [
            ResponseAction(
                name=ResponseAction.LOG_ONLY,
                description="Log incident",
                enabled=True
            )
        ]

        # Add severity-based actions
        if incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            default_actions.extend([
                ResponseAction(
                    name=ResponseAction.NOTIFICATION,
                    description="Send notifications",
                    enabled=True,
                    conditions={"min_severity": "high"}
                )
            ])

        if incident.severity == IncidentSeverity.CRITICAL:
            default_actions.extend([
                ResponseAction(
                    name=ResponseAction.ESCALATE,
                    description="Escalate to senior staff",
                    enabled=True,
                    conditions={"min_severity": "critical"}
                )
            ])

        # Add type-specific actions
        if incident.incident_type == IncidentType.DDOS_ATTACK:
            default_actions.append(
                ResponseAction(
                    name=ResponseAction.BLOCK_IP,
                    description="Block attacking IPs",
                    enabled=True,
                    conditions={"incident_types": ["ddos_attack"]},
                    parameters={"duration": 3600}  # 1 hour
                )
            )

        elif incident.incident_type == IncidentType.UNAUTHORIZED_ACCESS:
            default_actions.extend([
                ResponseAction(
                    name=ResponseAction.BLOCK_USER,
                    description="Block unauthorized user",
                    enabled=True,
                    conditions={"incident_types": ["unauthorized_access"]}
                ),
                ResponseAction(
                    name=ResponseAction.DISABLE_ACCOUNT,
                    description="Disable compromised account",
                    enabled=True,
                    conditions={"incident_types": ["unauthorized_access"]}
                )
            ])

        elif incident.incident_type == IncidentType.DATA_EXFILTRATION:
            default_actions.extend([
                ResponseAction(
                    name=ResponseAction.ISOLATE_SYSTEM,
                    description="Isolate affected systems",
                    enabled=True,
                    conditions={"incident_types": ["data_exfiltration"]}
                ),
                ResponseAction(
                    name=ResponseAction.ROTATE_KEYS,
                    description="Rotate encryption keys",
                    enabled=True,
                    conditions={"incident_types": ["data_exfiltration"]}
                )
            ])

        return default_actions

    async def execute_action(self, action: ResponseAction, incident: Incident) -> Dict[str, Any]:
        """Execute response action"""
        try:
            handler = self.action_handlers.get(action.name)
            if not handler:
                raise ValueError(f"No handler for action: {action.name}")

            logger.info(f"Executing action {action.name.value} for incident {incident.id}")

            # Record action start
            start_time = datetime.now()
            incident.actions_taken.append({
                "timestamp": start_time.isoformat(),
                "action": action.name.value,
                "description": action.description,
                "status": "in_progress"
            })

            # Execute action with timeout
            try:
                result = await asyncio.wait_for(
                    handler(incident, action.parameters),
                    timeout=action.timeout
                )

                # Record successful completion
                incident.actions_taken[-1]["status"] = "completed"
                incident.actions_taken[-1]["result"] = result
                incident.actions_taken[-1]["duration"] = (datetime.now() - start_time).total_seconds()

                return result

            except asyncio.TimeoutError:
                incident.actions_taken[-1]["status"] = "timeout"
                incident.actions_taken[-1]["error"] = "Action timed out"
                raise

        except Exception as e:
            # Record failed action
            if incident.actions_taken:
                incident.actions_taken[-1]["status"] = "failed"
                incident.actions_taken[-1]["error"] = str(e)

            logger.error(f"Action {action.name.value} failed: {e}")
            raise
        finally:
            # Save updated incident
            await self.save_incident(incident)

    # Action handlers
    async def handle_block_ip(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Block IP address action handler"""
        # Implementation would integrate with firewall/IDS
        blocked_ips = []

        # Extract IPs from evidence or metadata
        for evidence in incident.evidence:
            if "ip_address" in evidence:
                ip = evidence["ip_address"]
                # Add to blocklist (placeholder implementation)
                blocked_ips.append(ip)

        return {"blocked_ips": blocked_ips, "duration": parameters.get("duration", 3600)}

    async def handle_block_user(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Block user action handler"""
        # Implementation would integrate with user management
        blocked_users = []

        # Extract users from evidence or metadata
        for evidence in incident.evidence:
            if "user_id" in evidence:
                user_id = evidence["user_id"]
                blocked_users.append(user_id)

        return {"blocked_users": blocked_users}

    async def handle_isolate_system(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Isolate system action handler"""
        # Implementation would integrate with system management
        isolated_systems = incident.affected_assets

        return {"isolated_systems": isolated_systems}

    async def handle_disable_account(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Disable account action handler"""
        # Implementation would integrate with authentication system
        disabled_accounts = []

        for evidence in incident.evidence:
            if "account_id" in evidence:
                account_id = evidence["account_id"]
                disabled_accounts.append(account_id)

        return {"disabled_accounts": disabled_accounts}

    async def handle_reset_passwords(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Reset passwords action handler"""
        # Implementation would integrate with user management
        reset_accounts = []

        for evidence in incident.evidence:
            if "user_id" in evidence:
                user_id = evidence["user_id"]
                reset_accounts.append(user_id)

        return {"passwords_reset": reset_accounts}

    async def handle_rotate_keys(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rotate encryption keys action handler"""
        # Implementation would integrate with key management
        return {"keys_rotated": True, "timestamp": datetime.now().isoformat()}

    async def handle_backup_data(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Backup data action handler"""
        # Implementation would integrate with backup system
        return {"backup_initiated": True, "assets": incident.affected_assets}

    async def handle_scan_system(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scan system action handler"""
        # Implementation would integrate with vulnerability scanner
        return {"scan_initiated": True, "systems": incident.affected_assets}

    async def handle_update_firewall(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update firewall action handler"""
        # Implementation would integrate with firewall management
        return {"firewall_updated": True, "timestamp": datetime.now().isoformat()}

    async def handle_notification(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification action handler"""
        notifications_sent = []

        # Generate notification content
        template = self.incident_templates.get("notification")
        if template:
            content = template.render(incident=incident)

            # Send to configured channels
            for channel in self.notification_channels:
                if self._should_notify_channel(channel, incident):
                    # Send notification (placeholder implementation)
                    notifications_sent.append({
                        "channel": channel["name"],
                        "type": channel["type"],
                        "sent_at": datetime.now().isoformat()
                    })

        return {"notifications_sent": notifications_sent}

    async def handle_escalate(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate incident action handler"""
        # Update incident status
        incident.status = IncidentStatus.ASSIGNED

        # Add escalation to timeline
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "description": "Incident escalated to senior staff",
            "type": "escalation",
            "details": parameters
        })

        # Send escalation notifications
        escalated_contacts = []
        for rule in self.escalation_rules:
            if self._should_escalate(rule, incident):
                escalated_contacts.extend(rule.get("contacts", []))

        return {"escalated": True, "contacts": escalated_contacts}

    async def handle_log_only(self, incident: Incident, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Log only action handler"""
        logger.info(f"Incident logged: {incident.id} - {incident.title}")
        return {"logged": True, "timestamp": datetime.now().isoformat()}

    def _should_notify_channel(self, channel: Dict[str, Any], incident: Incident) -> bool:
        """Check if incident should be sent to notification channel"""
        # Check severity filters
        if "severities" in channel:
            if incident.severity.value not in channel["severities"]:
                return False

        # Check type filters
        if "incident_types" in channel:
            if incident.incident_type.value not in channel["incident_types"]:
                return False

        return True

    def _should_escalate(self, rule: Dict[str, Any], incident: Incident) -> bool:
        """Check if incident should be escalated by rule"""
        # Check severity conditions
        if "severity" in rule:
            if incident.severity.value not in rule["severity"]:
                return False

        # Check type conditions
        if "incident_types" in rule:
            if incident.incident_type.value not in rule["incident_types"]:
                return False

        return True

    async def check_escalation(self, incident: Incident):
        """Check if incident needs escalation"""
        try:
            escalated = False

            # Check escalation rules
            for rule in self.escalation_rules:
                if self._should_escalate(rule, incident):
                    if not escalated:
                        # Execute escalation action
                        escalation_action = ResponseAction(
                            name=ResponseAction.ESCALATE,
                            description="Escalate based on rules",
                            parameters=rule
                        )
                        await self.execute_action(escalation_action, incident)
                        escalated = True

        except Exception as e:
            logger.error(f"Failed to check escalation for incident {incident.id}: {e}")

    async def update_incident_status(self, incident_id: str, status: IncidentStatus,
                                   assigned_to: Optional[str] = None,
                                   resolution: Optional[str] = None) -> bool:
        """Update incident status"""
        try:
            incident = await self.get_incident(incident_id)
            if not incident:
                return False

            # Update fields
            old_status = incident.status
            incident.status = status

            if assigned_to:
                incident.assigned_to = assigned_to
                incident.assigned_at = datetime.now()

            if resolution and status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                incident.resolution = resolution
                incident.resolved_at = datetime.now()

            # Add timeline entry
            incident.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "description": f"Status changed from {old_status.value} to {status.value}",
                "type": "status_change",
                "details": {"assigned_to": assigned_to, "resolution": resolution}
            })

            # Save updated incident
            await self.save_incident(incident)

            logger.info(f"Updated incident {incident_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update incident status: {e}")
            return False

    async def add_evidence(self, incident_id: str, evidence: Dict[str, Any]) -> bool:
        """Add evidence to incident"""
        try:
            incident = await self.get_incident(incident_id)
            if not incident:
                return False

            evidence["added_at"] = datetime.now().isoformat()
            incident.evidence.append(evidence)

            # Add timeline entry
            incident.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "description": f"Evidence added: {evidence.get('type', 'unknown')}",
                "type": "evidence_added",
                "details": evidence
            })

            await self.save_incident(incident)
            return True

        except Exception as e:
            logger.error(f"Failed to add evidence to incident {incident_id}: {e}")
            return False

    async def save_incident(self, incident: Incident):
        """Save incident to storage"""
        try:
            if self.redis_client:
                # Save to Redis
                key = f"incident:{incident.id}"
                await self.redis_client.set(
                    key,
                    json.dumps(incident.to_dict()),
                    ex=86400 * 30  # 30 days TTL
                )

                # Add to incident list
                await self.redis_client.lpush("incidents", incident.id)
                await self.redis_client.expire("incidents", 86400 * 30)

        except Exception as e:
            logger.error(f"Failed to save incident {incident.id}: {e}")

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        try:
            if self.redis_client:
                key = f"incident:{incident_id}"
                data = await self.redis_client.get(key)
                if data:
                    return Incident.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Failed to get incident {incident_id}: {e}")
        return None

    async def list_incidents(self,
                           status: Optional[IncidentStatus] = None,
                           severity: Optional[IncidentSeverity] = None,
                           limit: int = 100) -> List[Incident]:
        """List incidents with filters"""
        try:
            incidents = []

            if self.redis_client:
                incident_ids = await self.redis_client.lrange("incidents", 0, limit - 1)

                for incident_id in incident_ids:
                    incident = await self.get_incident(incident_id)
                    if incident:
                        # Apply filters
                        if status and incident.status != status:
                            continue
                        if severity and incident.severity != severity:
                            continue

                        incidents.append(incident)

            return incidents

        except Exception as e:
            logger.error(f"Failed to list incidents: {e}")
            return []

    async def generate_incident_report(self, incident_id: str) -> Optional[str]:
        """Generate incident report"""
        try:
            incident = await self.get_incident(incident_id)
            if not incident:
                return None

            template = self.incident_templates.get("incident_report")
            if template:
                return template.render(incident=incident)

            return None

        except Exception as e:
            logger.error(f"Failed to generate incident report: {e}")
            return None

    async def get_metrics(self) -> Dict[str, Any]:
        """Get incident response metrics"""
        try:
            incidents = await self.list_incidents(limit=1000)

            # Calculate metrics
            total_incidents = len(incidents)
            incidents_by_status = {}
            incidents_by_severity = {}
            incidents_by_type = {}

            for incident in incidents:
                # Count by status
                status = incident.status.value
                incidents_by_status[status] = incidents_by_status.get(status, 0) + 1

                # Count by severity
                severity = incident.severity.value
                incidents_by_severity[severity] = incidents_by_severity.get(severity, 0) + 1

                # Count by type
                incident_type = incident.incident_type.value
                incidents_by_type[incident_type] = incidents_by_type.get(incident_type, 0) + 1

            # Calculate resolution metrics
            resolved_incidents = [i for i in incidents if i.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]]
            avg_resolution_time = 0

            if resolved_incidents:
                resolution_times = []
                for incident in resolved_incidents:
                    if incident.resolved_at and incident.detected_at:
                        resolution_time = (incident.resolved_at - incident.detected_at).total_seconds()
                        resolution_times.append(resolution_time)

                if resolution_times:
                    avg_resolution_time = sum(resolution_times) / len(resolution_times)

            return {
                "total_incidents": total_incidents,
                "incidents_by_status": incidents_by_status,
                "incidents_by_severity": incidents_by_severity,
                "incidents_by_type": incidents_by_type,
                "resolved_incidents": len(resolved_incidents),
                "resolution_rate": len(resolved_incidents) / total_incidents if total_incidents > 0 else 0,
                "avg_resolution_time_hours": avg_resolution_time / 3600 if avg_resolution_time > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get incident response metrics: {e}")
            return {}