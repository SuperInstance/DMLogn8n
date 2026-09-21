"""
Personality Engine - Big Five Model and Character Background System
Implements personality-driven behavior patterns
"""

import random
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from character_profile import CharacterProfile


class PersonalityTrait(Enum):
    """Big Five personality traits"""
    OPENNESS = "openness"      # Openness to experience
    CONSCIENTIOUSNESS = "conscientiousness"  # Organization and responsibility
    EXTRAVERSION = "extraversion"  # Social engagement and assertiveness
    AGREEABLENESS = "agreeableness"  # Compassion and cooperation
    NEUROTICISM = "neuroticism"  # Emotional stability


@dataclass
class BigFivePersonality:
    """Big Five personality traits with 0-100 scores"""
    openness: float = 50.0          # Creative, curious vs. conventional, cautious
    conscientiousness: float = 50.0 # Organized, disciplined vs. disorganized, impulsive
    extraversion: float = 50.0      # Outgoing, energetic vs. solitary, reserved
    agreeableness: float = 50.0     # Friendly, compassionate vs. challenging, detached
    neuroticism: float = 50.0       # Sensitive, nervous vs. secure, confident

    def get_primary_traits(self) -> List[Tuple[PersonalityTrait, float]]:
        """Get the 2-3 most dominant personality traits"""
        traits = [
            (PersonalityTrait.OPENNESS, self.openness),
            (PersonalityTrait.CONSCIENTIOUSNESS, self.conscientiousness),
            (PersonalityTrait.EXTRAVERSION, self.extraversion),
            (PersonalityTrait.AGREEABLENESS, self.agreeableness),
            (PersonalityTrait.NEUROTICISM, self.neuroticism)
        ]
        return sorted(traits, key=lambda x: x[1], reverse=True)[:3]

    def get_trait_score(self, trait: PersonalityTrait) -> float:
        """Get score for a specific trait"""
        return getattr(self, trait.value)


