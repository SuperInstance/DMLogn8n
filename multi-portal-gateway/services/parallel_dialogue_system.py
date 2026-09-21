"""
Parallel Dialogue Generation System
Generates dialogues for hundreds of characters simultaneously
"""

import asyncio
import aiohttp
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import uuid
import json
import re
from enum import Enum
import random


class DialogueType(Enum):
    CASUAL = "casual"
    COMBAT = "combat"
    QUEST = "quest"
    TRADE = "trade"
    SOCIAL = "social"
    ROMANCE = "romance"
    INTIMIDATION = "intimidation"
    PERSUASION = "persuasion"
    LORE = "lore"
    GOSSIP = "gossip"


class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    SAD = "sad"
    EXCITED = "excited"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    PROUD = "proud"
    JEALOUS = "jealous"


class RelationshipLevel(Enum):
    STRANGER = 0
    ACQUAINTANCE = 1
    FRIEND = 2
    GOOD_FRIEND = 3
    BEST_FRIEND = 4
    LOVER = 5
    FAMILY = 6
    ENEMY = -1
    RIVAL = -2


@dataclass
class DialogueContext:
    """Context for dialogue generation"""
    speaker_id: str
    listener_id: str
    dialogue_type: DialogueType
    emotion: Emotion
    relationship_level: RelationshipLevel
    location: str
    recent_events: List[str] = field(default_factory=list)
    shared_memories: List[str] = field(default_factory=list)
    current_topic: str = ""
    personality_traits: Dict[str, float] = field(default_factory=dict)
    mood: float = 0.0  # -1 to 1
    energy: float = 1.0  # 0 to 1


@dataclass
class DialogueResponse:
    """Generated dialogue response"""
    response_id: str
    speaker_id: str
    listener_id: str
    text: str
    emotion: Emotion
    tone: str
    intent: str
    follow_up_questions: List[str] = field(default_factory=list)
    relationship_change: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationState:
    """State of an ongoing conversation"""
    conversation_id: str
    participants: List[str]
    current_speaker: int
    dialogue_history: List[DialogueResponse] = field(default_factory=list)
    context: DialogueContext = None
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True


