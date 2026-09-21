"""
Semantic Memory Implementation
================================

Semantic memory stores generalized knowledge, concepts, and patterns extracted from experiences.
This mirrors human semantic memory which contains facts, concepts, and knowledge about the world.
"""

import math
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

from ..core.memory_base import MemoryBase, MemoryType, MemoryContent, MemoryMetadata


@dataclass
class ConceptualKnowledge:
    """Structured representation of conceptual knowledge"""
    concept: str
    definition: str
    relationships: Dict[str, List[str]]  # "is_a", "part_of", "related_to", etc.
    properties: Dict[str, Any]
    examples: List[str]
    confidence: float = 1.0
    source_memories: List[str] = None

    def __post_init__(self):
        if self.source_memories is None:
            self.source_memories = []


@dataclass
class LearnedPattern:
    """Pattern extracted from multiple experiences"""
    pattern_id: str
    description: str
    trigger_conditions: List[str]
    typical_outcomes: List[str]
    success_rate: float = 0.0
    frequency: int = 0
    confidence: float = 0.0
    source_memory_ids: List[str] = None
    last_confirmed: Optional[datetime] = None

    def __post_init__(self):
        if self.source_memory_ids is None:
            self.source_memory_ids = []
        if self.last_confirmed is None:
            self.last_confirmed = datetime.now()


