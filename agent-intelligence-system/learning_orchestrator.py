#!/usr/bin/env python3
"""
DMlogn8n Learning Orchestrator
================================

Central coordination system for all AI learning components based on AgentDnDengine3.txt research.

This orchestrator coordinates:
1. LoRA-based Strategic Adaptation
2. Hierarchical Memory Architecture
3. Progressive Skill Development
4. Intelligence Growth Dashboard

Author: DMlogn8n AI System
Version: 1.0.0
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from collections import defaultdict
import time

# Import learning subsystems
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lora-adaptation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-architecture'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'skill-development'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'learning-dashboard'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LearningSession:
    """Represents a complete learning session for an agent."""
    session_id: str
    agent_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    experiences: List[Dict[str, Any]] = None
    memory_consolidations: List[Dict[str, Any]] = None
    skill_improvements: List[Dict[str, Any]] = None
    lora_updates: List[Dict[str, Any]] = None
    intelligence_delta: float = 0.0

    def __post_init__(self):
        if self.experiences is None:
            self.experiences = []
        if self.memory_consolidations is None:
            self.memory_consolidations = []
        if self.skill_improvements is None:
            self.skill_improvements = []
        if self.lora_updates is None:
            self.lora_updates = []

class LearningOrchestrator:
    """
    Central coordination system for all AI learning processes.

    This orchestrator implements the unified learning loop described in AgentDnDengine3.txt,
    coordinating all learning subsystems to work together harmoniously.
    """

    def __init__(self, config_path: str = "config/orchestrator_config.json"):
        """Initialize the learning orchestrator with all subsystems."""
        self.config = self._load_config(config_path)
        self.active_sessions: Dict[str, LearningSession] = {}
        self.agent_learning_states: Dict[str, Dict[str, Any]] = {}

        # Initialize subsystems
        self.memory_manager = None
        self.skill_system = None
        self.lora_trainer = None
        self.dashboard_client = None

        # Learning metrics
        self.learning_metrics = defaultdict(lambda: {
            'sessions_completed': 0,
            'total_experiences': 0,
            'intelligence_improvement': 0.0,
            'skill_points_gained': 0,
            'memories_consolidated': 0,
            'lora_updates': 0
        })

        # Performance tracking
        self.performance_history = defaultdict(list)
        self.learning_velocity = defaultdict(lambda: 0.0)

        logger.info("Learning Orchestrator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load orchestrator configuration."""
        default_config = {
            "learning_cycle_interval": 300,  # 5 minutes
            "consolidation_threshold": 10,   # experiences
            "lora_training_threshold": 50,   # experiences
            "intelligence_update_interval": 100,  # experiences
            "session_timeout": 3600,         # 1 hour
            "max_concurrent_sessions": 100,
            "performance_window": 1000,      # experiences
            "auto_save_interval": 60,        # seconds
            "dashboard_websocket_url": "ws://localhost:8001/ws"
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        # Create default config
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    async def initialize_subsystems(self):
        """Initialize all learning subsystems."""
        try:
            logger.info("Initializing learning subsystems...")

            # Initialize Memory Manager
            from memory_manager import MemoryManager
            self.memory_manager = MemoryManager()
            logger.info("✓ Memory Manager initialized")

            # Initialize Skill System
            from skill_system import SkillSystem
            self.skill_system = SkillSystem()
            logger.info("✓ Skill System initialized")

            # Initialize LoRA Trainer
            from personalized_model_manager import PersonalizedModelManager
            self.lora_trainer = PersonalizedModelManager()
            logger.info("✓ LoRA Trainer initialized")

            # Initialize Dashboard Client
            self.dashboard_client = DashboardClient(self.config["dashboard_websocket_url"])
            await self.dashboard_client.connect()
            logger.info("✓ Dashboard Client connected")

            logger.info("All subsystems initialized successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize subsystems: {e}")
            raise

    async def start_learning_session(self, agent_id: str, context: Dict[str, Any]) -> str:
        """
        Start a new learning session for an agent.

        Args:
            agent_id: Unique identifier for the agent
            context: Initial context for the session

        Returns:
            session_id: Unique identifier for the learning session
        """
        session_id = f"{agent_id}_{int(time.time())}"

        session = LearningSession(
            session_id=session_id,
            agent_id=agent_id,
            start_time=datetime.now()
        )

        self.active_sessions[session_id] = session

        # Initialize agent learning state if needed
        if agent_id not in self.agent_learning_states:
            self.agent_learning_states[agent_id] = {
                'total_experiences': 0,
                'last_consolidation': 0,
                'last_lora_training': 0,
                'last_intelligence_update': 0,
                'learning_rate': 1.0,
                'specializations': [],
                'learning_preferences': {}
            }

        logger.info(f"Started learning session {session_id} for agent {agent_id}")

        # Notify dashboard
        await self._notify_dashboard('session_started', {
            'session_id': session_id,
            'agent_id': agent_id,
            'context': context
        })

        return session_id

    async def process_experience(self, session_id: str, experience: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single experience through all learning subsystems.

        This is the core learning loop that coordinates all subsystems.

        Args:
            session_id: Learning session identifier
            experience: Raw experience data from gameplay

        Returns:
            processing_results: Summary of all learning effects
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        agent_id = session.agent_id
        agent_state = self.agent_learning_states[agent_id]

        # Add experience to session
        session.experiences.append(experience)
        agent_state['total_experiences'] += 1

        processing_results = {
            'experience_id': experience.get('id', f"exp_{int(time.time())}"),
            'timestamp': datetime.now().isoformat(),
            'memory_effects': [],
            'skill_effects': [],
            'lora_effects': None,
            'intelligence_effects': 0.0
        }

        try:
            # 1. Memory Processing
            memory_results = await self._process_memory_experience(agent_id, experience)
            processing_results['memory_effects'] = memory_results

            # 2. Skill Development
            skill_results = await self._process_skill_experience(agent_id, experience)
            processing_results['skill_effects'] = skill_results

            # 3. Check for consolidation triggers
            if agent_state['total_experiences'] - agent_state['last_consolidation'] >= self.config["consolidation_threshold"]:
                consolidation_results = await self._trigger_memory_consolidation(agent_id, session)
                session.memory_consolidations.extend(consolidation_results)
                agent_state['last_consolidation'] = agent_state['total_experiences']

            # 4. Check for LoRA training
            if agent_state['total_experiences'] - agent_state['last_lora_training'] >= self.config["lora_training_threshold"]:
                lora_results = await self._trigger_lora_training(agent_id, session)
                processing_results['lora_effects'] = lora_results
                session.lora_updates.append(lora_results)
                agent_state['last_lora_training'] = agent_state['total_experiences']

            # 5. Update intelligence metrics
            if agent_state['total_experiences'] - agent_state['last_intelligence_update'] >= self.config["intelligence_update_interval"]:
                intelligence_delta = await self._update_intelligence_metrics(agent_id, session)
                processing_results['intelligence_effects'] = intelligence_delta
                session.intelligence_delta += intelligence_delta
                agent_state['last_intelligence_update'] = agent_state['total_experiences']

            # 6. Update learning metrics
            self._update_learning_metrics(agent_id, processing_results)

            # 7. Notify dashboard
            await self._notify_dashboard('experience_processed', {
                'agent_id': agent_id,
                'session_id': session_id,
                'results': processing_results
            })

            logger.debug(f"Processed experience for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error processing experience for agent {agent_id}: {e}")
            processing_results['error'] = str(e)

        return processing_results

    async def _process_memory_experience(self, agent_id: str, experience: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process experience through memory system."""
        if not self.memory_manager:
            return []

        try:
            # Extract memory-worthy information
            memory_data = {
                'experience_type': experience.get('type', 'unknown'),
                'context': experience.get('context', {}),
                'outcome': experience.get('outcome', {}),
                'emotional_weight': experience.get('emotional_impact', 0.5),
                'importance_score': experience.get('importance', 0.5),
                'timestamp': datetime.now()
            }

            # Store in working memory
            memory_id = await self.memory_manager.store_memory(agent_id, memory_data, 'working')

            # Check for immediate consolidation triggers
            consolidation_triggers = []
            if experience.get('importance', 0) > 0.8:
                consolidation_triggers.append('high_importance')
            if experience.get('type') == 'critical_event':
                consolidation_triggers.append('critical_event')

            results = [{
                'memory_id': memory_id,
                'memory_type': 'working',
                'triggers': consolidation_triggers
            }]

            return results

        except Exception as e:
            logger.error(f"Memory processing failed: {e}")
            return []

    async def _process_skill_experience(self, agent_id: str, experience: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process experience through skill system."""
        if not self.skill_system:
            return []

        try:
            skill_effects = []

            # Extract skill usage from experience
            skills_used = experience.get('skills_used', [])
            success = experience.get('success', False)
            difficulty = experience.get('difficulty', 0.5)
            context = experience.get('context', {})

            for skill_name in skills_used:
                # Calculate XP based on success and difficulty
                xp_gained = self.skill_system.calculate_xp(
                    base_xp=10,
                    success_multiplier=2.0 if success else 0.5,
                    difficulty_multiplier=1.0 + difficulty,
                    context_bonus=self._calculate_context_bonus(context)
                )

                # Award XP to skill
                result = await self.skill_system.award_xp(agent_id, skill_name, xp_gained)
                skill_effects.append(result)

            return skill_effects

        except Exception as e:
            logger.error(f"Skill processing failed: {e}")
            return []

    async def _trigger_memory_consolidation(self, agent_id: str, session: LearningSession) -> List[Dict[str, Any]]:
        """Trigger memory consolidation process."""
        if not self.memory_manager:
            return []

        try:
            consolidation_results = await self.memory_manager.consolidate_memories(agent_id)

            results = []
            for consolidation in consolidation_results:
                results.append({
                    'consolidation_id': consolidation.get('id'),
                    'memories_consolidated': len(consolidation.get('source_memories', [])),
                    'patterns_extracted': consolidation.get('patterns_extracted', []),
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Consolidated {len(results)} memory groups for agent {agent_id}")
            return results

        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            return []

    async def _trigger_lora_training(self, agent_id: str, session: LearningSession) -> Dict[str, Any]:
        """Trigger LoRA fine-tuning for agent."""
        if not self.lora_trainer:
            return {}

        try:
            # Collect recent experiences for training
            recent_experiences = session.experiences[-50:]  # Last 50 experiences

            # Format for LoRA training
            training_data = self.lora_trainer.format_experiences_for_training(recent_experiences)

            # Trigger fine-tuning
            training_result = await self.lora_trainer.fine_tune_agent(
                agent_id=agent_id,
                training_data=training_data,
                validation_split=0.2
            )

            result = {
                'training_id': training_result.get('training_id'),
                'experiences_used': len(recent_experiences),
                'training_loss': training_result.get('final_loss'),
                'improvement_score': training_result.get('improvement_score', 0.0),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"LoRA training completed for agent {agent_id}")
            return result

        except Exception as e:
            logger.error(f"LoRA training failed: {e}")
            return {'error': str(e)}

    async def _update_intelligence_metrics(self, agent_id: str, session: LearningSession) -> float:
        """Update intelligence metrics for agent."""
        try:
            # Calculate intelligence delta based on recent learning
            recent_experiences = session.experiences[-100:]  # Last 100 experiences

            # Factors affecting intelligence:
            # 1. Success rate improvement
            # 2. Skill diversity
            # 3. Memory consolidation efficiency
            # 4. Strategic pattern recognition

            success_rate = sum(1 for exp in recent_experiences if exp.get('success', False)) / len(recent_experiences)
            skill_diversity = len(set(exp.get('primary_skill', 'unknown') for exp in recent_experiences))
            consolidation_efficiency = len(session.memory_consolidations) / max(len(session.experiences), 1)

            # Calculate intelligence delta (simplified)
            intelligence_delta = (success_rate * 0.3 + skill_diversity * 0.1 + consolidation_efficiency * 0.6) * 0.1

            # Update agent's intelligence score
            current_intelligence = self.agent_learning_states[agent_id].get('intelligence_score', 100.0)
            new_intelligence = current_intelligence + intelligence_delta
            self.agent_learning_states[agent_id]['intelligence_score'] = new_intelligence

            logger.debug(f"Intelligence updated for agent {agent_id}: {current_intelligence} → {new_intelligence}")

            return intelligence_delta

        except Exception as e:
            logger.error(f"Intelligence update failed: {e}")
            return 0.0

    def _calculate_context_bonus(self, context: Dict[str, Any]) -> float:
        """Calculate contextual XP bonus."""
        bonus = 0.0

        # High pressure situations
        if context.get('is_combat', False):
            bonus += 0.2

        # Novel situations
        if context.get('is_novel', False):
            bonus += 0.3

        # Social complexity
        if context.get('social_complexity', 0) > 0.7:
            bonus += 0.15

        # Strategic depth
        if context.get('strategic_depth', 0) > 0.8:
            bonus += 0.25

        return min(bonus, 1.0)  # Cap at 100% bonus

    def _update_learning_metrics(self, agent_id: str, results: Dict[str, Any]):
        """Update learning metrics for agent."""
        metrics = self.learning_metrics[agent_id]

        metrics['total_experiences'] += 1
        metrics['memories_consolidated'] += len(results['memory_effects'])
        metrics['skill_points_gained'] += sum(effect.get('xp_gained', 0) for effect in results['skill_effects'])

        if results['lora_effects']:
            metrics['lora_updates'] += 1

        metrics['intelligence_improvement'] += results['intelligence_effects']

        # Track learning velocity
        current_time = time.time()
        self.performance_history[agent_id].append({
            'timestamp': current_time,
            'intelligence_score': self.agent_learning_states[agent_id].get('intelligence_score', 100.0),
            'success_rate': 0.8  # Placeholder - would calculate from recent experiences
        })

        # Keep only recent history
        if len(self.performance_history[agent_id]) > self.config["performance_window"]:
            self.performance_history[agent_id] = self.performance_history[agent_id][-self.config["performance_window"]:]

    async def end_learning_session(self, session_id: str) -> Dict[str, Any]:
        """End a learning session and return summary."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        session.end_time = datetime.now()

        # Calculate session summary
        duration = (session.end_time - session.start_time).total_seconds()

        summary = {
            'session_id': session_id,
            'agent_id': session.agent_id,
            'duration_seconds': duration,
            'experiences_processed': len(session.experiences),
            'memory_consolidations': len(session.memory_consolidations),
            'skill_improvements': len(session.skill_improvements),
            'lora_updates': len(session.lora_updates),
            'intelligence_improvement': session.intelligence_delta,
            'learning_velocity': session.intelligence_delta / max(duration / 3600, 1),  # per hour
            'summary': f"Processed {len(session.experiences)} experiences in {duration:.1f}s"
        }

        # Remove from active sessions
        del self.active_sessions[session_id]

        # Update metrics
        self.learning_metrics[session.agent_id]['sessions_completed'] += 1

        logger.info(f"Ended learning session {session_id}: {summary['summary']}")

        # Notify dashboard
        await self._notify_dashboard('session_ended', summary)

        return summary

    async def get_agent_learning_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive learning status for an agent."""
        if agent_id not in self.agent_learning_states:
            return {'error': 'Agent not found'}

        agent_state = self.agent_learning_states[agent_id]
        metrics = self.learning_metrics[agent_id]

        # Get subsystem status
        memory_status = {}
        skill_status = {}
        lora_status = {}

        try:
            if self.memory_manager:
                memory_status = await self.memory_manager.get_memory_status(agent_id)
        except Exception as e:
            memory_status = {'error': str(e)}

        try:
            if self.skill_system:
                skill_status = await self.skill_system.get_skill_summary(agent_id)
        except Exception as e:
            skill_status = {'error': str(e)}

        try:
            if self.lora_trainer:
                lora_status = await self.lora_trainer.get_agent_status(agent_id)
        except Exception as e:
            lora_status = {'error': str(e)}

        return {
            'agent_id': agent_id,
            'learning_state': agent_state,
            'metrics': dict(metrics),
            'memory_status': memory_status,
            'skill_status': skill_status,
            'lora_status': lora_status,
            'performance_history': self.performance_history[agent_id][-100:],  # Last 100 data points
            'learning_velocity': self.learning_velocity[agent_id],
            'active_sessions': [sid for sid, session in self.active_sessions.items() if session.agent_id == agent_id]
        }

    async def _notify_dashboard(self, event_type: str, data: Dict[str, Any]):
        """Send real-time updates to dashboard."""
        if self.dashboard_client:
            try:
                await self.dashboard_client.send_update(event_type, data)
            except Exception as e:
                logger.warning(f"Failed to notify dashboard: {e}")

    async def run_learning_cycle(self):
        """Run the main learning coordination cycle."""
        logger.info("Starting learning coordination cycle...")

        while True:
            try:
                # Process any pending consolidations
                for agent_id, state in self.agent_learning_states.items():
                    if state['total_experiences'] - state['last_consolidation'] >= self.config["consolidation_threshold"]:
                        # Find active session or create temporary one
                        active_sessions = [sid for sid, s in self.active_sessions.items() if s.agent_id == agent_id]
                        if active_sessions:
                            await self._trigger_memory_consolidation(agent_id, self.active_sessions[active_sessions[0]])
                            state['last_consolidation'] = state['total_experiences']

                # Clean up expired sessions
                current_time = datetime.now()
                expired_sessions = []
                for session_id, session in self.active_sessions.items():
                    if (current_time - session.start_time).total_seconds() > self.config["session_timeout"]:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    logger.warning(f"Session {session_id} expired, ending automatically")
                    await self.end_learning_session(session_id)

                # Auto-save metrics
                await self._save_metrics()

                # Sleep until next cycle
                await asyncio.sleep(self.config["learning_cycle_interval"])

            except Exception as e:
                logger.error(f"Error in learning cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _save_metrics(self):
        """Save learning metrics to file."""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'agent_learning_states': self.agent_learning_states,
                'learning_metrics': dict(self.learning_metrics),
                'performance_history': dict(self.performance_history)
            }

            os.makedirs('data', exist_ok=True)
            with open('data/learning_metrics.json', 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

class DashboardClient:
    """WebSocket client for real-time dashboard updates."""

    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.websocket = None
        self.connected = False

    async def connect(self):
        """Connect to dashboard WebSocket."""
        try:
            import websockets
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            logger.info("Connected to dashboard WebSocket")
        except Exception as e:
            logger.warning(f"Failed to connect to dashboard: {e}")
            self.connected = False

    async def send_update(self, event_type: str, data: Dict[str, Any]):
        """Send update to dashboard."""
        if self.connected and self.websocket:
            try:
                message = json.dumps({
                    'type': event_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                await self.websocket.send(message)
            except Exception as e:
                logger.error(f"Failed to send dashboard update: {e}")
                self.connected = False

# Main execution
async def main():
    """Main execution function."""
    orchestrator = LearningOrchestrator()

    try:
        # Initialize subsystems
        await orchestrator.initialize_subsystems()

        # Start learning coordination cycle
        await orchestrator.run_learning_cycle()

    except KeyboardInterrupt:
        logger.info("Learning Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Learning Orchestrator failed: {e}")
    finally:
        # Save final metrics
        await orchestrator._save_metrics()
        logger.info("Learning Orchestrator shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())