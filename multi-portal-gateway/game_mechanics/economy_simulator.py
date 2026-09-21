"""
Complex Economy Simulator for DMLogn8n
Implements realistic economy with supply/demand dynamics, trade routes, and market forces
"""

import random
import math
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

class ItemType(Enum):
    """Types of items in the economy"""
    RAW_MATERIAL = "raw_material"
    PROCESSED_GOOD = "processed_good"
    FOOD = "food"
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    SCROLL = "scroll"
    TOOL = "tool"
    LUXURY = "luxury"
    MAGICAL = "magical"

class Quality(Enum):
    """Item quality levels affecting price and demand"""
    POOR = 0
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    MYTHIC = 6

class MarketTrend(Enum):
    """Market trends affecting prices"""
    BULLISH = "bullish"  # Prices rising
    BEARISH = "bearish"  # Prices falling
    STABLE = "stable"    # Prices stable
    VOLATILE = "volatile"  # High fluctuation

class TradeRouteStatus(Enum):
    """Status of trade routes"""
    ACTIVE = "active"
    BLOCKED = "blocked"
    DANGEROUS = "dangerous"
    SEASONAL = "seasonal"
    CLOSED = "closed"

@dataclass
class EconomicItem:
    """Item in the economic system"""
    id: str
    name: str
    item_type: ItemType
    quality: Quality
    base_value: float
    weight: float = 1.0
    perishable: bool = False
    shelf_life_days: Optional[int] = None
    production_time: float = 1.0  # Hours to produce
    required_materials: Dict[str, int] = field(default_factory=dict)
    produced_by: List[str] = field(default_factory=list)  # NPC/profession IDs

    # Market properties
    elasticity: float = 1.0  # Price elasticity of demand
    necessity_level: float = 0.5  # 0 = luxury, 1 = necessity
    seasonal_modifier: float = 1.0  # Seasonal demand multiplier
    market_segments: List[str] = field(default_factory=list)  # Market segments

@dataclass
class MarketPrice:
    """Market price information"""
    item_id: str
    current_price: float
    base_price: float
    supply: int
    demand: int
    last_updated: datetime
    price_history: List[float] = field(default_factory=list)
    trend: MarketTrend = MarketTrend.STABLE
    volatility: float = 0.1

@dataclass
class TradeRoute:
    """Trade route between locations"""
    id: str
    from_location: str
    to_location: str
    distance: float
    travel_time: float  # Hours
    status: TradeRouteStatus
    danger_level: float = 0.0
    toll_cost: float = 0.0
    capacity: int = 100
    current_usage: int = 0
    required_equipment: List[str] = field(default_factory=list)
    seasonal_availability: Dict[str, bool] = field(default_factory=dict)

@dataclass
class Market:
    """Market at a specific location"""
    id: str
    location: str
    name: str
    size: str  # village, town, city, metropolis
    population: int

    # Market characteristics
    wealth_level: float = 1.0  # Relative wealth
    specializations: List[ItemType] = field(default_factory=list)
    tariffs: Dict[str, float] = field(default_factory=dict)  # item_type -> tariff_rate
    taxes: float = 0.1  # General tax rate
    regulations: List[str] = field(default_factory=list)

    # Market state
    prices: Dict[str, MarketPrice] = field(default_factory=dict)
    inventory: Dict[str, int] = field(default_factory=dict)
    demand_history: Dict[str, List[float]] = field(default_factory=dict)
    supply_history: Dict[str, List[float]] = field(default_factory=dict)

    # NPC merchants
    merchants: List[str] = field(default_factory=list)
    black_market_presence: float = 0.0  # 0-1

@dataclass
class Transaction:
    """Economic transaction record"""
    id: str
    timestamp: datetime
    buyer: str
    seller: str
    item_id: str
    quantity: int
    unit_price: float
    total_value: float
    location: str
    transaction_type: str  # purchase, sale, trade, etc.

