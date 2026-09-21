#!/usr/bin/env python3
"""
Batch Processor - Handles batch processing of messages.

This module provides batch processing capabilities including:
- Message batching and aggregation
- Batch validation and transformation
- Batch-level error handling
- Performance optimization for bulk operations
- Batch persistence and recovery
- Metrics and monitoring for batch operations
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Union, Iterator
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import hashlib

from .message_processor import (
    MessageProcessor, ProcessingContext, ProcessorConfig, ProcessorMetrics,
    ProcessingStatus, ProcessingError, ValidationError, TransformationError
)
from ..message_broker import Message, MessageType

logger = logging.getLogger(__name__)


class BatchTriggerType(Enum):
    """Batch trigger types."""
    SIZE = "size"           # Trigger when batch reaches size limit
    TIME = "time"           # Trigger after time limit
    MESSAGE = "message"     # Trigger on specific message type
    CUSTOM = "custom"       # Custom trigger function


class BatchProcessingMode(Enum):
    """Batch processing modes."""
    SEQUENTIAL = "sequential"   # Process messages one by one
    PARALLEL = "parallel"       # Process messages in parallel
    PIPELINE = "pipeline"       # Process in pipeline stages


@dataclass
class BatchConfig:
    """Batch processing configuration."""
    batch_size: int = 100
    batch_timeout: float = 5.0
    max_batch_wait: float = 30.0
    trigger_type: BatchTriggerType = BatchTriggerType.SIZE
    processing_mode: BatchProcessingMode = BatchProcessingMode.PARALLEL
    max_concurrent_batches: int = 5
    batch_key_function: Optional[Callable] = None
    aggregation_function: Optional[Callable] = None
    enable_batch_persistence: bool = False
    batch_retry_enabled: bool = True
    max_batch_retries: int = 3
    partial_failure_handling: str = "continue"  # continue, abort, retry_failed
    compression_enabled: bool = False
    validation_mode: str = "batch"  # batch, individual, none


@dataclass
class Batch:
    """Message batch structure."""
    batch_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    triggered_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    batch_key: Optional[str] = None
    size: int = 0
    total_processing_time: float = 0.0

    def add_message(self, message: Message):
        """Add a message to the batch."""
        self.messages.append(message)
        self.size = len(self.messages)

    def is_full(self, max_size: int) -> bool:
        """Check if batch is full."""
        return self.size >= max_size

    def is_expired(self, max_wait: float) -> bool:
        """Check if batch has expired."""
        return time.time() - self.created_at > max_wait


@dataclass
class BatchContext:
    """Context for batch processing."""
    batch_id: str
    processor_id: str
    batch: Batch
    message_contexts: Dict[str, ProcessingContext] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor(MessageProcessor):
    """
    Processor for handling batch message processing.
    """

    def __init__(self, processor_id: str, batch_config: BatchConfig, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Batch Processor {processor_id}",
            batch_size=batch_config.batch_size,
            parallel_processing=batch_config.processing_mode == BatchProcessingMode.PARALLEL,
            max_concurrent=batch_config.max_concurrent_batches,
            **kwargs
        )
        super().__init__(config)
        self.batch_config = batch_config
        self.active_batches: Dict[str, Batch] = {}
        self.completed_batches: deque = deque(maxlen=1000)  # Keep last 1000 completed batches
        self.batch_semaphore = asyncio.Semaphore(batch_config.max_concurrent_batches)
        self.batch_triggers: List[Callable] = []
        self.batch_aggregators: Dict[str, Callable] = {}
        self.batch_validators: Dict[str, Callable] = {}
        self.batch_metrics = {
            'batches_created': 0,
            'batches_completed': 0,
            'batches_failed': 0,
            'total_messages_batched': 0,
            'average_batch_size': 0.0,
            'average_batch_processing_time': 0.0
        }

    async def initialize(self):
        """Initialize the batch processor."""
        await super().initialize()

        # Start batch monitoring task
        asyncio.create_task(self._batch_monitoring_loop())

        # Setup default batch triggers
        self._setup_default_triggers()

        logger.info(f"Initialized batch processor: {self.config.name}")

    async def process_message(self, message: Message) -> ProcessingContext:
        """
        Process a single message by adding it to a batch.

        Args:
            message: The message to process

        Returns:
            Processing context (may not be immediately processed)
        """
        try:
            # Determine batch key for the message
            batch_key = self._get_batch_key(message)

            # Get or create batch
            batch = await self._get_or_create_batch(batch_key)

            # Add message to batch
            batch.add_message(message)

            # Update metrics
            self.batch_metrics['total_messages_batched'] += 1

            # Check if batch should be triggered
            if await self._should_trigger_batch(batch):
                await self._trigger_batch(batch)

            # Create context for immediate response
            context = ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                status=ProcessingStatus.PROCESSING,
                metadata={
                    'batch_id': batch.batch_id,
                    'batch_size': batch.size,
                    'batched': True
                }
            )

            return context

        except Exception as e:
            logger.error(f"Error processing message {message.id} in batch processor: {str(e)}")
            return ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                status=ProcessingStatus.FAILED,
                error=str(e)
            )

    async def process_batch_messages(self, messages: List[Message]) -> List[ProcessingContext]:
        """
        Process multiple messages by grouping them into batches.

        Args:
            messages: List of messages to process

        Returns:
            List of processing contexts
        """
        contexts = []

        # Group messages by batch key
        message_groups = defaultdict(list)
        for message in messages:
            batch_key = self._get_batch_key(message)
            message_groups[batch_key].append(message)

        # Process each group
        for batch_key, group_messages in message_groups.items():
            batch = await self._get_or_create_batch(batch_key)

            for message in group_messages:
                batch.add_message(message)
                self.batch_metrics['total_messages_batched'] += 1

                # Create context
                context = ProcessingContext(
                    message_id=message.id,
                    processor_id=self.config.processor_id,
                    status=ProcessingStatus.PROCESSING,
                    metadata={
                        'batch_id': batch.batch_id,
                        'batch_size': batch.size,
                        'batched': True
                    }
                )
                contexts.append(context)

            # Trigger batch if full
            if batch.is_full(self.batch_config.batch_size):
                await self._trigger_batch(batch)

        return contexts

    async def _get_or_create_batch(self, batch_key: str) -> Batch:
        """Get existing batch or create new one."""
        # Look for existing batch with same key that's not full
        for batch in self.active_batches.values():
            if (batch.batch_key == batch_key and
                batch.status == ProcessingStatus.PENDING and
                not batch.is_full(self.batch_config.batch_size)):
                return batch

        # Create new batch
        batch_id = str(uuid.uuid4())
        batch = Batch(
            batch_id=batch_id,
            batch_key=batch_key,
            metadata={
                'created_by': self.config.processor_id,
                'batch_key': batch_key
            }
        )

        self.active_batches[batch_id] = batch
        self.batch_metrics['batches_created'] += 1

        return batch

    def _get_batch_key(self, message: Message) -> str:
        """Get batch key for a message."""
        if self.batch_config.batch_key_function:
            if asyncio.iscoroutinefunction(self.batch_config.batch_key_function):
                # For async functions, we'll use a sync version or handle differently
                # For now, fallback to default key
                pass
            else:
                try:
                    return str(self.batch_config.batch_key_function(message))
                except Exception as e:
                    logger.warning(f"Error in batch key function: {str(e)}")

        # Default batch key based on message type and topic
        return f"{message.type.value}_{message.topic}"

    async def _should_trigger_batch(self, batch: Batch) -> bool:
        """Check if batch should be triggered for processing."""
        # Size-based trigger
        if self.batch_config.trigger_type == BatchTriggerType.SIZE:
            return batch.is_full(self.batch_config.batch_size)

        # Time-based trigger
        elif self.batch_config.trigger_type == BatchTriggerType.TIME:
            return time.time() - batch.created_at >= self.batch_config.batch_timeout

        # Message-based trigger
        elif self.batch_config.trigger_type == BatchTriggerType.MESSAGE:
            return await self._check_message_trigger(batch)

        # Custom triggers
        elif self.batch_config.trigger_type == BatchTriggerType.CUSTOM:
            for trigger in self.batch_triggers:
                try:
                    if await trigger(batch):
                        return True
                except Exception as e:
                    logger.error(f"Error in custom batch trigger: {str(e)}")

        # Check for expired batch
        if batch.is_expired(self.batch_config.max_batch_wait):
            logger.info(f"Batch {batch.batch_id} expired, triggering processing")
            return True

        return False

    async def _check_message_trigger(self, batch: Batch) -> bool:
        """Check for message-based trigger conditions."""
        # Look for specific message types that should trigger processing
        for message in batch.messages:
            if message.type == MessageType.SYSTEM_ALERT:
                return True
            elif message.headers.get("priority") == "critical":
                return True

        return False

    async def _trigger_batch(self, batch: Batch):
        """Trigger batch processing."""
        if batch.status != ProcessingStatus.PENDING:
            return

        batch.triggered_at = time.time()
        batch.status = ProcessingStatus.PROCESSING

        # Start batch processing in background
        asyncio.create_task(self._process_batch_with_semaphore(batch))

    async def _process_batch_with_semaphore(self, batch: Batch):
        """Process batch with semaphore limit."""
        async with self.batch_semaphore:
            try:
                await self._process_batch(batch)
            except Exception as e:
                logger.error(f"Error processing batch {batch.batch_id}: {str(e)}")
                await self._handle_batch_error(batch, e)

    async def _process_batch(self, batch: Batch):
        """Process a batch of messages."""
        start_time = time.time()

        try:
            # Create batch context
            batch_context = BatchContext(
                batch_id=batch.batch_id,
                processor_id=self.config.processor_id,
                batch=batch
            )

            # Validate batch if required
            if self.batch_config.validation_mode == "batch":
                await self._validate_batch(batch, batch_context)

            # Process based on mode
            if self.batch_config.processing_mode == BatchProcessingMode.SEQUENTIAL:
                result = await self._process_sequential(batch, batch_context)
            elif self.batch_config.processing_mode == BatchProcessingMode.PARALLEL:
                result = await self._process_parallel(batch, batch_context)
            elif self.batch_config.processing_mode == BatchProcessingMode.PIPELINE:
                result = await self._process_pipeline(batch, batch_context)
            else:
                raise ProcessingError(f"Unknown processing mode: {self.batch_config.processing_mode}")

            # Aggregate results if function provided
            if self.batch_config.aggregation_function and result is not None:
                result = await self._aggregate_batch_results(batch, result)

            # Update batch
            batch.result = result
            batch.status = ProcessingStatus.SUCCESS
            batch.completed_at = time.time()
            batch.total_processing_time = batch.completed_at - start_time

            # Update context
            batch_context.result = result
            batch_context.status = ProcessingStatus.SUCCESS
            batch_context.completed_at = batch.completed_at

            # Update metrics
            self._update_batch_metrics(batch)
            self._update_individual_message_contexts(batch, batch_context)

            # Move to completed batches
            self.completed_batches.append(batch)
            if batch.batch_id in self.active_batches:
                del self.active_batches[batch.batch_id]

            self.batch_metrics['batches_completed'] += 1

            logger.info(f"Successfully processed batch {batch.batch_id} with {batch.size} messages")

        except Exception as e:
            await self._handle_batch_error(batch, e)

    async def _validate_batch(self, batch: Batch, batch_context: BatchContext):
        """Validate entire batch."""
        try:
            # Custom batch validation
            if batch.batch_key in self.batch_validators:
                validator = self.batch_validators[batch.batch_key]
                if asyncio.iscoroutinefunction(validator):
                    await validator(batch, batch_context)
                else:
                    validator(batch, batch_context)

            # Default validation: ensure all messages have required fields
            for message in batch.messages:
                if not message.id or not message.type:
                    raise ValidationError(f"Invalid message in batch {batch.batch_id}")

        except Exception as e:
            raise ValidationError(f"Batch validation failed: {str(e)}")

    async def _process_sequential(self, batch: Batch, batch_context: BatchContext) -> List[Any]:
        """Process batch messages sequentially."""
        results = []
        failed_messages = []

        for message in batch.messages:
            try:
                # Create message context
                message_context = ProcessingContext(
                    message_id=message.id,
                    processor_id=self.config.processor_id
                )

                # Process message
                result = await self.process(message, message_context)
                results.append(result)
                batch_context.message_contexts[message.id] = message_context

            except Exception as e:
                logger.error(f"Error processing message {message.id} in batch {batch.batch_id}: {str(e)}")
                failed_messages.append((message, str(e)))

                # Handle based on partial failure setting
                if self.batch_config.partial_failure_handling == "abort":
                    raise ProcessingError(f"Batch processing aborted due to message failure: {str(e)}")
                elif self.batch_config.partial_failure_handling == "retry_failed":
                    # Could implement retry logic here
                    pass

        if failed_messages:
            batch_context.metadata['failed_messages'] = failed_messages

        return results

    async def _process_parallel(self, batch: Batch, batch_context: BatchContext) -> List[Any]:
        """Process batch messages in parallel."""
        tasks = []

        for message in batch.messages:
            task = asyncio.create_task(self._process_single_message(message, batch_context))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        failed_messages = []

        for i, result in enumerate(results):
            message = batch.messages[i]

            if isinstance(result, Exception):
                logger.error(f"Error processing message {message.id} in batch {batch.batch_id}: {str(result)}")
                failed_messages.append((message, str(result)))
                processed_results.append(None)
            else:
                processed_results.append(result)

        if failed_messages:
            batch_context.metadata['failed_messages'] = failed_messages

        return processed_results

    async def _process_pipeline(self, batch: Batch, batch_context: BatchContext) -> List[Any]:
        """Process batch messages through pipeline stages."""
        # Implement pipeline processing logic
        # This would require defining pipeline stages
        results = await self._process_parallel(batch, batch_context)
        return results

    async def _process_single_message(self, message: Message, batch_context: BatchContext) -> Any:
        """Process a single message within batch context."""
        message_context = ProcessingContext(
            message_id=message.id,
            processor_id=self.config.processor_id,
            metadata={
                'batch_id': batch_context.batch_id,
                'batch_processing': True
            }
        )

        try:
            result = await self.process(message, message_context)
            batch_context.message_contexts[message.id] = message_context
            return result
        except Exception as e:
            batch_context.message_contexts[message.id] = message_context
            raise

    async def _aggregate_batch_results(self, batch: Batch, results: List[Any]) -> Any:
        """Aggregate results from batch processing."""
        try:
            if self.batch_config.aggregation_function:
                if asyncio.iscoroutinefunction(self.batch_config.aggregation_function):
                    return await self.batch_config.aggregation_function(batch, results)
                else:
                    return self.batch_config.aggregation_function(batch, results)
            else:
                # Default aggregation: return results list
                return {
                    'batch_id': batch.batch_id,
                    'message_count': len(results),
                    'results': results,
                    'success_count': sum(1 for r in results if r is not None)
                }
        except Exception as e:
            logger.error(f"Error aggregating batch results: {str(e)}")
            return results

    async def _handle_batch_error(self, batch: Batch, error: Exception):
        """Handle batch processing error."""
        batch.error = str(error)
        batch.status = ProcessingStatus.FAILED
        batch.completed_at = time.time()

        self.batch_metrics['batches_failed'] += 1

        # Retry logic if enabled
        if self.batch_config.batch_retry_enabled and batch.retry_count < self.batch_config.max_batch_retries:
            batch.retry_count += 1
            batch.status = ProcessingStatus.PENDING

            # Wait before retry
            retry_delay = self.config.retry_delay * (self.config.backoff_factor ** batch.retry_count)
            await asyncio.sleep(retry_delay)

            # Retry processing
            logger.info(f"Retrying batch {batch.batch_id} (attempt {batch.retry_count})")
            asyncio.create_task(self._process_batch_with_semaphore(batch))
        else:
            # Final failure
            if batch.batch_id in self.active_batches:
                del self.active_batches[batch.batch_id]

            logger.error(f"Batch {batch.batch_id} failed permanently: {str(error)}")

    def _update_batch_metrics(self, batch: Batch):
        """Update batch-level metrics."""
        # Update average batch size
        total_batches = self.batch_metrics['batches_created']
        if total_batches > 0:
            self.batch_metrics['average_batch_size'] = (
                (self.batch_metrics['average_batch_size'] * (total_batches - 1) + batch.size) / total_batches
            )

        # Update average processing time
        completed_batches = self.batch_metrics['batches_completed']
        if completed_batches > 0:
            self.batch_metrics['average_batch_processing_time'] = (
                (self.batch_metrics['average_batch_processing_time'] * (completed_batches - 1) + batch.total_processing_time) / completed_batches
            )

    def _update_individual_message_contexts(self, batch: Batch, batch_context: BatchContext):
        """Update individual message contexts with batch results."""
        for message in batch.messages:
            if message.id in batch_context.message_contexts:
                message_context = batch_context.message_contexts[message.id]
                message_context.status = batch_context.status
                message_context.result = batch_context.result
                message_context.completed_at = batch_context.completed_at

    def _setup_default_triggers(self):
        """Setup default batch triggers."""
        # Time-based trigger
        if self.batch_config.trigger_type == BatchTriggerType.TIME:
            async def time_trigger(batch: Batch) -> bool:
                return time.time() - batch.created_at >= self.batch_config.batch_timeout
            self.batch_triggers.append(time_trigger)

    async def _batch_monitoring_loop(self):
        """Monitor for expired batches and cleanup."""
        while True:
            try:
                current_time = time.time()
                expired_batches = []

                for batch_id, batch in self.active_batches.items():
                    if batch.status == ProcessingStatus.PENDING and batch.is_expired(self.batch_config.max_batch_wait):
                        expired_batches.append(batch_id)

                for batch_id in expired_batches:
                    if batch_id in self.active_batches:
                        batch = self.active_batches[batch_id]
                        logger.info(f"Triggering expired batch {batch_id}")
                        await self._trigger_batch(batch)

                await asyncio.sleep(1.0)  # Check every second

            except Exception as e:
                logger.error(f"Error in batch monitoring loop: {str(e)}")
                await asyncio.sleep(5.0)

    def add_batch_trigger(self, trigger: Callable):
        """Add custom batch trigger."""
        self.batch_triggers.append(trigger)

    def add_batch_aggregator(self, batch_key: str, aggregator: Callable):
        """Add batch result aggregator."""
        self.batch_aggregators[batch_key] = aggregator

    def add_batch_validator(self, batch_key: str, validator: Callable):
        """Add batch validator."""
        self.batch_validators[batch_key] = validator

    def get_active_batches(self) -> Dict[str, Batch]:
        """Get currently active batches."""
        return self.active_batches.copy()

    def get_completed_batches(self, limit: int = 100) -> List[Batch]:
        """Get recently completed batches."""
        return list(self.completed_batches)[-limit:]

    def get_batch_metrics(self) -> Dict[str, Any]:
        """Get batch processing metrics."""
        return {
            **self.batch_metrics,
            'active_batches': len(self.active_batches),
            'completed_batches': len(self.completed_batches),
            'average_batch_size': self.batch_metrics['average_batch_size'],
            'average_batch_processing_time': self.batch_metrics['average_batch_processing_time']
        }

    async def force_trigger_batch(self, batch_id: str) -> bool:
        """Force trigger a specific batch."""
        if batch_id in self.active_batches:
            batch = self.active_batches[batch_id]
            await self._trigger_batch(batch)
            return True
        return False

    async def force_trigger_all_batches(self) -> int:
        """Force trigger all active batches."""
        batch_ids = list(self.active_batches.keys())
        for batch_id in batch_ids:
            await self.force_trigger_batch(batch_id)
        return len(batch_ids)


# Specialized batch processors

class SizeBasedBatchProcessor(BatchProcessor):
    """Batch processor that triggers based on batch size."""

    def __init__(self, processor_id: str, batch_size: int, **kwargs):
        batch_config = BatchConfig(
            batch_size=batch_size,
            trigger_type=BatchTriggerType.SIZE,
            **kwargs
        )
        super().__init__(processor_id, batch_config, **kwargs)


class TimeBasedBatchProcessor(BatchProcessor):
    """Batch processor that triggers based on time interval."""

    def __init__(self, processor_id: str, batch_timeout: float, **kwargs):
        batch_config = BatchConfig(
            batch_timeout=batch_timeout,
            trigger_type=BatchTriggerType.TIME,
            **kwargs
        )
        super().__init__(processor_id, batch_config, **kwargs)


class MessageKeyedBatchProcessor(BatchProcessor):
    """Batch processor that groups messages by a key function."""

    def __init__(self, processor_id: str, key_function: Callable, **kwargs):
        batch_config = BatchConfig(
            batch_key_function=key_function,
            **kwargs
        )
        super().__init__(processor_id, batch_config, **kwargs)


# Export main classes
__all__ = [
    'BatchProcessor',
    'Batch',
    'BatchContext',
    'BatchConfig',
    'BatchTriggerType',
    'BatchProcessingMode',
    'SizeBasedBatchProcessor',
    'TimeBasedBatchProcessor',
    'MessageKeyedBatchProcessor'
]