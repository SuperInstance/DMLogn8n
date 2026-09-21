"""
DMLogn8n Compliance Manager - Payment Processing Compliance and Fraud Detection

This module handles payment processing compliance, fraud detection, anti-money laundering (AML),
Know Your Customer (KYC) verification, and regulatory compliance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict
import redis
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis
import hashlib
import re
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import geoip2.database
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    PENDING_REVIEW = "pending_review"
    UNDER_INVESTIGATION = "under_investigation"
    NON_COMPLIANT = "non_compliant"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VerificationStatus(Enum):
    """KYC verification status"""
    NOT_VERIFIED = "not_verified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

class FraudType(Enum):
    """Types of fraud to detect"""
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    ACCOUNT_TAKEOVER = "account_takeover"
    IDENTITY_THEFT = "identity_theft"
    MONEY_LAUNDERING = "money_laundering"
    CHARGEBACK_FRAUD = "chargeback_fraud"
    BONUS_ABUSE = "bonus_abuse"
    COLLUSION = "collusion"
    SYNTHETIC_IDENTITY = "synthetic_identity"

class RegulationType(Enum):
    """Regulatory compliance types"""
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    CCPA = "ccpa"
    AML = "aml"
    KYC = "kyc"
    PSD2 = "psd2"
    SOX = "sox"

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    id: str
    name: str
    description: str
    regulation_type: RegulationType
    rule_type: str  # threshold, pattern, velocity, list_check
    parameters: Dict[str, Any]
    action: str  # alert, block, flag, require_review
    severity: RiskLevel
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FraudDetectionRule:
    """Fraud detection rule"""
    id: str
    name: str
    description: str
    fraud_type: FraudType
    conditions: Dict[str, Any]
    risk_score: int
    action: str
    machine_learning_model: bool = False
    active: bool = True

@dataclass
class ComplianceAlert:
    """Compliance alert"""
    id: str
    user_id: str
    rule_id: str
    alert_type: str
    severity: RiskLevel
    title: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

@dataclass
class TransactionRisk:
    """Transaction risk assessment"""
    transaction_id: str
    user_id: str
    risk_score: float
    risk_factors: List[str]
    recommended_action: str
    assessment_details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class KYCDocument:
    """KYC verification document"""
    id: str
    user_id: str
    document_type: str  # passport, driver_license, id_card, utility_bill, etc.
    document_url: str
    extraction_data: Dict[str, Any]
    verification_status: VerificationStatus
    verification_score: float
    expiry_date: Optional[datetime]
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None

@dataclass
class ComplianceReport:
    """Compliance report"""
    id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)

class ComplianceManager:
    """Main compliance management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        self.fraud_rules: Dict[str, FraudDetectionRule] = {}
        self.ml_models: Dict[str, Any] = {}
        self.blacklist_cache: Dict[str, Any] = {}
        self.watchlist_cache: Dict[str, Any] = {}
        self.geoip_reader = None

    async def initialize(self):
        """Initialize compliance manager"""
        logger.info("Initializing DMLogn8n Compliance Manager...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_compliance')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Initialize GeoIP database
        await self._initialize_geoip()

        # Load compliance rules
        await self._load_compliance_rules()

        # Load fraud detection rules
        await self._load_fraud_rules()

        # Initialize machine learning models
        await self._initialize_ml_models()

        # Load external blacklists and watchlists
        await self._load_external_lists()

        # Start background tasks
        asyncio.create_task(self._transaction_monitor())
        asyncio.create_task(self._fraud_detection_engine())
        asyncio.create_task(self._compliance_reporter())
        asyncio.create_task(self._list_updater())

        logger.info("Compliance Manager initialized successfully")

    async def _initialize_geoip(self):
        """Initialize GeoIP database"""
        try:
            # Initialize GeoIP2 reader
            geoip_db_path = self.config.get('geoip_database_path', 'GeoLite2-City.mmdb')
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
                logger.info("GeoIP database loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load GeoIP database: {e}")
                self.geoip_reader = None
        except Exception as e:
            logger.error(f"Error initializing GeoIP: {e}")
            self.geoip_reader = None

    async def _load_compliance_rules(self):
        """Load compliance rules"""
        default_rules = [
            ComplianceRule(
                id="pci_transaction_limit",
                name="PCI Transaction Limit",
                description="Daily transaction limit for PCI compliance",
                regulation_type=RegulationType.PCI_DSS,
                rule_type="threshold",
                parameters={
                    "daily_limit": 10000,
                    "currency": "USD",
                    "time_window": 24
                },
                action="alert",
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                id="gdpr_data_retention",
                name="GDPR Data Retention",
                description="Data retention period compliance",
                regulation_type=RegulationType.GDPR,
                rule_type="threshold",
                parameters={
                    "max_retention_days": 365,
                    "auto_delete": True
                },
                action="flag",
                severity=RiskLevel.MEDIUM
            ),
            ComplianceRule(
                id="aml_large_transaction",
                name="AML Large Transaction Reporting",
                description="Report transactions over threshold",
                regulation_type=RegulationType.AML,
                rule_type="threshold",
                parameters={
                    "reporting_threshold": 10000,
                    "currency": "USD"
                },
                action="require_review",
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                id="kyc_verification_required",
                name="KYC Verification Required",
                description="KYC verification for high-value transactions",
                regulation_type=RegulationType.KYC,
                rule_type="threshold",
                parameters={
                    "verification_threshold": 1000,
                    "currency": "USD"
                },
                action="block",
                severity=RiskLevel.CRITICAL
            ),
            ComplianceRule(
                id="suspicious_pattern_velocity",
                name="Suspicious Pattern Velocity Check",
                description="Detect rapid transaction patterns",
                regulation_type=RegulationType.AML,
                rule_type="velocity",
                parameters={
                    "max_transactions_per_minute": 5,
                    "max_transactions_per_hour": 50,
                    "amount_variance_threshold": 0.5
                },
                action="flag",
                severity=RiskLevel.HIGH
            ),
            ComplianceRule(
                id="sanctioned_country_check",
                name="Sanctioned Country Check",
                description="Block transactions from sanctioned countries",
                regulation_type=RegulationType.AML,
                rule_type="list_check",
                parameters={
                    "sanctioned_countries": ["IR", "KP", "SY", "CU"],
                    "action": "block"
                },
                action="block",
                severity=RiskLevel.CRITICAL
            )
        ]

        for rule in default_rules:
            self.compliance_rules[rule.id] = rule
            await self._cache_compliance_rule(rule)

    async def _cache_compliance_rule(self, rule: ComplianceRule):
        """Cache compliance rule"""
        rule_data = {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'regulation_type': rule.regulation_type.value,
            'rule_type': rule.rule_type,
            'parameters': rule.parameters,
            'action': rule.action,
            'severity': rule.severity.value,
            'active': rule.active,
            'metadata': rule.metadata
        }

        await self.redis_client.setex(
            f"compliance_rule:{rule.id}",
            86400 * 30,  # 30 days
            json.dumps(rule_data)
        )

    async def _load_fraud_rules(self):
        """Load fraud detection rules"""
        default_rules = [
            FraudDetectionRule(
                id="velocity_check",
                name="Transaction Velocity Check",
                description="Detect unusual transaction velocity",
                fraud_type=FraudType.CREDIT_CARD_FRAUD,
                conditions={
                    "max_per_minute": 3,
                    "max_per_hour": 20,
                    "amount_suspicion_threshold": 500
                },
                risk_score=40,
                action="flag"
            ),
            FraudDetectionRule(
                id="device_fingerprint",
                name="Suspicious Device Fingerprint",
                description="Detect multiple accounts from same device",
                fraud_type=FraudType.ACCOUNT_TAKEOVER,
                conditions={
                    "max_accounts_per_device": 3,
                    "time_window_hours": 24
                },
                risk_score=60,
                action="flag"
            ),
            FraudDetectionRule(
                id="ip_risk_check",
                name="High Risk IP Address",
                description="Check IP against known fraud databases",
                fraud_type=FraudType.IDENTITY_THEFT,
                conditions={
                    "use_external_blacklists": True,
                    "check_tor_exit_nodes": True,
                    "check_proxy": True
                },
                risk_score=80,
                action="flag"
            ),
            FraudDetectionRule(
                id="card_testing",
                name="Card Testing Pattern",
                description="Detect small amount transactions for card testing",
                fraud_type=FraudType.CREDIT_CARD_FRAUD,
                conditions={
                    "small_amount_threshold": 1.0,
                    "consecutive_small_transactions": 5,
                    "time_window_minutes": 10
                },
                risk_score=70,
                action="block"
            ),
            FraudDetectionRule(
                id="ml_fraud_detection",
                name="Machine Learning Fraud Detection",
                description="ML model for fraud pattern detection",
                fraud_type=FraudType.SYNTHETIC_IDENTITY,
                conditions={
                    "model_threshold": 0.7,
                    "feature_set": ["transaction_amount", "frequency", "device_risk", "ip_risk"]
                },
                risk_score=90,
                action="flag",
                machine_learning_model=True
            )
        ]

        for rule in default_rules:
            self.fraud_rules[rule.id] = rule
            await self._cache_fraud_rule(rule)

    async def _cache_fraud_rule(self, rule: FraudDetectionRule):
        """Cache fraud rule"""
        rule_data = {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'fraud_type': rule.fraud_type.value,
            'conditions': rule.conditions,
            'risk_score': rule.risk_score,
            'action': rule.action,
            'machine_learning_model': rule.machine_learning_model,
            'active': rule.active
        }

        await self.redis_client.setex(
            f"fraud_rule:{rule.id}",
            86400 * 30,
            json.dumps(rule_data)
        )

    async def _initialize_ml_models(self):
        """Initialize machine learning models for fraud detection"""
        # Isolation Forest for anomaly detection
        self.ml_models['isolation_forest'] = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )

        # Random Forest for classification
        self.ml_models['random_forest'] = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )

        # Feature scaler
        self.ml_models['scaler'] = StandardScaler()

        logger.info("Machine learning models initialized")

    async def _load_external_lists(self):
        """Load external blacklists and watchlists"""
        try:
            # Load known fraudulent IPs
            await self._load_fraudulent_ips()

            # Load known compromised cards
            await self._load_compromised_cards()

            # Load sanctioned entities
            await self._load_sanctioned_entities()

            # Load high-risk countries
            await self._load_high_risk_countries()

            logger.info("External lists loaded successfully")

        except Exception as e:
            logger.error(f"Error loading external lists: {e}")

    async def _load_fraudulent_ips(self):
        """Load known fraudulent IP addresses"""
        # Mock data - in production would fetch from fraud databases
        fraudulent_ips = [
            "192.168.1.100",
            "10.0.0.50",
            "172.16.0.25"
        ]

        self.blacklist_cache['fraudulent_ips'] = fraudulent_ips
        await self.redis_client.setex(
            "blacklist:fraudulent_ips",
            86400,  # 24 hours
            json.dumps(fraudulent_ips)
        )

    async def _load_compromised_cards(self):
        """Load known compromised card numbers"""
        # Mock data - only last 4 digits shown for security
        compromised_cards = [
            "**** **** **** 1234",
            "**** **** **** 5678",
            "**** **** **** 9012"
        ]

        self.blacklist_cache['compromised_cards'] = compromised_cards
        await self.redis_client.setex(
            "blacklist:compromised_cards",
            86400 * 7,  # 7 days
            json.dumps(compromised_cards)
        )

    async def _load_sanctioned_entities(self):
        """Load sanctioned entities and individuals"""
        # Mock data
        sanctioned_entities = [
            {"name": "Sanctioned Entity 1", "type": "organization", "countries": ["IR"]},
            {"name": "Sanctioned Individual 1", "type": "individual", "countries": ["KP"]}
        ]

        self.watchlist_cache['sanctioned_entities'] = sanctioned_entities
        await self.redis_client.setex(
            "watchlist:sanctioned_entities",
            86400,  # 24 hours
            json.dumps(sanctioned_entities)
        )

    async def _load_high_risk_countries(self):
        """Load high-risk countries for transactions"""
        high_risk_countries = [
            "AF", "IR", "KP", "MM", "SO", "SS", "SD", "SY", "YE", "ZW"
        ]

        self.blacklist_cache['high_risk_countries'] = high_risk_countries
        await self.redis_client.setex(
            "blacklist:high_risk_countries",
            86400 * 30,  # 30 days
            json.dumps(high_risk_countries)
        )

    async def assess_transaction_risk(self, transaction_data: Dict[str, Any]) -> TransactionRisk:
        """Assess risk level for a transaction"""
        try:
            transaction_id = transaction_data.get('transaction_id', str(uuid.uuid4()))
            user_id = transaction_data.get('user_id')
            amount = Decimal(str(transaction_data.get('amount', 0)))
            currency = transaction_data.get('currency', 'USD')
            ip_address = transaction_data.get('ip_address')
            device_fingerprint = transaction_data.get('device_fingerprint')
            card_last4 = transaction_data.get('card_last4', '')

            risk_score = 0.0
            risk_factors = []

            # Check amount thresholds
            if amount > Decimal('1000'):
                risk_score += 20
                risk_factors.append("high_amount_transaction")

            if amount > Decimal('10000'):
                risk_score += 30
                risk_factors.append("very_high_amount_transaction")

            # Check IP address
            ip_risk = await self._assess_ip_risk(ip_address)
            risk_score += ip_risk['score']
            risk_factors.extend(ip_risk['factors'])

            # Check device fingerprint
            device_risk = await self._assess_device_risk(device_fingerprint, user_id)
            risk_score += device_risk['score']
            risk_factors.extend(device_risk['factors'])

            # Check card against blacklist
            card_risk = await self._assess_card_risk(card_last4)
            risk_score += card_risk['score']
            risk_factors.extend(card_risk['factors'])

            # Check transaction velocity
            velocity_risk = await self._assess_transaction_velocity(user_id, transaction_id)
            risk_score += velocity_risk['score']
            risk_factors.extend(velocity_risk['factors'])

            # ML model prediction
            if self.ml_models.get('isolation_forest'):
                ml_risk = await self._assess_ml_risk(transaction_data)
                risk_score += ml_risk['score']
                risk_factors.extend(ml_risk['factors'])

            # Cap risk score at 100
            risk_score = min(100, risk_score)

            # Determine recommended action
            if risk_score >= 80:
                recommended_action = "block"
            elif risk_score >= 60:
                recommended_action = "manual_review"
            elif risk_score >= 40:
                recommended_action = "enhanced_monitoring"
            else:
                recommended_action = "proceed"

            assessment = TransactionRisk(
                transaction_id=transaction_id,
                user_id=user_id,
                risk_score=risk_score,
                risk_factors=risk_factors,
                recommended_action=recommended_action,
                assessment_details={
                    "amount": float(amount),
                    "currency": currency,
                    "ip_risk": ip_risk,
                    "device_risk": device_risk,
                    "card_risk": card_risk,
                    "velocity_risk": velocity_risk
                }
            )

            # Cache assessment
            await self._cache_transaction_risk(assessment)

            # Create alert if high risk
            if risk_score >= 60:
                await self._create_fraud_alert(assessment)

            return assessment

        except Exception as e:
            logger.error(f"Error assessing transaction risk: {e}")
            return TransactionRisk(
                transaction_id=transaction_data.get('transaction_id', 'unknown'),
                user_id=transaction_data.get('user_id', 'unknown'),
                risk_score=50.0,
                risk_factors=["assessment_error"],
                recommended_action="manual_review",
                assessment_details={"error": str(e)}
            )

    async def _assess_ip_risk(self, ip_address: str) -> Dict[str, Any]:
        """Assess IP address risk"""
        risk_score = 0
        factors = []

        if not ip_address:
            return {"score": 20, "factors": ["missing_ip_address"]}

        # Check against fraudulent IP blacklist
        if ip_address in self.blacklist_cache.get('fraudulent_ips', []):
            risk_score += 50
            factors.append("fraudulent_ip_blacklist")

        # Check if it's a private IP
        if self._is_private_ip(ip_address):
            risk_score += 10
            factors.append("private_ip_address")

        # Check GeoIP information
        if self.geoip_reader:
            try:
                response = self.geoip_reader.city(ip_address)
                country_code = response.country.iso_code

                # Check high-risk countries
                if country_code in self.blacklist_cache.get('high_risk_countries', []):
                    risk_score += 40
                    factors.append(f"high_risk_country_{country_code}")

                # Check for suspicious locations
                if response.country.iso_code in ['XX', 'A1']:  # Anonymous/Proxy
                    risk_score += 30
                    factors.append("anonymous_proxy")

            except Exception as e:
                logger.warning(f"GeoIP lookup failed for {ip_address}: {e}")
                risk_score += 5
                factors.append("geoip_lookup_failed")

        # Check IP reputation (simplified)
        if await self._check_ip_reputation(ip_address):
            risk_score += 25
            factors.append("poor_ip_reputation")

        return {"score": risk_score, "factors": factors}

    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is private"""
        try:
            private_ranges = [
                ('10.0.0.0', '10.255.255.255'),
                ('172.16.0.0', '172.31.255.255'),
                ('192.168.0.0', '192.168.255.255'),
                ('127.0.0.0', '127.255.255.255')
            ]

            ip_num = int(''.join(f'{int(octet):08b}' for octet in ip_address.split('.')), 2)

            for start_ip, end_ip in private_ranges:
                start_num = int(''.join(f'{int(octet):08b}' for octet in start_ip.split('.')), 2)
                end_num = int(''.join(f'{int(octet):08b}' for octet in end_ip.split('.')), 2)
                if start_num <= ip_num <= end_num:
                    return True

            return False
        except:
            return True  # Assume private if parsing fails

    async def _check_ip_reputation(self, ip_address: str) -> bool:
        """Check IP reputation against external services"""
        # Simplified implementation
        # In production, would use services like MaxMind, IPQualityScore, etc.
        return False

    async def _assess_device_risk(self, device_fingerprint: str, user_id: str) -> Dict[str, Any]:
        """Assess device fingerprint risk"""
        risk_score = 0
        factors = []

        if not device_fingerprint:
            return {"score": 15, "factors": ["missing_device_fingerprint"]}

        # Check how many accounts use this device
        device_key = f"device_users:{device_fingerprint}"
        user_count = await self.redis_client.scard(device_key)

        if user_count > 5:
            risk_score += 40
            factors.append("multiple_accounts_device")
        elif user_count > 2:
            risk_score += 20
            factors.append("multiple_accounts_device_medium")

        # Check if device is new for this user
        user_devices_key = f"user_devices:{user_id}"
        is_known_device = await self.redis_client.sismember(user_devices_key, device_fingerprint)

        if not is_known_device:
            risk_score += 15
            factors.append("new_device_for_user")

        # Add device to user's known devices
        await self.redis_client.sadd(user_devices_key, device_fingerprint)
        await self.redis_client.expire(user_devices_key, 86400 * 30)  # 30 days

        # Add user to device users
        await self.redis_client.sadd(device_key, user_id)
        await self.redis_client.expire(device_key, 86400 * 30)

        return {"score": risk_score, "factors": factors}

    async def _assess_card_risk(self, card_last4: str) -> Dict[str, Any]:
        """Assess card risk based on last 4 digits"""
        risk_score = 0
        factors = []

        if not card_last4:
            return {"score": 10, "factors": ["missing_card_info"]}

        # Check against compromised cards
        if f"**** **** **** {card_last4}" in self.blacklist_cache.get('compromised_cards', []):
            risk_score += 80
            factors.append("compromised_card_blacklist")

        # Check for suspicious patterns (simplified)
        if card_last4 in ['0000', '1111', '1234', '4321']:
            risk_score += 30
            factors.append("suspicious_card_pattern")

        return {"score": risk_score, "factors": factors}

    async def _assess_transaction_velocity(self, user_id: str, transaction_id: str) -> Dict[str, Any]:
        """Assess transaction velocity risk"""
        risk_score = 0
        factors = []

        now = datetime.utcnow()

        # Check recent transactions
        recent_key = f"user_transactions:{user_id}:recent"
        recent_transactions = await self.redis_client.lrange(recent_key, 0, -1)

        # Count transactions in different time windows
        last_minute_count = 0
        last_hour_count = 0
        last_day_count = 0

        for tx_bytes in recent_transactions:
            tx_data = json.loads(tx_bytes.decode())
            tx_time = datetime.fromisoformat(tx_data['timestamp'])
            time_diff = (now - tx_time).total_seconds()

            if time_diff <= 60:  # Last minute
                last_minute_count += 1
            if time_diff <= 3600:  # Last hour
                last_hour_count += 1
            if time_diff <= 86400:  # Last day
                last_day_count += 1

        # Check velocity thresholds
        if last_minute_count >= 3:
            risk_score += 50
            factors.append("high_velocity_minute")

        if last_hour_count >= 20:
            risk_score += 30
            factors.append("high_velocity_hour")

        if last_day_count >= 100:
            risk_score += 20
            factors.append("high_velocity_day")

        # Add current transaction
        await self.redis_client.lpush(recent_key, json.dumps({
            'transaction_id': transaction_id,
            'timestamp': now.isoformat()
        }))
        await self.redis_client.ltrim(recent_key, 0, 999)  # Keep last 1000 transactions
        await self.redis_client.expire(recent_key, 86400 * 7)  # 7 days

        return {"score": risk_score, "factors": factors}

    async def _assess_ml_risk(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk using machine learning models"""
        risk_score = 0
        factors = []

        try:
            # Extract features
            features = await self._extract_ml_features(transaction_data)

            if len(features) >= 5:  # Minimum features required
                # Normalize features
                features_array = np.array(features).reshape(1, -1)

                # Predict using isolation forest
                model = self.ml_models.get('isolation_forest')
                if model:
                    prediction = model.predict(features_array)[0]
                    if prediction == -1:  # Anomaly detected
                        risk_score += 40
                        factors.append("ml_anomaly_detected")

                # Predict using random forest if trained
                rf_model = self.ml_models.get('random_forest')
                if hasattr(rf_model, 'feature_importances_'):
                    rf_prediction = rf_model.predict_proba(features_array)[0]
                    if len(rf_prediction) > 1 and rf_prediction[1] > 0.7:  # High fraud probability
                        risk_score += 35
                        factors.append("ml_high_fraud_probability")

        except Exception as e:
            logger.error(f"Error in ML risk assessment: {e}")
            factors.append("ml_assessment_error")

        return {"score": risk_score, "factors": factors}

    async def _extract_ml_features(self, transaction_data: Dict[str, Any]) -> List[float]:
        """Extract features for ML models"""
        features = []

        # Amount
        features.append(float(transaction_data.get('amount', 0)))

        # Time of day (normalized)
        now = datetime.utcnow()
        features.append(now.hour / 24.0)

        # Day of week (normalized)
        features.append(now.weekday() / 7.0)

        # Transaction frequency (simplified)
        user_id = transaction_data.get('user_id', '')
        recent_tx_key = f"user_transactions:{user_id}:recent"
        recent_count = await self.redis_client.llen(recent_tx_key)
        features.append(min(recent_count, 100) / 100.0)

        # Device risk (simplified)
        features.append(0.1)  # Placeholder

        # IP risk (simplified)
        features.append(0.1)  # Placeholder

        return features

    async def _cache_transaction_risk(self, risk: TransactionRisk):
        """Cache transaction risk assessment"""
        risk_data = {
            'transaction_id': risk.transaction_id,
            'user_id': risk.user_id,
            'risk_score': risk.risk_score,
            'risk_factors': risk.risk_factors,
            'recommended_action': risk.recommended_action,
            'assessment_details': risk.assessment_details,
            'timestamp': risk.timestamp.isoformat()
        }

        await self.redis_client.setex(
            f"transaction_risk:{risk.transaction_id}",
            86400 * 7,  # 7 days
            json.dumps(risk_data)
        )

    async def _create_fraud_alert(self, risk: TransactionRisk):
        """Create fraud alert for high-risk transaction"""
        alert = ComplianceAlert(
            id=str(uuid.uuid4()),
            user_id=risk.user_id,
            rule_id="ml_fraud_detection",
            alert_type="fraud_detection",
            severity=RiskLevel.HIGH if risk.risk_score >= 80 else RiskLevel.MEDIUM,
            title=f"High Risk Transaction Detected: {risk.transaction_id}",
            description=f"Transaction risk score: {risk.risk_score}",
            details={
                'transaction_id': risk.transaction_id,
                'risk_score': risk.risk_score,
                'risk_factors': risk.risk_factors,
                'recommended_action': risk.recommended_action
            }
        )

        await self._store_alert(alert)

    async def process_kyc_verification(self, user_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process KYC document verification"""
        try:
            document_id = str(uuid.uuid4())
            document_type = document_data.get('document_type')
            document_url = document_data.get('document_url')

            # Create KYC document record
            kyc_doc = KYCDocument(
                id=document_id,
                user_id=user_id,
                document_type=document_type,
                document_url=document_url,
                extraction_data={},
                verification_status=VerificationStatus.PENDING,
                verification_score=0.0
            )

            # Extract information from document (simplified)
            extraction_result = await self._extract_document_info(document_data)
            kyc_doc.extraction_data = extraction_result

            # Verify document (simplified)
            verification_result = await self._verify_document(kyc_doc)
            kyc_doc.verification_status = verification_result['status']
            kyc_doc.verification_score = verification_result['score']

            # Store document
            await self._store_kyc_document(kyc_doc)

            # Update user KYC status
            await self._update_user_kyc_status(user_id, kyc_doc)

            return {
                'success': True,
                'document_id': document_id,
                'verification_status': kyc_doc.verification_status.value,
                'verification_score': kyc_doc.verification_score,
                'extracted_data': kyc_doc.extraction_data
            }

        except Exception as e:
            logger.error(f"Error processing KYC verification: {e}")
            return {'success': False, 'error': str(e)}

    async def _extract_document_info(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from KYC document"""
        # Simplified implementation
        # In production, would use OCR services like Amazon Textract, Google Vision, etc.
        extracted_data = {
            'document_number': 'DOC123456',
            'name': 'John Doe',
            'date_of_birth': '1990-01-01',
            'expiry_date': '2025-01-01',
            'issuing_country': 'US',
            'confidence_score': 0.85
        }

        return extracted_data

    async def _verify_document(self, kyc_doc: KYCDocument) -> Dict[str, Any]:
        """Verify authenticity of KYC document"""
        # Simplified verification logic
        extracted_data = kyc_doc.extraction_data

        # Check for required fields
        required_fields = ['document_number', 'name', 'date_of_birth']
        missing_fields = [field for field in required_fields if not extracted_data.get(field)]

        if missing_fields:
            return {
                'status': VerificationStatus.REJECTED,
                'score': 0.0,
                'reason': f'Missing required fields: {missing_fields}'
            }

        # Check expiry date
        expiry_date = extracted_data.get('expiry_date')
        if expiry_date:
            try:
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
                if expiry < datetime.utcnow():
                    return {
                        'status': VerificationStatus.REJECTED,
                        'score': 0.0,
                        'reason': 'Document expired'
                    }
            except ValueError:
                pass

        # Calculate verification score
        base_score = extracted_data.get('confidence_score', 0.5)

        # Additional checks
        if extracted_data.get('issuing_country') in self.blacklist_cache.get('high_risk_countries', []):
            base_score *= 0.5

        # Determine status
        if base_score >= 0.8:
            status = VerificationStatus.VERIFIED
        elif base_score >= 0.6:
            status = VerificationStatus.PENDING
        else:
            status = VerificationStatus.REJECTED

        return {
            'status': status,
            'score': base_score
        }

    async def _store_kyc_document(self, kyc_doc: KYCDocument):
        """Store KYC document record"""
        document_data = {
            'id': kyc_doc.id,
            'user_id': kyc_doc.user_id,
            'document_type': kyc_doc.document_type,
            'document_url': kyc_doc.document_url,
            'extraction_data': kyc_doc.extraction_data,
            'verification_status': kyc_doc.verification_status.value,
            'verification_score': kyc_doc.verification_score,
            'expiry_date': kyc_doc.expiry_date.isoformat() if kyc_doc.expiry_date else None,
            'uploaded_at': kyc_doc.uploaded_at.isoformat(),
            'verified_at': kyc_doc.verified_at.isoformat() if kyc_doc.verified_at else None,
            'verified_by': kyc_doc.verified_by
        }

        await self.redis_client.setex(
            f"kyc_document:{kyc_doc.id}",
            86400 * 365,  # 1 year
            json.dumps(document_data)
        )

    async def _update_user_kyc_status(self, user_id: str, kyc_doc: KYCDocument):
        """Update user's KYC verification status"""
        user_kyc_key = f"user_kyc:{user_id}"

        # Get existing KYC documents for user
        user_documents = await self.redis_client.lrange(user_kyc_key, 0, -1)

        # Determine overall KYC status
        verified_count = 0
        total_count = len(user_documents) + 1  # Include current document

        for doc_bytes in user_documents:
            doc_data = json.loads(doc_bytes.decode())
            if doc_data.get('verification_status') == VerificationStatus.VERIFIED.value:
                verified_count += 1

        if kyc_doc.verification_status == VerificationStatus.VERIFIED:
            verified_count += 1

        # Calculate overall verification level
        if verified_count >= 2:
            overall_status = VerificationStatus.VERIFIED
        elif verified_count >= 1:
            overall_status = VerificationStatus.PENDING
        else:
            overall_status = VerificationStatus.NOT_VERIFIED

        # Store updated status
        user_status = {
            'user_id': user_id,
            'overall_status': overall_status.value,
            'verified_documents': verified_count,
            'total_documents': total_count,
            'last_updated': datetime.utcnow().isoformat()
        }

        await self.redis_client.setex(
            f"user_kyc_status:{user_id}",
            86400 * 365,  # 1 year
            json.dumps(user_status)
        )

        # Add document to user's document list
        await self.redis_client.lpush(user_kyc_key, json.dumps({
            'document_id': kyc_doc.id,
            'document_type': kyc_doc.document_type,
            'verification_status': kyc_doc.verification_status.value,
            'uploaded_at': kyc_doc.uploaded_at.isoformat()
        }))

    async def check_compliance_rules(self, transaction_data: Dict[str, Any]) -> List[ComplianceAlert]:
        """Check transaction against all compliance rules"""
        alerts = []

        for rule_id, rule in self.compliance_rules.items():
            if not rule.active:
                continue

            try:
                violation = await self._evaluate_compliance_rule(rule, transaction_data)
                if violation:
                    alert = ComplianceAlert(
                        id=str(uuid.uuid4()),
                        user_id=transaction_data.get('user_id', ''),
                        rule_id=rule_id,
                        alert_type="compliance_violation",
                        severity=rule.severity,
                        title=f"Compliance Rule Violation: {rule.name}",
                        description=violation['message'],
                        details=violation['details']
                    )
                    alerts.append(alert)
                    await self._store_alert(alert)

            except Exception as e:
                logger.error(f"Error evaluating compliance rule {rule_id}: {e}")

        return alerts

    async def _evaluate_compliance_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate a single compliance rule"""
        try:
            if rule.rule_type == "threshold":
                return await self._evaluate_threshold_rule(rule, transaction_data)
            elif rule.rule_type == "velocity":
                return await self._evaluate_velocity_rule(rule, transaction_data)
            elif rule.rule_type == "list_check":
                return await self._evaluate_list_check_rule(rule, transaction_data)
            elif rule.rule_type == "pattern":
                return await self._evaluate_pattern_rule(rule, transaction_data)

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")

        return None

    async def _evaluate_threshold_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate threshold-based compliance rule"""
        params = rule.parameters

        if rule.id == "pci_transaction_limit":
            # Check daily transaction limit
            daily_limit = params.get('daily_limit', 10000)
            user_id = transaction_data.get('user_id')
            amount = float(transaction_data.get('amount', 0))

            # Get user's daily transaction total
            daily_total_key = f"user_daily_total:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            daily_total = float(await self.redis_client.get(daily_total) or 0)

            if daily_total + amount > daily_limit:
                return {
                    'message': f"Daily transaction limit of ${daily_limit} exceeded",
                    'details': {
                        'current_daily_total': daily_total,
                        'transaction_amount': amount,
                        'limit_exceeded_by': (daily_total + amount) - daily_limit
                    }
                }

        elif rule.id == "aml_large_transaction":
            # Check AML reporting threshold
            reporting_threshold = params.get('reporting_threshold', 10000)
            amount = float(transaction_data.get('amount', 0))

            if amount >= reporting_threshold:
                return {
                    'message': f"Transaction amount ${amount} exceeds AML reporting threshold of ${reporting_threshold}",
                    'details': {
                        'transaction_amount': amount,
                        'reporting_threshold': reporting_threshold,
                        'requires_aml_report': True
                    }
                }

        elif rule.id == "kyc_verification_required":
            # Check if KYC verification is required
            verification_threshold = params.get('verification_threshold', 1000)
            amount = float(transaction_data.get('amount', 0))
            user_id = transaction_data.get('user_id')

            # Get user's KYC status
            kyc_status_key = f"user_kyc_status:{user_id}"
            kyc_status = await self.redis_client.get(kyc_status_key)

            if not kyc_status or json.loads(kyc_status)['overall_status'] != VerificationStatus.VERIFIED.value:
                if amount >= verification_threshold:
                    return {
                        'message': f"Transaction amount ${amount} requires KYC verification",
                        'details': {
                            'transaction_amount': amount,
                            'verification_threshold': verification_threshold,
                            'kyc_status': json.loads(kyc_status)['overall_status'] if kyc_status else 'not_verified'
                        }
                    }

        return None

    async def _evaluate_velocity_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate velocity-based compliance rule"""
        params = rule.parameters
        user_id = transaction_data.get('user_id')

        # Get recent transactions for velocity analysis
        recent_key = f"user_transactions:{user_id}:recent"
        recent_transactions = await self.redis_client.lrange(recent_key, 0, -1)

        now = datetime.utcnow()
        count_per_minute = 0
        count_per_hour = 0

        for tx_bytes in recent_transactions:
            tx_data = json.loads(tx_bytes.decode())
            tx_time = datetime.fromisoformat(tx_data['timestamp'])
            time_diff = (now - tx_time).total_seconds()

            if time_diff <= 60:
                count_per_minute += 1
            if time_diff <= 3600:
                count_per_hour += 1

        max_per_minute = params.get('max_transactions_per_minute', 5)
        max_per_hour = params.get('max_transactions_per_hour', 50)

        if count_per_minute >= max_per_minute:
            return {
                'message': f"Transaction velocity limit exceeded: {count_per_minute} transactions per minute",
                'details': {
                    'current_velocity_per_minute': count_per_minute,
                    'limit_per_minute': max_per_minute,
                    'current_velocity_per_hour': count_per_hour,
                    'limit_per_hour': max_per_hour
                }
            }

        if count_per_hour >= max_per_hour:
            return {
                'message': f"Transaction velocity limit exceeded: {count_per_hour} transactions per hour",
                'details': {
                    'current_velocity_per_hour': count_per_hour,
                    'limit_per_hour': max_per_hour,
                    'current_velocity_per_minute': count_per_minute,
                    'limit_per_minute': max_per_minute
                }
            }

        return None

    async def _evaluate_list_check_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate list-based compliance rule"""
        params = rule.parameters

        if rule.id == "sanctioned_country_check":
            # Check if transaction originates from sanctioned country
            ip_address = transaction_data.get('ip_address')
            sanctioned_countries = params.get('sanctioned_countries', [])

            if ip_address and self.geoip_reader:
                try:
                    response = self.geoip_reader.city(ip_address)
                    country_code = response.country.iso_code

                    if country_code in sanctioned_countries:
                        return {
                            'message': f"Transaction from sanctioned country: {country_code}",
                            'details': {
                                'country_code': country_code,
                                'ip_address': ip_address,
                                'sanctioned': True
                            }
                        }

                except Exception as e:
                    logger.warning(f"GeoIP lookup failed: {e}")

        return None

    async def _evaluate_pattern_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate pattern-based compliance rule"""
        # Simplified pattern evaluation
        # In production, would use more sophisticated pattern matching
        return None

    async def _store_alert(self, alert: ComplianceAlert):
        """Store compliance alert"""
        alert_data = {
            'id': alert.id,
            'user_id': alert.user_id,
            'rule_id': alert.rule_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity.value,
            'title': alert.title,
            'description': alert.description,
            'details': alert.details,
            'timestamp': alert.timestamp.isoformat(),
            'status': alert.status,
            'assigned_to': alert.assigned_to,
            'resolution_notes': alert.resolution_notes
        }

        await self.redis_client.setex(
            f"compliance_alert:{alert.id}",
            86400 * 30,  # 30 days
            json.dumps(alert_data)
        )

        # Add to alerts list
        await self.redis_client.lpush("compliance_alerts", json.dumps(alert_data))
        await self.redis_client.ltrim("compliance_alerts", 0, 9999)  # Keep last 10k alerts

    async def generate_compliance_report(self, report_type: str, start_date: datetime, end_date: datetime) -> ComplianceReport:
        """Generate compliance report"""
        try:
            report_id = str(uuid.uuid4())

            if report_type == "aml_report":
                data = await self._generate_aml_report(start_date, end_date)
                summary = "AML compliance report covering transaction monitoring and suspicious activity reporting"
            elif report_type == "kyc_report":
                data = await self._generate_kyc_report(start_date, end_date)
                summary = "KYC verification report covering customer due diligence"
            elif report_type == "fraud_report":
                data = await self._generate_fraud_report(start_date, end_date)
                summary = "Fraud detection and prevention report"
            elif report_type == "pci_report":
                data = await self._generate_pci_report(start_date, end_date)
                summary = "PCI DSS compliance report for card payment processing"
            else:
                data = {}
                summary = f"General compliance report for period {start_date} to {end_date}"

            report = ComplianceReport(
                id=report_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                data=data,
                summary=summary
            )

            # Store report
            await self._store_compliance_report(report)

            return report

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise

    async def _generate_aml_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate AML compliance report"""
        # Get large transactions
        large_transactions = []
        total_large_amount = 0

        # Get suspicious activities
        suspicious_activities = []
        total_suspicious_amount = 0

        # Calculate metrics
        metrics = {
            'total_transactions': 0,
            'total_amount': 0,
            'large_transactions': len(large_transactions),
            'large_transaction_amount': total_large_amount,
            'suspicious_activities': len(suspicious_activities),
            'suspicious_activity_amount': total_suspicious_amount,
            'files_generated': 0,  # SARs filed
            'alerts_reviewed': 0
        }

        recommendations = [
            "Continue monitoring high-value transactions",
            "Review and update AML monitoring rules",
            "Ensure timely filing of suspicious activity reports"
        ]

        return {
            'metrics': metrics,
            'large_transactions': large_transactions,
            'suspicious_activities': suspicious_activities,
            'recommendations': recommendations
        }

    async def _generate_kyc_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate KYC compliance report"""
        metrics = {
            'total_verifications': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'pending_verifications': 0,
            'average_verification_time': 0,
            'document_types': {}
        }

        recommendations = [
            "Optimize document verification process",
            "Implement automated document extraction",
            "Review verification threshold criteria"
        ]

        return {
            'metrics': metrics,
            'recommendations': recommendations
        }

    async def _generate_fraud_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate fraud detection report"""
        metrics = {
            'total_transactions_screened': 0,
            'fraud_attempts_blocked': 0,
            'false_positives': 0,
            'average_risk_score': 0,
            'high_risk_transactions': 0,
            'fraud_types_detected': {}
        }

        recommendations = [
            "Fine-tune ML models for better accuracy",
            "Update fraud detection rules based on new patterns",
            "Investigate false positive reduction strategies"
        ]

        return {
            'metrics': metrics,
            'recommendations': recommendations
        }

    async def _generate_pci_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate PCI DSS compliance report"""
        metrics = {
            'card_transactions': 0,
            'card_data_breaches': 0,
            'encryption_compliance': 100,
            'access_control_violations': 0,
            'security_incidents': 0
        }

        recommendations = [
            "Maintain PCI DSS training for all staff",
            "Regular security audits and penetration testing",
            "Keep cardholder data on a need-to-know basis"
        ]

        return {
            'metrics': metrics,
            'recommendations': recommendations
        }

    async def _store_compliance_report(self, report: ComplianceReport):
        """Store compliance report"""
        report_data = {
            'id': report.id,
            'report_type': report.report_type,
            'period_start': report.period_start.isoformat(),
            'period_end': report.period_end.isoformat(),
            'generated_at': report.generated_at.isoformat(),
            'data': report.data,
            'summary': report.summary,
            'recommendations': report.recommendations
        }

        await self.redis_client.setex(
            f"compliance_report:{report.id}",
            86400 * 365,  # 1 year
            json.dumps(report_data)
        )

        # Add to reports list
        await self.redis_client.lpush("compliance_reports", json.dumps(report_data))
        await self.redis_client.ltrim("compliance_reports", 0, 999)  # Keep last 1000 reports

    async def _transaction_monitor(self):
        """Background task to monitor transactions for compliance"""
        while True:
            try:
                logger.info("Running transaction compliance monitor...")

                # Get recent transactions for compliance checking
                # This would integrate with transaction processing system
                # Simplified implementation

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in transaction monitor: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error

    async def _fraud_detection_engine(self):
        """Background task for fraud detection"""
        while True:
            try:
                logger.info("Running fraud detection engine...")

                # Process pending fraud detection tasks
                # This would analyze patterns and update ML models
                # Simplified implementation

                await asyncio.sleep(300)  # Run every 5 minutes

            except Exception as e:
                logger.error(f"Error in fraud detection engine: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _compliance_reporter(self):
        """Background task to generate compliance reports"""
        while True:
            try:
                logger.info("Generating compliance reports...")

                # Generate daily compliance reports
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=1)

                report_types = ["aml_report", "fraud_report"]
                for report_type in report_types:
                    try:
                        await self.generate_compliance_report(report_type, start_date, end_date)
                    except Exception as e:
                        logger.error(f"Error generating {report_type}: {e}")

                await asyncio.sleep(86400)  # Run daily

            except Exception as e:
                logger.error(f"Error in compliance reporter: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _list_updater(self):
        """Background task to update external blacklists and watchlists"""
        while True:
            try:
                logger.info("Updating external compliance lists...")

                # Update external lists
                await self._load_external_lists()

                await asyncio.sleep(86400)  # Update daily

            except Exception as e:
                logger.error(f"Error updating external lists: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

# Database models
class ComplianceAlertDB(Base):
    """Compliance alert database model"""
    __tablename__ = 'compliance_alerts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    rule_id = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='open')
    assigned_to = Column(String)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KYCDocumentDB(Base):
    """KYC document database model"""
    __tablename__ = 'kyc_documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    extraction_data = Column(JSON)
    verification_status = Column(String, nullable=False)
    verification_score = Column(Float, nullable=False)
    expiry_date = Column(DateTime)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    verified_by = Column(String)

class TransactionRiskDB(Base):
    """Transaction risk assessment database model"""
    __tablename__ = 'transaction_risks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String, nullable=False, unique=True)
    user_id = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_factors = Column(JSON)
    recommended_action = Column(String, nullable=False)
    assessment_details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_compliance',
            'geoip_database_path': 'GeoLite2-City.mmdb'
        }

        compliance = ComplianceManager(config)
        await compliance.initialize()

        # Assess transaction risk
        transaction_data = {
            'transaction_id': str(uuid.uuid4()),
            'user_id': 'user_123',
            'amount': 1500.00,
            'currency': 'USD',
            'ip_address': '192.168.1.100',
            'device_fingerprint': 'device_fp_123',
            'card_last4': '1234'
        }

        risk_assessment = await compliance.assess_transaction_risk(transaction_data)
        print(f"Risk assessment: {risk_assessment.risk_score} - {risk_assessment.recommended_action}")

        # Process KYC verification
        kyc_data = {
            'document_type': 'passport',
            'document_url': 'https://example.com/passport.jpg'
        }

        kyc_result = await compliance.process_kyc_verification('user_123', kyc_data)
        print(f"KYC verification: {kyc_result}")

        # Generate compliance report
        report = await compliance.generate_compliance_report(
            'aml_report',
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow()
        )
        print(f"Generated report: {report.id}")

    asyncio.run(main())