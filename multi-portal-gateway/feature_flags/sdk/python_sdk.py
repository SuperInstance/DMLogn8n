#!/usr/bin/env python3
"""
DMLogn8n Feature Flag Python SDK
Python client SDK for interacting with the feature flag service
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
import aiohttp
import requests
import redis
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlagType(Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

@dataclass
class FeatureFlagValue:
    flag_id: str
    value: Any
    variant: Optional[str] = None
    experiment_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ExperimentVariant:
    variant_id: str
    variant_name: str
    config: Dict[str, Any]
    is_control: bool

@dataclass
class ExperimentAssignment:
    experiment_id: str
    variant: ExperimentVariant
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class DMLogn8nSDK:
    """Python SDK for DMLogn8n Feature Flag Service"""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8001",
        sdk_key: str = None,
        user_id: str = None,
        context: Dict[str, Any] = None,
        cache_ttl: int = 300,  # 5 minutes
        enable_streaming: bool = False,
        redis_url: str = None
    ):
        self.api_base_url = api_base_url.rstrip('/')
        self.sdk_key = sdk_key
        self.user_id = user_id
        self.context = context or {}
        self.cache_ttl = cache_ttl
        self.enable_streaming = enable_streaming

        # Local cache
        self.flag_cache: Dict[str, FeatureFlagValue] = {}
        self.experiment_cache: Dict[str, ExperimentAssignment] = {}
        self.cache_timestamps: Dict[str, float] = {}

        # Redis cache (optional)
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")

        # Event handlers
        self.flag_change_handlers: Dict[str, List[Callable]] = {}
        self.experiment_handlers: List[Callable] = []

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        self.sync_session = requests.Session()

        # WebSocket connection for streaming
        self.websocket = None

    async def initialize(self):
        """Initialize the SDK"""
        try:
            # Create async session
            self.session = aiohttp.ClientSession()

            # Set up streaming if enabled
            if self.enable_streaming:
                await self._setup_streaming()

            logger.info("DMLogn8n SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SDK: {e}")
            raise

    async def close(self):
        """Close the SDK and clean up resources"""
        if self.session:
            await self.session.close()
        if self.websocket:
            await self.websocket.close()

    def set_user(self, user_id: str, context: Dict[str, Any] = None):
        """Set the current user and context"""
        self.user_id = user_id
        if context:
            self.context.update(context)

        # Clear user-specific caches
        self._clear_user_cache()

    def update_context(self, context: Dict[str, Any]):
        """Update user context"""
        self.context.update(context)
        self._clear_user_cache()

    async def get_flag(
        self,
        flag_name: str,
        default_value: Any = None,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> FeatureFlagValue:
        """Get a feature flag value"""
        effective_user_id = user_id or self.user_id
        effective_context = {**self.context, **(context or {})}

        if not effective_user_id:
            logger.warning("No user_id provided for flag evaluation")
            return FeatureFlagValue(
                flag_id="error",
                value=default_value,
                timestamp=datetime.utcnow()
            )

        # Check cache first
        cache_key = f"flag:{effective_user_id}:{flag_name}"
        cached_value = self._get_from_cache(cache_key)
        if cached_value and not self._is_cache_expired(cache_key):
            return cached_value

        try:
            # Make API request
            url = f"{self.api_base_url}/evaluate"
            payload = {
                "user_id": effective_user_id,
                "flag_name": flag_name,
                "context": effective_context
            }

            if self.sdk_key:
                headers = {"Authorization": f"Bearer {self.sdk_key}"}
            else:
                headers = {}

            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    flag_value = FeatureFlagValue(
                        flag_id=data['flag_id'],
                        value=data['value'],
                        variant=data.get('variant'),
                        experiment_id=data.get('experiment_id'),
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )
                else:
                    logger.error(f"Failed to get flag {flag_name}: {response.status}")
                    flag_value = FeatureFlagValue(
                        flag_id="error",
                        value=default_value,
                        timestamp=datetime.utcnow()
                    )

            # Cache the result
            self._set_cache(cache_key, flag_value)
            return flag_value

        except Exception as e:
            logger.error(f"Error getting flag {flag_name}: {e}")
            return FeatureFlagValue(
                flag_id="error",
                value=default_value,
                timestamp=datetime.utcnow()
            )

    def get_flag_sync(
        self,
        flag_name: str,
        default_value: Any = None,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> FeatureFlagValue:
        """Synchronous version of get_flag"""
        effective_user_id = user_id or self.user_id
        effective_context = {**self.context, **(context or {})}

        if not effective_user_id:
            logger.warning("No user_id provided for flag evaluation")
            return FeatureFlagValue(
                flag_id="error",
                value=default_value,
                timestamp=datetime.utcnow()
            )

        # Check cache first
        cache_key = f"flag:{effective_user_id}:{flag_name}"
        cached_value = self._get_from_cache(cache_key)
        if cached_value and not self._is_cache_expired(cache_key):
            return cached_value

        try:
            # Make synchronous API request
            url = f"{self.api_base_url}/evaluate"
            payload = {
                "user_id": effective_user_id,
                "flag_name": flag_name,
                "context": effective_context
            }

            headers = {"Authorization": f"Bearer {self.sdk_key}"} if self.sdk_key else {}
            response = self.sync_session.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                flag_value = FeatureFlagValue(
                    flag_id=data['flag_id'],
                    value=data['value'],
                    variant=data.get('variant'),
                    experiment_id=data.get('experiment_id'),
                    timestamp=datetime.fromisoformat(data['timestamp'])
                )
            else:
                logger.error(f"Failed to get flag {flag_name}: {response.status_code}")
                flag_value = FeatureFlagValue(
                    flag_id="error",
                    value=default_value,
                    timestamp=datetime.utcnow()
                )

            # Cache the result
            self._set_cache(cache_key, flag_value)
            return flag_value

        except Exception as e:
            logger.error(f"Error getting flag {flag_name}: {e}")
            return FeatureFlagValue(
                flag_id="error",
                value=default_value,
                timestamp=datetime.utcnow()
            )

    async def get_experiment_assignment(
        self,
        experiment_id: str,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> Optional[ExperimentAssignment]:
        """Get experiment assignment for a user"""
        effective_user_id = user_id or self.user_id
        effective_context = {**self.context, **(context or {})}

        if not effective_user_id:
            logger.warning("No user_id provided for experiment assignment")
            return None

        # Check cache first
        cache_key = f"experiment:{effective_user_id}:{experiment_id}"
        cached_assignment = self._get_from_cache(cache_key)
        if cached_assignment and not self._is_cache_expired(cache_key):
            return cached_assignment

        try:
            # This would integrate with the experiment manager
            # For now, return a placeholder
            assignment = ExperimentAssignment(
                experiment_id=experiment_id,
                variant=ExperimentVariant(
                    variant_id="control",
                    variant_name="Control",
                    config={},
                    is_control=True
                )
            )

            # Cache the assignment
            self._set_cache(cache_key, assignment)
            return assignment

        except Exception as e:
            logger.error(f"Error getting experiment assignment: {e}")
            return None

    def is_enabled(
        self,
        flag_name: str,
        default_value: bool = False,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """Check if a boolean flag is enabled (synchronous)"""
        flag_value = self.get_flag_sync(flag_name, default_value, user_id, context)
        return bool(flag_value.value)

    async def is_enabled_async(
        self,
        flag_name: str,
        default_value: bool = False,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """Check if a boolean flag is enabled (asynchronous)"""
        flag_value = await self.get_flag(flag_name, default_value, user_id, context)
        return bool(flag_value.value)

    def get_string_value(
        self,
        flag_name: str,
        default_value: str = "",
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Get string flag value (synchronous)"""
        flag_value = self.get_flag_sync(flag_name, default_value, user_id, context)
        return str(flag_value.value)

    async def get_string_value_async(
        self,
        flag_name: str,
        default_value: str = "",
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Get string flag value (asynchronous)"""
        flag_value = await self.get_flag(flag_name, default_value, user_id, context)
        return str(flag_value.value)

    def get_number_value(
        self,
        flag_name: str,
        default_value: float = 0.0,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> float:
        """Get number flag value (synchronous)"""
        flag_value = self.get_flag_sync(flag_name, default_value, user_id, context)
        try:
            return float(flag_value.value)
        except (ValueError, TypeError):
            return default_value

    async def get_number_value_async(
        self,
        flag_name: str,
        default_value: float = 0.0,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> float:
        """Get number flag value (asynchronous)"""
        flag_value = await self.get_flag(flag_name, default_value, user_id, context)
        try:
            return float(flag_value.value)
        except (ValueError, TypeError):
            return default_value

    def get_json_value(
        self,
        flag_name: str,
        default_value: Dict[str, Any] = None,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get JSON flag value (synchronous)"""
        if default_value is None:
            default_value = {}

        flag_value = self.get_flag_sync(flag_name, default_value, user_id, context)
        if isinstance(flag_value.value, dict):
            return flag_value.value
        elif isinstance(flag_value.value, str):
            try:
                return json.loads(flag_value.value)
            except json.JSONDecodeError:
                return default_value
        else:
            return default_value

    async def get_json_value_async(
        self,
        flag_name: str,
        default_value: Dict[str, Any] = None,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get JSON flag value (asynchronous)"""
        if default_value is None:
            default_value = {}

        flag_value = await self.get_flag(flag_name, default_value, user_id, context)
        if isinstance(flag_value.value, dict):
            return flag_value.value
        elif isinstance(flag_value.value, str):
            try:
                return json.loads(flag_value.value)
            except json.JSONDecodeError:
                return default_value
        else:
            return default_value

    async def track_metric(
        self,
        experiment_id: str,
        metric_name: str,
        value: float,
        user_id: str = None
    ):
        """Track a metric for an experiment"""
        effective_user_id = user_id or self.user_id

        if not effective_user_id:
            logger.warning("No user_id provided for metric tracking")
            return

        try:
            url = f"{self.api_base_url}/metrics"
            payload = {
                "experiment_id": experiment_id,
                "metric_name": metric_name,
                "value": value,
                "user_id": effective_user_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            headers = {"Authorization": f"Bearer {self.sdk_key}"} if self.sdk_key else {}
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to track metric: {response.status}")

        except Exception as e:
            logger.error(f"Error tracking metric: {e}")

    def add_flag_change_handler(self, flag_name: str, handler: Callable[[FeatureFlagValue], None]):
        """Add a handler for flag changes"""
        if flag_name not in self.flag_change_handlers:
            self.flag_change_handlers[flag_name] = []
        self.flag_change_handlers[flag_name].append(handler)

    def add_experiment_handler(self, handler: Callable[[ExperimentAssignment], None]):
        """Add a handler for experiment assignments"""
        self.experiment_handlers.append(handler)

    async def _setup_streaming(self):
        """Set up WebSocket connection for real-time updates"""
        try:
            ws_url = self.api_base_url.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws'
            self.websocket = await self.session.ws_connect(ws_url)

            # Start listening for messages
            asyncio.create_task(self._listen_for_updates())

        except Exception as e:
            logger.error(f"Failed to setup streaming: {e}")

    async def _listen_for_updates(self):
        """Listen for real-time updates via WebSocket"""
        try:
            async for message in self.websocket:
                data = json.loads(message.data)

                if data.get('type') == 'flag_change':
                    await self._handle_flag_change(data)
                elif data.get('type') == 'experiment_update':
                    await self._handle_experiment_update(data)

        except Exception as e:
            logger.error(f"Error listening for updates: {e}")

    async def _handle_flag_change(self, data: Dict[str, Any]):
        """Handle flag change notifications"""
        try:
            flag_data = data.get('flag', {})
            flag_name = flag_data.get('name')

            if flag_name and flag_name in self.flag_change_handlers:
                # Invalidate cache for this flag
                cache_keys_to_remove = [key for key in self.flag_cache.keys()
                                       if key.endswith(f":{flag_name}")]
                for cache_key in cache_keys_to_remove:
                    self.flag_cache.pop(cache_key, None)
                    self.cache_timestamps.pop(cache_key, None)

                # Call handlers
                flag_value = FeatureFlagValue(
                    flag_id=flag_data.get('id'),
                    value=flag_data.get('current_value'),
                    timestamp=datetime.fromisoformat(data.get('timestamp'))
                )

                for handler in self.flag_change_handlers[flag_name]:
                    try:
                        handler(flag_value)
                    except Exception as e:
                        logger.error(f"Error in flag change handler: {e}")

        except Exception as e:
            logger.error(f"Error handling flag change: {e}")

    async def _handle_experiment_update(self, data: Dict[str, Any]):
        """Handle experiment update notifications"""
        try:
            # Clear experiment cache
            experiment_cache_keys_to_remove = [key for key in self.experiment_cache.keys()
                                              if key.startswith(f"experiment:")]
            for cache_key in experiment_cache_keys_to_remove:
                self.experiment_cache.pop(cache_key, None)
                self.cache_timestamps.pop(cache_key, None)

            # Call experiment handlers
            for handler in self.experiment_handlers:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in experiment handler: {e}")

        except Exception as e:
            logger.error(f"Error handling experiment update: {e}")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check local cache
        if key in self.flag_cache:
            return self.flag_cache[key]
        elif key in self.experiment_cache:
            return self.experiment_cache[key]

        # Check Redis cache
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Error getting from Redis cache: {e}")

        return None

    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        # Set in local cache
        if isinstance(value, FeatureFlagValue):
            self.flag_cache[key] = value
        elif isinstance(value, ExperimentAssignment):
            self.experiment_cache[key] = value

        self.cache_timestamps[key] = time.time()

        # Set in Redis cache
        if self.redis_client:
            try:
                if isinstance(value, (FeatureFlagValue, ExperimentAssignment)):
                    self.redis_client.setex(
                        key,
                        self.cache_ttl,
                        json.dumps(asdict(value), default=str)
                    )
            except Exception as e:
                logger.warning(f"Error setting Redis cache: {e}")

    def _is_cache_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.cache_timestamps:
            return True

        return time.time() - self.cache_timestamps[key] > self.cache_ttl

    def _clear_user_cache(self):
        """Clear user-specific cache entries"""
        if self.user_id:
            # Clear flag cache for this user
            flag_keys_to_remove = [key for key in self.flag_cache.keys()
                                  if key.startswith(f"flag:{self.user_id}:")]
            for key in flag_keys_to_remove:
                self.flag_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)

            # Clear experiment cache for this user
            experiment_keys_to_remove = [key for key in self.experiment_cache.keys()
                                        if key.startswith(f"experiment:{self.user_id}:")]
            for key in experiment_keys_to_remove:
                self.experiment_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)

    async def flush_cache(self):
        """Flush all cache entries"""
        self.flag_cache.clear()
        self.experiment_cache.clear()
        self.cache_timestamps.clear()

        if self.redis_client:
            try:
                # Flush Redis cache (only SDK-related keys)
                pattern = "flag:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)

                pattern = "experiment:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Error flushing Redis cache: {e}")

# Convenience functions for common use cases
class FeatureFlags:
    """Convenience wrapper for common feature flag operations"""

    def __init__(self, sdk: DMLogn8nSDK):
        self.sdk = sdk

    def is_ai_model_enhanced(self, user_id: str = None) -> bool:
        """Check if enhanced AI model is enabled for user"""
        return self.sdk.is_enabled("ai_model_enhanced", False, user_id)

    def get_ai_model(self, user_id: str = None) -> str:
        """Get AI model to use for user"""
        return self.sdk.get_string_value("ai_model_selection", "gpt-4", user_id)

    def is_voice_chat_enabled(self, user_id: str = None) -> bool:
        """Check if voice chat is enabled for user"""
        return self.sdk.is_enabled("voice_chat_enabled", False, user_id)

    def get_combat_damage_method(self, user_id: str = None) -> str:
        """Get combat damage calculation method"""
        return self.sdk.get_string_value("combat_damage_calculation", "standard", user_id)

    def is_enhanced_ui_enabled(self, user_id: str = None) -> bool:
        """Check if enhanced UI is enabled for user"""
        return self.sdk.is_enabled("enhanced_ui_animations", False, user_id)

    def get_ai_creativity_level(self, user_id: str = None) -> float:
        """Get AI creativity level for user"""
        return self.sdk.get_number_value("ai_response_creativity", 0.7, user_id)

# Example usage
if __name__ == "__main__":
    import asyncio

    async def example_usage():
        # Initialize SDK
        sdk = DMLogn8nSDK(
            api_base_url="http://localhost:8001",
            user_id="user123",
            context={
                "level": 25,
                "is_premium": True,
                "platform": "web"
            }
        )

        await sdk.initialize()

        try:
            # Use feature flags
            if await sdk.is_enabled_async("voice_chat_enabled"):
                print("Voice chat is enabled for this user")

            ai_model = await sdk.get_string_value_async("ai_model_selection")
            print(f"Using AI model: {ai_model}")

            creativity = await sdk.get_number_value_async("ai_response_creativity")
            print(f"AI creativity level: {creativity}")

            # Use convenience wrapper
            flags = FeatureFlags(sdk)
            if flags.is_voice_chat_enabled():
                print("Voice chat is enabled (via convenience wrapper)")

            # Set up real-time updates
            def on_flag_change(flag_value):
                print(f"Flag changed: {flag_value.flag_id} = {flag_value.value}")

            sdk.add_flag_change_handler("voice_chat_enabled", on_flag_change)

            # Keep running to receive updates
            print("SDK initialized. Press Ctrl+C to stop...")
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await sdk.close()

    # Run the example
    asyncio.run(example_usage())