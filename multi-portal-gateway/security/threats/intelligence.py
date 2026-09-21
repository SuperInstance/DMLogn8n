#!/usr/bin/env python3
"""
DMLogn8n Threat Intelligence System
Integration with threat intelligence feeds and reputation services
"""

import json
import logging
import asyncio
import time
import hashlib
import aiohttp
import aiofiles
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis
import yaml
import ipaddress
import geoip2.database
import re

logger = logging.getLogger(__name__)

class ThreatFeedType(Enum):
    MALWARE_DOMAINS = "malware_domains"
    PHISHING_URLS = "phishing_urls"
    MALICIOUS_IPS = "malicious_ips"
    BOTNET_C2 = "botnet_c2"
    TOR_EXIT_NODES = "tor_exit_nodes"
    KNOWN_ATTACKERS = "known_attackers"
    VULNERABILITIES = "vulnerabilities"
    EXPLOIT_KITS = "exploit_kits"

class ReputationLevel(Enum):
    UNKNOWN = 0
    BENIGN = 1
    SUSPICIOUS = 2
    MALICIOUS = 3
    CRITICAL = 4

class ThreatConfidence(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ThreatIndicator:
    indicator_id: str
    indicator_type: str  # ip, domain, url, hash, email, etc.
    value: str
    threat_types: List[str]
    reputation_level: ReputationLevel
    confidence: ThreatConfidence
    source_feed: str
    first_seen: datetime
    last_seen: datetime
    description: str
    tags: List[str] = None
    context: Dict[str, Any] = None
    expires_at: Optional[datetime] = None

@dataclass
class ThreatFeed:
    feed_id: str
    name: str
    feed_type: ThreatFeedType
    url: str
    format: str  # json, xml, csv, text
    update_interval_minutes: int
    enabled: bool = True
    api_key: Optional[str] = None
    headers: Dict[str, str] = None
    last_updated: Optional[datetime] = None
    error_count: int = 0
    status: str = "active"

@dataclass
class ThreatIntelligenceReport:
    report_id: str
    timestamp: datetime
    source_ip: str
    indicators: List[ThreatIndicator]
    risk_score: float
    recommendations: List[str]
    false_positive_risk: float
    investigation_priority: str

class ThreatIntelligence:
    """
    Threat intelligence integration and analysis system
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.geoip_reader = None
        self.threat_feeds = {}
        self.indicators = {}
        self.reputation_cache = {}
        self.active_feeds = set()
        self.feed_errors = defaultdict(list)

        # Configuration
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 1)
        self.max_indicators_per_type = self.config.get('max_indicators_per_type', 100000)
        self.confidence_threshold = self.config.get('confidence_threshold', ThreatConfidence.MEDIUM)
        self.enable_geo_intelligence = self.config.get('enable_geo_intelligence', True)
        self.enable_reputation_scoring = self.config.get('enable_reputation_scoring', True)

        # Initialize default feeds
        self._initialize_default_feeds()

    async def initialize(self):
        """Initialize threat intelligence components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=8,  # Threat intelligence specific DB
                decode_responses=True
            )

            # Initialize GeoIP
            if self.enable_geo_intelligence:
                try:
                    self.geoip_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
                except Exception as e:
                    logger.warning(f"GeoIP database not available: {e}")

            # Load threat feeds
            await self._load_threat_feeds()

            # Load cached indicators
            await self._load_cached_indicators()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("Threat Intelligence System initialized")

        except Exception as e:
            logger.error(f"Threat Intelligence System initialization failed: {e}")
            raise

    async def initialize_feeds(self):
        """Initialize all threat intelligence feeds"""
        try:
            for feed_id, feed in self.threat_feeds.items():
                if feed.enabled:
                    await self._update_threat_feed(feed_id)
                    self.active_feeds.add(feed_id)

            logger.info(f"Initialized {len(self.active_feeds)} threat intelligence feeds")

        except Exception as e:
            logger.error(f"Threat feeds initialization error: {e}")

    async def check_request(self, request) -> List[ThreatIndicator]:
        """
        Check HTTP request against threat intelligence
        """
        indicators = []

        try:
            # Extract indicators from request
            request_indicators = await self._extract_request_indicators(request)

            # Check each indicator
            for indicator_type, value in request_indicators.items():
                threat_indicator = await self._check_indicator(indicator_type, value)
                if threat_indicator:
                    indicators.append(threat_indicator)

            # Add geo-intelligence if enabled
            if self.enable_geo_intelligence:
                geo_indicators = await self._get_geo_intelligence(request)
                indicators.extend(geo_indicators)

            return indicators

        except Exception as e:
            logger.error(f"Request threat intelligence check error: {e}")
            return []

    async def check_ip_reputation(self, ip_address: str) -> Tuple[ReputationLevel, float, List[str]]:
        """
        Check IP address reputation
        """
        try:
            # Check cache first
            cache_key = f"ip_reputation:{ip_address}"
            if self.redis_client:
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    result = json.loads(cached_result)
                    return (
                        ReputationLevel(result['reputation']),
                        result['risk_score'],
                        result['threat_types']
                    )

            # Initialize reputation
            reputation = ReputationLevel.UNKNOWN
            risk_score = 0.0
            threat_types = []

            # Check against malicious IP indicators
            malicious_indicator = await self._check_indicator('ip', ip_address)
            if malicious_indicator:
                reputation = max(reputation, ReputationLevel.MALICIOUS)
                risk_score += malicious_indicator.confidence.value * 0.25
                threat_types.extend(malicious_indicator.threat_types)

            # Check against Tor exit nodes
            if await self._is_tor_exit_node(ip_address):
                reputation = max(reputation, ReputationLevel.SUSPICIOUS)
                risk_score += 0.3
                threat_types.append('tor_exit_node')

            # Check geo-intelligence
            if self.enable_geo_intelligence and self.geoip_reader:
                geo_risk = await self._calculate_geo_risk(ip_address)
                risk_score += geo_risk
                if geo_risk > 0.5:
                    reputation = max(reputation, ReputationLevel.SUSPICIOUS)

            # Check historical reputation
            historical_risk = await self._get_historical_risk(ip_address)
            risk_score += historical_risk * 0.2

            # Cap risk score
            risk_score = min(1.0, risk_score)

            # Determine final reputation
            if risk_score >= 0.8:
                reputation = ReputationLevel.CRITICAL
            elif risk_score >= 0.6:
                reputation = ReputationLevel.MALICIOUS
            elif risk_score >= 0.4:
                reputation = ReputationLevel.SUSPICIOUS
            elif risk_score >= 0.2:
                reputation = ReputationLevel.BENIGN

            # Cache result
            if self.redis_client:
                result_data = {
                    'reputation': reputation.value,
                    'risk_score': risk_score,
                    'threat_types': threat_types,
                    'timestamp': datetime.now().isoformat()
                }
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl_hours * 3600,
                    json.dumps(result_data)
                )

            return reputation, risk_score, threat_types

        except Exception as e:
            logger.error(f"IP reputation check error: {e}")
            return ReputationLevel.UNKNOWN, 0.0, []

    async def check_domain_reputation(self, domain: str) -> Tuple[ReputationLevel, float, List[str]]:
        """
        Check domain reputation
        """
        try:
            # Check cache first
            cache_key = f"domain_reputation:{domain}"
            if self.redis_client:
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    result = json.loads(cached_result)
                    return (
                        ReputationLevel(result['reputation']),
                        result['risk_score'],
                        result['threat_types']
                    )

            # Initialize reputation
            reputation = ReputationLevel.UNKNOWN
            risk_score = 0.0
            threat_types = []

            # Check against domain indicators
            domain_indicator = await self._check_indicator('domain', domain)
            if domain_indicator:
                reputation = max(reputation, ReputationLevel.MALICIOUS)
                risk_score += domain_indicator.confidence.value * 0.25
                threat_types.extend(domain_indicator.threat_types)

            # Check domain characteristics
            domain_risk = await self._calculate_domain_risk(domain)
            risk_score += domain_risk

            # Check WHOIS data (placeholder)
            whois_risk = await self._calculate_whois_risk(domain)
            risk_score += whois_risk * 0.1

            # Cap risk score
            risk_score = min(1.0, risk_score)

            # Determine final reputation
            if risk_score >= 0.8:
                reputation = ReputationLevel.CRITICAL
            elif risk_score >= 0.6:
                reputation = ReputationLevel.MALICIOUS
            elif risk_score >= 0.4:
                reputation = ReputationLevel.SUSPICIOUS
            elif risk_score >= 0.2:
                reputation = ReputationLevel.BENIGN

            # Cache result
            if self.redis_client:
                result_data = {
                    'reputation': reputation.value,
                    'risk_score': risk_score,
                    'threat_types': threat_types,
                    'timestamp': datetime.now().isoformat()
                }
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl_hours * 3600,
                    json.dumps(result_data)
                )

            return reputation, risk_score, threat_types

        except Exception as e:
            logger.error(f"Domain reputation check error: {e}")
            return ReputationLevel.UNKNOWN, 0.0, []

    async def generate_intelligence_report(self, request, indicators: List[ThreatIndicator]) -> ThreatIntelligenceReport:
        """
        Generate comprehensive threat intelligence report
        """
        try:
            report_id = str(uuid.uuid4())
            source_ip = self._get_client_ip(request)

            # Calculate overall risk score
            risk_score = self._calculate_overall_risk(indicators)

            # Generate recommendations
            recommendations = self._generate_recommendations(indicators, risk_score)

            # Calculate false positive risk
            false_positive_risk = self._calculate_false_positive_risk(indicators)

            # Determine investigation priority
            investigation_priority = self._determine_investigation_priority(risk_score, indicators)

            report = ThreatIntelligenceReport(
                report_id=report_id,
                timestamp=datetime.now(),
                source_ip=source_ip,
                indicators=indicators,
                risk_score=risk_score,
                recommendations=recommendations,
                false_positive_risk=false_positive_risk,
                investigation_priority=investigation_priority
            )

            # Store report
            if self.redis_client:
                await self.redis_client.setex(
                    f"intel_report:{report_id}",
                    86400 * 7,  # 7 days
                    json.dumps(asdict(report))
                )

            return report

        except Exception as e:
            logger.error(f"Intelligence report generation error: {e}")
            raise

    async def get_feed_status(self) -> Dict[str, Any]:
        """Get status of all threat intelligence feeds"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'total_feeds': len(self.threat_feeds),
                'active_feeds': len(self.active_feeds),
                'total_indicators': len(self.indicators),
                'feeds': {}
            }

            for feed_id, feed in self.threat_feeds.items():
                status['feeds'][feed_id] = {
                    'name': feed.name,
                    'type': feed.feed_type.value,
                    'status': feed.status,
                    'enabled': feed.enabled,
                    'last_updated': feed.last_updated.isoformat() if feed.last_updated else None,
                    'error_count': feed.error_count,
                    'errors': self.feed_errors.get(feed_id, [])[-5:]  # Last 5 errors
                }

            return status

        except Exception as e:
            logger.error(f"Feed status retrieval error: {e}")
            return {'error': str(e)}

    # Private methods
    async def _extract_request_indicators(self, request) -> Dict[str, str]:
        """Extract threat indicators from HTTP request"""
        indicators = {}

        try:
            # Client IP
            client_ip = self._get_client_ip(request)
            indicators['ip'] = client_ip

            # User Agent
            user_agent = request.headers.get('user-agent', '')
            if user_agent:
                indicators['user_agent'] = user_agent

            # Referer
            referer = request.headers.get('referer', '')
            if referer:
                try:
                    from urllib.parse import urlparse
                    parsed_referer = urlparse(referer)
                    if parsed_referer.netloc:
                        indicators['domain'] = parsed_referer.netloc
                except:
                    pass

            # Host header
            host = request.headers.get('host', '')
            if host:
                indicators['domain'] = host

            # Query parameters
            if request.query_params:
                for param, value in request.query_params.items():
                    if self._looks_like_ip(value):
                        indicators['ip'] = value
                    elif self._looks_like_domain(value):
                        indicators['domain'] = value
                    elif self._looks_like_url(value):
                        indicators['url'] = value

            # Check for file hashes in path
            path = request.url.path
            hash_pattern = r'[a-fA-F0-9]{32,64}'
            matches = re.findall(hash_pattern, path)
            if matches:
                indicators['hash'] = matches[0]

        except Exception as e:
            logger.error(f"Request indicator extraction error: {e}")

        return indicators

    async def _check_indicator(self, indicator_type: str, value: str) -> Optional[ThreatIndicator]:
        """Check specific indicator against threat intelligence"""
        try:
            # Check cache first
            cache_key = f"indicator:{indicator_type}:{hashlib.md5(value.encode()).hexdigest()}"
            if self.redis_client:
                cached_indicator = await self.redis_client.get(cache_key)
                if cached_indicator:
                    indicator_data = json.loads(cached_indicator)
                    return ThreatIndicator(**indicator_data)

            # Check against loaded indicators
            for indicator in self.indicators.values():
                if (indicator.indicator_type == indicator_type and
                    indicator.value.lower() == value.lower()):
                    return indicator

            # Check against specific feed types
            if indicator_type == 'ip':
                return await self._check_ip_feeds(value)
            elif indicator_type == 'domain':
                return await self._check_domain_feeds(value)
            elif indicator_type == 'url':
                return await self._check_url_feeds(value)
            elif indicator_type == 'hash':
                return await self._check_hash_feeds(value)

            return None

        except Exception as e:
            logger.error(f"Indicator check error: {e}")
            return None

    async def _check_ip_feeds(self, ip_address: str) -> Optional[ThreatIndicator]:
        """Check IP against malicious IP feeds"""
        try:
            # Check against known malicious IPs
            if self.redis_client:
                # Check malicious IPs set
                is_malicious = await self.redis_client.sismember("malicious_ips", ip_address)
                if is_malicious:
                    return ThreatIndicator(
                        indicator_id=f"malicious_ip_{hashlib.md5(ip_address.encode()).hexdigest()[:8]}",
                        indicator_type="ip",
                        value=ip_address,
                        threat_types=["malicious_ip"],
                        reputation_level=ReputationLevel.MALICIOUS,
                        confidence=ThreatConfidence.HIGH,
                        source_feed="internal_malicious_ips",
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        description="IP address found in malicious IP list"
                    )

            return None

        except Exception as e:
            logger.error(f"IP feed check error: {e}")
            return None

    async def _check_domain_feeds(self, domain: str) -> Optional[ThreatIndicator]:
        """Check domain against malicious domain feeds"""
        try:
            # Check against known malicious domains
            if self.redis_client:
                # Check malicious domains set
                is_malicious = await self.redis_client.sismember("malicious_domains", domain)
                if is_malicious:
                    return ThreatIndicator(
                        indicator_id=f"malicious_domain_{hashlib.md5(domain.encode()).hexdigest()[:8]}",
                        indicator_type="domain",
                        value=domain,
                        threat_types=["malicious_domain"],
                        reputation_level=ReputationLevel.MALICIOUS,
                        confidence=ThreatConfidence.HIGH,
                        source_feed="internal_malicious_domains",
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        description="Domain found in malicious domain list"
                    )

            return None

        except Exception as e:
            logger.error(f"Domain feed check error: {e}")
            return None

    async def _check_url_feeds(self, url: str) -> Optional[ThreatIndicator]:
        """Check URL against malicious URL feeds"""
        try:
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Check domain reputation
            reputation, risk_score, threat_types = await self.check_domain_reputation(domain)
            if reputation in [ReputationLevel.MALICIOUS, ReputationLevel.CRITICAL]:
                return ThreatIndicator(
                    indicator_id=f"malicious_url_{hashlib.md5(url.encode()).hexdigest()[:8]}",
                    indicator_type="url",
                    value=url,
                    threat_types=threat_types,
                    reputation_level=reputation,
                    confidence=ThreatConfidence.MEDIUM,
                    source_feed="url_analysis",
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    description=f"URL with malicious domain: {domain}",
                    context={'risk_score': risk_score}
                )

            return None

        except Exception as e:
            logger.error(f"URL feed check error: {e}")
            return None

    async def _check_hash_feeds(self, file_hash: str) -> Optional[ThreatIndicator]:
        """Check file hash against malware feeds"""
        try:
            # Check against known malware hashes
            if self.redis_client:
                # Check malware hashes set
                is_malicious = await self.redis_client.sismember("malware_hashes", file_hash)
                if is_malicious:
                    return ThreatIndicator(
                        indicator_id=f"malware_hash_{hashlib.md5(file_hash.encode()).hexdigest()[:8]}",
                        indicator_type="hash",
                        value=file_hash,
                        threat_types=["malware"],
                        reputation_level=ReputationLevel.CRITICAL,
                        confidence=ThreatConfidence.CRITICAL,
                        source_feed="malware_hashes",
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        description="File hash found in malware database"
                    )

            return None

        except Exception as e:
            logger.error(f"Hash feed check error: {e}")
            return None

    async def _get_geo_intelligence(self, request) -> List[ThreatIndicator]:
        """Get geo-location based threat intelligence"""
        indicators = []

        try:
            if not self.geoip_reader:
                return indicators

            client_ip = self._get_client_ip(request)

            # Skip private IPs
            try:
                ip_obj = ipaddress.ip_address(client_ip)
                if ip_obj.is_private:
                    return indicators
            except:
                pass

            # Get country information
            response = self.geoip_reader.country(client_ip)
            country = response.country.iso_code

            # Check high-risk countries
            high_risk_countries = self.config.get('high_risk_countries', [])
            if country in high_risk_countries:
                indicator = ThreatIndicator(
                    indicator_id=f"geo_risk_{country}_{hashlib.md5(client_ip.encode()).hexdigest()[:8]}",
                    indicator_type="geo_location",
                    value=client_ip,
                    threat_types=["high_risk_location"],
                    reputation_level=ReputationLevel.SUSPICIOUS,
                    confidence=ThreatConfidence.LOW,
                    source_feed="geo_intelligence",
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    description=f"IP from high-risk country: {country}",
                    context={'country': country}
                )
                indicators.append(indicator)

        except Exception as e:
            logger.error(f"Geo intelligence error: {e}")

        return indicators

    async def _is_tor_exit_node(self, ip_address: str) -> bool:
        """Check if IP is a Tor exit node"""
        try:
            if self.redis_client:
                return await self.redis_client.sismember("tor_exit_nodes", ip_address)
            return False

        except Exception as e:
            logger.error(f"Tor exit node check error: {e}")
            return False

    async def _calculate_geo_risk(self, ip_address: str) -> float:
        """Calculate geographic risk score for IP"""
        try:
            if not self.geoip_reader:
                return 0.0

            response = self.geoip_reader.country(ip_address)
            country = response.country.iso_code

            # Risk scoring based on country
            high_risk_countries = self.config.get('high_risk_countries', ['CN', 'RU', 'KP', 'IR'])
            medium_risk_countries = self.config.get('medium_risk_countries', ['BR', 'IN', 'ID', 'PK'])

            if country in high_risk_countries:
                return 0.6
            elif country in medium_risk_countries:
                return 0.3
            else:
                return 0.1

        except Exception as e:
            logger.error(f"Geo risk calculation error: {e}")
            return 0.0

    async def _calculate_domain_risk(self, domain: str) -> float:
        """Calculate domain risk score"""
        try:
            risk_score = 0.0

            # Check domain age (placeholder)
            domain_age = await self._get_domain_age(domain)
            if domain_age and domain_age < 30:  # Less than 30 days old
                risk_score += 0.3

            # Check domain length
            if len(domain) > 50:
                risk_score += 0.2

            # Check for suspicious patterns
            suspicious_patterns = [
                r'[0-9]{5,}',  # Lots of numbers
                r'[a-z]{20,}',  # Long strings
                r'-.{1,2}\.',  # Short subdomains
                r'\.tk$|\.ml$|\.ga$',  # Suspicious TLDs
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, domain, re.IGNORECASE):
                    risk_score += 0.1

            return min(1.0, risk_score)

        except Exception as e:
            logger.error(f"Domain risk calculation error: {e}")
            return 0.0

    async def _get_domain_age(self, domain: str) -> Optional[int]:
        """Get domain age in days"""
        # Placeholder for WHOIS lookup
        return None

    async def _calculate_whois_risk(self, domain: str) -> float:
        """Calculate WHOIS-based risk score"""
        # Placeholder for WHOIS analysis
        return 0.0

    async def _get_historical_risk(self, ip_address: str) -> float:
        """Get historical risk score for IP"""
        try:
            if self.redis_client:
                historical_threats = await self.redis_client.lrange(f"ip_threats:{ip_address}", 0, -1)
                return min(1.0, len(historical_threats) * 0.1)
            return 0.0

        except Exception as e:
            logger.error(f"Historical risk calculation error: {e}")
            return 0.0

    def _calculate_overall_risk(self, indicators: List[ThreatIndicator]) -> float:
        """Calculate overall risk score from indicators"""
        if not indicators:
            return 0.0

        total_risk = 0.0
        for indicator in indicators:
            # Weight risk by confidence and reputation
            indicator_risk = (indicator.confidence.value / 4.0) * (indicator.reputation_level.value / 4.0)
            total_risk += indicator_risk

        # Normalize by number of indicators
        return min(1.0, total_risk / len(indicators))

    def _generate_recommendations(self, indicators: List[ThreatIndicator], risk_score: float) -> List[str]:
        """Generate security recommendations based on indicators"""
        recommendations = []

        if risk_score >= 0.8:
            recommendations.append("CRITICAL: Block source IP immediately")
            recommendations.append("Enable additional authentication requirements")
            recommendations.append("Escalate to security team for immediate investigation")

        elif risk_score >= 0.6:
            recommendations.append("Block source IP temporarily")
            recommendations.append("Increase monitoring and logging")
            recommendations.append("Review related sessions and activities")

        elif risk_score >= 0.4:
            recommendations.append("Apply rate limiting to source IP")
            recommendations.append("Require additional verification")
            recommendations.append("Monitor for suspicious behavior")

        # Indicator-specific recommendations
        threat_types = set()
        for indicator in indicators:
            threat_types.update(indicator.threat_types)

        if 'malware' in threat_types:
            recommendations.append("Scan for malware infection")
            recommendations.append("Isolate affected systems")

        if 'phishing' in threat_types:
            recommendations.append("Check for credential compromise")
            recommendations.append("Review authentication logs")

        if 'botnet' in threat_types or 'tor_exit_node' in threat_types:
            recommendations.append("Block anonymous/proxy traffic")
            recommendations.append("Require strong authentication")

        if not recommendations:
            recommendations.append("Continue monitoring")

        return recommendations

    def _calculate_false_positive_risk(self, indicators: List[ThreatIndicator]) -> float:
        """Calculate false positive risk"""
        if not indicators:
            return 0.0

        # Higher confidence indicators have lower false positive risk
        avg_confidence = sum(ind.confidence.value for ind in indicators) / len(indicators)
        false_positive_risk = (4.0 - avg_confidence) / 4.0

        # Adjust based on source reliability
        reliable_sources = ['internal_malicious_ips', 'internal_malicious_domains', 'malware_hashes']
        for indicator in indicators:
            if indicator.source_feed in reliable_sources:
                false_positive_risk *= 0.5

        return min(1.0, false_positive_risk)

    def _determine_investigation_priority(self, risk_score: float, indicators: List[ThreatIndicator]) -> str:
        """Determine investigation priority"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _looks_like_ip(self, value: str) -> bool:
        """Check if value looks like an IP address"""
        try:
            ipaddress.ip_address(value)
            return True
        except:
            return False

    def _looks_like_domain(self, value: str) -> bool:
        """Check if value looks like a domain name"""
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, value))

    def _looks_like_url(self, value: str) -> bool:
        """Check if value looks like a URL"""
        return value.startswith(('http://', 'https://'))

    async def _update_threat_feed(self, feed_id: str):
        """Update specific threat intelligence feed"""
        try:
            if feed_id not in self.threat_feeds:
                logger.error(f"Unknown feed: {feed_id}")
                return

            feed = self.threat_feeds[feed_id]

            if not feed.enabled:
                return

            logger.info(f"Updating threat feed: {feed.name}")

            # Download feed data
            headers = feed.headers or {}
            if feed.api_key:
                headers['Authorization'] = f'Bearer {feed.api_key}'

            async with aiohttp.ClientSession() as session:
                async with session.get(feed.url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        await self._process_feed_data(feed, content)
                        feed.last_updated = datetime.now()
                        feed.error_count = 0
                        feed.status = "active"
                    else:
                        feed.error_count += 1
                        feed.status = "error"
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        self.feed_errors[feed_id].append({
                            'timestamp': datetime.now().isoformat(),
                            'error': error_msg
                        })
                        logger.error(f"Feed update error for {feed.name}: {error_msg}")

        except Exception as e:
            logger.error(f"Threat feed update error for {feed_id}: {e}")
            if feed_id in self.threat_feeds:
                self.threat_feeds[feed_id].error_count += 1
                self.threat_feeds[feed_id].status = "error"
                self.feed_errors[feed_id].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })

    async def _process_feed_data(self, feed: ThreatFeed, content: str):
        """Process feed data and extract indicators"""
        try:
            indicators = []

            if feed.format == 'json':
                data = json.loads(content)
                indicators = await self._parse_json_feed(feed, data)
            elif feed.format == 'csv':
                indicators = await self._parse_csv_feed(feed, content)
            elif feed.format == 'text':
                indicators = await self._parse_text_feed(feed, content)
            else:
                logger.warning(f"Unsupported feed format: {feed.format}")

            # Store indicators
            for indicator in indicators:
                indicator_id = f"{feed.feed_id}_{hashlib.md5(indicator['value'].encode()).hexdigest()[:8]}"
                threat_indicator = ThreatIndicator(
                    indicator_id=indicator_id,
                    indicator_type=indicator['type'],
                    value=indicator['value'],
                    threat_types=indicator.get('threat_types', ['unknown']),
                    reputation_level=ReputationLevel(indicator.get('reputation', 2)),
                    confidence=ThreatConfidence(indicator.get('confidence', 2)),
                    source_feed=feed.feed_id,
                    first_seen=datetime.fromisoformat(indicator.get('first_seen', datetime.now().isoformat())),
                    last_seen=datetime.fromisoformat(indicator.get('last_seen', datetime.now().isoformat())),
                    description=indicator.get('description', ''),
                    tags=indicator.get('tags', []),
                    context=indicator.get('context', {})
                )
                self.indicators[indicator_id] = threat_indicator

                # Store in Redis
                if self.redis_client:
                    cache_key = f"indicator:{threat_indicator.indicator_type}:{hashlib.md5(threat_indicator.value.encode()).hexdigest()}"
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl_hours * 3600,
                        json.dumps(asdict(threat_indicator))
                    )

                    # Add to appropriate sets for quick lookup
                    if threat_indicator.indicator_type == 'ip':
                        await self.redis_client.sadd("malicious_ips", threat_indicator.value)
                    elif threat_indicator.indicator_type == 'domain':
                        await self.redis_client.sadd("malicious_domains", threat_indicator.value)
                    elif threat_indicator.indicator_type == 'hash':
                        await self.redis_client.sadd("malware_hashes", threat_indicator.value)

            logger.info(f"Processed {len(indicators)} indicators from {feed.name}")

        except Exception as e:
            logger.error(f"Feed data processing error: {e}")

    async def _parse_json_feed(self, feed: ThreatFeed, data: Dict) -> List[Dict]:
        """Parse JSON format feed data"""
        indicators = []

        # This is a placeholder implementation
        # Actual implementation depends on feed format
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    indicators.append(item)
        elif isinstance(data, dict) and 'indicators' in data:
            indicators = data['indicators']

        return indicators

    async def _parse_csv_feed(self, feed: ThreatFeed, content: str) -> List[Dict]:
        """Parse CSV format feed data"""
        indicators = []

        # Simple CSV parsing (placeholder)
        lines = content.strip().split('\n')
        for line in lines[1:]:  # Skip header
            parts = line.split(',')
            if len(parts) >= 2:
                indicators.append({
                    'type': feed.feed_type.value.split('_')[0],  # Extract type from feed type
                    'value': parts[0].strip(),
                    'description': parts[1].strip() if len(parts) > 1 else '',
                    'threat_types': [feed.feed_type.value]
                })

        return indicators

    async def _parse_text_feed(self, feed: ThreatFeed, content: str) -> List[Dict]:
        """Parse text format feed data"""
        indicators = []

        # Simple text parsing (one indicator per line)
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip comments
                indicators.append({
                    'type': feed.feed_type.value.split('_')[0],
                    'value': line,
                    'description': f'From {feed.name}',
                    'threat_types': [feed.feed_type.value]
                })

        return indicators

    def _initialize_default_feeds(self):
        """Initialize default threat intelligence feeds"""
        # Placeholder feeds - in production, configure real feeds
        default_feeds = [
            ThreatFeed(
                feed_id="tor_exit_nodes",
                name="Tor Exit Nodes",
                feed_type=ThreatFeedType.TOR_EXIT_NODES,
                url="https://check.torproject.org/exit-addresses",
                format="text",
                update_interval_minutes=60
            ),
            ThreatFeed(
                feed_id="malware_domains",
                name="Malicious Domains",
                feed_type=ThreatFeedType.MALWARE_DOMAINS,
                url="https://example.com/malware_domains.txt",
                format="text",
                update_interval_minutes=120
            ),
            ThreatFeed(
                feed_id="phishing_urls",
                name="Phishing URLs",
                feed_type=ThreatFeedType.PHISHING_URLS,
                url="https://example.com/phishing_urls.json",
                format="json",
                update_interval_minutes=60
            )
        ]

        for feed in default_feeds:
            self.threat_feeds[feed.feed_id] = feed

    async def _load_threat_feeds(self):
        """Load threat feeds from configuration"""
        try:
            feeds_config = self.config.get('threat_feeds', {})
            for feed_id, feed_config in feeds_config.items():
                feed = ThreatFeed(
                    feed_id=feed_id,
                    name=feed_config.get('name', ''),
                    feed_type=ThreatFeedType(feed_config.get('feed_type', 'malicious_ips')),
                    url=feed_config.get('url', ''),
                    format=feed_config.get('format', 'text'),
                    update_interval_minutes=feed_config.get('update_interval_minutes', 60),
                    enabled=feed_config.get('enabled', True),
                    api_key=feed_config.get('api_key'),
                    headers=feed_config.get('headers', {})
                )
                self.threat_feeds[feed_id] = feed

            logger.info(f"Loaded {len(self.threat_feeds)} threat feeds")

        except Exception as e:
            logger.error(f"Threat feeds loading error: {e}")

    async def _load_cached_indicators(self):
        """Load indicators from cache"""
        try:
            if not self.redis_client:
                return

            # Load indicators from Redis
            indicator_keys = await self.redis_client.keys("indicator:*")
            for key in indicator_keys:
                indicator_data = await self.redis_client.get(key)
                if indicator_data:
                    indicator_dict = json.loads(indicator_data)
                    indicator = ThreatIndicator(**indicator_dict)
                    self.indicators[indicator.indicator_id] = indicator

            logger.info(f"Loaded {len(self.indicators)} cached indicators")

        except Exception as e:
            logger.error(f"Cached indicators loading error: {e}")

    async def _start_background_tasks(self):
        """Start background tasks for threat intelligence"""
        try:
            # Periodic feed updates
            asyncio.create_task(self._periodic_feed_updates())

            # Cache cleanup
            asyncio.create_task(self._periodic_cache_cleanup())

            # Statistics collection
            asyncio.create_task(self._periodic_statistics_collection())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _periodic_feed_updates(self):
        """Periodically update threat intelligence feeds"""
        while True:
            try:
                for feed_id, feed in self.threat_feeds.items():
                    if feed.enabled:
                        await self._update_threat_feed(feed_id)
                        await asyncio.sleep(60)  # Small delay between feeds

                # Wait before next update cycle
                min_interval = min(
                    (feed.update_interval_minutes for feed in self.threat_feeds.values() if feed.enabled),
                    default=60
                )
                await asyncio.sleep(min_interval * 60)

            except Exception as e:
                logger.error(f"Periodic feed update error: {e}")
                await asyncio.sleep(300)  # 5 minutes on error

    async def _periodic_cache_cleanup(self):
        """Clean up expired cached data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                if self.redis_client:
                    # Clean up expired indicators
                    current_time = datetime.now()
                    expired_keys = []

                    for indicator_id, indicator in self.indicators.items():
                        if indicator.expires_at and current_time >= indicator.expires_at:
                            expired_keys.append(indicator_id)
                            # Remove from Redis
                            cache_key = f"indicator:{indicator.indicator_type}:{hashlib.md5(indicator.value.encode()).hexdigest()}"
                            await self.redis_client.delete(cache_key)

                    # Remove from memory
                    for key in expired_keys:
                        del self.indicators[key]

                    if expired_keys:
                        logger.info(f"Cleaned up {len(expired_keys)} expired indicators")

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)

    async def _periodic_statistics_collection(self):
        """Collect and store threat intelligence statistics"""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Every 6 hours

                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'total_indicators': len(self.indicators),
                    'active_feeds': len(self.active_feeds),
                    'indicator_types': defaultdict(int),
                    'reputation_levels': defaultdict(int)
                }

                for indicator in self.indicators.values():
                    stats['indicator_types'][indicator.indicator_type] += 1
                    stats['reputation_levels'][indicator.reputation_level.name] += 1

                if self.redis_client:
                    await self.redis_client.setex(
                        "threat_intel_stats",
                        86400 * 7,  # 7 days
                        json.dumps(stats)
                    )

            except Exception as e:
                logger.error(f"Statistics collection error: {e}")
                await asyncio.sleep(300)