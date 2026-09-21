"""
Dialogue Generation System
Character-appropriate speech patterns, context-aware responses, and strategic conversation
"""

import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from character_profile import CharacterProfile
from memory_system import MemorySystem


class DialogueType(Enum):
    """Types of dialogue"""
    GENERAL = "general"
    COMBAT = "combat"
    SOCIAL = "social"
    INTIMIDATION = "intimidation"
    PERSUASION = "persuasion"
    DIPLOMACY = "diplomacy"
    DECEPTION = "deception"
    COMMAND = "command"
    QUESTION = "question"
    RESPONSE = "response"
    EMOTIONAL = "emotional"


class EmotionalTone(Enum):
    """Emotional tones for dialogue"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    FEARFUL = "fearful"
    CONFIDENT = "confident"
    CAUTIOUS = "cautious"
    EXCITED = "excited"
    SARCASTIC = "sarcastic"
    SERIOUS = "serious"


@dataclass
class DialogueTemplate:
    """Template for generating dialogue"""
    template_id: str
    dialogue_type: DialogueType
    emotional_tone: EmotionalTone
    patterns: List[str]  # Template patterns with placeholders
    contexts: List[str]  # Contexts where this template applies
    personality_requirements: Dict[str, float]  # Personality trait requirements


@dataclass
class SpeechPattern:
    """Character-specific speech pattern"""
    vocabulary_level: str  # simple, moderate, sophisticated
    sentence_structure: str  # simple, complex, varied
    speech_rate: str  # slow, moderate, fast
    formality_level: str  # informal, neutral, formal
    characteristic_phrases: List[str]
    accent_features: List[str]


class DialogueGenerator:
    """Advanced dialogue generation system"""

    def __init__(self, character_profile: CharacterProfile):
        self.profile = character_profile
        self.memory_system: Optional[MemorySystem] = None

        # Character speech patterns
        self.speech_pattern = self._create_speech_pattern()

        # Dialogue templates
        self.dialogue_templates = self._load_dialogue_templates()

        # Character-specific phrases and mannerisms
        self.character_phrases = self._generate_character_phrases()
        self.verbal_tics = self._generate_verbal_tics()

        # Context history for coherence
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_topic: Optional[str] = None

    def _create_speech_pattern(self) -> SpeechPattern:
        """Create speech pattern based on character attributes"""
        # Base patterns by class
        class_patterns = {
            "Fighter": SpeechPattern(
                vocabulary_level="moderate",
                sentence_structure="simple",
                speech_rate="moderate",
                formality_level="neutral",
                characteristic_phrases=["Let's handle this.", "Stay behind me.", "For honor!"],
                accent_features=["direct", "clear"]
            ),
            "Rogue": SpeechPattern(
                vocabulary_level="moderate",
                sentence_structure="varied",
                speech_rate="moderate",
                formality_level="informal",
                characteristic_phrases=["Let's be smart about this.", "I see an opportunity.", "Trust me."],
                accent_features=["subtle", "measured"]
            ),
            "Wizard": SpeechPattern(
                vocabulary_level="sophisticated",
                sentence_structure="complex",
                speech_rate="moderate",
                formality_level="formal",
                characteristic_phrases=["According to my research...", "The arcane principles suggest...", "Allow me to elucidate."],
                accent_features=["precise", "academic"]
            ),
            "Cleric": SpeechPattern(
                vocabulary_level="moderate",
                sentence_structure="complex",
                speech_rate="moderate",
                formality_level="formal",
                characteristic_phrases=["By the gods...", "Divine wisdom guides us.", "Have faith."],
                accent_features=["soothing", "authoritative"]
            ),
            "Barbarian": SpeechPattern(
                vocabulary_level="simple",
                sentence_structure="simple",
                speech_rate="fast",
                formality_level="informal",
                characteristic_phrases=["SMASH!", "Me strong!", "No fear!"],
                accent_features=["loud", "direct"]
            ),
            "Bard": SpeechPattern(
                vocabulary_level="sophisticated",
                sentence_structure="varied",
                speech_rate="moderate",
                formality_level="neutral",
                characteristic_phrases=["Allow me to sing a tale...", "Beauty in all things!", "Let harmony guide us."],
                accent_features=["melodic", "expressive"]
            )
        }

        base_pattern = class_patterns.get(self.profile.character_class, SpeechPattern(
            vocabulary_level="moderate",
            sentence_structure="varied",
            speech_rate="moderate",
            formality_level="neutral",
            characteristic_phrases=[],
            accent_features=[]
        ))

        # Adjust based on intelligence
        int_modifier = (self.profile.intelligence - 10) / 10
        if int_modifier > 0.5:
            base_pattern.vocabulary_level = "sophisticated"
            base_pattern.sentence_structure = "complex"
        elif int_modifier < -0.5:
            base_pattern.vocabulary_level = "simple"
            base_pattern.sentence_structure = "simple"

        # Adjust based on charisma
        cha_modifier = (self.profile.charisma - 10) / 10
        if cha_modifier > 0.5:
            base_pattern.characteristic_phrases.extend(["I believe...", "Trust in me...", "Together we can..."])
        elif cha_modifier < -0.5:
            base_pattern.speech_rate = "slow"
            base_pattern.characteristic_phrases.extend(["...", "Um...", "I think..."])

        return base_pattern

    def _load_dialogue_templates(self) -> List[DialogueTemplate]:
        """Load dialogue templates for various situations"""
        templates = []

        # Combat dialogue
        combat_templates = [
            DialogueTemplate(
                template_id="combat_attack",
                dialogue_type=DialogueType.COMBAT,
                emotional_tone=EmotionalTone.CONFIDENT,
                patterns=[
                    "For {goal}! I'll attack {target}!",
                    "{target}, face my {weapon}!",
                    "I strike at {target} with determination!"
                ],
                contexts=["combat", "attack"],
                personality_requirements={"extraversion": 0.6}
            ),
            DialogueTemplate(
                template_id="combat_defense",
                dialogue_type=DialogueType.COMBAT,
                emotional_tone=EmotionalTone.CAUTIOUS,
                patterns=[
                    "I'll protect {ally} from {threat}.",
                    "Defensive position against {enemy}.",
                    "Stay close, {ally}, I've got your back."
                ],
                contexts=["combat", "defense"],
                personality_requirements={"agreeableness": 0.7}
            ),
            DialogueTemplate(
                template_id="combat_hurt",
                dialogue_type=DialogueType.COMBAT,
                emotional_tone=EmotionalTone.FEARFUL,
                patterns=[
                    "I'm injured, but I'll keep fighting!",
                    "This wound won't stop me!",
                    "Need healing, but can still fight!"
                ],
                contexts=["combat", "injured"],
                personality_requirements={}
            )
        ]

        # Social dialogue
        social_templates = [
            DialogueTemplate(
                template_id="social_greeting",
                dialogue_type=DialogueType.SOCIAL,
                emotional_tone=EmotionalTone.NEUTRAL,
                patterns=[
                    "Greetings, {name}. I am {my_name}.",
                    "Hello {name}, pleasure to meet you.",
                    "Well met, {name}."
                ],
                contexts=["social", "greeting"],
                personality_requirements={"extraversion": 0.4}
            ),
            DialogueTemplate(
                template_id="social_question",
                dialogue_type=DialogueType.QUESTION,
                emotional_tone=EmotionalTone.NEUTRAL,
                patterns=[
                    "Can you tell me about {topic}?",
                    "What do you know of {subject}?",
                    "I'm curious about {topic}."
                ],
                contexts=["social", "inquiry"],
                personality_requirements={"openness": 0.6}
            ),
            DialogueTemplate(
                template_id="social_offer_help",
                dialogue_type=DialogueType.SOCIAL,
                emotional_tone=EmotionalTone.HAPPY,
                patterns=[
                    "I can help with {task}.",
                    "Allow me to assist you with {problem}.",
                    "Together we can solve {issue}."
                ],
                contexts=["social", "help"],
                personality_requirements={"agreeableness": 0.7}
            )
        ]

        # Strategic dialogue
        strategic_templates = [
            DialogueTemplate(
                template_id="strategic_plan",
                dialogue_type=DialogueType.DIPLOMACY,
                emotional_tone=EmotionalTone.SERIOUS,
                patterns=[
                    "Here's my plan: {plan_details}",
                    "I suggest we {strategy}",
                    "Our best approach is to {method}"
                ],
                contexts=["strategy", "planning"],
                personality_requirements={"conscientiousness": 0.7}
            ),
            DialogueTemplate(
                template_id="intimidation",
                dialogue_type=DialogueType.INTIMIDATION,
                emotional_tone=EmotionalTone.ANGRY,
                patterns=[
                    "You will {comply}, or face {consequence}.",
                    "I suggest you {action}, unless you want {threat}.",
                    "Don't test me, {target}."
                ],
                contexts=["combat", "threat"],
                personality_requirements={"neuroticism": 0.4}
            ),
            DialogueTemplate(
                template_id="persuasion",
                dialogue_type=DialogueType.PERSUASION,
                emotional_tone=EmotionalTone.CONFIDENT,
                patterns=[
                    "If you {action}, then {reward}.",
                    "Consider the benefits of {proposal}.",
                    "I believe you'll find that {argument} makes sense."
                ],
                contexts=["social", "negotiation"],
                personality_requirements={"charisma": 0.7}
            )
        ]

        templates.extend(combat_templates)
        templates.extend(social_templates)
        templates.extend(strategic_templates)

        return templates

    def _generate_character_phrases(self) -> List[str]:
        """Generate character-specific phrases"""
        base_phrases = []

        # Class-specific phrases
        class_phrases = {
            "Fighter": ["For honor!", "Never surrender!", "Stand your ground!"],
            "Rogue": ["Silence is golden.", "Opportunity knocks.", "Trust your instincts."],
            "Wizard": ["Knowledge is power.", "The arcane reveals all.", "Logic prevails."],
            "Cleric": ["Faith guides us.", "Divine will be done.", "Light in darkness."],
            "Barbarian": ["Strong survive!", "No fear!", "Might makes right!"],
            "Bard": ["Beauty in all.", "Song soothes the soul.", "Art speaks truth."]
        }

        base_phrases.extend(class_phrases.get(self.profile.character_class, []))

        # Background phrases
        if self.profile.background:
            background_phrases = {
                "Soldier": ["Fall in!", "Hold the line!", "For the cause!"],
                "Noble": ["By my honor.", "Duty calls.", "Protocol matters."],
                "Sage": ["Research shows...", "According to texts...", "Theories suggest..."],
                "Criminal": ["Keep quiet.", "No witnesses.", "Opportunity first."]
            }
            base_phrases.extend(background_phrases.get(self.profile.background, []))

        return base_phrases

    def _generate_verbal_tics(self) -> List[str]:
        """Generate verbal tics based on personality"""
        tics = []

        # Based on mental attributes
        if self.profile.intelligence < 8:
            tics.extend(["Um...", "Uh...", "I think..."])
        elif self.profile.intelligence > 14:
            tics.extend(["Actually...", "Technically...", "In fact..."])

        if self.profile.wisdom < 8:
            tics.extend(["Maybe...", "I guess...", "Probably..."])
        elif self.profile.wisdom > 14:
            tics.extend(["Wisdom suggests...", "Experience tells me...", "Instinct says..."])

        # Based on charisma
        if self.profile.charisma < 8:
            tics.extend(["...", "Well...", "So..."])
        elif self.profile.charisma > 14:
            tics.extend(["My friend...", "Believe me...", "Trust me..."])

        return tics[:2]  # Limit to 2 verbal tics

    def generate_dialogue(self, context: Dict[str, Any], speech_style: Dict[str, Any],
                         mood: str, memory_context: List, dialogue_type: str = "general") -> str:
        """Generate context-appropriate dialogue"""
        # Determine dialogue type and emotional tone
        dialogue_type_enum = self._determine_dialogue_type(dialogue_type, context)
        emotional_tone = self._determine_emotional_tone(mood, context)

        # Get relevant templates
        relevant_templates = self._get_relevant_templates(dialogue_type_enum, emotional_tone, context)

        if not relevant_templates:
            return self._generate_fallback_dialogue(context, emotional_tone)

        # Select template
        template = random.choice(relevant_templates)

        # Generate dialogue from template
        dialogue = self._fill_template(template, context, speech_style)

        # Apply speech patterns
        dialogue = self._apply_speech_patterns(dialogue, speech_style)

        # Add character-specific elements
        dialogue = self._add_character_elements(dialogue)

        # Add memory context if available
        if memory_context:
            dialogue = self._incorporate_memory_context(dialogue, memory_context)

        # Add verbal tics occasionally
        if random.random() < 0.2:  # 20% chance
            dialogue = self._add_verbal_tic(dialogue)

        # Record in conversation history
        self._record_dialogue(dialogue, context, dialogue_type_enum)

        return dialogue

    def _determine_dialogue_type(self, dialogue_type: str, context: Dict[str, Any]) -> DialogueType:
        """Determine the type of dialogue to generate"""
        type_mapping = {
            "general": DialogueType.GENERAL,
            "combat": DialogueType.COMBAT,
            "social": DialogueType.SOCIAL,
            "intimidation": DialogueType.INTIMIDATION,
            "persuasion": DialogueType.PERSUASION,
            "diplomacy": DialogueType.DIPLOMACY,
            "deception": DialogueType.DECEPTION,
            "question": DialogueType.QUESTION
        }

        base_type = type_mapping.get(dialogue_type, DialogueType.GENERAL)

        # Adjust based on context
        if context.get("combat_status", False):
            return DialogueType.COMBAT
        elif context.get("social_situation", False):
            return DialogueType.SOCIAL
        elif context.get("threat", False):
            return DialogueType.INTIMIDATION

        return base_type

    def _determine_emotional_tone(self, mood: str, context: Dict[str, Any]) -> EmotionalTone:
        """Determine emotional tone for dialogue"""
        # Map mood to emotional tone
        mood_mapping = {
            "happy": EmotionalTone.HAPPY,
            "angry": EmotionalTone.ANGRY,
            "sad": EmotionalTone.SAD,
            "fearful": EmotionalTone.FEARFUL,
            "confident": EmotionalTone.CONFIDENT,
            "cautious": EmotionalTone.CAUTIOUS,
            "excited": EmotionalTone.EXCITED,
            "neutral": EmotionalTone.NEUTRAL
        }

        base_tone = mood_mapping.get(mood, EmotionalTone.NEUTRAL)

        # Adjust based on context
        if context.get("combat_status", False):
            if context.get("health_low", False):
                return EmotionalTone.FEARFUL
            else:
                return EmotionalTone.CONFIDENT

        return base_tone

    def _get_relevant_templates(self, dialogue_type: DialogueType, emotional_tone: EmotionalTone,
                               context: Dict[str, Any]) -> List[DialogueTemplate]:
        """Get templates relevant to current situation"""
        relevant_templates = []

        for template in self.dialogue_templates:
            if template.dialogue_type == dialogue_type and template.emotional_tone == emotional_tone:
                # Check context relevance
                if any(ctx in str(context).lower() for ctx in template.contexts):
                    relevant_templates.append(template)

        return relevant_templates

    def _fill_template(self, template: DialogueTemplate, context: Dict[str, Any],
                      speech_style: Dict[str, Any]) -> str:
        """Fill template with context-specific content"""
        pattern = random.choice(template.patterns)

        # Common replacements
        replacements = {
            "{my_name}": self.profile.name,
            "{target}": context.get("target", "the enemy"),
            "{ally}": context.get("ally", "my friend"),
            "{weapon}": context.get("weapon", "my weapon"),
            "{goal}": context.get("goal", "victory"),
            "{name}": context.get("other_character", "friend"),
            "{topic}": context.get("topic", "this matter"),
            "{subject}": context.get("subject", "the subject"),
            "{task}": context.get("task", "this task"),
            "{problem}": context.get("problem", "this problem"),
            "{issue}": context.get("issue", "this issue"),
            "{plan_details}": context.get("plan", "my plan"),
            "{strategy}": context.get("strategy", "strategic action"),
            "{method}": context.get("method", "the best method"),
            "{comply}": context.get("demand", "do what I say"),
            "{consequence}": context.get("threat", "consequences"),
            "{action}": context.get("requested_action", "cooperate"),
            "{threat}": context.get("threat_outcome", "trouble"),
            "{reward}": context.get("reward", "benefits"),
            "{proposal}": context.get("proposal", "this proposal"),
            "{argument}": context.get("argument", "my reasoning")
        }

        # Apply replacements
        result = pattern
        for placeholder, replacement in replacements.items():
            result = result.replace(placeholder, str(replacement))

        return result

    def _apply_speech_patterns(self, dialogue: str, speech_style: Dict[str, Any]) -> str:
        """Apply character-specific speech patterns to dialogue"""
        # Adjust based on vocabulary level
        if self.speech_pattern.vocabulary_level == "simple":
            # Simplify complex words
            dialogue = dialogue.replace("elucidate", "explain")
            dialogue = dialogue.replace("endeavor", "try")
            dialogue = dialogue.replace("assistance", "help")
        elif self.speech_pattern.vocabulary_level == "sophisticated":
            # Use more complex vocabulary
            dialogue = dialogue.replace("help", "assistance")
            dialogue = dialogue.replace("show", "demonstrate")
            dialogue = dialogue.replace("think", "contemplate")

        # Adjust sentence structure
        if self.speech_pattern.sentence_structure == "simple":
            # Break complex sentences
            if ", and " in dialogue:
                dialogue = dialogue.replace(", and ", ". And ")
        elif self.speech_pattern.sentence_structure == "complex":
            # Add conjunctions
            if "." in dialogue and not "," in dialogue:
                dialogue = dialogue.replace(".", ", however.", 1)

        return dialogue

    def _add_character_elements(self, dialogue: str) -> str:
        """Add character-specific phrases and mannerisms"""
        # Occasionally add characteristic phrases
        if random.random() < 0.1:  # 10% chance
            if self.character_phrases:
                phrase = random.choice(self.character_phrases)
                dialogue = f"{phrase} {dialogue}"

        return dialogue

    def _incorporate_memory_context(self, dialogue: str, memory_context: List) -> str:
        """Incorporate relevant memories into dialogue"""
        if not memory_context:
            return dialogue

        # Simple memory incorporation - can be made more sophisticated
        for memory in memory_context[:2]:  # Limit to 2 memories
            if isinstance(memory, dict) and "content" in memory:
                content = memory["content"]
                if isinstance(content, dict):
                    if "location" in content:
                        dialogue += f" (reminds me of {content['location']})"
                    elif "person" in content:
                        dialogue += f" (like {content['person']})"

        return dialogue

    def _add_verbal_tic(self, dialogue: str) -> str:
        """Add verbal tic to dialogue"""
        if self.verbal_tics:
            tic = random.choice(self.verbal_tics)
            dialogue = f"{tic} {dialogue}"

        return dialogue

    def _generate_fallback_dialogue(self, context: Dict[str, Any], emotional_tone: EmotionalTone) -> str:
        """Generate fallback dialogue when no templates match"""
        fallbacks = {
            EmotionalTone.NEUTRAL: ["I understand.", "Let's proceed.", "Noted."],
            EmotionalTone.CONFIDENT: ["I can handle this.", "Leave it to me.", "Watch this."],
            EmotionalTone.CAUTIOUS: ["Let's be careful.", "Are you sure?", "Maybe we should wait."],
            EmotionalTone.HAPPY: ["Excellent!", "Wonderful!", "Great!"],
            EmotionalTone.ANGRY: ["This is unacceptable.", "I won't stand for this.", "Enough!"],
            EmotionalTone.FEARFUL: ["I'm not sure about this.", "Be careful.", "This seems dangerous."]
        }

        possible_dialogue = fallbacks.get(emotional_tone, ["I see.", "Understood.", "Alright."])
        return random.choice(possible_dialogue)

    def _record_dialogue(self, dialogue: str, context: Dict[str, Any], dialogue_type: DialogueType) -> None:
        """Record dialogue in conversation history"""
        record = {
            "dialogue": dialogue,
            "context": context,
            "type": dialogue_type.value,
            "timestamp": context.get("timestamp", "unknown")
        }

        self.conversation_history.append(record)

        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        # Update current topic
        if "topic" in context:
            self.current_topic = context["topic"]

    def generate_response(self, input_dialogue: str, context: Dict[str, Any]) -> str:
        """Generate a response to input dialogue"""
        # Analyze input dialogue
        input_analysis = self._analyze_input_dialogue(input_dialogue)

        # Update context with input analysis
        context.update(input_analysis)

        # Generate response
        response = self.generate_dialogue(
            context=context,
            speech_style={},  # Will be determined by character
            mood=context.get("mood", "neutral"),
            memory_context=[],  # Will be provided by memory system
            dialogue_type="response"
        )

        return response

    def _analyze_input_dialogue(self, dialogue: str) -> Dict[str, Any]:
        """Analyze input dialogue to determine appropriate response"""
        analysis = {}

        dialogue_lower = dialogue.lower()

        # Detect emotional content
        if any(word in dialogue_lower for word in ["angry", "mad", "furious"]):
            analysis["mood"] = "angry"
        elif any(word in dialogue_lower for word in ["happy", "glad", "pleased"]):
            analysis["mood"] = "happy"
        elif any(word in dialogue_lower for word in ["sad", "upset", "hurt"]):
            analysis["mood"] = "sad"
        elif any(word in dialogue_lower for word in ["scared", "afraid", "frightened"]):
            analysis["mood"] = "fearful"
        else:
            analysis["mood"] = "neutral"

        # Detect intent
        if "?" in dialogue:
            analysis["intent"] = "question"
        elif any(word in dialogue_lower for word in ["please", "help", "assist"]):
            analysis["intent"] = "request"
        elif any(word in dialogue_lower for word in ["stop", "don't", "quit"]):
            analysis["intent"] = "command"
        else:
            analysis["intent"] = "statement"

        return analysis