"""
Parallel World Simulation Engine
Simulates multiple regions and world states in parallel
"""

import asyncio
import numpy as np
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import defaultdict, deque
import uuid
import json
import math
import random
from enum import Enum


class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"


class TimeOfDay(Enum):
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    NIGHT = "night"
    MIDNIGHT = "midnight"


@dataclass
class RegionState:
    """State of a world region"""
    region_id: str
    name: str
    population: int
    economy: float  # 0-100
    stability: float  # 0-100
    weather: WeatherType
    temperature: float  # Celsius
    time_of_day: TimeOfDay
    resources: Dict[str, float] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    players: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class WorldEvent:
    """Event occurring in the world"""
    event_id: str
    region_id: str
    event_type: str
    description: str
    impact: Dict[str, float] = field(default_factory=dict)
    duration: Optional[float] = None  # seconds
    start_time: datetime = field(default_factory=datetime.now)
    participants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationTick:
    """Single simulation tick"""
    tick_number: int
    timestamp: datetime
    delta_time: float  # seconds since last tick
    world_time: datetime  # In-game time
    region_updates: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ParallelWorldSimulation:
    """Parallel world simulation engine"""

    def __init__(self,
                 num_regions: int = 100,
                 tick_rate: float = 10.0,  # ticks per second
                 simulation_speed: float = 3600.0):  # 1 real second = 1 game hour

        self.num_regions = num_regions
        self.tick_rate = tick_rate
        self.simulation_speed = simulation_speed
        self.tick_interval = 1.0 / tick_rate

        # World state
        self.regions: Dict[str, RegionState] = {}
        self.active_events: Dict[str, WorldEvent] = {}
        self.event_history: deque = deque(maxlen=10000)

        # Time tracking
        self.current_world_time = datetime.now().replace(hour=6, minute=0, second=0)  # Start at 6 AM
        self.tick_counter = 0
        self.last_tick_time = datetime.now()

        # Parallel processing
        self.region_processors: Dict[str, asyncio.Task] = {}
        self.event_processors: List[asyncio.Task] = []
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        self.process_pool = ProcessPoolExecutor(max_processes=10)

        # Simulation queues
        self.region_update_queue = asyncio.Queue(maxsize=10000)
        self.event_queue = asyncio.Queue(maxsize=5000)
        self.player_action_queue = asyncio.Queue(maxsize=2000)
        self.npc_action_queue = asyncio.Queue(maxsize=5000)

        # Shared state
        self.world_metrics = {
            "total_population": 0,
            "average_economy": 0.0,
            "average_stability": 0.0,
            "active_events": 0,
            "processed_events": 0,
            "simulation_ticks": 0
        }

        # Weather patterns
        self.weather_patterns = self._initialize_weather_patterns()
        self.regional_climates = {}

        # NPC behavior
        self.npc_behaviors = {}
        self.npc_schedules = {}

        # Economic simulation
        self.trade_routes = {}
        self.market_prices = defaultdict(lambda: defaultdict(float))
        self.supply_demand = defaultdict(lambda: defaultdict(lambda: {"supply": 100, "demand": 100}))

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False

    async def initialize(self):
        """Initialize the world simulation"""
        logger.info(f"Initializing parallel world simulation with {self.num_regions} regions")

        # Create regions
        await self._create_regions()

        # Initialize weather patterns
        await self._initialize_climates()

        # Initialize NPC behaviors
        await self._initialize_npc_behaviors()

        # Initialize economy
        await self._initialize_economy()

        # Start background processors
        await self._start_processors()

        self.is_running = True
        logger.info("World simulation initialized")

    async def _create_regions(self):
        """Create world regions"""
        region_types = ["city", "town", "village", "wilderness", "dungeon", "special"]
        region_names = [
            "Capital City", "Merchant's Haven", "Frostfall", "Sunstone Village",
            "Shadowmere", "Dragon's Peak", "Emerald Forest", "Ironforge",
            "Silvermoon", "Raven's Roost", "Golden Fields", "Mystic Woods"
        ]

        for i in range(self.num_regions):
            region_type = random.choice(region_types)
            base_name = random.choice(region_names)

            region = RegionState(
                region_id=f"region_{i}",
                name=f"{base_name} {i}" if i >= len(region_names) else base_name,
                population=random.randint(50, 50000) if region_type in ["city", "town"] else random.randint(10, 500),
                economy=random.uniform(20, 100),
                stability=random.uniform(30, 100),
                weather=random.choice(list(WeatherType)),
                temperature=random.uniform(-10, 35),
                time_of_day=TimeOfDay.MORNING,
                resources={
                    "gold": random.uniform(100, 10000),
                    "food": random.uniform(500, 5000),
                    "wood": random.uniform(200, 2000),
                    "stone": random.uniform(100, 1500),
                    "iron": random.uniform(50, 500)
                }
            )

            # Add NPCs based on population
            num_npcs = min(region.population // 10, 100)
            region.npcs = [f"npc_{uuid.uuid4().hex[:8]}" for _ in range(num_npcs)]

            self.regions[region.region_id] = region

            # Start region processor
            processor = asyncio.create_task(self._process_region(region.region_id))
            self.region_processors[region.region_id] = processor

    async def _initialize_climates(self):
        """Initialize regional climate patterns"""
        climate_types = ["temperate", "tropical", "arctic", "desert", "mountain", "coastal"]

        for region_id, region in self.regions.items():
            climate = random.choice(climate_types)
            self.regional_climates[region_id] = climate

            # Set initial weather based on climate
            if climate == "arctic":
                region.weather = random.choice([WeatherType.SNOW, WeatherType.CLEAR, WeatherType.CLOUDY])
                region.temperature = random.uniform(-20, 5)
            elif climate == "desert":
                region.weather = random.choice([WeatherType.CLEAR, WeatherType.CLOUDY])
                region.temperature = random.uniform(15, 45)
            elif climate == "tropical":
                region.weather = random.choice([WeatherType.CLEAR, WeatherType.RAIN, WeatherType.STORM])
                region.temperature = random.uniform(20, 35)
            else:
                region.weather = random.choice(list(WeatherType))
                region.temperature = random.uniform(-5, 30)

    async def _initialize_npc_behaviors(self):
        """Initialize NPC behavior patterns"""
        behavior_types = ["merchant", "guard", "farmer", "artisan", "noble", "thief", "priest", "scholar"]
        schedules = {
            "merchant": {"work": [8, 12, 14, 18], "rest": [0, 6, 19, 23]},
            "guard": {"patrol": [6, 12, 18, 23], "rest": [0, 5]},
            "farmer": {"work": [5, 11, 13, 19], "rest": [0, 4, 20, 23]},
            "artisan": {"work": [7, 12, 13, 19], "rest": [0, 6, 20, 23]},
            "noble": {"social": [10, 14, 18, 22], "rest": [0, 8, 23]},
            "thief": {"active": [20, 5], "hide": [5, 20]},
            "priest": {"prayer": [6, 8, 18, 20], "work": [9, 17], "rest": [0, 5, 21, 23]},
            "scholar": {"study": [8, 12, 14, 18], "rest": [0, 7, 19, 23]}
        }

        for region in self.regions.values():
            for npc_id in region.npcs:
                behavior = random.choice(behavior_types)
                self.npc_behaviors[npc_id] = behavior
                self.npc_schedules[npc_id] = schedules[behavior]

    async def _initialize_economy(self):
        """Initialize economic system"""
        # Create trade routes between nearby regions
        region_ids = list(self.regions.keys())
        for i, region_id in enumerate(region_ids):
            # Connect to 3-5 nearby regions
            num_connections = random.randint(3, min(5, len(region_ids) - 1))
            connected_regions = random.sample([r for r in region_ids if r != region_id], num_connections)

            self.trade_routes[region_id] = connected_regions

        # Initialize market prices
        goods = ["food", "wood", "stone", "iron", "gold", "cloth", "weapons", "potions"]
        for region_id in self.regions:
            for good in goods:
                self.market_prices[region_id][good] = random.uniform(1, 100)

    async def _start_processors(self):
        """Start all background processors"""
        # Main simulation loop
        task = asyncio.create_task(self._simulation_loop())
        self.background_tasks.add(task)

        # Event processors
        for _ in range(5):
            task = asyncio.create_task(self._event_processor())
            self.background_tasks.add(task)

        # NPC action processors
        for _ in range(10):
            task = asyncio.create_task(self._npc_action_processor())
            self.background_tasks.add(task)

        # Player action processor
        task = asyncio.create_task(self._player_action_processor())
        self.background_tasks.add(task)

        # Weather processor
        task = asyncio.create_task(self._weather_processor())
        self.background_tasks.add(task)

        # Economic processor
        task = asyncio.create_task(self._economic_processor())
        self.background_tasks.add(task)

        # Time processor
        task = asyncio.create_task(self._time_processor())
        self.background_tasks.add(task)

        # Metrics collector
        task = asyncio.create_task(self._metrics_collector())
        self.background_tasks.add(task)

    async def _simulation_loop(self):
        """Main simulation loop"""
        while self.is_running:
            try:
                start_time = datetime.now()

                # Create simulation tick
                tick = SimulationTick(
                    tick_number=self.tick_counter,
                    timestamp=start_time,
                    delta_time=self.tick_interval,
                    world_time=self.current_world_time
                )

                # Process all regions in parallel
                region_tasks = []
                for region_id in self.regions:
                    region_tasks.append(
                        asyncio.create_task(self._update_region_tick(region_id, tick))
                    )

                # Wait for all regions to update
                region_updates = await asyncio.gather(*region_tasks, return_exceptions=True)

                # Collect results
                for i, update in enumerate(region_updates):
                    if not isinstance(update, Exception):
                        region_id = list(self.regions.keys())[i]
                        tick.region_updates[region_id] = update

                # Process global events
                await self._process_global_events(tick)

                # Update world time
                self.current_world_time += timedelta(seconds=self.simulation_speed * self.tick_interval)

                # Update metrics
                self.tick_counter += 1
                self.world_metrics["simulation_ticks"] = self.tick_counter

                # Sleep until next tick
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, self.tick_interval - elapsed)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                await asyncio.sleep(0.1)

    async def _process_region(self, region_id: str):
        """Process individual region updates"""
        while self.is_running:
            try:
                # Get update from queue
                update_data = await self.region_update_queue.get()

                if update_data["region_id"] == region_id:
                    region = self.regions[region_id]

                    # Apply updates
                    if "economy_change" in update_data:
                        region.economy = max(0, min(100, region.economy + update_data["economy_change"]))

                    if "stability_change" in update_data:
                        region.stability = max(0, min(100, region.stability + update_data["stability_change"]))

                    if "population_change" in update_data:
                        region.population = max(0, region.population + update_data["population_change"])

                    if "resource_change" in update_data:
                        for resource, amount in update_data["resource_change"].items():
                            region.resources[resource] = max(0, region.resources.get(resource, 0) + amount)

                    if "new_event" in update_data:
                        region.events.append(update_data["new_event"])
                        # Keep only last 100 events
                        if len(region.events) > 100:
                            region.events = region.events[-100:]

                    region.last_updated = datetime.now()

            except Exception as e:
                logger.error(f"Region processor error for {region_id}: {e}")
                await asyncio.sleep(0.1)

    async def _update_region_tick(self, region_id: str, tick: SimulationTick) -> Dict[str, Any]:
        """Update region for one tick"""
        region = self.regions[region_id]

        updates = {}

        # Economic simulation
        economy_change = random.gauss(0, 0.1)
        updates["economy_change"] = economy_change

        # Population growth/decline
        if region.population > 0:
            growth_rate = 0.001 * (region.economy / 100) * (region.stability / 100)
            population_change = int(region.population * growth_rate * self.simulation_speed * self.tick_interval / 31536000)
            updates["population_change"] = population_change

        # Resource production/consumption
        resource_change = {}
        for resource in region.resources:
            production = random.uniform(-0.1, 0.5) * region.population / 1000
            resource_change[resource] = production * self.simulation_speed * self.tick_interval
        updates["resource_change"] = resource_change

        # Random events
        if random.random() < 0.001:  # 0.1% chance per tick
            event = await self._generate_region_event(region)
            if event:
                updates["new_event"] = event
                self.active_events[event.event_id] = event

        # Update weather based on climate
        if random.random() < 0.01:  # 1% chance of weather change
            new_weather = await self._calculate_weather_change(region)
            if new_weather != region.weather:
                region.weather = new_weather

        # Apply updates
        await self.region_update_queue.put({
            "region_id": region_id,
            **updates
        })

        return updates

    async def _event_processor(self):
        """Process world events"""
        while self.is_running:
            try:
                # Get batch of events
                events_batch = []
                for _ in range(min(10, self.event_queue.qsize())):
                    if not self.event_queue.empty():
                        event = await self.event_queue.get()
                        events_batch.append(event)

                if events_batch:
                    # Process events in parallel
                    await asyncio.gather(
                        *[self._process_event(event) for event in events_batch],
                        return_exceptions=True
                    )

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Event processor error: {e}")
                await asyncio.sleep(0.1)

    async def _process_event(self, event: WorldEvent):
        """Process individual event"""
        region = self.regions.get(event.region_id)
        if not region:
            return

        # Apply event impacts
        if event.impact:
            updates = {
                "region_id": event.region_id,
                "economy_change": event.impact.get("economy", 0),
                "stability_change": event.impact.get("stability", 0),
                "resource_change": event.impact.get("resources", {})
            }
            await self.region_update_queue.put(updates)

        # Check if event should end
        if event.duration and (datetime.now() - event.start_time).total_seconds() > event.duration:
            if event.event_id in self.active_events:
                del self.active_events[event.event_id]
            self.event_history.append(event)

    async def _npc_action_processor(self):
        """Process NPC actions"""
        while self.is_running:
            try:
                # Get batch of NPC actions
                actions_batch = []
                for _ in range(min(50, self.npc_action_queue.qsize())):
                    if not self.npc_action_queue.empty():
                        action = await self.npc_action_queue.get()
                        actions_batch.append(action)

                if actions_batch:
                    # Process actions in parallel
                    await asyncio.gather(
                        *[self._process_npc_action(action) for action in actions_batch],
                        return_exceptions=True
                    )

                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"NPC action processor error: {e}")
                await asyncio.sleep(0.05)

    async def _process_npc_action(self, action: Dict[str, Any]):
        """Process individual NPC action"""
        npc_id = action.get("npc_id")
        action_type = action.get("action_type")
        region_id = action.get("region_id")

        if not all([npc_id, action_type, region_id]):
            return

        # Process action based on type
        if action_type == "trade":
            await self._process_trade_action(action)
        elif action_type == "work":
            await self._process_work_action(action)
        elif action_type == "social":
            await self._process_social_action(action)

    async def _process_trade_action(self, action: Dict[str, Any]):
        """Process trade action between NPCs"""
        buyer = action.get("buyer")
        seller = action.get("seller")
        good = action.get("good")
        quantity = action.get("quantity", 1)
        price = action.get("price")

        region_id = action.get("region_id")
        base_price = self.market_prices[region_id].get(good, 10)

        # Update supply/demand
        self.supply_demand[region_id][good]["supply"] += quantity
        self.supply_demand[region_id][good]["demand"] += quantity

        # Adjust price based on supply/demand
        sd_ratio = self.supply_demand[region_id][good]["supply"] / self.supply_demand[region_id][good]["demand"]
        new_price = base_price * (2 - sd_ratio)
        self.market_prices[region_id][good] = max(0.1, new_price)

    async def _process_work_action(self, action: Dict[str, Any]):
        """Process work action"""
        npc_id = action.get("npc_id")
        profession = self.npc_behaviors.get(npc_id, "farmer")
        region_id = action.get("region_id")

        # Generate resources based on profession
        if profession == "farmer":
            await self.region_update_queue.put({
                "region_id": region_id,
                "resource_change": {"food": random.uniform(0.5, 2.0)}
            })
        elif profession == "artisan":
            await self.region_update_queue.put({
                "region_id": region_id,
                "resource_change": {"gold": random.uniform(0.1, 1.0)}
            })

    async def _process_social_action(self, action: Dict[str, Any]):
        """Process social interaction"""
        # Generate social events
        pass

    async def _player_action_processor(self):
        """Process player actions"""
        while self.is_running:
            try:
                if not self.player_action_queue.empty():
                    action = await self.player_action_queue.get()
                    await self._process_player_action(action)

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Player action processor error: {e}")
                await asyncio.sleep(0.01)

    async def _process_player_action(self, action: Dict[str, Any]):
        """Process player action"""
        player_id = action.get("player_id")
        region_id = action.get("region_id")
        action_type = action.get("action_type")

        if action_type == "trade":
            # Handle player trade
            pass
        elif action_type == "combat":
            # Handle combat
            pass
        elif action_type == "quest":
            # Handle quest actions
            pass

    async def _weather_processor(self):
        """Process weather changes"""
        while self.is_running:
            try:
                # Update weather for all regions
                weather_tasks = []
                for region_id, region in self.regions.items():
                    if random.random() < 0.05:  # 5% chance of weather change
                        weather_tasks.append(
                            asyncio.create_task(self._update_region_weather(region_id))
                        )

                if weather_tasks:
                    await asyncio.gather(*weather_tasks, return_exceptions=True)

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                logger.error(f"Weather processor error: {e}")
                await asyncio.sleep(10)

    async def _update_region_weather(self, region_id: str):
        """Update weather for a region"""
        region = self.regions[region_id]
        climate = self.regional_climates.get(region_id, "temperate")

        # Calculate new weather based on climate and current weather
        new_weather = await self._calculate_weather_change(region)
        region.weather = new_weather

        # Update temperature
        temp_change = random.gauss(0, 2)
        region.temperature = max(-30, min(50, region.temperature + temp_change))

    async def _economic_processor(self):
        """Process economic simulation"""
        while self.is_running:
            try:
                # Process trade routes
                await self._process_trade_routes()

                # Update market prices
                await self._update_market_prices()

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Economic processor error: {e}")
                await asyncio.sleep(5)

    async def _process_trade_routes(self):
        """Process trade between regions"""
        for region_id, connected_regions in self.trade_routes.items():
            for connected_region in connected_regions:
                # Simulate trade caravans
                if random.random() < 0.1:  # 10% chance of trade
                    # Transfer goods
                    goods = ["food", "wood", "stone", "iron", "gold"]
                    good = random.choice(goods)
                    quantity = random.uniform(10, 100)

                    # Update supply/demand in both regions
                    self.supply_demand[region_id][good]["supply"] -= quantity
                    self.supply_demand[connected_region][good]["supply"] += quantity

    async def _update_market_prices(self):
        """Update market prices based on supply/demand"""
        for region_id in self.regions:
            for good in self.market_prices[region_id]:
                sd = self.supply_demand[region_id][good]
                if sd["demand"] > 0:
                    ratio = sd["supply"] / sd["demand"]
                    # Price adjustment
                    adjustment = (2 - ratio) * 0.01
                    self.market_prices[region_id][good] *= (1 + adjustment)
                    self.market_prices[region_id][good] = max(0.1, self.market_prices[region_id][good])

    async def _time_processor(self):
        """Process time progression"""
        while self.is_running:
            try:
                # Update time of day for all regions
                hour = self.current_world_time.hour

                for region in self.regions.values():
                    if 5 <= hour < 7:
                        region.time_of_day = TimeOfDay.DAWN
                    elif 7 <= hour < 10:
                        region.time_of_day = TimeOfDay.MORNING
                    elif 10 <= hour < 14:
                        region.time_of_day = TimeOfDay.NOON
                    elif 14 <= hour < 17:
                        region.time_of_day = TimeOfDay.AFTERNOON
                    elif 17 <= hour < 19:
                        region.time_of_day = TimeOfDay.DUSK
                    elif 19 <= hour < 23:
                        region.time_of_day = TimeOfDay.NIGHT
                    else:
                        region.time_of_day = TimeOfDay.MIDNIGHT

                await asyncio.sleep(1)  # Update every second

            except Exception as e:
                logger.error(f"Time processor error: {e}")
                await asyncio.sleep(1)

    async def _metrics_collector(self):
        """Collect world metrics"""
        while self.is_running:
            try:
                # Calculate totals
                total_population = sum(r.population for r in self.regions.values())
                avg_economy = sum(r.economy for r in self.regions.values()) / len(self.regions)
                avg_stability = sum(r.stability for r in self.regions.values()) / len(self.regions)

                # Update metrics
                self.world_metrics.update({
                    "total_population": total_population,
                    "average_economy": avg_economy,
                    "average_stability": avg_stability,
                    "active_events": len(self.active_events),
                    "processed_events": len(self.event_history)
                })

                await asyncio.sleep(5)  # Collect every 5 seconds

            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(5)

    async def _process_global_events(self, tick: SimulationTick):
        """Process global world events"""
        # Check for global events
        if random.random() < 0.0001:  # Very rare
            await self._generate_global_event()

    async def _generate_global_event(self):
        """Generate a global event"""
        event_types = ["plague", "war", "festival", "disaster", "discovery"]
        event_type = random.choice(event_types)

        event = WorldEvent(
            event_id=f"global_{uuid.uuid4().hex[:8]}",
            region_id="global",
            event_type=event_type,
            description=f"A {event_type} has begun across the land!",
            impact={
                "economy": random.uniform(-20, 10),
                "stability": random.uniform(-30, 5)
            },
            duration=random.uniform(300, 3600)  # 5-60 minutes
        )

        self.active_events[event.event_id] = event

    async def _generate_region_event(self, region: RegionState) -> Optional[WorldEvent]:
        """Generate event for a region"""
        event_types = ["monster_attack", "merchant_arrival", "festival", "crime", "discovery"]
        event_type = random.choice(event_types)

        event = WorldEvent(
            event_id=f"region_{uuid.uuid4().hex[:8]}",
            region_id=region.region_id,
            event_type=event_type,
            description=f"A {event_type} has occurred in {region.name}!",
            impact={
                "stability": random.uniform(-10, 5),
                "economy": random.uniform(-5, 10)
            }
        )

        return event

    async def _calculate_weather_change(self, region: RegionState) -> WeatherType:
        """Calculate new weather based on current and climate"""
        climate = self.regional_climates.get(region.region_id, "temperate")
        current = region.weather

        # Weather transition probabilities based on climate
        transitions = {
            "temperate": {
                WeatherType.CLEAR: {WeatherType.CLOUDY: 0.3, WeatherType.RAIN: 0.1},
                WeatherType.CLOUDY: {WeatherType.CLEAR: 0.3, WeatherType.RAIN: 0.2, WeatherType.FOG: 0.1},
                WeatherType.RAIN: {WeatherType.CLOUDY: 0.4, WeatherType.STORM: 0.1, WeatherType.CLEAR: 0.2},
                WeatherType.STORM: {WeatherType.RAIN: 0.5, WeatherType.CLOUDY: 0.3},
                WeatherType.FOG: {WeatherType.CLEAR: 0.3, WeatherType.CLOUDY: 0.4}
            },
            "desert": {
                WeatherType.CLEAR: {WeatherType.CLOUDY: 0.2},
                WeatherType.CLOUDY: {WeatherType.CLEAR: 0.5, WeatherType.STORM: 0.05}
            },
            "arctic": {
                WeatherType.SNOW: {WeatherType.CLEAR: 0.2, WeatherType.CLOUDY: 0.3, WeatherType.STORM: 0.1},
                WeatherType.CLEAR: {WeatherType.SNOW: 0.3, WeatherType.CLOUDY: 0.4},
                WeatherType.CLOUDY: {WeatherType.SNOW: 0.4, WeatherType.CLEAR: 0.3, WeatherType.STORM: 0.1}
            }
        }

        climate_transitions = transitions.get(climate, transitions["temperate"])
        possible_transitions = climate_transitions.get(current, {})

        if possible_transitions and random.random() < 0.1:  # 10% chance of transition
            # Choose transition based on probabilities
            weather_types = list(possible_transitions.keys())
            probabilities = list(possible_transitions.values())
            return np.random.choice(weather_types, p=probabilities)

        return current

    def _initialize_weather_patterns(self) -> Dict[str, List[WeatherType]]:
        """Initialize weather patterns for different climates"""
        return {
            "temperate": [WeatherType.CLEAR, WeatherType.CLOUDY, WeatherType.RAIN, WeatherType.FOG],
            "desert": [WeatherType.CLEAR, WeatherType.CLOUDY, WeatherType.STORM],
            "arctic": [WeatherType.SNOW, WeatherType.CLOUDY, WeatherType.CLEAR, WeatherType.STORM],
            "tropical": [WeatherType.CLEAR, WeatherType.RAIN, WeatherType.STORM, WeatherType.CLOUDY],
            "mountain": [WeatherType.CLEAR, WeatherType.CLOUDY, WeatherType.SNOW, WeatherType.STORM],
            "coastal": [WeatherType.CLEAR, WeatherType.CLOUDY, WeatherType.RAIN, WeatherType.FOG]
        }

    async def add_player_action(self, action: Dict[str, Any]):
        """Add player action to queue"""
        await self.player_action_queue.put(action)

    async def add_world_event(self, event: WorldEvent):
        """Add world event"""
        await self.event_queue.put(event)

    async def get_region_state(self, region_id: str) -> Optional[RegionState]:
        """Get current state of a region"""
        return self.regions.get(region_id)

    async def get_world_state(self) -> Dict[str, Any]:
        """Get complete world state"""
        return {
            "current_time": self.current_world_time.isoformat(),
            "tick_count": self.tick_counter,
            "regions": {
                region_id: {
                    "name": region.name,
                    "population": region.population,
                    "economy": region.economy,
                    "stability": region.stability,
                    "weather": region.weather.value,
                    "temperature": region.temperature,
                    "time_of_day": region.time_of_day.value,
                    "resources": region.resources,
                    "players": region.players,
                    "npcs": len(region.npcs)
                }
                for region_id, region in self.regions.items()
            },
            "active_events": len(self.active_events),
            "metrics": self.world_metrics
        }

    async def shutdown(self):
        """Shutdown the world simulation"""
        logger.info("Shutting down world simulation")

        self.is_running = False

        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()

        # Cancel region processors
        for processor in self.region_processors.values():
            processor.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, *self.region_processors.values(), return_exceptions=True)

        # Shutdown executors
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        logger.info("World simulation shutdown complete")


# Test function
async def test_world_simulation():
    """Test the world simulation"""
    sim = ParallelWorldSimulation(
        num_regions=50,
        tick_rate=20,
        simulation_speed=3600
    )

    await sim.initialize()

    # Run for 30 seconds
    await asyncio.sleep(30)

    # Get world state
    state = await sim.get_world_state()
    print(f"Simulated {state['tick_count']} ticks")
    print(f"Total population: {state['metrics']['total_population']}")
    print(f"Average economy: {state['metrics']['average_economy']:.2f}")

    await sim.shutdown()


if __name__ == "__main__":
    asyncio.run(test_world_simulation())