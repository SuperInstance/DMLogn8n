#!/usr/bin/env python3
"""
DMLogn8n Reputation System - Comprehensive Social Standing and Trust Mechanics

Handles reputation tracking, trust scoring, social standing, faction relationships,
player ratings, behavioral analysis, and consequence systems.

Features:
- Multi-dimensional reputation scoring
- Faction-based reputation systems
- Trust and credibility tracking
- Behavioral reputation analysis
- Player rating and review systems
- Reputation decay and recovery
- Social consequence mechanics
- NPC reputation systems
- Achievement-based reputation boosts
- Cross-server reputation sync
- Reputation rewards and penalties
"""

import asyncio
import json
import logging
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import random
from collections import defaultdict, deque

class ReputationType(Enum):
    """Types of reputation"""
    GENERAL = "general"
    COMBAT = "combat"
    TRADING = "trading"
    CRAFTING = "crafting"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    LEADERSHIP = "leadership"
    HELPING = "helping"
    ROLEPLAY = "roleplay"
    PVP = "pvp"
    QUESTING = "questing"
    DUNGEONEERING = "dungeoneering"
    COMMUNITY = "community"

class ReputationLevel(Enum):
    """Reputation level tiers"""
    HATED = -5
    HOSTILE = -4
    UNFRIENDLY = -3
    NEUTRAL = -2
    INDIFFERENT = -1
    FRIENDLY = 0
    HONORED = 1
    REVERED = 2
    EXALTED = 3
    LEGENDARY = 4
    MYTHIC = 5

class ReputationSource(Enum):
    """Sources of reputation changes"""
    QUEST_COMPLETION = "quest_completion"
    PVP_VICTORY = "pvp_victory"
    PVP_DEFEAT = "pvp_defeat"
    TRADE_SUCCESS = "trade_success"
    TRADE_SCAM = "trade_scam"
    HELPING_OTHERS = "helping_others"
    GUILD_CONTRIBUTION = "guild_contribution"
    COMMUNITY_EVENT = "community_event"
    PLAYER_RATING = "player_rating"
    SYSTEM_AWARD = "system_award"
    MODERATOR_ACTION = "moderator_action"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    FACTION_QUEST = "faction_quest"
    NPC_INTERACTION = "npc_interaction"

class TrustFactor(Enum):
    """Factors affecting trust score"""
    CONSISTENCY = "consistency"
    RELIABILITY = "reliability"
    HONESTY = "honesty"
    FAIRNESS = "fairness"
    HELPFULNESS = "helpfulness"
    COMMUNICATION = "communication"
    RESPECT = "respect"
    INTEGRITY = "integrity"
    GENEROSITY = "generosity"
    RESPONSIBILITY = "responsibility"

