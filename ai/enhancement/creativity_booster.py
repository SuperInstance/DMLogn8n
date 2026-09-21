#!/usr/bin/env python3
"""
Creativity Booster - Enhanced creative problem-solving for AI agents

This module enhances AI creative thinking, problem-solving capabilities, and
innovative idea generation through various creativity techniques and approaches.
"""

import json
import time
import random
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import itertools
import hashlib

class CreativityTechnique(Enum):
    BRAINSTORMING = "brainstorming"
    MIND_MAPPING = "mind_mapping"
    ANALOGICAL_THINKING = "analogical_thinking"
    LATERAL_THINKING = "lateral_thinking"
    SCAMPER = "scamper"  # Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse
    SIX_THINKING_HATS = "six_thinking_hats"
    DESIGN_THINKING = "design_thinking"
    TRIZ = "triz"  # Theory of Inventive Problem Solving
    FIRST_PRINCIPLES = "first_principles"
    DIVERGENT_CONVERGENT = "divergent_convergent"

class ProblemType(Enum):
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    PRACTICAL = "practical"
    STRATEGIC = "strategic"
    TECHNICAL = "technical"
    INTERPERSONAL = "interpersonal"

class CreativityLevel(Enum):
    BASIC = 0.3
    INTERMEDIATE = 0.5
    ADVANCED = 0.7
    EXPERT = 0.9

@dataclass
class CreativeIdea:
    """Represents a creative idea with metadata."""
    content: str
    technique: CreativityTechnique
    originality_score: float
    feasibility_score: float
    impact_score: float
    tags: Set[str] = field(default_factory=set)
    related_ideas: List[str] = field(default_factory=list)
    development_stage: str = "concept"
    confidence: float = 0.5

@dataclass
class CreativityMetrics:
    """Metrics for creativity enhancement performance."""
    idea_quantity: int
    idea_quality: float
    originality_score: float
    diversity_score: float
    elaboration_score: float
    implementation_potential: float