@dataclass
class EconomicEvent:
    """Event affecting the economy"""
    id: str
    event_type: str
    description: str
    start_time: datetime
    duration: timedelta
    affected_locations: List[str]
    affected_items: List[str]
    price_modifier: float
    supply_modifier: float
    demand_modifier: float

class SupplyDemandModel:
    """Models supply and demand dynamics"""

    def __init__(self):
        self.base_demand_elasticity = 1.0
        self.base_supply_elasticity = 0.8
        self.market_shock_threshold = 0.2

    def calculate_equilibrium_price(self, item: EconomicItem, supply: int,
                                  demand: int, market_modifier: float = 1.0) -> float:
        """Calculate equilibrium price based on supply and demand"""
        if supply <= 0:
            return item.base_value * 10  # Extreme scarcity

        # Price ratio based on supply/demand
        ratio = demand / max(1, supply)

        # Apply elasticity
        price_factor = math.pow(ratio, 1 / item.elasticity)

        # Apply market modifiers
        base_price = item.base_value * price_factor * market_modifier

        # Quality modifier
        quality_modifier = 1.0 + (item.quality.value * 0.5)

        return base_price * quality_modifier

    def calculate_demand(self, item: EconomicItem, price: float,
                        market_wealth: float, population: int,
                        seasonal_factor: float = 1.0) -> float:
        """Calculate demand for an item"""
        # Base demand affected by price
        price_effect = math.pow(item.base_value / max(1, price), item.elasticity)

        # Market size effect
        population_effect = math.sqrt(population / 1000)

        # Wealth effect
        wealth_effect = market_wealth

        # Necessity effect
        necessity_effect = 0.3 + (item.necessity_level * 0.7)

        # Seasonal effect
        seasonal_effect = seasonal_factor

        # Market segment specialization
        specialization_bonus = 1.0
        if item.market_segments:
            specialization_bonus = 1.2

        return (price_effect * population_effect * wealth_effect *
                necessity_effect * seasonal_effect * specialization_bonus)

    def calculate_supply(self, item: EconomicItem, price: float,
                        available_producers: int, material_costs: float) -> float:
        """Calculate supply for an item"""
        if available_producers <= 0:
            return 0

        # Profit incentive
        profit_margin = (price - material_costs) / max(1, material_costs)
        profit_effect = max(0.1, profit_margin)

        # Producer count effect
        producer_effect = math.sqrt(available_producers)

        # Production capacity
        production_capacity = available_producers * (24 / item.production_time)

        return production_capacity * producer_effect * profit_effect

class TradeRouteManager:
    """Manages trade routes and logistics"""

    def __init__(self):
        self.routes: Dict[str, TradeRoute] = {}
        self.route_efficiency: Dict[str, float] = {}
        self.danger_zones: Dict[str, float] = {}

    def create_route(self, from_location: str, to_location: str,
                     distance: float, **kwargs) -> TradeRoute:
        """Create a new trade route"""
        route = TradeRoute(
            id=str(uuid.uuid4()),
            from_location=from_location,
            to_location=to_location,
            distance=distance,
            travel_time=distance / 20,  # Assume 20 units/hour speed
            status=TradeRouteStatus.ACTIVE,
            **kwargs
        )

        self.routes[route.id] = route
        self.route_efficiency[route.id] = 1.0

        return route

    def calculate_transport_cost(self, route_id: str, item_weight: float,
                               quantity: int) -> float:
        """Calculate transport cost for items on route"""
        route = self.routes.get(route_id)
        if not route:
            return float('inf')

        base_cost = route.distance * 0.1 * item_weight * quantity
        danger_surcharge = base_cost * route.danger_level
        toll_cost = route.toll_cost

        efficiency_modifier = 1.0 / self.route_efficiency.get(route_id, 1.0)

        return (base_cost + danger_surcharge + toll_cost) * efficiency_modifier

    def update_route_status(self, route_id: str, new_status: TradeRouteStatus,
                          danger_level: Optional[float] = None):
        """Update route status and conditions"""
        route = self.routes.get(route_id)
        if route:
            route.status = new_status
            if danger_level is not None:
                route.danger_level = danger_level

            # Update efficiency based on status
            if new_status == TradeRouteStatus.ACTIVE:
                self.route_efficiency[route_id] = 1.0
            elif new_status == TradeRouteStatus.DANGEROUS:
                self.route_efficiency[route_id] = 0.7
            elif new_status == TradeRouteStatus.BLOCKED:
                self.route_efficiency[route_id] = 0.0