class SemanticMemory(MemoryBase):
    """
    Semantic memory for conceptual knowledge, patterns, and generalizations.
    Created through consolidation of episodic memories and direct learning.
    """

    def __init__(
        self,
        content: str,
        concept: str = "",
        pattern_type: str = "generalization",
        source_memory_ids: List[str] = None,
        confidence: float = 1.0,
        importance: float = 7.0,
        **kwargs
    ):
        # Create metadata for semantic memory
        metadata = MemoryMetadata(
            source="consolidation",
            confidence=confidence,
            source_memory_ids=source_memory_ids or []
        )

        # Create structured content
        memory_content = MemoryContent(
            primary_content=content,
            summary=self._generate_semantic_summary(content),
            key_concepts=[concept] if concept else self._extract_concepts(content),
            extracted_patterns=self._identify_patterns(content)
        )

        super().__init__(memory_content, MemoryType.SEMANTIC, importance, metadata, **kwargs)

        # Semantic-specific fields
        self.concept = concept
        self.pattern_type = pattern_type  # "generalization", "rule", "concept", "schema"
        self.confidence = confidence

        # Conceptual knowledge structure
        self.conceptual_knowledge = self._build_conceptual_knowledge(content, concept)

        # Pattern information
        self.learned_patterns: List[LearnedPattern] = []
        self.rule_conditions: List[str] = []
        self.rule_consequences: List[str] = []

        # Knowledge graph connections
        self.semantic_network: Dict[str, List[str]] = defaultdict(list)
        self.concept_hierarchy: Dict[str, List[str]] = defaultdict(list)

        # Consolidation tracking
        self.consolidation_sources = source_memory_ids or []
        self.consolidation_date = datetime.now()
        self.validation_count = 0
        self.last_validated = None

        # Usage statistics
        self.application_count = 0
        self.application_successes = 0
        self.last_applied = None

    def get_capacity_requirement(self) -> int:
        """Return capacity requirement based on semantic complexity"""
        base_requirement = 15

        # Concept complexity
        concept_requirement = len(self.concept) if self.concept else 10

        # Pattern complexity
        pattern_requirement = len(self.learned_patterns) * 5

        # Network connections
        network_requirement = sum(len(connections) for connections in self.semantic_network.values()) * 2

        return base_requirement + concept_requirement + pattern_requirement + network_requirement

    def calculate_retrieval_score(self, query: str, context: Dict[str, Any]) -> float:
        """Calculate retrieval relevance score with semantic factors"""
        base_score = self._calculate_semantic_similarity(query)

        # Concept matching boost
        if "concepts" in context:
            concept_boost = self._calculate_concept_relevance(context["concepts"])
            base_score *= (1.0 + concept_boost * 0.3)

        # Pattern matching boost
        if "pattern_types" in context:
            pattern_boost = 1.0 if self.pattern_type in context["pattern_types"] else 0.0
            base_score *= (1.0 + pattern_boost * 0.2)

        # Confidence boost
        confidence_factor = self.confidence
        base_score *= (0.7 + 0.3 * confidence_factor)

        # Application success rate boost
        if self.application_count > 0:
            success_rate = self.application_successes / self.application_count
            base_score *= (0.8 + 0.2 * success_rate)

        # Recency of validation
        if self.last_validated:
            days_since_validation = (datetime.now() - self.last_validated).days
            recency_factor = math.exp(-days_since_validation / 90.0)  # 90-day half-life
            base_score *= (0.8 + 0.2 * recency_factor)

        return min(base_score, 1.0)

    def can_consolidate(self) -> bool:
        """Check if semantic memory can be further consolidated"""
        # Semantic memories don't typically consolidate further
        # But they can be updated or refined
        return False

    def add_learned_pattern(self, pattern: LearnedPattern) -> None:
        """Add a learned pattern to this semantic memory"""
        self.learned_patterns.append(pattern)
        self.content.extracted_patterns.append(pattern.description)

        # Update consolidation sources
        self.consolidation_sources.extend(pattern.source_memory_ids)
        self.consolidation_sources = list(set(self.consolidation_sources))  # Remove duplicates

    def validate_knowledge(self, outcome: bool, context: Dict[str, Any] = None) -> None:
        """Validate this semantic knowledge against real-world outcome"""
        self.validation_count += 1
        self.last_validated = datetime.now()

        # Update confidence based on validation
        if outcome:
            self.confidence = min(self.confidence * 1.05, 1.0)
        else:
            self.confidence = max(self.confidence * 0.95, 0.1)

        # Update validation metadata
        self.metadata.context["validation_history"] = self.metadata.context.get("validation_history", [])
        self.metadata.context["validation_history"].append({
            "timestamp": self.last_validated.isoformat(),
            "outcome": outcome,
            "context": context or {}
        })

    def apply_knowledge(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply this semantic knowledge to a given context"""
        self.application_count += 1
        self.last_applied = datetime.now()

        application_result = {
            "applied": True,
            "confidence": self.confidence,
            "knowledge_applied": self.concept or self.content.primary_content[:50],
            "relevant_patterns": [],
            "suggested_actions": [],
            "expected_outcomes": []
        }

        # Find relevant patterns
        for pattern in self.learned_patterns:
            if self._pattern_matches_context(pattern, context):
                application_result["relevant_patterns"].append(pattern.description)
                application_result["suggested_actions"].extend(pattern.typical_outcomes)

        # Add conceptual knowledge
        if self.conceptual_knowledge:
            application_result["conceptual_insights"] = {
                "concept": self.conceptual_knowledge.concept,
                "relationships": self.conceptual_knowledge.relationships,
                "properties": self.conceptual_knowledge.properties
            }

        return application_result

    def record_application_success(self, success: bool) -> None:
        """Record whether application of this knowledge was successful"""
        if success:
            self.application_successes += 1

        # Update confidence based on success rate
        if self.application_count >= 5:
            success_rate = self.application_successes / self.application_count
            target_confidence = 0.5 + success_rate * 0.5
            self.confidence = 0.9 * self.confidence + 0.1 * target_confidence

    def merge_with(self, other_semantic: 'SemanticMemory') -> None:
        """Merge with another semantic memory to create more general knowledge"""
        if not isinstance(other_semantic, SemanticMemory):
            return

        # Combine concepts
        combined_concept = f"{self.concept} + {other_semantic.concept}"
        self.concept = combined_concept

        # Merge content
        combined_content = f"{self.content.primary_content}. Additionally: {other_semantic.content.primary_content}"
        self.content.primary_content = combined_content

        # Merge patterns
        self.learned_patterns.extend(other_semantic.learned_patterns)

        # Merge consolidation sources
        self.consolidation_sources.extend(other_semantic.consolidation_sources)
        self.consolidation_sources = list(set(self.consolidation_sources))

        # Update confidence (weighted average)
        total_applications = self.application_count + other_semantic.application_count
        if total_applications > 0:
            self.confidence = (
                (self.confidence * self.application_count +
                 other_semantic.confidence * other_semantic.application_count) /
                total_applications
            )

        # Update importance
        self.importance = max(self.importance, other_semantic.importance)

        # Record merge
        self.metadata.context["merge_history"] = self.metadata.context.get("merge_history", [])
        self.metadata.context["merge_history"].append({
            "timestamp": datetime.now().isoformat(),
            "merged_with": other_semantic.id,
            "previous_concept": self.concept
        })

    def abstract_to_higher_level(self) -> 'SemanticMemory':
        """Create a more abstract version of this semantic memory"""
        if not self.conceptual_knowledge:
            return None

        # Create abstract concept
        abstract_concept = f"abstract_{self.concept}"
        abstract_content = f"General principle: {self.content.primary_content}"

        # Create new semantic memory at higher abstraction level
        abstract_memory = SemanticMemory(
            content=abstract_content,
            concept=abstract_concept,
            pattern_type="abstract_principle",
            source_memory_ids=[self.id],
            confidence=self.confidence * 0.9,  # Slightly lower confidence for abstraction
            importance=self.importance * 1.1   # Higher importance for abstractions
        )

        # Copy learned patterns
        abstract_memory.learned_patterns = [
            LearnedPattern(
                pattern_id=f"abstract_{p.pattern_id}",
                description=f"Abstract: {p.description}",
                trigger_conditions=p.trigger_conditions,
                typical_outcomes=p.typical_outcomes,
                success_rate=p.success_rate,
                frequency=p.frequency,
                confidence=p.confidence * 0.9,
                source_memory_ids=[self.id]
            )
            for p in self.learned_patterns
        ]

        # Link to original
        self.semantic_network["abstracts_to"].append(abstract_memory.id)
        abstract_memory.semantic_network["concretizes"].append(self.id)

        return abstract_memory

    def get_explanation(self, context: Dict[str, Any]) -> str:
        """Generate explanation of this knowledge in given context"""
        explanation_parts = []

        # Basic definition
        if self.concept:
            explanation_parts.append(f"Concept: {self.concept}")
        explanation_parts.append(f"Knowledge: {self.content.primary_content}")

        # Confidence
        explanation_parts.append(f"Confidence: {self.confidence:.2f}")

        # Supporting patterns
        if self.learned_patterns:
            explanation_parts.append("Supporting patterns:")
            for pattern in self.learned_patterns[:2]:  # Top 2 patterns
                explanation_parts.append(f"  - {pattern.description}")

        # Application context
        if self.application_count > 0:
            success_rate = self.application_successes / self.application_count
            explanation_parts.append(f"Application success rate: {success_rate:.1%}")

        return "\n".join(explanation_parts)

    def _generate_semantic_summary(self, content: str) -> str:
        """Generate semantic summary focusing on conceptual aspects"""
        # Extract key conceptual elements
        sentences = re.split(r'[.!?]+', content)
        conceptual_sentences = []

        # Look for sentences with conceptual indicators
        conceptual_indicators = ['is', 'are', 'means', 'represents', 'defines', 'concept', 'principle', 'rule', 'pattern', 'understands', 'knows']

        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in conceptual_indicators):
                conceptual_sentences.append(sentence)

        if conceptual_sentences:
            return " ".join(conceptual_sentences[:2])  # Top 2 conceptual sentences
        else:
            return content[:150] + "..." if len(content) > 150 else content

    def _extract_concepts(self, content: str) -> List[str]:
        """Extract concepts from content"""
        # Look for noun phrases and conceptual terms
        concept_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Capitalized terms
            r'\b(concept|principle|rule|pattern|idea|notion|theory)\b',  # Concept indicators
            r'\b(understanding|knowledge|belief|fact|truth)\b'  # Knowledge terms
        ]

        concepts = []
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend(matches)

        # Remove duplicates and common words
        common_words = {'this', 'that', 'with', 'from', 'have', 'been', 'said', 'each', 'time', 'will', 'about', 'after', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also'}
        concepts = [c for c in concepts if c.lower() not in common_words]

        return list(set(concepts))[:5]  # Return top 5 unique concepts

    def _identify_patterns(self, content: str) -> List[str]:
        """Identify patterns in the content"""
        patterns = []

        # Look for conditional patterns
        if_re_matches = re.findall(r'if\s+(.+?)\s*,?\s*then\s+(.+)', content, re.IGNORECASE)
        for condition, consequence in if_re_matches:
            patterns.append(f"If {condition.strip()}, then {consequence.strip()}")

        # Look for generalization patterns
        generalization_indicators = ['always', 'never', 'usually', 'typically', 'generally', 'tend to']
        for indicator in generalization_indicators:
            matches = re.findall(rf'{indicator}\s+(.+?)(?:\.|$)', content, re.IGNORECASE)
            patterns.extend([f"{indicator} {match.strip()}" for match in matches])

        # Look for causal patterns
        causal_words = ['because', 'since', 'due to', 'results in', 'leads to', 'causes']
        for word in causal_words:
            matches = re.findall(rf'(.+?)\s*{word}\s*(.+?)(?:\.|$)', content, re.IGNORECASE)
            for cause, effect in matches:
                patterns.append(f"{cause.strip()} {word} {effect.strip()}")

        return patterns[:3]  # Return top 3 patterns

    def _build_conceptual_knowledge(self, content: str, concept: str) -> ConceptualKnowledge:
        """Build conceptual knowledge structure"""
        return ConceptualKnowledge(
            concept=concept or self._extract_main_concept(content),
            definition=self._extract_definition(content),
            relationships=self._extract_relationships(content),
            properties=self._extract_properties(content),
            examples=self._extract_examples(content),
            confidence=self.confidence
        )

    def _extract_main_concept(self, content: str) -> str:
        """Extract the main concept from content"""
        # Look for the first capitalized term or conceptual phrase
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for "X is Y" pattern
            is_pattern = re.match(r'(.+?)\s+is\s+(.+)', sentence, re.IGNORECASE)
            if is_pattern:
                return is_pattern.group(1).strip()

        # Fallback to first few words
        words = content.split()[:3]
        return " ".join(words)

    def _extract_definition(self, content: str) -> str:
        """Extract definition from content"""
        # Look for definitional patterns
        definition_patterns = [
            r'(.+?)\s+is\s+(.+?)(?:\.|$)',
            r'(.+?)\s+means\s+(.+?)(?:\.|$)',
            r'(.+?)\s+refers\s+to\s+(.+?)(?:\.|$)',
            r'definition[s]?:\s*(.+?)(?:\.|$)'
        ]

        for pattern in definition_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(2).strip()

        return "Definition not explicitly stated"

    def _extract_relationships(self, content: str) -> Dict[str, List[str]]:
        """Extract semantic relationships from content"""
        relationships = defaultdict(list)

        # Is-a relationships
        is_a_matches = re.findall(r'(.+?)\s+is\s+a\s+(.+?)(?:\.|$)', content, re.IGNORECASE)
        for subject, predicate in is_a_matches:
            relationships["is_a"].append(f"{subject.strip()} is a {predicate.strip()}")

        # Part-of relationships
        part_of_matches = re.findall(r'(.+?)\s+is\s+part\s+of\s+(.+?)(?:\.|$)', content, re.IGNORECASE)
        for part, whole in part_of_matches:
            relationships["part_of"].append(f"{part.strip()} is part of {whole.strip()}")

        # Related concepts
        related_matches = re.findall(r'(.+?)\s+is\s+related\s+to\s+(.+?)(?:\.|$)', content, re.IGNORECASE)
        for concept1, concept2 in related_matches:
            relationships["related_to"].append(f"{concept1.strip()} is related to {concept2.strip()}")

        return dict(relationships)

    def _extract_properties(self, content: str) -> Dict[str, Any]:
        """Extract properties of the concept"""
        properties = {}

        # Look for adjectives and descriptions
        adjective_patterns = [
            r'is\s+(.+?)\s+and\s+(.+)',
            r'is\s+(.+?)\,',
            r'has\s+(.+?)\s+property',
            r'characterized\s+by\s+(.+)'
        ]

        for pattern in adjective_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for prop in match:
                        if prop.strip():
                            properties[f"property_{len(properties)}"] = prop.strip()
                else:
                    properties[f"property_{len(properties)}"] = match.strip()

        return properties

    def _extract_examples(self, content: str) -> List[str]:
        """Extract examples from content"""
        example_indicators = ['for example', 'for instance', 'such as', 'like', 'including']
        examples = []

        for indicator in example_indicators:
            pattern = rf'{indicator}\s+(.+?)(?:\.|$)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            examples.extend([match.strip() for match in matches])

        return examples[:3]  # Return top 3 examples

    def _calculate_semantic_similarity(self, query: str) -> float:
        """Calculate semantic similarity using concept overlap"""
        query_concepts = set(self._extract_concepts(query))
        memory_concepts = set(self.content.key_concepts)

        if not query_concepts or not memory_concepts:
            # Fallback to word overlap
            return self._calculate_word_overlap(query, self.content.primary_content)

        # Concept overlap
        concept_intersection = len(query_concepts & memory_concepts)
        concept_union = len(query_concepts | memory_concepts)
        concept_similarity = concept_intersection / concept_union if concept_union > 0 else 0.0

        # Word overlap
        word_similarity = self._calculate_word_overlap(query, self.content.primary_content)

        # Weighted combination
        return concept_similarity * 0.7 + word_similarity * 0.3

    def _calculate_word_overlap(self, text1: str, text2: str) -> float:
        """Calculate word overlap similarity"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_concept_relevance(self, target_concepts: List[str]) -> float:
        """Calculate relevance to target concepts"""
        if not target_concepts:
            return 0.0

        memory_concepts = set(self.content.key_concepts)
        target_set = set(target_concepts)

        intersection = len(memory_concepts & target_set)
        return intersection / len(target_set) if target_set else 0.0

    def _pattern_matches_context(self, pattern: LearnedPattern, context: Dict[str, Any]) -> bool:
        """Check if a pattern matches the given context"""
        # Simple pattern matching based on trigger conditions
        context_str = str(context).lower()

        for condition in pattern.trigger_conditions:
            if condition.lower() in context_str:
                return True

        return False