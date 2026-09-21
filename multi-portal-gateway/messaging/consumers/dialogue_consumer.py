#!/usr/bin/env python3
"""
Dialogue Consumer - Handles dialogue system message consumption.

This consumer processes dialogue-related messages including:
- Dialogue events and updates
- NPC conversations
- Player dialogue choices
- Dialogue state changes
- Voice line triggers
- Story progression events
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

from ..message_broker import (
    Message, MessageType, MessagePriority, MessageBroker,
    QueueConfig, ExchangeConfig, ConsumerConfig
)

logger = logging.getLogger(__name__)


class DialogueEventType(Enum):
    """Dialogue event types."""
    DIALOGUE_START = "dialogue_start"
    DIALOGUE_END = "dialogue_end"
    DIALOGUE_CHOICE = "dialogue_choice"
    DIALOGUE_RESPONSE = "dialogue_response"
    NPC_SPEAK = "npc_speak"
    PLAYER_SPEAK = "player_speak"
    VOICE_LINE_TRIGGER = "voice_line_trigger"
    DIALOGUE_STATE_CHANGE = "dialogue_state_change"
    RELATIONSHIP_CHANGE = "relationship_change"
    STORY_PROGRESSION = "story_progression"
    CONDITION_CHECK = "condition_check"
    QUEST_DIALOGUE = "quest_dialogue"


class DialogueState(Enum):
    """Dialogue state types."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_FOR_CHOICE = "waiting_for_choice"
    PROCESSING_CHOICE = "processing_choice"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


@dataclass
class DialogueNode:
    """Dialogue node structure."""
    node_id: str
    speaker_id: str
    text: str
    choices: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    voice_line_id: Optional[str] = None
    animation_id: Optional[str] = None
    emotion: Optional[str] = None
    next_nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueSession:
    """Dialogue session structure."""
    session_id: str
    participants: List[str] = field(default_factory=list)
    current_node_id: Optional[str] = None
    state: DialogueState = DialogueState.INACTIVE
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    timeout: float = 300.0  # 5 minutes default timeout


