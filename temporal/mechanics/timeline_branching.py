"""
Timeline Branching - Alternate Timeline Generation and Tracking
Manages the creation, evolution, and convergence of parallel timelines
"""

import datetime
import uuid
import hashlib
import math
import random
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import networkx as nx
import numpy as np
from collections import defaultdict, deque

class TimelineType(Enum):
    """Types of timelines"""
    PRIME = "prime"  # Original/prime timeline
    BRANCH = "branch"  # Branch from parent timeline
    CONVERGED = "converged"  # Converged timelines
    COLLAPSED = "collapsed"  # Collapsed timeline
    ISOLATED = "isolated"  # Isolated timeline
    QUANTUM = "quantum"  # Quantum superposition timeline
    DREAM = "dream"  # Dream/virtual timeline
    SIMULATION = "simulation"  # Simulated timeline

class BranchTrigger(Enum):
    """Triggers that cause timeline branching"""
    MAJOR_EVENT_CHANGE = "major_event_change"
    PARADOX_CREATION = "paradox_creation"
    TEMPORAL_INTERVENTION = "temporal_intervention"
    CRITICAL_CHOICE = "critical_choice"
    DEATH_PREVENTION = "death_prevention"
    TECHNOLOGY_INTRODUCTION = "technology_introduction"
    CONSPIRACY_REVELATION = "conspiracy_revelation"
    QUANTUM_OBSERVATION = "quantum_observation"
    TEMPORAL_STORM = "temporal_storm"

class TimelineStability(Enum):
    """Stability levels of timelines"""
    STABLE = "stable"  # Fully stable timeline
    UNSTABLE = "unstable"  # Minor instability
    VOLATILE = "volatile"  # Major instability
    COLLAPSING = "collapsing"  # Timeline collapsing
    DISSOLVING = "dissolving"  # Timeline dissolving
    MERGED = "merged"  # Merged with another timeline

@dataclass
class TimelineEvent:
    """Event that defines timeline divergence"""
    event_id: str
    timestamp: datetime.datetime
    location: str
    description: str
    actors: List[str]
    change_magnitude: float  # 0.0 to 1.0
    temporal_significance: float  # 0.0 to 1.0
    divergence_point: bool = False
    convergence_point: bool = False
    quantum_locked: bool = False
    probability_amplitude: float = 1.0

@dataclass
class TimelineMetadata:
    """Metadata for timeline"""
    timeline_id: str
    name: str
    description: str
    created_at: datetime.datetime
    created_by: str  # What caused the branch
    parent_timeline_id: Optional[str]
    root_timeline_id: str
    timeline_type: TimelineType
    stability: TimelineStability
    divergence_strength: float  # 0.0 to 1.0
    convergence_potential: float  # 0.0 to 1.0
    temporal_drift: float  # How much timeline has drifted from parent
    population_density: float  # Population relative to prime
    technology_level: float  # Tech advancement relative to prime
    paradox_level: float  # 0.0 to 1.0
    isolation_factor: float  # 0.0 to 1.0, how isolated from other timelines
    quantum_coherence: float  # 0.0 to 1.0, quantum state coherence
    tags: Set[str] = field(default_factory=set)
    alternate_history_traits: List[str] = field(default_factory=list)

@dataclass
class TimelineBranch:
    """Represents a branch point in timeline"""
    branch_id: str
    parent_timeline_id: str
    child_timeline_id: str
    divergence_event: TimelineEvent
    branch_probability: float  # 0.0 to 1.0
    temporal_distance: datetime.timedelta
    causal_strength: float  # 0.0 to 1.0
    quantum_entanglement: float  # 0.0 to 1.0
    creation_method: str
    is_reversible: bool = False
    collapse_conditions: List[str] = field(default_factory=list)

@dataclass
class TimelineConvergence:
    """Represents convergence of two or more timelines"""
    convergence_id: str
    converging_timelines: List[str]
    convergence_point: datetime.datetime
    convergence_event: str
    convergence_strength: float  # 0.0 to 1.0
    result_timeline_id: str
    survival_probability: Dict[str, float]  # Timeline survival probability
    merge_properties: List[str]  # Properties that will be merged
    conflict_resolution: Dict[str, str]  # How conflicts are resolved

