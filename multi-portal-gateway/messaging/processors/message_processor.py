#!/usr/bin/env python3
"""
Message Processor - Base message processing framework.

This module provides the foundation for message processing including:
- Base processor interface
- Message validation and transformation
- Error handling and recovery
- Processing pipelines
- Metrics and monitoring
- Plugin system for custom processors
"""

import asyncio
import json
import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic
from collections import defaultdict, deque
import hashlib
import uuid

from ..message_broker import Message, MessageType, MessagePriority

logger = logging.getLogger(__name__)

# Type hints
T = TypeVar('T')
ProcessorResult = Union[bool, Dict[str, Any], List[Any], None]


class ProcessingStatus(Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class ProcessingContext:
    """Context for message processing."""
    message_id: str
    processor_id: str
    attempt_count: int = 0
    max_attempts: int = 3
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[ProcessorResult] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessorConfig:
    """Processor configuration."""
    processor_id: str
    name: str
    enabled: bool = True
    priority: int = 0
    timeout: float = 30.0
    max_attempts: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    parallel_processing: bool = True
    max_concurrent: int = 10
    batch_size: int = 1
    validation_required: bool = True
    transformation_required: bool = False
    metrics_enabled: bool = True
    error_handling: str = "retry"  # retry, skip, dead_letter
    dead_letter_queue: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessorMetrics:
    """Processor performance metrics."""
    processor_id: str
    messages_processed: int = 0
    messages_failed: int = 0
    messages_skipped: int = 0
    messages_retried: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    max_processing_time: float = 0.0
    last_processed_at: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0  # messages per second
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)


class ProcessingError(Exception):
    """Base exception for processing errors."""
    pass


class ValidationError(ProcessingError):
    """Message validation error."""
    pass


class TransformationError(ProcessingError):
    """Message transformation error."""
    pass


class TimeoutError(ProcessingError):
    """Processing timeout error."""
    pass


class RetryableError(ProcessingError):
    """Error that can be retried."""
    pass


class FatalError(ProcessingError):
    """Non-retryable error."""
    pass


