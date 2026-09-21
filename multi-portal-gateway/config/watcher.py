"""
File watcher for dynamic configuration updates in DMLogn8n multi-agent platform.
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from enum import Enum

from .config_manager import ConfigManager, config_manager


# Setup logging
logger = logging.getLogger(__name__)


class WatcherEventType(str, Enum):
    """File watcher event types."""
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    DIRECTORY_MODIFIED = "directory_modified"


@dataclass
class ConfigWatcherEvent:
    """Configuration watcher event."""
    event_type: WatcherEventType
    file_path: Path
    timestamp: datetime
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    source: str = "file_watcher"


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration files."""

    def __init__(self, config_watcher: 'ConfigFileWatcher'):
        self.config_watcher = config_watcher
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path, WatcherEventType.FILE_MODIFIED)

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path, WatcherEventType.FILE_CREATED)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path, WatcherEventType.FILE_DELETED)

    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            self._handle_file_event(event.dest_path, WatcherEventType.FILE_MOVED, event.src_path)

    def _handle_file_event(self, file_path: str, event_type: WatcherEventType, old_path: Optional[str] = None):
        """Handle file system events."""
        path = Path(file_path)

        # Check if this is a configuration file we should watch
        if not self.config_watcher.should_watch_file(path):
            return

        # Debounce rapid events
        if self.config_watcher.is_event_debounced(path, event_type):
            return

        try:
            # Calculate file info
            file_size = path.stat().st_size if path.exists() else None
            checksum = self.config_watcher.calculate_file_checksum(path) if path.exists() else None

            # Create event
            event = ConfigWatcherEvent(
                event_type=event_type,
                file_path=path,
                timestamp=datetime.now(timezone.utc),
                file_size=file_size,
                checksum=checksum
            )

            # Add to queue
            self.config_watcher.add_event_to_queue(event)

            self.logger.debug(f"File event detected: {event_type.value} - {path}")

        except Exception as e:
            self.logger.error(f"Error handling file event for {path}: {str(e)}")


