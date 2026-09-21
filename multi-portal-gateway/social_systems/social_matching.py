#!/usr/bin/env python3
"""
DMLogn8n Social Matching - Intelligent Matchmaking and Group Formation System

Handles intelligent matchmaking algorithms, player compatibility analysis, group formation,
activity pairing, social connection recommendations, and collaborative play matching.

Features:
- Multi-factor compatibility analysis
- Intelligent matchmaking algorithms
- Group formation optimization
- Activity-based matching
- Social compatibility scoring
- Dynamic preference learning
- Match quality prediction
- Cross-server matching
- Matchmaking analytics
- Feedback-driven improvements
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
import statistics

class MatchType(Enum):
    """Types of matches"""
    PARTY = "party"
    GUILD = "guild"
    DUNGEON = "dungeon"
    RAID = "raid"
    PVP = "pvp"
    QUEST = "quest"
    TRADING = "trading"
    MENTORING = "mentoring"
    FRIENDSHIP = "friendship"
    COLLABORATION = "collaboration"
    ACTIVITY_PARTNER = "activity_partner"
    TEAM = "team"
    TUTORIAL = "tutorial"

class MatchingCriteria(Enum):
    """Criteria used for matching"""
    SKILL_LEVEL = "skill_level"
    PLAYSTYLE = "playstyle"
    AVAILABILITY = "availability"
    TIMEZONE = "timezone"
    LANGUAGE = "language"
    AGE_GROUP = "age_group"
    EXPERIENCE = "experience"
    PERSONALITY = "personality"
    GOALS = "goals"
    INTERESTS = "interests"
    ACTIVITY_PREFERENCES = "activity_preferences"
    SOCIAL_COMPATIBILITY = "social_compatibility"
    REPUTATION = "reputation"
    GUILD_AFFILIATION = "guild_affiliation"

class MatchStatus(Enum):
    """Status of matches"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"

