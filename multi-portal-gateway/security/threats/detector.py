#!/usr/bin/env python3
"""
DMLogn8n Threat Detection Engine
Advanced threat detection using machine learning and pattern analysis
"""

import json
import logging
import asyncio
import time
import re
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis.asyncio as redis
from fastapi import Request, Response
import yaml
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import os
from ipaddress import ip_address, ip_network
import geoip2.database

logger = logging.getLogger(__name__)

class ThreatType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    SCANNER = "scanner"
    BOTNET = "botnet"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ZERO_DAY = "zero_day"
    INSIDER_THREAT = "insider_threat"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"

class ThreatSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class DetectionMethod(Enum):
    SIGNATURE_BASED = "signature_based"
    ANOMALY_DETECTION = "anomaly_detection"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    MACHINE_LEARNING = "machine_learning"
    HEURISTIC = "heuristic"

@dataclass
class ThreatSignature:
    signature_id: str
    name: str
    threat_type: ThreatType
    pattern: str
    severity: ThreatSeverity
    method: DetectionMethod
    description: str
    references: List[str] = None
    false_positive_rate: float = 0.0

@dataclass
class ThreatAlert:
    alert_id: str
    timestamp: datetime
    threat_type: ThreatType
    severity: ThreatSeverity
    source_ip: str
    target_resource: str
    detection_method: DetectionMethod
    confidence: float
    details: Dict[str, Any]
    signature_id: Optional[str] = None
    mitre_tactics: List[str] = None
    iocs: List[str] = None

@dataclass
class BehaviorProfile:
    user_id: str
    baseline_features: Dict[str, float]
    last_updated: datetime
    anomaly_threshold: float = 2.0
    risk_score: float = 0.0

