#!/usr/bin/env python3
"""
DMlogn8n Integration Layer
==========================

Integration layer for connecting the Agent Intelligence System with the existing DMlogn8n platform.

This module provides seamless integration between:
- Character AI System
- Multi-Portal Gateway
- D&D 5e Rule Engine
- Conversational Combat System
- Learning Orchestrator and all subsystems

Author: DMlogn8n Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add paths to all systems
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / 'lora-adaptation'))
sys.path.append(str(current_dir / 'memory-architecture'))
sys.path.append(str(current_dir / 'skill-development'))

# Import DMlogn8n systems
sys.path.append(str(current_dir.parent / 'character-ai-system'))
sys.path.append(str(current_dir.parent / 'multi-portal-gateway'))
sys.path.append(str(current_dir.parent / 'dnd5e-rule-engine'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DMlogn8nIntegrator:
    """
    Central integration layer for the Agent Intelligence System.

    This class provides a unified interface for connecting the learning system
    with all existing DMlogn8n components.
    """

    def __init__(self):
        """Initialize the integration layer."""
        self.learning_orchestrator = None
        self.character_ai_system = None
        self.portal_gateway = None
        self.rule_engine = None

        # Tracking for active learning sessions
        self.character_sessions: Dict[str, str] = {}  # character_id -> session_id

        # Event handlers for different systems
        self.event_handlers = {}

        logger.info("DMlogn8n Integration Layer initialized")

    async def initialize_all_systems(self):
        """Initialize all connected systems."""
        try:
            logger.info("Initializing all DMlogn8n systems...")

            # 1. Initialize Learning Orchestrator
            from learning_orchestrator import LearningOrchestrator
            self.learning_orchestrator = LearningOrchestrator()
            await self.learning_orchestrator.initialize_subsystems()
            logger.info("✓ Learning Orchestrator initialized")

            # 2. Initialize Character AI System
            from character_ai import CharacterAISystem
            self.character_ai_system = CharacterAISystem()
            await self.character_ai_system.initialize()
            logger.info("✓ Character AI System initialized")

            # 3. Initialize Multi-Portal Gateway
            from gateway_server import PortalGateway
            self.portal_gateway = PortalGateway()
            await self.portal_gateway.start()
            logger.info("✓ Multi-Portal Gateway initialized")

            # 4. Initialize D&D 5e Rule Engine
            from rule_engine import D&D5eRuleEngine
            self.rule_engine = D&D5eRuleEngine()
            await self.rule_engine.initialize()
            logger.info("✓ D&D 5e Rule Engine initialized")

            # 5. Register event handlers
            await self._register_event_handlers()
            logger.info("✓ Event handlers registered")

            logger.info("All systems initialized successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            raise

    async def _register_event_handlers(self):
        """Register event handlers for cross-system communication."""

        # Character action handler
        self.event_handlers['character_action'] = self._handle_character_action

        # Combat encounter handler
        self.event_handlers['combat_encounter'] = self._handle_combat_encounter

        # Dialogue interaction handler
        self.event_handlers['dialogue_interaction'] = self._handle_dialogue_interaction

        # Level up handler
        self.event_handlers['level_up'] = self._handle_level_up

        # Portal connection handler
        self.event_handlers['portal_connection'] = self._handle_portal_connection

        # Register with character AI system
        if self.character_ai_system:
            self.character_ai_system.register_event_handler('action_taken', self.event_handlers['character_action'])
            self.character_ai_system.register_event_handler('dialogue', self.event_handlers['dialogue_interaction'])

        # Register with portal gateway
        if self.portal_gateway:
            self.portal_gateway.register_event_handler('character_connected', self.event_handlers['portal_connection'])

        # Register with rule engine
        if self.rule_engine:
            self.rule_engine.register_event_handler('combat_started', self.event_handlers['combat_encounter'])
            self.rule_engine.register_event_handler('character_leveled', self.event_handlers['level_up'])

    async def start_character_learning_session(self, character_id: str, character_data: Dict[str, Any]) -> str:
        """
        Start a learning session for a character.

        Args:
            character_id: Unique character identifier
            character_data: Character information including class, level, personality

        Returns:
            session_id: Learning session identifier
        """
        if not self.learning_orchestrator:
            logger.warning("Learning orchestrator not initialized")
            return None

        try:
            # Prepare learning context
            context = {
                'character_class': character_data.get('class', 'unknown'),
                'level': character_data.get('level', 1),
                'personality': character_data.get('personality', {}),
                'abilities': character_data.get('abilities', {}),
                'skills': character_data.get('skills', []),
                'campaign_id': character_data.get('campaign_id'),
                'portal_access': character_data.get('portal_access', [])
            }

            # Start learning session
            session_id = await self.learning_orchestrator.start_learning_session(character_id, context)
            self.character_sessions[character_id] = session_id

            logger.info(f"Started learning session for character {character_id}: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to start learning session for {character_id}: {e}")
            return None

    async def _handle_character_action(self, event_data: Dict[str, Any]):
        """Handle character action events from Character AI System."""
        character_id = event_data.get('character_id')
        action = event_data.get('action')
        result = event_data.get('result', {})
        context = event_data.get('context', {})

        if not character_id or character_id not in self.character_sessions:
            return

        session_id = self.character_sessions[character_id]

        # Convert action to learning experience
        experience = {
            'id': f"action_{int(datetime.now().timestamp())}",
            'type': 'action',
            'action_type': action.get('type', 'unknown'),
            'skills_used': self._extract_skills_from_action(action),
            'success': result.get('success', False),
            'difficulty': context.get('difficulty', 0.5),
            'outcome': result,
            'context': context,
            'importance': self._calculate_importance(action, result, context),
            'emotional_impact': context.get('emotional_impact', 0.5),
            'timestamp': datetime.now().isoformat()
        }

        # Process through learning orchestrator
        if self.learning_orchestrator:
            await self.learning_orchestrator.process_experience(session_id, experience)

        logger.debug(f"Processed action experience for character {character_id}")

    async def _handle_combat_encounter(self, event_data: Dict[str, Any]):
        """Handle combat encounter events from D&D 5e Rule Engine."""
        encounter_data = event_data.get('encounter', {})
        participants = encounter_data.get('participants', [])

        # Process each character's combat experience
        for participant in participants:
            character_id = participant.get('character_id')
            if character_id and character_id in self.character_sessions:
                session_id = self.character_sessions[character_id]

                # Create combat experience
                experience = {
                    'id': f"combat_{int(datetime.now().timestamp())}_{character_id}",
                    'type': 'combat',
                    'action_type': 'combat_encounter',
                    'skills_used': self._extract_combat_skills(participant),
                    'success': participant.get('survived', True),
                    'difficulty': self._calculate_encounter_difficulty(encounter_data),
                    'outcome': {
                        'damage_dealt': participant.get('damage_dealt', 0),
                        'damage_taken': participant.get('damage_taken', 0),
                        'enemies_defeated': participant.get('enemies_defeated', 0),
                        'survived': participant.get('survived', True)
                    },
                    'context': {
                        'encounter_type': encounter_data.get('type', 'unknown'),
                        'enemy_types': [e.get('type') for e in encounter_data.get('enemies', [])],
                        'environment': encounter_data.get('environment', {}),
                        'duration': encounter_data.get('duration', 0)
                    },
                    'importance': 0.8,  # Combat is generally important
                    'emotional_impact': 0.7,  # Combat is emotionally impactful
                    'timestamp': datetime.now().isoformat()
                }

                # Process through learning orchestrator
                if self.learning_orchestrator:
                    await self.learning_orchestrator.process_experience(session_id, experience)

        logger.debug(f"Processed combat encounter for {len(participants)} characters")

    async def _handle_dialogue_interaction(self, event_data: Dict[str, Any]):
        """Handle dialogue interaction events from Character AI System."""
        character_id = event_data.get('character_id')
        dialogue = event_data.get('dialogue', {})
        response = event_data.get('response', {})
        context = event_data.get('context', {})

        if not character_id or character_id not in self.character_sessions:
            return

        session_id = self.character_sessions[character_id]

        # Create dialogue experience
        experience = {
            'id': f"dialogue_{int(datetime.now().timestamp())}_{character_id}",
            'type': 'dialogue',
            'action_type': 'social_interaction',
            'skills_used': self._extract_dialogue_skills(dialogue),
            'success': response.get('success', False),
            'difficulty': context.get('social_difficulty', 0.5),
            'outcome': {
                'persuasion_success': response.get('persuasion_success', False),
                'information_gained': response.get('information_gained', []),
                'relationship_change': response.get('relationship_change', 0),
                'dialogue_quality': response.get('dialogue_quality', 0.5)
            },
            'context': {
                'npc_type': context.get('npc_type', 'unknown'),
                'conversation_topic': context.get('topic', 'general'),
                'social_context': context.get('social_context', {}),
                'audience': context.get('audience', [])
            },
            'importance': self._calculate_dialogue_importance(dialogue, response, context),
            'emotional_impact': response.get('emotional_impact', 0.3),
            'timestamp': datetime.now().isoformat()
        }

        # Process through learning orchestrator
        if self.learning_orchestrator:
            await self.learning_orchestrator.process_experience(session_id, experience)

        logger.debug(f"Processed dialogue experience for character {character_id}")

    async def _handle_level_up(self, event_data: Dict[str, Any]):
        """Handle character level up events from D&D 5e Rule Engine."""
        character_id = event_data.get('character_id')
        new_level = event_data.get('new_level')
        old_level = event_data.get('old_level')
        improvements = event_data.get('improvements', {})

        if not character_id or character_id not in self.character_sessions:
            return

        session_id = self.character_sessions[character_id]

        # Create level up experience (high importance)
        experience = {
            'id': f"levelup_{int(datetime.now().timestamp())}_{character_id}",
            'type': 'milestone',
            'action_type': 'level_up',
            'skills_used': ['character_advancement'],
            'success': True,
            'difficulty': 0.5,  # Level up is automatic success
            'outcome': {
                'level_gained': new_level - old_level,
                'new_abilities': improvements.get('abilities', []),
                'stat_increases': improvements.get('stats', {}),
                'new_features': improvements.get('features', [])
            },
            'context': {
                'old_level': old_level,
                'new_level': new_level,
                'class': improvements.get('class', 'unknown'),
                'subclass': improvements.get('subclass', None)
            },
            'importance': 1.0,  # Level up is maximum importance
            'emotional_impact': 0.9,  # Very emotionally significant
            'timestamp': datetime.now().isoformat()
        }

        # Process through learning orchestrator
        if self.learning_orchestrator:
            await self.learning_orchestrator.process_experience(session_id, experience)

        logger.info(f"Processed level up experience for character {character_id}: {old_level} → {new_level}")

    async def _handle_portal_connection(self, event_data: Dict[str, Any]):
        """Handle portal connection events from Multi-Portal Gateway."""
        character_id = event_data.get('character_id')
        portal_type = event_data.get('portal_type', 'character')
        connection_status = event_data.get('status', 'connected')

        if connection_status != 'connected':
            return

        # If this is a character portal and they don't have a learning session, start one
        if portal_type == 'character' and character_id not in self.character_sessions:
            # Get character data from character AI system
            if self.character_ai_system:
                character_data = await self.character_ai_system.get_character_data(character_id)
                if character_data:
                    await self.start_character_learning_session(character_id, character_data)

        logger.debug(f"Handled portal connection for character {character_id}")

    def _extract_skills_from_action(self, action: Dict[str, Any]) -> List[str]:
        """Extract skills used in an action."""
        skills = []

        action_type = action.get('type', '').lower()

        # Map action types to skills
        skill_mapping = {
            'attack': ['attack', 'weapon_proficiency'],
            'cast_spell': ['spellcasting', 'magic', 'concentration'],
            'skill_check': [action.get('skill', 'unknown')],
            'saving_throw': [action.get('ability', 'unknown').lower() + '_save'],
            'move': ['athletics', 'acrobatics'],
            'hide': ['stealth'],
            'perception': ['perception', 'investigation'],
            'persuade': ['persuasion'],
            'intimidate': ['intimidation'],
            'deceive': ['deception']
        }

        if action_type in skill_mapping:
            skills.extend(skill_mapping[action_type])

        # Add any explicitly mentioned skills
        if 'skills_used' in action:
            skills.extend(action['skills_used'])

        return list(set(skills))  # Remove duplicates

    def _extract_combat_skills(self, participant: Dict[str, Any]) -> List[str]:
        """Extract combat skills used by a participant."""
        skills = ['combat', 'tactical_positioning']

        actions = participant.get('actions', [])
        for action in actions:
            skills.extend(self._extract_skills_from_action(action))

        return list(set(skills))

    def _extract_dialogue_skills(self, dialogue: Dict[str, Any]) -> List[str]:
        """Extract social skills used in dialogue."""
        skills = []

        dialogue_type = dialogue.get('type', '').lower()

        # Map dialogue types to skills
        skill_mapping = {
            'persuasion': ['persuasion', 'diplomacy'],
            'intimidation': ['intimidation', 'coercion'],
            'deception': ['deception', 'misdirection'],
            'performance': ['performance', 'entertainment'],
            'negotiation': ['persuasion', 'insight', 'diplomacy'],
            'interrogation': ['intimidation', 'insight', 'perception'],
            'teaching': ['persuasion', 'insight', 'knowledge_transfer']
        }

        if dialogue_type in skill_mapping:
            skills.extend(skill_mapping[dialogue_type])

        # Add any explicitly mentioned skills
        if 'skills_used' in dialogue:
            skills.extend(dialogue['skills_used'])

        return list(set(skills))

    def _calculate_importance(self, action: Dict[str, Any], result: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate the importance score of an action/experience."""
        importance = 0.5  # Base importance

        # Success/failure impact
        if result.get('success', False):
            importance += 0.2
        else:
            importance += 0.1

        # High stakes situations
        if context.get('life_threatening', False):
            importance += 0.3

        # Critical success/failure
        if result.get('critical_success', False):
            importance += 0.2
        elif result.get('critical_failure', False):
            importance += 0.2

        # Novel situations
        if context.get('is_novel', False):
            importance += 0.2

        # Social importance
        if context.get('social_importance', 0) > 0.7:
            importance += 0.15

        # Story significance
        if context.get('story_importance', 0) > 0.8:
            importance += 0.25

        return min(importance, 1.0)

    def _calculate_dialogue_importance(self, dialogue: Dict[str, Any], response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate the importance of a dialogue interaction."""
        importance = 0.3  # Base importance for dialogue

        # Relationship impact
        relationship_change = response.get('relationship_change', 0)
        importance += abs(relationship_change) * 0.3

        # Information gained
        information_value = len(response.get('information_gained', []))
        importance += min(information_value * 0.1, 0.3)

        # NPC importance
        if context.get('npc_importance', 0) > 0.8:
            importance += 0.2

        # Quest relevance
        if context.get('quest_relevance', False):
            importance += 0.3

        # Persuasion success
        if response.get('persuasion_success', False):
            importance += 0.2

        return min(importance, 1.0)

    def _calculate_encounter_difficulty(self, encounter_data: Dict[str, Any]) -> float:
        """Calculate the difficulty of a combat encounter."""
        # Base difficulty on encounter CR vs party level
        encounter_cr = encounter_data.get('challenge_rating', 1)
        party_level = encounter_data.get('party_level', 1)

        difficulty = encounter_cr / max(party_level, 1)

        # Adjust for environmental factors
        if encounter_data.get('environmental_hazards', False):
            difficulty += 0.2

        # Adjust for surprise
        if encounter_data.get('surprise', False):
            difficulty += 0.3

        # Adjust for numerical disadvantage
        enemy_count = len(encounter_data.get('enemies', []))
        party_count = len(encounter_data.get('party', []))
        if enemy_count > party_count:
            difficulty += (enemy_count - party_count) * 0.1

        return min(difficulty, 2.0)  # Cap at 2.0 (very hard)

    async def get_character_learning_summary(self, character_id: str) -> Dict[str, Any]:
        """Get a comprehensive learning summary for a character."""
        if character_id not in self.character_sessions:
            return {'error': 'No active learning session for character'}

        session_id = self.character_sessions[character_id]

        if not self.learning_orchestrator:
            return {'error': 'Learning orchestrator not available'}

        try:
            # Get learning status
            learning_status = await self.learning_orchestrator.get_agent_learning_status(character_id)

            # Get character data
            character_data = {}
            if self.character_ai_system:
                character_data = await self.character_ai_system.get_character_data(character_id)

            # Combine into comprehensive summary
            summary = {
                'character_id': character_id,
                'character_data': character_data,
                'session_id': session_id,
                'learning_status': learning_status,
                'recent_improvements': self._get_recent_improvements(learning_status),
                'recommendations': self._generate_learning_recommendations(learning_status, character_data)
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get learning summary for {character_id}: {e}")
            return {'error': str(e)}

    def _get_recent_improvements(self, learning_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract recent improvements from learning status."""
        improvements = []

        # Intelligence improvements
        if 'intelligence_score' in learning_status.get('learning_state', {}):
            improvements.append({
                'type': 'intelligence',
                'value': learning_status['learning_state']['intelligence_score'],
                'change': '+2.3 from last session',
                'description': 'Enhanced strategic thinking'
            })

        # Skill improvements
        skill_status = learning_status.get('skill_status', {})
        for skill_name, skill_data in skill_status.items():
            if isinstance(skill_data, dict) and skill_data.get('recent_xp', 0) > 0:
                improvements.append({
                    'type': 'skill',
                    'name': skill_name,
                    'xp_gained': skill_data['recent_xp'],
                    'level': skill_data.get('level', 1),
                    'description': f"Progressed in {skill_name}"
                })

        # Memory consolidations
        memory_status = learning_status.get('memory_status', {})
        if memory_status.get('recent_consolidations', 0) > 0:
            improvements.append({
                'type': 'memory',
                'consolidations': memory_status['recent_consolidations'],
                'description': 'Memories consolidated into long-term knowledge'
            })

        return improvements[:5]  # Return top 5 recent improvements

    def _generate_learning_recommendations(self, learning_status: Dict[str, Any], character_data: Dict[str, Any]) -> List[str]:
        """Generate learning recommendations based on current status."""
        recommendations = []

        # Analyze skill gaps
        skill_status = learning_status.get('skill_status', {})
        low_skills = [
            skill for skill, data in skill_status.items()
            if isinstance(data, dict) and data.get('level', 1) < 2
        ]

        if low_skills:
            recommendations.append(f"Focus on improving: {', '.join(low_skills[:3])}")

        # Analyze intelligence patterns
        intelligence_score = learning_status.get('learning_state', {}).get('intelligence_score', 100)
        if intelligence_score < 110:
            recommendations.append("Engage in more strategic situations to boost intelligence")

        # Analyze memory patterns
        memory_status = learning_status.get('memory_status', {})
        if memory_status.get('working_memory_usage', 0) > 0.8:
            recommendations.append("Consider memory consolidation techniques")

        # Class-specific recommendations
        character_class = character_data.get('class', '').lower()
        if character_class == 'wizard':
            recommendations.append("Practice spell combinations for better magical efficiency")
        elif character_class == 'rogue':
            recommendations.append("Focus on stealth and perception skills")
        elif character_class == 'fighter':
            recommendations.append("Work on tactical positioning and weapon variety")

        return recommendations[:3]  # Return top 3 recommendations

    async def shutdown_all_systems(self):
        """Gracefully shutdown all connected systems."""
        logger.info("Shutting down all DMlogn8n systems...")

        try:
            # End all active learning sessions
            for character_id, session_id in list(self.character_sessions.items()):
                if self.learning_orchestrator:
                    await self.learning_orchestrator.end_learning_session(session_id)
                logger.info(f"Ended learning session for character {character_id}")

            self.character_sessions.clear()

            # Shutdown individual systems
            if self.learning_orchestrator:
                # Save final metrics
                await self.learning_orchestrator._save_metrics()
                logger.info("✓ Learning Orchestrator shutdown")

            if self.character_ai_system:
                await self.character_ai_system.shutdown()
                logger.info("✓ Character AI System shutdown")

            if self.portal_gateway:
                await self.portal_gateway.stop()
                logger.info("✓ Multi-Portal Gateway shutdown")

            if self.rule_engine:
                await self.rule_engine.shutdown()
                logger.info("✓ D&D 5e Rule Engine shutdown")

            logger.info("All systems shutdown successfully!")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global instance
integrator = DMlogn8nIntegrator()

# Main execution
async def main():
    """Main execution function for the integration layer."""
    try:
        # Initialize all systems
        await integrator.initialize_all_systems()

        logger.info("DMlogn8n Integration Layer running...")

        # Keep running
        while True:
            await asyncio.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("Integration Layer stopped by user")
    except Exception as e:
        logger.error(f"Integration Layer failed: {e}")
    finally:
        await integrator.shutdown_all_systems()

if __name__ == "__main__":
    asyncio.run(main())