class FeedbackType(Enum):
    """Types of feedback for matches"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    INAPPROPRIATE = "inappropriate"
    TECHNICAL_ISSUE = "technical_issue"
    MISMATCH = "mismatch"
    EXCELLENT = "excellent"
    POOR = "poor"

@dataclass
class PlayerProfile:
    """Player profile for matchmaking"""
    player_id: str
    name: str
    level: int
    class_type: str
    skill_rating: float = 0.0
    playstyle: List[str] = field(default_factory=list)
    timezone: str = "UTC"
    languages: List[str] = field(default_factory=list)
    availability: Dict[str, List[str]] = field(default_factory=dict)  # day -> time ranges
    preferences: Dict[str, Any] = field(default_factory=dict)
    personality_traits: Dict[str, float] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    reputation_score: float = 0.5
    guild_id: Optional[str] = None
    last_active: datetime = field(default_factory=datetime.now)
    created_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MatchRequest:
    """Request for matchmaking"""
    id: str
    requester_id: str
    match_type: MatchType
    criteria: Dict[MatchingCriteria, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1-5
    max_matches: int = 5
    expires_date: Optional[datetime] = None
    created_date: datetime = field(default_factory=datetime.now)
    status: MatchStatus = MatchStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Match:
    """Generated match between players"""
    id: str
    match_type: MatchType
    participants: List[str]
    compatibility_score: float
    match_quality: str  # excellent, good, fair, poor
    criteria_satisfaction: Dict[MatchingCriteria, float] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    expires_date: Optional[datetime] = None
    status: MatchStatus = MatchStatus.PENDING
    response_deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MatchFeedback:
    """Feedback on a completed match"""
    id: str
    match_id: str
    participant_id: str
    feedback_type: FeedbackType
    rating: float  # 1-5
    comments: str = ""
    issues: List[str] = field(default_factory=list)
    would_match_again: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MatchingAlgorithm:
    """Matching algorithm configuration"""
    name: str
    description: str
    enabled: bool = True
    weight_config: Dict[MatchingCriteria, float] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    custom_logic: str = ""
    success_rate: float = 0.0
    usage_count: int = 0

class SocialMatchingSystem:
    """Main social matching system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.match_requests: Dict[str, MatchRequest] = {}
        self.matches: Dict[str, Match] = {}
        self.match_feedback: Dict[str, List[MatchFeedback]] = defaultdict(list)
        self.matching_algorithms: Dict[str, MatchingAlgorithm] = {}

        # Matching queues
        self.matching_queues: Dict[MatchType, List[str]] = defaultdict(list)  # match_type -> request_ids
        self.active_matches: Dict[str, Set[str]] = defaultdict(set)  # match_id -> participant_ids

        # Analytics and learning
        self.match_success_rates: Dict[str, float] = {}
        self.player_success_rates: Dict[str, float] = {}
        self.criteria_effectiveness: Dict[MatchingCriteria, float] = {}
        self.pattern_recognition: Dict[str, Dict] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_queue_wait_time": 1800,  # 30 minutes
            "default_match_expires": 3600,  # 1 hour
            "feedback_requirement_rate": 0.8,  # 80% of matches require feedback
            "min_compatibility_score": 0.3,
            "max_matches_per_request": 10,
            "match_request_timeout": 3600,  # 1 hour
            "profile_update_interval": 86400,  # 24 hours
            "matching_interval": 30,  # seconds
            "learning_enabled": True,
            "cross_server_matching": False,
            "quality_threshold": 0.5,
            "diversity_factor": 0.2,
            "new_player_bonus": 0.1,
            "guild_member_bonus": 0.15,
            "feedback_weight": 0.3
        }

    async def create_player_profile(self, player_id: str, profile_data: Dict) -> Dict:
        """Create or update a player profile for matchmaking"""
        try:
            # Create or update profile
            profile = PlayerProfile(
                player_id=player_id,
                name=profile_data["name"],
                level=profile_data.get("level", 1),
                class_type=profile_data.get("class_type", "warrior"),
                skill_rating=profile_data.get("skill_rating", 0.0),
                playstyle=profile_data.get("playstyle", []),
                timezone=profile_data.get("timezone", "UTC"),
                languages=profile_data.get("languages", ["en"]),
                availability=profile_data.get("availability", {}),
                preferences=profile_data.get("preferences", {}),
                personality_traits=profile_data.get("personality_traits", {}),
                interests=profile_data.get("interests", []),
                goals=profile_data.get("goals", []),
                reputation_score=profile_data.get("reputation_score", 0.5),
                guild_id=profile_data.get("guild_id"),
                metadata=profile_data.get("metadata", {})
            )

            # Update or store profile
            existing_profile = self.player_profiles.get(player_id)
            if existing_profile:
                # Preserve some fields from existing profile
                profile.created_date = existing_profile.created_date
                profile.success_count = getattr(existing_profile, 'success_count', 0)
                profile.total_matches = getattr(existing_profile, 'total_matches', 0)

            self.player_profiles[player_id] = profile

            self.logger.info(f"Player profile created/updated for {player_id}")

            return {
                "success": True,
                "player_id": player_id,
                "profile": asdict(profile),
                "message": "Player profile updated successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating player profile: {e}")
            return {"success": False, "error": str(e)}

    async def submit_match_request(self, requester_id: str, match_type: MatchType,
                                 criteria: Dict[MatchingCriteria, Any] = None,
                                 preferences: Dict = None, constraints: Dict = None) -> Dict:
        """Submit a matchmaking request"""
        try:
            # Validate player profile exists
            if requester_id not in self.player_profiles:
                return {"success": False, "error": "Player profile not found"}

            # Check for existing requests
            existing_requests = [
                req for req in self.match_requests.values()
                if req.requester_id == requester_id and req.match_type == match_type
                and req.status in [MatchStatus.PENDING, MatchStatus.IN_PROGRESS]
            ]

            if existing_requests:
                return {"success": False, "error": "Already have an active request for this match type"}

            # Create match request
            request = MatchRequest(
                id=str(uuid.uuid4()),
                requester_id=requester_id,
                match_type=match_type,
                criteria=criteria or {},
                preferences=preferences or {},
                constraints=constraints or {},
                priority=preferences.get("priority", 1),
                max_matches=preferences.get("max_matches", 5),
                expires_date=datetime.now() + timedelta(seconds=self.config["match_request_timeout"])
            )

            # Store request
            self.match_requests[request.id] = request
            self.matching_queues[match_type].append(request.id)

            self.logger.info(f"Match request submitted: {request.id} by {requester_id} for {match_type.value}")

            return {
                "success": True,
                "request_id": request.id,
                "estimated_wait_time": await self._estimate_wait_time(match_type),
                "message": f"Match request submitted for {match_type.value}"
            }

        except Exception as e:
            self.logger.error(f"Error submitting match request: {e}")
            return {"success": False, "error": str(e)}

    async def find_matches(self, request_id: str) -> Dict:
        """Find matches for a specific request"""
        try:
            if request_id not in self.match_requests:
                return {"success": False, "error": "Match request not found"}

            request = self.match_requests[request_id]

            # Check if request is still valid
            if request.status != MatchStatus.PENDING:
                return {"success": False, "error": "Request is no longer active"}

            if datetime.now() > request.expires_date:
                request.status = MatchStatus.EXPIRED
                return {"success": False, "error": "Request has expired"}

            # Find potential matches
            potential_matches = await self._find_potential_matches(request)

            if not potential_matches:
                return {
                    "success": True,
                    "matches": [],
                    "message": "No suitable matches found at this time"
                }

            # Validate and filter matches
            valid_matches = []
            for match_candidate in potential_matches:
                if await self._validate_match_candidate(request, match_candidate):
                    valid_matches.append(match_candidate)

            # Sort by compatibility score
            valid_matches.sort(key=lambda m: m.compatibility_score, reverse=True)

            # Limit to max_matches
            valid_matches = valid_matches[:request.max_matches]

            # Create match objects
            matches = []
            for match_candidate in valid_matches:
                match = Match(
                    id=str(uuid.uuid4()),
                    match_type=request.match_type,
                    participants=match_candidate.participants,
                    compatibility_score=match_candidate.compatibility_score,
                    match_quality=await self._determine_match_quality(match_candidate.compatibility_score),
                    criteria_satisfaction=match_candidate.criteria_satisfaction,
                    reasoning=match_candidate.reasoning,
                    created_date=datetime.now(),
                    expires_date=datetime.now() + timedelta(seconds=self.config["default_match_expires"]),
                    response_deadline=datetime.now() + timedelta(seconds=1800),  # 30 minutes
                    metadata=match_candidate.metadata
                )
                matches.append(match)
                self.matches[match.id] = match

            # Update request status
            if matches:
                request.status = MatchStatus.IN_PROGRESS

            self.logger.info(f"Found {len(matches)} matches for request {request_id}")

            return {
                "success": True,
                "request_id": request_id,
                "matches": [asdict(match) for match in matches],
                "total_found": len(matches),
                "message": f"Found {len(matches)} potential matches"
            }

        except Exception as e:
            self.logger.error(f"Error finding matches: {e}")
            return {"success": False, "error": str(e)}

    async def respond_to_match(self, player_id: str, match_id: str, response: str) -> Dict:
        """Respond to a match proposal"""
        try:
            if match_id not in self.matches:
                return {"success": False, "error": "Match not found"}

            match = self.matches[match_id]

            # Check if player is part of this match
            if player_id not in match.participants:
                return {"success": False, "error": "Not a participant in this match"}

            # Check if match is still pending
            if match.status != MatchStatus.PENDING:
                return {"success": False, "error": "Match is no longer pending"}

            # Check if response deadline has passed
            if match.response_deadline and datetime.now() > match.response_deadline:
                match.status = MatchStatus.EXPIRED
                return {"success": False, "error": "Match response deadline has passed"}

            # Record response
            if "responses" not in match.metadata:
                match.metadata["responses"] = {}

            match.metadata["responses"][player_id] = {
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

            # Check if all participants have responded
            total_responses = len(match.metadata["responses"])
            if total_responses == len(match.participants):
                # Analyze responses and determine outcome
                positive_responses = sum(1 for r in match.metadata["responses"].values() if r["response"].lower() in ["accept", "yes", "okay"])

                if positive_responses == len(match.participants):
                    # Everyone accepted
                    match.status = MatchStatus.ACCEPTED
                    await self._finalize_match(match_id)
                elif positive_responses == 0:
                    # Everyone rejected
                    match.status = MatchStatus.REJECTED
                else:
                    # Mixed responses - could proceed with subset or cancel
                    if positive_responses >= 2:  # Minimum for most activities
                        match.status = MatchStatus.ACCEPTED
                        await self._finalize_match(match_id, [p for p in match.participants
                                                     if match.metadata["responses"].get(p, {}).get("response", "").lower() in ["accept", "yes", "okay"]])
                    else:
                        match.status = MatchStatus.CANCELLED

            self.logger.info(f"Player {player_id} responded '{response}' to match {match_id}")

            return {
                "success": True,
                "match_id": match_id,
                "status": match.status.value,
                "message": f"Response recorded for match {match_id}"
            }

        except Exception as e:
            self.logger.error(f"Error responding to match: {e}")
            return {"success": False, "error": str(e)}

    async def submit_match_feedback(self, match_id: str, participant_id: str, feedback_type: FeedbackType,
                                   rating: float, comments: str = "", issues: List[str] = None) -> Dict:
        """Submit feedback for a completed match"""
        try:
            if match_id not in self.matches:
                return {"success": False, "error": "Match not found"}

            match = self.matches[match_id]

            # Check if participant was in the match
            if participant_id not in match.participants:
                return {"success": False, "error": "Not a participant in this match"}

            # Check if match is completed
            if match.status not in [MatchStatus.ACCEPTED, MatchStatus.COMPLETED]:
                return {"success": False, "error": "Match is not completed"}

            # Create feedback
            feedback = MatchFeedback(
                id=str(uuid.uuid4()),
                match_id=match_id,
                participant_id=participant_id,
                feedback_type=feedback_type,
                rating=max(1.0, min(5.0, rating)),
                comments=comments,
                issues=issues or [],
                would_match_again=rating >= 4.0,
                metadata={
                    "match_quality": match.match_quality,
                    "compatibility_score": match.compatibility_score
                }
            )

            # Store feedback
            self.match_feedback[match_id].append(feedback)

            # Update learning metrics
            await self._update_learning_metrics(match_id, feedback)

            self.logger.info(f"Feedback submitted for match {match_id} by {participant_id}")

            return {
                "success": True,
                "feedback_id": feedback.id,
                "message": "Feedback submitted successfully"
            }

        except Exception as e:
            self.logger.error(f"Error submitting match feedback: {e}")
            return {"success": False, "error": str(e)}

    async def get_player_matches(self, player_id: str, status_filter: Optional[MatchStatus] = None,
                               limit: int = 20) -> Dict:
        """Get matches for a player"""
        try:
            player_matches = []

            for match in self.matches.values():
                if player_id in match.participants:
                    # Apply status filter if provided
                    if status_filter and match.status != status_filter:
                        continue

                    match_info = {
                        "id": match.id,
                        "match_type": match.match_type.value,
                        "status": match.status.value,
                        "participants": match.participants,
                        "compatibility_score": match.compatibility_score,
                        "match_quality": match.match_quality,
                        "created_date": match.created_date.isoformat(),
                        "expires_date": match.expires_date.isoformat() if match.expires_date else None,
                        "reasoning": match.reasoning
                    }
                    player_matches.append(match_info)

            # Sort by creation date (most recent first)
            player_matches.sort(key=lambda x: x["created_date"], reverse=True)

            # Apply limit
            player_matches = player_matches[:limit]

            return {
                "success": True,
                "matches": player_matches,
                "total_count": len(player_matches)
            }

        except Exception as e:
            self.logger.error(f"Error getting player matches: {e}")
            return {"success": False, "error": str(e)}

    async def get_matchmaking_stats(self, player_id: Optional[str] = None) -> Dict:
        """Get matchmaking statistics"""
        try:
            stats = {
                "total_matches": len(self.matches),
                "active_matches": len([m for m in self.matches.values() if m.status == MatchStatus.ACCEPTED]),
                "pending_requests": len(self.match_requests),
                "success_rate": 0.0,
                "average_wait_time": 0.0,
                "popular_match_types": {},
                "criteria_effectiveness": {}
            }

            # Calculate success rate
            completed_matches = [m for m in self.matches.values() if m.status == MatchStatus.COMPLETED]
            if completed_matches:
                successful_matches = 0
                for match in completed_matches:
                    feedback = self.match_feedback.get(match.id, [])
                    if feedback:
                        avg_rating = sum(f.rating for f in feedback) / len(feedback)
                        if avg_rating >= 3.0:
                            successful_matches += 1

                stats["success_rate"] = successful_matches / len(completed_matches)

            # Calculate popular match types
            match_type_counts = defaultdict(int)
            for match in self.matches.values():
                match_type_counts[match.match_type.value] += 1

            total_matches = len(self.matches)
            if total_matches > 0:
                stats["popular_match_types"] = {
                    match_type: count / total_matches
                    for match_type, count in match_type_counts.items()
                }

            # Add player-specific stats if provided
            if player_id:
                player_stats = await self._get_player_matchmaking_stats(player_id)
                stats.update(player_stats)

            return {
                "success": True,
                "statistics": stats
            }

        except Exception as e:
            self.logger.error(f"Error getting matchmaking stats: {e}")
            return {"success": False, "error": str(e)}

    async def update_matching_algorithm(self, algorithm_name: str, config: Dict) -> Dict:
        """Update or create a matching algorithm configuration"""
        try:
            algorithm = MatchingAlgorithm(
                name=algorithm_name,
                description=config.get("description", ""),
                enabled=config.get("enabled", True),
                weight_config={
                    MatchingCriteria(key): value
                    for key, value in config.get("weights", {}).items()
                    if key in [c.value for c in MatchingCriteria]
                },
                thresholds=config.get("thresholds", {}),
                custom_logic=config.get("custom_logic", "")
            )

            self.matching_algorithms[algorithm_name] = algorithm

            self.logger.info(f"Matching algorithm '{algorithm_name}' updated")

            return {
                "success": True,
                "algorithm_name": algorithm_name,
                "message": f"Matching algorithm '{algorithm_name}' updated successfully"
            }

        except Exception as e:
            self.logger.error(f"Error updating matching algorithm: {e}")
            return {"success": False, "error": str(e)}

    # Core matching logic

    async def _find_potential_matches(self, request: MatchRequest) -> List[Dict]:
        """Find potential matches for a request"""
        potential_matches = []

        # Get requester profile
        requester_profile = self.player_profiles.get(request.requester_id)
        if not requester_profile:
            return potential_matches

        # Find other players looking for matches
        candidate_requests = [
            req for req in self.match_requests.values()
            if (req.id != request.id and
                req.match_type == request.match_type and
                req.status == MatchStatus.PENDING and
                req.requester_id in self.player_profiles)
        ]

        # Check for solo match (just the requester)
        if await self._can_solo_match(request):
            solo_match = await self._create_solo_match(request)
            if solo_match:
                potential_matches.append(solo_match)

        # Check group matches
        group_candidates = await self._find_group_candidates(request, candidate_requests, requester_profile)
        potential_matches.extend(group_candidates)

        return potential_matches

    async def _find_group_candidates(self, request: MatchRequest, candidate_requests: List[MatchRequest],
                                   requester_profile: PlayerProfile) -> List[Dict]:
        """Find group match candidates"""
        candidates = []

        # Determine optimal group size for match type
        optimal_size = await self._get_optimal_group_size(request.match_type)

        # Try different group combinations
        for group_size in range(2, min(optimal_size + 1, len(candidate_requests) + 2)):
            group_candidates = await self._evaluate_group_combinations(
                request, candidate_requests, requester_profile, group_size
            )
            candidates.extend(group_candidates)

        return candidates

    async def _evaluate_group_combinations(self, request: MatchRequest, candidate_requests: List[MatchRequest],
                                        requester_profile: PlayerProfile, group_size: int) -> List[Dict]:
        """Evaluate combinations of players for group matching"""
        combinations = []

        # Create combinations including requester
        all_participants = [request] + candidate_requests

        # Generate combinations (simplified - would use more sophisticated combinatorial algorithms)
        for i in range(len(all_participants)):
            for j in range(i + 1, min(i + group_size - 1, len(all_participants))):
                participants = [all_participants[i]] + all_participants[i + 1:j + 1]

                if len(participants) == group_size:
                    # Evaluate this combination
                    compatibility_score, criteria_satisfaction, reasoning = await self._evaluate_compatibility(
                        participants, request.match_type
                    )

                    if compatibility_score >= self.config["min_compatibility_score"]:
                        combinations.append({
                            "participants": [p.requester_id for p in participants],
                            "compatibility_score": compatibility_score,
                            "criteria_satisfaction": criteria_satisfaction,
                            "reasoning": reasoning,
                            "metadata": {
                                "group_size": group_size,
                                "evaluation_details": await self._get_evaluation_details(participants)
                            }
                        })

        return combinations

    async def _evaluate_compatibility(self, participants: List[MatchRequest], match_type: MatchType) -> Tuple[float, Dict, List[str]]:
        """Evaluate compatibility between participants"""
        participant_profiles = [
            self.player_profiles[p.requester_id] for p in participants
            if p.requester_id in self.player_profiles
        ]

        if len(participant_profiles) < 2:
            return 1.0, {}, ["Solo match"]

        # Get algorithm configuration
        algorithm = self.matching_algorithms.get("default", MatchingAlgorithm("default", ""))
        weights = algorithm.weight_config

        # Calculate compatibility scores for each criteria
        criteria_scores = {}
        reasoning = []

        # Skill level compatibility
        skill_levels = [p.skill_rating for p in participant_profiles]
        skill_std = statistics.stdev(skill_levels) if len(skill_levels) > 1 else 0
        skill_compatibility = max(0, 1 - skill_std)  # Lower deviation = higher compatibility
        criteria_scores[MatchingCriteria.SKILL_LEVEL] = skill_compatibility
        if skill_compatibility > 0.8:
            reasoning.append("Similar skill levels")

        # Playstyle compatibility
        playstyle_compatibility = await self._calculate_playstyle_compatibility(participant_profiles)
        criteria_scores[MatchingCriteria.PLAYSTYLE] = playstyle_compatibility
        if playstyle_compatibility > 0.7:
            reasoning.append("Compatible playstyles")

        # Availability compatibility
        availability_compatibility = await self._calculate_availability_compatibility(participant_profiles)
        criteria_scores[MatchingCriteria.AVAILABILITY] = availability_compatibility
        if availability_compatibility > 0.6:
            reasoning.append("Compatible schedules")

        # Social compatibility
        social_compatibility = await self._calculate_social_compatibility(participant_profiles)
        criteria_scores[MatchingCriteria.SOCIAL_COMPATIBILITY] = social_compatibility
        if social_compatibility > 0.7:
            reasoning.append("Socially compatible")

        # Calculate weighted overall score
        total_score = 0.0
        total_weight = 0.0
        for criteria, score in criteria_scores.items():
            weight = weights.get(criteria, 1.0)
            total_score += score * weight
            total_weight += weight

        overall_score = total_score / total_weight if total_weight > 0 else 0.0

        # Apply bonuses
        overall_score += await self._apply_compatibility_bonuses(participants, match_type)

        return min(1.0, overall_score), criteria_scores, reasoning

    async def _calculate_playstyle_compatibility(self, profiles: List[PlayerProfile]) -> float:
        """Calculate playstyle compatibility between players"""
        # Jaccard similarity for playstyles
        all_playstyles = set()
        for profile in profiles:
            all_playstyles.update(profile.playstyle)

        if not all_playstyles:
            return 0.5

        # Calculate average overlap
        total_overlap = 0
        comparisons = 0

        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                set1 = set(profiles[i].playstyle)
                set2 = set(profiles[j].playstyle)

                if set1 or set2:
                    overlap = len(set1.intersection(set2)) / len(set1.union(set2))
                    total_overlap += overlap
                    comparisons += 1

        return total_overlap / comparisons if comparisons > 0 else 0.5

    async def _calculate_availability_compatibility(self, profiles: List[PlayerProfile]) -> float:
        """Calculate availability compatibility between players"""
        # Simplified - check if players have overlapping time slots
        common_slots = 0
        total_slots = 0

        # Check each day of the week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in days:
            day_slots = []
            for profile in profiles:
                if day in profile.availability:
                    day_slots.extend(profile.availability[day])

            if day_slots:
                # Find overlapping hours (simplified)
                all_hours = set(range(24))
                available_hours = set()
                for slot in day_slots:
                    # Parse time slot (e.g., "18:00-22:00")
                    try:
                        start, end = slot.split("-")
                        start_hour = int(start.split(":")[0])
                        end_hour = int(end.split(":")[0])
                        available_hours.update(range(start_hour, end_hour))
                    except:
                        continue

                overlap_ratio = len(available_hours) / 24
                common_slots += overlap_ratio
                total_slots += 1

        return common_slots / total_slots if total_slots > 0 else 0.3

    async def _calculate_social_compatibility(self, profiles: List[PlayerProfile]) -> float:
        """Calculate social compatibility between players"""
        if len(profiles) < 2:
            return 0.8

        compatibility = 0.5  # Base compatibility

        # Language compatibility
        languages = [set(p.languages) for p in profiles]
        common_languages = set.intersection(*languages) if languages else set()
        if common_languages:
            compatibility += 0.2

        # Interest compatibility
        interests = [set(p.interests) for p in profiles]
        common_interests = set.intersection(*interests) if interests else set()
        if common_interests:
            compatibility += 0.15

        # Reputation compatibility
        reputations = [p.reputation_score for p in profiles]
        if reputations:
            avg_reputation = sum(reputations) / len(reputations)
            if avg_reputation > 0.7:
                compatibility += 0.15

        return min(1.0, compatibility)

    async def _apply_compatibility_bonuses(self, participants: List[MatchRequest], match_type: MatchType) -> float:
        """Apply compatibility bonuses"""
        bonus = 0.0

        # New player bonus
        new_players = 0
        for participant in participants:
            profile = self.player_profiles.get(participant.requester_id)
            if profile and (datetime.now() - profile.created_date).days < 7:
                new_players += 1

        if new_players > 0:
            bonus += self.config["new_player_bonus"] * new_players

        # Guild member bonus
        guild_ids = set()
        for participant in participants:
            profile = self.player_profiles.get(participant.requester_id)
            if profile and profile.guild_id:
                guild_ids.add(profile.guild_id)

        if len(guild_ids) == 1:  # All from same guild
            bonus += self.config["guild_member_bonus"]

        return bonus

    async def _validate_match_candidate(self, request: MatchRequest, candidate: Dict) -> bool:
        """Validate if a match candidate is suitable"""
        # Check constraints
        for constraint, value in request.constraints.items():
            if not await self._meets_constraint(candidate, constraint, value):
                return False

        # Check if participants are still available
        for participant_id in candidate["participants"]:
            participant_profile = self.player_profiles.get(participant_id)
            if not participant_profile:
                return False

            # Check if player is already in an active match
            if await self._is_player_in_active_match(participant_id):
                return False

        return True

    async def _determine_match_quality(self, compatibility_score: float) -> str:
        """Determine match quality based on compatibility score"""
        if compatibility_score >= 0.9:
            return "excellent"
        elif compatibility_score >= 0.7:
            return "good"
        elif compatibility_score >= 0.5:
            return "fair"
        else:
            return "poor"

    async def _estimate_wait_time(self, match_type: MatchType) -> int:
        """Estimate wait time for match type (in seconds)"""
        # Calculate based on current queue length and historical data
        queue_length = len(self.matching_queues[match_type])
        avg_time_per_match = 300  # 5 minutes average

        return queue_length * avg_time_per_match

    async def _get_optimal_group_size(self, match_type: MatchType) -> int:
        """Get optimal group size for match type"""
        size_map = {
            MatchType.PARTY: 4,
            MatchType.DUNGEON: 5,
            MatchType.RAID: 10,
            MatchType.PVP: 4,
            MatchType.QUEST: 3,
            MatchType.GUILD: 1,  # Individual matching
            MatchType.FRIENDSHIP: 2,
            MatchType.MENTORING: 2,
            MatchType.COLLABORATION: 5,
            MatchType.TEAM: 6
        }
        return size_map.get(match_type, 4)

    async def _can_solo_match(self, request: MatchType) -> bool:
        """Check if request can be satisfied solo"""
        solo_match_types = [MatchType.FRIENDSHIP, MatchType.MENTORING, MatchType.GUILD]
        return request.match_type in solo_match_types

    async def _create_solo_match(self, request: MatchRequest) -> Optional[Dict]:
        """Create a solo match if applicable"""
        if not await self._can_solo_match(request):
            return None

        return {
            "participants": [request.requester_id],
            "compatibility_score": 1.0,
            "criteria_satisfaction": {},
            "reasoning": ["Solo match"],
            "metadata": {"match_type": "solo"}
        }

    async def _finalize_match(self, match_id: str, accepted_participants: List[str] = None):
        """Finalize an accepted match"""
        match = self.matches[match_id]

        # Update participants if subset accepted
        if accepted_participants:
            match.participants = accepted_participants

        # Add to active matches
        for participant_id in match.participants:
            self.active_matches[match_id].add(participant_id)

        # Clean up related requests
        for participant_id in match.participants:
            for request in self.match_requests.values():
                if request.requester_id == participant_id and request.match_type == match.match_type:
                    request.status = MatchStatus.COMPLETED

    async def _update_learning_metrics(self, match_id: str, feedback: MatchFeedback):
        """Update learning metrics from feedback"""
        if not self.config["learning_enabled"]:
            return

        # Update player success rates
        if feedback.participant_id not in self.player_success_rates:
            self.player_success_rates[feedback.participant_id] = 0.0

        current_rate = self.player_success_rates[feedback.participant_id]
        feedback_value = (feedback.rating - 3.0) / 2.0  # Convert 1-5 to -1 to 1
        self.player_success_rates[feedback.participant_id] = current_rate * 0.9 + feedback_value * 0.1

        # Update criteria effectiveness
        match = self.matches.get(match_id)
        if match:
            for criteria, satisfaction in match.criteria_satisfaction.items():
                if criteria not in self.criteria_effectiveness:
                    self.criteria_effectiveness[criteria] = 0.5

                current_effectiveness = self.criteria_effectiveness[criteria]
                # Update based on feedback and criteria satisfaction
                update_value = satisfaction * (feedback.rating / 5.0)
                self.criteria_effectiveness[criteria] = current_effectiveness * 0.95 + update_value * 0.05

    async def _get_player_matchmaking_stats(self, player_id: str) -> Dict:
        """Get player-specific matchmaking statistics"""
        player_matches = [
            match for match in self.matches.values()
            if player_id in match.participants
        ]

        completed_matches = [m for m in player_matches if m.status == MatchStatus.COMPLETED]
        successful_matches = 0
        total_rating = 0.0
        rating_count = 0

        for match in completed_matches:
            feedback_list = self.match_feedback.get(match.id, [])
            player_feedback = [f for f in feedback_list if f.participant_id == player_id]

            for feedback in player_feedback:
                if feedback.rating >= 3.0:
                    successful_matches += 1
                total_rating += feedback.rating
                rating_count += 1

        return {
            "total_matches": len(player_matches),
            "completed_matches": len(completed_matches),
            "successful_matches": successful_matches,
            "success_rate": successful_matches / len(completed_matches) if completed_matches else 0.0,
            "average_rating": total_rating / rating_count if rating_count > 0 else 0.0,
            "most_recent_match": max((m.created_date for m in player_matches), default=None)
        }

    async def _meets_constraint(self, candidate: Dict, constraint: str, value: Any) -> bool:
        """Check if candidate meets a constraint"""
        # Simplified constraint checking
        if constraint == "max_level_difference":
            # Check level difference between participants
            profiles = [self.player_profiles.get(pid) for pid in candidate["participants"]]
            levels = [p.level for p in profiles if p]
            if levels:
                return max(levels) - min(levels) <= value
        elif constraint == "same_guild":
            # Check if all participants are from same guild
            profiles = [self.player_profiles.get(pid) for pid in candidate["participants"]]
            guild_ids = [p.guild_id for p in profiles if p]
            return len(set(guild_ids)) <= 1

        return True

    async def _is_player_in_active_match(self, player_id: str) -> bool:
        """Check if player is in an active match"""
        for match_id, participants in self.active_matches.items():
            if player_id in participants:
                match = self.matches.get(match_id)
                if match and match.status in [MatchStatus.ACCEPTED, MatchStatus.IN_PROGRESS]:
                    return True
        return False

    async def _get_evaluation_details(self, participants: List[MatchRequest]) -> Dict:
        """Get detailed evaluation information for debugging"""
        return {
            "participant_count": len(participants),
            "average_level": sum(self.player_profiles.get(p.requester_id, PlayerProfile("", "", 1)).level
                               for p in participants) / len(participants) if participants else 1,
            "diversity_bonus": self.config["diversity_factor"]
        }

    # Background tasks

    async def start_background_tasks(self):
        """Start background matchmaking tasks"""
        if self._running:
            return

        self._running = True

        # Matching processing task
        self._background_tasks.append(
            asyncio.create_task(self._matching_processing_task())
        )

        # Cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_task())
        )

        # Analytics update task
        self._background_tasks.append(
            asyncio.create_task(self._analytics_update_task())
        )

    async def stop_background_tasks(self):
        """Stop background matchmaking tasks"""
        self._running = False

        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()

    async def _matching_processing_task(self):
        """Process matchmaking queues"""
        while self._running:
            try:
                # Process each queue
                for match_type, request_ids in self.matching_queues.items():
                    # Remove expired requests
                    active_requests = []
                    for request_id in request_ids:
                        request = self.match_requests.get(request_id)
                        if request and request.status == MatchStatus.PENDING and request.expires_date > datetime.now():
                            active_requests.append(request_id)

                    self.matching_queues[match_type] = active_requests

                    # Process requests
                    for request_id in active_requests:
                        await self.find_matches(request_id)

                await asyncio.sleep(self.config["matching_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in matching processing task: {e}")
                await asyncio.sleep(60)

    async def _cleanup_task(self):
        """Clean up expired data"""
        while self._running:
            try:
                current_time = datetime.now()

                # Clean up expired requests
                for request_id, request in list(self.match_requests.items()):
                    if request.expires_date and current_time > request.expires_date:
                        request.status = MatchStatus.EXPIRED

                # Clean up expired matches
                for match_id, match in list(self.matches.items()):
                    if match.expires_date and current_time > match.expires_date and match.status == MatchStatus.PENDING:
                        match.status = MatchStatus.EXPIRED

                # Clean up very old completed matches
                cutoff_date = current_time - timedelta(days=30)
                for match_id in list(self.matches.keys()):
                    match = self.matches[match_id]
                    if (match.status in [MatchStatus.COMPLETED, MatchStatus.REJECTED, MatchStatus.CANCELLED] and
                        match.created_date < cutoff_date):
                        del self.matches[match_id]

                await asyncio.sleep(3600)  # Run hourly

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(600)

    async def _analytics_update_task(self):
        """Update analytics and learning metrics"""
        while self._running:
            try:
                # Update success rates
                await self._update_success_rates()

                # Update pattern recognition
                await self._update_pattern_recognition()

                await asyncio.sleep(1800)  # Run every 30 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in analytics update task: {e}")
                await asyncio.sleep(300)

    async def _update_success_rates(self):
        """Update overall success rates"""
        completed_matches = [m for m in self.matches.values() if m.status == MatchStatus.COMPLETED]

        if completed_matches:
            successful_matches = 0
            for match in completed_matches:
                feedback = self.match_feedback.get(match.id, [])
                if feedback:
                    avg_rating = sum(f.rating for f in feedback) / len(feedback)
                    if avg_rating >= 3.0:
                        successful_matches += 1

            self.match_success_rates["overall"] = successful_matches / len(completed_matches)

    async def _update_pattern_recognition(self):
        """Update pattern recognition data"""
        # This would implement more sophisticated pattern recognition
        # For now, just track basic statistics
        for match_type in MatchType:
            type_matches = [m for m in self.matches.values() if m.match_type == match_type]
            if type_matches:
                avg_score = sum(m.compatibility_score for m in type_matches) / len(type_matches)
                if match_type not in self.pattern_recognition:
                    self.pattern_recognition[match_type.value] = {}
                self.pattern_recognition[match_type.value]["avg_compatibility"] = avg_score

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize social matching system
        matching_system = SocialMatchingSystem()

        # Start background tasks
        await matching_system.start_background_tasks()

        # Create player profiles
        await matching_system.create_player_profile("player1", {
            "name": "Alice",
            "level": 15,
            "class_type": "warrior",
            "skill_rating": 1200,
            "playstyle": ["competitive", "teamwork"],
            "timezone": "UTC",
            "languages": ["en"],
            "availability": {
                "weekend": ["18:00-22:00"],
                "weekday": ["20:00-22:00"]
            },
            "interests": ["pvp", "raids", "adventure"],
            "reputation_score": 0.8
        })

        await matching_system.create_player_profile("player2", {
            "name": "Bob",
            "level": 14,
            "class_type": "mage",
            "skill_rating": 1150,
            "playstyle": ["strategic", "support"],
            "timezone": "UTC",
            "languages": ["en"],
            "availability": {
                "weekend": ["18:00-22:00"],
                "weekday": ["19:00-21:00"]
            },
            "interests": ["pve", "dungeons", "exploration"],
            "reputation_score": 0.7
        })

        await matching_system.create_player_profile("player3", {
            "name": "Charlie",
            "level": 16,
            "class_type": "cleric",
            "skill_rating": 1300,
            "playstyle": ["support", "healing"],
            "timezone": "UTC",
            "languages": ["en"],
            "availability": {
                "weekend": ["15:00-23:00"],
                "weekday": ["18:00-22:00"]
            },
            "interests": ["healing", "raids", "teamwork"],
            "reputation_score": 0.9
        })

        # Submit match requests
        request1 = await matching_system.submit_match_request(
            "player1",
            MatchType.DUNGEON,
            {
                MatchingCriteria.SKILL_LEVEL: "similar",
                MatchingCriteria.AVAILABILITY: "compatible"
            },
            {
                "priority": 2,
                "max_matches": 3
            }
        )
        print(f"Match request submitted: {request1['request_id']}")

        request2 = await matching_system.submit_match_request(
            "player2",
            MatchType.DUNGEON,
            {
                MatchingCriteria.SKILL_LEVEL: "similar",
                MatchingCriteria.PLAYSTYLE: "balanced"
            }
        )
        print(f"Match request submitted: {request2['request_id']}")

        request3 = await matching_system.submit_match_request(
            "player3",
            MatchType.DUNGEON,
            {
                MatchingCriteria.SKILL_LEVEL: "similar",
                MatchingCriteria.AVAILABILITY: "compatible"
            }
        )
        print(f"Match request submitted: {request3['request_id']}")

        # Process matches (normally done by background task)
        if request1["success"]:
            matches = await matching_system.find_matches(request1["request_id"])
            print(f"Found matches: {matches['total_found']}")

            if matches["matches"]:
                match_id = matches["matches"][0]["id"]
                print(f"Match quality: {matches['matches'][0]['match_quality']}")
                print(f"Compatibility score: {matches['matches'][0]['compatibility_score']:.2f}")

                # Respond to match
                response = await matching_system.respond_to_match("player1", match_id, "accept")
                print(f"Response: {response['status']}")

        # Get player matches
        player_matches = await matching_system.get_player_matches("player1")
        print(f"Player1 matches: {player_matches['total_count']}")

        # Get matchmaking stats
        stats = await matching_system.get_matchmaking_stats()
        print(f"Overall success rate: {stats['statistics']['success_rate']:.2%}")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await matching_system.stop_background_tasks()

    asyncio.run(main())