class EconomySimulator:
    """Main economy simulation system"""

    def __init__(self):
        self.items: Dict[str, EconomicItem] = {}
        self.markets: Dict[str, Market] = {}
        self.transactions: List[Transaction] = []
        self.events: List[EconomicEvent] = []
        self.trade_routes = TradeRouteManager()
        self.supply_demand_model = SupplyDemandModel()

        # Economic indicators
       .global_inflation_rate: float = 0.02  # 2% annual
       .gdp_growth_rate: float = 0.03  # 3% annual
       .unemployment_rate: float = 0.05  # 5%
       .interest_rate: float = 0.05  # 5%

        # Simulation state
        current_date: datetime = datetime.now()
        simulation_speed: float = 1.0  # Days per real second

        self._initialize_items()
        self._initialize_markets()

    def _initialize_items(self):
        """Initialize basic economic items"""
        # Raw materials
        iron_ore = EconomicItem(
            id="iron_ore",
            name="Iron Ore",
            item_type=ItemType.RAW_MATERIAL,
            quality=Quality.COMMON,
            base_value=10,
            weight=5.0,
            elasticity=1.2,
            necessity_level=0.6,
            market_segments=["mining", "crafting"]
        )
        self.items[iron_ore.id] = iron_ore

        wood = EconomicItem(
            id="wood",
            name="Wood",
            item_type=ItemType.RAW_MATERIAL,
            quality=Quality.COMMON,
            base_value=5,
            weight=3.0,
            elasticity=1.5,
            necessity_level=0.7,
            market_segments=["logging", "construction", "crafting"]
        )
        self.items[wood.id] = wood

        # Processed goods
        steel_ingot = EconomicItem(
            id="steel_ingot",
            name="Steel Ingot",
            item_type=ItemType.PROCESSED_GOOD,
            quality=Quality.COMMON,
            base_value=25,
            weight=2.0,
            production_time=4.0,
            required_materials={"iron_ore": 2, "coal": 1},
            elasticity=1.0,
            necessity_level=0.5,
            market_segments=["crafting", "weaponry"]
        )
        self.items[steel_ingot.id] = steel_ingot

        # Food items
        bread = EconomicItem(
            id="bread",
            name="Bread",
            item_type=ItemType.FOOD,
            quality=Quality.COMMON,
            base_value=3,
            weight=0.5,
            perishable=True,
            shelf_life_days=7,
            production_time=2.0,
            required_materials={"wheat": 2},
            elasticity=1.8,
            necessity_level=0.9,
            market_segments=["food", "daily_life"]
        )
        self.items[bread.id] = bread

        # Weapons
        sword = EconomicItem(
            id="sword",
            name="Iron Sword",
            item_type=ItemType.WEAPON,
            quality=Quality.COMMON,
            base_value=50,
            weight=3.0,
            production_time=8.0,
            required_materials={"steel_ingot": 2, "wood": 1},
            elasticity=0.8,
            necessity_level=0.3,
            market_segments=["military", "adventurers"]
        )
        self.items[sword.id] = sword

        # Potions
        health_potion = EconomicItem(
            id="health_potion",
            name="Health Potion",
            item_type=ItemType.POTION,
            quality=Quality.UNCOMMON,
            base_value=30,
            weight=0.2,
            production_time=3.0,
            required_materials={"herbs": 3, "water": 1},
            elasticity=1.1,
            necessity_level=0.4,
            market_segments=["healing", "adventurers"]
        )
        self.items[health_potion.id] = health_potion

    def _initialize_markets(self):
        """Initialize market locations"""
        # Capital city market
        capital_market = Market(
            id="capital_market",
            location="capital_city",
            name="Grand Capital Market",
            size="metropolis",
            population=50000,
            wealth_level=1.5,
            specializations=[ItemType.MAGICAL, ItemType.LUXURY, ItemType.WEAPON],
            tariffs={ItemType.LUXURY: 0.2, ItemType.MAGICAL: 0.1}
        )
        self.markets[capital_market.id] = capital_market

        # Village market
        village_market = Market(
            id="village_market",
            location="riverdale",
            name="Riverdale Market",
            size="village",
            population=500,
            wealth_level=0.7,
            specializations=[ItemType.FOOD, ItemType.RAW_MATERIAL],
            tariffs={ItemType.PROCESSED_GOOD: 0.05}
        )
        self.markets[village_market.id] = village_market

        # Trading post
        trading_post = Market(
            id="trading_post",
            location="crossroads",
            name="Crossroads Trading Post",
            size="town",
            population=2000,
            wealth_level=1.0,
            specializations=[ItemType.TOOL, ItemType.PROCESSED_GOOD]
        )
        self.markets[trading_post.id] = trading_post

        # Initialize prices for all markets
        for market in self.markets.values():
            self._initialize_market_prices(market)

    def _initialize_market_prices(self, market: Market):
        """Initialize starting prices for a market"""
        for item_id, item in self.items.items():
            # Calculate starting supply and demand
            base_supply = random.randint(10, 100) * market.population // 1000
            base_demand = random.randint(10, 100) * market.population // 1000

            # Apply market specializations
            if item.item_type in market.specializations:
                base_supply *= 1.5
                base_demand *= 1.3

            # Calculate initial price
            market_modifier = market.wealth_level
            price = self.supply_demand_model.calculate_equilibrium_price(
                item, base_supply, base_demand, market_modifier
            )

            market_price = MarketPrice(
                item_id=item_id,
                current_price=price,
                base_price=item.base_value,
                supply=base_supply,
                demand=base_demand,
                last_updated=self.current_date,
                price_history=[price],
                volatility=random.uniform(0.05, 0.2)
            )

            market.prices[item_id] = market_price
            market.inventory[item_id] = base_supply

    def simulate_day(self):
        """Simulate one day of economic activity"""
        self.current_date += timedelta(days=1)

        # Update market prices
        for market in self.markets.values():
            self._update_market(market)

        # Process economic events
        self._process_events()

        # Update trade routes
        self._update_trade_routes()

        # Generate economic reports
        if self.current_date.day % 7 == 0:  # Weekly reports
            self._generate_economic_report()

    def _update_market(self, market: Market):
        """Update individual market state"""
        # Update supply and demand
        for item_id, price_info in market.prices.items():
            item = self.items.get(item_id)
            if not item:
                continue

            # Calculate new supply and demand
            demand = self.supply_demand_model.calculate_demand(
                item, price_info.current_price, market.wealth_level,
                market.population, self._get_seasonal_factor(item)
            )

            supply = self.supply_demand_model.calculate_supply(
                item, price_info.current_price, len(item.produced_by),
                self._calculate_material_cost(market, item)
            )

            # Apply market events
            demand *= self._get_demand_modifier(market, item_id)
            supply *= self._get_supply_modifier(market, item_id)

            # Update price
            new_price = self.supply_demand_model.calculate_equilibrium_price(
                item, int(supply), int(demand), market.wealth_level
            )

            # Apply market regulations
            new_price = self._apply_regulations(market, item, new_price)

            # Update price with smoothing
            price_info.current_price = (price_info.current_price * 0.7 + new_price * 0.3)
            price_info.supply = int(supply)
            price_info.demand = int(demand)
            price_info.last_updated = self.current_date

            # Update price history
            price_info.price_history.append(price_info.current_price)
            if len(price_info.price_history) > 30:  # Keep 30 days
                price_info.price_history.pop(0)

            # Update trend
            price_info.trend = self._calculate_price_trend(price_info.price_history)

            # Simulate some transactions
            self._simulate_transactions(market, item_id, price_info)

        # Update inventory
        self._update_inventory(market)

    def _get_seasonal_factor(self, item: EconomicItem) -> float:
        """Get seasonal demand modifier for item"""
        # Simple seasonal model based on month
        month = self.current_date.month

        seasonal_modifiers = {
            ItemType.FOOD: {
                12: 1.2, 1: 1.3, 2: 1.2,  # Winter - high demand
                6: 0.8, 7: 0.7, 8: 0.8    # Summer - low demand
            },
            ItemType.RAW_MATERIAL: {
                3: 1.1, 4: 1.2, 5: 1.1,  # Spring - construction
                9: 1.1, 10: 1.2, 11: 1.1  # Fall - preparation
            }
        }

        item_modifiers = seasonal_modifiers.get(item.item_type, {})
        return item_modifiers.get(month, 1.0)

    def _calculate_material_cost(self, market: Market, item: EconomicItem) -> float:
        """Calculate total material cost for producing an item"""
        total_cost = 0.0
        for material_id, quantity in item.required_materials.items():
            material_price = market.prices.get(material_id)
            if material_price:
                total_cost += material_price.current_price * quantity
        return total_cost

    def _get_demand_modifier(self, market: Market, item_id: str) -> float:
        """Get demand modifier from events and conditions"""
        modifier = 1.0

        # Check for economic events
        for event in self.events:
            if (item_id in event.affected_items and
                market.location in event.affected_locations):
                modifier *= event.demand_modifier

        return modifier

    def _get_supply_modifier(self, market: Market, item_id: str) -> float:
        """Get supply modifier from events and conditions"""
        modifier = 1.0

        # Check for economic events
        for event in self.events:
            if (item_id in event.affected_items and
                market.location in event.affected_locations):
                modifier *= event.supply_modifier

        return modifier

    def _apply_regulations(self, market: Market, item: EconomicItem, price: float) -> float:
        """Apply market regulations and taxes to price"""
        # Apply tariffs
        tariff = market.tariffs.get(item.item_type, 0)
        price *= (1 + tariff)

        # Apply general tax
        price *= (1 + market.taxes)

        # Apply price controls if any
        if "price_ceiling" in market.regulations:
            max_price = item.base_value * 2.0
            price = min(price, max_price)

        if "price_floor" in market.regulations:
            min_price = item.base_value * 0.5
            price = max(price, min_price)

        return price

    def _calculate_price_trend(self, price_history: List[float]) -> MarketTrend:
        """Calculate price trend from history"""
        if len(price_history) < 3:
            return MarketTrend.STABLE

        # Calculate trend over last 7 days
        recent_prices = price_history[-7:]
        if len(recent_prices) < 3:
            return MarketTrend.STABLE

        # Simple linear regression
        x = list(range(len(recent_prices)))
        y = recent_prices

        n = len(recent_prices)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] * x[i] for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Determine trend
        if slope > 0.1:
            return MarketTrend.BULLISH
        elif slope < -0.1:
            return MarketTrend.BEARISH
        else:
            return MarketTrend.STABLE

    def _simulate_transactions(self, market: Market, item_id: str, price_info: MarketPrice):
        """Simulate transactions for an item in a market"""
        # Number of transactions based on market activity
        base_transactions = market.population // 100
        num_transactions = random.randint(base_transactions // 2, base_transactions * 2)

        for _ in range(num_transactions):
            # Random transaction size
            quantity = random.randint(1, 5)

            # Random price variation
            price_variation = random.uniform(-0.1, 0.1)
            transaction_price = price_info.current_price * (1 + price_variation)

            transaction = Transaction(
                id=str(uuid.uuid4()),
                timestamp=self.current_date,
                buyer=f"buyer_{random.randint(1, 1000)}",
                seller=f"seller_{random.randint(1, 100)}",
                item_id=item_id,
                quantity=quantity,
                unit_price=transaction_price,
                total_value=transaction_price * quantity,
                location=market.location,
                transaction_type="purchase"
            )

            self.transactions.append(transaction)

        # Limit transaction history
        if len(self.transactions) > 10000:
            self.transactions = self.transactions[-5000:]

    def _update_inventory(self, market: Market):
        """Update market inventory based on supply and demand"""
        for item_id, price_info in market.prices.items():
            current_inventory = market.inventory.get(item_id, 0)

            # Simulate production
            production = int(price_info.supply * 0.1)  # 10% of daily supply produced
            current_inventory += production

            # Simulate consumption
            consumption = int(price_info.demand * 0.1)  # 10% of daily demand consumed
            current_inventory = max(0, current_inventory - consumption)

            market.inventory[item_id] = current_inventory

    def _process_events(self):
        """Process active economic events"""
        completed_events = []

        for event in self.events:
            # Check if event has ended
            if self.current_date > event.start_time + event.duration:
                completed_events.append(event)
            else:
                # Apply event effects
                self._apply_event_effects(event)

        # Remove completed events
        for event in completed_events:
            self.events.remove(event)

    def _apply_event_effects(self, event: EconomicEvent):
        """Apply effects of an economic event"""
        for location_id in event.affected_locations:
            market = self.markets.get(location_id)
            if not market:
                continue

            for item_id in event.affected_items:
                price_info = market.prices.get(item_id)
                if price_info:
                    price_info.current_price *= event.price_modifier
                    price_info.supply = int(price_info.supply * event.supply_modifier)
                    price_info.demand = int(price_info.demand * event.demand_modifier)

    def _update_trade_routes(self):
        """Update trade route conditions"""
        for route_id, route in self.trade_routes.routes.items():
            # Random events can affect routes
            if random.random() < 0.05:  # 5% chance of route event
                event_type = random.choice(["bandit", "weather", "construction"])

                if event_type == "bandit":
                    route.danger_level = min(1.0, route.danger_level + 0.1)
                    if route.danger_level > 0.7:
                        route.status = TradeRouteStatus.DANGEROUS
                elif event_type == "weather":
                    if route.status == TradeRouteStatus.ACTIVE:
                        route.status = TradeRouteStatus.SEASONAL
                elif event_type == "construction":
                    route.status = TradeRouteStatus.BLOCKED
                    route.status = TradeRouteStatus.ACTIVE  # Temporary

    def create_economic_event(self, event_type: str, description: str,
                            duration_days: int, affected_locations: List[str],
                            affected_items: List[str], price_modifier: float = 1.0,
                            supply_modifier: float = 1.0, demand_modifier: float = 1.0) -> EconomicEvent:
        """Create a new economic event"""
        event = EconomicEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            description=description,
            start_time=self.current_date,
            duration=timedelta(days=duration_days),
            affected_locations=affected_locations,
            affected_items=affected_items,
            price_modifier=price_modifier,
            supply_modifier=supply_modifier,
            demand_modifier=demand_modifier
        )

        self.events.append(event)
        return event

    def find_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """Find arbitrage opportunities between markets"""
        opportunities = []

        # Get connected markets
        connected_markets = list(self.markets.keys())

        for i, market1_id in enumerate(connected_markets):
            for market2_id in connected_markets[i+1:]:
                market1 = self.markets[market1_id]
                market2 = self.markets[market2_id]

                # Find trade route between markets
                route = self._find_trade_route(market1.location, market2.location)
                if not route or route.status != TradeRouteStatus.ACTIVE:
                    continue

                # Check each item for arbitrage
                for item_id in self.items:
                    price1 = market1.prices.get(item_id)
                    price2 = market2.prices.get(item_id)

                    if price1 and price2:
                        price_diff = abs(price1.current_price - price2.current_price)
                        price_ratio = max(price1.current_price, price2.current_price) / min(price1.current_price, price2.current_price)

                        # Calculate transport cost
                        item = self.items[item_id]
                        transport_cost = self.trade_routes.calculate_transport_cost(
                            route.id, item.weight, 1
                        )

                        # Check if arbitrage is profitable
                        if price_ratio > 1.2 and price_diff > transport_cost * 2:
                            opportunities.append({
                                "item_id": item_id,
                                "buy_market": market2_id if price2.current_price < price1.current_price else market1_id,
                                "sell_market": market1_id if price2.current_price < price1.current_price else market2_id,
                                "buy_price": min(price1.current_price, price2.current_price),
                                "sell_price": max(price1.current_price, price2.current_price),
                                "transport_cost": transport_cost,
                                "profit_potential": price_diff - transport_cost,
                                "route_id": route.id
                            })

        # Sort by profit potential
        opportunities.sort(key=lambda x: x["profit_potential"], reverse=True)
        return opportunities[:10]  # Return top 10 opportunities

    def _find_trade_route(self, from_location: str, to_location: str) -> Optional[TradeRoute]:
        """Find trade route between two locations"""
        for route in self.trade_routes.routes.values():
            if ((route.from_location == from_location and route.to_location == to_location) or
                (route.from_location == to_location and route.to_location == from_location)):
                return route
        return None

    def _generate_economic_report(self):
        """Generate weekly economic report"""
        print(f"\n=== ECONOMIC REPORT - {self.current_date.strftime('%Y-%m-%d')} ===")

        # Global indicators
        print(f"Global Inflation: {self.global_inflation_rate * 100:.1f}%")
        print(f"GDP Growth: {self.gdp_growth_rate * 100:.1f}%")
        print(f"Unemployment: {self.unemployment_rate * 100:.1f}%")
        print(f"Active Events: {len(self.events)}")

        # Market summaries
        for market_id, market in self.markets.items():
            print(f"\n{market.name} ({market.location}):")

            # Calculate market index
            total_value = sum(price.current_price * market.inventory.get(item_id, 0)
                            for item_id, price in market.prices.items())
            print(f"  Market Value: ${total_value:.0f}")
            print(f"  Population: {market.population:,}")
            print(f"  Wealth Level: {market.wealth_level:.1f}")

            # Top items by value
            items_by_value = sorted(
                [(item_id, price.current_price * market.inventory.get(item_id, 0))
                 for item_id, price in market.prices.items()],
                key=lambda x: x[1], reverse=True
            )

            print(f"  Top 3 Items by Value:")
            for item_id, value in items_by_value[:3]:
                item = self.items.get(item_id)
                if item:
                    print(f"    {item.name}: ${value:.0f}")

        # Arbitrage opportunities
        opportunities = self.find_arbitrage_opportunities()
        if opportunities:
            print(f"\nTop Arbitrage Opportunities:")
            for opp in opportunities[:3]:
                item = self.items.get(opp["item_id"])
                if item:
                    print(f"  {item.name}: Buy in {opp['buy_market']} at ${opp['buy_price']:.1f}, "
                          f"Sell in {opp['sell_market']} at ${opp['sell_price']:.1f}, "
                          f"Profit: ${opp['profit_potential']:.1f}")

        print("=" * 50)

    def get_market_summary(self, market_id: str) -> Dict[str, Any]:
        """Get detailed summary of a market"""
        market = self.markets.get(market_id)
        if not market:
            return {}

        # Calculate market statistics
        total_inventory_value = sum(
            price.current_price * market.inventory.get(item_id, 0)
            for item_id, price in market.prices.items()
        )

        # Find most expensive and cheapest items
        items_by_price = sorted(
            [(item_id, price.current_price) for item_id, price in market.prices.items()],
            key=lambda x: x[1]
        )

        # Calculate price trends
        trend_counts = {}
        for price_info in market.prices.values():
            trend = price_info.trend.value
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

        return {
            "market_name": market.name,
            "location": market.location,
            "size": market.size,
            "population": market.population,
            "wealth_level": market.wealth_level,
            "total_inventory_value": total_inventory_value,
            "specializations": [spec.value for spec in market.specializations],
            "number_of_items": len(market.prices),
            "price_trends": trend_counts,
            "cheapest_item": items_by_price[0] if items_by_price else None,
            "most_expensive_item": items_by_price[-1] if items_by_price else None,
            "active_events": len([e for e in self.events if market.location in e.affected_locations])
        }

