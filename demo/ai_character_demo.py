#!/usr/bin/env python3
"""
AI Character Demo - Showcases Intelligent AI Agent Capabilities
Demonstrates advanced AI dialogue, decision-making, and personality systems
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger('DMLogn8n-AICharacterDemo')

class AIState(Enum):
    """AI emotional and mental states"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    EXCITED = "excited"
    WORRIED = "worried"
    CONFUSED = "confused"
    DETERMINED = "determined"

class AIPersonalityTrait(Enum):
    """AI personality traits"""
    BRAVE = "brave"
    CAUTIOUS = "cautious"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    STRATEGIC = "strategic"
    IMPULSIVE = "impulsive"
    HONORABLE = "honorable"
    CUNNING = "cunning"
    GENEROUS = "generous"
    SELFISH = "selfish"
    CURIOUS = "curious"
    WISE = "wise"

@dataclass
class AIConversation:
    """Tracks conversation context and history"""
    id: str
    participants: List[str]
    topic: str
    context: Dict[str, Any]
    messages: List[Dict[str, Any]] = field(default_factory=list)
    emotional_trajectory: List[AIState] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

@dataclass
class AICharacter:
    """Advanced AI character with personality and memory"""
    id: str
    name: str
    class_type: str
    level: int
    personality: List[AIPersonalityTrait]
    current_state: AIState
    memories: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)  # relationship_name -> value
    goals: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    knowledge: Dict[str, Any] = field(default_factory=dict)
    learning_rate: float = 0.1
    adaptation_counter: int = 0

