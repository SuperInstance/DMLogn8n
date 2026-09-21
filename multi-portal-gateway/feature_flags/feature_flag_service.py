#!/usr/bin/env python3
"""
DMLogn8n Feature Flag Service
Provides real-time feature flag management with A/B testing capabilities
"""

import asyncio
import json
import logging
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import aioredis
import yaml
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio_mqtt as aiomqtt
import numpy as np
from scipy import stats
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FlagType(Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

class RolloutStrategy(Enum):
    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    SEGMENT = "segment"
    GRADUAL = "gradual"

@dataclass
class FeatureFlag:
    id: str
    name: str
    description: str
    flag_type: FlagType
    default_value: Any
    current_value: Any
    rollout_strategy: RolloutStrategy
    rollout_percentage: float = 0.0
    enabled_users: List[str] = None
    segments: List[str] = None
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = "system"
    updated_by: str = "system"
    version: int = 1

    def __post_init__(self):
        if self.enabled_users is None:
            self.enabled_users = []
        if self.segments is None:
            self.segments = []
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class FlagEvaluation:
    flag_id: str
    user_id: str
    value: Any
    variant: Optional[str] = None
    experiment_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class FeatureFlagRequest(BaseModel):
    user_id: str
    flag_name: str
    context: Dict[str, Any] = Field(default_factory=dict)

class FeatureFlagResponse(BaseModel):
    flag_id: str
    value: Any
    variant: Optional[str] = None
    experiment_id: Optional[str] = None
    timestamp: datetime

class FeatureFlagService:
    """Main feature flag management service"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.flags: Dict[str, FeatureFlag] = {}
        self.websocket_connections: List[WebSocket] = []
        self.mqtt_client: Optional[aiomqtt.Client] = None

        # Event handlers
        self.flag_change_handlers: Dict[str, List[Callable]] = {}
        self.evaluation_handlers: List[Callable] = []

        # Load default flags
        self._load_default_flags()

    async def initialize(self):
        """Initialize the service with Redis connections"""
        try:
            # Initialize Redis clients
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)

            # Load flags from Redis
            await self._load_flags_from_redis()

            # Start background tasks
            asyncio.create_task(self._websocket_manager())
            asyncio.create_task(self._flag_sync_task())

            logger.info("Feature flag service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize feature flag service: {e}")
            raise

    def _load_default_flags(self):
        """Load default feature flags"""
        default_flags = [
            FeatureFlag(
                id="ai_model_selection",
                name="AI Model Selection",
                description="Controls which AI model to use for dialogue generation",
                flag_type=FlagType.STRING,
                default_value="gpt-4",
                current_value="gpt-4",
                rollout_strategy=RolloutStrategy.ALL_USERS,
                tags=["ai", "dialogue"]
            ),
            FeatureFlag(
                id="combat_damage_calculation",
                name="Combat Damage Calculation",
                description="Controls combat damage calculation method",
                flag_type=FlagType.STRING,
                default_value="standard",
                current_value="standard",
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=50.0,
                tags=["combat", "gameplay"]
            ),
            FeatureFlag(
                id="enhanced_ui_animations",
                name="Enhanced UI Animations",
                description="Enable enhanced UI animations and transitions",
                flag_type=FlagType.BOOLEAN,
                default_value=False,
                current_value=False,
                rollout_strategy=RolloutStrategy.GRADUAL,
                rollout_percentage=10.0,
                tags=["ui", "ux"]
            ),
            FeatureFlag(
                id="voice_chat_enabled",
                name="Voice Chat Enabled",
                description="Enable voice chat functionality",
                flag_type=FlagType.BOOLEAN,
                default_value=False,
                current_value=False,
                rollout_strategy=RolloutStrategy.SEGMENT,
                segments=["premium_users", "beta_testers"],
                tags=["voice", "communication"]
            ),
            FeatureFlag(
                id="ai_response_creativity",
                name="AI Response Creativity",
                description="Controls AI response creativity level",
                flag_type=FlagType.NUMBER,
                default_value=0.7,
                current_value=0.7,
                rollout_strategy=RolloutStrategy.ALL_USERS,
                tags=["ai", "creativity"]
            )
        ]

        for flag in default_flags:
            self.flags[flag.id] = flag

    async def _load_flags_from_redis(self):
        """Load feature flags from Redis"""
        try:
            flag_data = await self.async_redis_client.hgetall("feature_flags")
            for flag_id, flag_json in flag_data.items():
                flag_dict = json.loads(flag_json)
                flag = FeatureFlag(
                    id=flag_dict['id'],
                    name=flag_dict['name'],
                    description=flag_dict['description'],
                    flag_type=FlagType(flag_dict['flag_type']),
                    default_value=flag_dict['default_value'],
                    current_value=flag_dict['current_value'],
                    rollout_strategy=RolloutStrategy(flag_dict['rollout_strategy']),
                    rollout_percentage=flag_dict.get('rollout_percentage', 0.0),
                    enabled_users=flag_dict.get('enabled_users', []),
                    segments=flag_dict.get('segments', []),
                    tags=flag_dict.get('tags', []),
                    created_at=datetime.fromisoformat(flag_dict['created_at']),
                    updated_at=datetime.fromisoformat(flag_dict['updated_at']),
                    created_by=flag_dict.get('created_by', 'system'),
                    updated_by=flag_dict.get('updated_by', 'system'),
                    version=flag_dict.get('version', 1)
                )
                self.flags[flag_id] = flag
            logger.info(f"Loaded {len(self.flags)} feature flags from Redis")
        except Exception as e:
            logger.warning(f"Failed to load flags from Redis: {e}")

    async def _save_flag_to_redis(self, flag: FeatureFlag):
        """Save feature flag to Redis"""
        try:
            flag_dict = asdict(flag)
            flag_dict['flag_type'] = flag.flag_type.value
            flag_dict['rollout_strategy'] = flag.rollout_strategy.value
            flag_dict['created_at'] = flag.created_at.isoformat()
            flag_dict['updated_at'] = flag.updated_at.isoformat()

            await self.async_redis_client.hset(
                "feature_flags",
                flag.id,
                json.dumps(flag_dict)
            )

            # Publish update
            await self.async_redis_client.publish(
                "flag_updates",
                json.dumps({
                    "type": "flag_updated",
                    "flag_id": flag.id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
        except Exception as e:
            logger.error(f"Failed to save flag {flag.id} to Redis: {e}")
            raise

    def evaluate_flag(self, flag_name: str, user_id: str, context: Dict[str, Any] = None) -> FlagEvaluation:
        """Evaluate a feature flag for a specific user"""
        if context is None:
            context = {}

        # Find flag by name
        flag = None
        for f in self.flags.values():
            if f.name == flag_name:
                flag = f
                break

        if not flag:
            # Return default if flag not found
            return FlagEvaluation(
                flag_id="not_found",
                user_id=user_id,
                value=None
            )

        value = flag.default_value
        variant = None

        # Apply rollout strategy
        if flag.rollout_strategy == RolloutStrategy.ALL_USERS:
            value = flag.current_value
        elif flag.rollout_strategy == RolloutStrategy.PERCENTAGE:
            if self._user_in_percentage(user_id, flag.rollout_percentage):
                value = flag.current_value
        elif flag.rollout_strategy == RolloutStrategy.USER_LIST:
            if user_id in flag.enabled_users:
                value = flag.current_value
        elif flag.rollout_strategy == RolloutStrategy.SEGMENT:
            if self._user_in_segment(user_id, flag.segments, context):
                value = flag.current_value
        elif flag.rollout_strategy == RolloutStrategy.GRADUAL:
            # Gradual rollout based on user hash and time
            if self._user_in_gradual_rollout(user_id, flag):
                value = flag.current_value

        evaluation = FlagEvaluation(
            flag_id=flag.id,
            user_id=user_id,
            value=value,
            variant=variant
        )

        # Log evaluation
        self._log_evaluation(evaluation)

        # Call evaluation handlers
        for handler in self.evaluation_handlers:
            try:
                handler(evaluation)
            except Exception as e:
                logger.error(f"Error in evaluation handler: {e}")

        return evaluation

    def _user_in_percentage(self, user_id: str, percentage: float) -> bool:
        """Check if user is in rollout percentage"""
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < percentage

    def _user_in_segment(self, user_id: str, segments: List[str], context: Dict[str, Any]) -> bool:
        """Check if user belongs to any of the specified segments"""
        # This would integrate with the segmentation service
        # For now, simple segment checking
        user_segments = context.get('segments', [])

        if 'premium_users' in segments and context.get('is_premium'):
            return True
        if 'beta_testers' in segments and context.get('is_beta_tester'):
            return True
        if 'new_users' in segments and context.get('account_age_days', 0) < 7:
            return True
        if 'power_users' in segments and context.get('sessions_per_week', 0) > 10:
            return True

        return any(segment in user_segments for segment in segments)

    def _user_in_gradual_rollout(self, user_id: str, flag: FeatureFlag) -> bool:
        """Check if user is in gradual rollout based on time and percentage"""
        days_since_creation = (datetime.utcnow() - flag.created_at).days
        gradual_percentage = min(100.0, days_since_creation * 10.0)  # 10% per day
        return self._user_in_percentage(user_id, gradual_percentage)

    def _log_evaluation(self, evaluation: FlagEvaluation):
        """Log flag evaluation for analytics"""
        try:
            log_entry = {
                "flag_id": evaluation.flag_id,
                "user_id": evaluation.user_id,
                "value": evaluation.value,
                "variant": evaluation.variant,
                "experiment_id": evaluation.experiment_id,
                "timestamp": evaluation.timestamp.isoformat()
            }

            # Log to Redis stream
            if self.redis_client:
                self.redis_client.xadd(
                    "flag_evaluations",
                    log_entry,
                    maxlen=10000  # Keep last 10k evaluations
                )
        except Exception as e:
            logger.error(f"Failed to log flag evaluation: {e}")

    async def create_flag(self, flag_data: Dict[str, Any]) -> FeatureFlag:
        """Create a new feature flag"""
        flag_id = str(uuid.uuid4())

        flag = FeatureFlag(
            id=flag_id,
            name=flag_data['name'],
            description=flag_data['description'],
            flag_type=FlagType(flag_data['flag_type']),
            default_value=flag_data['default_value'],
            current_value=flag_data.get('current_value', flag_data['default_value']),
            rollout_strategy=RolloutStrategy(flag_data['rollout_strategy']),
            rollout_percentage=flag_data.get('rollout_percentage', 0.0),
            enabled_users=flag_data.get('enabled_users', []),
            segments=flag_data.get('segments', []),
            tags=flag_data.get('tags', []),
            created_by=flag_data.get('created_by', 'system'),
            updated_by=flag_data.get('created_by', 'system')
        )

        self.flags[flag_id] = flag
        await self._save_flag_to_redis(flag)

        # Notify clients
        await self._notify_flag_change(flag, "created")

        logger.info(f"Created feature flag: {flag.name}")
        return flag

    async def update_flag(self, flag_id: str, updates: Dict[str, Any]) -> FeatureFlag:
        """Update an existing feature flag"""
        if flag_id not in self.flags:
            raise HTTPException(status_code=404, detail=f"Flag {flag_id} not found")

        flag = self.flags[flag_id]

        # Update fields
        for field, value in updates.items():
            if hasattr(flag, field) and field not in ['id', 'created_at']:
                if field in ['flag_type', 'rollout_strategy']:
                    if field == 'flag_type':
                        setattr(flag, field, FlagType(value))
                    else:
                        setattr(flag, field, RolloutStrategy(value))
                else:
                    setattr(flag, field, value)

        flag.updated_at = datetime.utcnow()
        flag.version += 1

        await self._save_flag_to_redis(flag)

        # Notify clients
        await self._notify_flag_change(flag, "updated")

        logger.info(f"Updated feature flag: {flag.name}")
        return flag

    async def delete_flag(self, flag_id: str) -> bool:
        """Delete a feature flag"""
        if flag_id not in self.flags:
            raise HTTPException(status_code=404, detail=f"Flag {flag_id} not found")

        flag = self.flags.pop(flag_id)

        # Remove from Redis
        await self.async_redis_client.hdel("feature_flags", flag_id)

        # Notify clients
        await self._notify_flag_change(flag, "deleted")

        logger.info(f"Deleted feature flag: {flag.name}")
        return True

    def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags"""
        return list(self.flags.values())

    def get_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Get a specific feature flag"""
        return self.flags.get(flag_id)

    async def _notify_flag_change(self, flag: FeatureFlag, action: str):
        """Notify connected clients of flag changes"""
        message = {
            "type": "flag_change",
            "action": action,
            "flag": asdict(flag),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to WebSocket connections
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.append(websocket)

        # Remove disconnected websockets
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)

        # Call flag change handlers
        if flag.id in self.flag_change_handlers:
            for handler in self.flag_change_handlers[flag.id]:
                try:
                    handler(flag, action)
                except Exception as e:
                    logger.error(f"Error in flag change handler: {e}")

    async def _websocket_manager(self):
        """Manage WebSocket connections"""
        logger.info("WebSocket manager started")

    async def _flag_sync_task(self):
        """Background task to sync flags"""
        while True:
            try:
                # Periodically sync with Redis
                await self._load_flags_from_redis()
                await asyncio.sleep(60)  # Sync every minute
            except Exception as e:
                logger.error(f"Error in flag sync task: {e}")
                await asyncio.sleep(10)

    def add_flag_change_handler(self, flag_id: str, handler: Callable):
        """Add a handler for flag changes"""
        if flag_id not in self.flag_change_handlers:
            self.flag_change_handlers[flag_id] = []
        self.flag_change_handlers[flag_id].append(handler)

    def add_evaluation_handler(self, handler: Callable):
        """Add a handler for flag evaluations"""
        self.evaluation_handlers.append(handler)

    def get_flag_stats(self, flag_id: str, days: int = 7) -> Dict[str, Any]:
        """Get statistics for a specific flag"""
        try:
            # Get evaluations from Redis stream
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            evaluations = self.redis_client.xrange(
                "flag_evaluations",
                min=int(start_time.timestamp() * 1000),
                max=int(end_time.timestamp() * 1000)
            )

            # Calculate stats
            total_evaluations = 0
            true_count = 0
            user_counts = {}

            for eval_id, eval_data in evaluations:
                if eval_data.get('flag_id') == flag_id:
                    total_evaluations += 1
                    user_id = eval_data.get('user_id')
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1

                    if eval_data.get('value') in [True, 'true', 'enabled']:
                        true_count += 1

            return {
                "flag_id": flag_id,
                "total_evaluations": total_evaluations,
                "unique_users": len(user_counts),
                "true_percentage": (true_count / total_evaluations * 100) if total_evaluations > 0 else 0,
                "evaluations_per_user": sum(user_counts.values()) / len(user_counts) if user_counts else 0,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting flag stats: {e}")
            return {"error": str(e)}

# FastAPI application
app = FastAPI(title="DMLogn8n Feature Flag Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
feature_service = FeatureFlagService()

@app.on_event("startup")
async def startup_event():
    await feature_service.initialize()

@app.post("/evaluate")
async def evaluate_flag(request: FeatureFlagRequest) -> FeatureFlagResponse:
    """Evaluate a feature flag for a user"""
    evaluation = feature_service.evaluate_flag(
        request.flag_name,
        request.user_id,
        request.context
    )

    return FeatureFlagResponse(
        flag_id=evaluation.flag_id,
        value=evaluation.value,
        variant=evaluation.variant,
        experiment_id=evaluation.experiment_id,
        timestamp=evaluation.timestamp
    )

@app.get("/flags")
async def get_all_flags():
    """Get all feature flags"""
    return {"flags": [asdict(flag) for flag in feature_service.get_all_flags()]}

@app.get("/flags/{flag_id}")
async def get_flag(flag_id: str):
    """Get a specific feature flag"""
    flag = feature_service.get_flag(flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return asdict(flag)

@app.post("/flags")
async def create_flag(flag_data: Dict[str, Any]):
    """Create a new feature flag"""
    flag = await feature_service.create_flag(flag_data)
    return asdict(flag)

@app.put("/flags/{flag_id}")
async def update_flag(flag_id: str, updates: Dict[str, Any]):
    """Update a feature flag"""
    flag = await feature_service.update_flag(flag_id, updates)
    return asdict(flag)

@app.delete("/flags/{flag_id}")
async def delete_flag(flag_id: str):
    """Delete a feature flag"""
    await feature_service.delete_flag(flag_id)
    return {"message": "Flag deleted successfully"}

@app.get("/flags/{flag_id}/stats")
async def get_flag_stats(flag_id: str, days: int = 7):
    """Get statistics for a feature flag"""
    return feature_service.get_flag_stats(flag_id, days)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time flag updates"""
    await websocket.accept()
    feature_service.websocket_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        feature_service.websocket_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)