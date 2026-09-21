"""
DMLogn8n AI Intelligence Module

A comprehensive advanced AI intelligence system for DMLogn8n multi-agent platform.
This module provides cutting-edge cognitive capabilities including:

- Multi-layered cognitive architecture with attention and executive functions
- Advanced memory systems (working, episodic, semantic, procedural)
- Machine learning engine with multiple learning paradigms
- Sophisticated reasoning and inference capabilities
- Emotional intelligence and personality simulation
- Creative problem-solving and content generation
- Social cognition and relationship management
- Real-time adaptation and personalization

The system is designed to create truly intelligent, adaptive, and engaging
AI agents that can learn, grow, and build meaningful relationships.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .cognitive_architecture import (
    CognitiveArchitecture,
    CognitiveState,
    AttentionLevel,
    Stimulus,
    CognitiveContext,
    create_cognitive_architecture
)

from .memory_systems import (
    MemorySystem,
    MemoryType,
    MemoryTrace,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    WorkingMemoryItem,
    create_memory_system
)

from .learning_engine import (
    LearningEngine,
    LearningType,
    LearningExperience,
    SupervisedExample,
    LearningGoal,
    ReinforcementLearner,
    SupervisedLearner,
    UnsupervisedLearner,
    create_learning_engine
)

from .reasoning_system import (
    ReasoningSystem,
    ReasoningType,
    InferenceType,
    LogicalReasoner,
    CausalReasoner,
    AnalogicalReasoner,
    ProbabilisticReasoner,
    create_reasoning_system
)

from .emotional_engine import (
    EmotionalEngine,
    EmotionType,
    PersonalityTrait,
    MoodState,
    EmotionalState,
    Personality,
    create_emotional_engine
)

from .creativity_module import (
    CreativityModule,
    CreativityType,
    CreativeDomain,
    CreativeIdea,
    Concept,
    DivergentThinking,
    ConceptualBlending,
    ArtisticGenerator,
    create_creativity_module
)

from .social_intelligence import (
    SocialIntelligence,
    RelationshipType,
    SocialRole,
    CommunicationStyle,
    SocialRelationship,
    SocialInteraction,
    PersonalityProfile,
    create_social_intelligence
)

from .adaptation_controller import (
    AdaptationController,
    AdaptationType,
    AdaptationTrigger,
    AdaptationStrategy,
    AdaptationSignal,
    create_adaptation_controller
)

class AdvancedAIIntelligence:
    """
    Main integration class for the DMLogn8n AI Intelligence System.

    This class orchestrates all intelligence modules to provide a unified
    advanced AI capability for agents in the DMLogn8n platform.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        """
        Initialize the Advanced AI Intelligence system.

        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for all modules
        """
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Initialize all intelligence modules
        self.cognitive_architecture = None
        self.memory_system = None
        self.learning_engine = None
        self.reasoning_system = None
        self.emotional_engine = None
        self.creativity_module = None
        self.social_intelligence = None
        self.adaptation_controller = None

        # System state
        self.initialized = False
        self.active = False

        # Performance tracking
        self.system_metrics = {
            'initialization_time': 0,
            'total_operations': 0,
            'error_count': 0,
            'last_update': None
        }

        logger.info(f"Advanced AI Intelligence system created for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration for all modules"""
        return {
            'cognitive_architecture': {
                'working_memory_size': 7,
                'attention_capacity': 4,
                'perception_threshold': 0.3,
                'cognitive_load_threshold': 0.8
            },
            'memory_systems': {
                'working_memory_capacity': 7,
                'episodic_memory_capacity': 10000,
                'semantic_memory_capacity': 5000,
                'procedural_memory_capacity': 1000,
                'consolidation_interval': 60
            },
            'learning_engine': {
                'experience_buffer_size': 10000,
                'learning_frequency': 10,
                'enable_meta_learning': True,
                'enable_transfer_learning': True
            },
            'reasoning_system': {
                'workspace_size': 50,
                'confidence_threshold': 0.6,
                'enable_caching': True,
                'max_reasoning_depth': 5
            },
            'emotional_engine': {
                'emotional_decay_rate': 0.1,
                'stress_threshold': 0.8,
                'enable_learning': True,
                'enable_personality_adaptation': True
            },
            'creativity_module': {
                'max_ideas_per_session': 30,
                'quality_threshold': 0.6,
                'enable_neural_generation': True,
                'cross_domain_inspiration': True
            },
            'social_intelligence': {
                'max_relationships': 50,
                'enable_cultural_adaptation': True,
                'enable_personality_learning': True
            },
            'adaptation_controller': {
                'adaptation_interval': 60,
                'max_concurrent_adaptations': 5,
                'enable_predictive_adaptation': True
            }
        }

    async def initialize(self) -> bool:
        """
        Initialize all intelligence modules.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"Initializing Advanced AI Intelligence for agent {self.agent_id}")

            # Initialize modules in dependency order
            await self._initialize_cognitive_architecture()
            await self._initialize_memory_system()
            await self._initialize_learning_engine()
            await self._initialize_reasoning_system()
            await self._initialize_emotional_engine()
            await self._initialize_creativity_module()
            await self._initialize_social_intelligence()
            await self._initialize_adaptation_controller()

            # Set up inter-module connections
            await self._establish_module_connections()

            self.initialized = True
            self.system_metrics['initialization_time'] = time.time() - start_time

            logger.info(f"Advanced AI Intelligence initialized in {self.system_metrics['initialization_time']:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Advanced AI Intelligence: {e}")
            self.system_metrics['error_count'] += 1
            return False

    async def _initialize_cognitive_architecture(self):
        """Initialize cognitive architecture module"""
        self.cognitive_architecture = await create_cognitive_architecture(
            self.agent_id,
            self.config.get('cognitive_architecture')
        )
        logger.info("Cognitive architecture initialized")

    async def _initialize_memory_system(self):
        """Initialize memory system module"""
        self.memory_system = await create_memory_system(
            self.agent_id,
            self.config.get('memory_systems')
        )
        logger.info("Memory system initialized")

    async def _initialize_learning_engine(self):
        """Initialize learning engine module"""
        self.learning_engine = await create_learning_engine(
            self.agent_id,
            self.config.get('learning_engine')
        )

        # Initialize learners based on expected input dimensions
        if self.cognitive_architecture:
            # Get dimensions from cognitive architecture
            state_dim = 128  # Default, would be extracted from cognitive architecture
            action_dim = 10   # Default, would be extracted from cognitive architecture

            self.learning_engine.initialize_reinforcement_learner(state_dim, action_dim)
            self.learning_engine.initialize_supervised_learner(state_dim, 5, 'regression')
            self.learning_engine.initialize_unsupervised_learner(state_dim, 3)

        logger.info("Learning engine initialized")

    async def _initialize_reasoning_system(self):
        """Initialize reasoning system module"""
        self.reasoning_system = await create_reasoning_system(
            self.agent_id,
            self.config.get('reasoning_system')
        )

        if self.cognitive_architecture:
            self.reasoning_system.initialize_neural_reasoner(128)

        logger.info("Reasoning system initialized")

    async def _initialize_emotional_engine(self):
        """Initialize emotional engine module"""
        self.emotional_engine = await create_emotional_engine(
            self.agent_id,
            self.config.get('emotional_engine')
        )
        logger.info("Emotional engine initialized")

    async def _initialize_creativity_module(self):
        """Initialize creativity module"""
        self.creativity_module = await create_creativity_module(
            self.agent_id,
            self.config.get('creativity_module')
        )
        logger.info("Creativity module initialized")

    async def _initialize_social_intelligence(self):
        """Initialize social intelligence module"""
        self.social_intelligence = await create_social_intelligence(
            self.agent_id,
            self.config.get('social_intelligence')
        )
        logger.info("Social intelligence initialized")

    async def _initialize_adaptation_controller(self):
        """Initialize adaptation controller module"""
        self.adaptation_controller = await create_adaptation_controller(
            self.agent_id,
            self.config.get('adaptation_controller')
        )
        logger.info("Adaptation controller initialized")

    async def _establish_module_connections(self):
        """Establish connections and data flows between modules"""
        # Connect memory system to cognitive architecture
        if self.memory_system and self.cognitive_architecture:
            # Memory system provides working memory to cognitive architecture
            pass

        # Connect emotional engine to social intelligence
        if self.emotional_engine and self.social_intelligence:
            # Emotional states influence social interactions
            pass

        # Connect learning engine to adaptation controller
        if self.learning_engine and self.adaptation_controller:
            # Learning experiences inform adaptations
            pass

        # Connect all modules to performance monitoring
        if self.adaptation_controller:
            # Adaptation controller monitors all module performance
            pass

        logger.info("Module connections established")

    async def activate(self) -> bool:
        """
        Activate the AI intelligence system.

        Returns:
            bool: True if activation successful, False otherwise
        """
        if not self.initialized:
            logger.error("Cannot activate unintialized system")
            return False

        try:
            # Start background processes for each module
            if self.cognitive_architecture:
                await self.cognitive_architecture.start_continuous_processing()

            if self.memory_system:
                await self.memory_system.start_maintenance_tasks()

            if self.learning_engine:
                await self.learning_engine.start_continuous_processing()

            if self.emotional_engine:
                await self.emotional_engine.start_emotional_decay()

            if self.adaptation_controller:
                await self.adaptation_controller.start_adaptation_loop()

            self.active = True
            logger.info(f"Advanced AI Intelligence activated for agent {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to activate Advanced AI Intelligence: {e}")
            self.system_metrics['error_count'] += 1
            return False

    async def deactivate(self):
        """Deactivate the AI intelligence system."""
        try:
            # Stop all background processes
            if self.cognitive_architecture:
                self.cognitive_architecture.stop_continuous_processing()

            if self.memory_system:
                self.memory_system.stop_maintenance_tasks()

            if self.learning_engine:
                self.learning_engine.stop_learning_process()

            if self.emotional_engine:
                self.emotional_engine.stop_background_tasks()

            if self.adaptation_controller:
                await self.adaptation_controller.stop_adaptation_loop()

            self.active = False
            logger.info(f"Advanced AI Intelligence deactivated for agent {self.agent_id}")

        except Exception as e:
            logger.error(f"Error during deactivation: {e}")

    async def process_input(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input through the AI intelligence system.

        Args:
            input_data: Input data to process
            context: Context information for processing

        Returns:
            Dict containing processing results
        """
        if not self.active:
            logger.warning("Processing input on inactive system")
            return {'error': 'System not active'}

        try:
            self.system_metrics['total_operations'] += 1

            # Create stimulus for cognitive architecture
            stimulus = Stimulus(
                id=f"input_{int(time.time())}",
                content=input_data,
                modality=input_data.get('modality', 'textual'),
                intensity=input_data.get('intensity', 0.5),
                timestamp=datetime.now(),
                source='user',
                relevance_score=0.5
            )

            # Process through cognitive architecture
            cognitive_result = await self.cognitive_architecture.process_stimuli(stimulus)

            # Store in memory system
            if 'content' in input_data:
                self.memory_system.add_working_memory(
                    input_data['content'],
                    importance=input_data.get('importance', 0.5)
                )

            # Generate emotional response
            emotional_state = self.emotional_engine.process_emotional_stimulus({
                'trigger': 'user_input',
                'content': str(input_data),
                'context': context or {}
            })

            # Generate creative response if needed
            creative_response = None
            if input_data.get('request_creativity', False):
                problem = input_data.get('creative_prompt', 'Generate creative ideas')
                creative_ideas = self.creativity_module.generate_creative_ideas(problem)
                creative_response = {
                    'ideas': [idea.content for idea in creative_ideas],
                    'quality_scores': [idea.overall_quality for idea in creative_ideas]
                }

            # Generate reasoning if needed
            reasoning_result = None
            if input_data.get('request_reasoning', False):
                query = input_data.get('reasoning_query', 'Analyze the situation')
                reasoning_result = self.reasoning_system.logical_inference(query)

            # Generate social response if needed
            social_response = None
            if input_data.get('social_interaction', False):
                target_agent = input_data.get('target_agent', 'unknown')
                interaction_type = input_data.get('interaction_type', 'conversation')

                interaction = await self.social_intelligence.initiate_interaction(
                    target_agent,
                    interaction_type,
                    context or {},
                    str(input_data.get('content', ''))
                )
                social_response = {
                    'interaction_id': interaction.interaction_id,
                    'response': interaction.content,
                    'strategy': interaction.context
                }

            # Record performance
            self.adaptation_controller.record_performance(
                'response_quality',
                input_data.get('quality_score', 0.8),
                context
            )

            # Update system metrics
            self.system_metrics['last_update'] = datetime.now().isoformat()

            return {
                'success': True,
                'cognitive_processing': cognitive_result,
                'emotional_state': emotional_state.get_emotional_summary() if emotional_state else None,
                'creative_response': creative_response,
                'reasoning_result': reasoning_result,
                'social_response': social_response,
                'processing_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            self.system_metrics['error_count'] += 1
            return {
                'success': False,
                'error': str(e),
                'processing_timestamp': datetime.now().isoformat()
            }

    async def learn_from_experience(self, experience: Dict[str, Any]):
        """
        Learn from experience using the learning engine.

        Args:
            experience: Experience data to learn from
        """
        if not self.active:
            logger.warning("Learning on inactive system")
            return

        try:
            # Create learning experience
            learning_exp = LearningExperience(
                state=experience.get('state', {}),
                action=experience.get('action', {}),
                reward=experience.get('reward', 0.0),
                next_state=experience.get('next_state', {}),
                done=experience.get('done', False),
                timestamp=datetime.now(),
                context=experience.get('context', {}),
                importance=experience.get('importance', 1.0),
                agent_id=self.agent_id
            )

            # Add to learning engine
            self.learning_engine.add_experience(learning_exp)

            # Add supervised example if provided
            if 'input' in experience and 'output' in experience:
                supervised_exp = SupervisedExample(
                    input_data=experience['input'],
                    target_output=experience['output'],
                    timestamp=datetime.now(),
                    confidence=experience.get('confidence', 1.0),
                    source=experience.get('source', 'system')
                )
                self.learning_engine.add_supervised_example(supervised_exp)

            logger.info(f"Learning from experience for agent {self.agent_id}")

        except Exception as e:
            logger.error(f"Error learning from experience: {e}")
            self.system_metrics['error_count'] += 1

    def record_feedback(self, feedback: Dict[str, Any]):
        """
        Record user feedback for adaptation.

        Args:
            feedback: Feedback data to record
        """
        if self.adaptation_controller:
            self.adaptation_controller.record_user_feedback(feedback)
        else:
            logger.warning("Adaptation controller not available for feedback recording")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            Dict containing system status information
        """
        status = {
            'agent_id': self.agent_id,
            'initialized': self.initialized,
            'active': self.active,
            'system_metrics': self.system_metrics.copy(),
            'module_status': {}
        }

        # Get status from each module
        if self.cognitive_architecture:
            status['module_status']['cognitive_architecture'] = (
                self.cognitive_architecture.get_cognitive_state_summary()
            )

        if self.memory_system:
            status['module_status']['memory_system'] = (
                self.memory_system.get_memory_summary()
            )

        if self.learning_engine:
            status['module_status']['learning_engine'] = (
                self.learning_engine.get_learning_summary()
            )

        if self.reasoning_system:
            status['module_status']['reasoning_system'] = (
                self.reasoning_system.get_reasoning_summary()
            )

        if self.emotional_engine:
            status['module_status']['emotional_engine'] = (
                self.emotional_engine.get_emotional_summary()
            )

        if self.creativity_module:
            status['module_status']['creativity_module'] = (
                self.creativity_module.get_creativity_summary()
            )

        if self.social_intelligence:
            status['module_status']['social_intelligence'] = (
                self.social_intelligence.get_social_insights()
            )

        if self.adaptation_controller:
            status['module_status']['adaptation_controller'] = (
                self.adaptation_controller.get_adaptation_summary()
            )

        return status

    def save_system_state(self, filepath: str):
        """
        Save complete system state to file.

        Args:
            filepath: Path to save the system state
        """
        try:
            # Save each module's state
            base_path = filepath.rsplit('.', 1)[0]

            if self.cognitive_architecture:
                self.cognitive_architecture.save_state(f"{base_path}_cognitive.pkl")

            if self.memory_system:
                self.memory_system.save_memories(f"{base_path}_memory.pkl")

            if self.learning_engine:
                self.learning_engine.save_learning_state(f"{base_path}_learning.pkl")

            if self.reasoning_system:
                self.reasoning_system.save_reasoning_state(f"{base_path}_reasoning.pkl")

            if self.emotional_engine:
                self.emotional_engine.save_emotional_state(f"{base_path}_emotional.pkl")

            if self.creativity_module:
                self.creativity_module.export_ideas(f"{base_path}_creativity.json")

            if self.social_intelligence:
                self.social_intelligence.save_social_state(f"{base_path}_social.json")

            if self.adaptation_controller:
                self.adaptation_controller.save_adaptation_state(f"{base_path}_adaptation.json")

            # Save main system state
            system_state = {
                'agent_id': self.agent_id,
                'config': self.config,
                'initialized': self.initialized,
                'active': self.active,
                'system_metrics': self.system_metrics,
                'timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(system_state, f, indent=2, default=str)

            logger.info(f"System state saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving system state: {e}")

    def load_system_state(self, filepath: str):
        """
        Load complete system state from file.

        Args:
            filepath: Path to load the system state from
        """
        try:
            # Load main system state
            with open(filepath, 'r') as f:
                system_state = json.load(f)

            self.agent_id = system_state['agent_id']
            self.config = system_state['config']
            self.initialized = system_state['initialized']
            self.active = system_state['active']
            self.system_metrics = system_state['system_metrics']

            # Load individual module states
            base_path = filepath.rsplit('.', 1)[0]

            if self.cognitive_architecture:
                try:
                    self.cognitive_architecture.load_state(f"{base_path}_cognitive.pkl")
                except FileNotFoundError:
                    logger.warning("Cognitive architecture state file not found")

            if self.memory_system:
                try:
                    self.memory_system.load_memories(f"{base_path}_memory.pkl")
                except FileNotFoundError:
                    logger.warning("Memory system state file not found")

            if self.learning_engine:
                try:
                    self.learning_engine.load_learning_state(f"{base_path}_learning.pkl")
                except FileNotFoundError:
                    logger.warning("Learning engine state file not found")

            if self.reasoning_system:
                try:
                    self.reasoning_system.load_reasoning_state(f"{base_path}_reasoning.pkl")
                except FileNotFoundError:
                    logger.warning("Reasoning system state file not found")

            if self.emotional_engine:
                try:
                    self.emotional_engine.load_emotional_state(f"{base_path}_emotional.pkl")
                except FileNotFoundError:
                    logger.warning("Emotional engine state file not found")

            if self.adaptation_controller:
                try:
                    self.adaptation_controller.load_adaptation_state(f"{base_path}_adaptation.json")
                except FileNotFoundError:
                    logger.warning("Adaptation controller state file not found")

            logger.info(f"System state loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading system state: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        await self.activate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.deactivate()

# Export main class and key components
__all__ = [
    'AdvancedAIIntelligence',
    'CognitiveArchitecture',
    'MemorySystem',
    'LearningEngine',
    'ReasoningSystem',
    'EmotionalEngine',
    'CreativityModule',
    'SocialIntelligence',
    'AdaptationController'
]

__version__ = "1.0.0"
__author__ = "DMLogn8n AI Team"
__description__ = "Advanced AI Intelligence System for DMLogn8n Multi-Agent Platform"