class AICharacterDemo:
    """Showcases AI character intelligence and capabilities"""

    def __init__(self):
        self.ai_characters = {}
        self.conversations = {}
        self.dialogue_templates = self._load_dialogue_templates()
        self.response_patterns = self._load_response_patterns()
        self.learning_mechanisms = self._initialize_learning_mechanisms()
        self.demonstration_scenarios = self._create_demonstration_scenarios()

    def _load_dialogue_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load comprehensive dialogue templates"""
        return {
            "greeting": {
                "friendly": [
                    "Greetings, friend! It's a pleasure to meet you.",
                    "Well met! How may I assist you today?",
                    "Ah, welcome! I hope your journey has been safe.",
                    "It's good to see a friendly face around here."
                ],
                "formal": [
                    "Greetings. I am {name}. How may I be of service?",
                    "Welcome. What business brings you to these lands?",
                    "Salutations. I am at your disposal.",
                    "Good day. State your purpose, if you would."
                ],
                "suspicious": [
                    "Who goes there? State your business.",
                    "What do you want? I don't have time for games.",
                    "Another traveler... What makes you special?",
                    "I'm watching you. Don't try anything foolish."
                ]
            },
            "emotional": {
                AIState.HAPPY: [
                    "This is wonderful! I haven't felt this alive in ages!",
                    "Success at last! All our hard work paid off!",
                    "I'm so grateful for your help. This means everything to me.",
                    "Today is a good day! Let's celebrate our victory!"
                ],
                AIState.ANGRY: [
                    "This is unacceptable! Someone will pay for this!",
                    "How dare they! I won't rest until justice is served!",
                    "Enough of these games! It's time for action!",
                    "My patience has run out. Let's settle this now!"
                ],
                AIState.SAD: [
                    "I... I need a moment. This is too much to bear.",
                    "Everything went wrong. I don't know what to do now.",
                    "Why did this have to happen? It's just not fair.",
                    "I failed. I failed everyone who counted on me."
                ],
                AIState.WORRIED: [
                    "I have a bad feeling about this. We should be careful.",
                    "What if we're making a terrible mistake?",
                    "The risks are too high. Maybe we should reconsider.",
                    "I can't shake this feeling of dread. Something's wrong."
                ],
                AIState.EXCITED: [
                    "This is incredible! I can't believe we're actually doing this!",
                    "I've been waiting for this moment my whole life!",
                    "Adventure calls! Are you ready for something amazing?",
                    "The possibilities are endless! Think of what we could achieve!"
                ]
            },
            "strategic": {
                "planning": [
                    "Let me analyze the situation. We need a solid plan.",
                    "Here's what I suggest: first, we gather intelligence.",
                    "I've been thinking about our approach. Here's my analysis.",
                    "Strategy is key. Let me outline the optimal course of action."
                ],
                "tactical": [
                    "They'll expect a frontal assault. Let's use that against them.",
                    "Divide and conquer. We'll hit them from multiple angles.",
                    "Timing is everything. We strike when they're most vulnerable.",
                    "Feint and strike. Make them think we're going one way, then hit them from another."
                ]
            },
            "learning": {
                "curiosity": [
                    "That's fascinating! Tell me more about that.",
                    "I've never encountered that before. How does it work?",
                    "This changes everything I thought I knew!",
                    "Your perspective is intriguing. I'd like to understand better."
                ],
                "realization": [
                    "Wait... I think I understand now!",
                    "So that's how it works! It all makes sense!",
                    "I see the pattern now. This is brilliant!",
                    "This connects everything! Why didn't I see it before?"
                ]
            }
        }

    def _load_response_patterns(self) -> Dict[str, Any]:
        """Load AI response patterns and decision matrices"""
        return {
            "decision_factors": {
                "self_preservation": 0.3,
                "relationship_values": 0.25,
                "goal_achievement": 0.2,
                "emotional_state": 0.15,
                "learning_opportunity": 0.1
            },
            "response_weights": {
                "aggressive": {"brave": 1.2, "aggressive": 1.5, "strategic": 0.8, "cautious": 0.6},
                "defensive": {"cautious": 1.5, "defensive": 1.3, "wise": 1.1, "impulsive": 0.7},
                "diplomatic": {"honorable": 1.4, "generous": 1.2, "wise": 1.3, "selfish": 0.5},
                "curious": {"curious": 1.5, "wise": 1.2, "strategic": 1.0, "aggressive": 0.8}
            }
        }

    def _initialize_learning_mechanisms(self) -> Dict[str, Any]:
        """Initialize AI learning and adaptation systems"""
        return {
            "pattern_recognition": {
                "conversation_patterns": {},
                "behavior_patterns": {},
                "success_patterns": {}
            },
            "memory_consolidation": {
                "short_term": [],
                "long_term": [],
                "emotional_tags": {}
            },
            "personality_evolution": {
                "trait_changes": {},
                "state_transitions": {},
                "goal_adjustments": {}
            }
        }

    def _create_demonstration_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Create impressive AI demonstration scenarios"""
        return {
            "strategic_planning": {
                "title": "Strategic Battle Planning",
                "description": "AI characters plan a complex military operation",
                "participants": 4,
                "complexity": "high",
                "demonstrates": ["strategy", "coordination", "adaptation", "leadership"]
            },
            "emotional_journey": {
                "title": "Emotional Character Arc",
                "description": "AI character experiences profound emotional development",
                "participants": 2,
                "complexity": "medium",
                "demonstrates": ["emotion", "growth", "relationships", "memory"]
            },
            "problem_solving": {
                "title": "Complex Problem Solving",
                "description": "AI characters collaborate to solve a mystery",
                "participants": 3,
                "complexity": "high",
                "demonstrates": ["logic", "deduction", "cooperation", "learning"]
            },
            "social_dynamics": {
                "title": "Social Network Navigation",
                "description": "AI manages complex social relationships and politics",
                "participants": 5,
                "complexity": "high",
                "demonstrates": ["social_intelligence", "manipulation", "diplomacy", "ethics"]
            },
            "creative_collaboration": {
                "title": "Creative Project Collaboration",
                "description": "AI characters work together on a creative endeavor",
                "participants": 3,
                "complexity": "medium",
                "demonstrates": ["creativity", "cooperation", "compromise", "innovation"]
            }
        }

    async def initialize_ai_characters(self) -> Dict[str, AICharacter]:
        """Initialize AI characters for demonstration"""
        logger.info("🤖 Initializing AI characters...")

        character_configs = [
            {
                "name": "Eldrin Shadowbane",
                "class": "Warrior",
                "level": 45,
                "personality": [AIPersonalityTrait.BRAVE, AIPersonalityTrait.HONORABLE, AIPersonalityTrait.STRATEGIC],
                "goals": ["Protect the innocent", "Become legendary", "Master combat arts"],
                "fears": ["Failing to protect others", "Losing honor"]
            },
            {
                "name": "Lyra Moonwhisper",
                "class": "Mage",
                "level": 42,
                "personality": [AIPersonalityTrait.WISE, AIPersonalityTrait.CURIOUS, AIPersonalityTrait.GENEROUS],
                "goals": ["Unlock ancient magic", "Help others learn", "Discover lost knowledge"],
                "fears": ["Destruction of knowledge", "Misusing her powers"]
            },
            {
                "name": "Kael Nightblade",
                "class": "Rogue",
                "level": 44,
                "personality": [AIPersonalityTrait.CUNNING, AIPersonalityTrait.CAUTIOUS, AIPersonalityTrait.CURIOUS],
                "goals": ["Acquire wealth and power", "Uncover secrets", "Never be caught"],
                "fears": ["Losing freedom", "Being betrayed"]
            },
            {
                "name": "Mira Sunfire",
                "class": "Priest",
                "level": 40,
                "personality": [AIPersonalityTrait.GENEROUS, AIPersonalityTrait.HONORABLE, AIPersonalityTrait.WISE],
                "goals": ["Heal the suffering", "Spread hope", "Protect her companions"],
                "fears": ["Inability to save others", "Loss of faith"]
            },
            {
                "name": "Darius Darkmere",
                "class": "Warlock",
                "level": 46,
                "personality": [AIPersonalityTrait.CUNNING, AIPersonalityTrait.STRATEGIC, AIPersonalityTrait.SELFISH],
                "goals": ["Master forbidden magic", "Gain ultimate power", "Achieve immortality"],
                "fears": ["Being controlled by others", "Loss of power"]
            }
        ]

        for config in character_configs:
            character = AICharacter(
                id=f"ai_{len(self.ai_characters) + 1}",
                name=config["name"],
                class_type=config["class"],
                level=config["level"],
                personality=config["personality"],
                current_state=AIState.NEUTRAL,
                goals=config["goals"],
                fears=config["fears"]
            )

            self.ai_characters[character.id] = character

        logger.info(f"✅ Initialized {len(self.ai_characters)} AI characters")
        return self.ai_characters

    async def run_demo_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Run a specific AI demonstration scenario"""
        if scenario_name not in self.demonstration_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        scenario = self.demonstration_scenarios[scenario_name]
        logger.info(f"🎭 Running AI demo scenario: {scenario['title']}")

        print(f"\n🎬 {scenario['title']}")
        print(f"📝 {scenario['description']}")
        print(f"👥 Participants: {scenario['participants']} AI characters")
        print(f"🧠 Complexity: {scenario['complexity']}")

        # Initialize characters if not already done
        if not self.ai_characters:
            await self.initialize_ai_characters()

        # Select participants
        participants = list(self.ai_characters.values())[:scenario['participants']]

        # Create conversation context
        conversation = await self._create_conversation(scenario, participants)

        # Execute scenario
        results = await self._execute_ai_scenario(conversation)

        # Analyze results
        analysis = await self._analyze_ai_performance(results)

        return {
            'scenario': scenario_name,
            'conversation': conversation,
            'results': results,
            'analysis': analysis,
            'demonstrated_capabilities': scenario['demonstrates']
        }

    async def _create_conversation(self, scenario: Dict[str, Any], participants: List[AICharacter]) -> AIConversation:
        """Create conversation context for AI interaction"""
        conversation = AIConversation(
            id=f"conv_{len(self.conversations) + 1}",
            topic=scenario['title'],
            participants=[p.name for p in participants],
            context={
                'scenario': scenario['title'],
                'complexity': scenario['complexity'],
                'goals': {p.name: p.goals for p in participants},
                'personalities': {p.name: p.personality for p in participants}
            }
        )

        self.conversations[conversation.id] = conversation
        return conversation

    async def _execute_ai_scenario(self, conversation: AIConversation) -> List[Dict[str, Any]]:
        """Execute AI scenario with intelligent interactions"""
        results = []
        participants = [self.ai_characters[f"ai_{i+1}"] for i in range(len(conversation.participants))]

        # Simulate conversation turns
        max_turns = 12
        current_speaker_index = 0

        for turn in range(max_turns):
            current_speaker = participants[current_speaker_index]

            # Generate AI response based on context and personality
            response = await self._generate_ai_response(current_speaker, conversation, turn)

            # Add to conversation
            message = {
                'speaker': current_speaker.name,
                'text': response['text'],
                'emotional_state': response['state'],
                'reasoning': response['reasoning'],
                'turn': turn,
                'timestamp': datetime.now().isoformat()
            }

            conversation.messages.append(message)
            conversation.emotional_trajectory.append(current_speaker.current_state)

            # Update AI character based on interaction
            await self._update_ai_character(current_speaker, response, conversation)

            results.append({
                'turn': turn,
                'speaker': current_speaker.name,
                'response': response,
                'impact': response.get('impact', 'neutral')
            })

            # Rotate speakers
            current_speaker_index = (current_speaker_index + 1) % len(participants)

            # Add dramatic pause
            await asyncio.sleep(0.5)

        return results

    async def _generate_ai_response(self, character: AICharacter, conversation: AIConversation, turn: int) -> Dict[str, Any]:
        """Generate intelligent AI response based on personality and context"""
        # Analyze conversation context
        context_analysis = await self._analyze_conversation_context(character, conversation)

        # Determine emotional state
        new_state = await self._determine_emotional_state(character, context_analysis)
        character.current_state = new_state

        # Select response strategy
        response_strategy = await self._select_response_strategy(character, context_analysis)

        # Generate response text
        response_text = await self._generate_response_text(character, response_strategy, context_analysis)

        # Generate reasoning for AI decision
        reasoning = await self._generate_ai_reasoning(character, response_strategy, context_analysis)

        return {
            'text': response_text,
            'state': new_state,
            'strategy': response_strategy,
            'reasoning': reasoning,
            'confidence': random.uniform(0.7, 0.95),
            'impact': await self._calculate_response_impact(character, response_strategy)
        }

    async def _analyze_conversation_context(self, character: AICharacter, conversation: AIConversation) -> Dict[str, Any]:
        """Analyze conversation context from AI character's perspective"""
        recent_messages = conversation.messages[-3:] if conversation.messages else []

        # Extract themes and emotional tones
        themes = []
        emotional_tone = AIState.NEUTRAL

        for msg in recent_messages:
            if msg['emotional_state'] != character.current_state:
                emotional_tone = msg['emotional_state']

            # Simple theme extraction
            if any(word in msg['text'].lower() for word in ['danger', 'threat', 'enemy']):
                themes.append('danger')
            elif any(word in msg['text'].lower() for word in ['help', 'support', 'together']):
                themes.append('cooperation')
            elif any(word in msg['text'].lower() for word in ['plan', 'strategy', 'approach']):
                themes.append('strategy')
            elif any(word in msg['text'].lower() for word in ['mystery', 'unknown', 'discover']):
                themes.append('mystery')

        return {
            'recent_messages': recent_messages,
            'themes': themes,
            'emotional_tone': emotional_tone,
            'speaker_position': conversation.messages.count({'speaker': character.name}),
            'urgency': len([m for m in recent_messages if 'danger' in m['text'].lower()]) > 0
        }

    async def _determine_emotional_state(self, character: AICharacter, context: Dict[str, Any]) -> AIState:
        """Determine AI character's emotional state based on context"""
        current_state = character.current_state
        themes = context['themes']
        emotional_tone = context['emotional_tone']
        urgency = context['urgency']

        # State transition logic based on personality and context
        if urgency and AIPersonalityTrait.BRAVE in character.personality:
            return AIState.DETERMINED
        elif 'danger' in themes and AIPersonalityTrait.CAUTIOUS in character.personality:
            return AIState.WORRIED
        elif 'cooperation' in themes and AIPersonalityTrait.GENEROUS in character.personality:
            return AIState.HAPPY
        elif 'mystery' in themes and AIPersonalityTrait.CURIOUS in character.personality:
            return AIState.EXCITED
        elif emotional_tone != AIState.NEUTRAL:
            # Adapt to emotional tone based on personality
            if emotional_tone == AIState.ANGRY and AIPersonalityTrait.DEFENSIVE in character.personality:
                return AIState.ANGRY
            elif emotional_tone == AIState.HAPPY and AIPersonalityTrait.GENEROUS in character.personality:
                return AIState.HAPPY

        # Stay in current state or transition to neutral
        return current_state if random.random() > 0.3 else AIState.NEUTRAL

    async def _select_response_strategy(self, character: AICharacter, context: Dict[str, Any]) -> str:
        """Select response strategy based on personality and context"""
        themes = context['themes']
        personality_weights = {}

        # Calculate strategy weights based on personality
        for trait in character.personality:
            if trait in self.response_patterns["response_weights"]["aggressive"]:
                personality_weights["aggressive"] = personality_weights.get("aggressive", 0) + 1
            if trait in self.response_patterns["response_weights"]["defensive"]:
                personality_weights["defensive"] = personality_weights.get("defensive", 0) + 1
            if trait in self.response_patterns["response_weights"]["diplomatic"]:
                personality_weights["diplomatic"] = personality_weights.get("diplomatic", 0) + 1
            if trait in self.response_patterns["response_weights"]["curious"]:
                personality_weights["curious"] = personality_weights.get("curious", 0) + 1

        # Adjust weights based on context
        if 'danger' in themes:
            personality_weights["aggressive"] = personality_weights.get("aggressive", 0) + 2
            personality_weights["defensive"] = personality_weights.get("defensive", 0) + 1
        elif 'cooperation' in themes:
            personality_weights["diplomatic"] = personality_weights.get("diplomatic", 0) + 2
        elif 'mystery' in themes:
            personality_weights["curious"] = personality_weights.get("curious", 0) + 2

        # Select strategy with highest weight
        if not personality_weights:
            return "neutral"

        return max(personality_weights.items(), key=lambda x: x[1])[0]

    async def _generate_response_text(self, character: AICharacter, strategy: str, context: Dict[str, Any]) -> str:
        """Generate response text based on strategy and emotional state"""
        state = character.current_state
        themes = context['themes']

        # Select appropriate dialogue template
        if state in self.dialogue_templates["emotional"]:
            base_responses = self.dialogue_templates["emotional"][state]
        elif strategy in self.dialogue_templates.get("strategic", {}):
            base_responses = self.dialogue_templates["strategic"][strategy]
        elif themes and "learning" in themes:
            base_responses = random.choice(list(self.dialogue_templates["learning"].values()))
        else:
            base_responses = self.dialogue_templates["greeting"]["friendly"]

        # Select and personalize response
        response = random.choice(base_responses)

        # Personalize with character name and context
        response = response.format(name=character.name)

        # Add personality-specific modifications
        if AIPersonalityTrait.WISE in character.personality:
            response = f"{response} Wisdom guides our path."
        elif AIPersonalityTrait.CUNNING in character.personality:
            response = f"{response} Let us be clever about this."
        elif AIPersonalityTrait.HONORABLE in character.personality:
            response = f"{response} Honor demands we act rightly."

        return response

    async def _generate_ai_reasoning(self, character: AICharacter, strategy: str, context: Dict[str, Any]) -> str:
        """Generate reasoning for AI decision-making"""
        reasons = [
            f"My {character.personality[0].value if character.personality else 'nature'} compels me to {strategy}",
            f"Based on the {context['themes'] if context['themes'] else 'current situation'}, {strategy} seems best",
            f"My goals of {', '.join(character.goals[:2])} align with {strategy}",
            f"The emotional context ({character.current_state.value)} suggests {strategy}"
        ]

        return random.choice(reasons)

    async def _calculate_response_impact(self, character: AICharacter, strategy: str) -> str:
        """Calculate the impact of AI response on conversation"""
        impact_levels = {
            "aggressive": ["high", "disruptive", "confrontational"],
            "defensive": ["medium", "protective", "cautious"],
            "diplomatic": ["high", "cooperative", "harmonizing"],
            "curious": ["medium", "engaging", "exploratory"],
            "neutral": ["low", "observational", "neutral"]
        }

        return random.choice(impact_levels.get(strategy, ["low", "neutral"]))

    async def _update_ai_character(self, character: AICharacter, response: Dict[str, Any], conversation: AIConversation):
        """Update AI character based on conversation interaction"""
        # Store memory of interaction
        memory = {
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conversation.id,
            'response': response,
            'context': conversation.context,
            'outcome': response.get('impact', 'neutral')
        }

        character.memories.append(memory)

        # Update relationships with other participants
        for participant in conversation.participants:
            if participant != character.name:
                current_value = character.relationships.get(participant, 0)
                change = random.randint(-5, 10) if response.get('impact') == 'high' else random.randint(-2, 5)
                character.relationships[participant] = max(-100, min(100, current_value + change))

        # Learning and adaptation
        character.adaptation_counter += 1
        if character.adaptation_counter % 5 == 0:
            await self._adapt_character_personality(character)

    async def _adapt_character_personality(self, character: AICharacter):
        """Adapt character personality based on experiences"""
        # Simple personality adaptation based on success patterns
        recent_memories = character.memories[-10:]
        positive_outcomes = sum(1 for m in recent_memories if m.get('outcome') in ['high', 'cooperative'])

        if positive_outcomes > 6 and random.random() > 0.7:
            # Reinforce successful personality traits
            if AIPersonalityTrait.GENEROUS not in character.personality and len(character.personality) < 5:
                character.personality.append(AIPersonalityTrait.GENEROUS)
                logger.info(f"🧠 {character.name} developed generosity through positive interactions")

    async def _analyze_ai_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze AI performance metrics"""
        if not results:
            return {'message': 'No results to analyze'}

        # Calculate metrics
        total_responses = len(results)
        unique_strategies = len(set(r['response']['strategy'] for r in results))
        emotional_range = len(set(r['response']['state'] for r in results))
        high_impact_responses = sum(1 for r in results if r['response']['impact'] in ['high', 'disruptive', 'cooperative', 'harmonizing'])
        avg_confidence = sum(r['response']['confidence'] for r in results) / total_responses

        # Extract impressive moments
        impressive_moments = []
        for r in results:
            if r['response']['confidence'] > 0.9 and r['response']['impact'] in ['high', 'cooperative', 'harmonizing']:
                impressive_moments.append({
                    'speaker': r['speaker'],
                    'response': r['response']['text'],
                    'reasoning': r['response']['reasoning']
                })

        return {
            'total_responses': total_responses,
            'unique_strategies_used': unique_strategies,
            'emotional_range_covered': emotional_range,
            'high_impact_responses': high_impact_responses,
            'average_confidence': round(avg_confidence, 3),
            'impressive_moments': impressive_moments,
            'intelligence_score': min(100, (unique_strategies * 10) + (emotional_range * 15) + (high_impact_responses * 5) + (avg_confidence * 20)),
            'demonstrated_capabilities': [
                "Emotional intelligence",
                "Strategic thinking",
                "Context adaptation",
                "Personality consistency",
                "Learning behavior"
            ]
        }

    async def run_full_ai_demonstration(self) -> Dict[str, Any]:
        """Run comprehensive AI demonstration"""
        logger.info("🚀 Starting comprehensive AI demonstration...")

        print("\n" + "="*70)
        print("🤖 AI CHARACTER INTELLIGENCE DEMONSTRATION")
        print("="*70)
        print("Showcasing advanced AI agent capabilities")
        print("🧠 Emotional Intelligence • Strategic Thinking • Learning • Adaptation")
        print("="*70)

        # Initialize characters
        await self.initialize_ai_characters()

        # Run all demonstration scenarios
        all_results = {}

        for scenario_name in self.demonstration_scenarios:
            print(f"\n🎭 Running: {self.demonstration_scenarios[scenario_name]['title']}")
            result = await self.run_demo_scenario(scenario_name)
            all_results[scenario_name] = result

            # Display key results
            analysis = result['analysis']
            print(f"  📊 Intelligence Score: {analysis['intelligence_score']}/100")
            print(f"  🎯 High Impact Responses: {analysis['high_impact_responses']}")
            print(f"  🧠 Emotional Range: {analysis['emotional_range_covered']} states")
            print(f"  ✨ Impressive Moments: {len(analysis['impressive_moments'])}")

        # Generate overall summary
        overall_summary = await self._generate_overall_summary(all_results)

        print(f"\n🎉 AI DEMONSTRATION COMPLETE")
        print(f"📈 Overall Intelligence Score: {overall_summary['average_intelligence_score']}/100")
        print(f"🎭 Total Scenarios: {len(all_results)}")
        print(f"✨ Total Impressive Moments: {overall_summary['total_impressive_moments']}")
        print(f"🧠 AI Capabilities Demonstrated: {len(overall_summary['all_capabilities'])}")

        return overall_summary

    async def _generate_overall_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall demonstration summary"""
        total_scenarios = len(all_results)
        all_scores = [r['analysis']['intelligence_score'] for r in all_results.values()]
        all_moments = sum(len(r['analysis']['impressive_moments']) for r in all_results.values())
        all_capabilities = set()

        for result in all_results.values():
            all_capabilities.update(result['analysis']['demonstrated_capabilities'])

        return {
            'total_scenarios': total_scenarios,
            'average_intelligence_score': round(sum(all_scores) / total_scenarios, 1) if all_scores else 0,
            'highest_score': max(all_scores) if all_scores else 0,
            'total_impressive_moments': all_moments,
            'all_capabilities': sorted(list(all_capabilities)),
            'scenario_results': all_results
        }