class ConfigFileWatcher:
    """Configuration file watcher for dynamic updates."""

    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or config_manager
        self.logger = logging.getLogger(__name__)

        # Watcher settings
        self.enabled = os.getenv("CONFIG_WATCHER_ENABLED", "true").lower() == "true"
        self.debounce_time = float(os.getenv("CONFIG_WATCHER_DEBOUNCE", "1.0"))  # seconds
        self.check_interval = float(os.getenv("CONFIG_WATCHER_CHECK_INTERVAL", "5.0"))  # seconds
        self.max_queue_size = int(os.getenv("CONFIG_WATCHER_MAX_QUEUE_SIZE", "100"))

        # Paths to watch
        self.watch_paths: List[Path] = []
        self.watch_patterns: List[str] = ["*.yaml", "*.yml", "*.json"]
        self.ignore_patterns: List[str] = [
            "*.tmp", "*.bak", "*~", ".#*", "#*#",
            "*.swp", "*.swo", ".DS_Store"
        ]

        # Event handling
        self.event_queue: List[ConfigWatcherEvent] = []
        self.event_callbacks: List[Callable[[ConfigWatcherEvent], None]] = []
        self.last_event_times: Dict[str, float] = {}

        # Threading
        self.observer: Optional[Observer] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.queue_lock = threading.Lock()

        # Statistics
        self.stats = {
            'events_processed': 0,
            'config_reloads': 0,
            'errors': 0,
            'start_time': None
        }

    def add_watch_path(self, path: Path, recursive: bool = True) -> None:
        """Add a path to watch."""
        path = Path(path).resolve()

        if not path.exists():
            self.logger.warning(f"Watch path does not exist: {path}")
            return

        self.watch_paths.append((path, recursive))
        self.logger.info(f"Added watch path: {path} (recursive: {recursive})")

    def add_watch_pattern(self, pattern: str) -> None:
        """Add a file pattern to watch."""
        if pattern not in self.watch_patterns:
            self.watch_patterns.append(pattern)
            self.logger.info(f"Added watch pattern: {pattern}")

    def add_ignore_pattern(self, pattern: str) -> None:
        """Add an ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            self.logger.info(f"Added ignore pattern: {pattern}")

    def should_watch_file(self, file_path: Path) -> bool:
        """Check if a file should be watched."""
        # Check if file matches watch patterns
        if not any(file_path.match(pattern) for pattern in self.watch_patterns):
            return False

        # Check if file matches ignore patterns
        if any(file_path.match(pattern) for pattern in self.ignore_patterns):
            return False

        # Check if file is in watch paths
        for watch_path, recursive in self.watch_paths:
            if recursive:
                if watch_path in file_path.parents or file_path == watch_path:
                    return True
            else:
                if file_path.parent == watch_path:
                    return True

        return False

    def is_event_debounced(self, file_path: Path, event_type: WatcherEventType) -> bool:
        """Check if an event should be debounced."""
        key = f"{file_path}:{event_type.value}"
        current_time = time.time()

        if key in self.last_event_times:
            if current_time - self.last_event_times[key] < self.debounce_time:
                return True

        self.last_event_times[key] = current_time
        return False

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        import hashlib

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()[:16]
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {str(e)}")
            return ""

    def add_event_to_queue(self, event: ConfigWatcherEvent) -> None:
        """Add an event to the processing queue."""
        with self.queue_lock:
            if len(self.event_queue) >= self.max_queue_size:
                # Remove oldest event
                self.event_queue.pop(0)
                self.logger.warning("Event queue full, dropping oldest event")

            self.event_queue.append(event)

    def add_event_callback(self, callback: Callable[[ConfigWatcherEvent], None]) -> None:
        """Add an event callback."""
        self.event_callbacks.append(callback)

    def start(self) -> None:
        """Start the file watcher."""
        if not self.enabled:
            self.logger.info("File watcher disabled")
            return

        if self.observer and self.observer.is_alive():
            self.logger.warning("File watcher already running")
            return

        self.logger.info("Starting configuration file watcher...")
        self.stats['start_time'] = datetime.now(timezone.utc)

        try:
            # Set up default watch paths
            if not self.watch_paths:
                config_dir = Path(__file__).parent
                self.add_watch_path(config_dir)
                self.add_watch_path(config_dir / "environments")
                self.add_watch_path(config_dir.parent / "config_override.yaml")

            # Create and start observer
            self.observer = Observer()
            handler = ConfigFileHandler(self)

            for watch_path, recursive in self.watch_paths:
                self.observer.schedule(handler, str(watch_path), recursive=recursive)

            self.observer.start()

            # Start event processing thread
            self.stop_event.clear()
            self.processing_thread = threading.Thread(
                target=self._process_events,
                name="ConfigWatcherProcessor",
                daemon=True
            )
            self.processing_thread.start()

            self.logger.info("File watcher started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start file watcher: {str(e)}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the file watcher."""
        if not self.observer:
            return

        self.logger.info("Stopping configuration file watcher...")

        # Stop observer
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)

        # Stop processing thread
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.processing_thread.join(timeout=5)

        self.observer = None
        self.processing_thread = None

        # Clear queue
        with self.queue_lock:
            self.event_queue.clear()

        self.logger.info("File watcher stopped")

    def _process_events(self) -> None:
        """Process events from the queue."""
        while not self.stop_event.is_set():
            try:
                events_to_process = []

                # Get events from queue
                with self.queue_lock:
                    if self.event_queue:
                        events_to_process = self.event_queue.copy()
                        self.event_queue.clear()

                # Process events
                for event in events_to_process:
                    self._handle_config_event(event)
                    self.stats['events_processed'] += 1

                    # Call callbacks
                    for callback in self.event_callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            self.logger.error(f"Error in event callback: {str(e)}")

                # Sleep before next iteration
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error processing events: {str(e)}")
                self.stats['errors'] += 1
                time.sleep(self.check_interval)

    def _handle_config_event(self, event: ConfigWatcherEvent) -> None:
        """Handle a configuration file event."""
        try:
            self.logger.debug(f"Processing config event: {event.event_type.value} - {event.file_path}")

            # Determine configuration type from file path
            config_type = self._determine_config_type(event.file_path)

            if config_type:
                self.logger.info(f"Configuration change detected: {config_type}")

                # Check if it's a relevant change
                if self._is_relevant_change(event):
                    # Reload configuration
                    try:
                        self.config_manager.reload_configuration()
                        self.stats['config_reloads'] += 1
                        self.logger.info(f"Configuration reloaded due to {event.event_type.value} in {event.file_path}")

                        # Trigger change notification
                        self._notify_config_change(config_type, event)

                    except Exception as e:
                        self.logger.error(f"Failed to reload configuration: {str(e)}")
                        self.stats['errors'] += 1
                else:
                    self.logger.debug(f"Ignoring irrelevant change in {event.file_path}")
            else:
                self.logger.debug(f"Ignoring non-config file: {event.file_path}")

        except Exception as e:
            self.logger.error(f"Error handling config event: {str(e)}")
            self.stats['errors'] += 1

    def _determine_config_type(self, file_path: Path) -> Optional[str]:
        """Determine configuration type from file path."""
        file_name = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()

        # Check for main configuration files
        if 'database' in file_name or parent_dir == 'database':
            return 'database'
        elif 'ai_model' in file_name or 'model' in file_name or parent_dir == 'ai_models':
            return 'ai_models'
        elif 'monitoring' in file_name or parent_dir == 'monitoring':
            return 'monitoring'

        # Check for environment configurations
        if parent_dir == 'environments':
            return 'environment'

        # Check for override configurations
        if 'override' in file_name:
            return 'override'

        return None

    def _is_relevant_change(self, event: ConfigWatcherEvent) -> bool:
        """Check if a change is relevant for configuration reload."""
        # For now, we consider all config file changes relevant
        # In the future, we could be more sophisticated about this
        return True

    def _notify_config_change(self, config_type: str, event: ConfigWatcherEvent) -> None:
        """Notify about configuration changes."""
        # This could trigger additional notifications, webhook calls, etc.
        pass

    def get_statistics(self) -> Dict[str, any]:
        """Get watcher statistics."""
        stats = self.stats.copy()
        if stats['start_time']:
            stats['uptime_seconds'] = (datetime.now(timezone.utc) - stats['start_time']).total_seconds()
        stats['watch_paths'] = [str(path) for path, _ in self.watch_paths]
        stats['watch_patterns'] = self.watch_patterns
        stats['queue_size'] = len(self.event_queue)
        stats['is_running'] = self.observer and self.observer.is_alive()
        return stats

    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self.observer and self.observer.is_alive()

    def force_reload(self) -> None:
        """Force a configuration reload."""
        self.logger.info("Forcing configuration reload...")
        try:
            self.config_manager.reload_configuration()
            self.stats['config_reloads'] += 1
            self.logger.info("Force reload completed successfully")
        except Exception as e:
            self.logger.error(f"Force reload failed: {str(e)}")
            self.stats['errors'] += 1
            raise


# Global file watcher instance
config_watcher = ConfigFileWatcher()


# Convenience functions
def start_config_watcher() -> None:
    """Start the global configuration watcher."""
    config_watcher.start()


def stop_config_watcher() -> None:
    """Stop the global configuration watcher."""
    config_watcher.stop()


def add_config_watch_callback(callback: Callable[[ConfigWatcherEvent], None]) -> None:
    """Add a callback to configuration watch events."""
    config_watcher.add_event_callback(callback)


class ConfigWatcherManager:
    """Manager for configuration watcher lifecycle."""

    def __init__(self):
        self.watcher = config_watcher
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        """Context manager entry."""
        self.watcher.start()
        return self.watcher

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.watcher.stop()


# Usage example context manager
def with_config_watcher():
    """Context manager for using config watcher."""
    return ConfigWatcherManager()