class ParallelDialogueSystem:
    """Parallel dialogue generation system"""

    def __init__(self, max_concurrent_dialogues: int = 1000):
        self.max_concurrent_dialogues = max_concurrent_dialogues

        # Active conversations
        self.active_conversations: Dict[str, ConversationState] = {}
        self.conversation_queue = asyncio.Queue(maxsize=2000)

        # Character personalities and relationships
        self.character_personalities: Dict[str, Dict[str, float]] = {}
        self.character_relationships: Dict[str, Dict[str, RelationshipLevel]] = {}
        self.character_memories: Dict[str, List[str]] = defaultdict(list)

        # Dialogue templates and patterns
        self.dialogue_templates = self._load_dialogue_templates()
        self.emotion_patterns = self._load_emotion_patterns()
        self.topic_transitions = self._load_topic_transitions()

        # AI model connections
        self.ai_model_endpoints = {
            "fast": "http://localhost:11434/api/generate",
            "medium": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "creative": "https://api.openai.com/v1/chat/completions"
        }

        # Parallel processing pools
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        self.processing_queues = {
            DialogueType.CASUAL: asyncio.Queue(maxsize=500),
            DialogueType.COMBAT: asyncio.Queue(maxsize=200),
            DialogueType.QUEST: asyncio.Queue(maxsize=300),
            DialogueType.TRADE: asyncio.Queue(maxsize=200),
            DialogueType.SOCIAL: asyncio.Queue(maxsize=400),
            DialogueType.ROMANCE: asyncio.Queue(maxsize=100),
            DialogueType.INTIMIDATION: asyncio.Queue(maxsize=100),
            DialogueType.PERSUASION: asyncio.Queue(maxsize=200),
            DialogueType.LORE: asyncio.Queue(maxsize=200),
            DialogueType.GOSSIP: asyncio.Queue(maxsize=300)
        }

        # Background processors
        self.processors: Dict[DialogueType, asyncio.Task] = {}
        self.background_tasks: Set[asyncio.Task] = set()

        # Caching
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Metrics
        self.metrics = {
            "dialogues_generated": 0,
            "average_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "active_conversations": 0,
            "total_conversations": 0
        }

        # Performance optimization
        self.batch_size = 20
        self.processing_interval = 0.01  # 10ms

        self.is_running = False

    async def initialize(self):
        """Initialize the dialogue system"""
        logger.info(f"Initializing parallel dialogue system for {self.max_concurrent_dialogues} concurrent dialogues")

        # Start processors for each dialogue type
        for dialogue_type in DialogueType:
            processor = asyncio.create_task(
                self._dialogue_processor(dialogue_type)
            )
            self.processors[dialogue_type] = processor
            self.background_tasks.add(processor)

        # Start conversation manager
        task = asyncio.create_task(self._conversation_manager())
        self.background_tasks.add(task)

        # Start memory consolidation
        task = asyncio.create_task(self._memory_consolidation())
        self.background_tasks.add(task)

        # Start metrics collector
        task = asyncio.create_task(self._metrics_collector())
        self.background_tasks.add(task)

        # Start cache cleanup
        task = asyncio.create_task(self._cache_cleanup())
        self.background_tasks.add(task)

        self.is_running = True
        logger.info("Parallel dialogue system initialized")

    async def start_conversation(self,
                                participants: List[str],
                                dialogue_type: DialogueType,
                                location: str,
                                initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Start a new conversation"""
        conversation_id = str(uuid.uuid4())

        # Ensure all participants have personalities
        for participant in participants:
            if participant not in self.character_personalities:
                await self._generate_personality(participant)

        # Create conversation state
        conversation = ConversationState(
            conversation_id=conversation_id,
            participants=participants,
            current_speaker=0,
            context=DialogueContext(
                speaker_id=participants[0],
                listener_id=participants[1] if len(participants) > 1 else participants[0],
                dialogue_type=dialogue_type,
                emotion=Emotion.NEUTRAL,
                relationship_level=self._get_relationship_level(participants[0], participants[1] if len(participants) > 1 else participants[0]),
                location=location,
                personality_traits=self.character_personalities[participants[0]]
            )
        )

        self.active_conversations[conversation_id] = conversation
        self.metrics["total_conversations"] += 1

        # Add to processing queue
        await self.processing_queues[dialogue_type].put({
            "conversation_id": conversation_id,
            "action": "generate_response",
            "context": initial_context or {}
        })

        return conversation_id

    async def add_dialogue_input(self,
                                conversation_id: str,
                                speaker_id: str,
                                text: str,
                                emotion: Optional[Emotion] = None) -> Optional[DialogueResponse]:
        """Add input to an ongoing conversation"""
        conversation = self.active_conversations.get(conversation_id)
        if not conversation or not conversation.is_active:
            return None

        # Update conversation state
        conversation.last_activity = datetime.now()

        # Update context
        if emotion:
            conversation.context.emotion = emotion

        # Generate response
        await self.processing_queues[conversation.context.dialogue_type].put({
            "conversation_id": conversation_id,
            "action": "generate_response",
            "input": {
                "speaker_id": speaker_id,
                "text": text,
                "emotion": emotion
            }
        })

        return None

    async def _dialogue_processor(self, dialogue_type: DialogueType):
        """Process dialogues of a specific type in parallel"""
        while self.is_running:
            try:
                # Get batch of requests
                requests_batch = []
                queue = self.processing_queues[dialogue_type]

                for _ in range(min(self.batch_size, queue.qsize())):
                    if not queue.empty():
                        request = await queue.get()
                        requests_batch.append(request)

                if requests_batch:
                    # Process requests in parallel
                    results = await asyncio.gather(
                        *[self._process_dialogue_request(request, dialogue_type) for request in requests_batch],
                        return_exceptions=True
                    )

                    # Handle results
                    for request, result in zip(requests_batch, results):
                        if isinstance(result, Exception):
                            logger.error(f"Dialogue processing error: {result}")
                        else:
                            await self._handle_dialogue_result(request, result)

                await asyncio.sleep(self.processing_interval)

            except Exception as e:
                logger.error(f"Dialogue processor error for {dialogue_type}: {e}")
                await asyncio.sleep(self.processing_interval)

    async def _process_dialogue_request(self,
                                       request: Dict[str, Any],
                                       dialogue_type: DialogueType) -> Optional[DialogueResponse]:
        """Process individual dialogue request"""
        start_time = datetime.now()

        conversation_id = request.get("conversation_id")
        action = request.get("action")

        if action == "generate_response":
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                return None

            # Generate response based on complexity
            if dialogue_type in [DialogueType.CASUAL, DialogueType.GOSSIP, DialogueType.SOCIAL]:
                response = await self._generate_fast_response(conversation)
            elif dialogue_type in [DialogueType.QUEST, DialogueType.LORE, DialogueType.TRADE]:
                response = await self._generate_medium_response(conversation)
            else:
                response = await self._generate_complex_response(conversation)

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(processing_time)

            return response

        return None

    async def _generate_fast_response(self, conversation: ConversationState) -> DialogueResponse:
        """Generate fast response using templates"""
        context = conversation.context
        speaker = context.speaker_id
        listener = context.listener_id

        # Get template based on dialogue type and emotion
        templates = self.dialogue_templates.get(context.dialogue_type, {}).get(context.emotion, [])

        if templates:
            template = random.choice(templates)

            # Fill template with context
            text = template.format(
                speaker_name=self._get_character_name(speaker),
                listener_name=self._get_character_name(listener),
                location=context.location,
                topic=context.current_topic or "the weather"
            )
        else:
            # Fallback response
            text = f"*{self._get_character_name(speaker)} nods thoughtfully*"

        # Adjust based on personality
        text = self._apply_personality(text, context.personality_traits)

        response = DialogueResponse(
            response_id=str(uuid.uuid4()),
            speaker_id=speaker,
            listener_id=listener,
            text=text,
            emotion=context.emotion,
            tone=self._determine_tone(context.emotion, context.personality_traits),
            intent=self._determine_intent(context.dialogue_type),
            generated_at=datetime.now()
        )

        return response

    async def _generate_medium_response(self, conversation: ConversationState) -> DialogueResponse:
        """Generate medium complexity response using AI"""
        context = conversation.context

        # Build prompt
        prompt = self._build_dialogue_prompt(conversation, complexity="medium")

        # Call AI model
        response_text = await self._call_ai_model(prompt, model="medium")

        # Parse response
        text, emotion, intent = self._parse_ai_response(response_text)

        response = DialogueResponse(
            response_id=str(uuid.uuid4()),
            speaker_id=context.speaker_id,
            listener_id=context.listener_id,
            text=text,
            emotion=emotion or context.emotion,
            tone=self._determine_tone(emotion or context.emotion, context.personality_traits),
            intent=intent or self._determine_intent(context.dialogue_type),
            generated_at=datetime.now()
        )

        return response

    async def _generate_complex_response(self, conversation: ConversationState) -> DialogueResponse:
        """Generate complex response using advanced AI"""
        context = conversation.context

        # Build detailed prompt
        prompt = self._build_dialogue_prompt(conversation, complexity="complex")

        # Call advanced AI model
        response_text = await self._call_ai_model(prompt, model="creative")

        # Parse complex response
        parsed = self._parse_complex_ai_response(response_text)

        response = DialogueResponse(
            response_id=str(uuid.uuid4()),
            speaker_id=context.speaker_id,
            listener_id=context.listener_id,
            text=parsed.get("text", ""),
            emotion=parsed.get("emotion", context.emotion),
            tone=parsed.get("tone", "neutral"),
            intent=parsed.get("intent", self._determine_intent(context.dialogue_type)),
            follow_up_questions=parsed.get("follow_up_questions", []),
            relationship_change=parsed.get("relationship_change", 0.0),
            metadata=parsed.get("metadata", {}),
            generated_at=datetime.now()
        )

        return response

    async def _call_ai_model(self, prompt: str, model: str = "medium") -> str:
        """Call AI model for dialogue generation"""
        # Check cache first
        cache_key = hash(prompt + model)
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_ttl):
                self.metrics["cache_hits"] += 1
                return cached["response"]

        self.metrics["cache_misses"] += 1

        try:
            if model == "fast":
                # Use local model for fast responses
                response = await self._call_local_model(prompt)
            elif model == "medium":
                # Use GLM-4 for medium responses
                response = await self._call_glm4_model(prompt)
            else:
                # Use OpenAI/Anthropic for complex responses
                response = await self._call_advanced_model(prompt)

            # Cache response
            self.response_cache[cache_key] = {
                "response": response,
                "timestamp": datetime.now()
            }

            return response

        except Exception as e:
            logger.error(f"AI model call error: {e}")
            # Return fallback response
            return "I need a moment to think about that."

    async def _call_local_model(self, prompt: str) -> str:
        """Call local model for fast generation"""
        # Simulate local model call
        await asyncio.sleep(0.05)
        return "That's interesting! Tell me more."

    async def _call_glm4_model(self, prompt: str) -> str:
        """Call GLM-4 model"""
        # This would integrate with actual GLM-4 API
        # For now, simulate
        await asyncio.sleep(0.2)
        return "I understand your perspective. Let me consider that carefully."

    async def _call_advanced_model(self, prompt: str) -> str:
        """Call advanced AI model"""
        # This would integrate with OpenAI/Anthropic
        # For now, simulate
        await asyncio.sleep(0.5)
        return "That's a profound point. It reminds me of something that happened long ago..."

    def _build_dialogue_prompt(self, conversation: ConversationState, complexity: str) -> str:
        """Build prompt for AI dialogue generation"""
        context = conversation.context

        base_prompt = f"""
You are {context.speaker_id}, speaking with {context.listener_id} in {context.location}.
Dialogue type: {context.dialogue_type.value}
Current emotion: {context.emotion.value}
Relationship level: {context.relationship_level.name}
Current mood: {context.mood:.2f}

Personality traits:
{json.dumps(context.personality_traits, indent=2)}

"""

        if complexity == "complex":
            base_prompt += f"""
Recent dialogue history:
{self._format_dialogue_history(conversation.dialogue_history[-5:])}

Shared memories:
{chr(10).join(context.shared_memories[-3:])}

Recent events:
{chr(10).join(context.recent_events[-3:])}

"""

        base_prompt += f"""
Generate a response that:
1. Matches the character's personality
2. Reflects the current emotion
3. Considers the relationship level
4. Is appropriate for {context.dialogue_type.value} dialogue
5. Feels natural and engaging

Response:
"""

        return base_prompt

    def _format_dialogue_history(self, history: List[DialogueResponse]) -> str:
        """Format dialogue history for prompt"""
        if not history:
            return "No previous dialogue."

        formatted = []
        for response in history[-5:]:
            formatted.append(f"{response.speaker_id}: {response.text}")

        return "\n".join(formatted)

    def _parse_ai_response(self, response: str) -> Tuple[str, Emotion, str]:
        """Parse AI response into components"""
        # Simple parsing - in production would use structured output
        lines = response.strip().split('\n')

        text = lines[0] if lines else "..."
        emotion = self._detect_emotion(text)
        intent = "converse"

        return text, emotion, intent

    def _parse_complex_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse complex AI response"""
        # Would parse structured JSON in production
        return {
            "text": response.strip(),
            "emotion": Emotion.NEUTRAL,
            "tone": "neutral",
            "intent": "converse",
            "follow_up_questions": [],
            "relationship_change": 0.0,
            "metadata": {}
        }

    def _detect_emotion(self, text: str) -> Emotion:
        """Detect emotion from text"""
        text_lower = text.lower()

        emotion_keywords = {
            Emotion.HAPPY: ["happy", "glad", "joy", "wonderful", "great", "smile", "laugh"],
            Emotion.ANGRY: ["angry", "mad", "furious", "annoyed", "irritated", "rage"],
            Emotion.SAD: ["sad", "cry", "tears", "unhappy", "depressed", "sorrow"],
            Emotion.EXCITED: ["excited", "thrilled", "amazing", "wow", "incredible"],
            Emotion.FEARFUL: ["scared", "afraid", "fear", "terrified", "worried"],
            Emotion.SURPRISED: ["surprised", "shocked", "unexpected", "wow", "really"]
        }

        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion

        return Emotion.NEUTRAL

    def _apply_personality(self, text: str, traits: Dict[str, float]) -> str:
        """Apply personality traits to dialogue"""
        # Modify text based on traits
        if traits.get("openness", 0.5) > 0.7:
            # More expressive
            text = text.replace(".", "!") if random.random() < 0.3 else text

        if traits.get("agreeableness", 0.5) > 0.7:
            # More agreeable language
            if not any(polite in text.lower() for polite in ["please", "thank", "kindly"]):
                text = text.replace("you", "you kindly") if random.random() < 0.2 else text

        return text

    def _determine_tone(self, emotion: Emotion, traits: Dict[str, float]) -> str:
        """Determine dialogue tone"""
        tone_map = {
            Emotion.HAPPY: "cheerful",
            Emotion.ANGRY: "hostile",
            Emotion.SAD: "somber",
            Emotion.EXCITED: "enthusiastic",
            Emotion.FEARFUL: "nervous",
            Emotion.NEUTRAL: "neutral"
        }

        base_tone = tone_map.get(emotion, "neutral")

        # Adjust based on traits
        if traits.get("conscientiousness", 0.5) > 0.7:
            base_tone = "formal " + base_tone
        elif traits.get("extraversion", 0.5) > 0.7:
            base_tone = "friendly " + base_tone

        return base_tone

    def _determine_intent(self, dialogue_type: DialogueType) -> str:
        """Determine dialogue intent"""
        intent_map = {
            DialogueType.CASUAL: "chat",
            DialogueType.COMBAT: "taunt",
            DialogueType.QUEST: "inform",
            DialogueType.TRADE: "negotiate",
            DialogueType.SOCIAL: "interact",
            DialogueType.ROMANCE: "flirt",
            DialogueType.INTIMIDATION: "threaten",
            DialogueType.PERSUASION: "convince",
            DialogueType.LORE: "explain",
            DialogueType.GOSSIP: "share"
        }

        return intent_map.get(dialogue_type, "chat")

    async def _handle_dialogue_result(self, request: Dict[str, Any], response: DialogueResponse):
        """Handle generated dialogue response"""
        conversation_id = request.get("conversation_id")
        conversation = self.active_conversations.get(conversation_id)

        if not conversation:
            return

        # Add to dialogue history
        conversation.dialogue_history.append(response)

        # Update context
        conversation.context.speaker_id, conversation.context.listener_id = \
            conversation.context.listener_id, conversation.context.speaker_id

        # Update relationship if needed
        if response.relationship_change != 0:
            await self._update_relationship(
                conversation.context.listener_id,
                conversation.context.speaker_id,
                response.relationship_change
            )

        # Store memory
        await self._store_dialogue_memory(response)

        # Update metrics
        self.metrics["dialogues_generated"] += 1

    async def _conversation_manager(self):
        """Manage active conversations"""
        while self.is_running:
            try:
                # Check for inactive conversations
                now = datetime.now()
                inactive_threshold = timedelta(minutes=5)

                inactive_conversations = [
                    conv_id for conv_id, conv in self.active_conversations.items()
                    if now - conv.last_activity > inactive_threshold
                ]

                for conv_id in inactive_conversations:
                    await self._end_conversation(conv_id)

                # Update metrics
                self.metrics["active_conversations"] = len(self.active_conversations)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Conversation manager error: {e}")
                await asyncio.sleep(30)

    async def _memory_consolidation(self):
        """Consolidate dialogue memories"""
        while self.is_running:
            try:
                # Process recent dialogues for memory consolidation
                all_recent_responses = []
                for conv in self.active_conversations.values():
                    all_recent_responses.extend(conv.dialogue_history[-10:])

                # Consolidate in parallel
                await asyncio.gather(
                    *[self._consolidate_response_memory(response) for response in all_recent_responses[-100:]],
                    return_exceptions=True
                )

                await asyncio.sleep(60)  # Consolidate every minute

            except Exception as e:
                logger.error(f"Memory consolidation error: {e}")
                await asyncio.sleep(60)

    async def _consolidate_response_memory(self, response: DialogueResponse):
        """Consolidate single response into memory"""
        # Extract key information
        memory_text = f"{response.speaker_id} said: {response.text[:100]}"

        # Store for both speaker and listener
        self.character_memories[response.speaker_id].append(memory_text)
        self.character_memories[response.listener_id].append(memory_text)

        # Keep only recent memories
        max_memories = 1000
        if len(self.character_memories[response.speaker_id]) > max_memories:
            self.character_memories[response.speaker_id] = self.character_memories[response.speaker_id][-max_memories:]

        if len(self.character_memories[response.listener_id]) > max_memories:
            self.character_memories[response.listener_id] = self.character_memories[response.listener_id][-max_memories:]

    async def _end_conversation(self, conversation_id: str):
        """End a conversation"""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]
            conversation.is_active = False

            # Archive conversation
            # In production, would save to database

            del self.active_conversations[conversation_id]

    async def _generate_personality(self, character_id: str):
        """Generate personality for character"""
        # Big Five personality traits
        personality = {
            "openness": random.uniform(0, 1),
            "conscientiousness": random.uniform(0, 1),
            "extraversion": random.uniform(0, 1),
            "agreeableness": random.uniform(0, 1),
            "neuroticism": random.uniform(0, 1)
        }

        self.character_personalities[character_id] = personality

    def _get_relationship_level(self, char1: str, char2: str) -> RelationshipLevel:
        """Get relationship level between two characters"""
        return self.character_relationships.get(char1, {}).get(char2, RelationshipLevel.STRANGER)

    async def _update_relationship(self, char1: str, char2: str, change: float):
        """Update relationship level"""
        current_level = self._get_relationship_level(char1, char2)
        new_value = current_level.value + change

        # Convert back to enum
        if new_value <= -2:
            new_level = RelationshipLevel.RIVAL
        elif new_value <= -1:
            new_level = RelationshipLevel.ENEMY
        elif new_value <= 0:
            new_level = RelationshipLevel.STRANGER
        elif new_value <= 1:
            new_level = RelationshipLevel.ACQUAINTANCE
        elif new_value <= 2:
            new_level = RelationshipLevel.FRIEND
        elif new_value <= 3:
            new_level = RelationshipLevel.GOOD_FRIEND
        elif new_value <= 4:
            new_level = RelationshipLevel.BEST_FRIEND
        else:
            new_level = RelationshipLevel.LOVER

        # Update both directions
        self.character_relationships.setdefault(char1, {})[char2] = new_level
        self.character_relationships.setdefault(char2, {})[char1] = new_level

    async def _store_dialogue_memory(self, response: DialogueResponse):
        """Store dialogue in character memory"""
        memory_key = f"{response.speaker_id}_{response.listener_id}"

        # Store shared memory
        if memory_key not in self.character_memories:
            self.character_memories[memory_key] = []

        self.character_memories[memory_key].append(response.text[:200])

    def _get_character_name(self, character_id: str) -> str:
        """Get display name for character"""
        # In production, would look up from database
        return character_id.split('_')[0] if '_' in character_id else character_id

    def _update_metrics(self, processing_time: float):
        """Update performance metrics"""
        # Update average response time
        total = self.metrics["average_response_time"] * (self.metrics["dialogues_generated"] - 1)
        self.metrics["average_response_time"] = (total + processing_time) / self.metrics["dialogues_generated"]

    async def _metrics_collector(self):
        """Collect system metrics"""
        while self.is_running:
            try:
                # Log current metrics
                logger.info(f"Dialogue metrics: {self.metrics}")

                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)

    async def _cache_cleanup(self):
        """Clean up expired cache entries"""
        while self.is_running:
            try:
                now = datetime.now()
                expired_keys = []

                for key, value in self.response_cache.items():
                    if now - value["timestamp"] > timedelta(seconds=self.cache_ttl):
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.response_cache[key]

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)

    def _load_dialogue_templates(self) -> Dict[DialogueType, Dict[Emotion, List[str]]]:
        """Load dialogue templates"""
        templates = {
            DialogueType.CASUAL: {
                Emotion.HAPPY: [
                    "It's a beautiful day in {location}, isn't it?",
                    "I'm so glad to see you!",
                    "Things have been going really well lately."
                ],
                Emotion.NEUTRAL: [
                    "How are you doing today?",
                    "Nice weather we're having.",
                    "What's on your mind?"
                ]
            },
            DialogueType.GOSSIP: {
                Emotion.EXCITED: [
                    "You won't believe what I heard!",
                    "I have to tell you something interesting.",
                    "There's been quite a bit of talk about {topic}."
                ]
            }
        }

        return templates

    def _load_emotion_patterns(self) -> Dict[Emotion, List[str]]:
        """Load emotion patterns"""
        return {
            Emotion.HAPPY: ["smile", "laugh", "bright", "wonderful"],
            Emotion.ANGRY: ["frown", "glare", "angry", "frustrated"],
            Emotion.SAD: ["sigh", "tear", "sad", "unhappy"]
        }

    def _load_topic_transitions(self) -> Dict[str, List[str]]:
        """Load topic transitions"""
        return {
            "weather": ["travel", "crops", "local events"],
            "travel": ["danger", "merchants", "distant lands"],
            "local events": ["people", "rumors", "opportunities"]
        }

    async def get_conversation_history(self, conversation_id: str) -> List[DialogueResponse]:
        """Get conversation history"""
        conversation = self.active_conversations.get(conversation_id)
        return conversation.dialogue_history if conversation else []

    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self.metrics.copy()

    async def shutdown(self):
        """Shutdown the dialogue system"""
        logger.info("Shutting down parallel dialogue system")

        self.is_running = False

        # Cancel all processors
        for processor in self.processors.values():
            processor.cancel()

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        all_tasks = list(self.processors.values()) + list(self.background_tasks)
        await asyncio.gather(*all_tasks, return_exceptions=True)

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        logger.info("Parallel dialogue system shutdown complete")


# Test function
async def test_dialogue_system():
    """Test the dialogue system"""
    system = ParallelDialogueSystem(max_concurrent_dialogues=100)
    await system.initialize()

    # Start multiple conversations
    conversations = []
    for i in range(10):
        conv_id = await system.start_conversation(
            participants=[f"npc_{i}", f"player"],
            dialogue_type=DialogueType.CASUAL,
            location="tavern"
        )
        conversations.append(conv_id)

    # Add some dialogue inputs
    for conv_id in conversations[:5]:
        await system.add_dialogue_input(
            conv_id,
            f"player",
            "Hello there! How are you?"
        )

    # Wait for processing
    await asyncio.sleep(2)

    # Get metrics
    metrics = await system.get_metrics()
    print(f"Generated {metrics['dialogues_generated']} dialogues")
    print(f"Average response time: {metrics['average_response_time']:.3f}s")

    await system.shutdown()


if __name__ == "__main__":
    asyncio.run(test_dialogue_system())