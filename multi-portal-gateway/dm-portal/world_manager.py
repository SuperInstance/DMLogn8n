"""
World Manager - Manages the game world, locations, and global state.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

from ..database.models import WorldState
from ..database.database import get_db

logger = logging.getLogger(__name__)

@dataclass
class Location:
    """Represents a location in the game world."""
    id: str
    name: str
    description: str
    coordinates: Dict[str, float]  # x, y, z coordinates
    area_type: str  # dungeon, forest, city, etc.
    size: str  # small, medium, large
    climate: str
    population: int
    resources: List[str]
    dangers: List[str]
    points_of_interest: List[Dict[str, Any]]
    connected_locations: List[str]  # IDs of connected locations
    metadata: Dict[str, Any]

@dataclass
class WorldEnvironment:
    """Represents world environmental conditions."""
    time_of_day: str
    weather: str
    temperature: str
    visibility: str
    magical_aura: str
    ambient_sounds: List[str]
    special_conditions: List[str]

class WorldManager:
    """Manages the game world state and locations."""

    def __init__(self):
        self.world_state: Optional[WorldState] = None
        self.locations: Dict[str, Location] = {}
        self.environment: WorldEnvironment = WorldEnvironment(
            time_of_day="morning",
            weather="clear",
            temperature="mild",
            visibility="good",
            magical_aura="normal",
            ambient_sounds=["birds", "wind"],
            special_conditions=[]
        )
        self.global_events: List[Dict[str, Any]] = []
        self.world_history: List[Dict[str, Any]] = []
        self.is_initialized = False

    async def initialize(self):
        """Initialize the world manager."""
        logger.info("Initializing World Manager...")

        # Load existing world state
        await self._load_world_state()

        # Load locations
        await self._load_locations()

        # Create default world if none exists
        if not self.world_state:
            await self._create_default_world()

        self.is_initialized = True
        logger.info("World Manager initialized")

    async def _load_world_state(self):
        """Load world state from database."""
        try:
            db = next(get_db())
            world_state = db.query(WorldState).filter(WorldState.name == "main_world").first()

            if world_state:
                self.world_state = world_state
                self.environment = WorldEnvironment(**world_state.environment_state)
                self.global_events = world_state.world_events or []
                logger.info("Loaded existing world state")
            else:
                logger.info("No existing world state found")

        except Exception as e:
            logger.error(f"Failed to load world state: {str(e)}")

    async def _load_locations(self):
        """Load locations from database or create defaults."""
        try:
            # For now, create some default locations
            await self._create_default_locations()
        except Exception as e:
            logger.error(f"Failed to load locations: {str(e)}")

    async def _create_default_world(self):
        """Create a default world state."""
        logger.info("Creating default world state")

        try:
            db = next(get_db())
            world_state = WorldState(
                id=str(uuid.uuid4()),
                name="main_world",
                description="A world of adventure and mystery",
                current_location="starting_town",
                game_time="Day 1, Morning",
                weather="Clear",
                environment_state=asdict(self.environment),
                active_encounters=[],
                pending_events=[],
                world_events=[]
            )

            db.add(world_state)
            db.commit()
            db.refresh(world_state)

            self.world_state = world_state
            logger.info("Default world state created")

        except Exception as e:
            logger.error(f"Failed to create default world: {str(e)}")

    async def _create_default_locations(self):
        """Create default locations."""
        default_locations = [
            Location(
                id="starting_town",
                name="Starting Town",
                description="A small town surrounded by forests and mountains. It serves as a safe haven for adventurers.",
                coordinates={"x": 0, "y": 0, "z": 0},
                area_type="town",
                size="small",
                climate="temperate",
                population=500,
                resources=["food", "water", "basic supplies"],
                dangers=["occasional goblin raids"],
                points_of_interest=[
                    {"name": "Tavern", "type": "social", "description": "The local gathering place"},
                    {"name": "General Store", "type": "shop", "description": "Sells basic equipment"},
                    {"name": "Town Hall", "type": "government", "description": "Center of town administration"}
                ],
                connected_locations=["forest_entrance", "mountain_path"],
                metadata={"faction": "neutral", "security": "low"}
            ),
            Location(
                id="forest_entrance",
                name="Forest Entrance",
                description="The edge of a mysterious forest that stretches to the horizon.",
                coordinates={"x": 5, "y": 0, "z": 0},
                area_type="forest",
                size="large",
                climate="temperate",
                population=0,
                resources=["wood", "herbs", "wildlife"],
                dangers=["wolves", "bandits", "magical creatures"],
                points_of_interest=[
                    {"name": "Ancient Tree", "type": "landmark", "description": "A massive tree hundreds of years old"},
                    {"name": "Hidden Path", "type": "secret", "description": "A barely visible trail deeper into the forest"}
                ],
                connected_locations=["starting_town", "deep_forest"],
                metadata={"faction": "neutral", "security": "medium"}
            ),
            Location(
                id="mountain_path",
                name="Mountain Path",
                description="A winding path that leads up into the mountains beyond the town.",
                coordinates={"x": -3, "y": 2, "z": 0},
                area_type="mountain",
                size="medium",
                climate="cold",
                population=0,
                resources=["ore", "stone", "rare minerals"],
                dangers=["rockslides", "mountain lions", "harsh weather"],
                points_of_interest=[
                    {"name": "Abandoned Mine", "type": "dungeon", "description": "An old mine entrance, dark and foreboding"},
                    {"name": "Mountain Pass", "type": "route", "description": "A narrow pass through the mountains"}
                ],
                connected_locations=["starting_town", "mountain_peak"],
                metadata={"faction": "neutral", "security": "high"}
            )
        ]

        for location in default_locations:
            self.locations[location.id] = location

        logger.info(f"Created {len(default_locations)} default locations")

    async def get_world_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return {
            "id": self.world_state.id if self.world_state else None,
            "name": self.world_state.name if self.world_state else "Unknown",
            "description": self.world_state.description if self.world_state else "",
            "current_location": self.world_state.current_location if self.world_state else "unknown",
            "game_time": self.world_state.game_time if self.world_state else "Unknown",
            "weather": self.world_state.weather if self.world_state else "Unknown",
            "environment": asdict(self.environment),
            "locations": {loc_id: asdict(loc) for loc_id, loc in self.locations.items()},
            "global_events": self.global_events,
            "active_encounters": self.world_state.active_encounters if self.world_state else [],
            "pending_events": self.world_state.pending_events if self.world_state else [],
            "timestamp": datetime.now().isoformat()
        }

    async def update_world(self, world_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update world state."""
        try:
            # Update environment if provided
            if "environment" in world_data:
                env_data = world_data["environment"]
                for key, value in env_data.items():
                    if hasattr(self.environment, key):
                        setattr(self.environment, key, value)

            # Update world state fields
            if self.world_state:
                updates = {}

                if "current_location" in world_data:
                    updates["current_location"] = world_data["current_location"]
                    self.world_state.current_location = world_data["current_location"]

                if "game_time" in world_data:
                    updates["game_time"] = world_data["game_time"]
                    self.world_state.game_time = world_data["game_time"]

                if "weather" in world_data:
                    updates["weather"] = world_data["weather"]
                    self.world_state.weather = world_data["weather"]

                if "environment_state" in world_data:
                    updates["environment_state"] = world_data["environment_state"]

                # Update database
                db = next(get_db())
                db.query(WorldState).filter(WorldState.id == self.world_state.id).update(updates)
                db.commit()

            # Add to history
            self.world_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "world_update",
                "data": world_data
            })

            # Keep history limited
            if len(self.world_history) > 1000:
                self.world_history = self.world_history[-500:]

            logger.info(f"World state updated: {world_data}")
            return {"status": "success", "updated_fields": list(world_data.keys())}

        except Exception as e:
            logger.error(f"Failed to update world: {str(e)}")
            raise

    async def create_location(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new location."""
        try:
            location_id = location_data.get("id", str(uuid.uuid4()))

            location = Location(
                id=location_id,
                name=location_data.get("name", "Unknown Location"),
                description=location_data.get("description", ""),
                coordinates=location_data.get("coordinates", {"x": 0, "y": 0, "z": 0}),
                area_type=location_data.get("area_type", "unknown"),
                size=location_data.get("size", "medium"),
                climate=location_data.get("climate", "temperate"),
                population=location_data.get("population", 0),
                resources=location_data.get("resources", []),
                dangers=location_data.get("dangers", []),
                points_of_interest=location_data.get("points_of_interest", []),
                connected_locations=location_data.get("connected_locations", []),
                metadata=location_data.get("metadata", {})
            )

            self.locations[location_id] = location

            # Add to history
            self.world_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "location_created",
                "location_id": location_id,
                "data": asdict(location)
            })

            logger.info(f"Created new location: {location.name}")
            return asdict(location)

        except Exception as e:
            logger.error(f"Failed to create location: {str(e)}")
            raise

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get all locations."""
        return [asdict(location) for location in self.locations.values()]

    async def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific location."""
        if location_id in self.locations:
            return asdict(self.locations[location_id])
        return None

    async def update_location(self, location_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a location."""
        try:
            if location_id not in self.locations:
                raise ValueError(f"Location {location_id} not found")

            location = self.locations[location_id]

            # Update fields
            for key, value in update_data.items():
                if hasattr(location, key):
                    setattr(location, key, value)

            # Add to history
            self.world_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "location_updated",
                "location_id": location_id,
                "data": update_data
            })

            logger.info(f"Updated location {location_id}")
            return asdict(location)

        except Exception as e:
            logger.error(f"Failed to update location: {str(e)}")
            raise

    async def delete_location(self, location_id: str) -> Dict[str, Any]:
        """Delete a location."""
        try:
            if location_id not in self.locations:
                raise ValueError(f"Location {location_id} not found")

            location = self.locations.pop(location_id)

            # Remove from other locations' connections
            for loc in self.locations.values():
                if location_id in loc.connected_locations:
                    loc.connected_locations.remove(location_id)

            # Add to history
            self.world_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "location_deleted",
                "location_id": location_id,
                "data": asdict(location)
            })

            logger.info(f"Deleted location {location_id}")
            return {"status": "success", "deleted_location": asdict(location)}

        except Exception as e:
            logger.error(f"Failed to delete location: {str(e)}")
            raise

    async def process_edit(self, edit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process world edit requests."""
        edit_type = edit_data.get("type")

        if edit_type == "location_create":
            return await self.create_location(edit_data.get("location_data", {}))
        elif edit_type == "location_update":
            return await self.update_location(edit_data.get("location_id"), edit_data.get("update_data", {}))
        elif edit_type == "location_delete":
            return await self.delete_location(edit_data.get("location_id"))
        elif edit_type == "environment_update":
            return await self.update_world({"environment": edit_data.get("environment_data", {})})
        elif edit_type == "global_event":
            return await self.add_global_event(edit_data.get("event_data", {}))
        else:
            raise ValueError(f"Unknown edit type: {edit_type}")

    async def add_global_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a global event."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_data.get("event_type", "unknown"),
            "title": event_data.get("title", "Unknown Event"),
            "description": event_data.get("description", ""),
            "affected_locations": event_data.get("affected_locations", []),
            "effects": event_data.get("effects", {}),
            "duration": event_data.get("duration", "permanent"),
            "is_active": True
        }

        self.global_events.append(event)

        # Update world state
        if self.world_state:
            self.world_state.world_events.append(event)
            try:
                db = next(get_db())
                db.query(WorldState).filter(WorldState.id == self.world_state.id).update({
                    "world_events": self.world_state.world_events
                })
                db.commit()
            except Exception as e:
                logger.error(f"Failed to save global event: {str(e)}")

        logger.info(f"Added global event: {event['title']}")
        return event

    async def advance_time(self, time_units: int = 1) -> Dict[str, Any]:
        """Advance game time."""
        if not self.world_state:
            return {"error": "No world state loaded"}

        # Simple time advancement logic
        current_time = self.world_state.game_time
        # This would be more sophisticated in a real implementation
        new_time = f"Day {time_units + 1}, Morning"  # Simplified

        self.world_state.game_time = new_time

        # Update database
        try:
            db = next(get_db())
            db.query(WorldState).filter(WorldState.id == self.world_state.id).update({
                "game_time": new_time
            })
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save time advancement: {str(e)}")

        return {"old_time": current_time, "new_time": new_time}

    async def get_status(self) -> Dict[str, Any]:
        """Get world manager status."""
        return {
            "initialized": self.is_initialized,
            "world_loaded": self.world_state is not None,
            "location_count": len(self.locations),
            "global_events_count": len(self.global_events),
            "history_entries": len(self.world_history),
            "current_environment": asdict(self.environment)
        }