class MessageProcessor(ABC):
    """
    Abstract base class for message processors.
    """

    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.metrics = ProcessorMetrics(processor_id=config.processor_id)
        self.active_contexts: Dict[str, ProcessingContext] = {}
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.validator: Optional[Callable] = None
        self.transformer: Optional[Callable] = None
        self.error_handlers: Dict[type, Callable] = {}
        self.middleware: List[Callable] = []
        self.plugins: List[Any] = []
        self._shutdown = False

    @abstractmethod
    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """
        Process a single message.

        Args:
            message: The message to process
            context: Processing context

        Returns:
            Processing result
        """
        pass

    async def initialize(self):
        """Initialize the processor."""
        try:
            # Load plugins
            await self._load_plugins()

            # Setup middleware
            await self._setup_middleware()

            # Setup error handlers
            await self._setup_error_handlers()

            logger.info(f"Initialized processor: {self.config.name}")

        except Exception as e:
            logger.error(f"Failed to initialize processor {self.config.processor_id}: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown the processor gracefully."""
        try:
            self._shutdown = True

            # Wait for active processing to complete
            while self.active_contexts:
                logger.info(f"Waiting for {len(self.active_contexts)} active processes to complete...")
                await asyncio.sleep(1)

            # Unload plugins
            await self._unload_plugins()

            logger.info(f"Shutdown processor: {self.config.name}")

        except Exception as e:
            logger.error(f"Error during processor shutdown: {str(e)}")

    async def process_message(self, message: Message) -> ProcessingContext:
        """
        Process a message with full pipeline.

        Args:
            message: The message to process

        Returns:
            Processing context with results
        """
        if not self.config.enabled:
            context = ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                status=ProcessingStatus.SKIPPED,
                error="Processor is disabled"
            )
            return context

        # Create processing context
        context = ProcessingContext(
            message_id=message.id,
            processor_id=self.config.processor_id,
            max_attempts=self.config.max_attempts
        )

        self.active_contexts[message.id] = context

        try:
            # Process with retry logic
            result = await self._process_with_retry(message, context)

            # Update context
            context.result = result
            context.status = ProcessingStatus.SUCCESS
            context.completed_at = time.time()

            # Update metrics
            self._update_metrics(context)

            return context

        except Exception as e:
            context.error = str(e)
            context.traceback = traceback.format_exc()
            context.status = ProcessingStatus.FAILED
            context.completed_at = time.time()

            # Handle error
            await self._handle_processing_error(message, context, e)

            # Update metrics
            self._update_metrics(context)

            return context

        finally:
            # Clean up
            if message.id in self.active_contexts:
                del self.active_contexts[message.id]

    async def process_batch(self, messages: List[Message]) -> List[ProcessingContext]:
        """
        Process a batch of messages.

        Args:
            messages: List of messages to process

        Returns:
            List of processing contexts
        """
        if not self.config.parallel_processing:
            # Sequential processing
            contexts = []
            for message in messages:
                context = await self.process_message(message)
                contexts.append(context)
            return contexts

        # Parallel processing with semaphore limit
        tasks = []
        for message in messages:
            task = asyncio.create_task(self._process_with_semaphore(message))
            tasks.append(task)

        # Wait for all tasks to complete
        contexts = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_contexts = []
        for i, result in enumerate(contexts):
            if isinstance(result, Exception):
                # Create error context
                context = ProcessingContext(
                    message_id=messages[i].id,
                    processor_id=self.config.processor_id,
                    status=ProcessingStatus.FAILED,
                    error=str(result),
                    traceback=traceback.format_exc()
                )
                processed_contexts.append(context)
            else:
                processed_contexts.append(result)

        return processed_contexts

    async def _process_with_semaphore(self, message: Message) -> ProcessingContext:
        """Process message with semaphore limit."""
        async with self.semaphore:
            return await self.process_message(message)

    async def _process_with_retry(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Process message with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            context.attempt_count = attempt + 1
            context.status = ProcessingStatus.PROCESSING

            try:
                # Validate message
                if self.config.validation_required:
                    await self._validate_message(message)

                # Apply pre-processing middleware
                processed_message = await self._apply_pre_middleware(message)

                # Transform message if required
                if self.config.transformation_required and self.transformer:
                    processed_message = await self.transformer(processed_message)

                # Process with timeout
                result = await asyncio.wait_for(
                    self.process(processed_message, context),
                    timeout=self.config.timeout
                )

                # Apply post-processing middleware
                if result is not None:
                    result = await self._apply_post_middleware(processed_message, result)

                return result

            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(f"Processing timeout after {self.config.timeout}s")
                context.metrics['timeout'] = True

            except ValidationError as e:
                last_exception = e
                context.metrics['validation_error'] = True
                # Validation errors are typically not retryable
                break

            except FatalError as e:
                last_exception = e
                context.metrics['fatal_error'] = True
                # Fatal errors are not retryable
                break

            except RetryableError as e:
                last_exception = e
                context.metrics['retryable_error'] = True
                # Will retry

            except Exception as e:
                last_exception = e
                context.metrics['unknown_error'] = True
                # Unknown errors are typically retryable

            # If not the last attempt, wait before retry
            if attempt < self.config.max_attempts - 1:
                retry_delay = self.config.retry_delay * (self.config.backoff_factor ** attempt)
                context.metrics['retry_delay'] = retry_delay
                await asyncio.sleep(retry_delay)

                # Update retry metrics
                self.metrics.messages_retried += 1

        # All attempts failed
        raise last_exception or ProcessingError("Processing failed after all attempts")

    async def _validate_message(self, message: Message):
        """Validate message structure and content."""
        try:
            if not message.id:
                raise ValidationError("Message ID is required")

            if not message.type:
                raise ValidationError("Message type is required")

            if not message.topic:
                raise ValidationError("Message topic is required")

            # Custom validation
            if self.validator:
                await self.validator(message)

        except Exception as e:
            raise ValidationError(f"Message validation failed: {str(e)}")

    async def _apply_pre_middleware(self, message: Message) -> Message:
        """Apply pre-processing middleware."""
        processed_message = message

        for middleware in self.middleware:
            try:
                if hasattr(middleware, 'pre_process'):
                    processed_message = await middleware.pre_process(processed_message)
            except Exception as e:
                logger.error(f"Pre-middleware error: {str(e)}")
                # Continue processing despite middleware error

        return processed_message

    async def _apply_post_middleware(self, message: Message, result: ProcessorResult) -> ProcessorResult:
        """Apply post-processing middleware."""
        processed_result = result

        for middleware in self.middleware:
            try:
                if hasattr(middleware, 'post_process'):
                    processed_result = await middleware.post_process(message, processed_result)
            except Exception as e:
                logger.error(f"Post-middleware error: {str(e)}")
                # Continue processing despite middleware error

        return processed_result

    async def _handle_processing_error(self, message: Message, context: ProcessingContext, error: Exception):
        """Handle processing error."""
        try:
            error_type = type(error)

            # Use custom error handler if available
            if error_type in self.error_handlers:
                await self.error_handlers[error_type](message, context, error)
            else:
                # Default error handling
                await self._default_error_handler(message, context, error)

        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")

        # Update failure metrics
        self.metrics.messages_failed += 1

    async def _default_error_handler(self, message: Message, context: ProcessingContext, error: Exception):
        """Default error handler."""
        logger.error(f"Processing failed for message {message.id}: {str(error)}")

        # Send to dead letter queue if configured
        if self.config.dead_letter_queue and self.config.error_handling == "dead_letter":
            await self._send_to_dead_letter_queue(message, context, error)

    async def _send_to_dead_letter_queue(self, message: Message, context: ProcessingContext, error: Exception):
        """Send failed message to dead letter queue."""
        try:
            # This would typically use the message broker to send to DLQ
            # Implementation depends on broker integration
            logger.warning(f"Message {message.id} sent to dead letter queue: {str(error)}")

        except Exception as e:
            logger.error(f"Failed to send message to dead letter queue: {str(e)}")

    def _update_metrics(self, context: ProcessingContext):
        """Update processor metrics."""
        if not self.config.metrics_enabled:
            return

        processing_time = context.completed_at - context.started_at

        # Update basic metrics
        if context.status == ProcessingStatus.SUCCESS:
            self.metrics.messages_processed += 1
        elif context.status == ProcessingStatus.FAILED:
            self.metrics.messages_failed += 1
        elif context.status == ProcessingStatus.SKIPPED:
            self.metrics.messages_skipped += 1

        # Update timing metrics
        self.metrics.total_processing_time += processing_time
        self.metrics.last_processed_at = context.completed_at

        if self.metrics.messages_processed > 0:
            self.metrics.average_processing_time = (
                self.metrics.total_processing_time / self.metrics.messages_processed
            )

        self.metrics.min_processing_time = min(self.metrics.min_processing_time, processing_time)
        self.metrics.max_processing_time = max(self.metrics.max_processing_time, processing_time)

        # Calculate error rate
        total_messages = (self.metrics.messages_processed +
                         self.metrics.messages_failed +
                         self.metrics.messages_skipped)

        if total_messages > 0:
            self.metrics.error_rate = self.metrics.messages_failed / total_messages

        # Calculate throughput (messages per second over last minute)
        current_time = time.time()
        if self.metrics.last_processed_at > 0:
            time_diff = current_time - self.metrics.last_processed_at
            if time_diff > 0:
                self.metrics.throughput = 1.0 / time_diff

    async def _load_plugins(self):
        """Load processor plugins."""
        # Plugin loading implementation would go here
        pass

    async def _unload_plugins(self):
        """Unload processor plugins."""
        for plugin in self.plugins:
            try:
                if hasattr(plugin, 'unload'):
                    await plugin.unload()
            except Exception as e:
                logger.error(f"Error unloading plugin: {str(e)}")

        self.plugins.clear()

    async def _setup_middleware(self):
        """Setup processing middleware."""
        # Middleware setup implementation would go here
        pass

    async def _setup_error_handlers(self):
        """Setup error handlers."""
        # Register default error handlers
        self.error_handlers[ValidationError] = self._handle_validation_error
        self.error_handlers[TransformationError] = self._handle_transformation_error
        self.error_handlers[TimeoutError] = self._handle_timeout_error
        self.error_handlers[RetryableError] = self._handle_retryable_error
        self.error_handlers[FatalError] = self._handle_fatal_error

    async def _handle_validation_error(self, message: Message, context: ProcessingContext, error: ValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error for message {message.id}: {str(error)}")

    async def _handle_transformation_error(self, message: Message, context: ProcessingContext, error: TransformationError):
        """Handle transformation errors."""
        logger.error(f"Transformation error for message {message.id}: {str(error)}")

    async def _handle_timeout_error(self, message: Message, context: ProcessingContext, error: TimeoutError):
        """Handle timeout errors."""
        logger.error(f"Timeout error for message {message.id}: {str(error)}")

    async def _handle_retryable_error(self, message: Message, context: ProcessingContext, error: RetryableError):
        """Handle retryable errors."""
        logger.warning(f"Retryable error for message {message.id} (attempt {context.attempt_count}): {str(error)}")

    async def _handle_fatal_error(self, message: Message, context: ProcessingContext, error: FatalError):
        """Handle fatal errors."""
        logger.error(f"Fatal error for message {message.id}: {str(error)}")

    def set_validator(self, validator: Callable):
        """Set custom message validator."""
        self.validator = validator

    def set_transformer(self, transformer: Callable):
        """Set custom message transformer."""
        self.transformer = transformer

    def add_error_handler(self, error_type: type, handler: Callable):
        """Add custom error handler."""
        self.error_handlers[error_type] = handler

    def add_middleware(self, middleware: Any):
        """Add processing middleware."""
        self.middleware.append(middleware)

    def add_plugin(self, plugin: Any):
        """Add processor plugin."""
        self.plugins.append(plugin)

    def get_metrics(self) -> ProcessorMetrics:
        """Get current processor metrics."""
        return self.metrics

    def get_active_contexts(self) -> Dict[str, ProcessingContext]:
        """Get currently active processing contexts."""
        return self.active_contexts.copy()

    def get_config(self) -> ProcessorConfig:
        """Get processor configuration."""
        return self.config


class SimpleMessageProcessor(MessageProcessor):
    """
    Simple message processor implementation for basic use cases.
    """

    def __init__(self, processor_id: str, handler: Callable, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Simple Processor {processor_id}",
            **kwargs
        )
        super().__init__(config)
        self.handler = handler

    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Process message using the provided handler."""
        try:
            # Call the handler function
            if asyncio.iscoroutinefunction(self.handler):
                result = await self.handler(message, context)
            else:
                result = self.handler(message, context)

            return result

        except Exception as e:
            # Determine if error is retryable
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                raise RetryableError(str(e))
            elif "validation" in str(e).lower() or "format" in str(e).lower():
                raise ValidationError(str(e))
            else:
                raise FatalError(str(e))


class ConditionalProcessor(MessageProcessor):
    """
    Processor that processes messages based on conditions.
    """

    def __init__(self, processor_id: str, condition: Callable, processor: MessageProcessor, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Conditional Processor {processor_id}",
            **kwargs
        )
        super().__init__(config)
        self.condition = condition
        self.processor = processor

    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Process message only if condition is met."""
        try:
            # Check condition
            if asyncio.iscoroutinefunction(self.condition):
                should_process = await self.condition(message)
            else:
                should_process = self.condition(message)

            if not should_process:
                context.status = ProcessingStatus.SKIPPED
                context.metadata['skip_reason'] = "Condition not met"
                return None

            # Process with the wrapped processor
            return await self.processor.process(message, context)

        except Exception as e:
            raise FatalError(f"Conditional processing failed: {str(e)}")


class ChainProcessor(MessageProcessor):
    """
    Processor that chains multiple processors together.
    """

    def __init__(self, processor_id: str, processors: List[MessageProcessor], **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Chain Processor {processor_id}",
            **kwargs
        )
        super().__init__(config)
        self.processors = processors

    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Process message through all processors in chain."""
        result = None

        for i, processor in enumerate(self.processors):
            try:
                # Create sub-context for each processor
                sub_context = ProcessingContext(
                    message_id=message.id,
                    processor_id=processor.config.processor_id,
                    metadata={
                        'chain_position': i,
                        'chain_length': len(self.processors),
                        'parent_context': context
                    }
                )

                # Process with current processor
                result = await processor.process(message, sub_context)

                # Update main context with sub-context info
                context.metadata[f'processor_{i}_result'] = result
                context.metadata[f'processor_{i}_status'] = sub_context.status.value

                # If processor returned None and wants to stop chain, break
                if result is None and sub_context.status == ProcessingStatus.SKIPPED:
                    break

            except Exception as e:
                # Chain processing failed
                raise FatalError(f"Chain processor {i} failed: {str(e)}")

        return result


class FilterProcessor(MessageProcessor):
    """
    Processor that filters messages based on criteria.
    """

    def __init__(self, processor_id: str, filter_func: Callable, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Filter Processor {processor_id}",
            **kwargs
        )
        super().__init__(config)
        self.filter_func = filter_func

    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Filter message based on criteria."""
        try:
            # Apply filter
            if asyncio.iscoroutinefunction(self.filter_func):
                should_pass = await self.filter_func(message)
            else:
                should_pass = self.filter_func(message)

            if not should_pass:
                context.status = ProcessingStatus.SKIPPED
                context.metadata['skip_reason'] = "Filtered out"
                return None

            # Message passed filter, return it unchanged
            return message

        except Exception as e:
            raise FatalError(f"Filter processing failed: {str(e)}")


class TransformProcessor(MessageProcessor):
    """
    Processor that transforms messages.
    """

    def __init__(self, processor_id: str, transform_func: Callable, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Transform Processor {processor_id}",
            transformation_required=True,
            **kwargs
        )
        super().__init__(config)
        self.transform_func = transform_func

    async def process(self, message: Message, context: ProcessingContext) -> ProcessorResult:
        """Transform message."""
        try:
            # Apply transformation
            if asyncio.iscoroutinefunction(self.transform_func):
                transformed_message = await self.transform_func(message)
            else:
                transformed_message = self.transform_func(message)

            # Validate transformed message
            if not isinstance(transformed_message, Message):
                raise TransformationError("Transform function must return a Message object")

            return transformed_message

        except Exception as e:
            raise TransformationError(f"Message transformation failed: {str(e)}")


# Export main classes
__all__ = [
    'MessageProcessor',
    'ProcessingContext',
    'ProcessorConfig',
    'ProcessorMetrics',
    'ProcessingStatus',
    'ProcessingError',
    'ValidationError',
    'TransformationError',
    'TimeoutError',
    'RetryableError',
    'FatalError',
    'SimpleMessageProcessor',
    'ConditionalProcessor',
    'ChainProcessor',
    'FilterProcessor',
    'TransformProcessor'
]