class ThreatDetector:
    """
    Advanced threat detection engine with multiple detection methods
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.geoip_reader = None

        # Detection components
        self.signatures = {}
        self.behavior_profiles = {}
        self.anomaly_models = {}
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        self.threat_alerts = deque(maxlen=10000)

        # Machine learning models
        self.isolation_forest = None
        self.scaler = None
        self.vectorizer = None
        self.models_loaded = False

        # Detection settings
        self.enable_ml_detection = self.config.get('enable_ml_detection', True)
        self.enable_behavioral_analysis = self.config.get('enable_behavioral_analysis', True)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.1)
        self.min_confidence = self.config.get('min_confidence', 0.7)

        # Initialize detection components
        self._initialize_signatures()
        self._initialize_ml_models()

    async def initialize(self):
        """Initialize threat detection components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=6,  # Threat detection specific DB
                decode_responses=True
            )

            # Initialize GeoIP
            try:
                self.geoip_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
            except Exception as e:
                logger.warning(f"GeoIP database not available: {e}")

            # Load machine learning models
            await self._load_ml_models()

            # Load behavior profiles
            await self._load_behavior_profiles()

            # Load threat signatures
            await self._load_threat_signatures()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("Threat Detection Engine initialized")

        except Exception as e:
            logger.error(f"Threat Detection Engine initialization failed: {e}")
            raise

    async def analyze_request(self, request: Request, response: Response = None) -> List[ThreatAlert]:
        """
        Analyze HTTP request for threats using multiple detection methods
        """
        alerts = []

        try:
            # Extract request features
            features = await self._extract_request_features(request, response)

            # Signature-based detection
            signature_alerts = await self._signature_based_detection(request, features)
            alerts.extend(signature_alerts)

            # Machine learning detection
            if self.enable_ml_detection and self.models_loaded:
                ml_alerts = await self._ml_based_detection(request, features)
                alerts.extend(ml_alerts)

            # Behavioral analysis
            if self.enable_behavioral_analysis:
                behavior_alerts = await self._behavioral_analysis(request, features)
                alerts.extend(behavior_alerts)

            # Anomaly detection
            anomaly_alerts = await self._anomaly_detection(request, features)
            alerts.extend(anomaly_alerts)

            # Statistical analysis
            statistical_alerts = await self._statistical_analysis(request, features)
            alerts.extend(statistical_alerts)

            # Store alerts and update metrics
            for alert in alerts:
                await self._process_threat_alert(alert)

            return alerts

        except Exception as e:
            logger.error(f"Request analysis error: {e}")
            return []

    async def analyze_log_entry(self, log_entry: Dict[str, Any]) -> List[ThreatAlert]:
        """
        Analyze log entry for threats
        """
        alerts = []

        try:
            # Extract log features
            features = await self._extract_log_features(log_entry)

            # Apply detection methods
            signature_alerts = await self._signature_based_log_detection(log_entry, features)
            alerts.extend(signature_alerts)

            if self.enable_ml_detection and self.models_loaded:
                ml_alerts = await self._ml_based_log_detection(log_entry, features)
                alerts.extend(ml_alerts)

            return alerts

        except Exception as e:
            logger.error(f"Log analysis error: {e}")
            return []

    async def analyze_network_traffic(self, traffic_data: Dict[str, Any]) -> List[ThreatAlert]:
        """
        Analyze network traffic for threats
        """
        alerts = []

        try:
            # Extract network features
            features = await self._extract_network_features(traffic_data)

            # Network-specific detection
            ddos_alerts = await self._detect_ddos(traffic_data, features)
            alerts.extend(ddos_alerts)

            port_scan_alerts = await self._detect_port_scan(traffic_data, features)
            alerts.extend(port_scan_alerts)

            botnet_alerts = await self._detect_botnet_activity(traffic_data, features)
            alerts.extend(botnet_alerts)

            return alerts

        except Exception as e:
            logger.error(f"Network traffic analysis error: {e}")
            return []

    async def update_behavior_profile(self, user_id: str, features: Dict[str, float]):
        """
        Update user behavior profile with new data
        """
        try:
            if user_id not in self.behavior_profiles:
                # Create new profile
                self.behavior_profiles[user_id] = BehaviorProfile(
                    user_id=user_id,
                    baseline_features=features.copy(),
                    last_updated=datetime.now(),
                    anomaly_threshold=2.0,
                    risk_score=0.0
                )
            else:
                # Update existing profile
                profile = self.behavior_profiles[user_id]

                # Calculate anomaly score
                anomaly_score = self._calculate_anomaly_score(
                    profile.baseline_features,
                    features
                )

                # Update baseline with exponential moving average
                alpha = 0.1  # Learning rate
                for key, value in features.items():
                    if key in profile.baseline_features:
                        profile.baseline_features[key] = (
                            alpha * value + (1 - alpha) * profile.baseline_features[key]
                        )
                    else:
                        profile.baseline_features[key] = value

                # Update risk score
                profile.risk_score = min(1.0, profile.risk_score * 0.9 + anomaly_score * 0.1)
                profile.last_updated = datetime.now()

                # Store in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        f"behavior_profile:{user_id}",
                        86400 * 30,  # 30 days
                        json.dumps(asdict(profile))
                    )

        except Exception as e:
            logger.error(f"Behavior profile update error: {e}")

    # Detection methods
    async def _signature_based_detection(self, request: Request, features: Dict[str, Any]) -> List[ThreatAlert]:
        """Signature-based threat detection"""
        alerts = []

        try:
            # Get request data
            method = request.method
            path = request.url.path
            query_string = str(request.url.query)
            headers = dict(request.headers)

            # Combine request data for pattern matching
            request_data = f"{method} {path} {query_string}"

            # Get request body
            try:
                body = await request.body()
                if body:
                    request_data += " " + body.decode('utf-8', errors='ignore')
            except:
                pass

            # Check against signatures
            for signature in self.signatures.values():
                if re.search(signature.pattern, request_data, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                    alert = ThreatAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        threat_type=signature.threat_type,
                        severity=signature.severity,
                        source_ip=self._get_client_ip(request),
                        target_resource=path,
                        detection_method=DetectionMethod.SIGNATURE_BASED,
                        confidence=1.0 - signature.false_positive_rate,
                        details={
                            'signature_id': signature.signature_id,
                            'signature_name': signature.name,
                            'matched_pattern': signature.pattern,
                            'request_sample': request_data[:200] + "..." if len(request_data) > 200 else request_data
                        },
                        signature_id=signature.signature_id,
                        mitre_tactics=self._get_mitre_tactics(signature.threat_type)
                    )
                    alerts.append(alert)

        except Exception as e:
            logger.error(f"Signature-based detection error: {e}")

        return alerts

    async def _ml_based_detection(self, request: Request, features: Dict[str, Any]) -> List[ThreatAlert]:
        """Machine learning-based threat detection"""
        alerts = []

        try:
            if not self.models_loaded or not self.isolation_forest:
                return alerts

            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)

            if feature_vector is None:
                return alerts

            # Scale features
            scaled_features = self.scaler.transform([feature_vector])

            # Predict anomaly
            anomaly_score = self.isolation_forest.decision_function(scaled_features)[0]
            is_anomaly = self.isolation_forest.predict(scaled_features)[0] == -1

            if is_anomaly and anomaly_score < -self.anomaly_threshold:
                # Convert score to confidence (0-1)
                confidence = min(1.0, abs(anomaly_score))

                if confidence >= self.min_confidence:
                    alert = ThreatAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                        severity=ThreatSeverity.HIGH if confidence > 0.8 else ThreatSeverity.MEDIUM,
                        source_ip=self._get_client_ip(request),
                        target_resource=request.url.path,
                        detection_method=DetectionMethod.MACHINE_LEARNING,
                        confidence=confidence,
                        details={
                            'anomaly_score': float(anomaly_score),
                            'features': features,
                            'feature_vector': feature_vector[:10]  # First 10 features for debugging
                        }
                    )
                    alerts.append(alert)

        except Exception as e:
            logger.error(f"ML-based detection error: {e}")

        return alerts

    async def _behavioral_analysis(self, request: Request, features: Dict[str, Any]) -> List[ThreatAlert]:
        """Behavioral analysis for user/session"""
        alerts = []

        try:
            user_id = self._get_user_id_from_request(request)
            if not user_id:
                return alerts

            if user_id not in self.behavior_profiles:
                # Create initial profile
                await self.update_behavior_profile(user_id, features)
                return alerts

            profile = self.behavior_profiles[user_id]

            # Calculate behavioral anomaly score
            anomaly_score = self._calculate_anomaly_score(
                profile.baseline_features,
                features
            )

            # Check if anomaly exceeds threshold
            if anomaly_score > profile.anomaly_threshold:
                confidence = min(1.0, anomaly_score / profile.anomaly_threshold)

                if confidence >= self.min_confidence:
                    severity = ThreatSeverity.HIGH if profile.risk_score > 0.7 else ThreatSeverity.MEDIUM

                    alert = ThreatAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                        severity=severity,
                        source_ip=self._get_client_ip(request),
                        target_resource=request.url.path,
                        detection_method=DetectionMethod.BEHAVIORAL_ANALYSIS,
                        confidence=confidence,
                        details={
                            'user_id': user_id,
                            'anomaly_score': anomaly_score,
                            'baseline_risk_score': profile.risk_score,
                            'behavioral_drift': features,
                            'profile_last_updated': profile.last_updated.isoformat()
                        }
                    )
                    alerts.append(alert)

            # Update behavior profile
            await self.update_behavior_profile(user_id, features)

        except Exception as e:
            logger.error(f"Behavioral analysis error: {e}")

        return alerts

    async def _anomaly_detection(self, request: Request, features: Dict[str, Any]) -> List[ThreatAlert]:
        """Statistical anomaly detection"""
        alerts = []

        try:
            source_ip = self._get_client_ip(request)

            # Analyze request patterns
            current_time = time.time()

            # Check for rapid requests from same IP
            ip_requests = self.request_history[source_ip]
            recent_requests = [req_time for req_time in ip_requests if current_time - req_time < 60]

            if len(recent_requests) > 100:  # More than 100 requests in 1 minute
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.DDOS,
                    severity=ThreatSeverity.HIGH,
                    source_ip=source_ip,
                    target_resource=request.url.path,
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=min(1.0, len(recent_requests) / 100),
                    details={
                        'requests_per_minute': len(recent_requests),
                        'threshold': 100,
                        'time_window': 60
                    },
                    mitre_tactics=['Impact']
                )
                alerts.append(alert)

            # Check for unusual request patterns
            if self._is_unusual_request_pattern(request, features):
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    severity=ThreatSeverity.MEDIUM,
                    source_ip=source_ip,
                    target_resource=request.url.path,
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=0.7,
                    details={
                        'unusual_pattern': True,
                        'features': features
                    }
                )
                alerts.append(alert)

            # Add current request to history
            ip_requests.append(current_time)

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")

        return alerts

    async def _statistical_analysis(self, request: Request, features: Dict[str, Any]) -> List[ThreatAlert]:
        """Statistical analysis for threat detection"""
        alerts = []

        try:
            # Analyze header anomalies
            header_anomalies = self._analyze_header_anomalies(request)
            if header_anomalies:
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    severity=ThreatSeverity.LOW,
                    source_ip=self._get_client_ip(request),
                    target_resource=request.url.path,
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=0.6,
                    details={
                        'header_anomalies': header_anomalies
                    }
                )
                alerts.append(alert)

            # Analyze payload characteristics
            payload_anomalies = self._analyze_payload_anomalies(request, features)
            if payload_anomalies:
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    severity=ThreatSeverity.MEDIUM,
                    source_ip=self._get_client_ip(request),
                    target_resource=request.url.path,
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=0.7,
                    details={
                        'payload_anomalies': payload_anomalies
                    }
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Statistical analysis error: {e}")

        return alerts

    # Network-specific detection methods
    async def _detect_ddos(self, traffic_data: Dict[str, Any], features: Dict[str, Any]) -> List[ThreatAlert]:
        """Detect DDoS attacks"""
        alerts = []

        try:
            source_ip = traffic_data.get('source_ip')
            packet_count = traffic_data.get('packet_count', 0)
            byte_count = traffic_data.get('byte_count', 0)

            # Check for high packet rate
            if packet_count > 10000:  # More than 10k packets
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.DDOS,
                    severity=ThreatSeverity.HIGH,
                    source_ip=source_ip,
                    target_resource=traffic_data.get('destination_port', 'unknown'),
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=min(1.0, packet_count / 10000),
                    details={
                        'packet_count': packet_count,
                        'byte_count': byte_count,
                        'attack_type': 'volumetric_ddos'
                    },
                    mitre_tactics=['Impact']
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"DDoS detection error: {e}")

        return alerts

    async def _detect_port_scan(self, traffic_data: Dict[str, Any], features: Dict[str, Any]) -> List[ThreatAlert]:
        """Detect port scanning activity"""
        alerts = []

        try:
            source_ip = traffic_data.get('source_ip')
            ports_scanned = traffic_data.get('ports_scanned', [])

            # Check for port scanning
            if len(ports_scanned) > 10:  # Scanning more than 10 ports
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.SCANNER,
                    severity=ThreatSeverity.MEDIUM,
                    source_ip=source_ip,
                    target_resource=f"ports:{','.join(map(str, ports_scanned[:10]))}",
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=min(1.0, len(ports_scanned) / 100),
                    details={
                        'ports_scanned': len(ports_scanned),
                        'ports_list': ports_scanned[:20],  # First 20 ports
                        'scan_type': 'port_scan'
                    },
                    mitre_tactics=['Discovery']
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Port scan detection error: {e}")

        return alerts

    async def _detect_botnet_activity(self, traffic_data: Dict[str, Any], features: Dict[str, Any]) -> List[ThreatAlert]:
        """Detect botnet activity"""
        alerts = []

        try:
            source_ip = traffic_data.get('source_ip')
            c2_indicators = traffic_data.get('c2_indicators', [])

            # Check for C2 communication patterns
            if c2_indicators:
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.BOTNET,
                    severity=ThreatSeverity.CRITICAL,
                    source_ip=source_ip,
                    target_resource="c2_communication",
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=0.9,
                    details={
                        'c2_indicators': c2_indicators,
                        'botnet_activity': True
                    },
                    mitre_tactics=['Command and Control']
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Botnet detection error: {e}")

        return alerts

    # Helper methods
    async def _extract_request_features(self, request: Request, response: Response = None) -> Dict[str, float]:
        """Extract features from HTTP request"""
        features = {}

        try:
            # Basic request features
            features['request_method'] = hash(request.method) % 1000 / 1000.0
            features['path_length'] = len(request.url.path) / 1000.0
            features['query_length'] = len(str(request.url.query)) / 1000.0
            features['header_count'] = len(request.headers) / 100.0

            # Header-based features
            user_agent = request.headers.get('user-agent', '')
            features['user_agent_length'] = len(user_agent) / 1000.0
            features['user_agent_entropy'] = self._calculate_entropy(user_agent)

            # Content features
            content_length = request.headers.get('content-length', '0')
            try:
                features['content_length'] = int(content_length) / 1000000.0
            except:
                features['content_length'] = 0.0

            # URL features
            features['path_depth'] = request.url.path.count('/')
            features['query_param_count'] = len(request.query_params)
            features['has_file_extension'] = 1.0 if '.' in request.url.path.split('/')[-1] else 0.0

            # Security-related features
            features['has_authorization'] = 1.0 if 'authorization' in request.headers else 0.0
            features['has_api_key'] = 1.0 if 'x-api-key' in request.headers or 'api_key' in request.query_params else 0.0

            # Response features (if available)
            if response:
                features['response_status'] = response.status_code / 1000.0
                features['response_size'] = len(getattr(response, 'body', b'')) / 1000000.0

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")

        return features

    async def _extract_log_features(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from log entry"""
        features = {}

        try:
            # Log level features
            level = log_entry.get('level', '').upper()
            features['log_level'] = hash(level) % 1000 / 1000.0

            # Message features
            message = log_entry.get('message', '')
            features['message_length'] = len(message) / 1000.0
            features['message_entropy'] = self._calculate_entropy(message)

            # Time-based features
            timestamp = log_entry.get('timestamp')
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                features['hour_of_day'] = dt.hour / 24.0
                features['day_of_week'] = dt.weekday() / 7.0

        except Exception as e:
            logger.error(f"Log feature extraction error: {e}")

        return features

    async def _extract_network_features(self, traffic_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from network traffic"""
        features = {}

        try:
            features['packet_count'] = traffic_data.get('packet_count', 0) / 10000.0
            features['byte_count'] = traffic_data.get('byte_count', 0) / 1000000.0
            features['duration'] = traffic_data.get('duration', 0) / 1000.0
            features['unique_ports'] = len(traffic_data.get('ports_scanned', [])) / 1000.0

        except Exception as e:
            logger.error(f"Network feature extraction error: {e}")

        return features

    def _prepare_feature_vector(self, features: Dict[str, float]) -> Optional[List[float]]:
        """Prepare feature vector for ML models"""
        try:
            # Define expected feature order
            feature_order = [
                'request_method', 'path_length', 'query_length', 'header_count',
                'user_agent_length', 'user_agent_entropy', 'content_length',
                'path_depth', 'query_param_count', 'has_file_extension',
                'has_authorization', 'has_api_key', 'response_status', 'response_size'
            ]

            # Create vector
            vector = []
            for feature_name in feature_order:
                vector.append(features.get(feature_name, 0.0))

            return vector

        except Exception as e:
            logger.error(f"Feature vector preparation error: {e}")
            return None

    def _calculate_anomaly_score(self, baseline: Dict[str, float], current: Dict[str, float]) -> float:
        """Calculate anomaly score using euclidean distance"""
        try:
            if not baseline or not current:
                return 0.0

            # Get common features
            common_features = set(baseline.keys()) & set(current.keys())
            if not common_features:
                return 0.0

            # Calculate euclidean distance
            distance = 0.0
            for feature in common_features:
                diff = baseline[feature] - current[feature]
                distance += diff * diff

            return distance ** 0.5

        except Exception as e:
            logger.error(f"Anomaly score calculation error: {e}")
            return 0.0

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        try:
            if not text:
                return 0.0

            # Count character frequencies
            char_counts = defaultdict(int)
            for char in text:
                char_counts[char] += 1

            # Calculate entropy
            entropy = 0.0
            text_len = len(text)
            for count in char_counts.values():
                probability = count / text_len
                if probability > 0:
                    entropy -= probability * np.log2(probability)

            return entropy / 8.0  # Normalize by max entropy

        except Exception as e:
            logger.error(f"Entropy calculation error: {e}")
            return 0.0

    def _is_unusual_request_pattern(self, request: Request, features: Dict[str, Any]) -> bool:
        """Check for unusual request patterns"""
        try:
            # Check for unusual path patterns
            path = request.url.path

            # Common attack patterns
            suspicious_patterns = [
                r'\.\./',  # Path traversal
                r'<script',  # XSS
                r'union.*select',  # SQL injection
                r'exec\s*\(',  # Command injection
                r'%[0-9a-f]{2}',  # URL encoding (excessive)
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    return True

            # Check for unusual header combinations
            headers = dict(request.headers)
            if not headers.get('user-agent'):
                return True

            if headers.get('user-agent') == ''):
                return True

            # Check for unusual content lengths
            content_length = headers.get('content-length', '0')
            try:
                if int(content_length) > 10000000:  # 10MB
                    return True
            except:
                pass

            return False

        except Exception as e:
            logger.error(f"Unusual pattern detection error: {e}")
            return False

    def _analyze_header_anomalies(self, request: Request) -> List[str]:
        """Analyze HTTP headers for anomalies"""
        anomalies = []

        try:
            headers = dict(request.headers)

            # Missing common headers
            if 'user-agent' not in headers:
                anomalies.append('missing_user_agent')

            if 'host' not in headers:
                anomalies.append('missing_host')

            # Suspicious header values
            user_agent = headers.get('user-agent', '')
            if len(user_agent) > 500:
                anomalies.append('oversized_user_agent')

            if not user_agent or user_agent.lower() in ['bot', 'crawler', 'scanner']:
                anomalies.append('suspicious_user_agent')

            # Too many headers
            if len(headers) > 50:
                anomalies.append('excessive_headers')

        except Exception as e:
            logger.error(f"Header anomaly analysis error: {e}")

        return anomalies

    def _analyze_payload_anomalies(self, request: Request, features: Dict[str, Any]) -> List[str]:
        """Analyze request payload for anomalies"""
        anomalies = []

        try:
            content_type = request.headers.get('content-type', '')
            content_length = request.headers.get('content-length', '0')

            # Large payload without proper content-type
            try:
                if int(content_length) > 1000000 and not content_type:
                    anomalies.append('large_payload_no_content_type')
            except:
                pass

            # Suspicious content types
            suspicious_types = ['application/x-executable', 'application/octet-stream']
            if content_type in suspicious_types:
                anomalies.append('suspicious_content_type')

            # High entropy payload (possible encrypted/malicious content)
            if features.get('user_agent_entropy', 0) > 0.8:
                anomalies.append('high_entropy_payload')

        except Exception as e:
            logger.error(f"Payload anomaly analysis error: {e}")

        return anomalies

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_user_id_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try to get user from JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header[7:]
                # Decode JWT (simplified)
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get('sub') or payload.get('user_id')
            except:
                pass

        return None

    def _get_mitre_tactics(self, threat_type: ThreatType) -> List[str]:
        """Map threat types to MITRE ATT&CK tactics"""
        tactics_mapping = {
            ThreatType.SQL_INJECTION: ['Initial Access', 'Execution'],
            ThreatType.XSS: ['Initial Access', 'Execution'],
            ThreatType.COMMAND_INJECTION: ['Execution', 'Privilege Escalation'],
            ThreatType.PATH_TRAVERSAL: ['Discovery'],
            ThreatType.BRUTE_FORCE: ['Credential Access'],
            ThreatType.DDOS: ['Impact'],
            ThreatType.SCANNER: ['Discovery'],
            ThreatType.BOTNET: ['Command and Control'],
            ThreatType.DATA_EXFILTRATION: ['Collection', 'Exfiltration'],
            ThreatType.PRIVILEGE_ESCALATION: ['Privilege Escalation'],
            ThreatType.INSIDER_THREAT: ['Initial Access', 'Execution'],
            ThreatType.ANOMALOUS_BEHAVIOR: ['Discovery', 'Persistence']
        }

        return tactics_mapping.get(threat_type, [])

    async def _process_threat_alert(self, alert: ThreatAlert):
        """Process and store threat alert"""
        try:
            # Store alert
            self.threat_alerts.append(alert)

            # Store in Redis
            if self.redis_client:
                await self.redis_client.lpush(
                    "threat_alerts",
                    json.dumps(asdict(alert))
                )
                await self.redis_client.ltrim("threat_alerts", 0, 10000)

                # Update threat statistics
                await self.redis_client.incr(f"threat_stats:{alert.threat_type.value}")
                await self.redis_client.incr(f"threat_stats:severity_{alert.severity.value}")

            logger.warning(f"Threat detected: {alert.threat_type.value} from {alert.source_ip} with confidence {alert.confidence:.2f}")

        except Exception as e:
            logger.error(f"Threat alert processing error: {e}")

    # Initialization methods
    def _initialize_signatures(self):
        """Initialize default threat signatures"""
        signatures = [
            ThreatSignature(
                signature_id="sql_injection_1",
                name="SQL Injection - Union Select",
                threat_type=ThreatType.SQL_INJECTION,
                pattern=r"(?i)(union\s+select|select\s+.*\s+from\s+)",
                severity=ThreatSeverity.HIGH,
                method=DetectionMethod.SIGNATURE_BASED,
                description="Detects SQL injection attempts using UNION SELECT",
                references=["https://owasp.org/www-community/attacks/SQL_Injection"]
            ),
            ThreatSignature(
                signature_id="xss_1",
                name="Cross-Site Scripting - Script Tag",
                threat_type=ThreatType.XSS,
                pattern=r"(?i)(<script[^>]*>.*?</script>)",
                severity=ThreatSeverity.HIGH,
                method=DetectionMethod.SIGNATURE_BASED,
                description="Detects XSS attempts using script tags",
                references=["https://owasp.org/www-community/attacks/xss/"]
            ),
            ThreatSignature(
                signature_id="command_injection_1",
                name="Command Injection - Shell Commands",
                threat_type=ThreatType.COMMAND_INJECTION,
                pattern=r"(?i)(;\s*(whoami|id|uname|pwd|ls|cat|rm)\b)",
                severity=ThreatSeverity.CRITICAL,
                method=DetectionMethod.SIGNATURE_BASED,
                description="Detects command injection attempts",
                references=["https://owasp.org/www-community/attacks/Command_Injection"]
            ),
            ThreatSignature(
                signature_id="path_traversal_1",
                name="Path Traversal - Directory Traversal",
                threat_type=ThreatType.PATH_TRAVERSAL,
                pattern=r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
                severity=ThreatSeverity.HIGH,
                method=DetectionMethod.SIGNATURE_BASED,
                description="Detects path traversal attempts",
                references=["https://owasp.org/www-community/attacks/Path_Traversal"]
            )
        ]

        for signature in signatures:
            self.signatures[signature.signature_id] = signature

    def _initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            # Initialize isolation forest
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )

            # Initialize scaler
            self.scaler = StandardScaler()

            # Initialize text vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )

            logger.info("ML models initialized")

        except Exception as e:
            logger.error(f"ML model initialization error: {e}")

    async def _load_ml_models(self):
        """Load trained ML models from disk"""
        try:
            model_dir = "/home/activeloguser/DMLogn8n/multi-portal-gateway/security/models"

            # Load isolation forest
            if_model_path = os.path.join(model_dir, "isolation_forest.joblib")
            if os.path.exists(if_model_path):
                self.isolation_forest = joblib.load(if_model_path)
                self.models_loaded = True
                logger.info("Loaded isolation forest model")

            # Load scaler
            scaler_path = os.path.join(model_dir, "scaler.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            # Load vectorizer
            vectorizer_path = os.path.join(model_dir, "vectorizer.joblib")
            if os.path.exists(vectorizer_path):
                self.vectorizer = joblib.load(vectorizer_path)

        except Exception as e:
            logger.error(f"ML model loading error: {e}")
            self.models_loaded = False

    async def _load_behavior_profiles(self):
        """Load behavior profiles from Redis"""
        try:
            if not self.redis_client:
                return

            keys = await self.redis_client.keys("behavior_profile:*")
            for key in keys:
                profile_data = await self.redis_client.get(key)
                if profile_data:
                    profile_dict = json.loads(profile_data)
                    profile = BehaviorProfile(
                        user_id=profile_dict['user_id'],
                        baseline_features=profile_dict['baseline_features'],
                        last_updated=datetime.fromisoformat(profile_dict['last_updated']),
                        anomaly_threshold=profile_dict.get('anomaly_threshold', 2.0),
                        risk_score=profile_dict.get('risk_score', 0.0)
                    )
                    self.behavior_profiles[profile.user_id] = profile

            logger.info(f"Loaded {len(self.behavior_profiles)} behavior profiles")

        except Exception as e:
            logger.error(f"Behavior profiles loading error: {e}")

    async def _load_threat_signatures(self):
        """Load additional threat signatures from configuration"""
        try:
            signatures_config = self.config.get('threat_signatures', {})
            for sig_id, sig_config in signatures_config.items():
                signature = ThreatSignature(
                    signature_id=sig_id,
                    name=sig_config.get('name', ''),
                    threat_type=ThreatType(sig_config.get('threat_type')),
                    pattern=sig_config.get('pattern', ''),
                    severity=ThreatSeverity(sig_config.get('severity', 2)),
                    method=DetectionMethod(sig_config.get('method', 'signature_based')),
                    description=sig_config.get('description', ''),
                    references=sig_config.get('references', []),
                    false_positive_rate=sig_config.get('false_positive_rate', 0.0)
                )
                self.signatures[sig_id] = signature

            logger.info(f"Loaded {len(self.signatures)} threat signatures")

        except Exception as e:
            logger.error(f"Threat signatures loading error: {e}")

    async def _start_background_tasks(self):
        """Start background tasks for threat detection"""
        try:
            # Model retraining
            asyncio.create_task(self._periodic_model_retraining())

            # Profile cleanup
            asyncio.create_task(self._periodic_profile_cleanup())

            # Alert aggregation
            asyncio.create_task(self._periodic_alert_aggregation())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _periodic_model_retraining(self):
        """Periodically retrain ML models"""
        while True:
            try:
                await asyncio.sleep(86400 * 7)  # Retrain weekly

                if self.enable_ml_detection:
                    await self._retrain_models()
                    logger.info("ML models retrained")

            except Exception as e:
                logger.error(f"Model retraining error: {e}")
                await asyncio.sleep(3600)

    async def _periodic_profile_cleanup(self):
        """Clean up old behavior profiles"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily cleanup

                cutoff_time = datetime.now() - timedelta(days=90)
                expired_profiles = [
                    user_id for user_id, profile in self.behavior_profiles.items()
                    if profile.last_updated < cutoff_time
                ]

                for user_id in expired_profiles:
                    del self.behavior_profiles[user_id]
                    if self.redis_client:
                        await self.redis_client.delete(f"behavior_profile:{user_id}")

                logger.info(f"Cleaned up {len(expired_profiles)} expired behavior profiles")

            except Exception as e:
                logger.error(f"Profile cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _periodic_alert_aggregation(self):
        """Aggregate and analyze threat alerts"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                # Analyze alert patterns
                await self._analyze_alert_patterns()

            except Exception as e:
                logger.error(f"Alert aggregation error: {e}")
                await asyncio.sleep(300)

    async def _retrain_models(self):
        """Retrain machine learning models with new data"""
        try:
            # This is a placeholder for model retraining
            # In production, implement proper model retraining with new data
            logger.info("Model retraining completed (placeholder)")

        except Exception as e:
            logger.error(f"Model retraining error: {e}")

    async def _analyze_alert_patterns(self):
        """Analyze patterns in threat alerts"""
        try:
            # Get recent alerts from Redis
            if self.redis_client:
                recent_alerts = await self.redis_client.lrange("threat_alerts", 0, 1000)

                # Analyze patterns
                threat_counts = defaultdict(int)
                source_ips = defaultdict(int)

                for alert_json in recent_alerts:
                    alert = json.loads(alert_json)
                    threat_type = alert.get('threat_type')
                    source_ip = alert.get('source_ip')

                    threat_counts[threat_type] += 1
                    source_ips[source_ip] += 1

                # Store analysis results
                analysis = {
                    'timestamp': datetime.now().isoformat(),
                    'threat_counts': dict(threat_counts),
                    'top_source_ips': dict(sorted(source_ips.items(), key=lambda x: x[1], reverse=True)[:10])
                }

                await self.redis_client.setex(
                    "threat_analysis",
                    86400,  # 24 hours
                    json.dumps(analysis)
                )

        except Exception as e:
            logger.error(f"Alert pattern analysis error: {e}")

    # Log-based detection methods
    async def _signature_based_log_detection(self, log_entry: Dict[str, Any], features: Dict[str, Any]) -> List[ThreatAlert]:
        """Signature-based detection for log entries"""
        alerts = []

        try:
            message = log_entry.get('message', '')
            level = log_entry.get('level', '').upper()
            source = log_entry.get('source', '')

            # Check log message against signatures
            for signature in self.signatures.values():
                if re.search(signature.pattern, message, re.IGNORECASE):
                    alert = ThreatAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        threat_type=signature.threat_type,
                        severity=signature.severity,
                        source_ip=log_entry.get('source_ip', 'unknown'),
                        target_resource=source,
                        detection_method=DetectionMethod.SIGNATURE_BASED,
                        confidence=1.0 - signature.false_positive_rate,
                        details={
                            'signature_id': signature.signature_id,
                            'log_level': level,
                            'log_message': message[:200],
                            'source': source
                        },
                        signature_id=signature.signature_id
                    )
                    alerts.append(alert)

            # Check for critical log levels
            if level in ['CRITICAL', 'ALERT', 'EMERGENCY']:
                alert = ThreatAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    severity=ThreatSeverity.HIGH,
                    source_ip=log_entry.get('source_ip', 'unknown'),
                    target_resource=source,
                    detection_method=DetectionMethod.HEURISTIC,
                    confidence=0.8,
                    details={
                        'log_level': level,
                        'log_message': message[:200],
                        'source': source
                    }
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Log signature detection error: {e}")

        return alerts

    async def _ml_based_log_detection(self, log_entry: Dict[str, Any], features: Dict[str, Any]) -> List[ThreatAlert]:
        """ML-based detection for log entries"""
        alerts = []

        try:
            if not self.models_loaded or not self.vectorizer:
                return alerts

            # Analyze log message with text vectorization
            message = log_entry.get('message', '')

            # Vectorize message
            try:
                message_vector = self.vectorizer.transform([message])

                # Use simple anomaly detection for text
                # (In production, use proper text anomaly detection models)
                text_length = len(message)
                if text_length > 1000 or self._calculate_entropy(message) > 0.8:
                    alert = ThreatAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                        severity=ThreatSeverity.MEDIUM,
                        source_ip=log_entry.get('source_ip', 'unknown'),
                        target_resource=log_entry.get('source', ''),
                        detection_method=DetectionMethod.MACHINE_LEARNING,
                        confidence=0.7,
                        details={
                            'text_length': text_length,
                            'text_entropy': self._calculate_entropy(message),
                            'log_level': log_entry.get('level', ''),
                            'message_preview': message[:100]
                        }
                    )
                    alerts.append(alert)

            except Exception as e:
                logger.error(f"Text vectorization error: {e}")

        except Exception as e:
            logger.error(f"ML log detection error: {e}")

        return alerts