# Example usage and testing
if __name__ == "__main__":
    # Create economy simulator
    economy = EconomySimulator()

    # Create some trade routes
    route1 = economy.trade_routes.create_route(
        from_location="capital_city",
        to_location="riverdale",
        distance=50.0,
        toll_cost=5.0,
        danger_level=0.1
    )

    route2 = economy.trade_routes.create_route(
        from_location="capital_city",
        to_location="crossroads",
        distance=30.0,
        toll_cost=2.0,
        danger_level=0.05
    )

    print("=== ECONOMY SIMULATOR INITIALIZED ===")
    print(f"Items: {len(economy.items)}")
    print(f"Markets: {len(economy.markets)}")
    print(f"Trade Routes: {len(economy.trade_routes.routes)}")

    # Simulate a few days
    for day in range(7):
        print(f"\n--- Day {day + 1} ---")
        economy.simulate_day()

        # Show some prices
        capital_market = economy.markets["capital_market"]
        village_market = economy.markets["village_market"]

        print(f"Capital - Bread: ${capital_market.prices['bread'].current_price:.2f}, "
              f"Sword: ${capital_market.prices['sword'].current_price:.2f}")
        print(f"Village - Bread: ${village_market.prices['bread'].current_price:.2f}, "
              f"Sword: ${village_market.prices['sword'].current_price:.2f}")

    # Create an economic event
    print(f"\n=== ECONOMIC EVENT ===")
    harvest_festival = economy.create_economic_event(
        event_type="festival",
        description="Harvest Festival - Increased demand for food",
        duration_days=3,
        affected_locations=["riverdale", "crossroads"],
        affected_items=["bread", "wheat"],
        demand_modifier=1.5,
        price_modifier=1.2
    )
    print(f"Created: {harvest_festival.description}")

    # Simulate event effects
    for day in range(3):
        print(f"\n--- Festival Day {day + 1} ---")
        economy.simulate_day()

        village_market = economy.markets["village_market"]
        print(f"Village - Bread: ${village_market.prices['bread'].current_price:.2f} "
              f"(Trend: {village_market.prices['bread'].trend.value})")

    # Find arbitrage opportunities
    print(f"\n=== ARBITRAGE OPPORTUNITIES ===")
    opportunities = economy.find_arbitrage_opportunities()
    for i, opp in enumerate(opportunities[:3]):
        item = economy.items.get(opp["item_id"])
        if item:
            print(f"{i+1}. {item.name}: "
                  f"Buy at {opp['buy_market']} (${opp['buy_price']:.1f}), "
                  f"Sell at {opp['sell_market']} (${opp['sell_price']:.1f}), "
                  f"Profit: ${opp['profit_potential']:.1f}")

    # Get market summary
    print(f"\n=== MARKET SUMMARY ===")
    summary = economy.get_market_summary("capital_market")
    print(f"Market: {summary['market_name']}")
    print(f"Total Value: ${summary['total_inventory_value']:.0f}")
    print(f"Items Traded: {summary['number_of_items']}")
    print(f"Price Trends: {summary['price_trends']}")

    # Generate final economic report
    economy._generate_economic_report()