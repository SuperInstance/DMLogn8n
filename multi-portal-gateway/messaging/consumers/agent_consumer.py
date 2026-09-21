#!/usr/bin/env python3
"""
Agent Consumer - Handles agent communication message consumption.

This consumer processes agent-related messages including:
- Direct agent messages
- Group broadcasts
- Agent state updates
- Capability announcements
- Discovery requests and responses
- Heartbeat messages
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
from ..producers.agent_producer import AgentMessage, AgentMessageType, AgentInfo

logger = logging.getLogger(__name__)


class MessageProcessingResult(Enum):
    """Message processing result types."""
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    IGNORE = "ignore"
    DEAD_LETTER = "dead_letter"


@dataclass
class ConsumerStats:
    """Consumer statistics."""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    messages_ignored: int = 0
    messages_retried: int = 0
    messages_dead_lettered: int = 0
    processing_time_total: float = 0.0
    average_processing_time: float = 0.0
    last_message_time: float = 0.0
    errors: List[str] = field(default_factory=list)


class AgentConsumer:
    """
    Consumer for agent communication messages.
    """

    def __init__(self, message_broker: MessageBroker, agent_id: str):
        self.broker = message_broker
        self.agent_id = agent_id
        self.agent_info = AgentInfo(id=agent_id, name=f"Agent-{agent_id}", type="generic")
        self.message_handlers: Dict[AgentMessageType, Callable] = {}
        self.group_handlers: Dict[str, Callable] = {}
        self.subscribed_groups: Set[str] = set()
        self.consuming = False
        self.consumer_task: Optional[asyncio.Task] = None
        self.stats = ConsumerStats()
        self.dead_letter_queue = f"agent.{self.agent_id}.dlq"
        self.retry_queue = f"agent.{self.agent_id}.retry"
        self.max_retries = 3
        self.retry_delay = 5.0  # seconds

    async def initialize(self, agent_info: Optional[AgentInfo] = None):
        """Initialize the agent consumer."""
        if agent_info:
            self.agent_info = agent_info

        # Declare agent-specific queues
        await self._setup_queues()

        # Register default handlers
        self._register_default_handlers()

        logger.info(f"Initialized agent consumer for {self.agent_id}")

    async def _setup_queues(self):
        """Setup consumer queues."""
        try:
            # Main inbox queue
            inbox_config = QueueConfig(
                name=f"agent.{self.agent_id}.inbox",
                durable=True,
                arguments={
                    "x-message-ttl": 300000,  # 5 minutes TTL
                    "x-max-length": 1000,     # Max 1000 messages
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": self.dead_letter_queue
                }
            )
            await self.broker.declare_queue(inbox_config)

            # Retry queue
            retry_config = QueueConfig(
                name=self.retry_queue,
                durable=True,
                arguments={
                    "x-message-ttl": int(self.retry_delay * 1000),  # Convert to milliseconds
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": f"agent.{self.agent_id}.inbox"
                }
            )
            await self.broker.declare_queue(retry_config)

            # Dead letter queue
            dlq_config = QueueConfig(
                name=self.dead_letter_queue,
                durable=True,
                arguments={
                    "x-message-ttl": 604800000  # 7 days TTL
                }
            )
            await self.broker.declare_queue(dlq_config)

            # Group queues for subscribed groups
            for group_id in self.subscribed_groups:
                group_queue = QueueConfig(
                    name=f"agent.group.{group_id}.members",
                    durable=True,
                    arguments={
                        "x-message-ttl": 300000
                    }
                )
                await self.broker.declare_queue(group_queue)

        except Exception as e:
            logger.error(f"Failed to setup queues for agent {self.agent_id}: {str(e)}")
            raise

    def _register_default_handlers(self):
        """Register default message handlers."""
        self.message_handlers[AgentMessageType.DIRECT_MESSAGE] = self._handle_direct_message
        self.message_handlers[AgentMessageType.GROUP_BROADCAST] = self._handle_group_message
        self.message_handlers[AgentMessageType.STATE_UPDATE] = self._handle_state_update
        self.message_handlers[AgentMessageType.CAPABILITY_ANNOUNCEMENT] = self._handle_capability_announcement
        self.message_handlers[AgentMessageType.DISCOVERY_REQUEST] = self._handle_discovery_request
        self.message_handlers[AgentMessageType.DISCOVERY_RESPONSE] = self._handle_discovery_response
        self.message_handlers[AgentMessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[AgentMessageType.TASK_REQUEST] = self._handle_task_request
        self.message_handlers[AgentMessageType.TASK_RESPONSE] = self._handle_task_response
        self.message_handlers[AgentMessageType.COLLABORATION_REQUEST] = self._handle_collaboration_request
        self.message_handlers[AgentMessageType.COLLABORATION_RESPONSE] = self._handle_collaboration_response
        self.message_handlers[AgentMessageType.ERROR_REPORT] = self._handle_error_report
        self.message_handlers[AgentMessageType.SHUTDOWN_NOTIFICATION] = self._handle_shutdown_notification

    async def start_consuming(self):
        """Start consuming messages."""
        if self.consuming:
            logger.warning(f"Agent {self.agent_id} is already consuming")
            return

        try:
            self.consuming = True

            # Start consumer task
            self.consumer_task = asyncio.create_task(self._consume_loop())

            logger.info(f"Agent {self.agent_id} started consuming messages")

        except Exception as e:
            logger.error(f"Failed to start consuming for agent {self.agent_id}: {str(e)}")
            self.consuming = False
            raise

    async def stop_consuming(self):
        """Stop consuming messages."""
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

            logger.info(f"Agent {self.agent_id} stopped consuming messages")

        except Exception as e:
            logger.error(f"Error stopping consumption for agent {self.agent_id}: {str(e)}")

    async def _consume_loop(self):
        """Main consumption loop."""
        while self.consuming:
            try:
                # Create consumer config
                consumer_config = ConsumerConfig(
                    queue=f"agent.{self.agent_id}.inbox",
                    prefetch_count=10,
                    auto_ack=False,
                    consumer_tag=f"agent_{self.agent_id}_consumer"
                )

                # Start consuming
                await self.broker.consume(consumer_config, self._handle_message)

                # Keep the loop running
                while self.consuming:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in consume loop for agent {self.agent_id}: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _handle_message(self, message: Message):
        """Handle incoming message."""
        start_time = time.time()
        self.stats.messages_received += 1
        self.stats.last_message_time = start_time

        try:
            # Parse agent message from payload
            payload = message.payload
            if "agent_message" not in payload:
                logger.warning(f"Message {message.id} missing agent_message in payload")
                await self._send_to_dead_letter(message, "Missing agent_message")
                return

            agent_message_data = payload["agent_message"]
            agent_message = AgentMessage(**agent_message_data)

            # Determine message type and call appropriate handler
            message_type = AgentMessageType(agent_message.message_type)

            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                result = await handler(agent_message, message)

                # Handle processing result
                if result == MessageProcessingResult.SUCCESS:
                    await self.broker.ack_message(message.delivery_tag)
                    self.stats.messages_processed += 1

                elif result == MessageProcessingResult.FAILURE:
                    await self._handle_failed_message(message, "Processing failed")

                elif result == MessageProcessingResult.RETRY:
                    await self._retry_message(message)

                elif result == MessageProcessingResult.IGNORE:
                    await self.broker.ack_message(message.delivery_tag)
                    self.stats.messages_ignored += 1

                elif result == MessageProcessingResult.DEAD_LETTER:
                    await self._send_to_dead_letter(message, "Processing resulted in dead letter")

            else:
                logger.warning(f"No handler for message type: {message_type.value}")
                await self._send_to_dead_letter(message, f"No handler for type: {message_type.value}")

        except Exception as e:
            logger.error(f"Error handling message {message.id}: {str(e)}")
            self.stats.errors.append(str(e))
            await self._handle_failed_message(message, str(e))

        finally:
            # Update processing time statistics
            processing_time = time.time() - start_time
            self.stats.processing_time_total += processing_time
            if self.stats.messages_processed > 0:
                self.stats.average_processing_time = self.stats.processing_time_total / self.stats.messages_processed

    async def _handle_direct_message(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle direct agent message."""
        try:
            logger.debug(f"Agent {self.agent_id} received direct message from {agent_message.sender_id}")

            # Check if message is for this agent
            if agent_message.recipient_id != self.agent_id:
                return MessageProcessingResult.IGNORE

            # Process message content
            content = agent_message.content

            # Handle different types of direct messages
            if "action" in content:
                action = content["action"]
                if action == "ping":
                    return await self._handle_ping(agent_message, broker_message)
                elif action == "status_request":
                    return await self._handle_status_request(agent_message, broker_message)
                elif action == "task_assignment":
                    return await self._handle_task_assignment(agent_message, broker_message)

            # Send acknowledgment if required
            if agent_message.requires_ack:
                await self._send_acknowledgment(agent_message, broker_message)

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling direct message: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_group_message(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle group broadcast message."""
        try:
            logger.debug(f"Agent {self.agent_id} received group message for {agent_message.group_id}")

            # Check if agent is member of the group
            if agent_message.group_id not in self.subscribed_groups:
                return MessageProcessingResult.IGNORE

            # Process group message
            content = agent_message.content

            if "action" in content:
                action = content["action"]
                if action == "join":
                    member_info = content.get("member_info", {})
                    logger.info(f"Agent {member_info.get('agent_id', 'unknown')} joined group {agent_message.group_id}")
                elif action == "leave":
                    member_info = content.get("member_info", {})
                    logger.info(f"Agent {member_info.get('agent_id', 'unknown')} left group {agent_message.group_id}")

            # Call custom group handler if registered
            if agent_message.group_id in self.group_handlers:
                handler = self.group_handlers[agent_message.group_id]
                await handler(agent_message, broker_message)

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling group message: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_state_update(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle agent state update."""
        try:
            logger.debug(f"Agent {self.agent_id} received state update from {agent_message.sender_id}")

            content = agent_message.content
            agent_id = content.get("agent_id")
            state_updates = content.get("state_updates", {})

            # Update local agent registry if applicable
            # In a real implementation, this would update a shared agent registry
            logger.info(f"Agent {agent_id} state updated: {state_updates}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling state update: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_capability_announcement(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle capability announcement."""
        try:
            logger.debug(f"Agent {self.agent_id} received capability announcement from {agent_message.sender_id}")

            content = agent_message.content
            agent_id = content.get("agent_id")
            capabilities = content.get("capabilities", [])

            # Update local capability registry
            logger.info(f"Agent {agent_id} capabilities: {capabilities}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling capability announcement: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_discovery_request(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle agent discovery request."""
        try:
            logger.debug(f"Agent {self.agent_id} received discovery request from {agent_message.sender_id}")

            content = agent_message.content
            request_id = content.get("request_id")
            capability_filter = content.get("capability_filter")

            # Check if this agent matches the filter
            if capability_filter:
                if not any(cap in self.agent_info.capabilities for cap in capability_filter):
                    return MessageProcessingResult.IGNORE

            # Send discovery response
            response_content = {
                "request_id": request_id,
                "agent_info": self.agent_info.__dict__,
                "timestamp": time.time()
            }

            # Create response message
            response_agent_message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=agent_message.sender_id,
                message_type=AgentMessageType.DISCOVERY_RESPONSE,
                content=response_content,
                reply_to=agent_message.reply_to,
                correlation_id=agent_message.correlation_id or request_id,
                requires_ack=False
            )

            # Send response via broker
            response_broker_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.{agent_message.sender_id}.direct",
                payload={
                    "agent_message": response_agent_message.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": agent_message.sender_id,
                    "message_type": response_agent_message.message_type.value
                },
                priority=MessagePriority.NORMAL,
                source=self.agent_id,
                destination=agent_message.sender_id
            )

            await self.broker.publish(response_broker_message, f"agent.{agent_message.sender_id}.direct")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling discovery request: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_discovery_response(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle agent discovery response."""
        try:
            logger.debug(f"Agent {self.agent_id} received discovery response from {agent_message.sender_id}")

            content = agent_message.content
            request_id = content.get("request_id")
            agent_info = content.get("agent_info")

            # In a real implementation, this would update the agent registry
            logger.info(f"Discovered agent: {agent_info.get('name', 'unknown')}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling discovery response: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_heartbeat(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle agent heartbeat."""
        try:
            logger.debug(f"Agent {self.agent_id} received heartbeat from {agent_message.sender_id}")

            content = agent_message.content
            agent_id = content.get("agent_id")
            status = content.get("status")
            load_average = content.get("load_average", 0.0)

            # Update agent status in local registry
            logger.debug(f"Agent {agent_id} heartbeat: status={status}, load={load_average}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling heartbeat: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_task_request(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle task request."""
        try:
            logger.debug(f"Agent {self.agent_id} received task request from {agent_message.sender_id}")

            content = agent_message.content
            task_id = content.get("task_id")
            task_type = content.get("task_type")
            task_data = content.get("task_data", {})

            # Process task based on capabilities
            if task_type in self.agent_info.capabilities:
                # Accept task
                logger.info(f"Agent {self.agent_id} accepted task {task_id}")

                # Send task response
                response_content = {
                    "task_id": task_id,
                    "status": "accepted",
                    "agent_id": self.agent_id,
                    "timestamp": time.time()
                }

                await self._send_task_response(agent_message, response_content)

                return MessageProcessingResult.SUCCESS
            else:
                # Reject task
                logger.info(f"Agent {self.agent_id} rejected task {task_id} (no capability)")

                response_content = {
                    "task_id": task_id,
                    "status": "rejected",
                    "reason": "Insufficient capabilities",
                    "agent_id": self.agent_id,
                    "timestamp": time.time()
                }

                await self._send_task_response(agent_message, response_content)

                return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling task request: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_task_response(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle task response."""
        try:
            logger.debug(f"Agent {self.agent_id} received task response from {agent_message.sender_id}")

            content = agent_message.content
            task_id = content.get("task_id")
            status = content.get("status")

            logger.info(f"Task {task_id} response: {status}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling task response: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_collaboration_request(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle collaboration request."""
        try:
            logger.debug(f"Agent {self.agent_id} received collaboration request from {agent_message.sender_id}")

            content = agent_message.content
            collaboration_id = content.get("collaboration_id")
            collaboration_type = content.get("collaboration_type")

            # Process collaboration request
            logger.info(f"Collaboration request: {collaboration_id} ({collaboration_type})")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling collaboration request: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_collaboration_response(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle collaboration response."""
        try:
            logger.debug(f"Agent {self.agent_id} received collaboration response from {agent_message.sender_id}")

            content = agent_message.content
            collaboration_id = content.get("collaboration_id")
            response = content.get("response")

            logger.info(f"Collaboration response: {collaboration_id} -> {response}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling collaboration response: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_error_report(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle error report."""
        try:
            logger.debug(f"Agent {self.agent_id} received error report from {agent_message.sender_id}")

            content = agent_message.content
            error_type = content.get("error_type")
            error_message = content.get("error_message")

            logger.warning(f"Error report from {agent_message.sender_id}: {error_type} - {error_message}")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling error report: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_shutdown_notification(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle shutdown notification."""
        try:
            logger.info(f"Agent {self.agent_id} received shutdown notification from {agent_message.sender_id}")

            # Update agent status in local registry
            # In a real implementation, this would update the shared agent registry

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling shutdown notification: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_ping(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle ping message."""
        try:
            # Send pong response
            response_content = {
                "action": "pong",
                "timestamp": time.time(),
                "agent_id": self.agent_id
            }

            response_agent_message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=agent_message.sender_id,
                message_type=AgentMessageType.DIRECT_MESSAGE,
                content=response_content,
                reply_to=agent_message.reply_to,
                correlation_id=agent_message.correlation_id,
                requires_ack=False
            )

            response_broker_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.{agent_message.sender_id}.direct",
                payload={
                    "agent_message": response_agent_message.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": agent_message.sender_id,
                    "message_type": response_agent_message.message_type.value
                },
                priority=MessagePriority.LOW,
                source=self.agent_id,
                destination=agent_message.sender_id
            )

            await self.broker.publish(response_broker_message, f"agent.{agent_message.sender_id}.direct")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling ping: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_status_request(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle status request."""
        try:
            response_content = {
                "action": "status_response",
                "agent_info": self.agent_info.__dict__,
                "stats": self.stats.__dict__,
                "timestamp": time.time()
            }

            response_agent_message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=agent_message.sender_id,
                message_type=AgentMessageType.DIRECT_MESSAGE,
                content=response_content,
                reply_to=agent_message.reply_to,
                correlation_id=agent_message.correlation_id,
                requires_ack=False
            )

            response_broker_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.{agent_message.sender_id}.direct",
                payload={
                    "agent_message": response_agent_message.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": agent_message.sender_id,
                    "message_type": response_agent_message.message_type.value
                },
                priority=MessagePriority.NORMAL,
                source=self.agent_id,
                destination=agent_message.sender_id
            )

            await self.broker.publish(response_broker_message, f"agent.{agent_message.sender_id}.direct")

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling status request: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _handle_task_assignment(self, agent_message: AgentMessage, broker_message: Message) -> MessageProcessingResult:
        """Handle task assignment."""
        try:
            content = agent_message.content
            task_id = content.get("task_id")
            task_data = content.get("task_data", {})

            logger.info(f"Agent {self.agent_id} assigned task {task_id}")

            # Process task assignment
            # In a real implementation, this would add the task to a task queue

            return MessageProcessingResult.SUCCESS

        except Exception as e:
            logger.error(f"Error handling task assignment: {str(e)}")
            return MessageProcessingResult.FAILURE

    async def _send_acknowledgment(self, agent_message: AgentMessage, broker_message: Message):
        """Send message acknowledgment."""
        try:
            ack_content = {
                "message_id": agent_message.correlation_id or broker_message.id,
                "status": "acknowledged",
                "agent_id": self.agent_id,
                "timestamp": time.time()
            }

            ack_agent_message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=agent_message.sender_id,
                message_type=AgentMessageType.DIRECT_MESSAGE,
                content=ack_content,
                reply_to=agent_message.reply_to,
                correlation_id=agent_message.correlation_id,
                requires_ack=False
            )

            ack_broker_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=agent_message.reply_to or f"agent.{agent_message.sender_id}.responses",
                payload={
                    "agent_message": ack_agent_message.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": agent_message.sender_id,
                    "message_type": "acknowledgment"
                },
                priority=MessagePriority.LOW,
                source=self.agent_id,
                destination=agent_message.sender_id
            )

            await self.broker.publish(ack_broker_message, ack_broker_message.topic)

        except Exception as e:
            logger.error(f"Error sending acknowledgment: {str(e)}")

    async def _send_task_response(self, original_message: AgentMessage, response_content: Dict[str, Any]):
        """Send task response."""
        try:
            response_agent_message = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=original_message.sender_id,
                message_type=AgentMessageType.TASK_RESPONSE,
                content=response_content,
                reply_to=original_message.reply_to,
                correlation_id=original_message.correlation_id,
                requires_ack=False
            )

            response_broker_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic=f"agent.{original_message.sender_id}.direct",
                payload={
                    "agent_message": response_agent_message.__dict__,
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "recipient_id": original_message.sender_id,
                    "message_type": response_agent_message.message_type.value
                },
                priority=MessagePriority.NORMAL,
                source=self.agent_id,
                destination=original_message.sender_id
            )

            await self.broker.publish(response_broker_message, f"agent.{original_message.sender_id}.direct")

        except Exception as e:
            logger.error(f"Error sending task response: {str(e)}")

    async def _handle_failed_message(self, message: Message, error_reason: str):
        """Handle failed message processing."""
        if message.retry_count < self.max_retries:
            await self._retry_message(message)
        else:
            await self._send_to_dead_letter(message, error_reason)

    async def _retry_message(self, message: Message):
        """Retry message processing."""
        try:
            # Update retry count
            message.retry_count += 1

            # Create retry message
            retry_message = Message(
                id=message.id,
                type=message.type,
                topic=message.topic,
                payload=message.payload,
                headers={**message.headers, "x-retry-count": str(message.retry_count)},
                priority=message.priority,
                timestamp=message.timestamp,
                retry_count=message.retry_count,
                max_retries=message.max_retries,
                correlation_id=message.correlation_id,
                source=message.source,
                destination=message.destination
            )

            # Send to retry queue
            await self.broker.publish(retry_message, self.retry_queue)

            # Acknowledge original message
            await self.broker.ack_message(message.delivery_tag)

            self.stats.messages_retried += 1
            logger.info(f"Retrying message {message.id} (attempt {message.retry_count})")

        except Exception as e:
            logger.error(f"Error retrying message {message.id}: {str(e)}")
            await self._send_to_dead_letter(message, f"Retry failed: {str(e)}")

    async def _send_to_dead_letter(self, message: Message, reason: str):
        """Send message to dead letter queue."""
        try:
            # Create dead letter message
            dlq_message = Message(
                id=message.id,
                type=message.type,
                topic=message.topic,
                payload={**message.payload, "dead_letter_reason": reason},
                headers={**message.headers, "x-dead-letter-reason": reason},
                priority=message.priority,
                timestamp=message.timestamp,
                retry_count=message.retry_count,
                max_retries=message.max_retries,
                correlation_id=message.correlation_id,
                source=message.source,
                destination=message.destination
            )

            # Send to dead letter queue
            await self.broker.publish(dlq_message, self.dead_letter_queue)

            # Acknowledge original message
            await self.broker.ack_message(message.delivery_tag)

            self.stats.messages_dead_lettered += 1
            logger.warning(f"Sent message {message.id} to dead letter queue: {reason}")

        except Exception as e:
            logger.error(f"Error sending message {message.id} to dead letter queue: {str(e)}")
            # Force acknowledge to prevent infinite loop
            await self.broker.ack_message(message.delivery_tag)

    def register_message_handler(self, message_type: AgentMessageType, handler: Callable):
        """Register custom message handler."""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered custom handler for message type: {message_type.value}")

    def register_group_handler(self, group_id: str, handler: Callable):
        """Register custom group message handler."""
        self.group_handlers[group_id] = handler
        logger.info(f"Registered custom handler for group: {group_id}")

    async def subscribe_to_group(self, group_id: str) -> bool:
        """Subscribe to a group."""
        try:
            if group_id not in self.subscribed_groups:
                self.subscribed_groups.add(group_id)

                # Create group queue
                group_queue = QueueConfig(
                    name=f"agent.group.{group_id}.members",
                    durable=True,
                    arguments={
                        "x-message-ttl": 300000
                    }
                )
                await self.broker.declare_queue(group_queue)

                # Bind to group exchange
                await self.broker.bind_queue(
                    group_queue.name,
                    "agent.exchange",
                    f"agent.group.{group_id}.broadcast"
                )

                logger.info(f"Agent {self.agent_id} subscribed to group {group_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to group {group_id}: {str(e)}")
            return False

    async def unsubscribe_from_group(self, group_id: str) -> bool:
        """Unsubscribe from a group."""
        try:
            if group_id in self.subscribed_groups:
                self.subscribed_groups.remove(group_id)

                # Remove custom handler if exists
                if group_id in self.group_handlers:
                    del self.group_handlers[group_id]

                logger.info(f"Agent {self.agent_id} unsubscribed from group {group_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from group {group_id}: {str(e)}")
            return False

    def get_stats(self) -> ConsumerStats:
        """Get consumer statistics."""
        return self.stats

    async def shutdown(self):
        """Shutdown the consumer gracefully."""
        try:
            await self.stop_consuming()

            # Send shutdown notification
            shutdown_content = {
                "action": "shutdown",
                "agent_id": self.agent_id,
                "timestamp": time.time()
            }

            shutdown_message = Message(
                type=MessageType.AGENT_COMMUNICATION,
                topic="agent.broadcast.all",
                payload={
                    "agent_message": {
                        "sender_id": self.agent_id,
                        "message_type": AgentMessageType.SHUTDOWN_NOTIFICATION.value,
                        "content": shutdown_content,
                        "timestamp": time.time()
                    },
                    "agent_info": self.agent_info.__dict__
                },
                headers={
                    "sender_id": self.agent_id,
                    "message_type": AgentMessageType.SHUTDOWN_NOTIFICATION.value
                },
                priority=MessagePriority.HIGH,
                source=self.agent_id
            )

            await self.broker.publish(shutdown_message, "agent.broadcast.all")

            logger.info(f"Agent consumer {self.agent_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during agent consumer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'AgentConsumer',
    'MessageProcessingResult',
    'ConsumerStats'
]