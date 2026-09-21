"""
Core Character AI Engine
Central orchestrator for all character AI components
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from character_profile import CharacterProfile
from game_state import GameState
from personality_engine import PersonalityEngine
from decision_maker import StrategicDecisionMaker
from memory_system import MemorySystem
from dialogue_generator import DialogueGenerator
from class_modules import ClassAIFactory


class CharacterAI:
    """Main Character AI engine that orchestrates all subsystems"""

    def __init__(self, character_profile: CharacterProfile):
        self.character_id = str(uuid.uuid4())
        self.profile = character_profile

        # Initialize core AI components
        self.personality_engine = PersonalityEngine(character_profile)
        self.decision_maker = StrategicDecisionMaker(character_profile)
        self.memory_system = MemorySystem(character_profile)
        self.dialogue_generator = DialogueGenerator(character_profile)

        # Initialize class-specific AI module
        self.class_ai = ClassAIFactory.create_class_ai(
            character_profile.character_class,
            character_profile
        )

        # Current state
        self.current_state = GameState()
        self.current_mood = "neutral"
        self.current_goals: List[str] = []

        # AI state tracking
        self.last_decision_time = datetime.now()
        self.decision_history: List[Dict[str, Any]] = []

        print(f"Character AI initialized: {character_profile.name} ({character_profile.character_class})")

    def update_state(self, new_state: GameState) -> None:
        """Update the current game state"""
        self.current_state = new_state
        self.decision_maker.update_state(new_state)

        # Trigger personality reactions to state changes
        self._react_to_state_changes()

    def _react_to_state_changes(self) -> None:
        """Process personality-based reactions to state changes"""
        # Update mood based on situation
        if self.current_state.combat_status:
            self.current_mood = self.personality_engine.get_combat_mood()
        else:
            self.current_mood = self.personality_engine.get_peacetime_mood()

    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a strategic decision based on current situation"""
        # Gather information from all AI components
        personality_bias = self.personality_engine.get_decision_bias()
        memory_context = self.memory_system.get_relevant_memories(context)
        class_recommendations = self.class_ai.get_action_recommendations(self.current_state)

        # Combine all inputs for decision making
        decision_context = {
            "personality_bias": personality_bias,
            "memory_context": memory_context,
            "class_recommendations": class_recommendations,
            "current_state": self.current_state,
            "external_context": context
        }

        # Make the strategic decision
        decision = self.decision_maker.make_decision(decision_context)

        # Record decision for learning
        self._record_decision(decision)

        return decision

    def _record_decision(self, decision: Dict[str, Any]) -> None:
        """Record decision for future learning and pattern recognition"""
        decision_record = {
            "timestamp": datetime.now(),
            "decision": decision,
            "state": self.current_state,
            "mood": self.current_mood
        }
        self.decision_history.append(decision_record)

        # Update memory system
        self.memory_system.record_decision(decision_record)

        # Update last decision time
        self.last_decision_time = datetime.now()

    def generate_dialogue(self, context: Dict[str, Any], dialogue_type: str = "general") -> str:
        """Generate character-appropriate dialogue"""
        # Get personality-influenced speech patterns
        speech_style = self.personality_engine.get_speech_style()

        # Get relevant memories for context
        memory_context = self.memory_system.get_relevant_memories(context)

        # Generate dialogue
        dialogue = self.dialogue_generator.generate_dialogue(
            context=context,
            speech_style=speech_style,
            mood=self.current_mood,
            memory_context=memory_context,
            dialogue_type=dialogue_type
        )

        return dialogue

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from the results of actions"""
        # Update memory system with outcome
        self.memory_system.record_outcome(action, outcome)

        # Update personality traits based on experience
        self.personality_engine.process_experience(outcome)

        # Update class-specific AI learning
        self.class_ai.learn_from_outcome(action, outcome)

        # Update decision patterns
        self.decision_maker.learn_from_outcome(action, outcome)

    def get_character_status(self) -> Dict[str, Any]:
        """Get comprehensive character status"""
        return {
            "character_id": self.character_id,
            "name": self.profile.name,
            "class": self.profile.character_class,
            "level": self.profile.level,
            "current_mood": self.current_mood,
            "current_goals": self.current_goals,
            "personality_traits": self.personality_engine.get_active_traits(),
            "memory_summary": self.memory_system.get_memory_summary(),
            "decision_patterns": self.decision_maker.get_decision_patterns(),
            "class_ai_status": self.class_ai.get_status()
        }

    def update_goals(self, new_goals: List[str]) -> None:
        """Update current character goals"""
        self.current_goals = new_goals
        self.decision_maker.update_goals(new_goals)
        self.class_ai.update_goals(new_goals)

    def handle_social_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social interactions with other characters"""
        # Process personality reaction to interaction
        personality_response = self.personality_engine.process_social_interaction(interaction)

        # Generate dialogue response
        dialogue = self.generate_dialogue(
            context=interaction,
            dialogue_type="social"
        )

        # Update relationship memories
        self.memory_system.update_relationship(interaction["other_character"], interaction)

        return {
            "dialogue": dialogue,
            "personality_response": personality_response,
            "relationship_change": self.memory_system.get_relationship_change(interaction["other_character"])
        }