class CreativityBooster:
    """
    Advanced creativity enhancement system for AI agents.

    Features:
    - Multiple creativity techniques and approaches
    - Creative problem-solving methodologies
    - Idea generation and evaluation
    - Cross-domain inspiration
    - Analogical reasoning
    - Creative constraint handling
    - Innovation pattern recognition
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.creativity_history = []
        self.idea_database = []
        self.creativity_patterns = self._load_creativity_patterns()
        self.inspiration_sources = self._load_inspiration_sources()
        self.analogy_database = self._load_analogy_database()

        # Configuration
        self.enabled_techniques = set(CreativityTechnique)
        self.creativity_level = CreativityLevel.INTERMEDIATE
        self.max_ideas_per_session = 50
        self.idea_evaluation_threshold = 0.6

        # Learning parameters
        self.learning_rate = 0.1
        self.creativity_decay = 0.95
        self.inspiration_weight = 0.3

        # Creative constraints
        self.constraints = []
        self.context_factors = []

        # Idea evolution
        self.idea_evolution_chains = defaultdict(list)
        self.concept_combinations = []

        # Logging
        self.logger = logging.getLogger(f"creativity_booster_{agent_id}")

    def boost_creativity(self, problem: str, context: Dict[str, Any] = None,
                        preferred_techniques: List[CreativityTechnique] = None) -> Tuple[List[CreativeIdea], CreativityMetrics]:
        """
        Boost creativity for problem-solving using multiple techniques.

        Args:
            problem: Problem statement or challenge
            context: Additional context information
            preferred_techniques: Preferred creativity techniques to use

        Returns:
            Tuple of (creative_ideas, creativity_metrics)
        """
        start_time = time.time()

        # Analyze problem type
        problem_type = self._analyze_problem_type(problem, context)

        # Select appropriate techniques
        techniques = self._select_techniques(problem_type, preferred_techniques)

        # Generate creative ideas using selected techniques
        all_ideas = []
        for technique in techniques:
            ideas = self._apply_technique(technique, problem, context)
            all_ideas.extend(ideas)

        # Evaluate and filter ideas
        evaluated_ideas = self._evaluate_ideas(all_ideas, problem, context)

        # Enhance ideas through cross-pollination
        enhanced_ideas = self._cross_pollinate_ideas(evaluated_ideas)

        # Apply creative constraints
        constrained_ideas = self._apply_constraints(enhanced_ideas)

        # Rank and select final ideas
        final_ideas = self._rank_ideas(constrained_ideas)[:self.max_ideas_per_session]

        # Calculate creativity metrics
        metrics = self._calculate_creativity_metrics(final_ideas, time.time() - start_time)

        # Update creativity history
        self._update_creativity_history(problem, final_ideas, techniques, metrics)

        return final_ideas, metrics

    def _apply_technique(self, technique: CreativityTechnique, problem: str,
                        context: Dict[str, Any]) -> List[CreativeIdea]:
        """Apply a specific creativity technique to generate ideas."""
        if technique == CreativityTechnique.BRAINSTORMING:
            return self._brainstorming_technique(problem, context)
        elif technique == CreativityTechnique.MIND_MAPPING:
            return self._mind_mapping_technique(problem, context)
        elif technique == CreativityTechnique.ANALOGICAL_THINKING:
            return self._analogical_thinking_technique(problem, context)
        elif technique == CreativityTechnique.LATERAL_THINKING:
            return self._lateral_thinking_technique(problem, context)
        elif technique == CreativityTechnique.SCAMPER:
            return self._scamper_technique(problem, context)
        elif technique == CreativityTechnique.SIX_THINKING_HATS:
            return self._six_thinking_hats_technique(problem, context)
        elif technique == CreativityTechnique.DESIGN_THINKING:
            return self._design_thinking_technique(problem, context)
        elif technique == CreativityTechnique.TRIZ:
            return self._triz_technique(problem, context)
        elif technique == CreativityTechnique.FIRST_PRINCIPLES:
            return self._first_principles_technique(problem, context)
        elif technique == CreativityTechnique.DIVERGENT_CONVERGENT:
            return self._divergent_convergent_technique(problem, context)
        else:
            return []

    def _brainstorming_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using brainstorming technique."""
        ideas = []

        # Extract key concepts from problem
        concepts = self._extract_key_concepts(problem)

        # Generate random word associations
        for concept in concepts:
            associations = self._generate_associations(concept)
            for association in associations:
                idea_content = f"Combine {concept} with {association} to address the problem"
                idea = CreativeIdea(
                    content=idea_content,
                    technique=CreativityTechnique.BRAINSTORMING,
                    originality_score=random.uniform(0.3, 0.8),
                    feasibility_score=random.uniform(0.4, 0.9),
                    impact_score=random.uniform(0.3, 0.7),
                    tags={'brainstorming', 'association', concept}
                )
                ideas.append(idea)

        # Generate "what if" scenarios
        what_if_prompts = [
            "What if time/money weren't constraints?",
            "What if we had unlimited resources?",
            "What if we approached this backwards?",
            "What if we combined opposite approaches?",
            "What if we removed all assumptions?"
        ]

        for prompt in what_if_prompts:
            idea_content = f"{prompt} {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.BRAINSTORMING,
                originality_score=random.uniform(0.5, 0.9),
                feasibility_score=random.uniform(0.2, 0.6),
                impact_score=random.uniform(0.6, 0.9),
                tags={'brainstorming', 'what_if', 'scenario'}
            )
            ideas.append(idea)

        return ideas

    def _mind_mapping_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using mind mapping technique."""
        ideas = []

        # Central concept
        central_concept = self._extract_main_concept(problem)

        # Create branches for different aspects
        branches = [
            'benefits', 'challenges', 'stakeholders', 'resources',
            'alternatives', 'consequences', 'implementation', 'measurement'
        ]

        for branch in branches:
            # Generate sub-ideas for each branch
            sub_ideas = self._generate_branch_ideas(central_concept, branch)
            for sub_idea in sub_ideas:
                idea_content = f"From {branch} perspective: {sub_idea}"
                idea = CreativeIdea(
                    content=idea_content,
                    technique=CreativityTechnique.MIND_MAPPING,
                    originality_score=random.uniform(0.4, 0.7),
                    feasibility_score=random.uniform(0.5, 0.8),
                    impact_score=random.uniform(0.4, 0.7),
                    tags={'mind_mapping', branch, central_concept}
                )
                ideas.append(idea)

        return ideas

    def _analogical_thinking_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using analogical thinking."""
        ideas = []

        # Find analogies in nature
        nature_analogies = [
            "how beavers build dams",
            "how ants colonies organize",
            "how trees grow and adapt",
            "how ecosystems maintain balance",
            "how birds navigate"
        ]

        for analogy in nature_analogies:
            idea_content = f"Apply principles from {analogy} to solve: {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.ANALOGICAL_THINKING,
                originality_score=random.uniform(0.6, 0.9),
                feasibility_score=random.uniform(0.3, 0.7),
                impact_score=random.uniform(0.5, 0.8),
                tags={'analogical', 'nature', 'biomimicry'}
            )
            ideas.append(idea)

        # Find analogies in different domains
        domain_analogies = [
            "how successful startups innovate",
            "how artists approach creative blocks",
            "how scientists conduct experiments",
            "how athletes train for performance",
            "how chefs create new recipes"
        ]

        for analogy in domain_analogies:
            idea_content = f"Learn from {analogy} to address: {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.ANALOGICAL_THINKING,
                originality_score=random.uniform(0.5, 0.8),
                feasibility_score=random.uniform(0.4, 0.8),
                impact_score=random.uniform(0.4, 0.7),
                tags={'analogical', 'cross_domain', analogy}
            )
            ideas.append(idea)

        return ideas

    def _lateral_thinking_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using lateral thinking."""
        ideas = []

        # Challenge assumptions
        assumptions = self._identify_assumptions(problem)
        for assumption in assumptions:
            idea_content = f"Challenge assumption: {assumption}. What if the opposite is true?"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.LATERAL_THINKING,
                originality_score=random.uniform(0.7, 0.9),
                feasibility_score=random.uniform(0.2, 0.6),
                impact_score=random.uniform(0.6, 0.9),
                tags={'lateral_thinking', 'assumption_challenge', 'provocative'}
            )
            ideas.append(idea)

        # Random entry points
        random_words = ['bridge', 'mirror', 'catalyst', 'ecosystem', 'network', 'pattern']
        for word in random_words:
            idea_content = f"Use '{word}' as a metaphor to approach: {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.LATERAL_THINKING,
                originality_score=random.uniform(0.6, 0.8),
                feasibility_score=random.uniform(0.3, 0.7),
                impact_score=random.uniform(0.5, 0.8),
                tags={'lateral_thinking', 'metaphor', 'random_entry'}
            )
            ideas.append(idea)

        return ideas

    def _scamper_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using SCAMPER technique."""
        ideas = []

        scamper_actions = {
            'Substitute': "What can be substituted?",
            'Combine': "What can be combined?",
            'Adapt': "What can be adapted?",
            'Modify': "What can be modified?",
            'Put to another use': "How can it be used differently?",
            'Eliminate': "What can be eliminated?",
            'Reverse': "What can be reversed?"
        }

        for action, prompt in scamper_actions.items():
            idea_content = f"{prompt}: {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.SCAMPER,
                originality_score=random.uniform(0.5, 0.8),
                feasibility_score=random.uniform(0.5, 0.8),
                impact_score=random.uniform(0.4, 0.7),
                tags={'scamper', action.lower(), 'systematic'}
            )
            ideas.append(idea)

        return ideas

    def _six_thinking_hats_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using Six Thinking Hats technique."""
        ideas = []

        hats = {
            'White Hat (Facts)': "Focus on data and facts about the problem",
            'Red Hat (Emotions)': "Consider emotional responses and feelings",
            'Black Hat (Caution)': "Identify potential risks and problems",
            'Yellow Hat (Optimism)': "Focus on benefits and positives",
            'Green Hat (Creativity)': "Generate creative alternatives",
            'Blue Hat (Process)': "Consider the overall approach and process"
        }

        for hat, description in hats.items():
            idea_content = f"From {hat} perspective: {description} for {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.SIX_THINKING_HATS,
                originality_score=random.uniform(0.4, 0.7),
                feasibility_score=random.uniform(0.6, 0.8),
                impact_score=random.uniform(0.5, 0.7),
                tags={'six_thinking_hats', hat.split('(')[0].strip().lower()}
            )
            ideas.append(idea)

        return ideas

    def _design_thinking_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using Design Thinking methodology."""
        ideas = []

        phases = [
            'Empathize': "Understand user needs and perspectives",
            'Define': "Clearly define the problem statement",
            'Ideate': "Generate a wide range of ideas",
            'Prototype': "Create experimental solutions",
            'Test': "Gather feedback and iterate"
        ]

        for phase, description in phases.items():
            idea_content = f"Design Thinking - {phase}: {description} for {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.DESIGN_THINKING,
                originality_score=random.uniform(0.5, 0.7),
                feasibility_score=random.uniform(0.6, 0.9),
                impact_score=random.uniform(0.6, 0.8),
                tags={'design_thinking', phase.lower(), 'user_centered'}
            )
            ideas.append(idea)

        return ideas

    def _triz_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using TRIZ methodology."""
        ideas = []

        # TRIZ contradictions
        contradictions = [
            "Improve X without worsening Y",
            "Increase benefit while reducing harm",
            "Make it stronger but lighter",
            "Make it faster but more accurate",
            "Make it cheaper but higher quality"
        ]

        for contradiction in contradictions:
            idea_content = f"TRIZ principle: Resolve contradiction '{contradiction}' in {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.TRIZ,
                originality_score=random.uniform(0.6, 0.8),
                feasibility_score=random.uniform(0.4, 0.7),
                impact_score=random.uniform(0.6, 0.9),
                tags={'triz', 'contradiction', 'systematic_innovation'}
            )
            ideas.append(idea)

        return ideas

    def _first_principles_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using first principles thinking."""
        ideas = []

        # Break down to fundamental components
        components = self._decompose_problem(problem)

        for component in components:
            idea_content = f"First principles analysis of '{component}' in context of {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.FIRST_PRINCIPLES,
                originality_score=random.uniform(0.5, 0.8),
                feasibility_score=random.uniform(0.6, 0.9),
                impact_score=random.uniform(0.5, 0.8),
                tags={'first_principles', 'fundamental', component}
            )
            ideas.append(idea)

        return ideas

    def _divergent_convergent_technique(self, problem: str, context: Dict[str, Any]) -> List[CreativeIdea]:
        """Generate ideas using divergent and convergent thinking."""
        ideas = []

        # Divergent phase - generate many possibilities
        divergent_prompts = [
            "List 10 completely different approaches",
            "Consider solutions from unrelated fields",
            "Imagine how a child would solve this",
            "Think about this in 100 years",
            "Consider alien perspectives"
        ]

        for prompt in divergent_prompts:
            idea_content = f"Divergent thinking: {prompt} for {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.DIVERGENT_CONVERGENT,
                originality_score=random.uniform(0.7, 0.9),
                feasibility_score=random.uniform(0.3, 0.6),
                impact_score=random.uniform(0.6, 0.8),
                tags={'divergent_thinking', 'possibility', 'exploration'}
            )
            ideas.append(idea)

        # Convergent phase - focus and refine
        convergent_prompts = [
            "Select the most promising approach and develop it",
            "Combine the best elements from different ideas",
            "Create a practical implementation plan",
            "Identify the simplest effective solution"
        ]

        for prompt in convergent_prompts:
            idea_content = f"Convergent thinking: {prompt} for {problem}"
            idea = CreativeIdea(
                content=idea_content,
                technique=CreativityTechnique.DIVERGENT_CONVERGENT,
                originality_score=random.uniform(0.3, 0.6),
                feasibility_score=random.uniform(0.7, 0.9),
                impact_score=random.uniform(0.6, 0.8),
                tags={'convergent_thinking', 'focus', 'refinement'}
            )
            ideas.append(idea)

        return ideas

    def _evaluate_ideas(self, ideas: List[CreativeIdea], problem: str,
                       context: Dict[str, Any]) -> List[CreativeIdea]:
        """Evaluate and score ideas based on multiple criteria."""
        evaluated_ideas = []

        for idea in ideas:
            # Calculate overall quality score
            quality_score = (
                idea.originality_score * 0.3 +
                idea.feasibility_score * 0.3 +
                idea.impact_score * 0.4
            )

            # Update idea confidence based on quality
            idea.confidence = quality_score

            # Keep ideas above threshold
            if quality_score >= self.idea_evaluation_threshold:
                evaluated_ideas.append(idea)

        return evaluated_ideas

    def _cross_pollinate_ideas(self, ideas: List[CreativeIdea]) -> List[CreativeIdea]:
        """Cross-pollinate ideas to create new combinations."""
        enhanced_ideas = ideas.copy()

        # Combine complementary ideas
        for i, idea1 in enumerate(ideas):
            for j, idea2 in enumerate(ideas[i+1:], i+1):
                if self._are_complementary(idea1, idea2):
                    combined_content = f"Combine: {idea1.content} + {idea2.content}"
                    combined_idea = CreativeIdea(
                        content=combined_content,
                        technique=CreativityTechnique.BRAINSTORMING,  # Combination technique
                        originality_score=(idea1.originality_score + idea2.originality_score) / 2 * 1.2,
                        feasibility_score=(idea1.feasibility_score + idea2.feasibility_score) / 2 * 0.9,
                        impact_score=(idea1.impact_score + idea2.impact_score) / 2 * 1.1,
                        tags=idea1.tags.union(idea2.tags).union({'combination', 'hybrid'}),
                        related_ideas=[idea1.content, idea2.content]
                    )
                    enhanced_ideas.append(combined_idea)

        return enhanced_ideas

    def _apply_constraints(self, ideas: List[CreativeIdea]) -> List[CreativeIdea]:
        """Apply creative constraints to refine ideas."""
        constrained_ideas = []

        for idea in ideas:
            # Check against constraints
            satisfies_constraints = True

            for constraint in self.constraints:
                if not self._check_constraint(idea, constraint):
                    satisfies_constraints = False
                    break

            if satisfies_constraints:
                constrained_ideas.append(idea)

        return constrained_ideas

    def _rank_ideas(self, ideas: List[CreativeIdea]) -> List[CreativeIdea]:
        """Rank ideas by overall quality and potential."""
        return sorted(ideas, key=lambda x: x.confidence, reverse=True)

    def _calculate_creativity_metrics(self, ideas: List[CreativeIdea], processing_time: float) -> CreativityMetrics:
        """Calculate comprehensive creativity metrics."""
        if not ideas:
            return CreativityMetrics(0, 0, 0, 0, 0, 0)

        # Calculate individual metrics
        idea_quantity = len(ideas)
        idea_quality = sum(idea.confidence for idea in ideas) / len(ideas)
        originality_score = sum(idea.originality_score for idea in ideas) / len(ideas)
        diversity_score = self._calculate_diversity_score(ideas)
        elaboration_score = self._calculate_elaboration_score(ideas)
        implementation_potential = sum(idea.feasibility_score for idea in ideas) / len(ideas)

        return CreativityMetrics(
            idea_quantity=idea_quantity,
            idea_quality=idea_quality,
            originality_score=originality_score,
            diversity_score=diversity_score,
            elaboration_score=elaboration_score,
            implementation_potential=implementation_potential
        )

    def _update_creativity_history(self, problem: str, ideas: List[CreativeIdea],
                                 techniques: List[CreativityTechnique], metrics: CreativityMetrics):
        """Update creativity history for learning and improvement."""
        session = {
            'timestamp': time.time(),
            'problem': problem,
            'ideas_generated': len(ideas),
            'techniques_used': [t.value for t in techniques],
            'metrics': {
                'quantity': metrics.idea_quantity,
                'quality': metrics.idea_quality,
                'originality': metrics.originality_score,
                'diversity': metrics.diversity_score
            },
            'top_ideas': [idea.content for idea in ideas[:5]]
        }

        self.creativity_history.append(session)

        # Keep history manageable
        if len(self.creativity_history) > 100:
            self.creativity_history = self.creativity_history[-100:]

        # Learn from session
        self._learn_from_session(session)

    def get_creativity_insights(self) -> Dict[str, Any]:
        """Get insights into creativity performance and patterns."""
        if not self.creativity_history:
            return {'message': 'No creativity history available'}

        # Calculate statistics
        total_sessions = len(self.creativity_history)
        total_ideas = sum(session['ideas_generated'] for session in self.creativity_history)
        avg_quality = sum(session['metrics']['quality'] for session in self.creativity_history) / total_sessions

        # Most effective techniques
        technique_effectiveness = defaultdict(list)
        for session in self.creativity_history:
            for technique in session['techniques_used']:
                technique_effectiveness[technique].append(session['metrics']['quality'])

        avg_technique_performance = {
            tech: sum(scores) / len(scores)
            for tech, scores in technique_effectiveness.items()
        }

        # Creativity trends
        recent_sessions = self.creativity_history[-10:]
        early_sessions = self.creativity_history[:10]

        recent_avg_quality = sum(s['metrics']['quality'] for s in recent_sessions) / len(recent_sessions)
        early_avg_quality = sum(s['metrics']['quality'] for s in early_sessions) / len(early_sessions)
        quality_trend = recent_avg_quality - early_avg_quality

        return {
            'agent_id': self.agent_id,
            'total_sessions': total_sessions,
            'total_ideas_generated': total_ideas,
            'average_idea_quality': avg_quality,
            'most_effective_techniques': sorted(
                avg_technique_performance.items(),
                key=lambda x: x[1], reverse=True
            )[:5],
            'quality_trend': quality_trend,
            'creativity_level': self.creativity_level.value,
            'enabled_techniques': [t.value for t in self.enabled_techniques]
        }

    # Helper methods
    def _analyze_problem_type(self, problem: str, context: Dict[str, Any]) -> ProblemType:
        """Analyze the type of problem to select appropriate techniques."""
        problem_lower = problem.lower()

        if any(word in problem_lower for word in ['create', 'design', 'invent', 'imagine']):
            return ProblemType.CREATIVE
        elif any(word in problem_lower for word in ['analyze', 'evaluate', 'compare', 'assess']):
            return ProblemType.ANALYTICAL
        elif any(word in problem_lower for word in ['solve', 'fix', 'implement', 'execute']):
            return ProblemType.PRACTICAL
        elif any(word in problem_lower for word in ['plan', 'strategy', 'long-term', 'vision']):
            return ProblemType.STRATEGIC
        elif any(word in problem_lower for word in ['technical', 'engineering', 'system', 'code']):
            return ProblemType.TECHNICAL
        elif any(word in problem_lower for word in ['team', 'people', 'communication', 'relationship']):
            return ProblemType.INTERPERSONAL
        else:
            return ProblemType.PRACTICAL

    def _select_techniques(self, problem_type: ProblemType,
                         preferred_techniques: List[CreativityTechnique] = None) -> List[CreativityTechnique]:
        """Select appropriate creativity techniques for the problem type."""
        if preferred_techniques:
            return [t for t in preferred_techniques if t in self.enabled_techniques]

        # Default technique mappings by problem type
        technique_mapping = {
            ProblemType.CREATIVE: [
                CreativityTechnique.BRAINSTORMING,
                CreativityTechnique.LATERAL_THINKING,
                CreativityTechnique.ANALOGICAL_THINKING
            ],
            ProblemType.ANALYTICAL: [
                CreativityTechnique.FIRST_PRINCIPLES,
                CreativityTechnique.TRIZ,
                CreativityTechnique.DIVERGENT_CONVERGENT
            ],
            ProblemType.PRACTICAL: [
                CreativityTechnique.SCAMPER,
                CreativityTechnique.DESIGN_THINKING,
                CreativityTechnique.SIX_THINKING_HATS
            ],
            ProblemType.STRATEGIC: [
                CreativityTechnique.SIX_THINKING_HATS,
                CreativityTechnique.DESIGN_THINKING,
                CreativityTechnique.DIVERGENT_CONVERGENT
            ],
            ProblemType.TECHNICAL: [
                CreativityTechnique.TRIZ,
                CreativityTechnique.FIRST_PRINCIPLES,
                CreativityTechnique.ANALOGICAL_THINKING
            ],
            ProblemType.INTERPERSONAL: [
                CreativityTechnique.DESIGN_THINKING,
                CreativityTechnique.SIX_THINKING_HATS,
                CreativityTechnique.BRAINSTORMING
            ]
        }

        return technique_mapping.get(problem_type, list(self.enabled_techniques))[:3]

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        concepts = [word for word in words if len(word) > 3 and word not in stop_words]
        return concepts[:5]  # Return top 5 concepts

    def _extract_main_concept(self, text: str) -> str:
        """Extract the main concept from text."""
        concepts = self._extract_key_concepts(text)
        return concepts[0] if concepts else "problem"

    def _generate_associations(self, concept: str) -> List[str]:
        """Generate word associations for a concept."""
        # Simple association dictionary
        associations = {
            'problem': ['solution', 'challenge', 'opportunity', 'innovation'],
            'solution': ['implementation', 'strategy', 'approach', 'method'],
            'improve': ['enhance', 'optimize', 'refine', 'upgrade'],
            'create': ['design', 'develop', 'build', 'innovate'],
            'user': ['customer', 'client', 'person', 'individual'],
            'system': ['process', 'framework', 'structure', 'mechanism']
        }

        return associations.get(concept, ['alternative', 'different', 'new', 'innovative'])

    def _generate_branch_ideas(self, central_concept: str, branch: str) -> List[str]:
        """Generate ideas for a mind mapping branch."""
        branch_ideas = {
            'benefits': [f"Advantages of solving {central_concept}"],
            'challenges': [f"Obstacles in addressing {central_concept}"],
            'stakeholders': [f"People affected by {central_concept}"],
            'resources': [f"Resources needed for {central_concept}"],
            'alternatives': [f"Different approaches to {central_concept}"],
            'consequences': [f"Outcomes of solving {central_concept}"],
            'implementation': [f"Steps to implement solution for {central_concept}"],
            'measurement': [f"How to measure success for {central_concept}"]
        }

        return branch_ideas.get(branch, [f"Ideas related to {branch} of {central_concept}"])

    def _identify_assumptions(self, problem: str) -> List[str]:
        """Identify common assumptions in the problem."""
        common_assumptions = [
            "Current methods are the only way",
            "Resources are limited",
            "Time is a constraint",
            "Existing knowledge is complete",
            "Current approach is optimal"
        ]

        # Simple heuristic - return assumptions that might apply
        applicable_assumptions = []
        for assumption in common_assumptions:
            if random.random() < 0.3:  # 30% chance each assumption applies
                applicable_assumptions.append(assumption)

        return applicable_assumptions

    def _decompose_problem(self, problem: str) -> List[str]:
        """Decompose problem into fundamental components."""
        # Simple decomposition based on keywords
        components = []

        if 'improve' in problem.lower():
            components.append('current_state')
            components.append('desired_state')
            components.append('improvement_methods')

        if 'create' in problem.lower():
            components.append('requirements')
            components.append('resources')
            components.append('process')

        if 'solve' in problem.lower():
            components.append('problem_definition')
            components.append('root_causes')
            components.append('solution_criteria')

        return components if components else ['problem', 'context', 'constraints']

    def _are_complementary(self, idea1: CreativeIdea, idea2: CreativeIdea) -> bool:
        """Check if two ideas are complementary."""
        # Simple heuristic - ideas with different techniques are often complementary
        return idea1.technique != idea2.technique

    def _check_constraint(self, idea: CreativeIdea, constraint: str) -> bool:
        """Check if idea satisfies a constraint."""
        # Simple constraint checking - can be enhanced
        constraint_lower = constraint.lower()
        idea_content_lower = idea.content.lower()

        if 'cost' in constraint_lower and 'expensive' in idea_content_lower:
            return False
        if 'time' in constraint_lower and 'slow' in idea_content_lower:
            return False
        if 'simple' in constraint_lower and 'complex' in idea_content_lower:
            return False

        return True

    def _calculate_diversity_score(self, ideas: List[CreativeIdea]) -> float:
        """Calculate diversity score of ideas."""
        if len(ideas) < 2:
            return 0.0

        # Calculate technique diversity
        techniques = set(idea.technique for idea in ideas)
        technique_diversity = len(techniques) / len(CreativityTechnique)

        # Calculate tag diversity
        all_tags = set()
        for idea in ideas:
            all_tags.update(idea.tags)
        tag_diversity = len(all_tags) / max(len(ideas), 1)

        return (technique_diversity + tag_diversity) / 2

    def _calculate_elaboration_score(self, ideas: List[CreativeIdea]) -> float:
        """Calculate elaboration score of ideas."""
        if not ideas:
            return 0.0

        # Calculate average content length as proxy for elaboration
        avg_length = sum(len(idea.content.split()) for idea in ideas) / len(ideas)
        normalized_length = min(avg_length / 20, 1.0)  # Normalize to 0-1

        return normalized_length

    def _learn_from_session(self, session: Dict[str, Any]):
        """Learn from creativity session to improve future performance."""
        # Update technique effectiveness
        for technique in session['techniques_used']:
            current_effectiveness = 0.5  # Default effectiveness
            # This would update based on actual performance metrics

        # Adjust creativity level based on performance
        if session['metrics']['quality'] > 0.8:
            if self.creativity_level != CreativityLevel.EXPERT:
                current_level = self.creativity_level.value
                new_level = min(current_level + 0.1, 0.9)
                self.creativity_level = CreativityLevel(new_level)

    def _load_creativity_patterns(self) -> Dict[str, List[str]]:
        """Load creativity patterns and templates."""
        return {
            'innovation_patterns': [
                "combine existing concepts",
                "adapt from other domains",
                "challenge assumptions",
                "use random connections",
                "think metaphorically"
            ],
            'problem_solving_patterns': [
                "break into smaller parts",
                "work backwards from solution",
                "consider opposite approach",
                "remove constraints temporarily",
                "use extreme cases"
            ]
        }

    def _load_inspiration_sources(self) -> Dict[str, List[str]]:
        """Load sources of inspiration."""
        return {
            'nature': ['biomimicry', 'ecosystems', 'evolution', 'natural cycles'],
            'art': ['creativity techniques', 'aesthetics', 'composition', 'metaphor'],
            'science': ['scientific method', 'experimentation', 'patterns', 'principles'],
            'technology': ['innovation', 'disruption', 'efficiency', 'automation'],
            'philosophy': ['first principles', 'logic', 'ethics', 'paradigms']
        }

    def _load_analogy_database(self) -> Dict[str, List[str]]:
        """Load analogy database for cross-domain inspiration."""
        return {
            'systems': ['ecosystems', 'organisms', 'organizations', 'networks'],
            'processes': ['growth', 'evolution', 'learning', 'adaptation'],
            'structures': ['architecture', 'anatomy', 'crystals', 'patterns'],
            'relationships': ['symbiosis', 'competition', 'cooperation', 'hierarchy']
        }

# Example usage and testing
if __name__ == "__main__":
    # Create creativity booster
    booster = CreativityBooster("test_agent_1")

    # Test creativity enhancement
    problem = "How can we improve team communication in remote work?"
    context = {'team_size': 10, 'industry': 'technology', 'constraints': ['low_budget']}

    ideas, metrics = booster.boost_creativity(problem, context)

    print(f"Generated {len(ideas)} creative ideas")
    print(f"Quality metrics: Quality={metrics.idea_quality:.2f}, "
          f"Originality={metrics.originality_score:.2f}, "
          f"Diversity={metrics.diversity_score:.2f}")

    print("\nTop 3 ideas:")
    for i, idea in enumerate(ideas[:3], 1):
        print(f"{i}. [{idea.technique.value}] {idea.content}")
        print(f"   Confidence: {idea.confidence:.2f}, Tags: {', '.join(list(idea.tags)[:3])}")

    # Get creativity insights
    insights = booster.get_creativity_insights()
    print("\nCreativity Insights:", json.dumps(insights, indent=2))