class TimelineGraph:
    """Graph structure managing timeline relationships"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.timelines: Dict[str, TimelineMetadata] = {}
        self.branches: Dict[str, TimelineBranch] = {}
        self.convergences: Dict[str, TimelineConvergence] = {}
        self.events: Dict[str, TimelineEvent] = {}
        self.quantum_states: Dict[str, Dict] = {}

    def add_timeline(self, metadata: TimelineMetadata) -> bool:
        """Add a timeline to the graph"""
        if metadata.timeline_id in self.timelines:
            return False

        self.timelines[metadata.timeline_id] = metadata
        self.graph.add_node(
            metadata.timeline_id,
            timeline_type=metadata.timeline_type.value,
            stability=metadata.stability.value,
            divergence_strength=metadata.divergence_strength,
            created_at=metadata.created_at.isoformat()
        )

        return True

    def add_branch(self, branch: TimelineBranch) -> bool:
        """Add a branch relationship between timelines"""
        if branch.parent_timeline_id not in self.timelines or \
           branch.child_timeline_id not in self.timelines:
            return False

        self.branches[branch.branch_id] = branch
        self.graph.add_edge(
            branch.parent_timeline_id,
            branch.child_timeline_id,
            branch_id=branch.branch_id,
            divergence_strength=branch.divergence_strength,
            causal_strength=branch.causal_strength,
            branch_probability=branch.branch_probability
        )

        return True

    def get_timeline_ancestors(self, timeline_id: str) -> List[str]:
        """Get all ancestor timelines"""
        try:
            return list(nx.ancestors(self.graph, timeline_id))
        except nx.NetworkXError:
            return []

    def get_timeline_descendants(self, timeline_id: str) -> List[str]:
        """Get all descendant timelines"""
        try:
            return list(nx.descendants(self.graph, timeline_id))
        except nx.NetworkXError:
            return []

    def find_convergence_candidates(self, timeline_id: str,
                                  time_window: datetime.timedelta) -> List[str]:
        """Find timelines that could converge with given timeline"""
        candidates = []

        for other_id, other_timeline in self.timelines.items():
            if other_id == timeline_id:
                continue

            # Check temporal proximity
            # For simplicity, we'll assume timelines are close if they share similar divergence points
            if other_timeline.root_timeline_id == self.timelines[timeline_id].root_timeline_id:
                # Check convergence potential
                if other_timeline.convergence_potential > 0.5:
                    candidates.append(other_id)

        return candidates

class TimelineBranchingManager:
    """Manages timeline branching and evolution"""

    def __init__(self):
        self.timeline_graph = TimelineGraph()
        self.branch_triggers: Dict[BranchTrigger, float] = {}
        self.convergence_threshold = 0.7
        self.collapse_threshold = 0.2
        self.max_timeline_depth = 100
        self.branching_cooldown = datetime.timedelta(hours=1)
        self.last_branch_time: Dict[str, datetime.datetime] = {}

        # Initialize branch triggers
        self._initialize_branch_triggers()

        # Create prime timeline
        self._create_prime_timeline()

    def _initialize_branch_triggers(self):
        """Initialize branch trigger probabilities"""
        self.branch_triggers = {
            BranchTrigger.MAJOR_EVENT_CHANGE: 0.8,
            BranchTrigger.PARADOX_CREATION: 0.9,
            BranchTrigger.TEMPORAL_INTERVENTION: 0.7,
            BranchTrigger.CRITICAL_CHOICE: 0.6,
            BranchTrigger.DEATH_PREVENTION: 0.8,
            BranchTrigger.TECHNOLOGY_INTRODUCTION: 0.5,
            BranchTrigger.CONSPIRACY_REVELATION: 0.4,
            BranchTrigger.QUANTUM_OBSERVATION: 0.3,
            BranchTrigger.TEMPORAL_STORM: 0.9
        }

    def _create_prime_timeline(self):
        """Create the prime timeline"""
        prime_metadata = TimelineMetadata(
            timeline_id="prime",
            name="Prime Timeline",
            description="The original, unaltered timeline",
            created_at=datetime.datetime.now(),
            created_by="system_initialization",
            parent_timeline_id=None,
            root_timeline_id="prime",
            timeline_type=TimelineType.PRIME,
            stability=TimelineStability.STABLE,
            divergence_strength=0.0,
            convergence_potential=1.0,
            temporal_drift=0.0,
            population_density=1.0,
            technology_level=1.0,
            paradox_level=0.0,
            isolation_factor=0.0,
            quantum_coherence=1.0,
            tags={"original", "prime", "stable"},
            alternate_history_traits=[]
        )

        self.timeline_graph.add_timeline(prime_metadata)

    async def evaluate_branching_potential(self,
                                         event: TimelineEvent,
                                         timeline_id: str) -> Dict[str, Any]:
        """Evaluate if an event should cause timeline branching"""

        if timeline_id not in self.timeline_graph.timelines:
            return {"should_branch": False, "error": "Timeline not found"}

        # Check cooldown period
        last_branch = self.last_branch_time.get(timeline_id)
        if last_branch and datetime.datetime.now() - last_branch < self.branching_cooldown:
            return {"should_branch": False, "reason": "Branching cooldown active"}

        timeline = self.timeline_graph.timelines[timeline_id]

        # Calculate branching probability
        base_probability = self._calculate_branching_probability(event, timeline)

        # Check if event is a divergence point
        is_divergence_point = event.divergence_point or base_probability > 0.7

        # Consider timeline stability
        if timeline.stability == TimelineStability.COLLAPSING:
            base_probability *= 0.5  # Less likely to branch from collapsing timeline

        # Check maximum depth
        ancestors = self.timeline_graph.get_timeline_ancestors(timeline_id)
        if len(ancestors) >= self.max_timeline_depth:
            base_probability *= 0.3  # Discourage very deep timelines

        should_branch = base_probability > 0.5 and is_divergence_point

        return {
            "should_branch": should_branch,
            "branching_probability": base_probability,
            "is_divergence_point": is_divergence_point,
            "reason": "High-impact temporal event" if should_branch else "Insufficient divergence potential"
        }

    def _calculate_branching_probability(self,
                                       event: TimelineEvent,
                                       timeline: TimelineMetadata) -> float:
        """Calculate probability that event causes timeline branching"""
        probability = 0.0

        # Base probability from event magnitude
        probability += event.change_magnitude * 0.4

        # Temporal significance
        probability += event.temporal_significance * 0.3

        # Timeline factors
        if timeline.stability == TimelineStability.UNSTABLE:
            probability *= 1.5
        elif timeline.stability == TimelineStability.VOLATILE:
            probability *= 2.0

        # Paradox level increases branching probability
        probability += timeline.paradox_level * 0.2

        # Isolation factor decreases branching (isolated timelines resist change)
        probability *= (1.0 - timeline.isolation_factor * 0.5)

        # Quantum coherence affects branching
        if timeline.quantum_coherence < 0.5:
            probability *= 1.3  # Low coherence means more branching

        return min(1.0, probability)

    async def create_timeline_branch(self,
                                   parent_timeline_id: str,
                                   divergence_event: TimelineEvent,
                                   branch_trigger: BranchTrigger,
                                   branch_properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new timeline branch"""

        if parent_timeline_id not in self.timeline_graph.timelines:
            return {"success": False, "error": "Parent timeline not found"}

        parent_timeline = self.timeline_graph.timelines[parent_timeline_id]

        # Generate new timeline ID
        branch_id = self._generate_timeline_id(parent_timeline_id, divergence_event)

        # Create child timeline metadata
        child_metadata = self._create_child_timeline_metadata(
            parent_timeline, branch_id, divergence_event, branch_trigger
        )

        # Add to graph
        if not self.timeline_graph.add_timeline(child_metadata):
            return {"success": False, "error": "Failed to add timeline to graph"}

        # Create branch relationship
        branch = TimelineBranch(
            branch_id=f"branch_{uuid.uuid4().hex[:8]}",
            parent_timeline_id=parent_timeline_id,
            child_timeline_id=branch_id,
            divergence_event=divergence_event,
            branch_probability=self.branch_triggers.get(branch_trigger, 0.5),
            temporal_distance=datetime.timedelta(hours=1),
            causal_strength=divergence_event.change_magnitude,
            quantum_entanglement=parent_timeline.quantum_coherence * 0.8,
            creation_method=branch_trigger.value,
            is_reversible=branch_properties.get("reversible", False) if branch_properties else False,
            collapse_conditions=branch_properties.get("collapse_conditions", []) if branch_properties else []
        )

        if not self.timeline_graph.add_branch(branch):
            # Rollback timeline creation
            del self.timeline_graph.timelines[branch_id]
            return {"success": False, "error": "Failed to create branch relationship"}

        # Update parent timeline
        self._update_parent_timeline_after_branch(parent_timeline, divergence_event)

        # Record branching event
        self.timeline_graph.events[divergence_event.event_id] = divergence_event

        # Update last branch time
        self.last_branch_time[parent_timeline_id] = datetime.datetime.now()

        # Apply quantum effects if applicable
        if branch_trigger == BranchTrigger.QUANTUM_OBSERVATION:
            await self._apply_quantum_branching_effects(branch_id, divergence_event)

        return {
            "success": True,
            "new_timeline_id": branch_id,
            "branch_id": branch.branch_id,
            "divergence_event": divergence_event.event_id,
            "branch_properties": {
                "divergence_strength": branch.causal_strength,
                "quantum_entanglement": branch.quantum_entanglement,
                "reversible": branch.is_reversible
            }
        }

    def _generate_timeline_id(self, parent_id: str, event: TimelineEvent) -> str:
        """Generate unique timeline ID"""
        # Create hash from parent ID and event
        hash_input = f"{parent_id}_{event.timestamp.isoformat()}_{event.description[:50]}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return f"timeline_{hash_value}"

    def _create_child_timeline_metadata(self,
                                      parent: TimelineMetadata,
                                      child_id: str,
                                      divergence_event: TimelineEvent,
                                      trigger: BranchTrigger) -> TimelineMetadata:
        """Create metadata for child timeline"""

        # Calculate divergence strength
        divergence_strength = min(1.0, divergence_event.change_magnitude *
                                self.branch_triggers.get(trigger, 0.5))

        # Determine stability
        if parent.stability == TimelineStability.STABLE and divergence_strength < 0.5:
            stability = TimelineStability.STABLE
        elif divergence_strength > 0.8:
            stability = TimelineStability.VOLATILE
        else:
            stability = TimelineStability.UNSTABLE

        # Create alternate history traits
        traits = self._generate_alternate_history_traits(divergence_event, trigger)

        return TimelineMetadata(
            timeline_id=child_id,
            name=f"Branch {child_id[-8:]}",
            description=f"Timeline branched from {parent.name} due to {divergence_event.description}",
            created_at=datetime.datetime.now(),
            created_by=trigger.value,
            parent_timeline_id=parent.timeline_id,
            root_timeline_id=parent.root_timeline_id,
            timeline_type=TimelineType.BRANCH,
            stability=stability,
            divergence_strength=divergence_strength,
            convergence_potential=max(0.1, 1.0 - divergence_strength),
            temporal_drift=parent.temporal_drift + divergence_strength * 0.1,
            population_density=parent.population_density * random.uniform(0.8, 1.2),
            technology_level=parent.technology_level * random.uniform(0.9, 1.1),
            paradox_level=min(1.0, parent.paradox_level + divergence_strength * 0.2),
            isolation_factor=parent.isolation_factor * random.uniform(0.9, 1.1),
            quantum_coherence=parent.quantum_coherence * random.uniform(0.8, 1.0),
            tags={"branch", trigger.value} | (parent.tags - {"prime"}),
            alternate_history_traits=traits
        )

    def _generate_alternate_history_traits(self,
                                         event: TimelineEvent,
                                         trigger: BranchTrigger) -> List[str]:
        """Generate traits describing how history diverged"""
        traits = []

        # Add trigger-specific traits
        if trigger == BranchTrigger.DEATH_PREVENTION:
            traits.append("famous_person_alive")
            traits.append("altered_succession")
        elif trigger == BranchTrigger.TECHNOLOGY_INTRODUCTION:
            traits.append("advanced_technology")
            traits.append("accelerated_progress")
        elif trigger == BranchTrigger.CONSPIRACY_REVELATION:
            traits.append("increased_transparency")
            traits.append("social_upheaval")
        elif trigger == BranchTrigger.MAJOR_EVENT_CHANGE:
            traits.append("altered_history")
            traits.append("different_outcomes")
        elif trigger == BranchTrigger.PARADOX_CREATION:
            traits.append("paradox_affected")
            traits.append("causal_instability")

        # Add magnitude-based traits
        if event.change_magnitude > 0.8:
            traits.append("radically_different")
        elif event.change_magnitude > 0.5:
            traits.append("significantly_changed")

        # Add location-based traits
        if "battle" in event.description.lower():
            traits.append("different_war_outcome")
        elif "election" in event.description.lower():
            traits.append("alternate_politics")
        elif "discovery" in event.description.lower():
            traits.append("changed_knowledge")

        return list(set(traits))  # Remove duplicates

    def _update_parent_timeline_after_branch(self,
                                           parent: TimelineMetadata,
                                           event: TimelineEvent):
        """Update parent timeline after branching"""
        # Reduce parent stability slightly
        if parent.stability == TimelineStability.STABLE:
            parent.stability = TimelineStability.UNSTABLE

        # Increase paradox level slightly
        parent.paradox_level = min(1.0, parent.paradox_level + 0.1)

        # Update isolation factor
        parent.isolation_factor = min(1.0, parent.isolation_factor + 0.05)

    async def _apply_quantum_branching_effects(self,
                                             timeline_id: str,
                                             event: TimelineEvent):
        """Apply quantum mechanical effects to timeline branching"""
        timeline = self.timeline_graph.timelines[timeline_id]

        # Create quantum superposition state
        quantum_state = {
            "superposition": True,
            "coherence": timeline.quantum_coherence,
            "entanglement_partners": [],
            "wavefunction_collapse_probability": 0.1,
            "quantum_events": [event.event_id]
        }

        self.timeline_graph.quantum_states[timeline_id] = quantum_state

        # Reduce quantum coherence due to observation
        timeline.quantum_coherence *= 0.9

    async def check_timeline_convergence(self,
                                       timeline_id: str,
                                       convergence_window: datetime.timedelta = datetime.timedelta(days=365)) -> List[Dict[str, Any]]:
        """Check for possible timeline convergences"""

        if timeline_id not in self.timeline_graph.timelines:
            return []

        timeline = self.timeline_graph.timelines[timeline_id]
        convergences = []

        # Find convergence candidates
        candidates = self.timeline_graph.find_convergence_candidates(timeline_id, convergence_window)

        for candidate_id in candidates:
            candidate = self.timeline_graph.timelines[candidate_id]

            # Calculate convergence probability
            convergence_probability = self._calculate_convergence_probability(timeline, candidate)

            if convergence_probability > self.convergence_threshold:
                convergence = {
                    "candidate_timeline_id": candidate_id,
                    "candidate_timeline_name": candidate.name,
                    "convergence_probability": convergence_probability,
                    "convergence_strength": min(1.0, convergence_probability * 1.2),
                    "predicted_convergence_time": datetime.datetime.now() + datetime.timedelta(days=30),
                    "merge_properties": self._predict_merge_properties(timeline, candidate),
                    "potential_conflicts": self._predict_convergence_conflicts(timeline, candidate)
                }
                convergences.append(convergence)

        # Sort by convergence probability
        convergences.sort(key=lambda x: x["convergence_probability"], reverse=True)

        return convergences

    def _calculate_convergence_probability(self,
                                        timeline1: TimelineMetadata,
                                        timeline2: TimelineMetadata) -> float:
        """Calculate probability that two timelines will converge"""
        probability = 0.0

        # Root timeline match is essential
        if timeline1.root_timeline_id != timeline2.root_timeline_id:
            return 0.0

        # Convergence potential of both timelines
        probability += (timeline1.convergence_potential + timeline2.convergence_potential) / 2

        # Temporal drift (less drift = higher convergence chance)
        drift_factor = 1.0 - abs(timeline1.temporal_drift - timeline2.temporal_drift)
        probability += drift_factor * 0.3

        # Similar stability levels converge better
        stability_match = 1.0 - abs(timeline1.stability.value.count('n') - timeline2.stability.value.count('n')) * 0.1
        probability += stability_match * 0.2

        # Technology and population similarity
        tech_similarity = 1.0 - abs(timeline1.technology_level - timeline2.technology_level)
        probability += tech_similarity * 0.1

        pop_similarity = 1.0 - abs(timeline1.population_density - timeline2.population_density)
        probability += pop_similarity * 0.1

        # Shared traits increase convergence
        shared_traits = set(timeline1.alternate_history_traits) & set(timeline2.alternate_history_traits)
        if shared_traits:
            probability += len(shared_traits) * 0.05

        return min(1.0, probability)

    def _predict_merge_properties(self,
                                timeline1: TimelineMetadata,
                                timeline2: TimelineMetadata) -> List[str]:
        """Predict which properties will merge in convergence"""
        merge_properties = []

        # Always merge shared traits
        shared_traits = set(timeline1.alternate_history_traits) & set(timeline2.alternate_history_traits)
        merge_properties.extend([f"trait_{trait}" for trait in shared_traits])

        # Merge high-convergence properties
        if timeline1.convergence_potential > 0.7 and timeline2.convergence_potential > 0.7:
            merge_properties.append("stability")
            merge_properties.append("quantum_coherence")

        # Merge similar technology levels
        if abs(timeline1.technology_level - timeline2.technology_level) < 0.2:
            merge_properties.append("technology")

        # Merge population if similar
        if abs(timeline1.population_density - timeline2.population_density) < 0.3:
            merge_properties.append("population")

        return merge_properties

    def _predict_convergence_conflicts(self,
                                     timeline1: TimelineMetadata,
                                     timeline2: TimelineMetadata) -> List[str]:
        """Predict conflicts in timeline convergence"""
        conflicts = []

        # Contradictory traits
        contradictory_pairs = [
            ("famous_person_alive", "famous_person_dead"),
            ("advanced_technology", "primitive_technology"),
            ("peace", "war"),
            ("prosperity", "collapse")
        ]

        traits1 = set(timeline1.alternate_history_traits)
        traits2 = set(timeline2.alternate_history_traits)

        for trait1, trait2 in contradictory_pairs:
            if trait1 in traits1 and trait2 in traits2:
                conflicts.append(f"trait_conflict: {trait1} vs {trait2}")
            elif trait2 in traits1 and trait1 in traits2:
                conflicts.append(f"trait_conflict: {trait2} vs {trait1}")

        # Stability conflicts
        if abs(timeline1.stability.value.count('n') - timeline2.stability.value.count('n')) > 1:
            conflicts.append("stability_mismatch")

        # Technology gap conflicts
        if abs(timeline1.technology_level - timeline2.technology_level) > 0.5:
            conflicts.append("technology_gap")

        # Paradox level conflicts
        if abs(timeline1.paradox_level - timeline2.paradox_level) > 0.4:
            conflicts.append("paradox_level_mismatch")

        return conflicts

    async def execute_timeline_convergence(self,
                                         timeline1_id: str,
                                         timeline2_id: str,
                                         convergence_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Execute convergence of two timelines"""

        if timeline1_id not in self.timeline_graph.timelines or \
           timeline2_id not in self.timeline_graph.timelines:
            return {"success": False, "error": "One or both timelines not found"}

        timeline1 = self.timeline_graph.timelines[timeline1_id]
        timeline2 = self.timeline_graph.timelines[timeline2_id]

        # Generate convergence ID
        convergence_id = f"convergence_{uuid.uuid4().hex[:8]}"

        # Create convergence event
        convergence_event = TimelineEvent(
            event_id=f"conv_event_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(),
            location="temporal_convergence_point",
            description=f"Convergence of {timeline1.name} and {timeline2.name}",
            actors=["temporal_mechanism"],
            change_magnitude=1.0,
            temporal_significance=1.0,
            divergence_point=False,
            convergence_point=True,
            probability_amplitude=1.0
        )

        # Create merged timeline metadata
        merged_metadata = self._create_merged_timeline_metadata(
            timeline1, timeline2, convergence_properties, convergence_id
        )

        # Add merged timeline
        if not self.timeline_graph.add_timeline(merged_metadata):
            return {"success": False, "error": "Failed to create merged timeline"}

        # Create convergence record
        convergence = TimelineConvergence(
            convergence_id=convergence_id,
            converging_timelines=[timeline1_id, timeline2_id],
            convergence_point=datetime.datetime.now(),
            convergence_event=convergence_event.event_id,
            convergence_strength=convergence_properties.get("strength", 0.7),
            result_timeline_id=merged_metadata.timeline_id,
            survival_probability={
                timeline1_id: convergence_properties.get("survival_1", 0.6),
                timeline2_id: convergence_properties.get("survival_2", 0.6)
            },
            merge_properties=convergence_properties.get("merge_properties", []),
            conflict_resolution=convergence_properties.get("conflict_resolution", {})
        )

        self.timeline_graph.convergences[convergence_id] = convergence

        # Mark original timelines as merged
        timeline1.timeline_type = TimelineType.CONVERGED
        timeline2.timeline_type = TimelineType.CONVERGED

        # Handle conflicts
        await self._resolve_convergence_conflicts(convergence)

        return {
            "success": True,
            "convergence_id": convergence_id,
            "merged_timeline_id": merged_metadata.timeline_id,
            "survival_probabilities": convergence.survival_probability,
            "merged_properties": convergence.merge_properties,
            "resolved_conflicts": list(convergence.conflict_resolution.keys())
        }

    def _create_merged_timeline_metadata(self,
                                       timeline1: TimelineMetadata,
                                       timeline2: TimelineMetadata,
                                       properties: Dict[str, Any],
                                       convergence_id: str) -> TimelineMetadata:
        """Create metadata for merged timeline"""

        # Merge traits
        merged_traits = list(set(timeline1.alternate_history_traits +
                                timeline2.alternate_history_traits))

        # Calculate merged properties
        merged_divergence = (timeline1.divergence_strength + timeline2.divergence_strength) / 2
        merged_convergence = max(timeline1.convergence_potential, timeline2.convergence_potential)
        merged_drift = (timeline1.temporal_drift + timeline2.temporal_drift) / 2
        merged_population = (timeline1.population_density + timeline2.population_density) / 2
        merged_tech = (timeline1.technology_level + timeline2.technology_level) / 2
        merged_paradox = max(timeline1.paradox_level, timeline2.paradox_level)
        merged_isolation = min(timeline1.isolation_factor, timeline2.isolation_factor)
        merged_coherence = (timeline1.quantum_coherence + timeline2.quantum_coherence) / 2

        # Determine stability
        stability_level = properties.get("stability", "unstable")
        stability = TimelineStability.STABLE if stability_level == "stable" else TimelineStability.UNSTABLE

        return TimelineMetadata(
            timeline_id=f"merged_{convergence_id}",
            name=f"Merged {timeline1.name} + {timeline2.name}",
            description=f"Timeline merged from {timeline1.name} and {timeline2.name}",
            created_at=datetime.datetime.now(),
            created_by="timeline_convergence",
            parent_timeline_id=None,
            root_timeline_id=timeline1.root_timeline_id,  # Keep same root
            timeline_type=TimelineType.CONVERGED,
            stability=stability,
            divergence_strength=merged_divergence,
            convergence_potential=merged_convergence,
            temporal_drift=merged_drift,
            population_density=merged_population,
            technology_level=merged_tech,
            paradox_level=merged_paradox,
            isolation_factor=merged_isolation,
            quantum_coherence=merged_coherence,
            tags={"merged", "converged"} | (timeline1.tags & timeline2.tags),
            alternate_history_traits=merged_traits
        )

    async def _resolve_convergence_conflicts(self, convergence: TimelineConvergence):
        """Resolve conflicts in timeline convergence"""
        # Simple conflict resolution - can be expanded
        resolution_methods = {
            "trait_conflict": "dominant_timeline",
            "stability_mismatch": "use_most_stable",
            "technology_gap": "average_technology",
            "paradox_level_mismatch": "use_higher"
        }

        for conflict_type in convergence.conflict_resolution.keys():
            if conflict_type in resolution_methods:
                convergence.conflict_resolution[conflict_type] = resolution_methods[conflict_type]

    async def check_timeline_collapse(self, timeline_id: str) -> Dict[str, Any]:
        """Check if timeline is at risk of collapse"""

        if timeline_id not in self.timeline_graph.timelines:
            return {"at_risk": False, "error": "Timeline not found"}

        timeline = self.timeline_graph.timelines[timeline_id]

        collapse_risk = 0.0
        collapse_factors = []

        # Check stability
        if timeline.stability == TimelineStability.COLLAPSING:
            collapse_risk += 0.8
            collapse_factors.append("already_collapsing")
        elif timeline.stability == TimelineStability.VOLATILE:
            collapse_risk += 0.5
            collapse_factors.append("volatile_stability")

        # Check paradox level
        if timeline.paradox_level > 0.8:
            collapse_risk += 0.6
            collapse_factors.append("high_paradox_level")

        # Check divergence strength (too much divergence causes instability)
        if timeline.divergence_strength > 0.9:
            collapse_risk += 0.4
            collapse_factors.append("excessive_divergence")

        # Check isolation
        if timeline.isolation_factor > 0.9:
            collapse_risk += 0.3
            collapse_factors.append("extreme_isolation")

        # Check quantum coherence
        if timeline.quantum_coherence < 0.1:
            collapse_risk += 0.5
            collapse_factors.append("quantum_decoherence")

        # Check timeline depth
        ancestors = self.timeline_graph.get_timeline_ancestors(timeline_id)
        if len(ancestors) > self.max_timeline_depth * 0.8:
            collapse_risk += 0.2
            collapse_factors.append("excessive_depth")

        at_risk = collapse_risk > self.collapse_threshold

        return {
            "at_risk": at_risk,
            "collapse_risk": collapse_risk,
            "collapse_factors": collapse_factors,
            "estimated_time_to_collapse": self._estimate_collapse_time(collapse_risk),
            "mitigation_suggestions": self._suggest_collapse_mitigation(timeline, collapse_factors)
        }

    def _estimate_collapse_time(self, risk: float) -> str:
        """Estimate time until timeline collapse"""
        if risk < 0.3:
            return "not_imminent"
        elif risk < 0.5:
            return "months"
        elif risk < 0.7:
            return "weeks"
        elif risk < 0.9:
            return "days"
        else:
            return "hours"

    def _suggest_collapse_mitigation(self,
                                   timeline: TimelineMetadata,
                                   factors: List[str]) -> List[str]:
        """Suggest ways to prevent timeline collapse"""
        suggestions = []

        for factor in factors:
            if factor == "volatile_stability":
                suggestions.append("Reduce temporal interventions")
                suggestions.append("Strengthen causality anchors")
            elif factor == "high_paradox_level":
                suggestions.append("Resolve existing paradoxes")
                suggestions.append("Limit paradox-creating activities")
            elif factor == "excessive_divergence":
                suggestions.append("Seek timeline convergence")
                suggestions.append("Stabilize key historical events")
            elif factor == "extreme_isolation":
                suggestions.append("Establish contact with parent timeline")
                suggestions.append("Reduce isolation factors")
            elif factor == "quantum_decoherence":
                suggestions.append("Quantum coherence restoration")
                suggestions.append("Reduce quantum observations")
            elif factor == "excessive_depth":
                suggestions.append("Timeline consolidation")
                suggestions.append("Merge with ancestor timeline")

        return suggestions

    def get_timeline_overview(self, timeline_id: str) -> Dict[str, Any]:
        """Get comprehensive overview of a timeline"""
        if timeline_id not in self.timeline_graph.timelines:
            return {"error": "Timeline not found"}

        timeline = self.timeline_graph.timelines[timeline_id]

        # Get relationships
        ancestors = self.timeline_graph.get_timeline_ancestors(timeline_id)
        descendants = self.timeline_graph.get_timeline_descendants(timeline_id)

        # Find related branches
        related_branches = [
            branch_id for branch_id, branch in self.timeline_graph.branches.items()
            if branch.parent_timeline_id == timeline_id or branch.child_timeline_id == timeline_id
        ]

        # Find related convergences
        related_convergences = [
            conv_id for conv_id, conv in self.timeline_graph.convergences.items()
            if timeline_id in conv.converging_timelines or timeline_id == conv.result_timeline_id
        ]

        return {
            "timeline_id": timeline_id,
            "name": timeline.name,
            "description": timeline.description,
            "type": timeline.timeline_type.value,
            "stability": timeline.stability.value,
            "created_at": timeline.created_at.isoformat(),
            "created_by": timeline.created_by,
            "parent_timeline": timeline.parent_timeline_id,
            "root_timeline": timeline.root_timeline_id,
            "ancestors_count": len(ancestors),
            "descendants_count": len(descendants),
            "related_branches": related_branches,
            "related_convergences": related_convergences,
            "properties": {
                "divergence_strength": timeline.divergence_strength,
                "convergence_potential": timeline.convergence_potential,
                "temporal_drift": timeline.temporal_drift,
                "population_density": timeline.population_density,
                "technology_level": timeline.technology_level,
                "paradox_level": timeline.paradox_level,
                "isolation_factor": timeline.isolation_factor,
                "quantum_coherence": timeline.quantum_coherence
            },
            "tags": list(timeline.tags),
            "alternate_history_traits": timeline.alternate_history_traits,
            "quantum_state": self.timeline_graph.quantum_states.get(timeline_id, None)
        }

    def export_timeline_data(self, timeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Export timeline data for analysis"""
        if timeline_id:
            # Export single timeline
            return self.get_timeline_overview(timeline_id)
        else:
            # Export all timelines
            return {
                "timelines": {
                    tid: self.get_timeline_overview(tid)
                    for tid in self.timeline_graph.timelines.keys()
                },
                "branches": {
                    branch_id: {
                        "parent": branch.parent_timeline_id,
                        "child": branch.child_timeline_id,
                        "divergence_event": branch.divergence_event.event_id,
                        "strength": branch.causal_strength,
                        "quantum_entanglement": branch.quantum_entanglement
                    }
                    for branch_id, branch in self.timeline_graph.branches.items()
                },
                "convergences": {
                    conv_id: {
                        "converging_timelines": conv.converging_timelines,
                        "result_timeline": conv.result_timeline_id,
                        "strength": conv.convergence_strength,
                        "survival_probabilities": conv.survival_probability
                    }
                    for conv_id, conv in self.timeline_graph.convergences.items()
                },
                "quantum_states": self.timeline_graph.quantum_states
            }

# Export main classes
__all__ = [
    'TimelineBranchingManager',
    'TimelineGraph',
    'TimelineMetadata',
    'TimelineBranch',
    'TimelineConvergence',
    'TimelineEvent',
    'TimelineType',
    'BranchTrigger',
    'TimelineStability'
]