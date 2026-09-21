#!/usr/bin/env python3
"""
Advanced Creativity Module for DMLogn8n AI Agents

This module implements sophisticated creative capabilities that enable AI agents to
generate novel ideas, solve problems creatively, engage in artistic expression, and
think outside conventional boundaries. The system combines divergent thinking,
pattern recognition, conceptual blending, and generative models.

Key Features:
- Divergent and convergent thinking processes
- Conceptual blending and metaphor generation
- Creative problem-solving and ideation
- Artistic content generation (stories, poetry, music)
- Pattern innovation and analogical reasoning
- Serendipity and unexpected connections
- Creative evaluation and refinement
- Cross-domain creativity and synthesis
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
import random
import math
import itertools
from collections import defaultdict, deque, Counter
import re
import hashlib
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CreativityType(Enum):
    """Types of creative processes"""
    DIVERGENT_THINKING = "divergent_thinking"
    CONVERGENT_THINKING = "convergent_thinking"
    CONCEPTUAL_BLENDING = "conceptual_blending"
    ANALOGICAL_REASONING = "analogical_reasoning"
    PATTERN_INNOVATION = "pattern_innovation"
    ARTISTIC_GENERATION = "artistic_generation"
    PROBLEM_SOLVING = "problem_solving"
    SERENDIPITY = "serendipity"

class CreativeDomain(Enum):
    """Creative domains"""
    LITERARY = "literary"
    VISUAL = "visual"
    MUSICAL = "musical"
    MATHEMATICAL = "mathematical"
    SCIENTIFIC = "scientific"
    SOCIAL = "social"
    TECHNICAL = "technical"
    PHILOSOPHICAL = "philosophical"

class IdeaQuality(Enum):
    """Quality levels for creative ideas"""
    NOVEL = "novel"
    USEFUL = "useful"
    ELEGANT = "elegant"
    TRANSFORMATIVE = "transformative"
    BREAKTHROUGH = "breakthrough"

@dataclass
class CreativeIdea:
    """Represents a creative idea"""
    id: str
    content: str
    domain: CreativeDomain
    creativity_type: CreativityType
    novelty_score: float
    usefulness_score: float
    elegance_score: float
    overall_quality: float
    source_concepts: List[str]
    generated_by: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Concept:
    """Represents a concept for creative blending"""
    name: str
    domain: str
    attributes: Dict[str, Any]
    relationships: List[str]
    abstraction_level: float
    emotional_valence: float
    complexity: float

@dataclass
class CreativeConstraint:
    """Represents a constraint in creative process"""
    type: str
    description: str
    weight: float
    is_hard: bool = True  # Hard constraint vs soft constraint

class ConceptualBlender(nn.Module):
    """Neural network for conceptual blending"""

    def __init__(self, concept_dim: int = 256, hidden_dim: int = 512):
        super().__init__()
        self.concept_dim = concept_dim
        self.hidden_dim = hidden_dim

        # Concept encoders
        self.concept_encoder = nn.Sequential(
            nn.Linear(concept_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )

        # Blending mechanism
        self.blending_network = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim)
        )

        # Attention for conceptual relationships
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            batch_first=True
        )

        # Creativity scoring
        self.creativity_scorer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, concept1_emb, concept2_emb):
        """Blend two concepts"""
        # Encode concepts
        enc1 = self.concept_encoder(concept1_emb)
        enc2 = self.concept_encoder(concept2_emb)

        # Apply attention
        concepts = torch.stack([enc1, enc2], dim=1)
        attended, _ = self.attention(concepts, concepts, concepts)

        # Blend concepts
        blended = self.blending_network(
            torch.cat([attended[:, 0], attended[:, 1]], dim=-1)
        )

        # Score creativity
        creativity_score = self.creativity_scorer(blended)

        return blended, creativity_score

class GenerativeModel(nn.Module):
    """Generative model for creative content"""

    def __init__(self, vocab_size: int = 10000, embedding_dim: int = 256, hidden_dim: int = 512):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # Transformer-like architecture
        self.transformer = nn.Transformer(
            d_model=embedding_dim,
            nhead=8,
            num_encoder_layers=6,
            num_decoder_layers=6,
            dim_feedforward=hidden_dim,
            batch_first=True
        )

        # Output projection
        self.output_proj = nn.Linear(embedding_dim, vocab_size)

        # Creativity parameters
        self.creativity_temperature = nn.Parameter(torch.tensor(1.0))
        self.novelty_weight = nn.Parameter(torch.tensor(0.3))

    def forward(self, input_ids, target_ids=None):
        """Generate creative content"""
        # Embed input
        input_emb = self.embedding(input_ids)

        if target_ids is not None:
            # Training mode
            target_emb = self.embedding(target_ids)
            output = self.transformer(input_emb, target_emb)
            logits = self.output_proj(output)
            return logits
        else:
            # Generation mode
            output = self.transformer(input_emb)
            logits = self.output_proj(output)
            return logits

    def generate_creative(self, input_ids, max_length=100, creativity_factor=1.0):
        """Generate content with creativity factor"""
        with torch.no_grad():
            input_emb = self.embedding(input_ids)
            generated = input_emb

            for _ in range(max_length):
                output = self.transformer(generated)
                logits = self.output_proj(output[:, -1:, :])

                # Apply creativity temperature
                temp = self.creativity_temperature * creativity_factor
                probs = F.softmax(logits / temp, dim=-1)

                # Sample with novelty bias
                next_token = torch.multinomial(probs.squeeze(1), 1)
                next_emb = self.embedding(next_token)
                generated = torch.cat([generated, next_emb], dim=1)

            return generated

class DivergentThinking:
    """Divergent thinking processes for idea generation"""

    def __init__(self):
        self.ideation_techniques = {
            'brainstorming': self._brainstorming,
            'mind_mapping': self._mind_mapping,
            'scamper': self._scamper,
            'random_association': self._random_association,
            'reverse_thinking': self._reverse_thinking,
            'analogical_thinking': self._analogical_thinking
        }
        self.idea_database = []
        self.concept_network = {}

    def generate_ideas(self, problem: str, technique: str = 'brainstorming',
                      num_ideas: int = 10) -> List[CreativeIdea]:
        """Generate creative ideas using specified technique"""
        if technique not in self.ideation_techniques:
            technique = 'brainstorming'

        generator = self.ideation_techniques[technique]
        raw_ideas = generator(problem, num_ideas)

        # Convert to CreativeIdea objects
        creative_ideas = []
        for i, idea_content in enumerate(raw_ideas):
            idea = CreativeIdea(
                id=f"{technique}_{int(time.time())}_{i}",
                content=idea_content,
                domain=self._classify_idea_domain(idea_content),
                creativity_type=CreativityType.DIVERGENT_THINKING,
                novelty_score=self._assess_novelty(idea_content),
                usefulness_score=self._assess_usefulness(idea_content, problem),
                elegance_score=self._assess_elegance(idea_content),
                overall_quality=0.0,
                source_concepts=self._extract_concepts(idea_content),
                generated_by=technique
            )
            idea.overall_quality = self._calculate_overall_quality(idea)
            creative_ideas.append(idea)

        self.idea_database.extend(creative_ideas)
        return creative_ideas

    def _brainstorming(self, problem: str, num_ideas: int) -> List[str]:
        """Generate ideas through free association"""
        ideas = []
        problem_words = problem.lower().split()

        # Word associations
        associations = {
            'problem': ['challenge', 'opportunity', 'situation', 'issue'],
            'solve': ['address', 'tackle', 'resolve', 'handle'],
            'create': ['make', 'build', 'develop', 'design'],
            'improve': ['enhance', 'upgrade', 'optimize', 'refine'],
            'new': ['innovative', 'fresh', 'original', 'novel']
        }

        for i in range(num_ideas):
            # Randomly associate words
            seed_word = random.choice(problem_words)
            if seed_word in associations:
                associated = random.choice(associations[seed_word])
            else:
                associated = seed_word

            # Generate idea template
            templates = [
                f"What if we {associated} the {problem}?",
                f"Consider {associated}-ing to address {problem}",
                f"Apply {associated} thinking to {problem}",
                f"Explore {associated} solutions for {problem}",
                f"Innovate through {associated} approaches to {problem}"
            ]

            idea = random.choice(templates)
            ideas.append(idea)

        return ideas

    def _mind_mapping(self, problem: str, num_ideas: int) -> List[str]:
        """Generate ideas through mind mapping"""
        central_concept = problem
        branches = ['how', 'why', 'what', 'when', 'where', 'who']
        ideas = []

        for i in range(num_ideas):
            branch = random.choice(branches)
            sub_concepts = self._generate_sub_concepts(central_concept, branch)

            for sub_concept in sub_concepts[:2]:  # Take first 2
                idea = f"{branch.capitalize()}: {sub_concept} for {central_concept}"
                ideas.append(idea)

        return ideas[:num_ideas]

    def _scamper(self, problem: str, num_ideas: int) -> List[str]:
        """SCAMPER technique (Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse)"""
        scamper_actions = [
            f"Substitute elements in {problem}",
            f"Combine {problem} with something unexpected",
            f"Adapt {problem} to a new context",
            f"Modify or magnify aspects of {problem}",
            f"Put {problem} to another use",
            f"Eliminate or simplify aspects of {problem}",
            f"Reverse or rearrange elements of {problem}"
        ]

        ideas = []
        for i in range(num_ideas):
            action = random.choice(scamper_actions)
            elaboration = f" by considering innovative approaches"
            idea = action + elaboration
            ideas.append(idea)

        return ideas

    def _random_association(self, problem: str, num_ideas: int) -> List[str]:
        """Generate ideas through random word association"""
        random_words = ['butterfly', 'mountain', 'ocean', 'forest', 'city', 'technology',
                       'nature', 'art', 'music', 'space', 'time', 'energy', 'light', 'color']

        ideas = []
        for i in range(num_ideas):
            random_word = random.choice(random_words)
            idea = f"Apply principles of {random_word} to solve {problem}"
            ideas.append(idea)

        return ideas

    def _reverse_thinking(self, problem: str, num_ideas: int) -> List[str]:
        """Generate ideas by reversing the problem"""
        ideas = []
        reverse_prompts = [
            f"What would make {problem} worse?",
            f"How could we achieve the opposite of solving {problem}?",
            f"What if we embraced the opposite of typical solutions for {problem}?",
            f"Consider anti-solutions for {problem}",
            f"Explore paradoxical approaches to {problem}"
        ]

        for i in range(num_ideas):
            prompt = random.choice(reverse_prompts)
            ideas.append(prompt)

        return ideas

    def _analogical_thinking(self, problem: str, num_ideas: int) -> List[str]:
        """Generate ideas through analogical reasoning"""
        analogies = [
            ("nature", "ecosystem", "balance"),
            ("technology", "algorithm", "efficiency"),
            ("art", "composition", "harmony"),
            ("music", "rhythm", "pattern"),
            ("architecture", "structure", "foundation")
        ]

        ideas = []
        for i in range(num_ideas):
            domain, concept, principle = random.choice(analogies)
            idea = f"Like {concept} in {domain}, apply {principle} to {problem}"
            ideas.append(idea)

        return ideas

    def _generate_sub_concepts(self, concept: str, branch: str) -> List[str]:
        """Generate sub-concepts for mind mapping"""
        sub_concepts = {
            'how': [f"methods for {concept}", f"processes of {concept}", f"techniques for {concept}"],
            'why': [f"reasons for {concept}", f"purposes of {concept}", f"motivations behind {concept}"],
            'what': [f"components of {concept}", f"elements in {concept}", f"aspects of {concept}"],
            'when': [f"timing for {concept}", f"occasions of {concept}", f"schedules for {concept}"],
            'where': [f"locations for {concept}", f"contexts of {concept}", f"environments for {concept}"],
            'who': [f"people involved in {concept}", f"stakeholders of {concept}", f"users of {concept}"]
        }
        return sub_concepts.get(branch, [f"aspects of {concept}"])

    def _classify_idea_domain(self, idea: str) -> CreativeDomain:
        """Classify idea into creative domain"""
        domain_keywords = {
            CreativeDomain.LITERARY: ['story', 'narrative', 'character', 'plot', 'writing', 'poetry'],
            CreativeDomain.VISUAL: ['visual', 'image', 'color', 'design', 'art', 'aesthetic'],
            CreativeDomain.MUSICAL: ['music', 'sound', 'rhythm', 'melody', 'harmony', 'beat'],
            CreativeDomain.MATHEMATICAL: ['pattern', 'formula', 'calculation', 'logic', 'number'],
            CreativeDomain.SCIENTIFIC: ['experiment', 'hypothesis', 'research', 'discovery', 'theory'],
            CreativeDomain.SOCIAL: ['people', 'community', 'relationship', 'society', 'culture'],
            CreativeDomain.TECHNICAL: ['technology', 'system', 'tool', 'mechanism', 'device'],
            CreativeDomain.PHILOSOPHICAL: ['meaning', 'purpose', 'ethics', 'wisdom', 'truth']
        }

        idea_lower = idea.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in idea_lower for keyword in keywords):
                return domain

        return CreativeDomain.TECHNICAL  # Default

    def _assess_novelty(self, idea: str) -> float:
        """Assess novelty of an idea"""
        # Simple novelty assessment based on uncommon words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word for word in idea.lower().split() if word not in common_words]

        if not words:
            return 0.0

        # Check word rarity (simplified)
        rare_words = ['innovative', 'revolutionary', 'paradigm', 'synergy', 'ecosystem', 'holistic']
        rare_count = sum(1 for word in words if word in rare_words)

        novelty = min(rare_count / len(words) * 2, 1.0)
        return novelty

    def _assess_usefulness(self, idea: str, problem: str) -> float:
        """Assess usefulness of an idea for the problem"""
        # Check if idea contains solution-oriented words
        solution_words = ['solve', 'solution', 'address', 'resolve', 'fix', 'improve', 'enhance']
        idea_lower = idea.lower()

        solution_score = sum(1 for word in solution_words if word in idea_lower)
        problem_overlap = len(set(problem.lower().split()) & set(idea_lower.split()))

        usefulness = min((solution_score + problem_overlap) / 10, 1.0)
        return usefulness

    def _assess_elegance(self, idea: str) -> float:
        """Assess elegance (simplicity and sophistication)"""
        words = idea.split()

        # Elegance factors: not too simple, not too complex
        length_score = 1.0 - abs(len(words) - 10) / 20  # Optimal around 10 words

        # Check for sophisticated vocabulary
        elegant_words = ['elegant', 'refined', 'sophisticated', 'nuanced', 'balanced']
        elegance_score = sum(1 for word in words if word.lower() in elegant_words) / len(words) if words else 0

        return (length_score + elegance_score) / 2

    def _calculate_overall_quality(self, idea: CreativeIdea) -> float:
        """Calculate overall quality score"""
        return (idea.novelty_score * 0.4 +
                idea.usefulness_score * 0.4 +
                idea.elegance_score * 0.2)

    def _extract_concepts(self, idea: str) -> List[str]:
        """Extract key concepts from idea"""
        # Simple concept extraction
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words = [word for word in idea.lower().split() if word not in stop_words and len(word) > 3]
        return words[:5]  # Top 5 concepts

class ConceptualBlending:
    """Conceptual blending for creative synthesis"""

    def __init__(self):
        self.concepts = {}
        self.blend_history = []
        self.blending_rules = {
            'attribute_transfer': self._attribute_transfer,
            'relation_mapping': self._relation_mapping,
            'structure_merging': self._structure_merging,
            'metaphorical_projection': self._metaphorical_projection
        }

    def add_concept(self, concept: Concept):
        """Add a concept to the blending space"""
        self.concepts[concept.name] = concept

    def create_blend(self, concept1_name: str, concept2_name: str,
                    blend_type: str = 'attribute_transfer') -> Optional[CreativeIdea]:
        """Create a blend of two concepts"""
        if concept1_name not in self.concepts or concept2_name not in self.concepts:
            return None

        concept1 = self.concepts[concept1_name]
        concept2 = self.concepts[concept2_name]

        if blend_type not in self.blending_rules:
            blend_type = 'attribute_transfer'

        blend_result = self.blending_rules[blend_type](concept1, concept2)

        if blend_result:
            idea = CreativeIdea(
                id=f"blend_{int(time.time())}",
                content=blend_result,
                domain=CreativeDomain.TECHNICAL,  # Default domain
                creativity_type=CreativityType.CONCEPTUAL_BLENDING,
                novelty_score=self._assess_blend_novelty(concept1, concept2),
                usefulness_score=self._assess_blend_usefulness(blend_result),
                elegance_score=self._assess_blend_elegance(blend_result),
                overall_quality=0.0,
                source_concepts=[concept1_name, concept2_name],
                generated_by=f"conceptual_blending_{blend_type}"
            )
            idea.overall_quality = idea.novelty_score * 0.5 + idea.usefulness_score * 0.3 + idea.elegance_score * 0.2

            self.blend_history.append(idea)
            return idea

        return None

    def _attribute_transfer(self, concept1: Concept, concept2: Concept) -> Optional[str]:
        """Transfer attributes from one concept to another"""
        # Select key attributes from concept1 to transfer to concept2
        key_attrs = list(concept1.attributes.keys())[:3]

        if not key_attrs:
            return None

        transferred_attrs = []
        for attr in key_attrs:
            value = concept1.attributes[attr]
            transferred_attrs.append(f"{attr} as {value}")

        blend_content = f"Imagine {concept2.name} with {', '.join(transferred_attrs)}"
        return blend_content

    def _relation_mapping(self, concept1: Concept, concept2: Concept) -> Optional[str]:
        """Map relations from one concept to another"""
        if not concept1.relationships or not concept2.relationships:
            return None

        relation1 = random.choice(concept1.relationships)
        relation2 = random.choice(concept2.relationships)

        blend_content = f"Apply the '{relation1}' relationship from {concept1.name} to '{relation2}' in {concept2.name}"
        return blend_content

    def _structure_merging(self, concept1: Concept, concept2: Concept) -> Optional[str]:
        """Merge structural aspects of two concepts"""
        # Create a hybrid structure
        structure1 = list(concept1.attributes.keys())[:2]
        structure2 = list(concept2.attributes.keys())[:2]

        if not structure1 or not structure2:
            return None

        blend_content = f"Combine {concept1.name}'s {', '.join(structure1)} with {concept2.name}'s {', '.join(structure2)}"
        return blend_content

    def _metaphorical_projection(self, concept1: Concept, concept2: Concept) -> Optional[str]:
        """Create metaphorical projection between concepts"""
        blend_content = f"Treat {concept2.name} as if it were {concept1.name}, applying {concept1.name}'s principles to {concept2.name}"
        return blend_content

    def _assess_blend_novelty(self, concept1: Concept, concept2: Concept) -> float:
        """Assess novelty of a concept blend"""
        # Novelty based on domain distance and abstraction difference
        domain_distance = 1.0 if concept1.domain != concept2.domain else 0.3
        abstraction_diff = abs(concept1.abstraction_level - concept2.abstraction_level)

        novelty = (domain_distance + abstraction_diff) / 2
        return min(novelty, 1.0)

    def _assess_blend_usefulness(self, blend_content: str) -> float:
        """Assess usefulness of blend result"""
        # Check for utility indicators
        utility_words = ['useful', 'effective', 'efficient', 'powerful', 'innovative']
        content_lower = blend_content.lower()

        utility_score = sum(1 for word in utility_words if word in content_lower) / len(utility_words)
        return utility_score

    def _assess_blend_elegance(self, blend_content: str) -> float:
        """Assess elegance of blend result"""
        # Elegance based on clarity and sophistication
        words = blend_content.split()
        clarity_score = 1.0 - min(len(words) / 50, 1.0)  # Prefer concise expressions

        # Check for elegant language
        elegant_indicators = ['harmonious', 'balanced', 'refined', 'seamless']
        elegance_score = sum(1 for word in elegant_indicators if word in content_lower) / len(elegant_indicators)

        return (clarity_score + elegance_score) / 2

class ArtisticGenerator:
    """Generator for artistic content"""

    def __init__(self):
        self.generative_model = None
        self.style_templates = {
            'poetry': {
                'structures': ['haiku', 'sonnet', 'free_verse', 'limerick'],
                'themes': ['nature', 'love', 'time', 'technology', 'society'],
                'moods': ['melancholic', 'joyful', 'contemplative', 'passionate']
            },
            'story': {
                'structures': ['hero_journey', 'mystery', 'romance', 'adventure'],
                'themes': ['growth', 'conflict', 'discovery', 'transformation'],
                'genres': ['fantasy', 'scifi', 'realism', 'magical_realism']
            },
            'music': {
                'structures': ['verse_chorus', 'aba_form', 'rondo', 'fugue'],
                'moods': ['upbeat', 'somber', 'mysterious', 'energetic'],
                'instruments': ['piano', 'guitar', 'orchestra', 'electronic']
            }
        }

    def initialize_model(self, vocab_size: int = 10000):
        """Initialize the generative model"""
        self.generative_model = GenerativeModel(vocab_size)
        logger.info("Artistic generative model initialized")

    def generate_poetry(self, theme: str, style: str = 'free_verse', length: int = 50) -> str:
        """Generate poetry"""
        if not self.generative_model:
            return self._template_poetry(theme, style, length)

        # Neural generation would go here
        return self._template_poetry(theme, style, length)

    def _template_poetry(self, theme: str, style: str, length: int) -> str:
        """Template-based poetry generation"""
        templates = {
            'haiku': [
                f"{theme} dances gently,\nwhispers of ancient wisdom,\npeace unfolds within.",
                f"Golden {theme} shines,\nnature's eternal rhythm,\nmoment captured still."
            ],
            'free_verse': [
                f"In the realm of {theme},\nmysteries unfold like petals\nrevealing hidden truths.",
                f"Where {theme} resides,\ndreams take flight on wings of hope,\njourneying beyond stars."
            ]
        }

        style_templates = templates.get(style, templates['free_verse'])
        return random.choice(style_templates)

    def generate_story_prompt(self, genre: str, theme: str) -> str:
        """Generate a story prompt"""
        prompt_templates = {
            'fantasy': f"In a world where {theme} holds magical power, a young protagonist discovers they can shape reality through {theme}.",
            'scifi': f" aboard a generation ship, humanity's last hope depends on understanding {theme} before reaching their destination.",
            'mystery': f"When a series of impossible deaths are all connected to {theme}, a detective must unravel the supernatural conspiracy.",
            'romance': f"Two souls, bound by their shared connection to {theme}, must overcome societal barriers to be together."
        }

        return prompt_templates.get(genre, f"A story about {theme} that explores human nature and destiny.")

    def generate_lyrics(self, theme: str, mood: str, structure: str = 'verse_chorus') -> str:
        """Generate song lyrics"""
        verse_templates = {
            'upbeat': [
                f"Dancing through the {theme}, feeling alive tonight,\nEvery moment shining ever so bright.",
                f"Heart beating like a drum to the rhythm of {theme},\nNothing can stop this magical energy."
            ],
            'somber': [
                f"In the shadows of {theme}, memories remain,\nWhispers of yesterday in the gentle rain.",
                f"Carrying the weight of {theme} on my soul,\nSearching for meaning to make me whole."
            ]
        }

        chorus_templates = {
            'upbeat': f"Oh, {theme} brings us together, forever and always!",
            'somber': f"Lost in the echoes of {theme}, time stands still."
        }

        verse = random.choice(verse_templates.get(mood, verse_templates['upbeat']))
        chorus = random.choice(list(chorus_templates.values()))

        if structure == 'verse_chorus':
            return f"{verse}\n\n{chorus}\n\n{verse}"
        else:
            return f"{verse}\n\n{verse}"

class CreativityModule:
    """
    Advanced Creativity Module for AI Agents

    This class integrates multiple creative processes to enable AI agents to generate
    novel ideas, solve problems creatively, and engage in artistic expression.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Creative components
        self.divergent_thinking = DivergentThinking()
        self.conceptual_blending = ConceptualBlending()
        self.artistic_generator = ArtisticGenerator()
        self.neural_blender = ConceptualBlender()

        # Idea management
        self.idea_database = []
        self.idea_evaluation_criteria = {}
        self.creative_constraints = []

        # Performance metrics
        self.metrics = {
            'total_ideas_generated': 0,
            'breakthrough_ideas': 0,
            'average_idea_quality': 0.0,
            'creativity_sessions': 0,
            'successful_blends': 0,
            'artistic_creations': 0,
            'novelty_score': 0.0,
            'diversity_index': 0.0
        }

        # State
        self.current_session_id = None
        self.session_ideas = []
        self.inspiration_level = 0.5

        logger.info(f"Creativity Module initialized for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'max_ideas_per_session': 50,
            'quality_threshold': 0.6,
            'novelty_threshold': 0.5,
            'enable_neural_generation': True,
            'idea_retention_days': 30,
            'cross_domain_inspiration': True,
            'serendipity_factor': 0.1
        }

    def start_creativity_session(self, problem: str, session_type: str = 'divergent') -> str:
        """Start a new creativity session"""
        self.current_session_id = f"session_{int(time.time())}"
        self.session_ideas = []
        self.inspiration_level = 0.5

        logger.info(f"Started creativity session {self.current_session_id} for: {problem}")
        return self.current_session_id

    def generate_creative_ideas(self, problem: str, techniques: List[str] = None,
                              num_ideas: int = 10) -> List[CreativeIdea]:
        """Generate creative ideas using multiple techniques"""
        if techniques is None:
            techniques = ['brainstorming', 'conceptual_blending', 'analogical_thinking']

        all_ideas = []

        for technique in techniques:
            try:
                if technique in self.divergent_thinking.ideation_techniques:
                    # Divergent thinking techniques
                    ideas = self.divergent_thinking.generate_ideas(problem, technique, num_ideas // len(techniques))
                    all_ideas.extend(ideas)

                elif technique == 'conceptual_blending':
                    # Conceptual blending (need predefined concepts)
                    blend_ideas = self._generate_conceptual_blends(problem, num_ideas // len(techniques))
                    all_ideas.extend(blend_ideas)

                elif technique == 'artistic_generation':
                    # Artistic approach
                    artistic_ideas = self._generate_artistic_ideas(problem, num_ideas // len(techniques))
                    all_ideas.extend(artistic_ideas)

            except Exception as e:
                logger.error(f"Error in technique {technique}: {e}")

        # Evaluate and filter ideas
        evaluated_ideas = self._evaluate_ideas(all_ideas)
        filtered_ideas = [idea for idea in evaluated_ideas if idea.overall_quality >= self.config['quality_threshold']]

        # Update metrics
        self._update_metrics(all_ideas, filtered_ideas)

        # Store ideas
        self.idea_database.extend(filtered_ideas)
        self.session_ideas.extend(filtered_ideas)

        return filtered_ideas

    def _generate_conceptual_blends(self, problem: str, num_ideas: int) -> List[CreativeIdea]:
        """Generate ideas through conceptual blending"""
        # Define some basic concepts for blending
        base_concepts = [
            Concept("technology", "technical", {"speed": "fast", "efficiency": "high"}, [], 0.7, 0.2, 0.8),
            Concept("nature", "natural", {"growth": "organic", "balance": "dynamic"}, [], 0.5, 0.8, 0.6),
            Concept("art", "artistic", {"beauty": "subjective", "expression": "creative"}, [], 0.6, 0.9, 0.7),
            Concept("science", "scientific", {"precision": "accurate", "method": "systematic"}, [], 0.8, 0.1, 0.9),
            Concept("emotion", "emotional", {"intensity": "variable", "depth": "profound"}, [], 0.4, 0.7, 0.5)
        ]

        # Add concepts to blender
        for concept in base_concepts:
            self.conceptual_blending.add_concept(concept)

        # Generate blends
        blends = []
        concept_names = [c.name for c in base_concepts]

        for i in range(min(num_ideas, len(concept_names) * 2)):
            concept1, concept2 = random.sample(concept_names, 2)
            blend = self.conceptual_blending.create_blend(concept1, concept2)
            if blend:
                blends.append(blend)

        return blends

    def _generate_artistic_ideas(self, problem: str, num_ideas: int) -> List[CreativeIdea]:
        """Generate ideas through artistic approaches"""
        artistic_ideas = []

        # Generate poetry ideas
        poetry_prompt = self.artistic_generator.generate_story_prompt('poetry', problem)
        poetry_idea = CreativeIdea(
            id=f"poetry_{int(time.time())}",
            content=f"Create a poem about {problem}: {poetry_prompt}",
            domain=CreativeDomain.LITERARY,
            creativity_type=CreativityType.ARTISTIC_GENERATION,
            novelty_score=0.7,
            usefulness_score=0.5,
            elegance_score=0.8,
            overall_quality=0.67,
            source_concepts=[problem, 'poetry'],
            generated_by='artistic_generation'
        )
        artistic_ideas.append(poetry_idea)

        # Generate story ideas
        story_genres = ['fantasy', 'scifi', 'mystery', 'romance']
        for genre in story_genres[:min(num_ideas-1, len(story_genres))]:
            story_prompt = self.artistic_generator.generate_story_prompt(genre, problem)
            story_idea = CreativeIdea(
                id=f"story_{genre}_{int(time.time())}",
                content=f"Write a {genre} story: {story_prompt}",
                domain=CreativeDomain.LITERARY,
                creativity_type=CreativityType.ARTISTIC_GENERATION,
                novelty_score=0.6,
                usefulness_score=0.4,
                elegance_score=0.7,
                overall_quality=0.57,
                source_concepts=[problem, genre, 'story'],
                generated_by='artistic_generation'
            )
            artistic_ideas.append(story_idea)

        return artistic_ideas

    def _evaluate_ideas(self, ideas: List[CreativeIdea]) -> List[CreativeIdea]:
        """Evaluate and score ideas"""
        for idea in ideas:
            # Additional evaluation criteria can be added here
            if idea.overall_quality > 0.8:
                idea.metadata['quality_level'] = 'breakthrough'
            elif idea.overall_quality > 0.6:
                idea.metadata['quality_level'] = 'high'
            else:
                idea.metadata['quality_level'] = 'moderate'

        # Sort by quality
        ideas.sort(key=lambda x: x.overall_quality, reverse=True)
        return ideas

    def _update_metrics(self, all_ideas: List[CreativeIdea], filtered_ideas: List[CreativeIdea]):
        """Update performance metrics"""
        self.metrics['total_ideas_generated'] += len(all_ideas)
        self.metrics['breakthrough_ideas'] += sum(1 for idea in filtered_ideas if idea.overall_quality > 0.8)
        self.metrics['successful_blends'] += sum(1 for idea in filtered_ideas if idea.creativity_type == CreativityType.CONCEPTUAL_BLENDING)
        self.metrics['artistic_creations'] += sum(1 for idea in filtered_ideas if idea.domain == CreativeDomain.LITERARY)

        # Update average quality
        if self.idea_database:
            avg_quality = sum(idea.overall_quality for idea in self.idea_database) / len(self.idea_database)
            self.metrics['average_idea_quality'] = avg_quality

        # Update novelty score
        if self.idea_database:
            avg_novelty = sum(idea.novelty_score for idea in self.idea_database) / len(self.idea_database)
            self.metrics['novelty_score'] = avg_novelty

        # Calculate diversity index (simplified)
        domains = [idea.domain for idea in self.idea_database]
        if domains:
            domain_counts = Counter(domains)
            diversity = len(domain_counts) / len(CreativeDomain)
            self.metrics['diversity_index'] = diversity

    def find_similar_ideas(self, idea: CreativeIdea, threshold: float = 0.7) -> List[CreativeIdea]:
        """Find similar ideas in the database"""
        similar_ideas = []
        idea_concepts = set(idea.source_concepts)

        for stored_idea in self.idea_database:
            if stored_idea.id == idea.id:
                continue

            stored_concepts = set(stored_idea.source_concepts)
            similarity = len(idea_concepts & stored_concepts) / len(idea_concepts | stored_concepts)

            if similarity >= threshold:
                similar_ideas.append(stored_idea)

        return similar_ideas

    def combine_ideas(self, ideas: List[CreativeIdea]) -> Optional[CreativeIdea]:
        """Combine multiple ideas into a new idea"""
        if len(ideas) < 2:
            return None

        # Extract concepts from all ideas
        all_concepts = []
        for idea in ideas:
            all_concepts.extend(idea.source_concepts)

        # Create combined idea
        combined_content = f"Synthesis of concepts: {', '.join(set(all_concepts))}"
        combined_novelty = sum(idea.novelty_score for idea in ideas) / len(ideas) * 1.2  # Boost novelty
        combined_usefulness = sum(idea.usefulness_score for idea in ideas) / len(ideas) * 0.9
        combined_elegance = sum(idea.elegance_score for idea in ideas) / len(ideas)

        combined_idea = CreativeIdea(
            id=f"combined_{int(time.time())}",
            content=combined_content,
            domain=ideas[0].domain,  # Use first idea's domain
            creativity_type=CreativityType.CONCEPTUAL_BLENDING,
            novelty_score=min(combined_novelty, 1.0),
            usefulness_score=min(combined_usefulness, 1.0),
            elegance_score=min(combined_elegance, 1.0),
            overall_quality=0.0,
            source_concepts=list(set(all_concepts)),
            generated_by='idea_combination',
            metadata={'source_idea_ids': [idea.id for idea in ideas]}
        )

        combined_idea.overall_quality = (
            combined_idea.novelty_score * 0.4 +
            combined_idea.usefulness_score * 0.4 +
            combined_idea.elegance_score * 0.2
        )

        return combined_idea

    def generate_serendipitous_connections(self) -> List[CreativeIdea]:
        """Generate unexpected connections between existing ideas"""
        if len(self.idea_database) < 2:
            return []

        serendipitous_ideas = []
        num_connections = min(5, len(self.idea_database) // 2)

        for _ in range(num_connections):
            # Randomly select two ideas
            idea1, idea2 = random.sample(self.idea_database, 2)

            # Check if they're from different domains (more likely to be novel)
            if idea1.domain != idea2.domain:
                combined = self.combine_ideas([idea1, idea2])
                if combined and combined.novelty_score > 0.7:
                    combined.creativity_type = CreativityType.SERENDIPITY
                    combined.metadata['serendipitous'] = True
                    serendipitous_ideas.append(combined)

        return serendipitous_ideas

    def refine_idea(self, idea: CreativeIdea, refinement_direction: str = 'improve_quality') -> CreativeIdea:
        """Refine an existing idea"""
        refined_idea = copy.deepcopy(idea)
        refined_idea.id = f"refined_{idea.id}_{int(time.time())}"

        if refinement_direction == 'improve_quality':
            # Enhance elegance and usefulness
            refined_idea.elegance_score = min(idea.elegance_score * 1.2, 1.0)
            refined_idea.usefulness_score = min(idea.usefulness_score * 1.1, 1.0)
            refined_idea.content = f"Refined version: {idea.content} (enhanced for quality and effectiveness)"

        elif refinement_direction == 'increase_novelty':
            # Increase novelty through unexpected associations
            refined_idea.novelty_score = min(idea.novelty_score * 1.3, 1.0)
            unexpected_concept = random.choice(['quantum', 'biological', 'cosmic', 'digital', 'ancient'])
            refined_idea.source_concepts.append(unexpected_concept)
            refined_idea.content = f"Innovative twist: {idea.content} + {unexpected_concept} perspective"

        elif refinement_direction == 'practical_application':
            # Focus on practical aspects
            refined_idea.usefulness_score = min(idea.usefulness_score * 1.4, 1.0)
            refined_idea.content = f"Practical application: {idea.content} (focused on real-world implementation)"

        # Recalculate overall quality
        refined_idea.overall_quality = (
            refined_idea.novelty_score * 0.4 +
            refined_idea.usefulness_score * 0.4 +
            refined_idea.elegance_score * 0.2
        )

        refined_idea.metadata['refined_from'] = idea.id
        refined_idea.metadata['refinement_type'] = refinement_direction

        return refined_idea

    def get_creativity_summary(self) -> Dict[str, Any]:
        """Get comprehensive creativity module summary"""
        return {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.copy(),
            'current_session': self.current_session_id,
            'session_ideas_count': len(self.session_ideas),
            'total_ideas_count': len(self.idea_database),
            'idea_domains': {
                domain.value: sum(1 for idea in self.idea_database if idea.domain == domain)
                for domain in CreativeDomain
            },
            'creativity_types': {
                ctype.value: sum(1 for idea in self.idea_database if idea.creativity_type == ctype)
                for ctype in CreativityType
            },
            'top_ideas': [
                {
                    'id': idea.id,
                    'content': idea.content[:100] + '...' if len(idea.content) > 100 else idea.content,
                    'quality': idea.overall_quality,
                    'domain': idea.domain.value,
                    'type': idea.creativity_type.value
                }
                for idea in sorted(self.idea_database, key=lambda x: x.overall_quality, reverse=True)[:5]
            ],
            'inspiration_level': self.inspiration_level
        }

    def export_ideas(self, filepath: str, format: str = 'json'):
        """Export ideas to file"""
        ideas_data = []
        for idea in self.idea_database:
            idea_dict = {
                'id': idea.id,
                'content': idea.content,
                'domain': idea.domain.value,
                'creativity_type': idea.creativity_type.value,
                'novelty_score': idea.novelty_score,
                'usefulness_score': idea.usefulness_score,
                'elegance_score': idea.elegance_score,
                'overall_quality': idea.overall_quality,
                'source_concepts': idea.source_concepts,
                'generated_by': idea.generated_by,
                'timestamp': idea.timestamp.isoformat(),
                'metadata': idea.metadata
            }
            ideas_data.append(idea_dict)

        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump({
                    'agent_id': self.agent_id,
                    'export_timestamp': datetime.now().isoformat(),
                    'total_ideas': len(ideas_data),
                    'ideas': ideas_data
                }, f, indent=2)

        logger.info(f"Exported {len(ideas_data)} ideas to {filepath}")

# Utility functions for integration
async def create_creativity_module(agent_id: str, config: Optional[Dict] = None) -> CreativityModule:
    """Factory function to create and initialize creativity module"""
    module = CreativityModule(agent_id, config)
    module.artistic_generator.initialize_model()
    return module

def benchmark_creativity_performance(creativity_module: CreativityModule,
                                   test_problems: List[str]) -> Dict:
    """Benchmark creativity module performance"""
    import time

    start_time = time.time()
    all_results = []

    for problem in test_problems:
        problem_start = time.time()

        # Generate ideas
        ideas = creativity_module.generate_creative_ideas(
            problem,
            techniques=['brainstorming', 'conceptual_blending', 'artistic_generation'],
            num_ideas=15
        )

        problem_time = time.time() - problem_start

        all_results.append({
            'problem': problem,
            'ideas_generated': len(ideas),
            'average_quality': sum(idea.overall_quality for idea in ideas) / len(ideas) if ideas else 0,
            'time': problem_time
        })

    total_time = time.time() - start_time

    return {
        'total_time': total_time,
        'problems_processed': len(test_problems),
        'average_ideas_per_problem': sum(r['ideas_generated'] for r in all_results) / len(all_results),
        'average_quality': sum(r['average_quality'] for r in all_results) / len(all_results),
        'results': all_results,
        'final_metrics': creativity_module.metrics
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create creativity module
        config = {
            'max_ideas_per_session': 30,
            'quality_threshold': 0.5,
            'enable_neural_generation': True
        }

        creativity_module = await create_creativity_module("test_agent", config)

        # Test creative idea generation
        problem = "How can we make learning more engaging for students?"

        session_id = creativity_module.start_creativity_session(problem, "divergent")

        ideas = creativity_module.generate_creative_ideas(
            problem,
            techniques=['brainstorming', 'conceptual_blending', 'analogical_thinking'],
            num_ideas=20
        )

        print(f"\nGenerated {len(ideas)} creative ideas for: {problem}")
        print("\nTop 5 ideas:")
        for i, idea in enumerate(ideas[:5]):
            print(f"\n{i+1}. {idea.content}")
            print(f"   Quality: {idea.overall_quality:.2f} | Novelty: {idea.novelty_score:.2f} | Usefulness: {idea.usefulness_score:.2f}")
            print(f"   Domain: {idea.domain.value} | Type: {idea.creativity_type.value}")

        # Test conceptual blending
        blend_idea = creativity_module._generate_conceptual_blends(problem, 5)
        if blend_idea:
            print(f"\nConceptual blend example: {blend_idea[0].content}")

        # Test artistic generation
        poetry_idea = creativity_module.artistic_generator.generate_poetry("learning", "free_verse", 30)
        print(f"\nGenerated poetry: {poetry_idea}")

        # Test serendipitous connections
        if len(creativity_module.idea_database) > 5:
            serendipitous = creativity_module.generate_serendipitous_connections()
            if serendipitous:
                print(f"\nSerendipitous connection: {serendipitous[0].content}")

        # Test idea refinement
        if ideas:
            refined = creativity_module.refine_idea(ideas[0], 'improve_quality')
            print(f"\nRefined idea: {refined.content}")
            print(f"Original quality: {ideas[0].overall_quality:.2f} -> Refined: {refined.overall_quality:.2f}")

        # Get creativity summary
        summary = creativity_module.get_creativity_summary()
        print("\nCreativity module summary:")
        print(json.dumps(summary, indent=2, default=str))

        # Export ideas
        creativity_module.export_ideas("/tmp/creative_ideas.json")

    asyncio.run(main())