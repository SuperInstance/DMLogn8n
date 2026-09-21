#!/usr/bin/env python3
"""
Strategic Pattern Analyzer for D&D Agent Learning
Extracts and analyzes successful strategies from gameplay data
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter
import asyncio

# Import the CharacterExperience from the LoRA trainer
from agent_dnd_lora_trainer import CharacterExperience

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs/pattern_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StrategicPattern:
    """Represents a discovered strategic pattern"""
    pattern_id: str
    pattern_type: str  # "success", "failure", "improvement"
    situation_keywords: List[str]
    action_sequence: List[str]
    success_rate: float
    frequency: int
    character_classes: List[str]
    level_range: Tuple[int, int]
    skill_requirements: List[str]
    contextual_factors: Dict[str, Any]
    confidence_score: float
    timestamp: datetime

@dataclass
class StrategyRecommendation:
    """Represents a strategy recommendation for an agent"""
    agent_id: str
    situation: str
    recommended_strategy: str
    success_probability: float
    risk_assessment: str
    alternative_strategies: List[str]
    skill_requirements: List[str]
    historical_evidence: List[str]
    confidence: float

class StrategicPatternAnalyzer:
    """
    Analyzes gameplay data to extract successful strategic patterns
    and provide recommendations for agent improvement
    """

    def __init__(self):
        self.pattern_cache: Dict[str, List[StrategicPattern]] = {}
        self.strategy_models: Dict[str, Any] = {}
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        self.topic_model = LatentDirichletAllocation(n_components=10, random_state=42)
        self.pattern_history: Dict[str, List[Dict]] = defaultdict(list)

        # Ensure directories exist
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/patterns").mkdir(parents=True, exist_ok=True)
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models/pattern_analysis").mkdir(parents=True, exist_ok=True)

        logger.info("Strategic Pattern Analyzer initialized")

    async def analyze_agent_experiences(self, agent_id: str, experiences: List[CharacterExperience]) -> List[StrategicPattern]:
        """
        Analyze experiences for a specific agent to identify strategic patterns

        Args:
            agent_id: Agent identifier
            experiences: List of character experiences

        Returns:
            List of discovered strategic patterns
        """
        try:
            logger.info(f"Analyzing {len(experiences)} experiences for agent {agent_id}")

            if len(experiences) < 10:
                logger.warning(f"Insufficient experiences for pattern analysis: {len(experiences)}")
                return []

            # Separate experiences by outcome
            successful = [exp for exp in experiences if exp.success_score > 0.7]
            failed = [exp for exp in experiences if exp.success_score < 0.3]
            mixed = [exp for exp in experiences if 0.3 <= exp.success_score <= 0.7]

            # Analyze different pattern types
            success_patterns = await self._analyze_success_patterns(agent_id, successful)
            failure_patterns = await self._analyze_failure_patterns(agent_id, failed)
            learning_patterns = await self._analyze_learning_patterns(agent_id, mixed)

            # Combine all patterns
            all_patterns = success_patterns + failure_patterns + learning_patterns

            # Filter and rank patterns
            quality_patterns = self._filter_quality_patterns(all_patterns)

            # Cache patterns
            self.pattern_cache[agent_id] = quality_patterns

            # Save pattern analysis
            await self._save_pattern_analysis(agent_id, quality_patterns)

            logger.info(f"Discovered {len(quality_patterns)} strategic patterns for agent {agent_id}")
            return quality_patterns

        except Exception as e:
            logger.error(f"Failed to analyze experiences for agent {agent_id}: {str(e)}")
            return []

    async def _analyze_success_patterns(self, agent_id: str, successful_experiences: List[CharacterExperience]) -> List[StrategicPattern]:
        """Analyze patterns in successful experiences"""
        patterns = []

        if len(successful_experiences) < 3:
            return patterns

        # Group experiences by similarity
        experience_groups = await self._group_similar_experiences(successful_experiences)

        for group_id, group_experiences in experience_groups.items():
            if len(group_experiences) < 2:  # Need multiple similar successes
                continue

            pattern = await self._extract_pattern_from_group(agent_id, group_experiences, "success")
            if pattern:
                patterns.append(pattern)

        return patterns

    async def _analyze_failure_patterns(self, agent_id: str, failed_experiences: List[CharacterExperience]) -> List[StrategicPattern]:
        """Analyze patterns in failed experiences to identify what to avoid"""
        patterns = []

        if len(failed_experiences) < 3:
            return patterns

        # Group failures by similarity
        experience_groups = await self._group_similar_experiences(failed_experiences)

        for group_id, group_experiences in experience_groups.items():
            if len(group_experiences) < 2:
                continue

            pattern = await self._extract_pattern_from_group(agent_id, group_experiences, "failure")
            if pattern:
                patterns.append(pattern)

        return patterns

    async def _analyze_learning_patterns(self, agent_id: str, mixed_experiences: List[CharacterExperience]) -> List[StrategicPattern]:
        """Analyze patterns in mixed-outcome experiences for learning opportunities"""
        patterns = []

        if len(mixed_experiences) < 5:
            return patterns

        # Look for situations where small changes in approach lead to different outcomes
        contextual_patterns = await self._analyze_contextual_sensitivity(mixed_experiences)

        for pattern in contextual_patterns:
            patterns.append(pattern)

        return patterns

    async def _group_similar_experiences(self, experiences: List[CharacterExperience]) -> Dict[str, List[CharacterExperience]]:
        """Group experiences by similarity using clustering"""
        try:
            # Convert experiences to text for vectorization
            experience_texts = []
            for exp in experiences:
                text = f"{exp.situation} {exp.action} {exp.outcome} {', '.join(exp.skills_used)}"
                experience_texts.append(text)

            # Vectorize experiences
            try:
                X = self.vectorizer.fit_transform(experience_texts)
            except ValueError:
                # Handle case where vectorization fails
                logger.warning("Failed to vectorize experiences, using simple grouping")
                return {"group_0": experiences}

            # Cluster experiences
            clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
            cluster_labels = clustering.fit_predict(X.toarray())

            # Group by cluster
            groups = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label == -1:  # Noise points
                    groups["noise"].append(experiences[i])
                else:
                    groups[f"group_{label}"].append(experiences[i])

            return dict(groups)

        except Exception as e:
            logger.error(f"Failed to group similar experiences: {str(e)}")
            return {"default": experiences}

    async def _extract_pattern_from_group(self, agent_id: str, experiences: List[CharacterExperience], pattern_type: str) -> Optional[StrategicPattern]:
        """Extract a strategic pattern from a group of similar experiences"""
        try:
            if len(experiences) < 2:
                return None

            # Calculate pattern metrics
            avg_success_rate = np.mean([exp.success_score for exp in experiences])
            success_rates = [exp.success_score for exp in experiences]

            # Extract common elements
            common_situations = self._find_common_elements([exp.situation for exp in experiences])
            common_actions = self._find_common_elements([exp.action for exp in experiences])
            common_skills = self._find_common_elements([skill for exp in experiences for skill in exp.skills_used])

            # Determine level range
            levels = [exp.level for exp in experiences]
            level_range = (min(levels), max(levels))

            # Get character classes
            character_classes = list(set([exp.character_class for exp in experiences]))

            # Extract contextual factors
            contextual_factors = self._extract_contextual_factors(experiences)

            # Calculate confidence score
            confidence = self._calculate_pattern_confidence(experiences, pattern_type)

            # Generate pattern ID
            pattern_id = f"{agent_id}_{pattern_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(common_situations[0]) % 1000}"

            pattern = StrategicPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                situation_keywords=common_situations,
                action_sequence=common_actions,
                success_rate=avg_success_rate,
                frequency=len(experiences),
                character_classes=character_classes,
                level_range=level_range,
                skill_requirements=common_skills,
                contextual_factors=contextual_factors,
                confidence_score=confidence,
                timestamp=datetime.now()
            )

            return pattern

        except Exception as e:
            logger.error(f"Failed to extract pattern from group: {str(e)}")
            return None

    async def _analyze_contextual_sensitivity(self, mixed_experiences: List[CharacterExperience]) -> List[StrategicPattern]:
        """Analyze how small contextual changes affect outcomes"""
        patterns = []

        # Group by similar situations but different outcomes
        situation_groups = defaultdict(list)
        for exp in mixed_experiences:
            situation_key = self._simplify_situation(exp.situation)
            situation_groups[situation_key].append(exp)

        for situation_key, group_exps in situation_groups.items():
            if len(group_exps) < 3:
                continue

            # Look for patterns where context matters
            contextual_pattern = await self._identify_contextual_pattern(group_exps)
            if contextual_pattern:
                patterns.append(contextual_pattern)

        return patterns

    def _find_common_elements(self, elements: List[str], min_frequency: float = 0.4) -> List[str]:
        """Find elements that appear frequently in the list"""
        if not elements:
            return []

        # Simple keyword extraction
        element_counts = Counter()
        for element in elements:
            words = element.lower().split()
            for word in words:
                if len(word) > 3:  # Ignore very short words
                    element_counts[word] += 1

        threshold = len(elements) * min_frequency
        common_words = [word for word, count in element_counts.items() if count >= threshold]

        # Return the original elements that contain common words
        common_elements = []
        for element in elements:
            if any(word in element.lower() for word in common_words):
                common_elements.append(element)

        return common_elements[:3]  # Return top 3

    def _extract_contextual_factors(self, experiences: List[CharacterExperience]) -> Dict[str, Any]:
        """Extract contextual factors that influence success"""
        factors = {}

        # Time of day effects
        if experiences:
            # Environmental factors
            locations = [exp.context.get("location", "unknown") for exp in experiences]
            location_counts = Counter(locations)
            factors["common_locations"] = location_counts.most_common(3)

            # Social factors
            ally_counts = [len(exp.context.get("allies", [])) for exp in experiences]
            factors["avg_allies"] = np.mean(ally_counts) if ally_counts else 0

            # Resource factors
            resources = [exp.context.get("resources", []) for exp in experiences]
            resource_types = set()
            for resource_list in resources:
                resource_types.update(resource_list)
            factors["available_resources"] = list(resource_types)[:5]

        return factors

    def _calculate_pattern_confidence(self, experiences: List[CharacterExperience], pattern_type: str) -> float:
        """Calculate confidence score for a pattern"""
        confidence = 0.0

        # Base confidence from frequency
        frequency_confidence = min(1.0, len(experiences) / 10.0)
        confidence += frequency_confidence * 0.3

        # Consistency of outcomes
        if pattern_type == "success":
            success_rates = [exp.success_score for exp in experiences]
            consistency = 1.0 - np.std(success_rates)
            confidence += consistency * 0.4
        elif pattern_type == "failure":
            failure_rates = [1.0 - exp.success_score for exp in experiences]
            consistency = 1.0 - np.std(failure_rates)
            confidence += consistency * 0.4

        # Recency bonus
        if experiences:
            most_recent = max([exp.timestamp for exp in experiences])
            days_old = (datetime.now() - most_recent).days
            recency_bonus = max(0, 1.0 - days_old / 30.0)
            confidence += recency_bonus * 0.3

        return min(1.0, confidence)

    def _simplify_situation(self, situation: str) -> str:
        """Simplify situation description for grouping"""
        situation_lower = situation.lower()

        # Extract key themes
        themes = []
        if any(word in situation_lower for word in ["combat", "fight", "battle"]):
            themes.append("combat")
        if any(word in situation_lower for word in ["talk", "negotiate", "social"]):
            themes.append("social")
        if any(word in situation_lower for word in ["trap", "puzzle", "mystery"]):
            themes.append("puzzle")
        if any(word in situation_lower for word in ["magic", "spell"]):
            themes.append("magic")

        return "_".join(themes) if themes else "general"

    async def _identify_contextual_pattern(self, experiences: List[CharacterExperience]) -> Optional[StrategicPattern]:
        """Identify patterns where context affects outcomes"""
        if len(experiences) < 3:
            return None

        # Sort by success to see patterns
        experiences.sort(key=lambda x: x.success_score, reverse=True)

        successful = [exp for exp in experiences if exp.success_score > 0.6]
        unsuccessful = [exp for exp in experiences if exp.success_score < 0.4]

        if len(successful) == 0 or len(unsuccessful) == 0:
            return None

        # Find differentiating factors
        success_factors = self._extract_contextual_factors(successful)
        failure_factors = self._extract_contextual_factors(unsuccessful)

        # Identify key differences
        key_differences = self._compare_contextual_factors(success_factors, failure_factors)

        if key_differences:
            pattern = StrategicPattern(
                pattern_id=f"contextual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                pattern_type="improvement",
                situation_keywords=[self._simplify_situation(experiences[0].situation)],
                action_sequence=[exp.action for exp in successful[:3]],  # Top successful actions
                success_rate=np.mean([exp.success_score for exp in successful]),
                frequency=len(experiences),
                character_classes=list(set([exp.character_class for exp in experiences])),
                level_range=(min([exp.level for exp in experiences]), max([exp.level for exp in experiences])),
                skill_requirements=list(set([skill for exp in experiences for skill in exp.skills_used])),
                contextual_factors={"key_factors": key_differences},
                confidence_score=0.7,
                timestamp=datetime.now()
            )
            return pattern

        return None

    def _compare_contextual_factors(self, success_factors: Dict, failure_factors: Dict) -> List[str]:
        """Compare contextual factors to find key differences"""
        differences = []

        # Compare locations
        success_locs = [loc[0] for loc in success_factors.get("common_locations", [])]
        failure_locs = [loc[0] for loc in failure_factors.get("common_locations", [])]

        if success_locs and failure_locs:
            if set(success_locs) != set(failure_locs):
                differences.append("location matters")

        # Compare ally support
        success_allies = success_factors.get("avg_allies", 0)
        failure_allies = failure_factors.get("avg_allies", 0)

        if abs(success_allies - failure_allies) > 1:
            if success_allies > failure_allies:
                differences.append("allies helpful")
            else:
                differences.append("solo approach better")

        # Compare resources
        success_resources = set(success_factors.get("available_resources", []))
        failure_resources = set(failure_factors.get("available_resources", []))

        if success_resources != failure_resources:
            if success_resources - failure_resources:
                differences.append(f"specific resources help: {list(success_resources - failure_resources)}")

        return differences

    def _filter_quality_patterns(self, patterns: List[StrategicPattern]) -> List[StrategicPattern]:
        """Filter patterns based on quality criteria"""
        quality_patterns = []

        for pattern in patterns:
            # Minimum frequency and confidence thresholds
            if pattern.frequency >= 2 and pattern.confidence_score >= 0.5:
                # Additional quality checks
                if pattern.pattern_type == "success" and pattern.success_rate >= 0.7:
                    quality_patterns.append(pattern)
                elif pattern.pattern_type == "failure" and pattern.success_rate <= 0.3:
                    quality_patterns.append(pattern)
                elif pattern.pattern_type == "improvement" and pattern.confidence_score >= 0.6:
                    quality_patterns.append(pattern)

        # Sort by confidence and frequency
        quality_patterns.sort(key=lambda p: (p.confidence_score, p.frequency), reverse=True)

        return quality_patterns[:20]  # Return top 20 patterns

    async def _save_pattern_analysis(self, agent_id: str, patterns: List[StrategicPattern]):
        """Save pattern analysis results"""
        try:
            analysis_data = {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "pattern_count": len(patterns),
                "patterns": [asdict(pattern) for pattern in patterns]
            }

            # Save to file
            file_path = f"/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/patterns/{agent_id}_patterns.json"
            with open(file_path, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)

            # Update history
            self.pattern_history[agent_id].append({
                "timestamp": datetime.now().isoformat(),
                "pattern_count": len(patterns),
                "avg_confidence": np.mean([p.confidence_score for p in patterns]) if patterns else 0.0
            })

            # Keep only recent history
            if len(self.pattern_history[agent_id]) > 10:
                self.pattern_history[agent_id] = self.pattern_history[agent_id][-10:]

        except Exception as e:
            logger.error(f"Failed to save pattern analysis for agent {agent_id}: {str(e)}")

    async def get_strategy_recommendations(self, agent_id: str, current_situation: str,
                                         character_info: Dict[str, Any]) -> List[StrategyRecommendation]:
        """
        Generate strategy recommendations based on learned patterns

        Args:
            agent_id: Agent identifier
            current_situation: Description of current situation
            character_info: Character class, level, skills, etc.

        Returns:
            List of strategy recommendations
        """
        try:
            if agent_id not in self.pattern_cache:
                logger.warning(f"No patterns found for agent {agent_id}")
                return []

            patterns = self.pattern_cache[agent_id]
            recommendations = []

            # Find relevant patterns
            relevant_patterns = self._find_relevant_patterns(current_situation, patterns, character_info)

            # Generate recommendations from patterns
            for pattern in relevant_patterns:
                recommendation = await self._create_recommendation_from_pattern(
                    agent_id, pattern, current_situation, character_info
                )
                if recommendation:
                    recommendations.append(recommendation)

            # Sort by confidence and success probability
            recommendations.sort(key=lambda r: (r.confidence * r.success_probability), reverse=True)

            return recommendations[:5]  # Return top 5 recommendations

        except Exception as e:
            logger.error(f"Failed to generate strategy recommendations for agent {agent_id}: {str(e)}")
            return []

    def _find_relevant_patterns(self, situation: str, patterns: List[StrategicPattern],
                              character_info: Dict[str, Any]) -> List[StrategicPattern]:
        """Find patterns relevant to current situation"""
        relevant_patterns = []

        situation_lower = situation.lower()
        character_class = character_info.get("class", "").lower()
        character_level = character_info.get("level", 1)

        for pattern in patterns:
            relevance_score = 0.0

            # Situation keyword matching
            for keyword in pattern.situation_keywords:
                if keyword.lower() in situation_lower:
                    relevance_score += 0.3

            # Character class matching
            if character_class in [cls.lower() for cls in pattern.character_classes]:
                relevance_score += 0.4

            # Level range matching
            if pattern.level_range[0] <= character_level <= pattern.level_range[1]:
                relevance_score += 0.3

            # Skill requirements
            character_skills = [skill.lower() for skill in character_info.get("skills", [])]
            required_skills = [skill.lower() for skill in pattern.skill_requirements]
            skill_match = len(set(character_skills) & set(required_skills)) / max(len(required_skills), 1)
            relevance_score += skill_match * 0.2

            if relevance_score >= 0.5:  # Relevance threshold
                pattern.relevance_score = relevance_score  # Add relevance for sorting
                relevant_patterns.append(pattern)

        # Sort by relevance and confidence
        relevant_patterns.sort(key=lambda p: (p.relevance_score, p.confidence_score), reverse=True)

        return relevant_patterns[:10]

    async def _create_recommendation_from_pattern(self, agent_id: str, pattern: StrategicPattern,
                                                current_situation: str,
                                                character_info: Dict[str, Any]) -> Optional[StrategyRecommendation]:
        """Create a strategy recommendation from a pattern"""
        try:
            if pattern.pattern_type == "success":
                # Recommend successful strategies
                recommended_strategy = "Consider this approach: " + "; ".join(pattern.action_sequence)
                success_probability = pattern.success_rate
                risk_assessment = "Low risk based on past success"
            elif pattern.pattern_type == "failure":
                # Warn against failed strategies
                recommended_strategy = "Avoid this approach: " + "; ".join(pattern.action_sequence)
                success_probability = 1.0 - pattern.success_rate  # Invert for recommendations
                risk_assessment = "High risk based on past failures"
            else:  # improvement
                # Suggest improvements
                recommended_strategy = "Focus on: " + "; ".join(pattern.action_sequence)
                success_probability = 0.6  # Moderate probability for learning patterns
                risk_assessment = "Moderate risk - learning opportunity"

            # Create alternative strategies
            alternatives = []
            if pattern.pattern_type == "failure":
                alternatives = ["Try a completely different approach", "Consider seeking help", "Analyze the situation more carefully"]
            elif pattern.pattern_type == "improvement":
                alternatives = ["Practice this approach in safer situations", "Combine with complementary strategies"]

            # Historical evidence
            evidence = [
                f"Pattern observed {pattern.frequency} times",
                f"Success rate: {pattern.success_rate:.1%}",
                f"Confidence: {pattern.confidence_score:.1%}"
            ]

            recommendation = StrategyRecommendation(
                agent_id=agent_id,
                situation=current_situation,
                recommended_strategy=recommended_strategy,
                success_probability=success_probability,
                risk_assessment=risk_assessment,
                alternative_strategies=alternatives,
                skill_requirements=pattern.skill_requirements,
                historical_evidence=evidence,
                confidence=pattern.confidence_score
            )

            return recommendation

        except Exception as e:
            logger.error(f"Failed to create recommendation from pattern: {str(e)}")
            return None

    def get_pattern_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get summary of patterns for an agent"""
        if agent_id not in self.pattern_cache:
            return {"error": "No patterns found for agent"}

        patterns = self.pattern_cache[agent_id]

        summary = {
            "agent_id": agent_id,
            "total_patterns": len(patterns),
            "pattern_types": {
                "success": len([p for p in patterns if p.pattern_type == "success"]),
                "failure": len([p for p in patterns if p.pattern_type == "failure"]),
                "improvement": len([p for p in patterns if p.pattern_type == "improvement"])
            },
            "avg_confidence": np.mean([p.confidence_score for p in patterns]) if patterns else 0.0,
            "most_successful_patterns": sorted(
                [p for p in patterns if p.pattern_type == "success"],
                key=lambda p: p.success_rate,
                reverse=True
            )[:5],
            "recent_analysis_history": self.pattern_history.get(agent_id, [])[-5:],
            "last_updated": max([p.timestamp for p in patterns]).isoformat() if patterns else None
        }

        return summary

