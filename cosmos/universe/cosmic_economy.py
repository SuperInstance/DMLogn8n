#!/usr/bin/env python3
"""
Cosmic Economy System - Galaxy-Wide Resource Trading
Manages interstellar trade, markets, and economic systems
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import random
import math

# Economic Constants
BASE_CURRENCY_UNIT = 1e6  # Base value for currency calculations
LIGHT_YEAR = 9.461e15  # meters
AU = 1.496e11  # meters

class ResourceType(Enum):
    COMMON_METALS = "common_metals"
    RARE_METALS = "rare_metals"
    EXOTIC_METALS = "exotic_metals"
    RADIOACTIVE_MATERIALS = "radioactive_materials"
    ORGANIC_COMPOUNDS = "organic_compounds"
    BIOMASS = "biomass"
    WATER = "water"
    OXYGEN = "oxygen"
    HYDROGEN = "hydrogen"
    HELIUM = "helium"
    ENERGY_CELLS = "energy_cells"
    ANTIMATTER = "antimatter"
    QUANTUM_COMPONENTS = "quantum_components"
    DARK_MATTER = "dark_matter"
    STRANGE_MATTER = "strange_matter"
    NANITES = "nanites"
    SYNTHETIC_MATERIALS = "synthetic_materials"
    BIOLOGICAL_SAMPLES = "biological_samples"
    ARTIFACTS = "artifacts"
    DATA = "data"

class TradeGoodType(Enum):
    RAW_MATERIALS = "raw_materials"
    PROCESSED_MATERIALS = "processed_materials"
    CONSUMER_GOODS = "consumer_goods"
    LUXURY_GOODS = "luxury_goods"
    TECHNOLOGY = "technology"
    WEAPONS = "weapons"
    MEDICINE = "medicine"
    FOOD = "food"
    INFORMATION = "information"
    SERVICES = "services"

class MarketType(Enum):
    LOCAL = "local"  # Single system market
    REGIONAL = "regional"  # Multi-system region
    SECTOR = "sector"  # Large sector of space
    GALACTIC = "galactic"  # Galaxy-wide market
    INTERGALACTIC = "intergalactic"  # Between galaxies

class EconomicPolicy(Enum):
    FREE_MARKET = "free_market"  # Laissez-faire capitalism
    PLANNED_ECONOMY = "planned_economy"  # State-controlled
    MIXED_ECONOMY = "mixed_economy"  # Combination
    CORPORATE_STATE = "corporate_state"  # Corporate control
    RESOURCE_BASED = "resource_based"  # Post-scarcity
    TRADITIONAL = "traditional"  # Barter and local exchange

@dataclass
class Vector3D:
    """3D vector for spatial calculations"""
    x: float
    y: float
    z: float

    def magnitude(self):
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)

@dataclass
class Resource:
    """Represents a tradeable resource"""
    resource_type: ResourceType
    quantity: float  # Amount in base units
    quality: float  # 0-1 quality rating
    purity: float  # 0-1 purity level
    origin: str  # System of origin
    processing_level: int  # 0-5 processing level
    special_properties: List[str] = field(default_factory=list)
    expiration_date: Optional[float] = None  # For perishable goods

@dataclass
class TradeGood:
    """Represents a manufactured trade good"""
    good_type: TradeGoodType
    name: str
    base_value: float  # Base market value
    components: Dict[ResourceType, float]  # Required components
    production_complexity: float  # 0-1 manufacturing complexity
    quality_level: int  # 1-10 quality rating
    brand_reputation: float  # 0-1 brand value
    patent_holder: Optional[str] = None  # Corporation that holds patent
    market_demand: float = 1.0  # Current demand multiplier

@dataclass
class TradeRoute:
    """Represents an established trade route"""
    id: str
    origin_system: str
    destination_system: str
    distance: float  # Distance in light-years
    trade_volume: float  # Total trade volume
    security_level: float  # 0-1 security rating
    toll_cost: float  # Cost to use route
    route_efficiency: float  # 0-1 efficiency rating
    controlling_faction: Optional[str] = None
    competing_factions: List[str] = field(default_factory=list)

@dataclass
class MarketPrice:
    """Represents market price information"""
    resource_type: ResourceType
    base_price: float
    current_price: float
    price_history: List[float] = field(default_factory=list)
    supply: float
    demand: float
    price_volatility: float  # 0-1 volatility
    market_trend: str  # "rising", "falling", "stable"

@dataclass
class TradingPost:
    """Represents a trading post or market"""
    id: str
    name: str
    location: Vector3D
    system_id: str
    market_type: MarketType
    economic_policy: EconomicPolicy
    tax_rate: float  # 0-1 tax rate
    inventory: Dict[ResourceType, List[Resource]] = field(default_factory=dict)
    market_prices: Dict[ResourceType, MarketPrice] = field(default_factory=dict)
    trade_routes: List[str] = field(default_factory=list)  # Connected route IDs
    specializations: List[ResourceType] = field(default_factory=list)
    reputation: float = 0.5  # 0-1 market reputation

@dataclass
class Corporation:
    """Represents a trading corporation"""
    id: str
    name: str
    headquarters: str  # System location
    founded_date: float
    ceo_id: str
    market_capitalization: float
    employee_count: int
    specializations: List[ResourceType] = field(default_factory=list)
    holdings: Dict[str, float] = field(default_factory=dict)  # System stakes
    patents: List[str] = field(default_factory=list)
    reputation: float = 0.5  # 0-1 corporate reputation
    ethical_rating: float = 0.5  # 0-1 ethical business practices

@dataclass
class TradeTransaction:
    """Represents a completed trade transaction"""
    id: str
    buyer_id: str
    seller_id: str
    resource_type: ResourceType
    quantity: float
    unit_price: float
    total_value: float
    location: str  # Where transaction occurred
    timestamp: float
    transaction_type: str  # "buy", "sell", "barter"
    payment_method: str
    taxes_paid: float = 0.0

class CosmicEconomySystem:
    """Manages the interstellar economy"""

    def __init__(self):
        self.trading_posts: Dict[str, TradingPost] = {}
        self.corporations: Dict[str, Corporation] = {}
        self.trade_routes: Dict[str, TradeRoute] = {}
        self.trade_goods: Dict[str, TradeGood] = {}
        self.transactions: List[TradeTransaction] = []
        self.market_indices: Dict[str, float] = {}  # Market performance indices
        self.current_time = 0.0

        # Resource base values
        self.resource_base_values = {
            ResourceType.COMMON_METALS: 100,
            ResourceType.RARE_METALS: 1000,
            ResourceType.EXOTIC_METALS: 10000,
            ResourceType.RADIOACTIVE_MATERIALS: 5000,
            ResourceType.ORGANIC_COMPOUNDS: 200,
            ResourceType.BIOMASS: 150,
            ResourceType.WATER: 50,
            ResourceType.OXYGEN: 80,
            ResourceType.HYDROGEN: 60,
            ResourceType.HELIUM: 200,
            ResourceType.ENERGY_CELLS: 500,
            ResourceType.ANTIMATTER: 50000,
            ResourceType.QUANTUM_COMPONENTS: 25000,
            ResourceType.DARK_MATTER: 100000,
            ResourceType.STRANGE_MATTER: 500000,
            ResourceType.NANITES: 5000,
            ResourceType.SYNTHETIC_MATERIALS: 1000,
            ResourceType.BIOLOGICAL_SAMPLES: 3000,
            ResourceType.ARTIFACTS: 100000,
            ResourceType.DATA: 100
        }

        # Initialize trade goods
        self.initialize_trade_goods()

    def initialize_trade_goods(self):
        """Initialize available trade goods"""

        self.trade_goods = {
            'computer_chips': TradeGood(
                good_type=TradeGoodType.TECHNOLOGY,
                name='Quantum Computer Chips',
                base_value=5000,
                components={ResourceType.QUANTUM_COMPONENTS: 0.1, ResourceType.RARE_METALS: 0.5, ResourceType.ENERGY_CELLS: 0.2},
                production_complexity=0.8,
                quality_level=7,
                brand_reputation=0.7
            ),
            'medical_supplies': TradeGood(
                good_type=TradeGoodType.MEDICINE,
                name='Advanced Medical Supplies',
                base_value=2000,
                components={ResourceType.BIOLOGICAL_SAMPLES: 0.3, ResourceType.SYNTHETIC_MATERIALS: 0.4, ResourceType.NANITES: 0.1},
                production_complexity=0.6,
                quality_level=8,
                brand_reputation=0.8
            ),
            'luxury_foods': TradeGood(
                good_type=TradeGoodType.LUXURY_GOODS,
                name='Exotic Cuisine Collection',
                base_value=1500,
                components={ResourceType.BIOMASS: 0.6, ResourceType.ORGANIC_COMPOUNDS: 0.2, ResourceType.WATER: 0.1},
                production_complexity=0.4,
                quality_level=6,
                brand_reputation=0.6
            ),
            'weapons_systems': TradeGood(
                good_type=TradeGoodType.WEAPONS,
                name='Plasma Weapon Systems',
                base_value=10000,
                components={ResourceType.EXOTIC_METALS: 0.3, ResourceType.ENERGY_CELLS: 0.4, ResourceType.RARE_METALS: 0.2},
                production_complexity=0.9,
                quality_level=9,
                brand_reputation=0.8
            ),
            'fuel_cells': TradeGood(
                good_type=TradeGoodType.PROCESSED_MATERIALS,
                name='High-Density Fuel Cells',
                base_value=800,
                components={ResourceType.HYDROGEN: 0.6, ResourceType.ENERGY_CELLS: 0.3, ResourceType.RARE_METALS: 0.1},
                production_complexity=0.5,
                quality_level=5,
                brand_reputation=0.5
            ),
            'research_data': TradeGood(
                good_type=TradeGoodType.INFORMATION,
                name='Scientific Research Data',
                base_value=3000,
                components={ResourceType.DATA: 0.8, ResourceType.QUANTUM_COMPONENTS: 0.1},
                production_complexity=0.7,
                quality_level=8,
                brand_reputation=0.9
            )
        }

    def create_trading_post(self, post_data: Dict) -> TradingPost:
        """Create a new trading post"""

        post = TradingPost(
            id=post_data['id'],
            name=post_data['name'],
            location=Vector3D(*post_data.get('location', [0, 0, 0])),
            system_id=post_data['system_id'],
            market_type=MarketType(post_data.get('market_type', 'local')),
            economic_policy=EconomicPolicy(post_data.get('economic_policy', 'free_market')),
            tax_rate=post_data.get('tax_rate', 0.1),
            specializations=post_data.get('specializations', [])
        )

        # Initialize market prices
        for resource_type, base_value in self.resource_base_values.items():
            # Add some randomization to initial prices
            price_variation = random.uniform(0.8, 1.2)
            current_price = base_value * price_variation

            market_price = MarketPrice(
                resource_type=resource_type,
                base_price=base_value,
                current_price=current_price,
                supply=random.uniform(100, 1000),
                demand=random.uniform(50, 500),
                price_volatility=random.uniform(0.1, 0.3),
                market_trend='stable'
            )

            post.market_prices[resource_type] = market_price

        self.trading_posts[post.id] = post
        return post

    def create_corporation(self, corp_data: Dict) -> Corporation:
        """Create a new corporation"""

        corporation = Corporation(
            id=corp_data['id'],
            name=corp_data['name'],
            headquarters=corp_data['headquarters'],
            founded_date=corp_data.get('founded_date', self.current_time),
            ceo_id=corp_data.get('ceo_id', f"ceo_{corp_data['id']}"),
            market_capitalization=corp_data.get('market_capitalization', 1e9),
            employee_count=corp_data.get('employee_count', 10000),
            specializations=corp_data.get('specializations', []),
            reputation=corp_data.get('reputation', 0.5),
            ethical_rating=corp_data.get('ethical_rating', 0.5)
        )

        self.corporations[corporation.id] = corporation
        return corporation

    def create_trade_route(self, route_data: Dict) -> TradeRoute:
        """Create a new trade route"""

        origin = route_data['origin_system']
        destination = route_data['destination_system']

        # Calculate distance if not provided
        if 'distance' not in route_data:
            # This would need actual system positions
            distance = random.uniform(10, 1000)  # Placeholder
        else:
            distance = route_data['distance']

        route = TradeRoute(
            id=route_data['id'],
            origin_system=origin,
            destination_system=destination,
            distance=distance,
            trade_volume=route_data.get('trade_volume', 1000),
            security_level=route_data.get('security_level', 0.7),
            toll_cost=route_data.get('toll_cost', distance * 10),
            route_efficiency=route_data.get('route_efficiency', 0.8),
            controlling_faction=route_data.get('controlling_faction'),
            competing_factions=route_data.get('competing_factions', [])
        )

        self.trade_routes[route.id] = route

        # Connect trading posts
        for post in self.trading_posts.values():
            if post.system_id in [origin, destination]:
                if route.id not in post.trade_routes:
                    post.trade_routes.append(route.id)

        return route

    def calculate_market_price(self, post: TradingPost, resource_type: ResourceType,
                             supply_shock: float = 0.0, demand_shock: float = 0.0) -> float:
        """Calculate current market price for a resource"""

        if resource_type not in post.market_prices:
            return self.resource_base_values.get(resource_type, 100)

        market_price = post.market_prices[resource_type]
        base_price = market_price.base_price

        # Supply and demand effects
        supply_ratio = market_price.supply / (market_price.demand + 1)
        price_multiplier = 1.0 / (1.0 + supply_ratio * 0.5)

        # Economic policy effects
        if post.economic_policy == EconomicPolicy.PLANNED_ECONOMY:
            price_multiplier *= 0.8  # Price controls
        elif post.economic_policy == EconomicPolicy.CORPORATE_STATE:
            price_multiplier *= 1.2  # Corporate markup
        elif post.economic_policy == EconomicPolicy.FREE_MARKET:
            price_multiplier *= (1.0 + market_price.price_volatility * 0.2)

        # Specialization bonus
        if resource_type in post.specializations:
            price_multiplier *= 0.9  # Better prices for specialized goods

        # Apply shocks
        price_multiplier *= (1.0 - supply_shock * 0.5)
        price_multiplier *= (1.0 + demand_shock * 0.5)

        # Calculate final price
        final_price = base_price * price_multiplier

        # Update market price
        market_price.current_price = final_price
        market_price.supply += supply_shock * 100
        market_price.demand += demand_shock * 100

        # Update price history
        market_price.price_history.append(final_price)
        if len(market_price.price_history) > 100:
            market_price.price_history.pop(0)

        # Update market trend
        if len(market_price.price_history) > 10:
            recent_avg = sum(market_price.price_history[-10:]) / 10
            older_avg = sum(market_price.price_history[-20:-10]) / 10
            if recent_avg > older_avg * 1.05:
                market_price.market_trend = 'rising'
            elif recent_avg < older_avg * 0.95:
                market_price.market_trend = 'falling'
            else:
                market_price.market_trend = 'stable'

        return final_price

    def execute_trade_transaction(self, buyer_id: str, seller_id: str,
                               post_id: str, resource_type: ResourceType,
                               quantity: float, payment_method: str = 'credits') -> Optional[TradeTransaction]:
        """Execute a trade transaction"""

        if post_id not in self.trading_posts:
            return None

        post = self.trading_posts[post_id]
        market_price = post.market_prices.get(resource_type)
        if not market_price:
            return None

        # Check if seller has enough resources (simplified)
        if market_price.supply < quantity:
            return None

        # Calculate transaction value
        unit_price = market_price.current_price
        total_value = unit_price * quantity

        # Calculate taxes
        taxes = total_value * post.tax_rate
        total_with_taxes = total_value + taxes

        # Create transaction
        transaction = TradeTransaction(
            id=f"tx_{len(self.transactions)}_{self.current_time}",
            buyer_id=buyer_id,
            seller_id=seller_id,
            resource_type=resource_type,
            quantity=quantity,
            unit_price=unit_price,
            total_value=total_value,
            location=post_id,
            timestamp=self.current_time,
            transaction_type='buy',
            payment_method=payment_method,
            taxes_paid=taxes
        )

        # Update market
        market_price.supply -= quantity
        market_price.demand += quantity * 0.1  # Trading activity increases demand

        # Record transaction
        self.transactions.append(transaction)

        return transaction

    def calculate_trade_route_profitability(self, route: TradeRoute,
                                         resource: ResourceType, quantity: float) -> Dict:
        """Calculate profitability of trading along a route"""

        # Find trading posts at origin and destination
        origin_post = None
        dest_post = None

        for post in self.trading_posts.values():
            if post.system_id == route.origin_system:
                origin_post = post
            elif post.system_id == route.destination_system:
                dest_post = post

        if not origin_post or not dest_post:
            return {'profitable': False, 'reason': 'No trading posts found'}

        # Get prices
        origin_price = self.calculate_market_price(origin_post, resource)
        dest_price = self.calculate_market_price(dest_post, resource)

        # Calculate costs
        purchase_cost = origin_price * quantity
        transport_cost = route.toll_cost + (route.distance * quantity * 0.1)
        total_cost = purchase_cost + transport_cost

        # Calculate revenue
        sale_revenue = dest_price * quantity

        # Calculate profit
        profit = sale_revenue - total_cost
        profit_margin = profit / total_cost if total_cost > 0 else 0

        # Risk assessment
        security_risk = 1.0 - route.security_level
        competition_risk = len(route.competing_factions) * 0.1
        total_risk = security_risk + competition_risk

        return {
            'profitable': profit > 0,
            'profit': profit,
            'profit_margin': profit_margin,
            'purchase_cost': purchase_cost,
            'transport_cost': transport_cost,
            'sale_revenue': sale_revenue,
            'total_cost': total_cost,
            'risk_level': total_risk,
            'security_risk': security_risk,
            'origin_price': origin_price,
            'dest_price': dest_price,
            'price_difference': dest_price - origin_price
        }

    def update_market_dynamics(self, dt: float) -> None:
        """Update market dynamics over time"""

        # Update each trading post
        for post in self.trading_posts.values():
            for resource_type, market_price in post.market_prices.items():
                # Random market fluctuations
                fluctuation = random.gauss(0, market_price.price_volatility * 0.01)
                market_price.current_price *= (1 + fluctuation)

                # Supply and demand regeneration
                market_price.supply += random.uniform(-10, 20) * dt
                market_price.demand += random.uniform(-5, 15) * dt

                # Ensure positive values
                market_price.supply = max(0, market_price.supply)
                market_price.demand = max(0, market_price.demand)

                # Price corrections based on supply/demand
                if market_price.supply > market_price.demand * 2:
                    market_price.current_price *= 0.99  # Oversupply drives prices down
                elif market_price.demand > market_price.supply * 2:
                    market_price.current_price *= 1.01  # High demand drives prices up

        # Update corporate values
        for corporation in self.corporations.values():
            # Random market fluctuations
            value_change = random.gauss(0, 0.02)
            corporation.market_capitalization *= (1 + value_change)

        # Update market indices
        self.update_market_indices()

        self.current_time += dt

    def update_market_indices(self) -> None:
        """Update market performance indices"""

        if not self.trading_posts:
            return

        # Calculate resource price index
        total_value = 0
        total_weight = 0

        for post in self.trading_posts.values():
            for resource_type, market_price in post.market_prices.items():
                base_value = self.resource_base_values.get(resource_type, 100)
                weight = market_price.supply + market_price.demand
                total_value += (market_price.current_price / base_value) * weight
                total_weight += weight

        if total_weight > 0:
            self.market_indices['resource_price_index'] = total_value / total_weight
        else:
            self.market_indices['resource_price_index'] = 1.0

        # Calculate trade volume index
        recent_transactions = [t for t in self.transactions if self.current_time - t.timestamp < 100]
        total_volume = sum(t.total_value for t in recent_transactions)
        self.market_indices['trade_volume_index'] = total_volume / 1e6  # Normalize to millions

        # Calculate corporate health index
        if self.corporations:
            avg_market_cap = sum(c.market_capitalization for c in self.corporations.values()) / len(self.corporations)
            self.market_indices['corporate_health_index'] = avg_market_cap / 1e9  # Normalize to billions

    def get_market_report(self, post_id: str) -> Dict:
        """Generate a market report for a trading post"""

        if post_id not in self.trading_posts:
            return {}

        post = self.trading_posts[post_id]

        # Top performing resources
        sorted_resources = sorted(post.market_prices.items(),
                                key=lambda x: x[1].current_price,
                                reverse=True)

        top_resources = [(res_type.value, price.current_price, price.market_trend)
                        for res_type, price in sorted_resources[:10]]

        # Market summary
        total_supply = sum(price.supply for price in post.market_prices.values())
        total_demand = sum(price.demand for price in post.market_prices.values())
        avg_price = sum(price.current_price for price in post.market_prices.values()) / len(post.market_prices)

        # Recent transactions
        recent_transactions = [t for t in self.transactions
                             if t.location == post_id and self.current_time - t.timestamp < 50]

        return {
            'post_name': post.name,
            'market_type': post.market_type.value,
            'economic_policy': post.economic_policy.value,
            'tax_rate': post.tax_rate,
            'reputation': post.reputation,
            'total_supply': total_supply,
            'total_demand': total_demand,
            'average_price': avg_price,
            'top_resources': top_resources,
            'recent_transactions': len(recent_transactions),
            'connected_routes': len(post.trade_routes),
            'specializations': [spec.value for spec in post.specializations]
        }

    def find_profitable_trade_routes(self, min_profit_margin: float = 0.1) -> List[Dict]:
        """Find profitable trade routes"""

        profitable_routes = []

        for route in self.trade_routes.values():
            # Check each resource type
            for resource_type in ResourceType:
                if resource_type not in self.resource_base_values:
                    continue

                profitability = self.calculate_trade_route_profitability(route, resource_type, 100)
                if (profitability['profitable'] and
                    profitability['profit_margin'] >= min_profit_margin):
                    profitable_routes.append({
                        'route_id': route.id,
                        'resource': resource_type.value,
                        'profit': profitability['profit'],
                        'profit_margin': profitability['profit_margin'],
                        'origin': route.origin_system,
                        'destination': route.destination_system,
                        'risk_level': profitability['risk_level']
                    })

        # Sort by profit margin
        profitable_routes.sort(key=lambda x: x['profit_margin'], reverse=True)

        return profitable_routes

    def simulate_market_event(self, event_type: str, affected_posts: List[str],
                            resource_impacts: Dict[str, float]) -> None:
        """Simulate a market event affecting specific resources"""

        for post_id in affected_posts:
            if post_id not in self.trading_posts:
                continue

            post = self.trading_posts[post_id]

            for resource_name, impact in resource_impacts.items():
                try:
                    resource_type = ResourceType(resource_name)
                    if resource_type in post.market_prices:
                        market_price = post.market_prices[resource_type]

                        if event_type == 'supply_shock':
                            market_price.supply *= (1 - impact)
                        elif event_type == 'demand_surge':
                            market_price.demand *= (1 + impact)
                        elif event_type == 'price_crash':
                            market_price.current_price *= (1 - impact)
                        elif event_type == 'price_spike':
                            market_price.current_price *= (1 + impact)

                except ValueError:
                    continue  # Invalid resource type

# Example usage and testing
if __name__ == "__main__":
    # Create cosmic economy system
    economy = CosmicEconomySystem()

    print("Cosmic Economy System Initialized")
    print(f"Available Resources: {[r.value for r in ResourceType]}")
    print(f"Available Trade Goods: {list(economy.trade_goods.keys())}")

    # Create trading posts
    print("\n" + "="*50)
    print("CREATING TRADING POSTS")
    print("="*50)

    sol_post = economy.create_trading_post({
        'id': 'sol_trading_post',
        'name': 'Sol Central Market',
        'system_id': 'sol',
        'location': [0, 0, 0],
        'market_type': 'regional',
        'economic_policy': 'mixed_economy',
        'tax_rate': 0.15,
        'specializations': ['common_metals', 'energy_cells', 'technology']
    })

    alpha_centauri_post = economy.create_trading_post({
        'id': 'alpha_centauri_market',
        'name': 'Alpha Centauri Exchange',
        'system_id': 'alpha_centauri',
        'location': [4.37, 0, 0],  # 4.37 light-years away
        'market_type': 'local',
        'economic_policy': 'free_market',
        'tax_rate': 0.08,
        'specializations': ['rare_metals', 'biological_samples']
    })

    sirius_post = economy.create_trading_post({
        'id': 'sirius_commercial_hub',
        'name': 'Sirius Commercial Hub',
        'system_id': 'sirius',
        'location': [8.66, 0, 0],  # 8.66 light-years away
        'market_type': 'regional',
        'economic_policy': 'corporate_state',
        'tax_rate': 0.20,
        'specializations': ['exotic_metals', 'luxury_goods']
    })

    print(f"Created {len(economy.trading_posts)} trading posts")

    # Create corporations
    print("\n" + "="*50)
    print("CREATING CORPORATIONS")
    print("="*50)

    megacorp = economy.create_corporation({
        'id': 'stellar_megacorp',
        'name': 'Stellar Megacorporation',
        'headquarters': 'sol',
        'market_capitalization': 5e12,
        'employee_count': 1000000,
        'specializations': ['technology', 'energy_cells', 'weapons'],
        'reputation': 0.7,
        'ethical_rating': 0.3
    })

    bio_industries = economy.create_corporation({
        'id': 'bio_frontier',
        'name': 'Bio Frontier Industries',
        'headquarters': 'alpha_centauri',
        'market_capitalization': 1.2e12,
        'employee_count': 250000,
        'specializations': ['biomass', 'medical_supplies', 'organic_compounds'],
        'reputation': 0.8,
        'ethical_rating': 0.9
    })

    print(f"Created {len(economy.corporations)} corporations")

    # Create trade routes
    print("\n" + "="*50)
    print("CREATING TRADE ROUTES")
    print("="*50)

    route1 = economy.create_trade_route({
        'id': 'sol_alpha_route',
        'origin_system': 'sol',
        'destination_system': 'alpha_centauri',
        'distance': 4.37,
        'trade_volume': 5000,
        'security_level': 0.9,
        'toll_cost': 1000,
        'controlling_faction': 'stellar_megacorp'
    })

    route2 = economy.create_trade_route({
        'id': 'sol_sirius_route',
        'origin_system': 'sol',
        'destination_system': 'sirius',
        'distance': 8.66,
        'trade_volume': 3000,
        'security_level': 0.7,
        'toll_cost': 2500,
        'controlling_faction': 'stellar_megacorp',
        'competing_factions': ['independent_traders']
    })

    route3 = economy.create_trade_route({
        'id': 'alpha_sirius_route',
        'origin_system': 'alpha_centauri',
        'destination_system': 'sirius',
        'distance': 5.0,
        'trade_volume': 2000,
        'security_level': 0.8,
        'toll_cost': 1800,
        'controlling_faction': 'independent_traders'
    })

    print(f"Created {len(economy.trade_routes)} trade routes")

    # Execute some sample transactions
    print("\n" + "="*50)
    print("EXECUTING TRADE TRANSACTIONS")
    print("="*50)

    # Transaction 1: Buy rare metals at Sol
    tx1 = economy.execute_trade_transaction(
        buyer_id='bio_frontier',
        seller_id='stellar_megacorp',
        post_id='sol_trading_post',
        resource_type=ResourceType.RARE_METALS,
        quantity=100,
        payment_method='credits'
    )

    if tx1:
        print(f"Transaction 1: {tx1.quantity} units of {tx1.resource_type.value}")
        print(f"  Unit Price: {tx1.unit_price:.2f} credits")
        print(f"  Total Value: {tx1.total_value:.2f} credits")
        print(f"  Taxes Paid: {tx1.taxes_paid:.2f} credits")

    # Transaction 2: Buy biological samples at Alpha Centauri
    tx2 = economy.execute_trade_transaction(
        buyer_id='stellar_megacorp',
        seller_id='bio_frontier',
        post_id='alpha_centauri_market',
        resource_type=ResourceType.BIOLOGICAL_SAMPLES,
        quantity=50,
        payment_method='credits'
    )

    if tx2:
        print(f"\nTransaction 2: {tx2.quantity} units of {tx2.resource_type.value}")
        print(f"  Unit Price: {tx2.unit_price:.2f} credits")
        print(f"  Total Value: {tx2.total_value:.2f} credits")

    # Calculate trade route profitability
    print("\n" + "="*50)
    print("ANALYZING TRADE ROUTES")
    print("="*50)

    # Check profitability of trading rare metals from Sol to Sirius
    profitability = economy.calculate_trade_route_profitability(
        route2, ResourceType.RARE_METALS, 200
    )

    print(f"Trade Route Analysis: {route2.id}")
    print(f"  Resource: {ResourceType.RARE_METALS.value}")
    print(f"  Origin Price: {profitability['origin_price']:.2f}")
    print(f"  Destination Price: {profitability['dest_price']:.2f}")
    print(f"  Purchase Cost: {profitability['purchase_cost']:.2f}")
    print(f"  Transport Cost: {profitability['transport_cost']:.2f}")
    print(f"  Sale Revenue: {profitability['sale_revenue']:.2f}")
    print(f"  Profit: {profitability['profit']:.2f}")
    print(f"  Profit Margin: {profitability['profit_margin']:.2%}")
    print(f"  Risk Level: {profitability['risk_level']:.2f}")

    # Find all profitable routes
    print("\n" + "="*50)
    print("PROFITABLE TRADE OPPORTUNITIES")
    print("="*50)

    profitable_routes = economy.find_profitable_trade_routes(min_profit_margin=0.15)
    print(f"Found {len(profitable_routes)} profitable trade opportunities:")

    for i, route in enumerate(profitable_routes[:5], 1):  # Show top 5
        print(f"  {i}. {route['resource']} from {route['origin']} to {route['destination']}")
        print(f"     Profit Margin: {route['profit_margin']:.2%}, Risk: {route['risk_level']:.2f}")

    # Market reports
    print("\n" + "="*50)
    print("MARKET REPORTS")
    print("="*50)

    for post_id, post in economy.trading_posts.items():
        report = economy.get_market_report(post_id)
        print(f"\n{report['post_name']}:")
        print(f"  Market Type: {report['market_type']}")
        print(f"  Economic Policy: {report['economic_policy']}")
        print(f"  Tax Rate: {report['tax_rate']:.1%}")
        print(f"  Reputation: {report['reputation']:.2f}")
        print(f"  Total Supply: {report['total_supply']:.0f}")
        print(f"  Total Demand: {report['demand']:.0f}")
        print(f"  Average Price: {report['average_price']:.2f}")
        print(f"  Top Resources: {report['top_resources'][:3]}")

    # Simulate market dynamics
    print("\n" + "="*50)
    print("SIMULATING MARKET DYNAMICS")
    print("="*50)

    print("Simulating 50 time periods of market activity...")
    economy.update_market_dynamics(50)

    # Simulate a market event
    print("\nSimulating market event: Supply shock in rare metals...")
    economy.simulate_market_event(
        'supply_shock',
        ['sol_trading_post', 'sirius_commercial_hub'],
        {'rare_metals': 0.5}  # 50% supply reduction
    )

    # Check updated prices
    print("\nUpdated rare metal prices:")
    for post_id, post in economy.trading_posts.items():
        if ResourceType.RARE_METALS in post.market_prices:
            price = post.market_prices[ResourceType.RARE_METALS].current_price
            trend = post.market_prices[ResourceType.RARE_METALS].market_trend
            print(f"  {post.name}: {price:.2f} credits ({trend})")

    # Market indices
    print("\n" + "="*50)
    print("MARKET INDICES")
    print("="*50)

    for index_name, value in economy.market_indices.items():
        print(f"  {index_name}: {value:.2f}")

    print(f"\nTotal Transactions Processed: {len(economy.transactions)}")
    print(f"Current Simulation Time: {economy.current_time:.1f}")

    print("\nCosmic Economy Features:")
    print("- Dynamic market pricing based on supply and demand")
    print("- Multiple trading posts with different economic policies")
    print("- Corporate entities with specializations")
    print("- Trade route profitability analysis")
    print("- Market events and price shocks")
    print("- Tax systems and transaction processing")
    print("- Market performance indices")
    print("- Resource scarcity and abundance modeling")

    print("\nCosmic economy system test completed successfully!")