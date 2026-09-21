"""
DMLogn8n Virtual Economy - In-Game Economy and Virtual Goods Marketplace

This module manages the virtual economy including virtual currencies, items, crafting,
trading, marketplace operations, and economic balance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict
import redis
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class CurrencyType(Enum):
    """Virtual currency types"""
    GOLD = "gold"
    GEMS = "gems"
    CREDITS = "credits"
    EXPERIENCE = "experience"
    REPUTATION = "reputation"
    LOYALTY_POINTS = "loyalty_points"
    REFERRAL_TOKENS = "referral_tokens"

class ItemType(Enum):
    """Virtual item categories"""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    CURRENCY = "currency"
    DECORATION = "decoration"
    TOOL = "tool"
    QUEST_ITEM = "quest_item"
    COSMETIC = "cosmetic"
    PET = "pet"
    MOUNT = "mount"
    SKIN = "skin"

class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    UNIQUE = "unique"

class TransactionType(Enum):
    """Transaction types"""
    PURCHASE = "purchase"
    SALE = "sale"
    TRADE = "trade"
    CRAFT = "craft"
    GIFT = "gift"
    REWARD = "reward"
    REFUND = "refund"
    EXCHANGE = "exchange"

class MarketStatus(Enum):
    """Market listing status"""
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

@dataclass
class VirtualCurrency:
    """Virtual currency definition"""
    id: str
    name: str
    symbol: str
    type: CurrencyType
    initial_supply: int = 0
    max_supply: Optional[int] = None
    inflation_rate: float = 0.0
    exchange_rate: Dict[str, float] = field(default_factory=dict)
    earnable: bool = True
    tradable: bool = True
    purchasable: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VirtualItem:
    """Virtual item definition"""
    id: str
    name: str
    description: str
    type: ItemType
    rarity: ItemRarity
    base_price: Decimal
    currency: CurrencyType
    stackable: bool = True
    max_stack: int = 999
    consumable: bool = False
    tradeable: bool = True
    sellable: bool = True
    durability: Optional[int] = None
    level_requirement: int = 0
    stats: Dict[str, Any] = field(default_factory=dict)
    effects: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CraftingRecipe:
    """Crafting recipe definition"""
    id: str
    name: str
    description: str
    result_item_id: str
    result_quantity: int = 1
    ingredients: Dict[str, int] = field(default_factory=dict)
    currency_cost: Dict[str, int] = field(default_factory=dict)
    crafting_time: int = 0  # seconds
    level_requirement: int = 0
    success_rate: float = 1.0
    experience_reward: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketListing:
    """Marketplace listing"""
    id: str
    seller_id: str
    item_id: str
    quantity: int
    price: Decimal
    currency: CurrencyType
    status: MarketStatus = MarketStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PlayerInventory:
    """Player inventory state"""
    player_id: str
    items: Dict[str, int] = field(default_factory=dict)
    currencies: Dict[CurrencyType, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class VirtualEconomy:
    """Main virtual economy manager"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.currencies: Dict[str, VirtualCurrency] = {}
        self.items: Dict[str, VirtualItem] = {}
        self.recipes: Dict[str, CraftingRecipe] = {}
        self.economic_indicators: Dict[str, float] = {}
        self.market_stats: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize virtual economy system"""
        logger.info("Initializing DMLogn8n Virtual Economy...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_economy')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Load currencies
        await self._load_currencies()

        # Load items
        await self._load_items()

        # Load recipes
        await self._load_recipes()

        # Initialize economic indicators
        await self._initialize_economic_indicators()

        # Start background tasks
        asyncio.create_task(self._economic_simulation())
        asyncio.create_task(self._market_cleanup())
        asyncio.create_task(self._inflation_control())

        logger.info("Virtual Economy initialized successfully")

    async def _load_currencies(self):
        """Load virtual currency definitions"""
        default_currencies = [
            VirtualCurrency(
                id="gold",
                name="Gold Coins",
                symbol="G",
                type=CurrencyType.GOLD,
                initial_supply=1000000,
                max_supply=10000000,
                inflation_rate=0.02,
                exchange_rate={"gems": 0.01, "credits": 10},
                earnable=True,
                tradable=True,
                purchasable=True,
                description="Standard currency for purchases and trading"
            ),
            VirtualCurrency(
                id="gems",
                name="Gemstones",
                symbol="💎",
                type=CurrencyType.GEMS,
                initial_supply=100000,
                max_supply=1000000,
                inflation_rate=0.01,
                exchange_rate={"gold": 100, "credits": 1000},
                earnable=True,
                tradable=True,
                purchasable=True,
                description="Premium currency for exclusive items"
            ),
            VirtualCurrency(
                id="credits",
                name="Campaign Credits",
                symbol="C",
                type=CurrencyType.CREDITS,
                initial_supply=0,
                max_supply=None,
                inflation_rate=0.0,
                exchange_rate={"gold": 0.1, "gems": 0.001},
                earnable=True,
                tradable=False,
                purchasable=True,
                description="Campaign-specific earned currency"
            ),
            VirtualCurrency(
                id="loyalty_points",
                name="Loyalty Points",
                symbol="⭐",
                type=CurrencyType.LOYALTY_POINTS,
                initial_supply=0,
                max_supply=None,
                inflation_rate=0.0,
                exchange_rate={},
                earnable=True,
                tradable=False,
                purchasable=False,
                description="Reward points for loyal players"
            )
        ]

        for currency in default_currencies:
            self.currencies[currency.id] = currency
            await self.redis_client.setex(
                f"currency:{currency.id}",
                86400 * 365,  # 1 year
                json.dumps({
                    'name': currency.name,
                    'symbol': currency.symbol,
                    'type': currency.type.value,
                    'exchange_rate': currency.exchange_rate
                })
            )

    async def _load_items(self):
        """Load virtual item definitions"""
        default_items = [
            VirtualItem(
                id="health_potion",
                name="Health Potion",
                description="Restores 50 health points",
                type=ItemType.CONSUMABLE,
                rarity=ItemRarity.COMMON,
                base_price=Decimal('10.00'),
                currency=CurrencyType.GOLD,
                stackable=True,
                max_stack=99,
                consumable=True,
                effects=["heal_50"]
            ),
            VirtualItem(
                id="iron_sword",
                name="Iron Sword",
                description="A sturdy iron sword",
                type=ItemType.WEAPON,
                rarity=ItemRarity.COMMON,
                base_price=Decimal('100.00'),
                currency=CurrencyType.GOLD,
                stackable=False,
                consumable=False,
                stats={"attack": 15, "durability": 100}
            ),
            VirtualItem(
                id="dragon_scale",
                name="Dragon Scale",
                description="Rare dragon scale for crafting",
                type=ItemType.MATERIAL,
                rarity=ItemRarity.RARE,
                base_price=Decimal('500.00'),
                currency=CurrencyType.GOLD,
                stackable=True,
                max_stack=20,
                stats={},
                tags=["rare_material", "crafting"]
            ),
            VirtualItem(
                id="mystic_crystal",
                name="Mystic Crystal",
                description="A crystal imbued with magical energy",
                type=ItemType.MATERIAL,
                rarity=ItemRarity.LEGENDARY,
                base_price=Decimal('50.00'),
                currency=CurrencyType.GEMS,
                stackable=True,
                max_stack=10,
                stats={},
                effects=["magic_boost_10"],
                tags=["legendary_material", "magic"]
            ),
            VirtualItem(
                id="campaign_map",
                name="Campaign Map",
                description="Detailed campaign world map",
                type=ItemType.QUEST_ITEM,
                rarity=ItemRarity.UNCOMMON,
                base_price=Decimal('25.00'),
                currency=CurrencyType.CREDITS,
                stackable=True,
                consumable=False,
                effects=["reveal_locations"]
            ),
            VirtualItem(
                id="golden_armor_skin",
                name="Golden Armor Skin",
                description="Cosmetic skin for armor",
                type=ItemType.COSMETIC,
                rarity=ItemRarity.EPIC,
                base_price=Decimal('100.00'),
                currency=CurrencyType.GEMS,
                stackable=False,
                consumable=False,
                tradeable=True,
                sellable=True,
                tags=["cosmetic", "armor"]
            )
        ]

        for item in default_items:
            self.items[item.id] = item
            await self.redis_client.setex(
                f"item:{item.id}",
                86400 * 365,  # 1 year
                json.dumps({
                    'name': item.name,
                    'description': item.description,
                    'type': item.type.value,
                    'rarity': item.rarity.value,
                    'base_price': float(item.base_price),
                    'currency': item.currency.value,
                    'stackable': item.stackable,
                    'max_stack': item.max_stack,
                    'consumable': item.consumable,
                    'tradeable': item.tradeable,
                    'sellable': item.sellable,
                    'stats': item.stats,
                    'effects': item.effects,
                    'tags': item.tags
                })
            )

    async def _load_recipes(self):
        """Load crafting recipes"""
        default_recipes = [
            CraftingRecipe(
                id="healing_salve",
                name="Healing Salve",
                description="Craft a healing salve from herbs",
                result_item_id="healing_salve",
                result_quantity=3,
                ingredients={"herb": 2, "water_vial": 1},
                currency_cost={"gold": 5},
                crafting_time=60,
                level_requirement=1,
                success_rate=0.95,
                experience_reward=10
            ),
            CraftingRecipe(
                id="iron_sword_craft",
                name="Iron Sword Crafting",
                description="Craft an iron sword from iron ingots",
                result_item_id="iron_sword",
                result_quantity=1,
                ingredients={"iron_ingot": 3, "wood_handle": 1},
                currency_cost={"gold": 20},
                crafting_time=300,
                level_requirement=5,
                success_rate=0.85,
                experience_reward=50
            ),
            CraftingRecipe(
                id="dragon_scale_armor",
                name="Dragon Scale Armor",
                description="Craft legendary armor from dragon scales",
                result_item_id="dragon_scale_armor",
                result_quantity=1,
                ingredients={"dragon_scale": 10, "mithril_ingot": 5, "enchantment_rune": 1},
                currency_cost={"gold": 1000, "gems": 50},
                crafting_time=3600,
                level_requirement=20,
                success_rate=0.6,
                experience_reward=500
            )
        ]

        for recipe in default_recipes:
            self.recipes[recipe.id] = recipe
            await self.redis_client.setex(
                f"recipe:{recipe.id}",
                86400 * 365,  # 1 year
                json.dumps({
                    'name': recipe.name,
                    'description': recipe.description,
                    'result_item_id': recipe.result_item_id,
                    'result_quantity': recipe.result_quantity,
                    'ingredients': recipe.ingredients,
                    'currency_cost': recipe.currency_cost,
                    'crafting_time': recipe.crafting_time,
                    'level_requirement': recipe.level_requirement,
                    'success_rate': recipe.success_rate,
                    'experience_reward': recipe.experience_reward
                })
            )

    async def _initialize_economic_indicators(self):
        """Initialize economic monitoring indicators"""
        self.economic_indicators = {
            'gold_supply': 1000000,
            'gem_supply': 100000,
            'inflation_rate': 0.02,
            'market_activity': 0.0,
            'price_index': 100.0,
            'liquidity_index': 100.0,
            'trade_volume': 0.0
        }

        # Store initial indicators
        await self.redis_client.hset(
            "economic_indicators",
            mapping={k: str(v) for k, v in self.economic_indicators.items()}
        )

    async def get_player_inventory(self, player_id: str) -> PlayerInventory:
        """Get player's current inventory"""
        try:
            # Try to get from cache
            cached_inventory = await self.redis_client.get(f"inventory:{player_id}")
            if cached_inventory:
                data = json.loads(cached_inventory)
                return PlayerInventory(
                    player_id=data['player_id'],
                    items=data['items'],
                    currencies={CurrencyType(k): v for k, v in data['currencies'].items()},
                    last_updated=datetime.fromisoformat(data['last_updated']),
                    metadata=data['metadata']
                )

            # Load from database
            inventory = await self._load_inventory_from_db(player_id)
            if inventory:
                await self._cache_inventory(inventory)
                return inventory

            # Create new inventory
            new_inventory = PlayerInventory(player_id=player_id)
            await self._save_inventory_to_db(new_inventory)
            await self._cache_inventory(new_inventory)
            return new_inventory

        except Exception as e:
            logger.error(f"Error getting inventory for {player_id}: {e}")
            return PlayerInventory(player_id=player_id)

    async def _cache_inventory(self, inventory: PlayerInventory):
        """Cache inventory in Redis"""
        inventory_data = {
            'player_id': inventory.player_id,
            'items': inventory.items,
            'currencies': {k.value: v for k, v in inventory.currencies.items()},
            'last_updated': inventory.last_updated.isoformat(),
            'metadata': inventory.metadata
        }

        await self.redis_client.setex(
            f"inventory:{inventory.player_id}",
            3600,  # 1 hour cache
            json.dumps(inventory_data)
        )

    async def _load_inventory_from_db(self, player_id: str) -> Optional[PlayerInventory]:
        """Load inventory from database"""
        session = self.session_factory()
        try:
            # Query inventory from database (simplified)
            # Would use proper ORM models in real implementation
            return None
        finally:
            session.close()

    async def _save_inventory_to_db(self, inventory: PlayerInventory):
        """Save inventory to database"""
        session = self.session_factory()
        try:
            # Save to database (simplified)
            pass
        finally:
            session.close()

    async def add_currency(self, player_id: str, currency_type: CurrencyType,
                          amount: int, reason: str = "") -> bool:
        """Add currency to player's inventory"""
        try:
            if amount <= 0:
                return False

            inventory = await self.get_player_inventory(player_id)
            current_amount = inventory.currencies.get(currency_type, 0)
            inventory.currencies[currency_type] = current_amount + amount
            inventory.last_updated = datetime.utcnow()

            # Update global currency supply
            if currency_type.value in self.economic_indicators:
                self.economic_indicators[f"{currency_type.value}_supply"] += amount

            # Cache and save
            await self._cache_inventory(inventory)
            await self._save_inventory_to_db(inventory)

            # Log transaction
            await self._log_transaction(
                player_id, TransactionType.REWARD, currency_type.value,
                amount, reason
            )

            return True

        except Exception as e:
            logger.error(f"Error adding currency: {e}")
            return False

    async def remove_currency(self, player_id: str, currency_type: CurrencyType,
                           amount: int, reason: str = "") -> bool:
        """Remove currency from player's inventory"""
        try:
            if amount <= 0:
                return False

            inventory = await self.get_player_inventory(player_id)
            current_amount = inventory.currencies.get(currency_type, 0)

            if current_amount < amount:
                return False

            inventory.currencies[currency_type] = current_amount - amount
            inventory.last_updated = datetime.utcnow()

            # Update global currency supply
            if currency_type.value in self.economic_indicators:
                self.economic_indicators[f"{currency_type.value}_supply"] -= amount

            # Cache and save
            await self._cache_inventory(inventory)
            await self._save_inventory_to_db(inventory)

            # Log transaction
            await self._log_transaction(
                player_id, TransactionType.PURCHASE, currency_type.value,
                amount, reason
            )

            return True

        except Exception as e:
            logger.error(f"Error removing currency: {e}")
            return False

    async def add_item(self, player_id: str, item_id: str, quantity: int = 1,
                      reason: str = "") -> bool:
        """Add item to player's inventory"""
        try:
            if quantity <= 0:
                return False

            item = self.items.get(item_id)
            if not item:
                return False

            inventory = await self.get_player_inventory(player_id)
            current_quantity = inventory.items.get(item_id, 0)

            # Check stack limit
            if item.stackable:
                new_quantity = min(current_quantity + quantity, item.max_stack)
                added_quantity = new_quantity - current_quantity
            else:
                if quantity > 1:
                    # Can't add more than 1 of non-stackable item
                    added_quantity = 1 if current_quantity == 0 else 0
                else:
                    added_quantity = 1 if current_quantity == 0 else 0

            if added_quantity > 0:
                inventory.items[item_id] = current_quantity + added_quantity
                inventory.last_updated = datetime.utcnow()

                # Cache and save
                await self._cache_inventory(inventory)
                await self._save_inventory_to_db(inventory)

                # Log transaction
                await self._log_transaction(
                    player_id, TransactionType.REWARD, item_id,
                    added_quantity, reason
                )

            return added_quantity > 0

        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return False

    async def remove_item(self, player_id: str, item_id: str, quantity: int = 1,
                         reason: str = "") -> bool:
        """Remove item from player's inventory"""
        try:
            if quantity <= 0:
                return False

            inventory = await self.get_player_inventory(player_id)
            current_quantity = inventory.items.get(item_id, 0)

            if current_quantity < quantity:
                return False

            new_quantity = current_quantity - quantity
            if new_quantity > 0:
                inventory.items[item_id] = new_quantity
            else:
                del inventory.items[item_id]

            inventory.last_updated = datetime.utcnow()

            # Cache and save
            await self._cache_inventory(inventory)
            await self._save_inventory_to_db(inventory)

            # Log transaction
            await self._log_transaction(
                player_id, TransactionType.PURCHASE, item_id,
                quantity, reason
            )

            return True

        except Exception as e:
            logger.error(f"Error removing item: {e}")
            return False

    async def purchase_item(self, player_id: str, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Purchase item with virtual currency"""
        try:
            item = self.items.get(item_id)
            if not item:
                return {'success': False, 'error': 'Item not found'}

            inventory = await self.get_player_inventory(player_id)

            # Check if player can afford
            required_amount = int(item.base_price * quantity)
            if not await self.remove_currency(player_id, item.currency, required_amount, "item_purchase"):
                return {'success': False, 'error': 'Insufficient currency'}

            # Add item to inventory
            if await self.add_item(player_id, item_id, quantity, "item_purchase"):
                # Update market stats
                await self._update_market_stats(item_id, quantity, float(item.base_price))

                return {
                    'success': True,
                    'item_id': item_id,
                    'quantity': quantity,
                    'total_cost': required_amount,
                    'currency': item.currency.value
                }
            else:
                # Refund currency if item couldn't be added
                await self.add_currency(player_id, item.currency, required_amount, "refund_failed_purchase")
                return {'success': False, 'error': 'Failed to add item to inventory'}

        except Exception as e:
            logger.error(f"Error purchasing item: {e}")
            return {'success': False, 'error': str(e)}

    async def create_market_listing(self, seller_id: str, item_id: str, quantity: int,
                                   price: Decimal, currency: CurrencyType,
                                   duration_days: int = 7) -> Dict[str, Any]:
        """Create marketplace listing"""
        try:
            item = self.items.get(item_id)
            if not item:
                return {'success': False, 'error': 'Item not found'}

            if not item.tradeable:
                return {'success': False, 'error': 'Item is not tradeable'}

            inventory = await self.get_player_inventory(seller_id)
            current_quantity = inventory.items.get(item_id, 0)

            if current_quantity < quantity:
                return {'success': False, 'error': 'Insufficient items'}

            # Remove items from inventory (hold for sale)
            if not await self.remove_item(seller_id, item_id, quantity, "market_listing"):
                return {'success': False, 'error': 'Failed to remove items from inventory'}

            # Create listing
            listing_id = str(uuid.uuid4())
            listing = MarketListing(
                id=listing_id,
                seller_id=seller_id,
                item_id=item_id,
                quantity=quantity,
                price=price,
                currency=currency,
                expires_at=datetime.utcnow() + timedelta(days=duration_days)
            )

            # Store listing
            listing_data = {
                'id': listing.id,
                'seller_id': listing.seller_id,
                'item_id': listing.item_id,
                'quantity': listing.quantity,
                'price': float(listing.price),
                'currency': listing.currency.value,
                'status': listing.status.value,
                'created_at': listing.created_at.isoformat(),
                'expires_at': listing.expires_at.isoformat() if listing.expires_at else None
            }

            await self.redis_client.setex(
                f"listing:{listing_id}",
                86400 * duration_days,
                json.dumps(listing_data)
            )

            # Add to market index
            await self.redis_client.lpush("market_listings", listing_id)

            return {
                'success': True,
                'listing_id': listing_id,
                'item_id': item_id,
                'quantity': quantity,
                'price': float(price),
                'currency': currency.value,
                'expires_at': listing.expires_at.isoformat() if listing.expires_at else None
            }

        except Exception as e:
            logger.error(f"Error creating market listing: {e}")
            return {'success': False, 'error': str(e)}

    async def purchase_market_listing(self, buyer_id: str, listing_id: str) -> Dict[str, Any]:
        """Purchase item from marketplace"""
        try:
            # Get listing
            listing_data = await self.redis_client.get(f"listing:{listing_id}")
            if not listing_data:
                return {'success': False, 'error': 'Listing not found'}

            listing_info = json.loads(listing_data)
            listing = MarketListing(
                id=listing_info['id'],
                seller_id=listing_info['seller_id'],
                item_id=listing_info['item_id'],
                quantity=listing_info['quantity'],
                price=Decimal(str(listing_info['price'])),
                currency=CurrencyType(listing_info['currency']),
                status=MarketStatus(listing_info['status']),
                created_at=datetime.fromisoformat(listing_info['created_at']),
                expires_at=datetime.fromisoformat(listing_info['expires_at']) if listing_info['expires_at'] else None
            )

            if listing.status != MarketStatus.ACTIVE:
                return {'success': False, 'error': 'Listing is not active'}

            if listing.expires_at and datetime.utcnow() > listing.expires_at:
                return {'success': False, 'error': 'Listing has expired'}

            # Calculate total cost
            total_cost = int(listing.price * listing.quantity)

            # Check if buyer can afford
            buyer_inventory = await self.get_player_inventory(buyer_id)
            if buyer_inventory.currencies.get(listing.currency, 0) < total_cost:
                return {'success': False, 'error': 'Insufficient currency'}

            # Process payment
            if not await self.remove_currency(buyer_id, listing.currency, total_cost, "market_purchase"):
                return {'success': False, 'error': 'Payment failed'}

            # Add items to buyer
            if not await self.add_item(buyer_id, listing.item_id, listing.quantity, "market_purchase"):
                # Refund if item addition failed
                await self.add_currency(buyer_id, listing.currency, total_cost, "refund_failed_purchase")
                return {'success': False, 'error': 'Failed to add items to inventory'}

            # Pay seller (minus marketplace fee)
            marketplace_fee_rate = 0.05  # 5% fee
            seller_payment = int(total_cost * (1 - marketplace_fee_rate))
            await self.add_currency(listing.seller_id, listing.currency, seller_payment, "market_sale")

            # Update listing status
            listing.status = MarketStatus.SOLD
            listing_data['status'] = listing.status.value
            await self.redis_client.setex(
                f"listing:{listing_id}",
                86400,
                json.dumps(listing_data)
            )

            # Update market stats
            await self._update_market_stats(listing.item_id, listing.quantity, float(listing.price))

            return {
                'success': True,
                'listing_id': listing_id,
                'item_id': listing.item_id,
                'quantity': listing.quantity,
                'total_cost': total_cost,
                'currency': listing.currency.value,
                'seller_id': listing.seller_id
            }

        except Exception as e:
            logger.error(f"Error purchasing market listing: {e}")
            return {'success': False, 'error': str(e)}

    async def craft_item(self, player_id: str, recipe_id: str) -> Dict[str, Any]:
        """Craft item using recipe"""
        try:
            recipe = self.recipes.get(recipe_id)
            if not recipe:
                return {'success': False, 'error': 'Recipe not found'}

            inventory = await self.get_player_inventory(player_id)

            # Check level requirement
            player_level = inventory.metadata.get('level', 1)
            if player_level < recipe.level_requirement:
                return {'success': False, 'error': 'Insufficient level'}

            # Check ingredients
            for ingredient_id, required_quantity in recipe.ingredients.items():
                current_quantity = inventory.items.get(ingredient_id, 0)
                if current_quantity < required_quantity:
                    return {'success': False, 'error': f'Insufficient {ingredient_id}'}

            # Check currency cost
            for currency_type, required_amount in recipe.currency_cost.items():
                current_amount = inventory.currencies.get(CurrencyType(currency_type), 0)
                if current_amount < required_amount:
                    return {'success': False, 'error': f'Insufficient {currency_type}'}

            # Remove ingredients
            for ingredient_id, required_quantity in recipe.ingredients.items():
                await self.remove_item(player_id, ingredient_id, required_quantity, "crafting")

            # Remove currency cost
            for currency_type, required_amount in recipe.currency_cost.items():
                await self.remove_currency(player_id, CurrencyType(currency_type), required_amount, "crafting")

            # Roll for success
            import random
            success = random.random() < recipe.success_rate

            if success:
                # Add crafted item
                await self.add_item(player_id, recipe.result_item_id, recipe.result_quantity, "crafting")

                # Add experience
                if recipe.experience_reward > 0:
                    await self.add_currency(player_id, CurrencyType.EXPERIENCE, recipe.experience_reward, "crafting_reward")

                return {
                    'success': True,
                    'item_id': recipe.result_item_id,
                    'quantity': recipe.result_quantity,
                    'experience_gained': recipe.experience_reward
                }
            else:
                return {
                    'success': False,
                    'error': 'Crafting failed',
                    'ingredients_consumed': True
                }

        except Exception as e:
            logger.error(f"Error crafting item: {e}")
            return {'success': False, 'error': str(e)}

    async def get_market_listings(self, item_type: Optional[ItemType] = None,
                                min_price: Optional[Decimal] = None,
                                max_price: Optional[Decimal] = None,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """Get marketplace listings with filters"""
        try:
            listings = []

            # Get all active listing IDs
            listing_ids = await self.redis_client.lrange("market_listings", 0, -1)

            for listing_id_bytes in listing_ids:
                listing_id = listing_id_bytes.decode()
                listing_data = await self.redis_client.get(f"listing:{listing_id}")

                if listing_data:
                    listing_info = json.loads(listing_data)

                    # Check if listing is still active
                    if listing_info['status'] != 'active':
                        continue

                    # Check if expired
                    if listing_info['expires_at']:
                        expires_at = datetime.fromisoformat(listing_info['expires_at'])
                        if datetime.utcnow() > expires_at:
                            # Mark as expired
                            listing_info['status'] = 'expired'
                            await self.redis_client.setex(
                                f"listing:{listing_id}",
                                86400,
                                json.dumps(listing_info)
                            )
                            continue

                    # Apply filters
                    item = self.items.get(listing_info['item_id'])
                    if not item:
                        continue

                    if item_type and item.type != item_type:
                        continue

                    price = Decimal(str(listing_info['price']))
                    if min_price and price < min_price:
                        continue

                    if max_price and price > max_price:
                        continue

                    # Add item info to listing
                    listing_info['item_name'] = item.name
                    listing_info['item_description'] = item.description
                    listing_info['item_rarity'] = item.rarity.value

                    listings.append(listing_info)

                    if len(listings) >= limit:
                        break

            return listings

        except Exception as e:
            logger.error(f"Error getting market listings: {e}")
            return []

    async def get_economy_stats(self) -> Dict[str, Any]:
        """Get economic statistics and indicators"""
        try:
            # Get current economic indicators
            indicators = await self.redis_client.hgetall("economic_indicators")
            current_indicators = {k.decode(): float(v.decode()) for k, v in indicators.items()}

            # Calculate additional metrics
            total_transactions = await self.redis_client.get("total_transactions")
            total_volume = await self.redis_client.get("total_volume")

            # Get market activity
            active_listings = await self.redis_client.llen("market_listings")

            # Calculate price trends
            price_trends = await self._calculate_price_trends()

            return {
                'economic_indicators': current_indicators,
                'total_transactions': int(total_transactions) if total_transactions else 0,
                'total_volume': float(total_volume) if total_volume else 0.0,
                'active_listings': active_listings,
                'price_trends': price_trends,
                'currency_supplies': {
                    currency_id: current_indicators.get(f"{currency_id}_supply", 0)
                    for currency_id in self.currencies.keys()
                }
            }

        except Exception as e:
            logger.error(f"Error getting economy stats: {e}")
            return {}

    async def _log_transaction(self, player_id: str, transaction_type: TransactionType,
                             item_or_currency: str, quantity: int, reason: str):
        """Log economic transaction"""
        transaction = {
            'player_id': player_id,
            'type': transaction_type.value,
            'item_or_currency': item_or_currency,
            'quantity': quantity,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.redis_client.lpush("transactions", json.dumps(transaction))
        await self.redis_client.incr("total_transactions")

    async def _update_market_stats(self, item_id: str, quantity: int, price: float):
        """Update market statistics"""
        # Update total volume
        total_volume = float(quantity * price)
        await self.redis_client.incrbyfloat("total_volume", total_volume)

        # Update item-specific stats
        item_stats_key = f"item_stats:{item_id}"
        await self.redis_client.hincrby(item_stats_key, "total_sold", quantity)
        await self.redis_client.hincrbyfloat(item_stats_key, "total_volume", total_volume)
        await self.redis_client.hincrbyfloat(item_stats_key, "avg_price", price)
        await self.redis_client.expire(item_stats_key, 86400 * 30)

    async def _calculate_price_trends(self) -> Dict[str, float]:
        """Calculate price trends for items"""
        trends = {}

        for item_id in self.items.keys():
            item_stats_key = f"item_stats:{item_id}"
            stats = await self.redis_client.hgetall(item_stats_key)

            if stats:
                avg_price = float(stats.get(b'avg_price', 0))
                total_sold = int(stats.get(b'total_sold', 0))
                total_volume = float(stats.get(b'total_volume', 0))

                # Calculate trend indicator (simplified)
                # In real implementation, would use historical data
                base_price = float(self.items[item_id].base_price)
                price_ratio = avg_price / base_price if base_price > 0 else 1.0

                trends[item_id] = price_ratio

        return trends

    async def _economic_simulation(self):
        """Background task for economic simulation"""
        while True:
            try:
                logger.info("Running economic simulation...")

                # Update inflation
                await self._update_inflation()

                # Adjust exchange rates
                await self._adjust_exchange_rates()

                # Update market activity
                await self._update_market_activity()

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in economic simulation: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _update_inflation(self):
        """Update inflation based on economic factors"""
        # Simple inflation model
        current_supply = self.economic_indicators.get('gold_supply', 1000000)
        base_supply = 1000000

        if current_supply > base_supply:
            inflation_rate = (current_supply - base_supply) / base_supply * 0.1
            self.economic_indicators['inflation_rate'] = min(inflation_rate, 0.1)  # Cap at 10%

        await self.redis_client.hset(
            "economic_indicators",
            mapping={'inflation_rate': str(self.economic_indicators['inflation_rate'])}
        )

    async def _adjust_exchange_rates(self):
        """Adjust currency exchange rates based on supply and demand"""
        # Dynamic exchange rate adjustment
        gold_supply = self.economic_indicators.get('gold_supply', 1000000)
        gem_supply = self.economic_indicators.get('gem_supply', 100000)

        base_gem_to_gold = 100
        current_gem_to_gold = int((gem_supply / gold_supply) * base_gem_to_gold * 1000)

        # Update exchange rates in currency definitions
        gold_currency = self.currencies.get('gold')
        if gold_currency:
            gold_currency.exchange_rate['gems'] = 1 / current_gem_to_gold

    async def _update_market_activity(self):
        """Update market activity indicators"""
        active_listings = await self.redis_client.llen("market_listings")
        total_transactions = int(await self.redis_client.get("total_transactions") or 0)

        # Calculate activity score
        activity_score = min(100, (active_listings * 2 + total_transactions * 0.1))
        self.economic_indicators['market_activity'] = activity_score

        await self.redis_client.hset(
            "economic_indicators",
            mapping={'market_activity': str(activity_score)}
        )

    async def _market_cleanup(self):
        """Background task to clean up expired listings"""
        while True:
            try:
                logger.info("Running market cleanup...")

                # Get all listing IDs
                listing_ids = await self.redis_client.lrange("market_listings", 0, -1)

                expired_listings = []
                for listing_id_bytes in listing_ids:
                    listing_id = listing_id_bytes.decode()
                    listing_data = await self.redis_client.get(f"listing:{listing_id}")

                    if listing_data:
                        listing_info = json.loads(listing_data)

                        if listing_info['expires_at']:
                            expires_at = datetime.fromisoformat(listing_info['expires_at'])
                            if datetime.utcnow() > expires_at and listing_info['status'] == 'active':
                                # Return items to seller
                                seller_id = listing_info['seller_id']
                                item_id = listing_info['item_id']
                                quantity = listing_info['quantity']

                                await self.add_item(seller_id, item_id, quantity, "listing_expired")

                                # Mark as expired
                                listing_info['status'] = 'expired'
                                await self.redis_client.setex(
                                    f"listing:{listing_id}",
                                    86400,
                                    json.dumps(listing_info)
                                )

                                expired_listings.append(listing_id)

                logger.info(f"Cleaned up {len(expired_listings)} expired listings")

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in market cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _inflation_control(self):
        """Background task to control inflation through economic mechanisms"""
        while True:
            try:
                logger.info("Running inflation control...")

                # Check inflation rate
                inflation_rate = self.economic_indicators.get('inflation_rate', 0.02)

                if inflation_rate > 0.05:  # High inflation
                    # Implement deflationary measures
                    await self._implement_deflationary_measures()

                await asyncio.sleep(86400)  # Run daily

            except Exception as e:
                logger.error(f"Error in inflation control: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _implement_deflationary_measures(self):
        """Implement measures to reduce inflation"""
        # Create special currency sinks
        # This could include special events, limited-time items, etc.
        logger.info("Implementing deflationary measures")

        # Example: Create a limited-time special item that consumes currency
        special_item = {
            'id': 'inflation_sink_item',
            'name': 'Gold Sink Special',
            'cost': {'gold': 10000},
            'description': 'Limited-time item to help control inflation'
        }

        # Store special item
        await self.redis_client.setex(
            "special_item:inflation_sink",
            86400,  # 24 hours
            json.dumps(special_item)
        )

# Database models
class PlayerInventoryDB(Base):
    """Player inventory database model"""
    __tablename__ = 'player_inventories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String, nullable=False, unique=True)
    items = Column(JSON, nullable=False)
    currencies = Column(JSON, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class TransactionLogDB(Base):
    """Transaction log database model"""
    __tablename__ = 'transaction_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    item_or_currency = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class MarketListingDB(Base):
    """Market listing database model"""
    __tablename__ = 'market_listings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(String, nullable=False)
    buyer_id = Column(String)
    item_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    sold_at = Column(DateTime)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_economy'
        }

        economy = VirtualEconomy(config)
        await economy.initialize()

        # Add currency to player
        result = await economy.add_currency("player_123", CurrencyType.GOLD, 1000, "welcome_bonus")
        print(f"Added currency: {result}")

        # Purchase item
        result = await economy.purchase_item("player_123", "health_potion", 5)
        print(f"Purchase result: {result}")

        # Create market listing
        result = await economy.create_market_listing(
            "player_123", "iron_sword", 1, Decimal('150.00'), CurrencyType.GOLD
        )
        print(f"Market listing result: {result}")

        # Get economy stats
        stats = await economy.get_economy_stats()
        print(f"Economy stats: {stats}")

    asyncio.run(main())