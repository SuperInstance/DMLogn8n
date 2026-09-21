#!/usr/bin/env python3
"""
Combat Consumer - Handles combat engine message consumption.

This consumer processes combat-related messages including:
- Combat events and updates
- Initiative rolls
- Attack and damage calculations
- Status effects and conditions
- Combat state changes
- Turn management
- Combat resolution
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


class CombatEventType(Enum):
    """Combat event types."""
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    INITIATIVE_ROLL = "initiative_roll"
    ATTACK_DECLARE = "attack_declare"
    ATTACK_RESOLVE = "attack_resolve"
    DAMAGE_APPLY = "damage_apply"
    HEALING_APPLY = "healing_apply"
    STATUS_EFFECT_APPLY = "status_effect_apply"
    STATUS_EFFECT_REMOVE = "status_effect_remove"
    MOVEMENT = "movement"
    ACTION_USE = "action_use"
    SPELL_CAST = "spell_cast"
    ABILITY_USE = "ability_use"
    CRITICAL_HIT = "critical_hit"
    FUMBLE = "fumble"
    COMBAT_LOG = "combat_log"


class CombatPhase(Enum):
    """Combat phase types."""
    SETUP = "setup"
    INITIATIVE = "initiative"
    ACTIVE = "active"
    RESOLUTION = "resolution"
    CLEANUP = "cleanup"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass
class Combatant:
    """Combatant information."""
    combatant_id: str
    name: str
    type: str  # player, npc, monster, ally
    initiative: int = 0
    current_hp: int = 0
    max_hp: int = 0
    armor_class: int = 10
    speed: int = 30
    status_effects: List[Dict[str, Any]] = field(default_factory=list)
    actions_used: int = 0
    bonus_actions_used: int = 0
    reactions_used: int = 0
    movement_remaining: int = 0
    concentration: bool = False
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CombatEncounter:
    """Combat encounter structure."""
    encounter_id: str
    name: str
    participants: List[Combatant] = field(default_factory=list)
    current_round: int = 0
    current_turn_index: int = 0
    phase: CombatPhase = CombatPhase.SETUP
    turn_order: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    rules: Dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CombatEvent:
    """Combat event structure."""
    event_id: str
    event_type: CombatEventType
    encounter_id: str
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: MessagePriority = MessagePriority.NORMAL
    round_number: Optional[int] = None
    turn_order_index: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CombatConsumer:
    """
    Consumer for combat engine messages.
    """

    def __init__(self, message_broker: MessageBroker, instance_id: str):
        self.broker = message_broker
        self.instance_id = instance_id
        self.active_encounters: Dict[str, CombatEncounter] = {}
        self.event_handlers: Dict[CombatEventType, Callable] = {}
        self.phase_handlers: Dict[CombatPhase, Callable] = {}
        self.consuming = False
        self.consumer_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_received': 0,
            'events_processed': 0,
            'encounters_created': 0,
            'encounters_completed': 0,
            'attacks_processed': 0,
            'damage_events': 0,
            'healing_events': 0,
            'status_effects_applied': 0,
            'errors': 0
        }

    async def initialize(self):
        """Initialize the combat consumer."""
        try:
            # Setup combat-specific queues
            await self._setup_queues()

            # Register default handlers
            self._register_default_handlers()

            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info(f"Initialized combat consumer for instance {self.instance_id}")

        except Exception as e:
            logger.error(f"Failed to initialize combat consumer: {str(e)}")
            raise

    async def _setup_queues(self):
        """Setup combat consumer queues."""
        try:
            # Combat events queue
            events_queue = QueueConfig(
                name=f"combat.{self.instance_id}.events",
                durable=True,
                arguments={
                    "x-message-ttl": 600000,  # 10 minutes TTL
                    "x-max-length": 5000      # Max 5000 events
                }
            )
            await self.broker.declare_queue(events_queue)

            # Combat encounter queue
            encounter_queue = QueueConfig(
                name=f"combat.{self.instance_id}.encounters",
                durable=True,
                arguments={
                    "x-message-ttl": 3600000,  # 1 hour TTL
                    "x-max-length": 1000       # Max 1000 encounters
                }
            )
            await self.broker.declare_queue(encounter_queue)

            # Combat resolution queue
            resolution_queue = QueueConfig(
                name=f"combat.{self.instance_id}.resolution",
                durable=True,
                arguments={
                    "x-message-ttl": 1800000   # 30 minutes TTL
                }
            )
            await self.broker.declare_queue(resolution_queue)

            # Bind queues to combat exchange
            combat_exchange = "combat.exchange"
            await self.broker.bind_queue(events_queue.name, combat_exchange, "combat.event.#")
            await self.broker.bind_queue(encounter_queue.name, combat_exchange, "combat.encounter.#")
            await self.broker.bind_queue(resolution_queue.name, combat_exchange, "combat.resolution.#")

        except Exception as e:
            logger.error(f"Failed to setup combat queues: {str(e)}")
            raise

    def _register_default_handlers(self):
        """Register default event handlers."""
        self.event_handlers[CombatEventType.COMBAT_START] = self._handle_combat_start
        self.event_handlers[CombatEventType.COMBAT_END] = self._handle_combat_end
        self.event_handlers[CombatEventType.ROUND_START] = self._handle_round_start
        self.event_handlers[CombatEventType.ROUND_END] = self._handle_round_end
        self.event_handlers[CombatEventType.TURN_START] = self._handle_turn_start
        self.event_handlers[CombatEventType.TURN_END] = self._handle_turn_end
        self.event_handlers[CombatEventType.INITIATIVE_ROLL] = self._handle_initiative_roll
        self.event_handlers[CombatEventType.ATTACK_DECLARE] = self._handle_attack_declare
        self.event_handlers[CombatEventType.ATTACK_RESOLVE] = self._handle_attack_resolve
        self.event_handlers[CombatEventType.DAMAGE_APPLY] = self._handle_damage_apply
        self.event_handlers[CombatEventType.HEALING_APPLY] = self._handle_healing_apply
        self.event_handlers[CombatEventType.STATUS_EFFECT_APPLY] = self._handle_status_effect_apply
        self.event_handlers[CombatEventType.STATUS_EFFECT_REMOVE] = self._handle_status_effect_remove
        self.event_handlers[CombatEventType.MOVEMENT] = self._handle_movement
        self.event_handlers[CombatEventType.ACTION_USE] = self._handle_action_use
        self.event_handlers[CombatEventType.SPELL_CAST] = self._handle_spell_cast
        self.event_handlers[CombatEventType.ABILITY_USE] = self._handle_ability_use
        self.event_handlers[CombatEventType.CRITICAL_HIT] = self._handle_critical_hit
        self.event_handlers[CombatEventType.FUMBLE] = self._handle_fumble
        self.event_handlers[CombatEventType.COMBAT_LOG] = self._handle_combat_log

        # Register phase handlers
        self.phase_handlers[CombatPhase.SETUP] = self._handle_setup_phase
        self.phase_handlers[CombatPhase.INITIATIVE] = self._handle_initiative_phase
        self.phase_handlers[CombatPhase.ACTIVE] = self._handle_active_phase
        self.phase_handlers[CombatPhase.RESOLUTION] = self._handle_resolution_phase
        self.phase_handlers[CombatPhase.CLEANUP] = self._handle_cleanup_phase

    async def start_consuming(self):
        """Start consuming combat messages."""
        if self.consuming:
            logger.warning(f"Combat consumer {self.instance_id} is already consuming")
            return

        try:
            self.consuming = True

            # Start consumer task
            self.consumer_task = asyncio.create_task(self._consume_loop())

            logger.info(f"Combat consumer {self.instance_id} started consuming messages")

        except Exception as e:
            logger.error(f"Failed to start combat consumption: {str(e)}")
            self.consuming = False
            raise

    async def stop_consuming(self):
        """Stop consuming combat messages."""
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

            logger.info(f"Combat consumer {self.instance_id} stopped consuming messages")

        except Exception as e:
            logger.error(f"Error stopping combat consumption: {str(e)}")

    async def _consume_loop(self):
        """Main consumption loop."""
        while self.consuming:
            try:
                # Create consumer config for events
                consumer_config = ConsumerConfig(
                    queue=f"combat.{self.instance_id}.events",
                    prefetch_count=20,
                    auto_ack=False,
                    consumer_tag=f"combat_{self.instance_id}_consumer"
                )

                # Start consuming
                await self.broker.consume(consumer_config, self._handle_message)

                # Keep the loop running
                while self.consuming:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in combat consume loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _handle_message(self, message: Message):
        """Handle incoming combat message."""
        try:
            self.stats['events_received'] += 1

            # Parse combat event from payload
            payload = message.payload
            if "event" not in payload:
                logger.warning(f"Message {message.id} missing event in payload")
                await self.broker.ack_message(message.delivery_tag)
                return

            event_data = payload["event"]
            event = CombatEvent(**event_data)

            # Call appropriate event handler
            if event.event_type in self.event_handlers:
                handler = self.event_handlers[event.event_type]
                await handler(event, message)

            else:
                logger.warning(f"No handler for combat event type: {event.event_type.value}")

            self.stats['events_processed'] += 1
            await self.broker.ack_message(message.delivery_tag)

        except Exception as e:
            logger.error(f"Error handling combat message {message.id}: {str(e)}")
            self.stats['errors'] += 1
            await self.broker.ack_message(message.delivery_tag)  # Ack to prevent reprocessing

    async def _handle_combat_start(self, event: CombatEvent, broker_message: Message):
        """Handle combat start event."""
        try:
            logger.debug(f"Starting combat encounter {event.encounter_id}")

            content = event.content
            encounter_id = event.encounter_id
            encounter_name = content.get("name", f"Combat {encounter_id}")
            participants_data = content.get("participants", [])
            environment = content.get("environment", {})
            rules = content.get("rules", {})

            # Create combat encounter
            participants = []
            for participant_data in participants_data:
                combatant = Combatant(**participant_data)
                participants.append(combatant)

            encounter = CombatEncounter(
                encounter_id=encounter_id,
                name=encounter_name,
                participants=participants,
                environment=environment,
                rules=rules,
                phase=CombatPhase.SETUP
            )

            self.active_encounters[encounter_id] = encounter
            self.stats['encounters_created'] += 1

            # Start setup phase
            await self._change_encounter_phase(encounter_id, CombatPhase.SETUP)

            logger.info(f"Started combat encounter {encounter_id} with {len(participants)} participants")

        except Exception as e:
            logger.error(f"Error handling combat start: {str(e)}")

    async def _handle_combat_end(self, event: CombatEvent, broker_message: Message):
        """Handle combat end event."""
        try:
            encounter_id = event.encounter_id

            if encounter_id not in self.active_encounters:
                logger.warning(f"Combat end for non-existent encounter {encounter_id}")
                return

            encounter = self.active_encounters[encounter_id]
            encounter.phase = CombatPhase.ENDED

            content = event.content
            outcome = content.get("outcome", "unknown")
            victors = content.get("victors", [])
            casualties = content.get("casualties", [])

            # Log final combat statistics
            final_stats = {
                "encounter_id": encounter_id,
                "outcome": outcome,
                "victors": victors,
                "casualties": casualties,
                "total_rounds": encounter.current_round,
                "duration": time.time() - encounter.started_at,
                "participants": [p.__dict__ for p in encounter.participants]
            }

            logger.info(f"Combat encounter {encounter_id} ended. Outcome: {outcome}")

            # Remove from active encounters
            del self.active_encounters[encounter_id]
            self.stats['encounters_completed'] += 1

            # Publish combat summary
            await self._publish_combat_summary(encounter_id, final_stats)

        except Exception as e:
            logger.error(f"Error handling combat end: {str(e)}")

    async def _handle_round_start(self, event: CombatEvent, broker_message: Message):
        """Handle round start event."""
        try:
            encounter_id = event.encounter_id

            if encounter_id not in self.active_encounters:
                logger.warning(f"Round start for non-existent encounter {encounter_id}")
                return

            encounter = self.active_encounters[encounter_id]
            encounter.current_round += 1
            encounter.last_activity = event.timestamp

            # Reset turn-related states for all participants
            for combatant in encounter.participants:
                combatant.actions_used = 0
                combatant.bonus_actions_used = 0
                combatant.reactions_used = 0
                combatant.movement_remaining = combatant.speed

            logger.debug(f"Round {encounter.current_round} started in encounter {encounter_id}")

        except Exception as e:
            logger.error(f"Error handling round start: {str(e)}")

    async def _handle_round_end(self, event: CombatEvent, broker_message: Message):
        """Handle round end event."""
        try:
            encounter_id = event.encounter_id

            if encounter_id not in self.active_encounters:
                logger.warning(f"Round end for non-existent encounter {encounter_id}")
                return

            encounter = self.active_encounters[encounter_id]

            # Process end-of-round effects
            await self._process_end_of_round_effects(encounter_id)

            logger.debug(f"Round {encounter.current_round} ended in encounter {encounter_id}")

        except Exception as e:
            logger.error(f"Error handling round end: {str(e)}")

    async def _handle_turn_start(self, event: CombatEvent, broker_message: Message):
        """Handle turn start event."""
        try:
            encounter_id = event.encounter_id
            turn_order_index = event.turn_order_index
            combatant_id = event.source_id

            if encounter_id not in self.active_encounters:
                logger.warning(f"Turn start for non-existent encounter {encounter_id}")
                return

            encounter = self.active_encounters[encounter_id]
            encounter.current_turn_index = turn_order_index

            # Reset combatant turn states
            combatant = self._get_combatant(encounter_id, combatant_id)
            if combatant:
                combatant.actions_used = 0
                combatant.bonus_actions_used = 0
                combatant.reactions_used = 0
                combatant.movement_remaining = combatant.speed

            logger.debug(f"Turn started for {combatant_id} in encounter {encounter_id}")

        except Exception as e:
            logger.error(f"Error handling turn start: {str(e)}")

    async def _handle_turn_end(self, event: CombatEvent, broker_message: Message):
        """Handle turn end event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id

            if encounter_id not in self.active_encounters:
                logger.warning(f"Turn end for non-existent encounter {encounter_id}")
                return

            # Process end-of-turn effects
            await self._process_end_of_turn_effects(encounter_id, combatant_id)

            logger.debug(f"Turn ended for {combatant_id} in encounter {encounter_id}")

        except Exception as e:
            logger.error(f"Error handling turn end: {str(e)}")

    async def _handle_initiative_roll(self, event: CombatEvent, broker_message: Message):
        """Handle initiative roll event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id
            content = event.content
            initiative_value = content.get("initiative_value", 0)
            roll_details = content.get("roll_details", {})

            if encounter_id not in self.active_encounters:
                logger.warning(f"Initiative roll for non-existent encounter {encounter_id}")
                return

            encounter = self.active_encounters[encounter_id]
            combatant = self._get_combatant(encounter_id, combatant_id)

            if combatant:
                combatant.initiative = initiative_value

            # Check if all participants have rolled initiative
            if all(p.initiative > 0 for p in encounter.participants):
                await self._determine_turn_order(encounter_id)

            logger.debug(f"Initiative roll for {combatant_id}: {initiative_value}")

        except Exception as e:
            logger.error(f"Error handling initiative roll: {str(e)}")

    async def _handle_attack_declare(self, event: CombatEvent, broker_message: Message):
        """Handle attack declaration event."""
        try:
            encounter_id = event.encounter_id
            attacker_id = event.source_id
            target_id = event.target_id
            content = event.content
            attack_type = content.get("attack_type", "melee")
            weapon = content.get("weapon", {})
            modifiers = content.get("modifiers", {})

            logger.debug(f"Attack declared: {attacker_id} -> {target_id} ({attack_type})")

            # Process attack declaration
            await self._process_attack_declaration(encounter_id, attacker_id, target_id, attack_type, weapon, modifiers)

        except Exception as e:
            logger.error(f"Error handling attack declaration: {str(e)}")

    async def _handle_attack_resolve(self, event: CombatEvent, broker_message: Message):
        """Handle attack resolution event."""
        try:
            encounter_id = event.encounter_id
            attacker_id = event.source_id
            target_id = event.target_id
            content = event.content
            attack_roll = content.get("attack_roll", 0)
            hit = content.get("hit", False)
            critical = content.get("critical", False)
            damage_rolls = content.get("damage_rolls", [])
            ac = content.get("armor_class", 10)

            logger.debug(f"Attack resolved: {attacker_id} -> {target_id}, hit={hit}, critical={critical}")

            self.stats['attacks_processed'] += 1

            # Process attack resolution
            await self._process_attack_resolution(encounter_id, attacker_id, target_id, attack_roll, hit, critical, damage_rolls, ac)

        except Exception as e:
            logger.error(f"Error handling attack resolution: {str(e)}")

    async def _handle_damage_apply(self, event: CombatEvent, broker_message: Message):
        """Handle damage application event."""
        try:
            encounter_id = event.encounter_id
            target_id = event.target_id
            content = event.content
            damage_amount = content.get("damage_amount", 0)
            damage_type = content.get("damage_type", "slashing")
            source = content.get("source", "unknown")
            reduction = content.get("damage_reduction", 0)

            # Apply damage to target
            actual_damage = max(0, damage_amount - reduction)
            combatant = self._get_combatant(encounter_id, target_id)

            if combatant:
                combatant.current_hp = max(0, combatant.current_hp - actual_damage)

            self.stats['damage_events'] += 1

            logger.debug(f"Damage applied to {target_id}: {actual_damage} {damage_type} damage (from {source})")

            # Check for unconscious/death
            if combatant and combatant.current_hp <= 0:
                await self._handle_combatant_defeated(encounter_id, target_id)

        except Exception as e:
            logger.error(f"Error handling damage application: {str(e)}")

    async def _handle_healing_apply(self, event: CombatEvent, broker_message: Message):
        """Handle healing application event."""
        try:
            encounter_id = event.encounter_id
            target_id = event.target_id
            content = event.content
            healing_amount = content.get("healing_amount", 0)
            healing_type = content.get("healing_type", "divine")
            source = content.get("source", "unknown")

            # Apply healing to target
            combatant = self._get_combatant(encounter_id, target_id)

            if combatant:
                combatant.current_hp = min(combatant.max_hp, combatant.current_hp + healing_amount)

            self.stats['healing_events'] += 1

            logger.debug(f"Healing applied to {target_id}: {healing_amount} {healing_type} healing (from {source})")

        except Exception as e:
            logger.error(f"Error handling healing application: {str(e)}")

    async def _handle_status_effect_apply(self, event: CombatEvent, broker_message: Message):
        """Handle status effect application event."""
        try:
            encounter_id = event.encounter_id
            target_id = event.target_id
            content = event.content
            effect_name = content.get("effect_name", "unknown")
            effect_data = content.get("effect_data", {})
            duration = content.get("duration", -1)  # -1 for permanent
            source = content.get("source", "unknown")

            # Apply status effect to target
            combatant = self._get_combatant(encounter_id, target_id)

            if combatant:
                status_effect = {
                    "name": effect_name,
                    "data": effect_data,
                    "duration": duration,
                    "source": source,
                    "applied_at": time.time()
                }
                combatant.status_effects.append(status_effect)

            self.stats['status_effects_applied'] += 1

            logger.debug(f"Status effect applied to {target_id}: {effect_name} (duration: {duration})")

        except Exception as e:
            logger.error(f"Error handling status effect application: {str(e)}")

    async def _handle_status_effect_remove(self, event: CombatEvent, broker_message: Message):
        """Handle status effect removal event."""
        try:
            encounter_id = event.encounter_id
            target_id = event.target_id
            content = event.content
            effect_name = content.get("effect_name", "unknown")
            reason = content.get("reason", "expired")

            # Remove status effect from target
            combatant = self._get_combatant(encounter_id, target_id)

            if combatant:
                combatant.status_effects = [
                    effect for effect in combatant.status_effects
                    if effect["name"] != effect_name
                ]

            logger.debug(f"Status effect removed from {target_id}: {effect_name} ({reason})")

        except Exception as e:
            logger.error(f"Error handling status effect removal: {str(e)}")

    async def _handle_movement(self, event: CombatEvent, broker_message: Message):
        """Handle movement event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id
            content = event.content
            distance = content.get("distance", 0)
            from_position = content.get("from_position", {})
            to_position = content.get("to_position", {})
            movement_type = content.get("movement_type", "walk")

            # Update combatant movement
            combatant = self._get_combatant(encounter_id, combatant_id)

            if combatant:
                combatant.movement_remaining = max(0, combatant.movement_remaining - distance)

            logger.debug(f"Movement: {combatant_id} moved {distance} feet ({movement_type})")

        except Exception as e:
            logger.error(f"Error handling movement: {str(e)}")

    async def _handle_action_use(self, event: CombatEvent, broker_message: Message):
        """Handle action use event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id
            content = event.content
            action_type = content.get("action_type", "attack")
            action_cost = content.get("action_cost", 1)  # 1 for action, 0.5 for bonus action

            combatant = self._get_combatant(encounter_id, combatant_id)

            if combatant:
                if action_cost == 1:
                    combatant.actions_used += 1
                elif action_cost == 0.5:
                    combatant.bonus_actions_used += 1

            logger.debug(f"Action used by {combatant_id}: {action_type} (cost: {action_cost})")

        except Exception as e:
            logger.error(f"Error handling action use: {str(e)}")

    async def _handle_spell_cast(self, event: CombatEvent, broker_message: Message):
        """Handle spell cast event."""
        try:
            encounter_id = event.encounter_id
            caster_id = event.source_id
            content = event.content
            spell_name = content.get("spell_name", "unknown")
            spell_level = content.get("spell_level", 1)
            targets = content.get("targets", [])
            components = content.get("components", [])

            logger.debug(f"Spell cast: {caster_id} cast {spell_name} (level {spell_level})")

            # Process spell effects
            await self._process_spell_effects(encounter_id, caster_id, spell_name, spell_level, targets, components)

        except Exception as e:
            logger.error(f"Error handling spell cast: {str(e)}")

    async def _handle_ability_use(self, event: CombatEvent, broker_message: Message):
        """Handle ability use event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id
            content = event.content
            ability_name = content.get("ability_name", "unknown")
            ability_type = content.get("ability_type", "special")
            targets = content.get("targets", [])

            logger.debug(f"Ability used by {combatant_id}: {ability_name} ({ability_type})")

            # Process ability effects
            await self._process_ability_effects(encounter_id, combatant_id, ability_name, ability_type, targets)

        except Exception as e:
            logger.error(f"Error handling ability use: {str(e)}")

    async def _handle_critical_hit(self, event: CombatEvent, broker_message: Message):
        """Handle critical hit event."""
        try:
            encounter_id = event.encounter_id
            attacker_id = event.source_id
            target_id = event.target_id
            content = event.content
            damage_multipler = content.get("damage_multiplier", 2.0)
            additional_effects = content.get("additional_effects", [])

            logger.info(f"CRITICAL HIT! {attacker_id} critically hit {target_id}")

            # Process critical hit effects
            await self._process_critical_hit_effects(encounter_id, attacker_id, target_id, damage_multipler, additional_effects)

        except Exception as e:
            logger.error(f"Error handling critical hit: {str(e)}")

    async def _handle_fumble(self, event: CombatEvent, broker_message: Message):
        """Handle fumble event."""
        try:
            encounter_id = event.encounter_id
            combatant_id = event.source_id
            content = event.content
            fumble_type = content.get("fumble_type", "miss")
            consequences = content.get("consequences", [])

            logger.warning(f"FUMBLE! {combatant_id} fumbled ({fumble_type})")

            # Process fumble consequences
            await self._process_fumble_consequences(encounter_id, combatant_id, fumble_type, consequences)

        except Exception as e:
            logger.error(f"Error handling fumble: {str(e)}")

    async def _handle_combat_log(self, event: CombatEvent, broker_message: Message):
        """Handle combat log event."""
        try:
            content = event.content
            log_message = content.get("message", "")
            log_level = content.get("level", "info")
            details = content.get("details", {})

            # Log combat message
            if log_level == "debug":
                logger.debug(f"Combat Log [{event.encounter_id}]: {log_message}")
            elif log_level == "info":
                logger.info(f"Combat Log [{event.encounter_id}]: {log_message}")
            elif log_level == "warning":
                logger.warning(f"Combat Log [{event.encounter_id}]: {log_message}")
            elif log_level == "error":
                logger.error(f"Combat Log [{event.encounter_id}]: {log_message}")

        except Exception as e:
            logger.error(f"Error handling combat log: {str(e)}")

    async def _change_encounter_phase(self, encounter_id: str, new_phase: CombatPhase):
        """Change the phase of a combat encounter."""
        try:
            if encounter_id not in self.active_encounters:
                return

            encounter = self.active_encounters[encounter_id]
            old_phase = encounter.phase
            encounter.phase = new_phase

            # Call phase handler
            if new_phase in self.phase_handlers:
                handler = self.phase_handlers[new_phase]
                await handler(encounter)

            # Publish phase change event
            phase_event = CombatEvent(
                event_id=f"phase_change_{int(time.time())}",
                event_type=CombatEventType.COMBAT_LOG,
                encounter_id=encounter_id,
                content={
                    "message": f"Combat phase changed: {old_phase.value} -> {new_phase.value}",
                    "level": "info",
                    "old_phase": old_phase.value,
                    "new_phase": new_phase.value
                },
                priority=MessagePriority.NORMAL
            )

            await self._publish_combat_event(phase_event)

        except Exception as e:
            logger.error(f"Error changing encounter phase: {str(e)}")

    async def _determine_turn_order(self, encounter_id: str):
        """Determine turn order based on initiative."""
        try:
            if encounter_id not in self.active_encounters:
                return

            encounter = self.active_encounters[encounter_id]

            # Sort participants by initiative (descending)
            sorted_participants = sorted(
                encounter.participants,
                key=lambda p: (p.initiative, p.name),
                reverse=True
            )

            # Set turn order
            encounter.turn_order = [p.combatant_id for p in sorted_participants]

            # Change to active phase
            await self._change_encounter_phase(encounter_id, CombatPhase.ACTIVE)

            # Publish turn order
            turn_order_event = CombatEvent(
                event_id=f"turn_order_{int(time.time())}",
                event_type=CombatEventType.COMBAT_LOG,
                encounter_id=encounter_id,
                content={
                    "message": f"Turn order determined: {', '.join(encounter.turn_order)}",
                    "level": "info",
                    "turn_order": encounter.turn_order
                },
                priority=MessagePriority.NORMAL
            )

            await self._publish_combat_event(turn_order_event)

        except Exception as e:
            logger.error(f"Error determining turn order: {str(e)}")

    def _get_combatant(self, encounter_id: str, combatant_id: str) -> Optional[Combatant]:
        """Get a combatant by ID."""
        if encounter_id not in self.active_encounters:
            return None

        encounter = self.active_encounters[encounter_id]
        for combatant in encounter.participants:
            if combatant.combatant_id == combatant_id:
                return combatant

        return None

    async def _process_end_of_round_effects(self, encounter_id: str):
        """Process end-of-round effects for all combatants."""
        try:
            if encounter_id not in self.active_encounters:
                return

            encounter = self.active_encounters[encounter_id]

            for combatant in encounter.participants:
                # Process status effects with duration
                remaining_effects = []
                for effect in combatant.status_effects:
                    if effect["duration"] > 0:
                        effect["duration"] -= 1
                        remaining_effects.append(effect)
                    elif effect["duration"] == 0:
                        # Effect expired - remove it
                        logger.debug(f"Status effect expired for {combatant.combatant_id}: {effect['name']}")
                combatant.status_effects = remaining_effects

                # Process regeneration effects
                if any(e["name"] == "regeneration" for e in combatant.status_effects):
                    regen_amount = 5  # Default regeneration amount
                    combatant.current_hp = min(combatant.max_hp, combatant.current_hp + regen_amount)

        except Exception as e:
            logger.error(f"Error processing end-of-round effects: {str(e)}")

    async def _process_end_of_turn_effects(self, encounter_id: str, combatant_id: str):
        """Process end-of-turn effects for a specific combatant."""
        try:
            combatant = self._get_combatant(encounter_id, combatant_id)
            if not combatant:
                return

            # Reset concentration check
            combatant.concentration = False

        except Exception as e:
            logger.error(f"Error processing end-of-turn effects: {str(e)}")

    async def _process_attack_declaration(self, encounter_id: str, attacker_id: str, target_id: str,
                                       attack_type: str, weapon: Dict[str, Any], modifiers: Dict[str, Any]):
        """Process attack declaration."""
        # This would typically trigger attack roll calculations
        pass

    async def _process_attack_resolution(self, encounter_id: str, attacker_id: str, target_id: str,
                                      attack_roll: int, hit: bool, critical: bool,
                                      damage_rolls: List[int], ac: int):
        """Process attack resolution."""
        if hit and critical:
            # Trigger critical hit processing
            critical_event = CombatEvent(
                event_id=f"critical_{int(time.time())}",
                event_type=CombatEventType.CRITICAL_HIT,
                encounter_id=encounter_id,
                source_id=attacker_id,
                target_id=target_id,
                content={
                    "damage_multiplier": 2.0,
                    "attack_roll": attack_roll,
                    "damage_rolls": damage_rolls
                },
                priority=MessagePriority.HIGH
            )

            await self._publish_combat_event(critical_event)

    async def _process_spell_effects(self, encounter_id: str, caster_id: str, spell_name: str,
                                  spell_level: int, targets: List[str], components: List[str]):
        """Process spell effects."""
        # This would handle spell-specific logic
        pass

    async def _process_ability_effects(self, encounter_id: str, combatant_id: str, ability_name: str,
                                    ability_type: str, targets: List[str]):
        """Process ability effects."""
        # This would handle ability-specific logic
        pass

    async def _process_critical_hit_effects(self, encounter_id: str, attacker_id: str, target_id: str,
                                         damage_multiplier: float, additional_effects: List[Dict[str, Any]]):
        """Process critical hit effects."""
        # This would handle critical hit specific effects
        pass

    async def _process_fumble_consequences(self, encounter_id: str, combatant_id: str,
                                        fumble_type: str, consequences: List[Dict[str, Any]]):
        """Process fumble consequences."""
        # This would handle fumble specific consequences
        pass

    async def _handle_combatant_defeated(self, encounter_id: str, combatant_id: str):
        """Handle combatant defeat (0 HP or less)."""
        try:
            combatant = self._get_combatant(encounter_id, combatant_id)
            if combatant:
                combatant.conditions.append("unconscious")

                # Publish defeat event
                defeat_event = CombatEvent(
                    event_id=f"defeat_{int(time.time())}",
                    event_type=CombatEventType.COMBAT_LOG,
                    encounter_id=encounter_id,
                    target_id=combatant_id,
                    content={
                        "message": f"{combatant.name} has been defeated!",
                        "level": "warning",
                        "defeated_combatant": combatant.combatant_id,
                        "current_hp": combatant.current_hp
                    },
                    priority=MessagePriority.HIGH
                )

                await self._publish_combat_event(defeat_event)

        except Exception as e:
            logger.error(f"Error handling combatant defeat: {str(e)}")

    async def _publish_combat_event(self, event: CombatEvent):
        """Publish a combat event."""
        try:
            message = Message(
                type=MessageType.COMBAT_EVENT,
                topic=f"combat.event.{event.event_type.value}",
                payload={
                    "event": event.__dict__,
                    "instance_id": self.instance_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "encounter_id": event.encounter_id,
                    "source_id": event.source_id or "",
                    "target_id": event.target_id or "",
                    "instance_id": self.instance_id
                },
                priority=event.priority,
                source="combat_consumer"
            )

            await self.broker.publish(message, f"combat.event.{event.event_type.value}")

        except Exception as e:
            logger.error(f"Error publishing combat event: {str(e)}")

    async def _publish_combat_summary(self, encounter_id: str, summary_data: Dict[str, Any]):
        """Publish combat summary."""
        try:
            message = Message(
                type=MessageType.COMBAT_EVENT,
                topic=f"combat.encounter.{encounter_id}.summary",
                payload={
                    "summary": summary_data,
                    "instance_id": self.instance_id
                },
                headers={
                    "encounter_id": encounter_id,
                    "message_type": "combat_summary",
                    "instance_id": self.instance_id
                },
                priority=MessagePriority.NORMAL,
                source="combat_consumer"
            )

            await self.broker.publish(message, f"combat.encounter.{encounter_id}.summary")

        except Exception as e:
            logger.error(f"Error publishing combat summary: {str(e)}")

    async def _cleanup_loop(self):
        """Cleanup loop for inactive encounters."""
        while True:
            try:
                current_time = time.time()
                inactive_threshold = 1800  # 30 minutes

                inactive_encounters = []
                for encounter_id, encounter in self.active_encounters.items():
                    if current_time - encounter.last_activity > inactive_threshold:
                        inactive_encounters.append(encounter_id)

                for encounter_id in inactive_encounters:
                    logger.warning(f"Cleaning up inactive combat encounter {encounter_id}")
                    await self._end_combat_encounter(encounter_id, "timeout")

                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(300)

    async def _end_combat_encounter(self, encounter_id: str, reason: str):
        """End a combat encounter."""
        try:
            if encounter_id in self.active_encounters:
                encounter = self.active_encounters[encounter_id]

                # Publish end event
                end_event = CombatEvent(
                    event_id=f"combat_end_{int(time.time())}",
                    event_type=CombatEventType.COMBAT_END,
                    encounter_id=encounter_id,
                    content={
                        "outcome": "abandoned",
                        "reason": reason,
                        "total_rounds": encounter.current_round,
                        "duration": time.time() - encounter.started_at
                    },
                    priority=MessagePriority.NORMAL
                )

                await self._publish_combat_event(end_event)

                # Remove from active encounters
                del self.active_encounters[encounter_id]

                logger.info(f"Combat encounter {encounter_id} ended due to {reason}")

        except Exception as e:
            logger.error(f"Error ending combat encounter {encounter_id}: {str(e)}")

    # Phase handlers
    async def _handle_setup_phase(self, encounter: CombatEncounter):
        """Handle setup phase."""
        logger.debug(f"Setup phase for encounter {encounter.encounter_id}")

    async def _handle_initiative_phase(self, encounter: CombatEncounter):
        """Handle initiative phase."""
        logger.debug(f"Initiative phase for encounter {encounter.encounter_id}")

    async def _handle_active_phase(self, encounter: CombatEncounter):
        """Handle active phase."""
        logger.debug(f"Active phase for encounter {encounter.encounter_id}")

    async def _handle_resolution_phase(self, encounter: CombatEncounter):
        """Handle resolution phase."""
        logger.debug(f"Resolution phase for encounter {encounter.encounter_id}")

    async def _handle_cleanup_phase(self, encounter: CombatEncounter):
        """Handle cleanup phase."""
        logger.debug(f"Cleanup phase for encounter {encounter.encounter_id}")

    def register_event_handler(self, event_type: CombatEventType, handler: Callable):
        """Register custom event handler."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered custom handler for combat event type: {event_type.value}")

    def register_phase_handler(self, phase: CombatPhase, handler: Callable):
        """Register custom phase handler."""
        self.phase_handlers[phase] = handler
        logger.info(f"Registered custom handler for combat phase: {phase.value}")

    def get_active_encounters(self) -> Dict[str, CombatEncounter]:
        """Get all active combat encounters."""
        return self.active_encounters.copy()

    def get_encounter(self, encounter_id: str) -> Optional[CombatEncounter]:
        """Get a specific combat encounter."""
        return self.active_encounters.get(encounter_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            **self.stats,
            'active_encounters': len(self.active_encounters),
            'instance_id': self.instance_id
        }

    async def shutdown(self):
        """Shutdown the combat consumer gracefully."""
        try:
            await self.stop_consuming()

            # End all active encounters
            encounter_ids = list(self.active_encounters.keys())
            for encounter_id in encounter_ids:
                await self._end_combat_encounter(encounter_id, "shutdown")

            # Clear data
            self.active_encounters.clear()
            self.event_handlers.clear()
            self.phase_handlers.clear()

            logger.info(f"Combat consumer {self.instance_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during combat consumer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'CombatConsumer',
    'CombatEvent',
    'CombatEncounter',
    'Combatant',
    'CombatEventType',
    'CombatPhase'
]