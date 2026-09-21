#!/usr/bin/env python3
"""
Advanced Cognitive Architecture for DMLogn8n AI Agents

This module implements a sophisticated cognitive architecture that mimics human
cognitive processes including attention, perception, working memory, and executive
functions. The architecture is designed to create truly intelligent, adaptive
AI agents that can engage in complex reasoning and meaningful interactions.

Key Features:
- Multi-layered cognitive processing
- Dynamic attention management
- Hierarchical perception system
- Executive function control
- Cognitive load management
- Context-aware processing
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
from collections import deque, defaultdict
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CognitiveState(Enum):
    """Cognitive states for the agent"""
    IDLE = "idle"
    ATTENTIVE = "attentive"
    PROCESSING = "processing"
    DECIDING = "deciding"
    ACTING = "acting"
    REFLECTING = "reflecting"
    OVERLOADED = "overloaded"

class AttentionLevel(Enum):
    """Attention levels for cognitive processing"""
    MINIMAL = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    FOCUSED = 0.9
    INTENSE = 1.0

@dataclass
class Stimulus:
    """Represents an external or internal stimulus"""
    id: str
    content: Any
    modality: str  # visual, auditory, textual, emotional, etc.
    intensity: float
    timestamp: datetime
    source: str
    relevance_score: float = 0.0
    priority: float = 0.5

@dataclass
class CognitiveContext:
    """Represents the current cognitive context"""
    situation: str
    goals: List[str]
    emotional_state: Dict[str, float]
    attention_level: AttentionLevel
    cognitive_load: float
    working_memory: List[Any]
    active_concepts: List[str]
    temporal_context: Dict[str, Any]
    social_context: Dict[str, Any]

class AttentionNetwork(nn.Module):
    """Neural attention network for stimulus selection and focus"""

    def __init__(self, input_dim: int = 512, hidden_dim: int = 256, num_heads: int = 8):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads

        # Multi-head attention mechanism
        self.query = nn.Linear(input_dim, hidden_dim)
        self.key = nn.Linear(input_dim, hidden_dim)
        self.value = nn.Linear(input_dim, hidden_dim)

        # Attention regulation
        self.attention_gate = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

        # Priority weighting network
        self.priority_network = nn.Sequential(
            nn.Linear(input_dim + 4, hidden_dim),  # +4 for metadata
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, stimuli_embeddings, metadata):
        """
        Compute attention weights for stimuli

        Args:
            stimuli_embeddings: Tensor of stimulus embeddings
            metadata: Tensor of stimulus metadata (intensity, relevance, etc.)
        """
        batch_size, num_stimuli, _ = stimuli_embeddings.shape

        # Multi-head attention
        Q = self.query(stimuli_embeddings)
        K = self.key(stimuli_embeddings)
        V = self.value(stimuli_embeddings)

        # Reshape for multi-head attention
        Q = Q.view(batch_size, num_stimuli, self.num_heads, -1).transpose(1, 2)
        K = K.view(batch_size, num_stimuli, self.num_heads, -1).transpose(1, 2)
        V = V.view(batch_size, num_stimuli, self.num_heads, -1).transpose(1, 2)

        # Scaled dot-product attention
        attention_scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.hidden_dim // self.num_heads)
        attention_weights = F.softmax(attention_scores, dim=-1)
        attended_output = torch.matmul(attention_weights, V)

        # Combine heads
        attended_output = attended_output.transpose(1, 2).contiguous().view(
            batch_size, num_stimuli, -1
        )

        # Apply attention gate
        attention_gates = self.attention_gate(attended_output)
        gated_output = attended_output * attention_gates

        # Priority weighting with metadata
        combined_input = torch.cat([stimuli_embeddings, metadata], dim=-1)
        priority_weights = self.priority_network(combined_input)

        # Final attention weights
        final_weights = priority_weights * attention_gates.squeeze(-1)
        normalized_weights = F.softmax(final_weights, dim=-1)

        return normalized_weights, gated_output

class WorkingMemoryNetwork(nn.Module):
    """Neural network for working memory operations"""

    def __init__(self, embedding_dim: int = 512, memory_size: int = 7):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.memory_size = memory_size

        # Memory encoding
        self.memory_encoder = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(embedding_dim, embedding_dim)
        )

        # Memory retrieval
        self.retrieval_network = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=8,
            batch_first=True
        )

        # Memory updating
        self.update_gate = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim),
            nn.Sigmoid()
        )

        # Forgetting mechanism
        self.forget_gate = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim // 2),
            nn.ReLU(),
            nn.Linear(embedding_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, current_stimulus, memory_buffer):
        """Process working memory operations"""
        if memory_buffer is None or len(memory_buffer) == 0:
            return current_stimulus.unsqueeze(1), torch.zeros(1, 1, self.embedding_dim)

        # Encode current stimulus
        encoded_stimulus = self.memory_encoder(current_stimulus)

        # Retrieve relevant memories
        memory_tensor = torch.stack(memory_buffer).unsqueeze(0)
        retrieved_memory, attention_weights = self.retrieval_network(
            encoded_stimulus.unsqueeze(1), memory_tensor, memory_tensor
        )

        # Update memory buffer
        combined = torch.cat([encoded_stimulus, retrieved_memory.squeeze(1)], dim=-1)
        update_signal = self.update_gate(combined)
        updated_memory = encoded_stimulus * update_signal + retrieved_memory.squeeze(1) * (1 - update_signal)

        # Apply forgetting
        forget_signal = self.forget_gate(updated_memory)
        final_memory = updated_memory * forget_signal

        return torch.cat([encoded_stimulus.unsqueeze(1), final_memory.unsqueeze(1)], dim=1), final_memory.unsqueeze(1)

class ExecutiveFunctionNetwork(nn.Module):
    """Executive function control network"""

    def __init__(self, input_dim: int = 512, num_functions: int = 8):
        super().__init__()
        self.num_functions = num_functions

        # Cognitive control
        self.control_network = nn.Sequential(
            nn.Linear(input_dim, input_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(input_dim, input_dim),
            nn.ReLU(),
            nn.Linear(input_dim, num_functions),
            nn.Sigmoid()
        )

        # Task switching
        self.switch_network = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.Linear(input_dim // 2, num_functions),
            nn.Softmax(dim=-1)
        )

        # Inhibition control
        self.inhibition_network = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.Linear(input_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, current_state):
        """Generate executive control signals"""
        control_signals = self.control_network(current_state)
        switch_signals = self.switch_network(current_state)
        inhibition_signal = self.inhibition_network(current_state)

        return {
            'control': control_signals,
            'switching': switch_signals,
            'inhibition': inhibition_signal
        }

class CognitiveArchitecture:
    """
    Advanced Cognitive Architecture for AI Agents

    This class implements a comprehensive cognitive system that includes:
    - Attention management and stimulus selection
    - Working memory operations
    - Executive function control
    - Cognitive load monitoring
    - Context-aware processing
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Initialize neural networks
        self.attention_network = AttentionNetwork()
        self.working_memory_network = WorkingMemoryNetwork()
        self.executive_function_network = ExecutiveFunctionNetwork()

        # Cognitive state
        self.state = CognitiveState.IDLE
        self.cognitive_load = 0.0
        self.attention_level = AttentionLevel.MODERATE

        # Working memory buffer
        self.working_memory_buffer = deque(maxlen=self.config['working_memory_size'])
        self.long_term_memory_buffer = []

        # Attention and perception
        self.active_stimuli = []
        self.attention_history = deque(maxlen=100)
        self.perception_threshold = self.config['perception_threshold']

        # Context management
        self.current_context = CognitiveContext(
            situation="unknown",
            goals=[],
            emotional_state={},
            attention_level=AttentionLevel.MODERATE,
            cognitive_load=0.0,
            working_memory=[],
            active_concepts=[],
            temporal_context={},
            social_context={}
        )

        # Performance metrics
        self.performance_metrics = {
            'attention_accuracy': 0.0,
            'memory_efficiency': 0.0,
            'processing_speed': 0.0,
            'decision_quality': 0.0,
            'adaptation_rate': 0.0
        }

        # Threading for async processing
        self.processing_lock = threading.Lock()
        self.background_tasks = set()

        logger.info(f"Cognitive Architecture initialized for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration for cognitive architecture"""
        return {
            'working_memory_size': 7,
            'attention_capacity': 4,
            'perception_threshold': 0.3,
            'cognitive_load_threshold': 0.8,
            'learning_rate': 0.001,
            'attention_decay_rate': 0.95,
            'memory_consolidation_interval': 60,  # seconds
            'max_stimuli_per_cycle': 10,
            'processing_timeout': 5.0,
            'enable_metacognition': True,
            'enable_predictive_processing': True
        }

    async def perceive_stimulus(self, stimulus: Stimulus) -> bool:
        """
        Process incoming stimulus and determine if it should be attended to

        Args:
            stimulus: The incoming stimulus to process

        Returns:
            bool: True if stimulus was perceived and registered
        """
        try:
            # Filter by perception threshold
            if stimulus.intensity < self.perception_threshold:
                return False

            # Check cognitive load
            if self.cognitive_load > self.config['cognitive_load_threshold']:
                # Only high-priority stimuli get through when overloaded
                if stimulus.priority < 0.8:
                    return False

            # Calculate relevance score
            relevance = self._calculate_relevance(stimulus)
            stimulus.relevance_score = relevance

            # Add to active stimuli
            self.active_stimuli.append(stimulus)

            # Update cognitive state
            self._update_cognitive_state()

            return True

        except Exception as e:
            logger.error(f"Error perceiving stimulus: {e}")
            return False

    def _calculate_relevance(self, stimulus: Stimulus) -> float:
        """Calculate relevance score for a stimulus"""
        relevance = 0.0

        # Goal relevance
        if self.current_context.goals:
            goal_relevance = self._calculate_goal_relevance(stimulus)
            relevance += goal_relevance * 0.3

        # Context relevance
        context_relevance = self._calculate_context_relevance(stimulus)
        relevance += context_relevance * 0.3

        # Emotional relevance
        emotional_relevance = self._calculate_emotional_relevance(stimulus)
        relevance += emotional_relevance * 0.2

        # Novelty relevance
        novelty_relevance = self._calculate_novelty_relevance(stimulus)
        relevance += novelty_relevance * 0.2

        return min(relevance, 1.0)

    def _calculate_goal_relevance(self, stimulus: Stimulus) -> float:
        """Calculate relevance to current goals"""
        if not self.current_context.goals:
            return 0.0

        # Simple implementation - can be enhanced with semantic similarity
        goal_keywords = [' '.join(goal.split()[:3]) for goal in self.current_context.goals]
        stimulus_text = str(stimulus.content).lower()

        relevance = 0.0
        for keyword in goal_keywords:
            if keyword.lower() in stimulus_text:
                relevance += 0.5

        return min(relevance / len(goal_keywords), 1.0)

    def _calculate_context_relevance(self, stimulus: Stimulus) -> float:
        """Calculate relevance to current context"""
        relevance = 0.0

        # Situation relevance
        if self.current_context.situation != "unknown":
            situation_keywords = self.current_context.situation.split()
            stimulus_text = str(stimulus.content).lower()
            for keyword in situation_keywords:
                if keyword.lower() in stimulus_text:
                    relevance += 0.3

        # Temporal relevance
        time_diff = datetime.now() - stimulus.timestamp
        recency = math.exp(-time_diff.total_seconds() / 3600)  # 1-hour decay
        relevance += recency * 0.3

        # Modality relevance
        relevant_modalities = self._get_relevant_modalities()
        if stimulus.modality in relevant_modalities:
            relevance += 0.4

        return min(relevance, 1.0)

    def _get_relevant_modalities(self) -> List[str]:
        """Get currently relevant sensory modalities"""
        # Context-dependent modality relevance
        modalities = ['textual']  # Always relevant

        if self.current_context.situation in ['conversation', 'dialogue']:
            modalities.extend(['auditory', 'textual'])
        elif self.current_context.situation in ['exploration', 'observation']:
            modalities.extend(['visual', 'spatial'])
        elif self.current_context.situation in ['emotional', 'social']:
            modalities.extend(['emotional', 'social'])

        return modalities

    def _calculate_emotional_relevance(self, stimulus: Stimulus) -> float:
        """Calculate emotional relevance of stimulus"""
        if not self.current_context.emotional_state:
            return 0.0

        # Check if stimulus contains emotional content
        emotional_keywords = {
            'happy': ['happy', 'joy', 'excited', 'pleased'],
            'sad': ['sad', 'unhappy', 'depressed', 'melancholy'],
            'angry': ['angry', 'mad', 'furious', 'irritated'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious'],
            'surprise': ['surprised', 'amazed', 'shocked', 'astonished']
        }

        stimulus_text = str(stimulus.content).lower()
        relevance = 0.0

        for emotion, keywords in emotional_keywords.items():
            if emotion in self.current_context.emotional_state:
                emotion_strength = self.current_context.emotional_state[emotion]
                for keyword in keywords:
                    if keyword in stimulus_text:
                        relevance += emotion_strength * 0.5
                        break

        return min(relevance, 1.0)

    def _calculate_novelty_relevance(self, stimulus: Stimulus) -> float:
        """Calculate novelty relevance of stimulus"""
        # Check if stimulus is similar to recent stimuli
        recent_stimuli = list(self.active_stimuli)[-5:]  # Last 5 stimuli

        if not recent_stimuli:
            return 1.0  # Completely novel

        stimulus_signature = self._create_stimulus_signature(stimulus)
        similarities = []

        for recent in recent_stimuli:
            recent_signature = self._create_stimulus_signature(recent)
            similarity = self._calculate_signature_similarity(stimulus_signature, recent_signature)
            similarities.append(similarity)

        max_similarity = max(similarities) if similarities else 0.0
        novelty = 1.0 - max_similarity

        return novelty

    def _create_stimulus_signature(self, stimulus: Stimulus) -> str:
        """Create a signature for stimulus similarity comparison"""
        return f"{stimulus.modality}:{stimulus.source}:{type(stimulus.content).__name__}"

    def _calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two stimulus signatures"""
        if sig1 == sig2:
            return 1.0
        elif sig1.split(':')[0] == sig2.split(':')[0]:  # Same modality
            return 0.5
        else:
            return 0.0

    def _update_cognitive_state(self):
        """Update cognitive state based on current conditions"""
        # Calculate cognitive load
        attention_demand = len(self.active_stimuli) / self.config['max_stimuli_per_cycle']
        working_memory_load = len(self.working_memory_buffer) / self.config['working_memory_size']

        self.cognitive_load = min(attention_demand * 0.6 + working_memory_load * 0.4, 1.0)

        # Update attention level
        if self.cognitive_load > 0.8:
            self.attention_level = AttentionLevel.MINIMAL
            self.state = CognitiveState.OVERLOADED
        elif self.cognitive_load > 0.6:
            self.attention_level = AttentionLevel.LOW
            self.state = CognitiveState.PROCESSING
        elif self.cognitive_load > 0.3:
            self.attention_level = AttentionLevel.MODERATE
            self.state = CognitiveState.ATTENTIVE
        else:
            self.attention_level = AttentionLevel.HIGH
            self.state = CognitiveState.IDLE

    async def process_stimuli(self) -> List[Dict]:
        """
        Process active stimuli through attention and working memory

        Returns:
            List of processed stimuli with attention weights
        """
        if not self.active_stimuli:
            return []

        try:
            with self.processing_lock:
                # Limit number of stimuli per processing cycle
                stimuli_to_process = self.active_stimuli[:self.config['max_stimuli_per_cycle']]

                # Create stimulus embeddings (simplified implementation)
                embeddings = []
                metadata = []

                for stimulus in stimuli_to_process:
                    embedding = self._create_stimulus_embedding(stimulus)
                    embeddings.append(embedding)

                    # Create metadata tensor
                    meta_tensor = torch.tensor([
                        stimulus.intensity,
                        stimulus.relevance_score,
                        stimulus.priority,
                        self.attention_level.value
                    ])
                    metadata.append(meta_tensor)

                if embeddings:
                    embeddings_tensor = torch.stack(embeddings).unsqueeze(0)
                    metadata_tensor = torch.stack(metadata).unsqueeze(0)

                    # Apply attention network
                    attention_weights, attended_output = self.attention_network(
                        embeddings_tensor, metadata_tensor
                    )

                    # Process through working memory
                    if len(self.working_memory_buffer) > 0:
                        memory_embeddings = [self._create_memory_embedding(mem) for mem in self.working_memory_buffer]
                        attended_with_memory, updated_memory = self.working_memory_network(
                            embeddings_tensor.mean(dim=1), memory_embeddings
                        )

                        # Update working memory buffer
                        if updated_memory is not None:
                            self.working_memory_buffer.append(updated_memory.squeeze(0))

                    # Create processed stimuli results
                    processed = []
                    for i, stimulus in enumerate(stimuli_to_process):
                        processed.append({
                            'stimulus': stimulus,
                            'attention_weight': attention_weights[0, i].item(),
                            'attended_representation': attended_output[0, i].tolist(),
                            'processing_time': datetime.now()
                        })

                    # Clear processed stimuli
                    self.active_stimuli = self.active_stimuli[len(stimuli_to_process):]

                    return processed

                return []

        except Exception as e:
            logger.error(f"Error processing stimuli: {e}")
            return []

    def _create_stimulus_embedding(self, stimulus: Stimulus) -> torch.Tensor:
        """Create embedding representation of stimulus"""
        # Simplified embedding - in practice, would use proper embedding models
        embedding_dim = 512

        # Hash-based embedding generation
        content_str = str(stimulus.content)
        source_hash = hash(stimulus.source) % embedding_dim
        modality_hash = hash(stimulus.modality) % embedding_dim
        content_hash = hash(content_str) % embedding_dim

        embedding = torch.zeros(embedding_dim)
        embedding[source_hash] = stimulus.intensity
        embedding[modality_hash] = stimulus.relevance_score
        embedding[content_hash] = stimulus.priority

        # Add some randomness for diversity
        noise = torch.randn(embedding_dim) * 0.01
        embedding = embedding + noise

        return embedding

    def _create_memory_embedding(self, memory_item) -> torch.Tensor:
        """Create embedding for memory item"""
        embedding_dim = 512

        # Simplified memory embedding
        memory_str = str(memory_item)
        memory_hash = hash(memory_str) % embedding_dim

        embedding = torch.zeros(embedding_dim)
        embedding[memory_hash] = 1.0

        return embedding

    async def execute_cognitive_cycle(self) -> Dict[str, Any]:
        """
        Execute a complete cognitive processing cycle

        Returns:
            Dict containing cycle results and metrics
        """
        cycle_start = time.time()

        try:
            # 1. Perceive and process stimuli
            processed_stimuli = await self.process_stimuli()

            # 2. Update executive functions
            if self.working_memory_buffer:
                current_memory_state = torch.stack(list(self.working_memory_buffer)).mean(dim=0)
                executive_signals = self.executive_function_network(current_memory_state)
            else:
                executive_signals = {
                    'control': torch.zeros(8),
                    'switching': torch.zeros(8),
                    'inhibition': torch.zeros(1)
                }

            # 3. Update performance metrics
            cycle_time = time.time() - cycle_start
            self._update_performance_metrics(processed_stimuli, cycle_time)

            # 4. Generate cognitive insights
            insights = self._generate_cognitive_insights(processed_stimuli, executive_signals)

            return {
                'cycle_id': int(time.time()),
                'processing_time': cycle_time,
                'processed_stimuli': len(processed_stimuli),
                'cognitive_load': self.cognitive_load,
                'attention_level': self.attention_level.name,
                'cognitive_state': self.state.name,
                'executive_signals': {
                    'control': executive_signals['control'].tolist(),
                    'switching': executive_signals['switching'].tolist(),
                    'inhibition': executive_signals['inhibition'].item()
                },
                'performance_metrics': self.performance_metrics,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error in cognitive cycle: {e}")
            return {
                'cycle_id': int(time.time()),
                'error': str(e),
                'cognitive_state': self.state.name
            }

    def _update_performance_metrics(self, processed_stimuli: List[Dict], cycle_time: float):
        """Update performance metrics based on cycle performance"""
        # Processing speed (stimuli per second)
        if cycle_time > 0:
            processing_speed = len(processed_stimuli) / cycle_time
            self.performance_metrics['processing_speed'] = min(processing_speed / 10, 1.0)

        # Memory efficiency (how well working memory is utilized)
        memory_efficiency = len(self.working_memory_buffer) / self.config['working_memory_size']
        self.performance_metrics['memory_efficiency'] = memory_efficiency

        # Attention accuracy (based on distribution of attention weights)
        if processed_stimuli:
            attention_weights = [s['attention_weight'] for s in processed_stimuli]
            attention_variance = np.var(attention_weights)
            # Higher variance = more selective attention
            self.performance_metrics['attention_accuracy'] = min(attention_variance * 4, 1.0)

    def _generate_cognitive_insights(self, processed_stimuli: List[Dict], executive_signals: Dict) -> List[str]:
        """Generate insights about cognitive processing"""
        insights = []

        # Cognitive load insights
        if self.cognitive_load > 0.8:
            insights.append("High cognitive load detected - consider reducing stimulus complexity")
        elif self.cognitive_load < 0.2:
            insights.append("Low cognitive engagement - may need more stimulation")

        # Attention insights
        if processed_stimuli:
            max_attention = max(s['attention_weight'] for s in processed_stimuli)
            if max_attention > 0.8:
                insights.append("Strong attentional focus detected on specific stimuli")
            elif max_attention < 0.3:
                insights.append("Diffuse attention pattern - stimuli may lack salience")

        # Executive function insights
        inhibition = executive_signals['inhibition'].item()
        if inhibition > 0.7:
            insights.append("Strong inhibitory control - active suppression of distractors")
        elif inhibition < 0.3:
            insights.append("Weak inhibitory control - susceptible to distractions")

        # Working memory insights
        if len(self.working_memory_buffer) > 5:
            insights.append("Working memory near capacity - information may be lost")
        elif len(self.working_memory_buffer) < 2:
            insights.append("Working memory underutilized - may miss important connections")

        return insights

    def update_context(self, new_context: Partial[CognitiveContext]):
        """Update the current cognitive context"""
        if new_context.situation:
            self.current_context.situation = new_context.situation

        if new_context.goals:
            self.current_context.goals = new_context.goals

        if new_context.emotional_state:
            self.current_context.emotional_state.update(new_context.emotional_state)

        if new_context.attention_level:
            self.attention_level = new_context.attention_level
            self.current_context.attention_level = new_context.attention_level

        if new_context.temporal_context:
            self.current_context.temporal_context.update(new_context.temporal_context)

        if new_context.social_context:
            self.current_context.social_context.update(new_context.social_context)

    def get_cognitive_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of current cognitive state"""
        return {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'cognitive_state': self.state.name,
            'attention_level': self.attention_level.name,
            'cognitive_load': self.cognitive_load,
            'working_memory_size': len(self.working_memory_buffer),
            'active_stimuli_count': len(self.active_stimuli),
            'context': {
                'situation': self.current_context.situation,
                'goals': self.current_context.goals,
                'emotional_state': self.current_context.emotional_state
            },
            'performance_metrics': self.performance_metrics,
            'attention_history': list(self.attention_history)[-10:]  # Last 10 entries
        }

    async def start_continuous_processing(self):
        """Start continuous cognitive processing in background"""
        async def processing_loop():
            while True:
                try:
                    cycle_result = await self.execute_cognitive_cycle()

                    # Log interesting events
                    if cycle_result.get('cognitive_load', 0) > 0.8:
                        logger.warning(f"High cognitive load for agent {self.agent_id}: {cycle_result['cognitive_load']}")

                    # Small delay between cycles
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error in continuous processing: {e}")
                    await asyncio.sleep(1.0)

        # Start background task
        task = asyncio.create_task(processing_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        logger.info(f"Started continuous cognitive processing for agent {self.agent_id}")

    def stop_continuous_processing(self):
        """Stop continuous cognitive processing"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()
        logger.info(f"Stopped continuous cognitive processing for agent {self.agent_id}")

    def save_state(self, filepath: str):
        """Save cognitive architecture state to file"""
        state_data = {
            'agent_id': self.agent_id,
            'config': self.config,
            'state': self.state.name,
            'cognitive_load': self.cognitive_load,
            'attention_level': self.attention_level.name,
            'performance_metrics': self.performance_metrics,
            'context': {
                'situation': self.current_context.situation,
                'goals': self.current_context.goals,
                'emotional_state': self.current_context.emotional_state,
                'working_memory': [str(item) for item in self.current_context.working_memory],
                'active_concepts': self.current_context.active_concepts,
                'temporal_context': self.current_context.temporal_context,
                'social_context': self.current_context.social_context
            },
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2)

        logger.info(f"Cognitive state saved to {filepath}")

    def load_state(self, filepath: str):
        """Load cognitive architecture state from file"""
        try:
            with open(filepath, 'r') as f:
                state_data = json.load(f)

            self.state = CognitiveState[state_data['state']]
            self.cognitive_load = state_data['cognitive_load']
            self.attention_level = AttentionLevel[state_data['attention_level']]
            self.performance_metrics = state_data['performance_metrics']

            # Restore context
            context_data = state_data['context']
            self.current_context = CognitiveContext(
                situation=context_data['situation'],
                goals=context_data['goals'],
                emotional_state=context_data['emotional_state'],
                attention_level=self.attention_level,
                cognitive_load=self.cognitive_load,
                working_memory=context_data['working_memory'],
                active_concepts=context_data['active_concepts'],
                temporal_context=context_data['temporal_context'],
                social_context=context_data['social_context']
            )

            logger.info(f"Cognitive state loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading cognitive state: {e}")

# Utility functions for integration
async def create_cognitive_architecture(agent_id: str, config: Optional[Dict] = None) -> CognitiveArchitecture:
    """Factory function to create and initialize cognitive architecture"""
    architecture = CognitiveArchitecture(agent_id, config)

    # Start continuous processing
    await architecture.start_continuous_processing()

    return architecture

def benchmark_cognitive_performance(architecture: CognitiveArchitecture, test_stimuli: List[Stimulus]) -> Dict:
    """Benchmark cognitive architecture performance"""
    import time

    start_time = time.time()
    processed_count = 0

    for stimulus in test_stimuli:
        result = asyncio.run(architecture.perceive_stimulus(stimulus))
        if result:
            processed_count += 1

    # Run processing cycles
    cycles = []
    for _ in range(10):
        cycle_result = asyncio.run(architecture.execute_cognitive_cycle())
        cycles.append(cycle_result)

    total_time = time.time() - start_time

    return {
        'total_stimuli': len(test_stimuli),
        'processed_stimuli': processed_count,
        'processing_rate': processed_count / total_time,
        'average_cycle_time': sum(c['processing_time'] for c in cycles) / len(cycles),
        'final_cognitive_load': architecture.cognitive_load,
        'performance_metrics': architecture.performance_metrics
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create cognitive architecture
        config = {
            'working_memory_size': 7,
            'attention_capacity': 4,
            'perception_threshold': 0.3
        }

        agent = await create_cognitive_architecture("test_agent", config)

        # Create test stimuli
        test_stimuli = [
            Stimulus(
                id="s1",
                content="Hello, how are you?",
                modality="textual",
                intensity=0.8,
                timestamp=datetime.now(),
                source="user",
                priority=0.7
            ),
            Stimulus(
                id="s2",
                content="The weather is nice today",
                modality="textual",
                intensity=0.5,
                timestamp=datetime.now(),
                source="environment",
                priority=0.3
            )
        ]

        # Process stimuli
        for stimulus in test_stimuli:
            await agent.perceive_stimulus(stimulus)

        # Run cognitive cycle
        cycle_result = await agent.execute_cognitive_cycle()
        print("Cognitive cycle result:", json.dumps(cycle_result, indent=2, default=str))

        # Get state summary
        summary = agent.get_cognitive_state_summary()
        print("\nCognitive state summary:", json.dumps(summary, indent=2, default=str))

    asyncio.run(main())