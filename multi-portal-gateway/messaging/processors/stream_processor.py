#!/usr/bin/env python3
"""
Stream Processor - Handles real-time stream processing of messages.

This module provides stream processing capabilities including:
- Real-time message stream processing
- Window-based processing (time, count, session)
- Stream aggregation and analytics
- Pattern matching in streams
- Complex event processing
- Stream state management
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Union, Iterator, AsyncIterator
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

from .message_processor import (
    MessageProcessor, ProcessingContext, ProcessorConfig, ProcessorMetrics,
    ProcessingStatus, ProcessingError, ValidationError, TransformationError
)
from ..message_broker import Message, MessageType

logger = logging.getLogger(__name__)


class WindowType(Enum):
    """Stream window types."""
    TIME = "time"           # Time-based window
    COUNT = "count"         # Count-based window
    SESSION = "session"     # Session-based window
    SLIDING = "sliding"     # Sliding window
    TUMBLING = "tumbling"   # Tumbling window
    GLOBAL = "global"       # Global window (no partitioning)


class StreamEventType(Enum):
    """Stream event types."""
    MESSAGE_ARRIVAL = "message_arrival"
    WINDOW_START = "window_start"
    WINDOW_END = "window_end"
    PATTERN_MATCH = "pattern_match"
    AGGREGATION_RESULT = "aggregation_result"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class StreamWindow:
    """Stream window structure."""
    window_id: str
    window_type: WindowType
    start_time: float
    end_time: Optional[float] = None
    start_sequence: Optional[int] = None
    end_sequence: Optional[int] = None
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    partition_key: Optional[str] = None
    size: int = 0
    is_active: bool = True

    def add_message(self, message: Message):
        """Add message to window."""
        self.messages.append(message)
        self.size = len(self.messages)

    def should_include(self, message: Message) -> bool:
        """Check if message should be included in window."""
        if self.window_type == WindowType.TIME:
            return self.start_time <= message.timestamp <= (self.end_time or float('inf'))
        elif self.window_type == WindowType.COUNT:
            return self.size < (self.end_sequence or float('inf'))
        elif self.window_type == WindowType.SESSION:
            return self.session_id == message.headers.get('session_id')
        return True

    def is_expired(self) -> bool:
        """Check if window is expired."""
        if self.window_type == WindowType.TIME and self.end_time:
            return time.time() > self.end_time
        elif self.window_type == WindowType.COUNT and self.end_sequence:
            return self.size >= self.end_sequence
        return False


@dataclass
class StreamPattern:
    """Stream pattern definition."""
    pattern_id: str
    name: str
    conditions: List[Callable] = field(default_factory=list)
    time_window: Optional[float] = None
    max_matches: Optional[int] = None
    action: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamEvent:
    """Stream event structure."""
    event_id: str
    event_type: StreamEventType
    timestamp: float = field(default_factory=time.time)
    window_id: Optional[str] = None
    message_id: Optional[str] = None
    pattern_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamConfig:
    """Stream processing configuration."""
    window_type: WindowType = WindowType.TIME
    window_size: float = 60.0  # seconds for time windows, count for count windows
    sliding_interval: Optional[float] = None
    max_concurrent_windows: int = 100
    buffer_size: int = 1000
    processing_delay: float = 0.0
    enable_pattern_matching: bool = True
    enable_aggregations: bool = True
    enable_state_management: bool = True
    partition_function: Optional[Callable] = None
    late_message_handling: str = "drop"  # drop, process, redirect
    max_lateness: float = 300.0  # seconds
    checkpoint_interval: float = 60.0  # seconds
    state_backend: str = "memory"  # memory, redis, database


class StreamProcessor(MessageProcessor):
    """
    Processor for real-time stream processing.
    """

    def __init__(self, processor_id: str, stream_config: StreamConfig, **kwargs):
        config = ProcessorConfig(
            processor_id=processor_id,
            name=f"Stream Processor {processor_id}",
            parallel_processing=True,
            max_concurrent=stream_config.max_concurrent_windows,
            **kwargs
        )
        super().__init__(config)
        self.stream_config = stream_config
        self.active_windows: Dict[str, StreamWindow] = {}
        self.completed_windows: deque = deque(maxlen=1000)
        self.stream_buffer: deque = deque(maxlen=stream_config.buffer_size)
        self.patterns: Dict[str, StreamPattern] = {}
        self.aggregations: Dict[str, Callable] = {}
        self.stream_state: Dict[str, Any] = {}
        self.stream_metrics = {
            'messages_processed': 0,
            'windows_created': 0,
            'windows_completed': 0,
            'patterns_matched': 0,
            'aggregations_computed': 0,
            'late_messages': 0,
            'processing_latency': 0.0
        }
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.window_task: Optional[asyncio.Task] = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize the stream processor."""
        await super().initialize()

        # Start monitoring tasks
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._stream_monitoring_loop())
        self.window_task = asyncio.create_task(self._window_management_loop())

        # Setup default aggregations
        self._setup_default_aggregations()

        logger.info(f"Initialized stream processor: {self.config.name}")

    async def shutdown(self):
        """Shutdown the stream processor gracefully."""
        self.is_running = False

        # Cancel monitoring tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.window_task:
            self.window_task.cancel()

        # Complete all active windows
        for window_id in list(self.active_windows.keys()):
            await self._complete_window(window_id)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        await super().shutdown()

        logger.info(f"Shutdown stream processor: {self.config.name}")

    async def process_message(self, message: Message) -> ProcessingContext:
        """
        Process a message in the stream.

        Args:
            message: The message to process

        Returns:
            Processing context
        """
        start_time = time.time()

        try:
            # Check for late messages
            if self._is_late_message(message):
                await self._handle_late_message(message)
                self.stream_metrics['late_messages'] += 1
            else:
                # Add to stream buffer
                self.stream_buffer.append(message)

                # Determine partition key
                partition_key = self._get_partition_key(message)

                # Get or create window
                window = await self._get_or_create_window(message, partition_key)

                # Add message to window
                if window.should_include(message):
                    window.add_message(message)

                    # Process message immediately if needed
                    if self.stream_config.processing_delay == 0:
                        await self._process_stream_message(message, window)

                    # Check for pattern matches
                    if self.stream_config.enable_pattern_matching:
                        await self._check_patterns(message, window)

                # Check if window should be completed
                if window.is_expired():
                    await self._complete_window(window.window_id)

            # Update metrics
            self.stream_metrics['messages_processed'] += 1
            processing_time = time.time() - start_time
            self._update_latency_metrics(processing_time)

            # Create context
            context = ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                status=ProcessingStatus.SUCCESS,
                metrics={
                    'processing_time': processing_time,
                    'stream_processing': True
                }
            )

            return context

        except Exception as e:
            logger.error(f"Error processing stream message {message.id}: {str(e)}")
            return ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                status=ProcessingStatus.FAILED,
                error=str(e)
            )

    async def process_stream(self, message_stream: AsyncIterator[Message]) -> AsyncIterator[ProcessingContext]:
        """
        Process a stream of messages.

        Args:
            message_stream: Async iterator of messages

        Yields:
            Processing contexts for each message
        """
        async for message in message_stream:
            context = await self.process_message(message)
            yield context

    def _get_partition_key(self, message: Message) -> str:
        """Get partition key for message."""
        if self.stream_config.partition_function:
            try:
                return str(self.stream_config.partition_function(message))
            except Exception as e:
                logger.warning(f"Error in partition function: {str(e)}")

        # Default partitioning by topic
        return message.topic

    async def _get_or_create_window(self, message: Message, partition_key: str) -> StreamWindow:
        """Get existing window or create new one."""
        current_time = message.timestamp

        # Look for suitable existing window
        for window in self.active_windows.values():
            if (window.partition_key == partition_key and
                window.should_include(message) and
                window.is_active):
                return window

        # Create new window
        window_id = str(uuid.uuid4())
        window = StreamWindow(
            window_id=window_id,
            window_type=self.stream_config.window_type,
            start_time=current_time,
            end_time=current_time + self.stream_config.window_size if self.stream_config.window_type == WindowType.TIME else None,
            end_sequence=self.stream_config.window_size if self.stream_config.window_type == WindowType.COUNT else None,
            session_id=message.headers.get('session_id') if self.stream_config.window_type == WindowType.SESSION else None,
            partition_key=partition_key
        )

        self.active_windows[window_id] = window
        self.stream_metrics['windows_created'] += 1

        # Emit window start event
        await self._emit_stream_event(StreamEventType.WINDOW_START, window_id=window_id)

        return window

    def _is_late_message(self, message: Message) -> bool:
        """Check if message is late."""
        if self.stream_config.window_type == WindowType.TIME:
            # Check if message is older than allowed lateness
            time_diff = time.time() - message.timestamp
            return time_diff > self.stream_config.max_lateness
        return False

    async def _handle_late_message(self, message: Message):
        """Handle late message based on configuration."""
        if self.stream_config.late_message_handling == "drop":
            logger.debug(f"Dropping late message: {message.id}")
        elif self.stream_config.late_message_handling == "process":
            logger.info(f"Processing late message: {message.id}")
            # Process in a special window for late messages
            window = await self._get_or_create_window(message, "late_messages")
            window.add_message(message)
        elif self.stream_config.late_message_handling == "redirect":
            # Redirect to special queue/topic
            logger.info(f"Redirecting late message: {message.id}")
            # Implementation would depend on broker integration

    async def _process_stream_message(self, message: Message, window: StreamWindow):
        """Process a stream message."""
        try:
            # Call the main processor
            context = ProcessingContext(
                message_id=message.id,
                processor_id=self.config.processor_id,
                metadata={
                    'window_id': window.window_id,
                    'stream_processing': True
                }
            )

            await self.process(message, context)

            # Update stream state if enabled
            if self.stream_config.enable_state_management:
                await self._update_stream_state(message, context)

        except Exception as e:
            logger.error(f"Error processing stream message {message.id}: {str(e)}")
            await self._emit_stream_event(StreamEventType.ERROR, message_id=message.id, data={'error': str(e)})

    async def _check_patterns(self, message: Message, window: StreamWindow):
        """Check if message matches any patterns."""
        for pattern in self.patterns.values():
            try:
                if await self._evaluate_pattern(pattern, message, window):
                    await self._handle_pattern_match(pattern, message, window)
                    self.stream_metrics['patterns_matched'] += 1
            except Exception as e:
                logger.error(f"Error evaluating pattern {pattern.pattern_id}: {str(e)}")

    async def _evaluate_pattern(self, pattern: StreamPattern, message: Message, window: StreamWindow) -> bool:
        """Evaluate if message matches pattern."""
        for condition in pattern.conditions:
            try:
                if asyncio.iscoroutinefunction(condition):
                    result = await condition(message, window)
                else:
                    result = condition(message, window)

                if not result:
                    return False
            except Exception as e:
                logger.error(f"Error in pattern condition: {str(e)}")
                return False

        return True

    async def _handle_pattern_match(self, pattern: StreamPattern, message: Message, window: StreamWindow):
        """Handle pattern match."""
        logger.info(f"Pattern matched: {pattern.name} for message {message.id}")

        # Emit pattern match event
        await self._emit_stream_event(
            StreamEventType.PATTERN_MATCH,
            pattern_id=pattern.pattern_id,
            message_id=message.id,
            window_id=window.window_id,
            data={'pattern_name': pattern.name}
        )

        # Execute pattern action
        if pattern.action:
            try:
                if asyncio.iscoroutinefunction(pattern.action):
                    await pattern.action(message, window, pattern)
                else:
                    pattern.action(message, window, pattern)
            except Exception as e:
                logger.error(f"Error executing pattern action: {str(e)}")

    async def _complete_window(self, window_id: str):
        """Complete a stream window."""
        if window_id not in self.active_windows:
            return

        window = self.active_windows[window_id]
        window.is_active = False
        window.end_time = time.time()

        try:
            # Process window aggregations
            if self.stream_config.enable_aggregations:
                await self._process_window_aggregations(window)

            # Move to completed windows
            self.completed_windows.append(window)
            del self.active_windows[window_id]
            self.stream_metrics['windows_completed'] += 1

            # Emit window end event
            await self._emit_stream_event(StreamEventType.WINDOW_END, window_id=window_id)

            logger.debug(f"Completed window {window_id} with {window.size} messages")

        except Exception as e:
            logger.error(f"Error completing window {window_id}: {str(e)}")

    async def _process_window_aggregations(self, window: StreamWindow):
        """Process aggregations for completed window."""
        for aggregation_name, aggregation_func in self.aggregations.items():
            try:
                if asyncio.iscoroutinefunction(aggregation_func):
                    result = await aggregation_func(window)
                else:
                    result = aggregation_func(window)

                # Emit aggregation result event
                await self._emit_stream_event(
                    StreamEventType.AGGREGATION_RESULT,
                    window_id=window.window_id,
                    data={
                        'aggregation_name': aggregation_name,
                        'result': result
                    }
                )

                self.stream_metrics['aggregations_computed'] += 1

            except Exception as e:
                logger.error(f"Error computing aggregation {aggregation_name}: {str(e)}")

    async def _update_stream_state(self, message: Message, context: ProcessingContext):
        """Update stream processing state."""
        try:
            # Update message counts
            state_key = f"count_{message.topic}"
            self.stream_state[state_key] = self.stream_state.get(state_key, 0) + 1

            # Update last seen timestamp
            self.stream_state[f"last_seen_{message.topic}"] = message.timestamp

            # Custom state updates can be added here

        except Exception as e:
            logger.error(f"Error updating stream state: {str(e)}")

    async def _emit_stream_event(self, event_type: StreamEventType, **kwargs):
        """Emit a stream event."""
        event = StreamEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            **kwargs
        )

        # Handle stream event (could publish to broker, etc.)
        logger.debug(f"Stream event: {event_type.value} - {event.event_id}")

    def _update_latency_metrics(self, processing_time: float):
        """Update processing latency metrics."""
        # Simple moving average
        alpha = 0.1  # Smoothing factor
        self.stream_metrics['processing_latency'] = (
            alpha * processing_time + (1 - alpha) * self.stream_metrics['processing_latency']
        )

    async def _stream_monitoring_loop(self):
        """Monitor stream processing and handle maintenance tasks."""
        while self.is_running:
            try:
                current_time = time.time()

                # Check for expired windows
                expired_windows = []
                for window_id, window in self.active_windows.items():
                    if window.is_expired():
                        expired_windows.append(window_id)

                for window_id in expired_windows:
                    await self._complete_window(window_id)

                # Process delayed messages if configured
                if self.stream_config.processing_delay > 0 and self.stream_buffer:
                    await self._process_delayed_messages()

                # Cleanup old completed windows
                await self._cleanup_old_windows()

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in stream monitoring loop: {str(e)}")
                await asyncio.sleep(5.0)

    async def _window_management_loop(self):
        """Manage window lifecycle for sliding/tumbling windows."""
        if self.stream_config.window_type not in [WindowType.SLIDING, WindowType.TUMBLING]:
            return

        while self.is_running:
            try:
                current_time = time.time()

                if self.stream_config.window_type == WindowType.SLIDING:
                    await self._manage_sliding_windows(current_time)
                elif self.stream_config.window_type == WindowType.TUMBLING:
                    await self._manage_tumbling_windows(current_time)

                await asyncio.sleep(self.stream_config.sliding_interval or 1.0)

            except Exception as e:
                logger.error(f"Error in window management loop: {str(e)}")
                await asyncio.sleep(5.0)

    async def _manage_sliding_windows(self, current_time: float):
        """Manage sliding windows."""
        # Implementation for sliding window management
        pass

    async def _manage_tumbling_windows(self, current_time: float):
        """Manage tumbling windows."""
        # Implementation for tumbling window management
        pass

    async def _process_delayed_messages(self):
        """Process messages with processing delay."""
        if not self.stream_buffer:
            return

        current_time = time.time()
        messages_to_process = []

        # Find messages that have waited long enough
        while self.stream_buffer:
            message = self.stream_buffer[0]
            if current_time - message.timestamp >= self.stream_config.processing_delay:
                messages_to_process.append(self.stream_buffer.popleft())
            else:
                break

        # Process delayed messages
        for message in messages_to_process:
            partition_key = self._get_partition_key(message)
            window = await self._get_or_create_window(message, partition_key)
            await self._process_stream_message(message, window)

    async def _cleanup_old_windows(self):
        """Cleanup old completed windows."""
        # Keep only recent windows in memory
        max_completed_windows = 1000
        while len(self.completed_windows) > max_completed_windows:
            self.completed_windows.popleft()

    def _setup_default_aggregations(self):
        """Setup default stream aggregations."""
        # Message count aggregation
        async def message_count(window: StreamWindow) -> Dict[str, Any]:
            return {
                'message_count': len(window.messages),
                'time_window': (window.end_time or time.time()) - window.start_time,
                'messages_per_second': len(window.messages) / max(1, (window.end_time or time.time()) - window.start_time)
            }

        self.aggregations['message_count'] = message_count

        # Topic distribution aggregation
        async def topic_distribution(window: StreamWindow) -> Dict[str, Any]:
            topic_counts = defaultdict(int)
            for message in window.messages:
                topic_counts[message.topic] += 1
            return dict(topic_counts)

        self.aggregations['topic_distribution'] = topic_distribution

    # Public API methods
    def add_pattern(self, pattern: StreamPattern):
        """Add a stream pattern."""
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Added stream pattern: {pattern.name}")

    def remove_pattern(self, pattern_id: str):
        """Remove a stream pattern."""
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            logger.info(f"Removed stream pattern: {pattern_id}")

    def add_aggregation(self, name: str, aggregation_func: Callable):
        """Add a stream aggregation."""
        self.aggregations[name] = aggregation_func
        logger.info(f"Added stream aggregation: {name}")

    def remove_aggregation(self, name: str):
        """Remove a stream aggregation."""
        if name in self.aggregations:
            del self.aggregations[name]
            logger.info(f"Removed stream aggregation: {name}")

    def get_active_windows(self) -> Dict[str, StreamWindow]:
        """Get currently active windows."""
        return self.active_windows.copy()

    def get_stream_state(self) -> Dict[str, Any]:
        """Get current stream state."""
        return self.stream_state.copy()

    def get_stream_metrics(self) -> Dict[str, Any]:
        """Get stream processing metrics."""
        return {
            **self.stream_metrics,
            'active_windows': len(self.active_windows),
            'completed_windows': len(self.completed_windows),
            'buffer_size': len(self.stream_buffer),
            'patterns_registered': len(self.patterns),
            'aggregations_registered': len(self.aggregations)
        }


