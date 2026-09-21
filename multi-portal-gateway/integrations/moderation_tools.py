#!/usr/bin/env python3
"""
Moderation Tools Integration
Connects with content moderation and safety services like Perspective API, Content Safety, etc.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import re
from .integration_manager import IntegrationStatus

@dataclass
class ModerationResult:
    content_id: str
    content_type: str  # 'text', 'image', 'video', 'audio'
    provider: str
    toxicity_score: float
    categories: Dict[str, float]
    flags: List[str]
    action_taken: str  # 'approved', 'rejected', 'flagged', 'review_needed'
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ModerationRule:
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    action: str
    enabled: bool
    created_at: datetime

class ModerationToolsIntegration:
    """Integration with content moderation and safety services"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # Moderation service clients
        self.perspective_client = None
        self.content_safety_client = None
        self.sightengine_client = None

        # Moderation rules
        self.rules: Dict[str, ModerationRule] = {}
        self.default_rules = []

        # Moderation history
        self.moderation_history: List[ModerationResult] = []

        # Content filters
        self.text_filters = {
            'profanity': [],
            'spam_patterns': [],
            'personal_info_patterns': [],
            'hate_speech_patterns': []
        }

        # Statistics
        self.stats = {
            'total_content_moderated': 0,
            'content_approved': 0,
            'content_rejected': 0,
            'content_flagged': 0,
            'false_positives': 0,
            'provider_usage': {}
        }

    async def initialize(self):
        """Initialize the moderation tools integration"""
        self.logger.info("Initializing Moderation Tools Integration")

        # Initialize Perspective API
        await self._initialize_perspective_api()

        # Initialize Content Safety
        await self._initialize_content_safety()

        # Initialize SightEngine
        await self._initialize_sightengine()

        # Load default rules
        await self._load_default_rules()

        # Initialize text filters
        await self._initialize_text_filters()

        # Start analytics processing
        asyncio.create_task(self._analytics_processor())

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_perspective_api(self):
        """Initialize Google Perspective API"""
        try:
            api_key = self.config.get('api_keys', {}).get('perspective_api_key')
            if api_key:
                self.perspective_client = {
                    'api_key': api_key,
                    'base_url': 'https://commentanalyzer.googleapis.com/v1alpha1'
                }
                self.logger.info("Perspective API initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Perspective API: {e}")

    async def _initialize_content_safety(self):
        """Initialize Azure Content Safety"""
        try:
            endpoint = self.config.get('api_keys', {}).get('content_safety_endpoint')
            api_key = self.config.get('api_keys', {}).get('content_safety_api_key')
            if endpoint and api_key:
                self.content_safety_client = {
                    'endpoint': endpoint,
                    'api_key': api_key
                }
                self.logger.info("Azure Content Safety initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Content Safety: {e}")

    async def _initialize_sightengine(self):
        """Initialize SightEngine API"""
        try:
            api_user = self.config.get('api_keys', {}).get('sightengine_api_user')
            api_secret = self.config.get('api_keys', {}).get('sightengine_api_secret')
            if api_user and api_secret:
                self.sightengine_client = {
                    'api_user': api_user,
                    'api_secret': api_secret,
                    'base_url': 'https://api.sightengine.com/1.0'
                }
                self.logger.info("SightEngine initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize SightEngine: {e}")

    async def _load_default_rules(self):
        """Load default moderation rules"""
        try:
            # Text moderation rules
            text_rules = [
                ModerationRule(
                    rule_id='high_toxicity',
                    name='High Toxicity Content',
                    description='Reject content with high toxicity scores',
                    conditions={
                        'provider': 'perspective',
                        'toxicity_score': {'gte': 0.8}
                    },
                    action='reject',
                    enabled=True,
                    created_at=datetime.now()
                ),
                ModerationRule(
                    rule_id='medium_toxicity',
                    name='Medium Toxicity Content',
                    description='Flag content with medium toxicity for review',
                    conditions={
                        'provider': 'perspective',
                        'toxicity_score': {'gte': 0.6, 'lt': 0.8}
                    },
                    action='flag',
                    enabled=True,
                    created_at=datetime.now()
                ),
                ModerationRule(
                    rule_id='hate_speech',
                    name='Hate Speech Detection',
                    description='Reject hate speech content',
                    conditions={
                        'provider': 'perspective',
                        'categories': {
                            'IDENTITY_ATTACK': {'gte': 0.7},
                            'THREAT': {'gte': 0.7}
                        }
                    },
                    action='reject',
                    enabled=True,
                    created_at=datetime.now()
                ),
                ModerationRule(
                    rule_id='spam_detection',
                    name='Spam Detection',
                    description='Flag potential spam content',
                    conditions={
                        'local_filters': ['spam_patterns'],
                        'repeated_content': True
                    },
                    action='flag',
                    enabled=True,
                    created_at=datetime.now()
                )
            ]

            for rule in text_rules:
                self.rules[rule.rule_id] = rule
                self.default_rules.append(rule.rule_id)

            self.logger.info(f"Loaded {len(text_rules)} default moderation rules")

        except Exception as e:
            self.logger.error(f"Error loading default rules: {e}")

    async def _initialize_text_filters(self):
        """Initialize text-based content filters"""
        try:
            # Profanity filter (simplified example)
            self.text_filters['profanity'] = [
                r'\b\b',  # Add actual profanity patterns
            ]

            # Spam patterns
            self.text_filters['spam_patterns'] = [
                r'click here',
                r'buy now',
                r'limited time',
                r'act now',
                r'free money',
                r'\b\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}\b',  # Phone numbers
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            ]

            # Personal information patterns
            self.text_filters['personal_info_patterns'] = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',  # Credit card
                r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd)\b',  # Address
            ]

            # Hate speech patterns (basic examples)
            self.text_filters['hate_speech_patterns'] = [
                # Add appropriate hate speech detection patterns
            ]

        except Exception as e:
            self.logger.error(f"Error initializing text filters: {e}")

    async def moderate_content(self, content: str,
                             content_type: str = 'text',
                             content_id: str = None,
                             user_id: str = None,
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Moderate content using all available services"""
        try:
            if not content_id:
                content_id = f"content_{int(datetime.now().timestamp())}"

            results = []

            # Run text moderation
            if content_type == 'text':
                # Local text filters
                local_result = await self._apply_local_filters(content, content_id)
                if local_result:
                    results.append(local_result)

                # Perspective API
                if self.perspective_client:
                    perspective_result = await self._moderate_with_perspective(content, content_id)
                    if perspective_result:
                        results.append(perspective_result)

                # Content Safety
                if self.content_safety_client:
                    safety_result = await self._moderate_with_content_safety(content, content_id)
                    if safety_result:
                        results.append(safety_result)

            # Image moderation
            elif content_type == 'image':
                if self.sightengine_client:
                    sightengine_result = await self._moderate_image_with_sightengine(content, content_id)
                    if sightengine_result:
                        results.append(sightengine_result)

            # Apply moderation rules
            final_action = await self._apply_moderation_rules(results, content_id)

            # Create final result
            final_result = ModerationResult(
                content_id=content_id,
                content_type=content_type,
                provider='combined',
                toxicity_score=max(r.toxicity_score for r in results) if results else 0.0,
                categories=self._combine_categories(results),
                flags=self._combine_flags(results),
                action_taken=final_action,
                confidence=self._calculate_confidence(results),
                timestamp=datetime.now(),
                metadata={
                    'user_id': user_id,
                    'context': context or {},
                    'provider_results': [asdict(r) for r in results]
                }
            )

            # Store in history
            self.moderation_history.append(final_result)

            # Update statistics
            self._update_stats(final_result)

            # Send webhook for moderation actions
            if final_action in ['rejected', 'flagged']:
                await self._send_moderation_webhook(final_result)

            return {
                'success': True,
                'content_id': content_id,
                'action_taken': final_action,
                'toxicity_score': final_result.toxicity_score,
                'flags': final_result.flags,
                'confidence': final_result.confidence,
                'provider_results': results
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _apply_local_filters(self, content: str, content_id: str) -> Optional[ModerationResult]:
        """Apply local text-based filters"""
        try:
            toxicity_score = 0.0
            categories = {}
            flags = []

            content_lower = content.lower()

            # Check for profanity
            profanity_matches = 0
            for pattern in self.text_filters['profanity']:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                profanity_matches += matches
            if profanity_matches > 0:
                toxicity_score += min(profanity_matches * 0.1, 0.3)
                categories['PROFANITY'] = min(profanity_matches * 0.2, 0.6)
                flags.append('profanity_detected')

            # Check for spam patterns
            spam_matches = 0
            for pattern in self.text_filters['spam_patterns']:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                spam_matches += matches
            if spam_matches > 0:
                toxicity_score += min(spam_matches * 0.15, 0.4)
                categories['SPAM'] = min(spam_matches * 0.3, 0.7)
                flags.append('spam_detected')

            # Check for personal information
            personal_info_matches = 0
            for pattern in self.text_filters['personal_info_patterns']:
                matches = len(re.findall(pattern, content))
                personal_info_matches += matches
            if personal_info_matches > 0:
                toxicity_score += min(personal_info_matches * 0.2, 0.5)
                categories['PERSONAL_INFO'] = min(personal_info_matches * 0.4, 0.8)
                flags.append('personal_info_detected')

            if toxicity_score > 0:
                return ModerationResult(
                    content_id=content_id,
                    content_type='text',
                    provider='local_filters',
                    toxicity_score=min(toxicity_score, 1.0),
                    categories=categories,
                    flags=flags,
                    action_taken='pending',
                    confidence=0.7,
                    timestamp=datetime.now(),
                    metadata={'filter_type': 'local_text_filters'}
                )

            return None

        except Exception as e:
            self.logger.error(f"Error applying local filters: {e}")
            return None

    async def _moderate_with_perspective(self, content: str, content_id: str) -> Optional[ModerationResult]:
        """Moderate content using Google Perspective API"""
        try:
            url = f"{self.perspective_client['base_url']}/comments:analyze"
            params = {'key': self.perspective_client['api_key']}

            data = {
                'comment': {'text': content},
                'languages': ['en'],
                'requestedAttributes': {
                    'TOXICITY': {},
                    'SEVERE_TOXICITY': {},
                    'IDENTITY_ATTACK': {},
                    'THREAT': {},
                    'PROFANITY': {},
                    'SEXUALLY_EXPLICIT': {},
                    'FLIRTATION': {}
                },
                'doNotStore': True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        attribute_scores = result['attributeScores']

                        categories = {}
                        for attr_name, attr_data in attribute_scores.items():
                            categories[attr_name] = attr_data['summaryScore']['value']

                        toxicity_score = categories.get('TOXICITY', {}).get('value', 0.0)

                        flags = []
                        if toxicity_score > 0.6:
                            flags.append('high_toxicity')
                        if categories.get('IDENTITY_ATTACK', {}).get('value', 0) > 0.5:
                            flags.append('identity_attack')
                        if categories.get('THREAT', {}).get('value', 0) > 0.5:
                            flags.append('threat')
                        if categories.get('PROFANITY', {}).get('value', 0) > 0.5:
                            flags.append('profanity')

                        return ModerationResult(
                            content_id=content_id,
                            content_type='text',
                            provider='perspective',
                            toxicity_score=toxicity_score,
                            categories=categories,
                            flags=flags,
                            action_taken='pending',
                            confidence=0.8,
                            timestamp=datetime.now(),
                            metadata={'api_version': 'v1alpha1'}
                        )
                    else:
                        self.logger.error(f"Perspective API error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error with Perspective API: {e}")
            return None

    async def _moderate_with_content_safety(self, content: str, content_id: str) -> Optional[ModerationResult]:
        """Moderate content using Azure Content Safety"""
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.content_safety_client['api_key'],
                'Content-Type': 'application/json'
            }

            data = {
                'text': content
            }

            url = f"{self.content_safety_client['endpoint']}/contentsafety/text:analyze"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()

                        categories = {}
                        toxicity_score = 0.0
                        flags = []

                        # Process Azure Content Safety results
                        for category, details in result.get('categoriesAnalysis', {}).items():
                            score = details.get('severity', 0) / 4.0  # Convert to 0-1 scale
                            categories[category] = score
                            toxicity_score = max(toxicity_score, score)

                            if score > 0.5:
                                flags.append(category.lower())

                        return ModerationResult(
                            content_id=content_id,
                            content_type='text',
                            provider='content_safety',
                            toxicity_score=toxicity_score,
                            categories=categories,
                            flags=flags,
                            action_taken='pending',
                            confidence=0.85,
                            timestamp=datetime.now(),
                            metadata={'api_version': 'v1'}
                        )
                    else:
                        self.logger.error(f"Content Safety error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error with Content Safety: {e}")
            return None

    async def _moderate_image_with_sightengine(self, image_url: str, content_id: str) -> Optional[ModerationResult]:
        """Moderate image using SightEngine API"""
        try:
            params = {
                'url': image_url,
                'models': 'nudity,wad,offensive,properties',
                'api_user': self.sightengine_client['api_user'],
                'api_secret': self.sightengine_client['api_secret']
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.sightengine_client['base_url']}/check.json",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        categories = {}
                        toxicity_score = 0.0
                        flags = []

                        # Process nudity detection
                        nudity = result.get('nudity', {})
                        if nudity.get('raw', 0) > 0.3:
                            categories['NUDITY'] = nudity.get('raw', 0)
                            toxicity_score = max(toxicity_score, categories['NUDITY'])
                            flags.append('nudity_detected')

                        # Process offensive content
                        offensive = result.get('offensive', {})
                        if offensive.get('prob', 0) > 0.3:
                            categories['OFFENSIVE'] = offensive.get('prob', 0)
                            toxicity_score = max(toxicity_score, categories['OFFENSIVE'])
                            flags.append('offensive_content')

                        # Process weapons/alcohol/drugs detection
                        wad = result.get('wad', {})
                        if wad.get('alcohol', 0) > 0.3:
                            categories['ALCOHOL'] = wad.get('alcohol', 0)
                            flags.append('alcohol_detected')
                        if wad.get('weapons', 0) > 0.3:
                            categories['WEAPONS'] = wad.get('weapons', 0)
                            flags.append('weapons_detected')
                        if wad.get('drugs', 0) > 0.3:
                            categories['DRUGS'] = wad.get('drugs', 0)
                            flags.append('drugs_detected')

                        return ModerationResult(
                            content_id=content_id,
                            content_type='image',
                            provider='sightengine',
                            toxicity_score=toxicity_score,
                            categories=categories,
                            flags=flags,
                            action_taken='pending',
                            confidence=0.9,
                            timestamp=datetime.now(),
                            metadata={'image_url': image_url}
                        )
                    else:
                        self.logger.error(f"SightEngine error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error with SightEngine: {e}")
            return None

    async def _apply_moderation_rules(self, results: List[ModerationResult], content_id: str) -> str:
        """Apply moderation rules to determine final action"""
        try:
            if not results:
                return 'approved'

            # Sort rules by priority
            enabled_rules = [rule for rule in self.rules.values() if rule.enabled]

            for rule in enabled_rules:
                if await self._evaluate_rule(rule, results):
                    return rule.action

            # Default action based on highest toxicity score
            max_toxicity = max(r.toxicity_score for r in results)
            if max_toxicity >= 0.8:
                return 'rejected'
            elif max_toxicity >= 0.6:
                return 'flagged'
            else:
                return 'approved'

        except Exception as e:
            self.logger.error(f"Error applying moderation rules: {e}")
            return 'review_needed'

    async def _evaluate_rule(self, rule: ModerationRule, results: List[ModerationResult]) -> bool:
        """Evaluate if a moderation rule applies"""
        try:
            conditions = rule.conditions

            # Check provider-specific conditions
            if 'provider' in conditions:
                provider_results = [r for r in results if r.provider == conditions['provider']]
                if not provider_results:
                    return False

                result = provider_results[0]

                # Check toxicity score conditions
                if 'toxicity_score' in conditions:
                    score_cond = conditions['toxicity_score']
                    if 'gte' in score_cond and result.toxicity_score < score_cond['gte']:
                        return False
                    if 'lt' in score_cond and result.toxicity_score >= score_cond['lt']:
                        return False

                # Check category conditions
                if 'categories' in conditions:
                    for category, category_cond in conditions['categories'].items():
                        if category not in result.categories:
                            return False
                        if 'gte' in category_cond and result.categories[category] < category_cond['gte']:
                            return False

            # Check local filter conditions
            if 'local_filters' in conditions:
                local_results = [r for r in results if r.provider == 'local_filters']
                if not local_results:
                    return False

                local_result = local_results[0]
                for filter_type in conditions['local_filters']:
                    if filter_type not in local_result.flags:
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Error evaluating rule: {e}")
            return False

    def _combine_categories(self, results: List[ModerationResult]) -> Dict[str, float]:
        """Combine categories from multiple moderation results"""
        combined = {}
        for result in results:
            for category, score in result.categories.items():
                combined[category] = max(combined.get(category, 0), score)
        return combined

    def _combine_flags(self, results: List[ModerationResult]) -> List[str]:
        """Combine flags from multiple moderation results"""
        combined = set()
        for result in results:
            combined.update(result.flags)
        return list(combined)

    def _calculate_confidence(self, results: List[ModerationResult]) -> float:
        """Calculate overall confidence in moderation results"""
        if not results:
            return 0.0
        return sum(r.confidence for r in results) / len(results)

    def _update_stats(self, result: ModerationResult):
        """Update moderation statistics"""
        self.stats['total_content_moderated'] += 1

        if result.action_taken == 'approved':
            self.stats['content_approved'] += 1
        elif result.action_taken == 'rejected':
            self.stats['content_rejected'] += 1
        elif result.action_taken == 'flagged':
            self.stats['content_flagged'] += 1

        # Update provider usage
        for provider_result in result.metadata.get('provider_results', []):
            provider = provider_result.get('provider', 'unknown')
            if provider not in self.stats['provider_usage']:
                self.stats['provider_usage'][provider] = 0
            self.stats['provider_usage'][provider] += 1

    async def _send_moderation_webhook(self, result: ModerationResult):
        """Send webhook for moderation actions"""
        try:
            webhook_data = {
                'event_type': 'content_moderated',
                'content_id': result.content_id,
                'content_type': result.content_type,
                'action_taken': result.action_taken,
                'toxicity_score': result.toxicity_score,
                'flags': result.flags,
                'confidence': result.confidence,
                'timestamp': result.timestamp.isoformat(),
                'metadata': result.metadata
            }

            # Send to analytics
            await self.manager.execute_webhook('analytics_services', 'moderation_event', webhook_data)

        except Exception as e:
            self.logger.error(f"Error sending moderation webhook: {e}")

    async def add_moderation_rule(self, rule: ModerationRule) -> Dict[str, Any]:
        """Add a new moderation rule"""
        try:
            self.rules[rule.rule_id] = rule

            # Save rule to cache
            rules_data = {rule_id: asdict(rule_obj) for rule_id, rule_obj in self.rules.items()}
            await self.manager.cache_set('moderation_rules', rules_data, ttl=86400)

            return {
                'success': True,
                'rule_id': rule.rule_id,
                'message': 'Moderation rule added successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def remove_moderation_rule(self, rule_id: str) -> Dict[str, Any]:
        """Remove a moderation rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]

                # Update cache
                rules_data = {rule_id: asdict(rule_obj) for rule_id, rule_obj in self.rules.items()}
                await self.manager.cache_set('moderation_rules', rules_data, ttl=86400)

                return {
                    'success': True,
                    'rule_id': rule_id,
                    'message': 'Moderation rule removed successfully'
                }
            else:
                return {'success': False, 'error': 'Rule not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_moderation_history(self, content_id: str = None,
                                   start_date: datetime = None,
                                   end_date: datetime = None,
                                   limit: int = 100) -> Dict[str, Any]:
        """Get moderation history"""
        try:
            history = self.moderation_history.copy()

            # Filter by content_id
            if content_id:
                history = [h for h in history if h.content_id == content_id]

            # Filter by date range
            if start_date:
                history = [h for h in history if h.timestamp >= start_date]
            if end_date:
                history = [h for h in history if h.timestamp <= end_date]

            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.timestamp, reverse=True)

            # Apply limit
            history = history[:limit]

            return {
                'history': [
                    {
                        'content_id': h.content_id,
                        'content_type': h.content_type,
                        'provider': h.provider,
                        'action_taken': h.action_taken,
                        'toxicity_score': h.toxicity_score,
                        'flags': h.flags,
                        'confidence': h.confidence,
                        'timestamp': h.timestamp.isoformat(),
                        'metadata': h.metadata
                    }
                    for h in history
                ],
                'total_count': len(history)
            }

        except Exception as e:
            return {'error': str(e), 'history': []}

    async def get_moderation_stats(self, start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """Get moderation statistics"""
        try:
            return {
                'total_content_moderated': self.stats['total_content_moderated'],
                'content_approved': self.stats['content_approved'],
                'content_rejected': self.stats['content_rejected'],
                'content_flagged': self.stats['content_flagged'],
                'approval_rate': (
                    self.stats['content_approved'] / self.stats['total_content_moderated']
                    if self.stats['total_content_moderated'] > 0 else 0
                ),
                'rejection_rate': (
                    self.stats['content_rejected'] / self.stats['total_content_moderated']
                    if self.stats['total_content_moderated'] > 0 else 0
                ),
                'flagging_rate': (
                    self.stats['content_flagged'] / self.stats['total_content_moderated']
                    if self.stats['total_content_moderated'] > 0 else 0
                ),
                'provider_usage': self.stats['provider_usage'],
                'time_period': f"{start_date} to {end_date}" if start_date and end_date else "All time"
            }

        except Exception as e:
            return {'error': str(e)}

    async def _analytics_processor(self):
        """Background processor for moderation analytics"""
        while True:
            try:
                # Process analytics every hour
                await asyncio.sleep(3600)

                # Generate analytics report
                await self._generate_analytics_report()

            except Exception as e:
                self.logger.error(f"Error in analytics processor: {e}")
                await asyncio.sleep(300)

    async def _generate_analytics_report(self):
        """Generate periodic analytics report"""
        try:
            # Generate daily statistics
            daily_stats = await self.get_moderation_stats(
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            )

            # Send to analytics service
            await self.manager.execute_webhook('analytics_services', 'moderation_daily_stats', daily_stats)

            self.logger.info("Generated daily moderation analytics report")

        except Exception as e:
            self.logger.error(f"Error generating analytics report: {e}")

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("Moderation Tools Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Moderation Tools Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'metrics': {
                'total_rules': len(self.rules),
                'active_rules': len([r for r in self.rules.values() if r.enabled]),
                'total_moderated': self.stats['total_content_moderated'],
                'approval_rate': (
                    self.stats['content_approved'] / self.stats['total_content_moderated']
                    if self.stats['total_content_moderated'] > 0 else 0
                )
            }
        }

        # Check Perspective API
        if self.perspective_client:
            try:
                # Test Perspective API with a simple request
                test_data = {
                    'comment': {'text': 'Hello world'},
                    'languages': ['en'],
                    'requestedAttributes': {'TOXICITY': {}}
                }
                # Would make actual test call here
                health_status['providers']['perspective'] = {'status': 'configured'}
            except Exception as e:
                health_status['providers']['perspective'] = {'status': 'error', 'error': str(e)}

        # Check other providers
        if self.content_safety_client:
            health_status['providers']['content_safety'] = {'status': 'configured'}

        if self.sightengine_client:
            health_status['providers']['sightengine'] = {'status': 'configured'}

        return health_status

    async def check_rate_limit(self):
        """Check rate limits"""
        # Rate limiting would be implemented here
        pass

    async def handle_webhook(self, event_type: str, data: Dict[str, Any]):
        """Handle webhook events"""
        if event_type == 'moderate_content':
            await self.moderate_content(
                content=data.get('content', ''),
                content_type=data.get('content_type', 'text'),
                content_id=data.get('content_id'),
                user_id=data.get('user_id'),
                context=data.get('context', {})
            )

    async def shutdown(self):
        """Shutdown the integration"""
        self.logger.info("Moderation Tools Integration shutdown")

# Helper function to convert dataclass to dict
def asdict(obj):
    """Convert dataclass to dictionary"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, tuple)):
                result[key] = [asdict(item) if hasattr(item, '__dict__') else item for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = asdict(value)
            else:
                result[key] = value
        return result
    return obj