# Main execution for testing
if __name__ == "__main__":
    async def main():
        analyzer = StrategicPatternAnalyzer()

        # Create sample experiences
        experiences = [
            CharacterExperience(
                agent_id="test_wizard_001",
                session_id="session_001",
                timestamp=datetime.now(),
                situation="Combat with goblins in forest",
                action="Cast fireball spell",
                outcome="Defeated all goblins efficiently",
                success_score=0.9,
                reward=100.0,
                context={"location": "forest", "allies": ["fighter"]},
                skills_used=["arcana", "evocation"],
                character_class="Wizard",
                level=5,
                emotional_valence=0.8,
                strategic_importance=0.9
            ),
            CharacterExperience(
                agent_id="test_wizard_001",
                session_id="session_002",
                timestamp=datetime.now(),
                situation="Negotiation with merchant",
                action="Used persuasion skill",
                outcome="Got favorable trade terms",
                success_score=0.8,
                reward=50.0,
                context={"location": "town", "allies": []},
                skills_used=["persuasion", "deception"],
                character_class="Wizard",
                level=5,
                emotional_valence=0.6,
                strategic_importance=0.7
            )
        ]

        patterns = await analyzer.analyze_agent_experiences("test_wizard_001", experiences)
        print(f"Discovered {len(patterns)} patterns")

        for pattern in patterns:
            print(f"Pattern: {pattern.pattern_type} - Confidence: {pattern.confidence_score:.2f}")

    asyncio.run(main())