# Specialized stream processors

class TimeWindowStreamProcessor(StreamProcessor):
    """Stream processor with time-based windows."""

    def __init__(self, processor_id: str, window_size: float, **kwargs):
        stream_config = StreamConfig(
            window_type=WindowType.TIME,
            window_size=window_size,
            **kwargs
        )
        super().__init__(processor_id, stream_config, **kwargs)


class CountWindowStreamProcessor(StreamProcessor):
    """Stream processor with count-based windows."""

    def __init__(self, processor_id: str, window_size: int, **kwargs):
        stream_config = StreamConfig(
            window_type=WindowType.COUNT,
            window_size=window_size,
            **kwargs
        )
        super().__init__(processor_id, stream_config, **kwargs)


class SessionWindowStreamProcessor(StreamProcessor):
    """Stream processor with session-based windows."""

    def __init__(self, processor_id: str, **kwargs):
        stream_config = StreamConfig(
            window_type=WindowType.SESSION,
            **kwargs
        )
        super().__init__(processor_id, stream_config, **kwargs)


# Utility functions for creating common patterns

def create_threshold_pattern(pattern_id: str, field: str, threshold: float, operator: str = ">") -> StreamPattern:
    """Create a threshold-based pattern."""
    def condition(message: Message, window: StreamWindow) -> bool:
        value = message.payload.get(field, 0)
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        return False

    return StreamPattern(
        pattern_id=pattern_id,
        name=f"Threshold: {field} {operator} {threshold}",
        conditions=[condition]
    )


def create_frequency_pattern(pattern_id: str, message_type: MessageType, count: int, time_window: float) -> StreamPattern:
    """Create a frequency-based pattern."""
    def condition(message: Message, window: StreamWindow) -> bool:
        if message.type != message_type:
            return False

        # Count messages of this type in the window
        type_count = sum(1 for msg in window.messages if msg.type == message_type)
        return type_count >= count

    return StreamPattern(
        pattern_id=pattern_id,
        name=f"Frequency: {count} {message_type.value} in {time_window}s",
        conditions=[condition],
        time_window=time_window
    )


# Export main classes
__all__ = [
    'StreamProcessor',
    'StreamWindow',
    'StreamPattern',
    'StreamEvent',
    'StreamConfig',
    'StreamEventType',
    'WindowType',
    'TimeWindowStreamProcessor',
    'CountWindowStreamProcessor',
    'SessionWindowStreamProcessor',
    'create_threshold_pattern',
    'create_frequency_pattern'
]