class BehaviorType(Enum):
    """Types of tracked behaviors"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    TOXIC = "toxic"
    HELPFUL = "helpful"
    TEAMWORK = "teamwork"
    LEADERSHIP = "leadership"
    CHEATING = "cheating"
    EXPLOITING = "exploiting"
    SCAMMING = "scamming"

@dataclass
class ReputationEntry:
    """Individual reputation entry"""
    id: str
    entity_id: str
    reputation_type: ReputationType
    source_id: Optional[str]  # Who gave this reputation (None for system)
    source_type: ReputationSource
    score: float
    reason: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    weight: float = 1.0
    expires_date: Optional[datetime] = None

@dataclass
class FactionReputation:
    """Reputation with a specific faction"""
    faction_id: str
    faction_name: str
    reputation_score: float
    level: ReputationLevel
    standing_bonuses: Dict[str, float] = field(default_factory=dict)
    access_rights: List[str] = field(default_factory=list)
    quest_access: List[str] = field(default_factory=list)
    vendor_discounts: Dict[str, float] = field(default_factory=dict)
    special_rewards: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class PlayerRating:
    """Player rating given by another player"""
    id: str
    rater_id: str
    rated_id: str
    overall_rating: float  # 1-5 stars
    category_ratings: Dict[str, float] = field(default_factory=dict)
    comment: str = ""
    tags: List[str] = field(default_factory=list)
    interaction_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    verified: bool = False
    helpful_votes: int = 0
    total_votes: int = 0

@dataclass
class TrustScore:
    """Trust score for an entity"""
    entity_id: str
    overall_trust: float
    factor_scores: Dict[TrustFactor, float] = field(default_factory=dict)
    confidence_level: float = 0.0
    prediction_accuracy: float = 0.0
    last_calculated: datetime = field(default_factory=datetime.now)
    calculation_history: List[Dict] = field(default_factory=list)

@dataclass
class BehaviorRecord:
    """Record of tracked behavior"""
    id: str
    entity_id: str
    behavior_type: BehaviorType
    description: str
    severity: float  # 0.0 to 1.0
    frequency: int = 1
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    impact_score: float = 0.0
    decay_rate: float = 0.1
    evidence: List[Dict] = field(default_factory=list)

@dataclass
class ReputationConsequence:
    """Consequence of reputation level"""
    id: str
    reputation_type: ReputationType
    level_range: Tuple[ReputationLevel, ReputationLevel]
    consequences: List[Dict]
    rewards: List[Dict]
    penalties: List[Dict]
    is_active: bool = True
    created_date: datetime = field(default_factory=datetime.now)

class ReputationSystem:
    """Main reputation management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.reputation_entries: Dict[str, List[ReputationEntry]] = defaultdict(list)
        self.faction_reputations: Dict[str, Dict[str, FactionReputation]] = defaultdict(dict)
        self.player_ratings: Dict[str, List[PlayerRating]] = defaultdict(list)
        self.trust_scores: Dict[str, TrustScore] = {}
        self.behavior_records: Dict[str, List[BehaviorRecord]] = defaultdict(list)
        self.consequences: Dict[str, List[ReputationConsequence]] = defaultdict(list)

        # Reputation scores cache
        self.reputation_cache: Dict[str, Dict[ReputationType, float]] = {}
        self.reputation_levels: Dict[str, Dict[ReputationType, ReputationLevel]] = {}

        # System settings
        self.reputation_decay_enabled = True
        self.behavior_analysis_enabled = True
        self.cross_faction_impact = True

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_reputation": 10000,
            "min_reputation": -10000,
            "neutral_reputation": 0,
            "reputation_decay_rate": 0.001,  # Daily decay
            "behavior_decay_rate": 0.01,
            "trust_calculation_interval": 3600,  # 1 hour
            "reputation_update_interval": 300,  # 5 minutes
            "max_rating_per_day": 10,
            "rating_cooldown_hours": 24,
            "behavior_impact_threshold": 0.1,
            "trust_weight_decay_days": 30,
            "faction_impact_multiplier": 1.2,
            "pvp_reputation_impact": 0.5,
            "trading_reputation_impact": 1.0,
            "helping_reputation_impact": 1.5,
            "toxic_behavior_penalty": -10.0,
            "scamming_penalty": -50.0,
            "cheating_penalty": -100.0,
            "achievement_bonus_multiplier": 1.5,
            "leadership_bonus_multiplier": 1.3
        }

    async def add_reputation(self, entity_id: str, reputation_type: ReputationType,
                           source_id: str, source_type: ReputationSource,
                           score: float, reason: str, context: Dict = None) -> Dict:
        """Add reputation to an entity"""
        try:
            # Validate input
            if score == 0:
                return {"success": False, "error": "Reputation score cannot be zero"}

            # Apply source-specific multipliers
            multiplier = await self._get_reputation_multiplier(source_type, reputation_type)
            adjusted_score = score * multiplier

            # Create reputation entry
            entry = ReputationEntry(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                reputation_type=reputation_type,
                source_id=source_id,
                source_type=source_type,
                score=adjusted_score,
                reason=reason,
                timestamp=datetime.now(),
                context=context or {},
                weight=await self._calculate_entry_weight(source_id, source_type)
            )

            # Store entry
            self.reputation_entries[entity_id].append(entry)

            # Update cached reputation
            await self._update_reputation_cache(entity_id, reputation_type)

            # Apply cross-faction impact if enabled
            if self.cross_faction_impact and reputation_type != ReputationType.GENERAL:
                await self._apply_cross_faction_impact(entity_id, reputation_type, adjusted_score)

            # Check for reputation level changes
            level_change = await self._check_reputation_level_change(entity_id, reputation_type)

            # Apply consequences
            if level_change:
                await self._apply_reputation_consequences(entity_id, reputation_type, level_change)

            # Log the change
            self.logger.info(f"Added {adjusted_score:.2f} {reputation_type.value} reputation to {entity_id} from {source_id}")

            return {
                "success": True,
                "entry_id": entry.id,
                "adjusted_score": adjusted_score,
                "new_level": self.reputation_levels.get(entity_id, {}).get(reputation_type),
                "level_change": level_change,
                "message": f"Reputation updated: {adjusted_score:+.2f}"
            }

        except Exception as e:
            self.logger.error(f"Error adding reputation: {e}")
            return {"success": False, "error": str(e)}

    async def rate_player(self, rater_id: str, rated_id: str, overall_rating: float,
                         category_ratings: Dict[str, float] = None, comment: str = "",
                         tags: List[str] = None, interaction_type: str = "") -> Dict:
        """Rate another player"""
        try:
            # Validate rating
            if rater_id == rated_id:
                return {"success": False, "error": "Cannot rate yourself"}

            if not 1.0 <= overall_rating <= 5.0:
                return {"success": False, "error": "Rating must be between 1 and 5"}

            # Check cooldown
            if not await self._can_rate_player(rater_id, rated_id):
                return {"success": False, "error": "Rating cooldown not expired"}

            # Validate category ratings
            if category_ratings:
                for category, rating in category_ratings.items():
                    if not 1.0 <= rating <= 5.0:
                        return {"success": False, "error": f"Category rating '{category}' must be between 1 and 5"}

            # Create rating
            rating = PlayerRating(
                id=str(uuid.uuid4()),
                rater_id=rater_id,
                rated_id=rated_id,
                overall_rating=overall_rating,
                category_ratings=category_ratings or {},
                comment=comment,
                tags=tags or [],
                interaction_type=interaction_type,
                timestamp=datetime.now()
            )

            # Store rating
            self.player_ratings[rated_id].append(rating)

            # Update trust scores
            await self._update_trust_score(rated_id)

            # Add reputation impact based on rating
            reputation_impact = (overall_rating - 3.0) * 2.0  # Scale: 1->-4, 3->0, 5->+4

            await self.add_reputation(
                rated_id,
                ReputationType.GENERAL,
                rater_id,
                ReputationSource.PLAYER_RATING,
                reputation_impact,
                f"Player rating: {overall_rating}/5 stars",
                {"interaction_type": interaction_type, "comment": comment}
            )

            # Update rater's last rating time
            await self._update_rating_cooldown(rater_id, rated_id)

            self.logger.info(f"Player {rated_id} rated {overall_rating}/5 by {rater_id}")

            return {
                "success": True,
                "rating_id": rating.id,
                "message": f"Rating submitted: {overall_rating}/5 stars"
            }

        except Exception as e:
            self.logger.error(f"Error rating player: {e}")
            return {"success": False, "error": str(e)}

    async def set_faction_reputation(self, entity_id: str, faction_id: str, faction_name: str,
                                   score: float) -> Dict:
        """Set reputation with a specific faction"""
        try:
            # Calculate reputation level
            level = self._calculate_reputation_level(score)

            # Create faction reputation
            faction_rep = FactionReputation(
                faction_id=faction_id,
                faction_name=faction_name,
                reputation_score=score,
                level=level,
                standing_bonuses=await self._calculate_standing_bonuses(level),
                access_rights=await self._get_access_rights(level, faction_id),
                quest_access=await self._get_quest_access(level, faction_id),
                vendor_discounts=await self._calculate_vendor_discounts(level),
                special_rewards=await self._get_special_rewards(level, faction_id)
            )

            # Store faction reputation
            if entity_id not in self.faction_reputations:
                self.faction_reputations[entity_id] = {}
            self.faction_reputations[entity_id][faction_id] = faction_rep

            self.logger.info(f"Set faction reputation: {entity_id} -> {faction_name} ({score}, {level.name})")

            return {
                "success": True,
                "faction_id": faction_id,
                "faction_name": faction_name,
                "score": score,
                "level": level.name,
                "standing_bonuses": faction_rep.standing_bonuses,
                "message": f"Faction reputation updated: {level.name}"
            }

        except Exception as e:
            self.logger.error(f"Error setting faction reputation: {e}")
            return {"success": False, "error": str(e)}

    async def record_behavior(self, entity_id: str, behavior_type: BehaviorType,
                            description: str, severity: float, evidence: List[Dict] = None) -> Dict:
        """Record a behavior for reputation analysis"""
        try:
            # Check if similar behavior exists
            existing_behavior = None
            for behavior in self.behavior_records[entity_id]:
                if (behavior.behavior_type == behavior_type and
                    behavior.description.lower() == description.lower()):
                    existing_behavior = behavior
                    break

            if existing_behavior:
                # Update existing behavior
                existing_behavior.frequency += 1
                existing_behavior.last_observed = datetime.now()
                existing_behavior.severity = max(existing_behavior.severity, severity)
                if evidence:
                    existing_behavior.evidence.extend(evidence)
            else:
                # Create new behavior record
                behavior = BehaviorRecord(
                    id=str(uuid.uuid4()),
                    entity_id=entity_id,
                    behavior_type=behavior_type,
                    description=description,
                    severity=severity,
                    evidence=evidence or []
                )
                self.behavior_records[entity_id].append(behavior)

            # Calculate impact on reputation
            impact = await self._calculate_behavior_impact(entity_id, behavior_type, severity)
            if impact != 0:
                # Apply reputation change
                reputation_type = await self._get_behavior_reputation_type(behavior_type)
                source_type = ReputationSource.BEHAVIOR_ANALYSIS

                await self.add_reputation(
                    entity_id,
                    reputation_type,
                    "system",
                    source_type,
                    impact,
                    f"Behavior recorded: {description}",
                    {"behavior_type": behavior_type.value, "severity": severity}
                )

            self.logger.info(f"Recorded behavior for {entity_id}: {behavior_type.value} ({severity:.2f})")

            return {
                "success": True,
                "behavior_id": existing_behavior.id if existing_behavior else behavior.id,
                "impact": impact,
                "message": f"Behavior recorded: {behavior_type.value}"
            }

        except Exception as e:
            self.logger.error(f"Error recording behavior: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_trust_score(self, entity_id: str) -> Dict:
        """Calculate comprehensive trust score for an entity"""
        try:
            # Get all relevant data
            reputation_scores = await self._get_all_reputation_scores(entity_id)
            player_ratings = self.player_ratings.get(entity_id, [])
            behavior_records = self.behavior_records.get(entity_id, [])

            # Calculate factor scores
            factor_scores = {}

            # Consistency - based on reputation stability over time
            factor_scores[TrustFactor.CONSISTENCY] = await self._calculate_consistency_score(entity_id)

            # Reliability - based on completed commitments and promises
            factor_scores[TrustFactor.RELIABILITY] = await self._calculate_reliability_score(entity_id)

            # Honesty - based on truthfulness and transparency
            factor_scores[TrustFactor.HONESTY] = await self._calculate_honesty_score(entity_id)

            # Fairness - based on equitable treatment of others
            factor_scores[TrustFactor.FAIRNESS] = await self._calculate_fairness_score(entity_id)

            # Helpfulness - based on assisting others
            factor_scores[TrustFactor.HELPFULNESS] = await self._calculate_helpfulness_score(entity_id)

            # Communication - based on positive communication patterns
            factor_scores[TrustFactor.COMMUNICATION] = await self._calculate_communication_score(entity_id)

            # Respect - based on respectful interactions
            factor_scores[TrustFactor.RESPECT] = await self._calculate_respect_score(entity_id)

            # Integrity - based on adherence to principles
            factor_scores[TrustFactor.INTEGRITY] = await self._calculate_integrity_score(entity_id)

            # Generosity - based on giving to others
            factor_scores[TrustFactor.GENEROSITY] = await self._calculate_generosity_score(entity_id)

            # Responsibility - based on accountability
            factor_scores[TrustFactor.RESPONSIBILITY] = await self._calculate_responsibility_score(entity_id)

            # Calculate overall trust score (weighted average)
            weights = {
                TrustFactor.CONSISTENCY: 0.10,
                TrustFactor.RELIABILITY: 0.15,
                TrustFactor.HONESTY: 0.15,
                TrustFactor.FAIRNESS: 0.12,
                TrustFactor.HELPFULNESS: 0.10,
                TrustFactor.COMMUNICATION: 0.08,
                TrustFactor.RESPECT: 0.10,
                TrustFactor.INTEGRITY: 0.12,
                TrustFactor.GENEROSITY: 0.04,
                TrustFactor.RESPONSIBILITY: 0.04
            }

            overall_trust = sum(
                factor_scores[factor] * weights[factor]
                for factor in TrustFactor
            )

            # Calculate confidence level based on data amount
            total_data_points = (
                len(reputation_scores) +
                len(player_ratings) +
                len(behavior_records)
            )
            confidence_level = min(1.0, total_data_points / 50.0)  # Normalize to 0-1

            # Create trust score object
            trust_score = TrustScore(
                entity_id=entity_id,
                overall_trust=overall_trust,
                factor_scores=factor_scores,
                confidence_level=confidence_level,
                last_calculated=datetime.now(),
                calculation_history=[{
                    "timestamp": datetime.now().isoformat(),
                    "overall_trust": overall_trust,
                    "confidence": confidence_level,
                    "data_points": total_data_points
                }]
            )

            # Store trust score
            self.trust_scores[entity_id] = trust_score

            self.logger.info(f"Calculated trust score for {entity_id}: {overall_trust:.3f} (confidence: {confidence_level:.3f})")

            return {
                "success": True,
                "trust_score": overall_trust,
                "factor_scores": {factor.name: score for factor, score in factor_scores.items()},
                "confidence_level": confidence_level,
                "data_points": total_data_points
            }

        except Exception as e:
            self.logger.error(f"Error calculating trust score: {e}")
            return {"success": False, "error": str(e)}

    async def get_reputation_summary(self, entity_id: str) -> Dict:
        """Get comprehensive reputation summary for an entity"""
        try:
            # Get all reputation scores
            reputation_scores = await self._get_all_reputation_scores(entity_id)

            # Get reputation levels
            reputation_levels = {}
            for rep_type, score in reputation_scores.items():
                reputation_levels[rep_type.value] = self._calculate_reputation_level(score).name

            # Get faction reputations
            faction_reps = self.faction_reputations.get(entity_id, {})

            # Get player ratings summary
            player_ratings = self.player_ratings.get(entity_id, [])
            ratings_summary = await self._calculate_ratings_summary(player_ratings)

            # Get trust score
            trust_score = self.trust_scores.get(entity_id)
            trust_data = None
            if trust_score:
                trust_data = {
                    "overall_trust": trust_score.overall_trust,
                    "confidence_level": trust_score.confidence_level,
                    "factor_scores": {factor.name: score for factor, score in trust_score.factor_scores.items()}
                }

            # Get behavior summary
            behavior_records = self.behavior_records.get(entity_id, [])
            behavior_summary = await self._calculate_behavior_summary(behavior_records)

            # Get recent reputation changes
            recent_changes = await self._get_recent_reputation_changes(entity_id, days=7)

            # Get reputation rank
            rank_info = await self._get_reputation_rank(entity_id)

            summary = {
                "entity_id": entity_id,
                "reputation_scores": {rep_type.value: score for rep_type, score in reputation_scores.items()},
                "reputation_levels": reputation_levels,
                "faction_reputations": {
                    faction_id: {
                        "name": rep.faction_name,
                        "score": rep.reputation_score,
                        "level": rep.level.name,
                        "bonuses": rep.standing_bonuses
                    }
                    for faction_id, rep in faction_reps.items()
                },
                "player_ratings": ratings_summary,
                "trust_score": trust_data,
                "behavior_summary": behavior_summary,
                "recent_changes": recent_changes,
                "rank_info": rank_info,
                "last_updated": datetime.now().isoformat()
            }

            return {
                "success": True,
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"Error getting reputation summary: {e}")
            return {"success": False, "error": str(e)}

    async def get_faction_benefits(self, entity_id: str, faction_id: str) -> Dict:
        """Get benefits and bonuses from faction reputation"""
        try:
            if entity_id not in self.faction_reputations:
                return {"success": False, "error": "No faction reputations found"}

            if faction_id not in self.faction_reputations[entity_id]:
                return {"success": False, "error": "No reputation with this faction"}

            faction_rep = self.faction_reputations[entity_id][faction_id]

            benefits = {
                "standing_bonuses": faction_rep.standing_bonuses,
                "access_rights": faction_rep.access_rights,
                "quest_access": faction_rep.quest_access,
                "vendor_discounts": faction_rep.vendor_discounts,
                "special_rewards": faction_rep.special_rewards,
                "reputation_level": faction_rep.level.name,
                "next_level_requirement": await self._get_next_level_requirement(faction_rep.reputation_score)
            }

            return {
                "success": True,
                "faction_id": faction_id,
                "faction_name": faction_rep.faction_name,
                "benefits": benefits
            }

        except Exception as e:
            self.logger.error(f"Error getting faction benefits: {e}")
            return {"success": False, "error": str(e)}

    async def apply_reputation_decay(self):
        """Apply reputation decay to all entities"""
        try:
            decay_rate = self.config["reputation_decay_rate"]
            current_time = datetime.now()

            for entity_id, entries in self.reputation_entries.items():
                for entry in entries:
                    # Skip recent entries
                    days_old = (current_time - entry.timestamp).days
                    if days_old < 1:
                        continue

                    # Apply decay
                    decay_amount = entry.score * decay_rate * days_old
                    entry.score *= (1 - decay_rate * days_old)

                    # Mark for recalculation if significant change
                    if abs(decay_amount) > 0.1:
                        await self._update_reputation_cache(entity_id, entry.reputation_type)

            # Decay behavior records
            behavior_decay_rate = self.config["behavior_decay_rate"]
            for entity_id, behaviors in self.behavior_records.items():
                for behavior in behaviors:
                    days_old = (current_time - behavior.last_observed).days
                    if days_old > 0:
                        behavior.impact_score *= (1 - behavior_decay_rate * days_old)

            self.logger.info("Applied reputation decay to all entities")

        except Exception as e:
            self.logger.error(f"Error applying reputation decay: {e}")

    async def get_reputation_leaderboard(self, reputation_type: ReputationType, limit: int = 100) -> Dict:
        """Get leaderboard for specific reputation type"""
        try:
            entity_scores = {}

            # Calculate current scores for all entities
            for entity_id in self.reputation_cache:
                if reputation_type in self.reputation_cache[entity_id]:
                    entity_scores[entity_id] = self.reputation_cache[entity_id][reputation_type]

            # Sort by score (descending)
            sorted_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)

            # Create leaderboard
            leaderboard = []
            for rank, (entity_id, score) in enumerate(sorted_entities[:limit], 1):
                level = self._calculate_reputation_level(score)
                leaderboard.append({
                    "rank": rank,
                    "entity_id": entity_id,
                    "entity_name": await self._get_entity_name(entity_id),
                    "score": score,
                    "level": level.name
                })

            return {
                "success": True,
                "reputation_type": reputation_type.value,
                "leaderboard": leaderboard,
                "total_entities": len(sorted_entities)
            }

        except Exception as e:
            self.logger.error(f"Error getting reputation leaderboard: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    async def _get_reputation_multiplier(self, source_type: ReputationSource, reputation_type: ReputationType) -> float:
        """Get reputation multiplier based on source and type"""
        base_multipliers = {
            ReputationSource.QUEST_COMPLETION: 1.0,
            ReputationSource.PVP_VICTORY: self.config["pvp_reputation_impact"],
            ReputationSource.PVP_DEFEAT: -0.5,
            ReputationSource.TRADE_SUCCESS: self.config["trading_reputation_impact"],
            ReputationSource.TRADE_SCAM: -5.0,
            ReputationSource.HELPING_OTHERS: self.config["helping_reputation_impact"],
            ReputationSource.GUILD_CONTRIBUTION: 1.2,
            ReputationSource.COMMUNITY_EVENT: 1.5,
            ReputationSource.PLAYER_RATING: 1.0,
            ReputationSource.SYSTEM_AWARD: 2.0,
            ReputationSource.MODERATOR_ACTION: 3.0,
            ReputationSource.BEHAVIOR_ANALYSIS: 1.0,
            ReputationSource.ACHIEVEMENT_UNLOCK: self.config["achievement_bonus_multiplier"],
            ReputationSource.FACTION_QUEST: 1.3,
            ReputationSource.NPC_INTERACTION: 0.8
        }

        return base_multipliers.get(source_type, 1.0)

    async def _calculate_entry_weight(self, source_id: str, source_type: ReputationSource) -> float:
        """Calculate weight for a reputation entry"""
        # System sources have higher weight
        if source_id == "system":
            return 1.5

        # Player sources have variable weight based on their reputation
        if source_type == ReputationSource.PLAYER_RATING:
            source_trust = self.trust_scores.get(source_id)
            if source_trust:
                return 0.5 + source_trust.overall_trust * 0.5
            return 0.5

        return 1.0

    async def _update_reputation_cache(self, entity_id: str, reputation_type: ReputationType):
        """Update cached reputation score for entity"""
        if entity_id not in self.reputation_cache:
            self.reputation_cache[entity_id] = {}

        # Calculate weighted average of entries
        entries = [e for e in self.reputation_entries[entity_id] if e.reputation_type == reputation_type]
        if not entries:
            return

        total_weight = sum(e.weight for e in entries)
        if total_weight == 0:
            return

        weighted_score = sum(e.score * e.weight for e in entries) / total_weight
        self.reputation_cache[entity_id][reputation_type] = weighted_score

        # Update reputation level
        if entity_id not in self.reputation_levels:
            self.reputation_levels[entity_id] = {}
        self.reputation_levels[entity_id][reputation_type] = self._calculate_reputation_level(weighted_score)

    def _calculate_reputation_level(self, score: float) -> ReputationLevel:
        """Calculate reputation level from score"""
        if score >= 8000:
            return ReputationLevel.MYTHIC
        elif score >= 5000:
            return ReputationLevel.LEGENDARY
        elif score >= 3000:
            return ReputationLevel.EXALTED
        elif score >= 1500:
            return ReputationLevel.REVERED
        elif score >= 500:
            return ReputationLevel.HONORED
        elif score >= 0:
            return ReputationLevel.FRIENDLY
        elif score >= -500:
            return ReputationLevel.INDIFFERENT
        elif score >= -1500:
            return ReputationLevel.NEUTRAL
        elif score >= -3000:
            return ReputationLevel.UNFRIENDLY
        elif score >= -5000:
            return ReputationLevel.HOSTILE
        else:
            return ReputationLevel.HATED

    async def _check_reputation_level_change(self, entity_id: str, reputation_type: ReputationType) -> Optional[Tuple[ReputationLevel, ReputationLevel]]:
        """Check if reputation level changed"""
        if entity_id not in self.reputation_levels or reputation_type not in self.reputation_levels[entity_id]:
            return None

        current_level = self.reputation_levels[entity_id][reputation_type]
        score = self.reputation_cache[entity_id].get(reputation_type, 0)
        new_level = self._calculate_reputation_level(score)

        if current_level != new_level:
            return (current_level, new_level)
        return None

    async def _apply_reputation_consequences(self, entity_id: str, reputation_type: ReputationType, level_change: Tuple[ReputationLevel, ReputationLevel]):
        """Apply consequences of reputation level change"""
        old_level, new_level = level_change

        # Get consequences for new level
        consequences = self.consequences.get(reputation_type.value, [])
        applicable_consequences = [
            c for c in consequences
            if c.is_active and c.level_range[0].value <= new_level.value <= c.level_range[1].value
        ]

        for consequence in applicable_consequences:
            # Apply rewards
            for reward in consequence.rewards:
                await self._apply_reward(entity_id, reward)

            # Apply penalties
            for penalty in consequence.penalties:
                await self._apply_penalty(entity_id, penalty)

        self.logger.info(f"Applied reputation consequences for {entity_id}: {old_level.name} -> {new_level.name}")

    async def _can_rate_player(self, rater_id: str, rated_id: str) -> bool:
        """Check if rater can rate rated player (cooldown check)"""
        # This would check rating cooldowns in a database
        return True  # Placeholder

    async def _update_rating_cooldown(self, rater_id: str, rated_id: str):
        """Update rating cooldown"""
        # This would set cooldown in a database
        pass  # Placeholder

    async def _get_all_reputation_scores(self, entity_id: str) -> Dict[ReputationType, float]:
        """Get all reputation scores for an entity"""
        return self.reputation_cache.get(entity_id, {})

    def _calculate_standing_bonuses(self, level: ReputationLevel) -> Dict[str, float]:
        """Calculate standing bonuses for reputation level"""
        bonuses = {
            ReputationLevel.HATED: {"vendor_prices": 2.0, "quest_rewards": 0.5},
            ReputationLevel.HOSTILE: {"vendor_prices": 1.5, "quest_rewards": 0.7},
            ReputationLevel.UNFRIENDLY: {"vendor_prices": 1.2, "quest_rewards": 0.85},
            ReputationLevel.NEUTRAL: {"vendor_prices": 1.0, "quest_rewards": 1.0},
            ReputationLevel.INDIFFERENT: {"vendor_prices": 1.0, "quest_rewards": 1.0},
            ReputationLevel.FRIENDLY: {"vendor_prices": 0.95, "quest_rewards": 1.1},
            ReputationLevel.HONORED: {"vendor_prices": 0.9, "quest_rewards": 1.2},
            ReputationLevel.REVERED: {"vendor_prices": 0.85, "quest_rewards": 1.3},
            ReputationLevel.EXALTED: {"vendor_prices": 0.8, "quest_rewards": 1.5},
            ReputationLevel.LEGENDARY: {"vendor_prices": 0.75, "quest_rewards": 1.75},
            ReputationLevel.MYTHIC: {"vendor_prices": 0.7, "quest_rewards": 2.0}
        }
        return bonuses.get(level, {})

    async def _get_access_rights(self, level: ReputationLevel, faction_id: str) -> List[str]:
        """Get access rights for reputation level"""
        rights = {
            ReputationLevel.HATED: [],
            ReputationLevel.HOSTILE: ["entry"],
            ReputationLevel.UNFRIENDLY: ["entry", "basic_vendor"],
            ReputationLevel.NEUTRAL: ["entry", "basic_vendor", "standard_vendor"],
            ReputationLevel.INDIFFERENT: ["entry", "basic_vendor", "standard_vendor"],
            ReputationLevel.FRIENDLY: ["entry", "basic_vendor", "standard_vendor", "advanced_vendor"],
            ReputationLevel.HONORED: ["entry", "all_vendors", "training_facilities"],
            ReputationLevel.REVERED: ["entry", "all_vendors", "training_facilities", "special_areas"],
            ReputationLevel.EXALTED: ["entry", "all_vendors", "training_facilities", "special_areas", "leadership_areas"],
            ReputationLevel.LEGENDARY: ["all_access"],
            ReputationLevel.MYTHIC: ["all_access", "exclusive_content"]
        }
        return rights.get(level, [])

    async def _get_quest_access(self, level: ReputationLevel, faction_id: str) -> List[str]:
        """Get quest access for reputation level"""
        # This would integrate with your quest system
        return []  # Placeholder

    async def _calculate_vendor_discounts(self, level: ReputationLevel) -> Dict[str, float]:
        """Calculate vendor discounts for reputation level"""
        discounts = {
            ReputationLevel.HATED: {},
            ReputationLevel.HOSTILE: {},
            ReputationLevel.UNFRIENDLY: {},
            ReputationLevel.NEUTRAL: {},
            ReputationLevel.INDIFFERENT: {},
            ReputationLevel.FRIENDLY: {"general": 0.05},
            ReputationLevel.HONORED: {"general": 0.1, "crafting": 0.05},
            ReputationLevel.REVERED: {"general": 0.15, "crafting": 0.1, "equipment": 0.05},
            ReputationLevel.EXALTED: {"general": 0.2, "crafting": 0.15, "equipment": 0.1},
            ReputationLevel.LEGENDARY: {"general": 0.25, "crafting": 0.2, "equipment": 0.15, "rare": 0.1},
            ReputationLevel.MYTHIC: {"general": 0.3, "crafting": 0.25, "equipment": 0.2, "rare": 0.15, "epic": 0.1}
        }
        return discounts.get(level, {})

    async def _get_special_rewards(self, level: ReputationLevel, faction_id: str) -> List[str]:
        """Get special rewards for reputation level"""
        # This would integrate with your reward system
        return []  # Placeholder

    async def _apply_cross_faction_impact(self, entity_id: str, reputation_type: ReputationType, score: float):
        """Apply cross-faction reputation impact"""
        # Apply a portion of reputation change to allied/opposed factions
        cross_impact = score * 0.1 * self.config["faction_impact_multiplier"]

        # This would need faction relationship data
        # For now, just apply to general reputation
        await self.add_reputation(
            entity_id,
            ReputationType.GENERAL,
            "system",
            ReputationSource.SYSTEM_AWARD,
            cross_impact,
            f"Cross-faction impact from {reputation_type.value} reputation"
        )

    async def _calculate_behavior_impact(self, entity_id: str, behavior_type: BehaviorType, severity: float) -> float:
        """Calculate reputation impact of behavior"""
        base_impacts = {
            BehaviorType.POSITIVE: severity * 5.0,
            BehaviorType.NEGATIVE: -severity * 3.0,
            BehaviorType.NEUTRAL: 0.0,
            BehaviorType.TOXIC: -severity * 10.0,
            BehaviorType.HELPFUL: severity * 8.0,
            BehaviorType.TEAMWORK: severity * 6.0,
            BehaviorType.LEADERSHIP: severity * 7.0,
            BehaviorType.CHEATING: -severity * 20.0,
            BehaviorType.EXPLOITING: -severity * 15.0,
            BehaviorType.SCAMMING: -severity * 25.0
        }

        return base_impacts.get(behavior_type, 0.0)

    async def _get_behavior_reputation_type(self, behavior_type: BehaviorType) -> ReputationType:
        """Get reputation type affected by behavior"""
        behavior_mapping = {
            BehaviorType.TEAMWORK: ReputationType.LEADERSHIP,
            BehaviorType.LEADERSHIP: ReputationType.LEADERSHIP,
            BehaviorType.HELPFUL: ReputationType.HELPING,
            BehaviorType.TOXIC: ReputationType.SOCIAL,
            BehaviorType.CHEATING: ReputationType.GENERAL,
            BehaviorType.EXPLOITING: ReputationType.GENERAL,
            BehaviorType.SCAMMING: ReputationType.TRADING
        }
        return behavior_mapping.get(behavior_type, ReputationType.GENERAL)

    async def _calculate_ratings_summary(self, ratings: List[PlayerRating]) -> Dict:
        """Calculate summary of player ratings"""
        if not ratings:
            return {"count": 0, "average": 0.0, "distribution": {}}

        total_ratings = len(ratings)
        average_rating = sum(r.overall_rating for r in ratings) / total_ratings

        # Calculate distribution
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            distribution[str(int(rating.overall_rating))] += 1

        # Calculate helpfulness
        helpful_ratings = [r for r in ratings if r.total_votes > 0]
        average_helpfulness = 0.0
        if helpful_ratings:
            average_helpfulness = sum(r.helpful_votes / r.total_votes for r in helpful_ratings) / len(helpful_ratings)

        return {
            "count": total_ratings,
            "average": average_rating,
            "distribution": distribution,
            "average_helpfulness": average_helpfulness,
            "recent_count": len([r for r in ratings if (datetime.now() - r.timestamp).days <= 30])
        }

    async def _calculate_behavior_summary(self, behaviors: List[BehaviorRecord]) -> Dict:
        """Calculate summary of behavior records"""
        if not behaviors:
            return {"total_behaviors": 0, "by_type": {}, "severity_average": 0.0}

        # Group by type
        by_type = defaultdict(list)
        for behavior in behaviors:
            by_type[behavior.behavior_type].append(behavior)

        # Calculate summary
        summary = {
            "total_behaviors": len(behaviors),
            "by_type": {},
            "severity_average": sum(b.severity for b in behaviors) / len(behaviors),
            "recent_behaviors": len([b for b in behaviors if (datetime.now() - b.last_observed).days <= 7])
        }

        for behavior_type, type_behaviors in by_type.items():
            summary["by_type"][behavior_type.value] = {
                "count": len(type_behaviors),
                "average_severity": sum(b.severity for b in type_behaviors) / len(type_behaviors),
                "total_impact": sum(b.impact_score for b in type_behaviors),
                "most_recent": max(b.last_observed for b in type_behaviors).isoformat()
            }

        return summary

    async def _get_recent_reputation_changes(self, entity_id: str, days: int = 7) -> List[Dict]:
        """Get recent reputation changes"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = [
            e for e in self.reputation_entries[entity_id]
            if e.timestamp > cutoff_date
        ]

        return [
            {
                "date": entry.timestamp.isoformat(),
                "type": entry.reputation_type.value,
                "source": entry.source_type.value,
                "score": entry.score,
                "reason": entry.reason
            }
            for entry in recent_entries[-20:]  # Last 20 changes
        ]

    async def _get_reputation_rank(self, entity_id: str) -> Dict:
        """Get reputation rank information"""
        # This would calculate rank across all entities
        return {
            "overall_rank": 1,  # Placeholder
            "total_entities": 1,  # Placeholder
            "percentile": 100.0  # Placeholder
        }

    async def _get_next_level_requirement(self, current_score: float) -> int:
        """Get score needed for next reputation level"""
        level = self._calculate_reputation_level(current_score)
        level_thresholds = {
            ReputationLevel.HATED: -5000,
            ReputationLevel.HOSTILE: -3000,
            ReputationLevel.UNFRIENDLY: -1500,
            ReputationLevel.NEUTRAL: -500,
            ReputationLevel.INDIFFERENT: 0,
            ReputationLevel.FRIENDLY: 500,
            ReputationLevel.HONORED: 1500,
            ReputationLevel.REVERED: 3000,
            ReputationLevel.EXALTED: 5000,
            ReputationLevel.LEGENDARY: 8000,
            ReputationLevel.MYTHIC: 10000
        }

        current_threshold = level_thresholds.get(level, 0)
        all_levels = sorted(set(level_thresholds.values()))
        current_index = all_levels.index(current_threshold)

        if current_index < len(all_levels) - 1:
            next_threshold = all_levels[current_index + 1]
            return next_threshold - current_score

        return 0  # Already at max level

    async def _get_entity_name(self, entity_id: str) -> str:
        """Get entity name by ID"""
        # This would integrate with your entity database
        return f"Entity_{entity_id[:8]}"  # Placeholder

    # Trust calculation methods (simplified)

    async def _calculate_consistency_score(self, entity_id: str) -> float:
        """Calculate consistency score based on behavior patterns"""
        return 0.8  # Placeholder

    async def _calculate_reliability_score(self, entity_id: str) -> float:
        """Calculate reliability score based on commitment completion"""
        return 0.7  # Placeholder

    async def _calculate_honesty_score(self, entity_id: str) -> float:
        """Calculate honesty score based on truthfulness"""
        return 0.9  # Placeholder

    async def _calculate_fairness_score(self, entity_id: str) -> float:
        """Calculate fairness score based on equitable treatment"""
        return 0.75  # Placeholder

    async def _calculate_helpfulness_score(self, entity_id: str) -> float:
        """Calculate helpfulness score based on assisting others"""
        helpful_behaviors = [b for b in self.behavior_records.get(entity_id, [])
                           if b.behavior_type == BehaviorType.HELPFUL]
        if not helpful_behaviors:
            return 0.5

        return min(1.0, len(helpful_behaviors) / 10.0)  # Scale based on helpful acts

    async def _calculate_communication_score(self, entity_id: str) -> float:
        """Calculate communication score based on positive communication"""
        return 0.8  # Placeholder

    async def _calculate_respect_score(self, entity_id: str) -> float:
        """Calculate respect score based on respectful interactions"""
        toxic_behaviors = [b for b in self.behavior_records.get(entity_id, [])
                          if b.behavior_type == BehaviorType.TOXIC]
        if toxic_behaviors:
            return max(0.0, 1.0 - len(toxic_behaviors) * 0.2)
        return 0.9

    async def _calculate_integrity_score(self, entity_id: str) -> float:
        """Calculate integrity score based on principle adherence"""
        cheating_behaviors = [b for b in self.behavior_records.get(entity_id, [])
                            if b.behavior_type == BehaviorType.CHEATING]
        if cheating_behaviors:
            return max(0.0, 1.0 - len(cheating_behaviors) * 0.5)
        return 0.95

    async def _calculate_generosity_score(self, entity_id: str) -> float:
        """Calculate generosity score based on giving to others"""
        return 0.6  # Placeholder

    async def _calculate_responsibility_score(self, entity_id: str) -> float:
        """Calculate responsibility score based on accountability"""
        return 0.85  # Placeholder

    async def _update_trust_score(self, entity_id: str):
        """Update trust score for entity"""
        await self.calculate_trust_score(entity_id)

    async def _apply_reward(self, entity_id: str, reward: Dict):
        """Apply a reputation reward"""
        # This would integrate with your reward system
        pass

    async def _apply_penalty(self, entity_id: str, penalty: Dict):
        """Apply a reputation penalty"""
        # This would integrate with your penalty system
        pass

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Reputation decay task
        self._background_tasks.append(
            asyncio.create_task(self._reputation_decay_task())
        )

        # Trust score calculation task
        self._background_tasks.append(
            asyncio.create_task(self._trust_score_calculation_task())
        )

    async def stop_background_tasks(self):
        """Stop background maintenance tasks"""
        self._running = False

        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()

    async def _reputation_decay_task(self):
        """Periodic reputation decay"""
        while self._running:
            try:
                if self.reputation_decay_enabled:
                    await self.apply_reputation_decay()

                await asyncio.sleep(86400)  # Daily

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in reputation decay task: {e}")
                await asyncio.sleep(3600)

    async def _trust_score_calculation_task(self):
        """Periodic trust score recalculation"""
        while self._running:
            try:
                # Recalculate trust scores for active entities
                for entity_id in list(self.trust_scores.keys()):
                    await self.calculate_trust_score(entity_id)

                await asyncio.sleep(self.config["trust_calculation_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in trust score calculation task: {e}")
                await asyncio.sleep(600)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize reputation system
        rep_system = ReputationSystem()

        # Start background tasks
        await rep_system.start_background_tasks()

        # Add some reputation entries
        await rep_system.add_reputation(
            "player1",
            ReputationType.QUESTING,
            "system",
            ReputationSource.QUEST_COMPLETION,
            100.0,
            "Completed the Dragon Slayer quest"
        )

        await rep_system.add_reputation(
            "player1",
            ReputationType.HELPING,
            "player2",
            ReputationSource.HELPING_OTHERS,
            50.0,
            "Helped with a difficult dungeon"
        )

        await rep_system.add_reputation(
            "player2",
            ReputationType.TRADING,
            "player1",
            ReputationSource.TRADE_SUCCESS,
            25.0,
            "Successful trade transaction"
        )

        # Rate a player
        await rep_system.rate_player(
            "player1",
            "player2",
            4.5,
            {"fairness": 5.0, "skill": 4.0, "communication": 4.5},
            "Great player to work with!",
            ["helpful", "skilled"],
            "dungeon_crawl"
        )

        # Set faction reputation
        await rep_system.set_faction_reputation(
            "player1",
            "stormwind_guard",
            "Stormwind Guard",
            1500.0
        )

        # Record behavior
        await rep_system.record_behavior(
            "player1",
            BehaviorType.HELPFUL,
            "Helped new player with tutorial",
            0.7
        )

        # Calculate trust score
        trust_result = await rep_system.calculate_trust_score("player1")
        print(f"Trust score for player1: {trust_result['trust_score']:.3f}")

        # Get reputation summary
        summary = await rep_system.get_reputation_summary("player1")
        print(f"Reputation summary for player1: {summary['summary']['reputation_scores']}")

        # Get faction benefits
        benefits = await rep_system.get_faction_benefits("player1", "stormwind_guard")
        print(f"Faction benefits: {benefits}")

        # Get leaderboard
        leaderboard = await rep_system.get_reputation_leaderboard(ReputationType.QUESTING)
        print(f"Questing leaderboard: {len(leaderboard['leaderboard'])} players")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await rep_system.stop_background_tasks()

    asyncio.run(main())