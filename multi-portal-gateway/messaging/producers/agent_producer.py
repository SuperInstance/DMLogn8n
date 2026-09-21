#!/usr/bin/env python3
"""
Agent Producer - Handles agent-to-agent communication messages.

This producer manages messages for agent communication including:
- Direct agent messages
- Agent group broadcasts
- Agent state updates
- Agent capability announcements
- Agent discovery and registration
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


class AgentMessageType(Enum):
    """Specific agent message types."""
    DIRECT_MESSAGE = "direct_message"
    GROUP_BROADCAST = "group_broadcast"
    STATE_UPDATE = "state_update"
    CAPABILITY_ANNOUNCEMENT = "capability_announcement"
    DISCOVERY_REQUEST = "discovery_request"
    DISCOVERY_RESPONSE = "discovery_response"
    HEARTBEAT = "heartbeat"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    ERROR_REPORT = "error_report"
    SHUTDOWN_NOTIFICATION = "shutdown_notification"


@dataclass
class AgentInfo:
    """Agent information structure."""
    id: str
    name: str
    type: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "active"  # active, inactive, busy, error
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    groups: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None
    load_average: float = 0.0
    active_tasks: int = 0
    max_concurrent_tasks: int = 10


@dataclass
class AgentMessage:
    """Agent-specific message structure."""
    sender_id: str
    recipient_id: Optional[str] = None
    group_id: Optional[str] = None
    message_type: AgentMessageType = AgentMessageType.DIRECT_MESSAGE
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    requires_ack: bool = True
    expires_at: Optional[float] = None


class AgentProducer:
    """
    Producer for agent communication messages.
    """

    def __init__(self, message_broker: MessageBroker, agent_id: str):
        self.broker = message_broker
        self.agent_id = agent_id
        self.agent_info = AgentInfo(id=agent_id, name=f"Agent-{agent_id}", type="generic")
        self.pending_messages: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[str, callable] = {}
        self.groups: List[str] = []
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'direct_messages': 0,
            'group_messages': 0,
            'broadcasts': 0,
            'errors': 0
        }

    async def initialize(self, agent_info: Optional[AgentInfo] = None):
        """Initialize the agent producer."""
        if agent_info:
            self.agent_info = agent_info

        # Declare agent-specific exchange
        exchange_config = ExchangeConfig(
            name="agent.exchange",
            type="topic",
            durable=True
        )
        await self.broker.declare_exchange(exchange_config)

        # Declare agent queue for direct messages
        queue_config = QueueConfig(
            name=f"agent.{self.agent_id}.inbox",
            durable=True,
            arguments={
                "x-message-ttl": 300000,  # 5 minutes TTL
                "x-max-length": 1000      # Max 1000 messages
            }
        )
        await self.broker.declare_queue(queue_config)

        # Bind queue to exchange
        await self.broker.bind_queue(
            queue_config.name,
            exchange_config.name,
            f"agent.{self.agent_id}.#"
        )

        logger.info(f"Initialized agent producer for {self.agent_id}")

    async def send_direct_message(self, recipient_id: str, content: Dict[str, Any],
                                 message_type: AgentMessageType = AgentMessageType.DIRECT_MESSAGE,
                                 priority: MessagePriority = MessagePriority.NORMAL,
                                 requires_ack: bool = True,
                                 timeout: Optional[float] = None) -> bool:
        """
        Send a direct message to another agent.

        Args:
            recipient_id: ID of the recipient agent
            content: Message content
            message_type: Type of agent message
            priority: Message priority
            requires_ack: Whether acknowledgment is required
            timeout: Timeout for response (if applicable)

        Returns:
            bool: True if message sent successfully
        """
        try:
            agent_msg = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
                priority=priority,
                requires_ack=requires_ack
            )

            # Create broker message
            message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.{recipient_id}.direct",
                payload={
                    "agent_message": agent_msg.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": recipient_id,
                    "message_type": message_type.value,
                    "requires_ack": str(requires_ack)
                },
                priority=priority,
                source=self.agent_id,
                destination=recipient_id,
                reply_to=f"agent.{self.agent_id}.responses" if requires_ack else None
            )

            # Set up response future if acknowledgment required
            if requires_ack:
                future = asyncio.Future()
                self.pending_messages[message.id] = future

                # Set timeout if specified
                if timeout:
                    asyncio.create_task(self._timeout_response(message.id, timeout))

            # Send message
            success = await self.broker.publish(message, f"agent.{recipient_id}.direct")

            if success:
                self.stats['messages_sent'] += 1
                self.stats['direct_messages'] += 1
                logger.debug(f"Sent direct message from {self.agent_id} to {recipient_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send direct message to {recipient_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def send_group_message(self, group_id: str, content: Dict[str, Any],
                               message_type: AgentMessageType = AgentMessageType.GROUP_BROADCAST,
                               priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Send a message to all agents in a group.

        Args:
            group_id: ID of the target group
            content: Message content
            message_type: Type of agent message
            priority: Message priority

        Returns:
            bool: True if message sent successfully
        """
        try:
            agent_msg = AgentMessage(
                sender_id=self.agent_id,
                group_id=group_id,
                message_type=message_type,
                content=content,
                priority=priority,
                requires_ack=False  # Group messages typically don't require individual ACKs
            )

            message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.group.{group_id}.broadcast",
                payload={
                    "agent_message": agent_msg.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "group_id": group_id,
                    "message_type": message_type.value
                },
                priority=priority,
                source=self.agent_id,
                destination=f"group:{group_id}"
            )

            success = await self.broker.publish(message, f"agent.group.{group_id}.broadcast")

            if success:
                self.stats['messages_sent'] += 1
                self.stats['group_messages'] += 1
                logger.debug(f"Sent group message to {group_id} from {self.agent_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send group message to {group_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def send_broadcast(self, content: Dict[str, Any],
                           message_type: AgentMessageType = AgentMessageType.CAPABILITY_ANNOUNCEMENT,
                           priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Send a broadcast message to all agents.

        Args:
            content: Message content
            message_type: Type of agent message
            priority: Message priority

        Returns:
            bool: True if message sent successfully
        """
        try:
            agent_msg = AgentMessage(
                sender_id=self.agent_id,
                message_type=message_type,
                content=content,
                priority=priority,
                requires_ack=False
            )

            message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic="agent.broadcast.all",
                payload={
                    "agent_message": agent_msg.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "message_type": message_type.value,
                    "broadcast": "true"
                },
                priority=priority,
                source=self.agent_id
            )

            success = await self.broker.publish(message, "agent.broadcast.all")

            if success:
                self.stats['messages_sent'] += 1
                self.stats['broadcasts'] += 1
                logger.debug(f"Sent broadcast from {self.agent_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send broadcast: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def announce_capabilities(self, capabilities: List[str]) -> bool:
        """
        Announce agent capabilities to the network.

        Args:
            capabilities: List of agent capabilities

        Returns:
            bool: True if announcement sent successfully
        """
        # Update agent info
        self.agent_info.capabilities = capabilities

        content = {
            "agent_id": self.agent_id,
            "capabilities": capabilities,
            "timestamp": time.time()
        }

        return await self.send_broadcast(
            content=content,
            message_type=AgentMessageType.CAPABILITY_ANNOUNCEMENT,
            priority=MessagePriority.NORMAL
        )

    async def update_state(self, state_updates: Dict[str, Any]) -> bool:
        """
        Send agent state update.

        Args:
            state_updates: Dictionary of state updates

        Returns:
            bool: True if update sent successfully
        """
        # Update agent info
        for key, value in state_updates.items():
            if hasattr(self.agent_info, key):
                setattr(self.agent_info, key, value)

        content = {
            "agent_id": self.agent_id,
            "state_updates": state_updates,
            "timestamp": time.time()
        }

        return await self.send_broadcast(
            content=content,
            message_type=AgentMessageType.STATE_UPDATE,
            priority=MessagePriority.LOW
        )

    async def send_heartbeat(self) -> bool:
        """Send heartbeat message."""
        self.agent_info.last_heartbeat = time.time()

        content = {
            "agent_id": self.agent_id,
            "status": self.agent_info.status,
            "load_average": self.agent_info.load_average,
            "active_tasks": self.agent_info.active_tasks,
            "timestamp": self.agent_info.last_heartbeat
        }

        return await self.send_broadcast(
            content=content,
            message_type=AgentMessageType.HEARTBEAT,
            priority=MessagePriority.LOW
        )

    async def discover_agents(self, capability_filter: Optional[List[str]] = None,
                            timeout: float = 10.0) -> List[AgentInfo]:
        """
        Discover other agents in the network.

        Args:
            capability_filter: Optional filter for agent capabilities
            timeout: Discovery timeout in seconds

        Returns:
            List[AgentInfo]: List of discovered agents
        """
        try:
            # Send discovery request
            discovery_id = f"discovery_{self.agent_id}_{int(time.time())}"
            content = {
                "request_id": discovery_id,
                "requester_id": self.agent_id,
                "capability_filter": capability_filter,
                "timestamp": time.time()
            }

            # Set up response collection
            discovered_agents = []
            response_future = asyncio.Future()

            # Store response handler
            self.message_handlers[discovery_id] = response_future

            # Send discovery request
            await self.send_broadcast(
                content=content,
                message_type=AgentMessageType.DISCOVERY_REQUEST,
                priority=MessagePriority.HIGH
            )

            # Wait for responses
            try:
                responses = await asyncio.wait_for(response_future, timeout=timeout)
                for response in responses:
                    if isinstance(response, dict) and "agent_info" in response:
                        agent_info = AgentInfo(**response["agent_info"])

                        # Apply capability filter if specified
                        if capability_filter:
                            if any(cap in agent_info.capabilities for cap in capability_filter):
                                discovered_agents.append(agent_info)
                        else:
                            discovered_agents.append(agent_info)

            except asyncio.TimeoutError:
                logger.warning(f"Discovery request timed out after {timeout} seconds")

            finally:
                # Clean up response handler
                if discovery_id in self.message_handlers:
                    del self.message_handlers[discovery_id]

            logger.info(f"Discovered {len(discovered_agents)} agents")
            return discovered_agents

        except Exception as e:
            logger.error(f"Failed to discover agents: {str(e)}")
            return []

    async def join_group(self, group_id: str) -> bool:
        """
        Join an agent group.

        Args:
            group_id: ID of the group to join

        Returns:
            bool: True if joined successfully
        """
        try:
            if group_id not in self.groups:
                self.groups.append(group_id)
                self.agent_info.groups.append(group_id)

                # Send group join notification
                content = {
                    "agent_id": self.agent_id,
                    "group_id": group_id,
                    "action": "join",
                    "timestamp": time.time()
                }

                success = await self.send_group_message(
                    group_id=group_id,
                    content=content,
                    message_type=AgentMessageType.DIRECT_MESSAGE,
                    priority=MessagePriority.NORMAL
                )

                if success:
                    logger.info(f"Agent {self.agent_id} joined group {group_id}")

                return success

            return True  # Already in group

        except Exception as e:
            logger.error(f"Failed to join group {group_id}: {str(e)}")
            return False

    async def leave_group(self, group_id: str) -> bool:
        """
        Leave an agent group.

        Args:
            group_id: ID of the group to leave

        Returns:
            bool: True if left successfully
        """
        try:
            if group_id in self.groups:
                self.groups.remove(group_id)
                if group_id in self.agent_info.groups:
                    self.agent_info.groups.remove(group_id)

                # Send group leave notification
                content = {
                    "agent_id": self.agent_id,
                    "group_id": group_id,
                    "action": "leave",
                    "timestamp": time.time()
                }

                success = await self.send_group_message(
                    group_id=group_id,
                    content=content,
                    message_type=AgentMessageType.DIRECT_MESSAGE,
                    priority=MessagePriority.NORMAL
                )

                if success:
                    logger.info(f"Agent {self.agent_id} left group {group_id}")

                return success

            return True  # Not in group

        except Exception as e:
            logger.error(f"Failed to leave group {group_id}: {str(e)}")
            return False

    async def handle_discovery_response(self, message: Message):
        """Handle discovery response messages."""
        try:
            payload = message.payload
            if "agent_info" in payload and "request_id" in payload:
                request_id = payload["request_id"]

                if request_id in self.message_handlers:
                    future = self.message_handlers[request_id]

                    if not future.done():
                        # Collect responses
                        if not hasattr(future, '_responses'):
                            future._responses = []
                        future._responses.append(payload)

                        # Complete after a short delay to collect multiple responses
                        async def complete_after_delay():
                            await asyncio.sleep(1.0)
                            if not future.done():
                                future.set_result(future._responses)

                        asyncio.create_task(complete_after_delay())

        except Exception as e:
            logger.error(f"Failed to handle discovery response: {str(e)}")

    async def handle_message_response(self, message: Message):
        """Handle message responses/acknowledgments."""
        try:
            if message.correlation_id and message.correlation_id in self.pending_messages:
                future = self.pending_messages[message.correlation_id]

                if not future.done():
                    future.set_result(message.payload)

                # Clean up
                del self.pending_messages[message.correlation_id]

        except Exception as e:
            logger.error(f"Failed to handle message response: {str(e)}")

    async def _timeout_response(self, message_id: str, timeout: float):
        """Handle response timeout."""
        await asyncio.sleep(timeout)

        if message_id in self.pending_messages:
            future = self.pending_messages[message_id]

            if not future.done():
                future.set_exception(asyncio.TimeoutError(f"Message response timed out after {timeout} seconds"))

            del self.pending_messages[message_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics."""
        return {
            **self.stats,
            'pending_messages': len(self.pending_messages),
            'groups': self.groups.copy(),
            'agent_info': self.agent_info.__dict__
        }

    async def shutdown(self):
        """Shutdown the agent producer gracefully."""
        try:
            # Send shutdown notification
            content = {
                "agent_id": self.agent_id,
                "timestamp": time.time()
            }

            await self.send_broadcast(
                content=content,
                message_type=AgentMessageType.SHUTDOWN_NOTIFICATION,
                priority=MessagePriority.HIGH
            )

            # Cancel pending message futures
            for message_id, future in self.pending_messages.items():
                if not future.done():
                    future.cancel()

            self.pending_messages.clear()
            self.message_handlers.clear()

            logger.info(f"Agent producer {self.agent_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during agent producer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'AgentProducer',
    'AgentMessage',
    'AgentInfo',
    'AgentMessageType'
]