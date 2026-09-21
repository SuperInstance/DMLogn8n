#!/usr/bin/env python3
"""
Game Producer - Handles game state updates and event messages.

This producer manages messages for game events including:
- Game state updates
- Player actions
- World events
- Combat events
- Quest updates
- Inventory changes
- Character progression
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from ..message_broker import (
    Message, MessageType, MessagePriority, MessageBroker,
    QueueConfig, ExchangeConfig, ConsumerConfig
)

logger = logging.getLogger(__name__)


class GameEventType(Enum):
    """Game event types."""
    PLAYER_ACTION = "player_action"
    STATE_UPDATE = "state_update"
    WORLD_EVENT = "world_event"
    COMBAT_EVENT = "combat_event"
    QUEST_UPDATE = "quest_update"
    INVENTORY_CHANGE = "inventory_change"
    CHARACTER_PROGRESSION = "character_progression"
    LOCATION_CHANGE = "location_change"
    DIALOGUE_EVENT = "dialogue_event"
    SKILL_CHECK = "skill_check"
    ENVIRONMENT_CHANGE = "environment_change"
    TIME_EVENT = "time_event"
    SYSTEM_EVENT = "system_event"


class ActionType(Enum):
    """Player action types."""
    MOVE = "move"
    ATTACK = "attack"
    DEFEND = "defend"
    USE_ITEM = "use_item"
    INTERACT = "interact"
    CAST_SPELL = "cast_spell"
    SKILL_USE = "skill_use"
    TALK = "talk"
    EXAMINE = "examine"
    WAIT = "wait"
    REST = "rest"


@dataclass
class GameState:
    """Game state structure."""
    game_id: str
    session_id: str
    turn_number: int = 0
    phase: str = "setup"  # setup, playing, paused, ended
    game_mode: str = "normal"  # normal, combat, dialogue, cutscene
    world_time: float = 0.0
    environment: Dict[str, Any] = field(default_factory=dict)
    global_flags: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerInfo:
    """Player information structure."""
    player_id: str
    name: str
    character_id: str
    location: str
    status: str = "active"  # active, inactive, busy, offline
    permissions: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    last_action: Optional[str] = None
    last_action_time: float = field(default_factory=time.time)


@dataclass
class GameEvent:
    """Game event structure."""
    event_id: str
    event_type: GameEventType
    game_id: str
    session_id: str
    player_id: Optional[str] = None
    target_id: Optional[str] = None
    location: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration: Optional[float] = None
    visibility: str = "all"  # all, players, dm, system
    priority: MessagePriority = MessagePriority.NORMAL
    requires_processing: bool = True


@dataclass
class PlayerAction:
    """Player action structure."""
    action_id: str
    player_id: str
    action_type: ActionType
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    location: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    intent: Optional[str] = None
    outcome: Optional[str] = None
    success: Optional[bool] = None
    processing_time: Optional[float] = None


class GameProducer:
    """
    Producer for game state and event messages.
    """

    def __init__(self, message_broker: MessageBroker, game_id: str):
        self.broker = message_broker
        self.game_id = game_id
        self.session_id = f"session_{int(time.time())}"
        self.game_state = GameState(game_id=game_id, session_id=self.session_id)
        self.players: Dict[str, PlayerInfo] = {}
        self.active_events: Dict[str, GameEvent] = {}
        self.pending_actions: Dict[str, PlayerAction] = {}
        self.event_handlers: Dict[str, callable] = {}
        self.stats = {
            'events_published': 0,
            'state_updates': 0,
            'player_actions': 0,
            'world_events': 0,
            'combat_events': 0,
            'quest_updates': 0,
            'errors': 0
        }

    async def initialize(self):
        """Initialize the game producer."""
        try:
            # Declare game-specific exchange
            exchange_config = ExchangeConfig(
                name=f"game.{self.game_id}.exchange",
                type="topic",
                durable=True
            )
            await self.broker.declare_exchange(exchange_config)

            # Declare game state queue
            queue_config = QueueConfig(
                name=f"game.{self.game_id}.state",
                durable=True,
                arguments={
                    "x-message-ttl": 600000,  # 10 minutes TTL
                    "x-max-length": 5000      # Max 5000 state updates
                }
            )
            await self.broker.declare_queue(queue_config)

            # Declare events queue
            events_queue = QueueConfig(
                name=f"game.{self.game_id}.events",
                durable=True,
                arguments={
                    "x-message-ttl": 300000,  # 5 minutes TTL
                    "x-max-length": 10000     # Max 10000 events
                }
            )
            await self.broker.declare_queue(events_queue)

            # Bind queues to exchange
            await self.broker.bind_queue(
                queue_config.name,
                exchange_config.name,
                "game.state.update"
            )

            await self.broker.bind_queue(
                events_queue.name,
                exchange_config.name,
                "game.event.#"
            )

            # Publish initial game state
            await self.publish_state_update(initial_state=True)

            logger.info(f"Initialized game producer for game {self.game_id}")

        except Exception as e:
            logger.error(f"Failed to initialize game producer: {str(e)}")
            raise

    async def add_player(self, player_info: PlayerInfo) -> bool:
        """
        Add a player to the game.

        Args:
            player_info: Player information

        Returns:
            bool: True if player added successfully
        """
        try:
            self.players[player_info.player_id] = player_info

            # Publish player join event
            event = GameEvent(
                event_id=f"player_join_{player_info.player_id}_{int(time.time())}",
                event_type=GameEventType.PLAYER_ACTION,
                game_id=self.game_id,
                session_id=self.session_id,
                player_id=player_info.player_id,
                location=player_info.location,
                data={
                    "action": "join",
                    "player_info": player_info.__dict__
                },
                priority=MessagePriority.NORMAL
            )

            await self.publish_event(event)

            # Update game state
            await self.publish_state_update()

            logger.info(f"Added player {player_info.player_id} to game {self.game_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add player {player_info.player_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def remove_player(self, player_id: str) -> bool:
        """
        Remove a player from the game.

        Args:
            player_id: ID of the player to remove

        Returns:
            bool: True if player removed successfully
        """
        try:
            if player_id in self.players:
                player_info = self.players[player_id]
                del self.players[player_id]

                # Publish player leave event
                event = GameEvent(
                    event_id=f"player_leave_{player_id}_{int(time.time())}",
                    event_type=GameEventType.PLAYER_ACTION,
                    game_id=self.game_id,
                    session_id=self.session_id,
                    player_id=player_id,
                    location=player_info.location,
                    data={
                        "action": "leave",
                        "player_info": player_info.__dict__
                    },
                    priority=MessagePriority.NORMAL
                )

                await self.publish_event(event)

                # Update game state
                await self.publish_state_update()

                logger.info(f"Removed player {player_id} from game {self.game_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove player {player_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_player_action(self, action: PlayerAction) -> bool:
        """
        Publish a player action event.

        Args:
            action: Player action to publish

        Returns:
            bool: True if action published successfully
        """
        try:
            # Store pending action
            self.pending_actions[action.action_id] = action

            # Create game event
            event = GameEvent(
                event_id=action.action_id,
                event_type=GameEventType.PLAYER_ACTION,
                game_id=self.game_id,
                session_id=self.session_id,
                player_id=action.player_id,
                location=action.location,
                data={
                    "action": action.__dict__,
                    "timestamp": action.timestamp
                },
                priority=action.priority,
                requires_processing=True
            )

            success = await self.publish_event(event)

            if success:
                self.stats['player_actions'] += 1
                logger.debug(f"Published player action {action.action_id} from {action.player_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish player action {action.action_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_state_update(self, updates: Optional[Dict[str, Any]] = None,
                                 initial_state: bool = False) -> bool:
        """
        Publish game state update.

        Args:
            updates: State updates to apply
            initial_state: Whether this is the initial state

        Returns:
            bool: True if update published successfully
        """
        try:
            # Apply updates to game state
            if updates:
                for key, value in updates.items():
                    if hasattr(self.game_state, key):
                        setattr(self.game_state, key, value)
                    else:
                        self.game_state.metadata[key] = value

            # Increment turn number if not initial state
            if not initial_state:
                self.game_state.turn_number += 1

            # Create state update message
            message = Message(
                type=MessageType.GAME_STATE_UPDATE,
                topic=f"game.{self.game_id}.state.update",
                payload={
                    "game_state": self.game_state.__dict__,
                    "players": {pid: p.__dict__ for pid, p in self.players.items()},
                    "updates": updates or {},
                    "initial_state": initial_state,
                    "timestamp": time.time()
                },
                headers={
                    "game_id": self.game_id,
                    "session_id": self.session_id,
                    "turn_number": str(self.game_state.turn_number),
                    "initial_state": str(initial_state)
                },
                priority=MessagePriority.HIGH if initial_state else MessagePriority.NORMAL,
                source="game_engine"
            )

            success = await self.broker.publish(message, "game.state.update")

            if success:
                self.stats['state_updates'] += 1
                logger.debug(f"Published state update for game {self.game_id}, turn {self.game_state.turn_number}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish state update: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_event(self, event: GameEvent) -> bool:
        """
        Publish a game event.

        Args:
            event: Game event to publish

        Returns:
            bool: True if event published successfully
        """
        try:
            # Store active event
            if event.duration:
                self.active_events[event.event_id] = event

            # Create event message
            message = Message(
                type=MessageType.GAME_STATE_UPDATE,
                topic=f"game.{self.game_id}.event.{event.event_type.value}",
                payload={
                    "event": event.__dict__,
                    "game_state": self.game_state.__dict__
                },
                headers={
                    "game_id": self.game_id,
                    "session_id": self.session_id,
                    "event_type": event.event_type.value,
                    "player_id": event.player_id or "",
                    "location": event.location or "",
                    "visibility": event.visibility,
                    "requires_processing": str(event.requires_processing)
                },
                priority=event.priority,
                source="game_engine",
                expiration=int((event.timestamp + (event.duration or 300)) * 1000) if event.duration else None
            )

            # Determine routing key based on event type and visibility
            routing_key = f"game.event.{event.event_type.value}"
            if event.visibility != "all":
                routing_key += f".{event.visibility}"

            success = await self.broker.publish(message, routing_key)

            if success:
                self.stats['events_published'] += 1

                # Update specific event type stats
                if event.event_type == GameEventType.WORLD_EVENT:
                    self.stats['world_events'] += 1
                elif event.event_type == GameEventType.COMBAT_EVENT:
                    self.stats['combat_events'] += 1
                elif event.event_type == GameEventType.QUEST_UPDATE:
                    self.stats['quest_updates'] += 1

                logger.debug(f"Published event {event.event_id} for game {self.game_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_world_event(self, event_data: Dict[str, Any],
                                location: Optional[str] = None,
                                visibility: str = "all") -> bool:
        """
        Publish a world event.

        Args:
            event_data: Event data
            location: Event location
            visibility: Event visibility

        Returns:
            bool: True if event published successfully
        """
        event = GameEvent(
            event_id=f"world_event_{int(time.time() * 1000)}",
            event_type=GameEventType.WORLD_EVENT,
            game_id=self.game_id,
            session_id=self.session_id,
            location=location,
            data=event_data,
            visibility=visibility,
            priority=MessagePriority.NORMAL
        )

        return await self.publish_event(event)

    async def publish_combat_event(self, combat_data: Dict[str, Any],
                                 participants: List[str],
                                 location: Optional[str] = None) -> bool:
        """
        Publish a combat event.

        Args:
            combat_data: Combat event data
            participants: List of participant IDs
            location: Combat location

        Returns:
            bool: True if event published successfully
        """
        event = GameEvent(
            event_id=f"combat_event_{int(time.time() * 1000)}",
            event_type=GameEventType.COMBAT_EVENT,
            game_id=self.game_id,
            session_id=self.session_id,
            location=location,
            data={
                "combat_data": combat_data,
                "participants": participants
            },
            visibility="players",
            priority=MessagePriority.HIGH
        )

        return await self.publish_event(event)

    async def publish_quest_update(self, quest_data: Dict[str, Any],
                                 player_ids: List[str]) -> bool:
        """
        Publish a quest update event.

        Args:
            quest_data: Quest update data
            player_ids: List of affected player IDs

        Returns:
            bool: True if update published successfully
        """
        event = GameEvent(
            event_id=f"quest_update_{int(time.time() * 1000)}",
            event_type=GameEventType.QUEST_UPDATE,
            game_id=self.game_id,
            session_id=self.session_id,
            data={
                "quest_data": quest_data,
                "affected_players": player_ids
            },
            visibility="players",
            priority=MessagePriority.NORMAL
        )

        return await self.publish_event(event)

    async def publish_dialogue_event(self, dialogue_data: Dict[str, Any],
                                   player_id: str, npc_id: str) -> bool:
        """
        Publish a dialogue event.

        Args:
            dialogue_data: Dialogue event data
            player_id: Player ID
            npc_id: NPC ID

        Returns:
            bool: True if event published successfully
        """
        event = GameEvent(
            event_id=f"dialogue_event_{int(time.time() * 1000)}",
            event_type=GameEventType.DIALOGUE_EVENT,
            game_id=self.game_id,
            session_id=self.session_id,
            player_id=player_id,
            target_id=npc_id,
            data=dialogue_data,
            visibility="players",
            priority=MessagePriority.NORMAL
        )

        return await self.publish_event(event)

    async def publish_environment_change(self, environment_data: Dict[str, Any],
                                       location: Optional[str] = None) -> bool:
        """
        Publish an environment change event.

        Args:
            environment_data: Environment change data
            location: Affected location

        Returns:
            bool: True if event published successfully
        """
        event = GameEvent(
            event_id=f"env_change_{int(time.time() * 1000)}",
            event_type=GameEventType.ENVIRONMENT_CHANGE,
            game_id=self.game_id,
            session_id=self.session_id,
            location=location,
            data=environment_data,
            visibility="all",
            priority=MessagePriority.NORMAL
        )

        return await self.publish_event(event)

    async def advance_time(self, time_delta: float) -> bool:
        """
        Advance game world time.

        Args:
            time_delta: Time to advance in seconds

        Returns:
            bool: True if time advanced successfully
        """
        try:
            self.game_state.world_time += time_delta

            # Create time event
            event = GameEvent(
                event_id=f"time_advance_{int(time.time() * 1000)}",
                event_type=GameEventType.TIME_EVENT,
                game_id=self.game_id,
                session_id=self.session_id,
                data={
                    "time_delta": time_delta,
                    "new_world_time": self.game_state.world_time
                },
                visibility="all",
                priority=MessagePriority.LOW
            )

            # Publish both event and state update
            event_success = await self.publish_event(event)
            state_success = await self.publish_state_update()

            return event_success and state_success

        except Exception as e:
            logger.error(f"Failed to advance time: {str(e)}")
            self.stats['errors'] += 1
            return False

    def get_player_info(self, player_id: str) -> Optional[PlayerInfo]:
        """Get player information."""
        return self.players.get(player_id)

    def get_game_state(self) -> GameState:
        """Get current game state."""
        return self.game_state

    def get_active_events(self) -> Dict[str, GameEvent]:
        """Get active events."""
        return self.active_events.copy()

    def get_pending_actions(self) -> Dict[str, PlayerAction]:
        """Get pending player actions."""
        return self.pending_actions.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics."""
        return {
            **self.stats,
            'game_id': self.game_id,
            'session_id': self.session_id,
            'player_count': len(self.players),
            'active_events': len(self.active_events),
            'pending_actions': len(self.pending_actions),
            'current_turn': self.game_state.turn_number,
            'world_time': self.game_state.world_time
        }

    async def cleanup_expired_events(self):
        """Clean up expired events."""
        current_time = time.time()
        expired_events = []

        for event_id, event in self.active_events.items():
            if event.duration and (event.timestamp + event.duration) < current_time:
                expired_events.append(event_id)

        for event_id in expired_events:
            del self.active_events[event_id]
            logger.debug(f"Cleaned up expired event: {event_id}")

        if expired_events:
            logger.info(f"Cleaned up {len(expired_events)} expired events")

    async def shutdown(self):
        """Shutdown the game producer gracefully."""
        try:
            # Publish game end event
            event = GameEvent(
                event_id=f"game_end_{int(time.time() * 1000)}",
                event_type=GameEventType.SYSTEM_EVENT,
                game_id=self.game_id,
                session_id=self.session_id,
                data={
                    "action": "shutdown",
                    "final_state": self.game_state.__dict__
                },
                visibility="all",
                priority=MessagePriority.HIGH
            )

            await self.publish_event(event)

            # Clear data
            self.players.clear()
            self.active_events.clear()
            self.pending_actions.clear()
            self.event_handlers.clear()

            logger.info(f"Game producer for {self.game_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during game producer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'GameProducer',
    'GameEvent',
    'GameState',
    'PlayerInfo',
    'PlayerAction',
    'GameEventType',
    'ActionType'
]