class PersonalityEngine:
    """Core personality engine that drives character behavior"""

    def __init__(self, character_profile: CharacterProfile):
        self.profile = character_profile

        # Initialize Big Five personality based on class, race, and background
        self.big_five = self._generate_base_personality()

        # Personality modifiers from race and background
        self.racial_modifiers = self._get_racial_modifiers()
        self.background_modifiers = self._get_background_modifiers()

        # Apply modifiers to base personality
        self._apply_modifiers()

        # Current personality state (can evolve over time)
        self.current_personality = BigFivePersonality(
            openness=self.big_five.openness,
            conscientiousness=self.big_five.conscientiousness,
            extraversion=self.big_five.extraversion,
            agreeableness=self.big_five.agreeableness,
            neuroticism=self.big_five.neuroticism
        )

        # Mood tracking
        self.current_mood = "neutral"
        self.mood_history: List[Tuple[str, float]] = []

    def _generate_base_personality(self) -> BigFivePersonality:
        """Generate base personality based on character class"""
        class_personalities = {
            "Fighter": BigFivePersonality(
                openness=35,  # Practical, straightforward
                conscientiousness=75,  # Disciplined, reliable
                extraversion=60,  # Confident, assertive
                agreeableness=50,  # Varies by individual
                neuroticism=30  # Emotionally stable under pressure
            ),
            "Rogue": BigFivePersonality(
                openness=65,  # Creative, adaptable
                conscientiousness=40,  # Flexible, opportunistic
                extraversion=55,  # Social when needed
                agreeableness=35,  # Self-interested
                neuroticism=45  # Cautious but adaptable
            ),
            "Wizard": BigFivePersonality(
                openness=85,  # Highly creative, curious
                conscientiousness=70,  # Studious, methodical
                extraversion=30,  # Often introverted, focused
                agreeableness=60,  # Generally cooperative
                neuroticism=40  # Mentally stable but sometimes stressed
            ),
            "Cleric": BigFivePersonality(
                openness=55,  # Open to divine wisdom
                conscientiousness=80,  # Devoted, responsible
                extraversion=65,  # Often community-oriented
                agreeableness=85,  # Compassionate, helpful
                neuroticism=25  # Faith provides emotional stability
            ),
            "Barbarian": BigFivePersonality(
                openness=40,  # Pragmatic, instinct-driven
                conscientiousness=35,  # Impulsive, freedom-loving
                extraversion=70,  # Bold, expressive
                agreeableness=45,  # Loyal but direct
                neuroticism=35  # Passionate but emotionally stable
            ),
            "Bard": BigFivePersonality(
                openness=90,  # Highly creative, expressive
                conscientiousness=45,  # Spontaneous, flexible
                extraversion=85,  # Very social, charismatic
                agreeableness=70,  # Generally friendly
                neuroticism=50  # Emotionally expressive
            ),
            "Druid": BigFivePersonality(
                openness=70,  # Connected to natural world
                conscientiousness=60,  # Patient, steady
                extraversion=40,  # Often solitary, contemplative
                agreeableness=75,  # Nurturing, protective
                neuroticism=30  # Emotionally balanced
            ),
            "Monk": BigFivePersonality(
                openness=60,  # Open to enlightenment
                conscientiousness=90,  # Highly disciplined
                extraversion=35,  # Often reserved, contemplative
                agreeableness=65,  # Generally peaceful
                neuroticism=20  # Highly emotionally controlled
            ),
            "Paladin": BigFivePersonality(
                openness=50,  # Open to righteous causes
                conscientiousness=85,  # Highly principled, reliable
                extraversion=60,  # Confident, inspiring
                agreeableness=70,  # Protective, just
                neuroticism=25  # Strong moral foundation
            ),
            "Ranger": BigFivePersonality(
                openness=60,  # Adaptable to wilderness
                conscientiousness=65,  # Self-reliant, prepared
                extraversion=45,  # Often solitary
                agreeableness=55,  # Selective about companions
                neuroticism=35  # Self-sufficient, emotionally stable
            ),
            "Sorcerer": BigFivePersonality(
                openness=80,  # Connected to magical nature
                conscientiousness=50,  # Relies on intuition
                extraversion=55,  # Confident in abilities
                agreeableness=60,  # Varies by personality
                neuroticism=45  # Can be emotionally intense
            ),
            "Warlock": BigFivePersonality(
                openness=75,  # Open to forbidden knowledge
                conscientiousness=55,  # Ambitious, calculating
                extraversion=50,  # Varies by patron
                agreeableness=40,  # Often self-interested
                neuroticism=60  # Can be paranoid or intense
            )
        }

        base = class_personalities.get(self.profile.character_class, BigFivePersonality())

        # Add randomness for individual variation
        for trait in PersonalityTrait:
            current_value = getattr(base, trait.value)
            variation = random.randint(-15, 15)
            new_value = max(10, min(90, current_value + variation))
            setattr(base, trait.value, new_value)

        return base

    def _get_racial_modifiers(self) -> Dict[str, float]:
        """Get personality modifiers based on race"""
        racial_mods = {
            "Human": {"openness": 5, "conscientiousness": 5, "extraversion": 5},
            "Elf": {"openness": 15, "conscientiousness": 10, "neuroticism": -10},
            "Dwarf": {"conscientiousness": 15, "agreeableness": 10, "openness": -10},
            "Halfling": {"agreeableness": 15, "extraversion": 10, "neuroticism": -5},
            "Dragonborn": {"extraversion": 10, "conscientiousness": 10, "neuroticism": -5},
            "Gnome": {"openness": 20, "extraversion": 10, "neuroticism": -10},
            "Half-Elf": {"extraversion": 10, "agreeableness": 10, "openness": 5},
            "Half-Orc": {"extraversion": -5, "conscientiousness": 5, "neuroticism": -10},
            "Tiefling": {"openness": 10, "neuroticism": 10, "agreeableness": -5}
        }
        return racial_mods.get(self.profile.race, {})

    def _get_background_modifiers(self) -> Dict[str, float]:
        """Get personality modifiers based on background"""
        background_mods = {
            "Acolyte": {"conscientiousness": 15, "agreeableness": 10, "neuroticism": -5},
            "Criminal": {"agreeableness": -15, "openness": 10, "neuroticism": 5},
            "Folk Hero": {"extraversion": 10, "agreeableness": 15, "conscientiousness": 5},
            "Noble": {"extraversion": 5, "conscientiousness": 10, "openness": -5},
            "Sage": {"openness": 20, "conscientiousness": 15, "extraversion": -10},
            "Soldier": {"conscientiousness": 15, "extraversion": 5, "neuroticism": -10},
            "Urchin": {"openness": 10, "neuroticism": 15, "agreeableness": -10}
        }
        return background_mods.get(self.profile.background, {})

    def _apply_modifiers(self) -> None:
        """Apply racial and background modifiers to base personality"""
        # Apply racial modifiers
        for trait, modifier in self.racial_modifiers.items():
            current_value = getattr(self.big_five, trait)
            new_value = max(10, min(90, current_value + modifier))
            setattr(self.big_five, trait, new_value)

        # Apply background modifiers
        for trait, modifier in self.background_modifiers.items():
            current_value = getattr(self.big_five, trait)
            new_value = max(10, min(90, current_value + modifier))
            setattr(self.big_five, trait, new_value)

    def get_decision_bias(self) -> Dict[str, Any]:
        """Get personality-based decision biases"""
        biases = {}

        # Openness influences creativity vs. tradition
        if self.current_personality.openness > 70:
            biases["approach"] = "creative_experimental"
        elif self.current_personality.openness < 30:
            biases["approach"] = "traditional_methodical"
        else:
            biases["approach"] = "balanced"

        # Conscientiousness influences planning vs. spontaneity
        if self.current_personality.conscientiousness > 70:
            biases["planning"] = "detailed_strategic"
        elif self.current_personality.conscientiousness < 30:
            biases["planning"] = "spontaneous_opportunistic"
        else:
            biases["planning"] = "moderate"

        # Extraversion influences social approach
        if self.current_personality.extraversion > 70:
            biases["social"] = "assertive_leading"
        elif self.current_personality.extraversion < 30:
            biases["social"] = "reserved_supporting"
        else:
            biases["social"] = "flexible"

        # Agreeableness influences cooperation vs. competition
        if self.current_personality.agreeableness > 70:
            biases["conflict"] = "cooperative_diplomatic"
        elif self.current_personality.agreeableness < 30:
            biases["conflict"] = "competitive_direct"
        else:
            biases["conflict"] = "situational"

        # Neuroticism influences risk tolerance
        if self.current_personality.neuroticism > 70:
            biases["risk"] = "cautious_risk_averse"
        elif self.current_personality.neuroticism < 30:
            biases["risk"] = "bold_risk_tolerant"
        else:
            biases["risk"] = "moderate"

        return biases

    def get_combat_mood(self) -> str:
        """Get mood during combat situations"""
        # Base combat mood on personality
        if self.current_personality.neuroticism > 70:
            return "anxious_focused"
        elif self.current_personality.extraversion > 70:
            return "excited_aggressive"
        elif self.current_personality.agreeableness > 70:
            return "protective_determined"
        elif self.current_personality.conscientiousness > 70:
            return "disciplined_strategic"
        else:
            return "neutral_combat"

    def get_peacetime_mood(self) -> str:
        """Get mood during non-combat situations"""
        if self.current_personality.extraversion > 70:
            return "social_engaged"
        elif self.current_personality.extraversion < 30:
            return "contemplative_reserved"
        elif self.current_personality.openness > 70:
            return "curious_exploring"
        elif self.current_personality.agreeableness > 70:
            return "friendly_helpful"
        else:
            return "balanced"

    def get_speech_style(self) -> Dict[str, Any]:
        """Get speech style based on personality"""
        style = {}

        # Openness affects vocabulary and creativity
        style["vocabulary"] = "rich_metaphorical" if self.current_personality.openness > 60 else "direct"

        # Extraversion affects speech patterns
        style["pace"] = "fast enthusiastic" if self.current_personality.extraversion > 60 else "measured"

        # Agreeableness affects tone
        style["tone"] = "warm cooperative" if self.current_personality.agreeableness > 60 else "neutral"

        # Conscientiousness affects structure
        style["structure"] = "organized_complete" if self.current_personality.conscientiousness > 60 else "spontaneous"

        # Neuroticism affects emotional expression
        style["emotional_level"] = "expressive" if self.current_personality.neuroticism > 60 else "controlled"

        return style

    def process_social_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Process personality response to social interactions"""
        response = {"emotional_reaction": "", "behavioral_tendency": ""}

        # Analyze interaction type and personality-based response
        interaction_type = interaction.get("type", "neutral")

        if interaction_type == "threat":
            if self.current_personality.neuroticism > 60:
                response["emotional_reaction"] = "fear_defensive"
            elif self.current_personality.extraversion > 60:
                response["emotional_reaction"] = "anger_confrontational"
            else:
                response["emotional_reaction"] = "cautious_analytical"

        elif interaction_type == "friendly":
            if self.current_personality.extraversion > 60:
                response["emotional_reaction"] = "enthusiastic_warm"
            elif self.current_personality.agreeableness > 60:
                response["emotional_reaction"] = "welcoming_trusting"
            else:
                response["emotional_reaction"] = "polite_reserved"

        elif interaction_type == "persuasion":
            if self.current_personality.openness > 60:
                response["behavioral_tendency"] = "receptive_curious"
            elif self.current_personality.conscientiousness > 60:
                response["behavioral_tendency"] = "analytical_skeptical"
            else:
                response["behavioral_tendency"] = "cautious_hesitant"

        return response

    def process_experience(self, outcome: Dict[str, Any]) -> None:
        """Update personality based on experiences"""
        experience_type = outcome.get("type", "neutral")
        emotional_impact = outcome.get("emotional_impact", 0)

        # Subtle personality evolution based on significant experiences
        if experience_type == "trauma" and abs(emotional_impact) > 0.7:
            # Increase neuroticism temporarily
            self.current_personality.neuroticism = min(90,
                self.current_personality.neuroticism + 5)
        elif experience_type == "success" and emotional_impact > 0.7:
            # Decrease neuroticism, increase confidence
            self.current_personality.neuroticism = max(10,
                self.current_personality.neuroticism - 3)
        elif experience_type == "leadership":
            # Increase extraversion and conscientiousness
            self.current_personality.extraversion = min(90,
                self.current_personality.extraversion + 2)
            self.current_personality.conscientiousness = min(90,
                self.current_personality.conscientiousness + 2)

    def get_active_traits(self) -> List[str]:
        """Get currently active personality traits"""
        primary_traits = self.current_personality.get_primary_traits()
        active_traits = []

        for trait, score in primary_traits:
            if score > 70:
                intensity = "very_high"
            elif score > 60:
                intensity = "high"
            else:
                intensity = "moderate"

            active_traits.append(f"{trait.value}_{intensity}")

        return active_traits

    def update_mood(self, new_mood: str, intensity: float = 0.5) -> None:
        """Update current mood with intensity"""
        self.current_mood = new_mood
        self.mood_history.append((new_mood, intensity))

        # Keep only recent mood history
        if len(self.mood_history) > 10:
            self.mood_history = self.mood_history[-10:]