@dataclass
class DialogueEvent:
    """Dialogue event structure."""
    event_id: str
    event_type: DialogueEventType
    session_id: str
    speaker_id: Optional[str] = None
    listener_id: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogueConsumer:
    """
    Consumer for dialogue system messages.
    """

    def __init__(self, message_broker: MessageBroker, instance_id: str):
        self.broker = message_broker
        self.instance_id = instance_id
        self.active_sessions: Dict[str, DialogueSession] = {}
        self.dialogue_nodes: Dict[str, DialogueNode] = {}
        self.event_handlers: Dict[DialogueEventType, Callable] = {}
        self.state_handlers: Dict[DialogueState, Callable] = {}
        self.consuming = False
        self.consumer_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_received': 0,
            'events_processed': 0,
            'sessions_created': 0,
            'sessions_completed': 0,
            'dialogue_nodes_processed': 0,
            'choices_processed': 0,
            'errors': 0
        }

    async def initialize(self):
        """Initialize the dialogue consumer."""
        try:
            # Setup dialogue-specific queues
            await self._setup_queues()

            # Register default handlers
            self._register_default_handlers()

            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info(f"Initialized dialogue consumer for instance {self.instance_id}")

        except Exception as e:
            logger.error(f"Failed to initialize dialogue consumer: {str(e)}")
            raise

    async def _setup_queues(self):
        """Setup dialogue consumer queues."""
        try:
            # Dialogue events queue
            events_queue = QueueConfig(
                name=f"dialogue.{self.instance_id}.events",
                durable=True,
                arguments={
                    "x-message-ttl": 600000,  # 10 minutes TTL
                    "x-max-length": 5000      # Max 5000 events
                }
            )
            await self.broker.declare_queue(events_queue)

            # Dialogue session queue
            session_queue = QueueConfig(
                name=f"dialogue.{self.instance_id}.sessions",
                durable=True,
                arguments={
                    "x-message-ttl": 3600000,  # 1 hour TTL
                    "x-max-length": 1000       # Max 1000 sessions
                }
            )
            await self.broker.declare_queue(session_queue)

            # Voice line queue
            voice_queue = QueueConfig(
                name=f"dialogue.{self.instance_id}.voice",
                durable=True,
                arguments={
                    "x-message-ttl": 1800000   # 30 minutes TTL
                }
            )
            await self.broker.declare_queue(voice_queue)

            # Bind queues to dialogue exchange
            dialogue_exchange = "dialogue.exchange"
            await self.broker.bind_queue(events_queue.name, dialogue_exchange, "dialogue.event.#")
            await self.broker.bind_queue(session_queue.name, dialogue_exchange, "dialogue.session.#")
            await self.broker.bind_queue(voice_queue.name, dialogue_exchange, "dialogue.voice.#")

        except Exception as e:
            logger.error(f"Failed to setup dialogue queues: {str(e)}")
            raise

    def _register_default_handlers(self):
        """Register default event handlers."""
        self.event_handlers[DialogueEventType.DIALOGUE_START] = self._handle_dialogue_start
        self.event_handlers[DialogueEventType.DIALOGUE_END] = self._handle_dialogue_end
        self.event_handlers[DialogueEventType.DIALOGUE_CHOICE] = self._handle_dialogue_choice
        self.event_handlers[DialogueEventType.DIALOGUE_RESPONSE] = self._handle_dialogue_response
        self.event_handlers[DialogueEventType.NPC_SPEAK] = self._handle_npc_speak
        self.event_handlers[DialogueEventType.PLAYER_SPEAK] = self._handle_player_speak
        self.event_handlers[DialogueEventType.VOICE_LINE_TRIGGER] = self._handle_voice_line_trigger
        self.event_handlers[DialogueEventType.DIALOGUE_STATE_CHANGE] = self._handle_dialogue_state_change
        self.event_handlers[DialogueEventType.RELATIONSHIP_CHANGE] = self._handle_relationship_change
        self.event_handlers[DialogueEventType.STORY_PROGRESSION] = self._handle_story_progression
        self.event_handlers[DialogueEventType.CONDITION_CHECK] = self._handle_condition_check
        self.event_handlers[DialogueEventType.QUEST_DIALOGUE] = self._handle_quest_dialogue

        # Register state handlers
        self.state_handlers[DialogueState.WAITING_FOR_CHOICE] = self._handle_waiting_for_choice
        self.state_handlers[DialogueState.PROCESSING_CHOICE] = self._handle_processing_choice

    async def start_consuming(self):
        """Start consuming dialogue messages."""
        if self.consuming:
            logger.warning(f"Dialogue consumer {self.instance_id} is already consuming")
            return

        try:
            self.consuming = True

            # Start consumer task
            self.consumer_task = asyncio.create_task(self._consume_loop())

            logger.info(f"Dialogue consumer {self.instance_id} started consuming messages")

        except Exception as e:
            logger.error(f"Failed to start dialogue consumption: {str(e)}")
            self.consuming = False
            raise

    async def stop_consuming(self):
        """Stop consuming dialogue messages."""
        if not self.consuming:
            return

        try:
            self.consuming = False

            if self.consumer_task:
                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    pass

            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            logger.info(f"Dialogue consumer {self.instance_id} stopped consuming messages")

        except Exception as e:
            logger.error(f"Error stopping dialogue consumption: {str(e)}")

    async def _consume_loop(self):
        """Main consumption loop."""
        while self.consuming:
            try:
                # Create consumer config for events
                consumer_config = ConsumerConfig(
                    queue=f"dialogue.{self.instance_id}.events",
                    prefetch_count=20,
                    auto_ack=False,
                    consumer_tag=f"dialogue_{self.instance_id}_consumer"
                )

                # Start consuming
                await self.broker.consume(consumer_config, self._handle_message)

                # Keep the loop running
                while self.consuming:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in dialogue consume loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _handle_message(self, message: Message):
        """Handle incoming dialogue message."""
        try:
            self.stats['events_received'] += 1

            # Parse dialogue event from payload
            payload = message.payload
            if "event" not in payload:
                logger.warning(f"Message {message.id} missing event in payload")
                await self.broker.ack_message(message.delivery_tag)
                return

            event_data = payload["event"]
            event = DialogueEvent(**event_data)

            # Call appropriate event handler
            if event.event_type in self.event_handlers:
                handler = self.event_handlers[event.event_type]
                await handler(event, message)

            else:
                logger.warning(f"No handler for dialogue event type: {event.event_type.value}")

            self.stats['events_processed'] += 1
            await self.broker.ack_message(message.delivery_tag)

        except Exception as e:
            logger.error(f"Error handling dialogue message {message.id}: {str(e)}")
            self.stats['errors'] += 1
            await self.broker.ack_message(message.delivery_tag)  # Ack to prevent reprocessing

    async def _handle_dialogue_start(self, event: DialogueEvent, broker_message: Message):
        """Handle dialogue start event."""
        try:
            logger.debug(f"Starting dialogue session {event.session_id}")

            content = event.content
            session_id = event.session_id
            participants = content.get("participants", [])
            initial_node_id = content.get("initial_node_id")
            context = content.get("context", {})

            # Create dialogue session
            session = DialogueSession(
                session_id=session_id,
                participants=participants,
                current_node_id=initial_node_id,
                state=DialogueState.ACTIVE,
                context=context
            )

            self.active_sessions[session_id] = session
            self.stats['sessions_created'] += 1

            # Process initial node if provided
            if initial_node_id and initial_node_id in self.dialogue_nodes:
                await self._process_dialogue_node(session_id, initial_node_id)

            logger.info(f"Started dialogue session {session_id} with participants: {participants}")

        except Exception as e:
            logger.error(f"Error handling dialogue start: {str(e)}")

    async def _handle_dialogue_end(self, event: DialogueEvent, broker_message: Message):
        """Handle dialogue end event."""
        try:
            session_id = event.session_id

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.state = DialogueState.COMPLETED

                # Update session history
                session.history.append({
                    "event_type": DialogueEventType.DIALOGUE_END.value,
                    "timestamp": event.timestamp,
                    "content": event.content
                })

                # Remove from active sessions
                del self.active_sessions[session_id]
                self.stats['sessions_completed'] += 1

                logger.info(f"Completed dialogue session {session_id}")

        except Exception as e:
            logger.error(f"Error handling dialogue end: {str(e)}")

    async def _handle_dialogue_choice(self, event: DialogueEvent, broker_message: Message):
        """Handle dialogue choice event."""
        try:
            session_id = event.session_id

            if session_id not in self.active_sessions:
                logger.warning(f"Dialogue choice for non-existent session {session_id}")
                return

            session = self.active_sessions[session_id]
            content = event.content
            choice_index = content.get("choice_index")
            choice_data = content.get("choice_data", {})

            # Update session history
            session.history.append({
                "event_type": DialogueEventType.DIALOGUE_CHOICE.value,
                "timestamp": event.timestamp,
                "choice_index": choice_index,
                "choice_data": choice_data
            })

            # Update session state
            session.state = DialogueState.PROCESSING_CHOICE
            session.last_activity = event.timestamp

            # Process the choice
            await self._process_dialogue_choice(session_id, choice_index, choice_data)

            self.stats['choices_processed'] += 1

        except Exception as e:
            logger.error(f"Error handling dialogue choice: {str(e)}")

    async def _handle_dialogue_response(self, event: DialogueEvent, broker_message: Message):
        """Handle dialogue response event."""
        try:
            session_id = event.session_id

            if session_id not in self.active_sessions:
                logger.warning(f"Dialogue response for non-existent session {session_id}")
                return

            session = self.active_sessions[session_id]
            content = event.content
            response_text = content.get("response_text", "")
            next_node_id = content.get("next_node_id")

            # Update session history
            session.history.append({
                "event_type": DialogueEventType.DIALOGUE_RESPONSE.value,
                "timestamp": event.timestamp,
                "response_text": response_text,
                "next_node_id": next_node_id
            })

            # Process next node if provided
            if next_node_id and next_node_id in self.dialogue_nodes:
                await self._process_dialogue_node(session_id, next_node_id)

        except Exception as e:
            logger.error(f"Error handling dialogue response: {str(e)}")

    async def _handle_npc_speak(self, event: DialogueEvent, broker_message: Message):
        """Handle NPC speak event."""
        try:
            content = event.content
            npc_id = event.speaker_id
            dialogue_text = content.get("text", "")
            emotion = content.get("emotion")
            voice_line_id = content.get("voice_line_id")

            logger.debug(f"NPC {npc_id} speaking: {dialogue_text[:50]}...")

            # Trigger voice line if specified
            if voice_line_id:
                await self._trigger_voice_line(voice_line_id, npc_id, emotion)

            # Update any active dialogue sessions
            await self._update_sessions_with_npc_speech(event)

        except Exception as e:
            logger.error(f"Error handling NPC speak: {str(e)}")

    async def _handle_player_speak(self, event: DialogueEvent, broker_message: Message):
        """Handle player speak event."""
        try:
            content = event.content
            player_id = event.speaker_id
            dialogue_text = content.get("text", "")

            logger.debug(f"Player {player_id} speaking: {dialogue_text[:50]}...")

            # Update any active dialogue sessions
            await self._update_sessions_with_player_speech(event)

        except Exception as e:
            logger.error(f"Error handling player speak: {str(e)}")

    async def _handle_voice_line_trigger(self, event: DialogueEvent, broker_message: Message):
        """Handle voice line trigger event."""
        try:
            content = event.content
            voice_line_id = content.get("voice_line_id")
            character_id = content.get("character_id")
            emotion = content.get("emotion")

            await self._trigger_voice_line(voice_line_id, character_id, emotion)

        except Exception as e:
            logger.error(f"Error handling voice line trigger: {str(e)}")

    async def _handle_dialogue_state_change(self, event: DialogueEvent, broker_message: Message):
        """Handle dialogue state change event."""
        try:
            session_id = event.session_id

            if session_id not in self.active_sessions:
                logger.warning(f"State change for non-existent session {session_id}")
                return

            session = self.active_sessions[session_id]
            content = event.content
            new_state = DialogueState(content.get("new_state", DialogueState.INACTIVE.value))

            old_state = session.state
            session.state = new_state
            session.last_activity = event.timestamp

            # Update session history
            session.history.append({
                "event_type": DialogueEventType.DIALOGUE_STATE_CHANGE.value,
                "timestamp": event.timestamp,
                "old_state": old_state.value,
                "new_state": new_state.value
            })

            logger.debug(f"Dialogue session {session_id} state changed: {old_state.value} -> {new_state.value}")

            # Call state handler if exists
            if new_state in self.state_handlers:
                handler = self.state_handlers[new_state]
                await handler(session, event)

        except Exception as e:
            logger.error(f"Error handling dialogue state change: {str(e)}")

    async def _handle_relationship_change(self, event: DialogueEvent, broker_message: Message):
        """Handle relationship change event."""
        try:
            content = event.content
            character_id = content.get("character_id")
            player_id = content.get("player_id")
            relationship_change = content.get("relationship_change", 0)
            new_relationship_level = content.get("new_relationship_level")

            logger.info(f"Relationship change: {character_id} -> {player_id}: {relationship_change}")

            # Update dialogue context for active sessions
            for session in self.active_sessions.values():
                if player_id in session.participants or character_id in session.participants:
                    relationship_key = f"relationship_{character_id}_{player_id}"
                    session.context[relationship_key] = new_relationship_level

        except Exception as e:
            logger.error(f"Error handling relationship change: {str(e)}")

    async def _handle_story_progression(self, event: DialogueEvent, broker_message: Message):
        """Handle story progression event."""
        try:
            content = event.content
            story_point = content.get("story_point")
            chapter = content.get("chapter")
            progress_data = content.get("progress_data", {})

            logger.info(f"Story progression: {story_point} (Chapter {chapter})")

            # Update dialogue context for all active sessions
            for session in self.active_sessions.values():
                session.context.update({
                    "current_story_point": story_point,
                    "current_chapter": chapter,
                    **progress_data
                })

        except Exception as e:
            logger.error(f"Error handling story progression: {str(e)}")

    async def _handle_condition_check(self, event: DialogueEvent, broker_message: Message):
        """Handle condition check event."""
        try:
            content = event.content
            session_id = event.session_id
            condition_type = content.get("condition_type")
            condition_data = content.get("condition_data", {})

            result = await self._evaluate_condition(session_id, condition_type, condition_data)

            # Send condition result back
            result_event = DialogueEvent(
                event_id=f"condition_result_{int(time.time())}",
                event_type=DialogueEventType.DIALOGUE_RESPONSE,
                session_id=session_id,
                content={
                    "condition_type": condition_type,
                    "condition_result": result,
                    "original_event_id": event.event_id
                },
                priority=MessagePriority.HIGH
            )

            await self._publish_dialogue_event(result_event)

        except Exception as e:
            logger.error(f"Error handling condition check: {str(e)}")

    async def _handle_quest_dialogue(self, event: DialogueEvent, broker_message: Message):
        """Handle quest dialogue event."""
        try:
            content = event.content
            quest_id = content.get("quest_id")
            quest_stage = content.get("quest_stage")
            dialogue_type = content.get("dialogue_type", "update")

            logger.info(f"Quest dialogue: {quest_id} - {quest_stage} ({dialogue_type})")

            # Update quest context in relevant sessions
            for session in self.active_sessions.values():
                session.context.update({
                    f"quest_{quest_id}_stage": quest_stage,
                    f"quest_{quest_id}_dialogue_type": dialogue_type
                })

        except Exception as e:
            logger.error(f"Error handling quest dialogue: {str(e)}")

    async def _process_dialogue_node(self, session_id: str, node_id: str):
        """Process a dialogue node."""
        try:
            if session_id not in self.active_sessions:
                return

            session = self.active_sessions[session_id]

            if node_id not in self.dialogue_nodes:
                logger.warning(f"Dialogue node {node_id} not found")
                return

            node = self.dialogue_nodes[node_id]
            session.current_node_id = node_id

            # Update session history
            session.history.append({
                "event_type": "node_processed",
                "timestamp": time.time(),
                "node_id": node_id,
                "speaker_id": node.speaker_id,
                "text": node.text
            })

            # Check node conditions
            if not await self._check_node_conditions(session, node):
                logger.debug(f"Node {node_id} conditions not met")
                return

            # Execute node actions
            await self._execute_node_actions(session, node)

            # Trigger voice line if specified
            if node.voice_line_id:
                await self._trigger_voice_line(node.voice_line_id, node.speaker_id, node.emotion)

            # Handle choices
            if node.choices:
                session.state = DialogueState.WAITING_FOR_CHOICE
                await self._present_choices_to_player(session, node)
            else:
                # Move to next node
                if node.next_nodes:
                    next_node_id = node.next_nodes[0]  # Simple progression
                    await self._process_dialogue_node(session_id, next_node_id)
                else:
                    # End dialogue
                    await self._end_dialogue_session(session_id)

            self.stats['dialogue_nodes_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing dialogue node {node_id}: {str(e)}")

    async def _process_dialogue_choice(self, session_id: str, choice_index: int, choice_data: Dict[str, Any]):
        """Process a dialogue choice."""
        try:
            if session_id not in self.active_sessions:
                return

            session = self.active_sessions[session_id]
            current_node_id = session.current_node_id

            if not current_node_id or current_node_id not in self.dialogue_nodes:
                logger.warning(f"No current node for choice processing in session {session_id}")
                return

            current_node = self.dialogue_nodes[current_node_id]

            if choice_index >= len(current_node.choices):
                logger.warning(f"Invalid choice index {choice_index} for node {current_node_id}")
                return

            choice = current_node.choices[choice_index]
            next_node_id = choice.get("next_node_id")

            # Execute choice actions
            if "actions" in choice:
                await self._execute_actions(session, choice["actions"])

            # Move to next node
            if next_node_id:
                session.state = DialogueState.ACTIVE
                await self._process_dialogue_node(session_id, next_node_id)
            else:
                # End dialogue
                await self._end_dialogue_session(session_id)

        except Exception as e:
            logger.error(f"Error processing dialogue choice: {str(e)}")

    async def _check_node_conditions(self, session: DialogueSession, node: DialogueNode) -> bool:
        """Check if node conditions are met."""
        try:
            for condition in node.conditions:
                condition_type = condition.get("type")
                condition_data = condition.get("data", {})

                result = await self._evaluate_condition(session.session_id, condition_type, condition_data)
                if not result:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking node conditions: {str(e)}")
            return True  # Default to allowing the node

    async def _evaluate_condition(self, session_id: str, condition_type: str, condition_data: Dict[str, Any]) -> bool:
        """Evaluate a dialogue condition."""
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]

            if condition_type == "relationship_check":
                character_id = condition_data.get("character_id")
                required_level = condition_data.get("required_level", 0)
                player_id = condition_data.get("player_id", session.participants[0])

                relationship_key = f"relationship_{character_id}_{player_id}"
                current_level = session.context.get(relationship_key, 0)

                return current_level >= required_level

            elif condition_type == "story_point_check":
                required_story_point = condition_data.get("required_story_point")
                current_story_point = session.context.get("current_story_point", 0)

                return current_story_point >= required_story_point

            elif condition_type == "quest_stage_check":
                quest_id = condition_data.get("quest_id")
                required_stage = condition_data.get("required_stage")

                current_stage = session.context.get(f"quest_{quest_id}_stage", 0)

                return current_stage >= required_stage

            elif condition_type == "item_check":
                required_items = condition_data.get("required_items", [])
                player_inventory = session.context.get("player_inventory", [])

                for item in required_items:
                    if item not in player_inventory:
                        return False

                return True

            elif condition_type == "custom":
                # Custom condition evaluation
                custom_function = condition_data.get("function")
                if custom_function and hasattr(self, custom_function):
                    func = getattr(self, custom_function)
                    return await func(session, condition_data)

            return True  # Default to passing unknown conditions

        except Exception as e:
            logger.error(f"Error evaluating condition {condition_type}: {str(e)}")
            return False

    async def _execute_node_actions(self, session: DialogueSession, node: DialogueNode):
        """Execute node actions."""
        if node.actions:
            await self._execute_actions(session, node.actions)

    async def _execute_actions(self, session: DialogueSession, actions: List[Dict[str, Any]]):
        """Execute a list of actions."""
        try:
            for action in actions:
                action_type = action.get("type")
                action_data = action.get("data", {})

                if action_type == "set_context":
                    session.context.update(action_data)

                elif action_type == "trigger_event":
                    event_type = action_data.get("event_type")
                    event_content = action_data.get("content", {})

                    event = DialogueEvent(
                        event_id=f"action_event_{int(time.time())}",
                        event_type=DialogueEventType(event_type),
                        session_id=session.session_id,
                        content=event_content
                    )

                    await self._publish_dialogue_event(event)

                elif action_type == "change_relationship":
                    character_id = action_data.get("character_id")
                    change_amount = action_data.get("change_amount", 0)
                    player_id = action_data.get("player_id", session.participants[0])

                    relationship_key = f"relationship_{character_id}_{player_id}"
                    current_level = session.context.get(relationship_key, 0)
                    new_level = current_level + change_amount
                    session.context[relationship_key] = new_level

                    # Trigger relationship change event
                    relationship_event = DialogueEvent(
                        event_id=f"relationship_change_{int(time.time())}",
                        event_type=DialogueEventType.RELATIONSHIP_CHANGE,
                        session_id=session.session_id,
                        speaker_id=character_id,
                        listener_id=player_id,
                        content={
                            "character_id": character_id,
                            "player_id": player_id,
                            "relationship_change": change_amount,
                            "new_relationship_level": new_level
                        }
                    )

                    await self._publish_dialogue_event(relationship_event)

        except Exception as e:
            logger.error(f"Error executing actions: {str(e)}")

    async def _present_choices_to_player(self, session: DialogueSession, node: DialogueNode):
        """Present dialogue choices to player."""
        try:
            # Filter choices based on conditions
            available_choices = []
            for i, choice in enumerate(node.choices):
                if "conditions" in choice:
                    conditions_met = True
                    for condition in choice["conditions"]:
                        condition_type = condition.get("type")
                        condition_data = condition.get("data", {})
                        if not await self._evaluate_condition(session.session_id, condition_type, condition_data):
                            conditions_met = False
                            break

                    if conditions_met:
                        available_choices.append((i, choice))
                else:
                    available_choices.append((i, choice))

            # Present choices event
            event = DialogueEvent(
                event_id=f"present_choices_{int(time.time())}",
                event_type=DialogueEventType.DIALOGUE_RESPONSE,
                session_id=session.session_id,
                content={
                    "action": "present_choices",
                    "choices": [{"index": i, "text": choice.get("text", ""), "data": choice} for i, choice in available_choices],
                    "speaker_id": node.speaker_id,
                    "node_id": node.node_id
                },
                priority=MessagePriority.HIGH
            )

            await self._publish_dialogue_event(event)

        except Exception as e:
            logger.error(f"Error presenting choices: {str(e)}")

    async def _trigger_voice_line(self, voice_line_id: str, character_id: str, emotion: Optional[str] = None):
        """Trigger a voice line."""
        try:
            event = DialogueEvent(
                event_id=f"voice_trigger_{int(time.time())}",
                event_type=DialogueEventType.VOICE_LINE_TRIGGER,
                session_id="",  # Not session-specific
                speaker_id=character_id,
                content={
                    "voice_line_id": voice_line_id,
                    "character_id": character_id,
                    "emotion": emotion
                },
                priority=MessagePriority.NORMAL
            )

            await self._publish_dialogue_event(event)

        except Exception as e:
            logger.error(f"Error triggering voice line: {str(e)}")

    async def _update_sessions_with_npc_speech(self, event: DialogueEvent):
        """Update active sessions with NPC speech."""
        npc_id = event.speaker_id
        content = event.content

        for session in self.active_sessions.values():
            if npc_id in session.participants:
                session.history.append({
                    "event_type": DialogueEventType.NPC_SPEAK.value,
                    "timestamp": event.timestamp,
                    "npc_id": npc_id,
                    "content": content
                })

    async def _update_sessions_with_player_speech(self, event: DialogueEvent):
        """Update active sessions with player speech."""
        player_id = event.speaker_id
        content = event.content

        for session in self.active_sessions.values():
            if player_id in session.participants:
                session.history.append({
                    "event_type": DialogueEventType.PLAYER_SPEAK.value,
                    "timestamp": event.timestamp,
                    "player_id": player_id,
                    "content": content
                })

    async def _end_dialogue_session(self, session_id: str):
        """End a dialogue session."""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.state = DialogueState.COMPLETED

                # Send end event
                event = DialogueEvent(
                    event_id=f"dialogue_end_{int(time.time())}",
                    event_type=DialogueEventType.DIALOGUE_END,
                    session_id=session_id,
                    content={
                        "reason": "natural_end",
                        "final_node_id": session.current_node_id,
                        "history_length": len(session.history)
                    },
                    priority=MessagePriority.NORMAL
                )

                await self._publish_dialogue_event(event)

                # Remove from active sessions
                del self.active_sessions[session_id]
                self.stats['sessions_completed'] += 1

                logger.info(f"Ended dialogue session {session_id}")

        except Exception as e:
            logger.error(f"Error ending dialogue session {session_id}: {str(e)}")

    async def _publish_dialogue_event(self, event: DialogueEvent):
        """Publish a dialogue event."""
        try:
            message = Message(
                type=MessageType.DIALOGUE_MESSAGE,
                topic=f"dialogue.event.{event.event_type.value}",
                payload={
                    "event": event.__dict__,
                    "instance_id": self.instance_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "session_id": event.session_id,
                    "speaker_id": event.speaker_id or "",
                    "instance_id": self.instance_id
                },
                priority=event.priority,
                source="dialogue_consumer"
            )

            await self.broker.publish(message, f"dialogue.event.{event.event_type.value}")

        except Exception as e:
            logger.error(f"Error publishing dialogue event: {str(e)}")

    async def _cleanup_loop(self):
        """Cleanup loop for expired sessions."""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []

                for session_id, session in self.active_sessions.items():
                    if current_time - session.last_activity > session.timeout:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    logger.info(f"Cleaning up expired dialogue session {session_id}")
                    await self._end_dialogue_session(session_id)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)

    def register_dialogue_node(self, node: DialogueNode):
        """Register a dialogue node."""
        self.dialogue_nodes[node.node_id] = node
        logger.debug(f"Registered dialogue node: {node.node_id}")

    def register_event_handler(self, event_type: DialogueEventType, handler: Callable):
        """Register custom event handler."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered custom handler for event type: {event_type.value}")

    def register_state_handler(self, state: DialogueState, handler: Callable):
        """Register custom state handler."""
        self.state_handlers[state] = handler
        logger.info(f"Registered custom handler for state: {state.value}")

    async def _handle_waiting_for_choice(self, session: DialogueSession, event: DialogueEvent):
        """Handle waiting for choice state."""
        # Default implementation - could be overridden
        pass

    async def _handle_processing_choice(self, session: DialogueSession, event: DialogueEvent):
        """Handle processing choice state."""
        # Default implementation - could be overridden
        pass

    def get_active_sessions(self) -> Dict[str, DialogueSession]:
        """Get all active dialogue sessions."""
        return self.active_sessions.copy()

    def get_session(self, session_id: str) -> Optional[DialogueSession]:
        """Get a specific dialogue session."""
        return self.active_sessions.get(session_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            **self.stats,
            'active_sessions': len(self.active_sessions),
            'registered_nodes': len(self.dialogue_nodes),
            'instance_id': self.instance_id
        }

    async def shutdown(self):
        """Shutdown the dialogue consumer gracefully."""
        try:
            await self.stop_consuming()

            # End all active sessions
            session_ids = list(self.active_sessions.keys())
            for session_id in session_ids:
                await self._end_dialogue_session(session_id)

            # Clear data
            self.active_sessions.clear()
            self.dialogue_nodes.clear()
            self.event_handlers.clear()
            self.state_handlers.clear()

            logger.info(f"Dialogue consumer {self.instance_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during dialogue consumer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'DialogueConsumer',
    'DialogueEvent',
    'DialogueSession',
    'DialogueNode',
    'DialogueEventType',
    'DialogueState'
]