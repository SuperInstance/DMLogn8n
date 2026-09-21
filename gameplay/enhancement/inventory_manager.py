#!/usr/bin/env python3
"""
Rich Inventory Management System for DMLogn8n
Provides deep item management, crafting, and customization
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"
    CURRENCY = "currency"
    TRINKET = "trinket"
    TOOL = "tool"
    SCROLL = "scroll"
    KEY = "key"

class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class ItemQuality(Enum):
    POOR = "poor"
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class CraftingCategory(Enum):
    BLACKSMITHING = "blacksmithing"
    ALCHEMY = "alchemy"
    ENCHANTING = "enchanting"
    COOKING = "cooking"
    TAILORING = "tailoring"
    JEWELCRAFTING = "jewelcrafting"
    ENGINEERING = "engineering"
    INSCRIPTION = "inscription"

@dataclass
class ItemStats:
    """Item statistics and properties"""
    damage: Optional[Tuple[int, int]] = None  # min, max
    defense: int = 0
    health: int = 0
    mana: int = 0
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0
    critical_chance: float = 0.0
    critical_damage: float = 0.0
    dodge_chance: float = 0.0
    accuracy: float = 0.0
    resistance_fire: float = 0.0
    resistance_ice: float = 0.0
    resistance_lightning: float = 0.0
    resistance_poison: float = 0.0

@dataclass
class ItemEffect:
    """Special effects for items"""
    name: str
    description: str
    trigger: str  # on_equip, on_hit, on_crit, on_use, passive
    chance: float = 1.0
    value: Any = None
    duration: Optional[int] = None

@dataclass
class Item:
    """Base item definition"""
    id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity
    quality: ItemQuality = ItemQuality.COMMON
    level_requirement: int = 1
    value: int = 0
    stack_size: int = 1
    consumable: bool = False
    tradeable: bool = True
    sellable: bool = True
    stats: ItemStats = field(default_factory=ItemStats)
    effects: List[ItemEffect] = field(default_factory=list)
    equipment_slot: Optional[str] = None
    durability: Optional[int] = None
    max_durability: Optional[int] = None
    crafting_materials: Dict[str, int] = field(default_factory=dict)

@dataclass
class ItemStack:
    """Stack of items in inventory"""
    item: Item
    quantity: int = 1
    durability: Optional[int] = None
    custom_name: Optional[str] = None
    enchantments: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InventorySlot:
    """Individual inventory slot"""
    item_stack: Optional[ItemStack] = None
    locked: bool = False
    slot_type: Optional[str] = None  # normal, special, quest

@dataclass
class CraftingRecipe:
    """Crafting recipe definition"""
    id: str
    name: str
    description: str
    category: CraftingCategory
    skill_requirement: int = 1
    materials: Dict[str, int] = field(default_factory=dict)
    result_item_id: str
    result_quantity: int = 1
    crafting_time: int = 5  # seconds
    success_chance: float = 1.0
    skill_xp_reward: int = 10
    quality_chance: Dict[ItemQuality, float] = field(default_factory=dict)

@dataclass
class Enchantment:
    """Enchantment definition"""
    id: str
    name: str
    description: str
    max_level: int = 5
    applicable_types: List[ItemType] = field(default_factory=list)
    required_materials: Dict[str, int] = field(default_factory=dict)
    skill_requirement: int = 1
    effects: List[ItemEffect] = field(default_factory=list)

class Inventory:
    """Character inventory management"""

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.slots: List[InventorySlot] = [InventorySlot() for _ in range(capacity)]
        self.equipped_items: Dict[str, Optional[ItemStack]] = {}
        self.currency: Dict[str, int] = defaultdict(int)
        self.quick_slots: List[Optional[ItemStack]] = [None] * 10
        self.custom_categories: Dict[str, List[int]] = defaultdict(list)

    def add_item(self, item: Item, quantity: int = 1, durability: Optional[int] = None) -> Tuple[bool, str]:
        """Add item to inventory"""
        if quantity <= 0:
            return False, "Invalid quantity"

        # Handle currency items
        if item.item_type == ItemType.CURRENCY:
            self.currency[item.id] += quantity
            return True, f"Added {quantity} {item.name}"

        # Check for stacking
        if item.stack_size > 1:
            existing_stack = self._find_stackable_slot(item)
            if existing_stack is not None:
                available_space = item.stack_size - existing_stack.quantity
                quantity_to_add = min(quantity, available_space)
                existing_stack.quantity += quantity_to_add
                quantity -= quantity_to_add

                if quantity <= 0:
                    return True, f"Added {quantity_to_add} {item.name} to existing stack"

        # Add new stacks
        added_count = 0
        while quantity > 0:
            empty_slot = self._find_empty_slot()
            if empty_slot is None:
                return False, f"Inventory full. Added {added_count} of {item_stack.item.name}"

            quantity_to_add = min(quantity, item.stack_size)
            item_stack = ItemStack(
                item=item,
                quantity=quantity_to_add,
                durability=durability or item.max_durability
            )

            self.slots[empty_slot].item_stack = item_stack
            quantity -= quantity_to_add
            added_count += quantity_to_add

        return True, f"Added {added_count} {item.name}"

    def remove_item(self, item_id: str, quantity: int = 1) -> Tuple[bool, str, Optional[ItemStack]]:
        """Remove item from inventory"""
        if quantity <= 0:
            return False, "Invalid quantity", None

        removed_quantity = 0
        removed_stack = None

        for slot in self.slots:
            if slot.item_stack and slot.item_stack.item.id == item_id:
                stack_quantity = slot.item_stack.quantity
                quantity_to_remove = min(quantity - removed_quantity, stack_quantity)

                if quantity_to_remove == stack_quantity:
                    # Remove entire stack
                    removed_stack = slot.item_stack
                    slot.item_stack = None
                else:
                    # Remove from stack
                    slot.item_stack.quantity -= quantity_to_remove
                    if removed_stack is None:
                        removed_stack = ItemStack(
                            item=slot.item_stack.item,
                            quantity=quantity_to_remove,
                            durability=slot.item_stack.durability,
                            custom_name=slot.item_stack.custom_name,
                            enchantments=slot.item_stack.enchantments.copy()
                        )

                removed_quantity += quantity_to_remove

                if removed_quantity >= quantity:
                    break

        if removed_quantity == 0:
            return False, f"No {item_id} found in inventory", None

        return True, f"Removed {removed_quantity} items", removed_stack

    def get_item_count(self, item_id: str) -> int:
        """Get total count of specific item"""
        count = 0
        for slot in self.slots:
            if slot.item_stack and slot.item_stack.item.id == item_id:
                count += slot.item_stack.quantity
        return count

    def _find_stackable_slot(self, item: Item) -> Optional[ItemStack]:
        """Find existing stack that can accept more of the item"""
        for slot in self.slots:
            if (slot.item_stack and
                slot.item_stack.item.id == item.id and
                slot.item_stack.quantity < item.stack_size and
                slot.item_stack.custom_name is None and
                not slot.item_stack.enchantments):
                return slot.item_stack
        return None

    def _find_empty_slot(self) -> Optional[int]:
        """Find first empty slot"""
        for i, slot in enumerate(self.slots):
            if slot.item_stack is None:
                return i
        return None

    def equip_item(self, slot_index: int, equipment_slot: str) -> Tuple[bool, str]:
        """Equip item from inventory slot"""
        if slot_index < 0 or slot_index >= len(self.slots):
            return False, "Invalid slot"

        slot = self.slots[slot_index]
        if not slot.item_stack:
            return False, "No item in slot"

        item = slot.item_stack.item
        if not item.equipment_slot:
            return False, "Item cannot be equipped"

        # Unequip current item if any
        if equipment_slot in self.equipped_items and self.equipped_items[equipment_slot]:
            unequipped = self.equipped_items[equipment_slot]
            self.add_item(unequipped.item, unequipped.quantity, unequipped.durability)

        # Equip new item
        self.equipped_items[equipment_slot] = slot.item_stack
        slot.item_stack = None

        return True, f"Equipped {item.name}"

    def unequip_item(self, equipment_slot: str) -> Tuple[bool, str]:
        """Unequip item to inventory"""
        if equipment_slot not in self.equipped_items:
            return False, "Invalid equipment slot"

        item_stack = self.equipped_items[equipment_slot]
        if not item_stack:
            return False, "No item equipped"

        success, message = self.add_item(item_stack.item, 1, item_stack.durability)
        if success:
            self.equipped_items[equipment_slot] = None
            return True, f"Unequipped {item_stack.item.name}"
        else:
            return False, f"Cannot unequip: {message}"

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get summary of inventory contents"""
        total_items = 0
        total_value = 0
        items_by_type = defaultdict(int)
        items_by_rarity = defaultdict(int)

        for slot in self.slots:
            if slot.item_stack:
                stack = slot.item_stack
                total_items += stack.quantity
                total_value += stack.item.value * stack.quantity
                items_by_type[stack.item.item_type.value] += stack.quantity
                items_by_rarity[stack.item.rarity.value] += stack.quantity

        return {
            "capacity": self.capacity,
            "used_slots": sum(1 for slot in self.slots if slot.item_stack),
            "total_items": total_items,
            "total_value": total_value,
            "currency": dict(self.currency),
            "items_by_type": dict(items_by_type),
            "items_by_rarity": dict(items_by_rarity),
            "equipped_items": {slot: stack.item.name if stack else None
                             for slot, stack in self.equipped_items.items()}
        }

class CraftingSystem:
    """Advanced crafting system"""

    def __init__(self):
        self.recipes: Dict[str, CraftingRecipe] = {}
        self.enchantments: Dict[str, Enchantment] = {}
        self.skill_levels: Dict[CraftingCategory, int] = defaultdict(int)
        self.skill_experience: Dict[CraftingCategory, int] = defaultdict(int)
        self.crafting_queue: List[Dict] = []
        self.discovered_recipes: Set[str] = set()
        self.analytics = CraftingAnalytics()

        self._initialize_default_recipes()
        self._initialize_default_enchantments()

    def _initialize_default_recipes(self):
        """Initialize default crafting recipes"""
        recipes = [
            CraftingRecipe(
                id="iron_sword",
                name="Iron Sword",
                description="A sturdy iron sword",
                category=CraftingCategory.BLACKSMITHING,
                skill_requirement=10,
                materials={"iron_ore": 3, "wood": 1},
                result_item_id="iron_sword",
                quality_chance={
                    ItemQuality.COMMON: 0.7,
                    ItemQuality.UNCOMMON: 0.25,
                    ItemQuality.RARE: 0.05
                }
            ),
            CraftingRecipe(
                id="health_potion",
                name="Health Potion",
                description="Restores health when consumed",
                category=CraftingCategory.ALCHEMY,
                skill_requirement=5,
                materials={"herb": 2, "water": 1},
                result_item_id="health_potion",
                result_quantity=3,
                quality_chance={
                    ItemQuality.COMMON: 0.8,
                    ItemQuality.UNCOMMON: 0.2
                }
            ),
            CraftingRecipe(
                id="leather_armor",
                name="Leather Armor",
                description="Basic leather armor",
                category=CraftingCategory.TAILORING,
                skill_requirement=8,
                materials={"leather": 5, "thread": 2},
                result_item_id="leather_armor",
                quality_chance={
                    ItemQuality.COMMON: 0.75,
                    ItemQuality.UNCOMMON: 0.2,
                    ItemQuality.RARE: 0.05
                }
            )
        ]

        for recipe in recipes:
            self.recipes[recipe.id] = recipe

    def _initialize_default_enchantments(self):
        """Initialize default enchantments"""
        enchantments = [
            Enchantment(
                id="sharpness",
                name="Sharpness",
                description="Increases weapon damage",
                max_level=5,
                applicable_types=[ItemType.WEAPON],
                required_materials={"magic_dust": 1, "iron": 1},
                skill_requirement=15,
                effects=[ItemEffect("damage_boost", "+5 damage per level", "on_hit")]
            ),
            Enchantment(
                id="protection",
                name="Protection",
                description="Increases armor defense",
                max_level=5,
                applicable_types=[ItemType.ARMOR],
                required_materials={"magic_dust": 1, "leather": 1},
                skill_requirement=12,
                effects=[ItemEffect("defense_boost", "+3 defense per level", "passive")]
            )
        ]

        for enchantment in enchantments:
            self.enchantments[enchantment.id] = enchantment

    def craft_item(self, recipe_id: str, character_inventory: Inventory, quantity: int = 1) -> Tuple[bool, str, Optional[Item]]:
        """Craft an item using a recipe"""
        if recipe_id not in self.recipes:
            return False, "Recipe not found", None

        recipe = self.recipes[recipe_id]

        # Check skill requirement
        if self.skill_levels[recipe.category] < recipe.skill_requirement:
            return False, f"Insufficient {recipe.category.value} skill", None

        # Check materials
        for material_id, required_qty in recipe.materials.items():
            if character_inventory.get_item_count(material_id) < required_qty * quantity:
                return False, f"Insufficient materials: need {material_id}", None

        # Consume materials
        for material_id, required_qty in recipe.materials.items():
            character_inventory.remove_item(material_id, required_qty * quantity)

        # Determine quality
        quality = self._determine_crafting_quality(recipe)

        # Create crafted item
        crafted_item = self._create_crafted_item(recipe, quality)

        # Award skill experience
        xp_reward = recipe.skill_xp_reward * quantity
        self.add_skill_experience(recipe.category, xp_reward)

        # Add to inventory
        character_inventory.add_item(crafted_item, quantity)

        self.analytics.record_crafting(recipe_id, quantity, quality.value)

        return True, f"Successfully crafted {quantity}x {crafted_item.name}", crafted_item

    def _determine_crafting_quality(self, recipe: CraftingRecipe) -> ItemQuality:
        """Determine quality of crafted item based on skill and chance"""
        skill_level = self.skill_levels[recipe.category]
        base_chance = random.random()

        # Skill increases chance of better quality
        skill_bonus = min(skill_level / 100, 0.5)
        modified_chance = base_chance + skill_bonus

        cumulative_chance = 0.0
        for quality, chance in recipe.quality_chance.items():
            cumulative_chance += chance
            if modified_chance <= cumulative_chance:
                return quality

        return ItemQuality.COMMON

    def _create_crafted_item(self, recipe: CraftingRecipe, quality: ItemQuality) -> Item:
        """Create item with quality modifications"""
        # This would create the actual item based on recipe
        # For now, return a placeholder
        return Item(
            id=recipe.result_item_id,
            name=f"{quality.value.title()} {recipe.name}",
            description=recipe.description,
            item_type=ItemType.WEAPON,  # Placeholder
            rarity=ItemRarity.COMMON,   # Would be determined by quality
            quality=quality
        )

    def enchant_item(self, item_stack: ItemStack, enchantment_id: str, level: int = 1) -> Tuple[bool, str]:
        """Enchant an item"""
        if enchantment_id not in self.enchantments:
            return False, "Enchantment not found"

        enchantment = self.enchantments[enchantment_id]

        # Check if enchantment is applicable
        if item_stack.item.item_type not in enchantment.applicable_types:
            return False, "Enchantment not applicable to this item type"

        # Check level
        if level > enchantment.max_level:
            return False, f"Enchantment level exceeds maximum of {enchantment.max_level}"

        # Check if already enchanted
        if enchantment_id in [e.split('_')[0] for e in item_stack.enchantments]:
            return False, "Item already has this enchantment"

        # Check skill requirement
        if self.skill_levels[CraftingCategory.ENCHANTING] < enchantment.skill_requirement:
            return False, "Insufficient enchanting skill"

        # Apply enchantment
        enchantment_key = f"{enchantment_id}_{level}"
        item_stack.enchantments.append(enchantment_key)

        self.analytics.record_enchantment(enchantment_id, level)

        return True, f"Successfully enchanted with {enchantment.name} level {level}"

    def add_skill_experience(self, category: CraftingCategory, experience: int):
        """Add experience to crafting skill"""
        self.skill_experience[category] += experience

        # Check for level up
        current_level = self.skill_levels[category]
        required_xp = self.calculate_skill_xp_requirement(current_level + 1)

        if self.skill_experience[category] >= required_xp:
            self.skill_levels[category] += 1
            self.skill_experience[category] -= required_xp
            self.analytics.record_skill_level_up(category.value, self.skill_levels[category])

    def calculate_skill_xp_requirement(self, level: int) -> int:
        """Calculate XP required for crafting skill level"""
        return int(100 * math.pow(1.5, level - 1))

    def discover_recipe(self, recipe_id: str) -> bool:
        """Discover a new recipe"""
        if recipe_id in self.recipes and recipe_id not in self.discovered_recipes:
            self.discovered_recipes.add(recipe_id)
            self.analytics.record_recipe_discovery(recipe_id)
            return True
        return False

    def get_available_recipes(self) -> List[CraftingRecipe]:
        """Get list of discovered recipes that can be crafted"""
        available = []
        for recipe_id in self.discovered_recipes:
            if recipe_id in self.recipes:
                recipe = self.recipes[recipe_id]
                if self.skill_levels[recipe.category] >= recipe.skill_requirement:
                    available.append(recipe)
        return available

class ItemDatabase:
    """Database of all items in the game"""

    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.item_sets: Dict[str, Dict[str, Any]] = {}
        self.item_families: Dict[str, List[str]] = defaultdict(list)

        self._initialize_default_items()

    def _initialize_default_items(self):
        """Initialize default items"""
        default_items = [
            Item(
                id="iron_sword",
                name="Iron Sword",
                description="A well-crafted iron sword",
                item_type=ItemType.WEAPON,
                rarity=ItemRarity.COMMON,
                level_requirement=5,
                value=50,
                stats=ItemStats(damage=(8, 12), strength=2),
                equipment_slot="weapon",
                durability=100,
                max_durability=100
            ),
            Item(
                id="health_potion",
                name="Health Potion",
                description="Restores 50 health points",
                item_type=ItemType.CONSUMABLE,
                rarity=ItemRarity.COMMON,
                value=10,
                stack_size=20,
                consumable=True,
                stats=ItemStats(health=50)
            ),
            Item(
                id="iron_ore",
                name="Iron Ore",
                description="Raw iron ore used for crafting",
                item_type=ItemType.MATERIAL,
                rarity=ItemRarity.COMMON,
                value=5,
                stack_size=99
            ),
            Item(
                id="gold_coin",
                name="Gold Coin",
                description="Standard currency",
                item_type=ItemType.CURRENCY,
                rarity=ItemRarity.COMMON,
                value=1,
                stack_size=99999
            )
        ]

        for item in default_items:
            self.items[item.id] = item

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item by ID"""
        return self.items.get(item_id)

    def add_item(self, item: Item):
        """Add new item to database"""
        self.items[item.id] = item

    def get_items_by_type(self, item_type: ItemType) -> List[Item]:
        """Get all items of specific type"""
        return [item for item in self.items.values() if item.item_type == item_type]

    def get_items_by_rarity(self, rarity: ItemRarity) -> List[Item]:
        """Get all items of specific rarity"""
        return [item for item in self.items.values() if item.rarity == rarity]

class CraftingAnalytics:
    """Analytics for crafting system balance"""

    def __init__(self):
        self.crafting_history = []
        self.enchantment_history = []
        self.skill_progression = defaultdict(list)
        self.popularity_tracking = defaultdict(int)
        self.quality_distribution = defaultdict(int)

    def record_crafting(self, recipe_id: str, quantity: int, quality: str):
        """Record crafting activity"""
        self.crafting_history.append({
            "recipe_id": recipe_id,
            "quantity": quantity,
            "quality": quality,
            "timestamp": time.time()
        })
        self.popularity_tracking[recipe_id] += quantity
        self.quality_distribution[quality] += quantity

    def record_enchantment(self, enchantment_id: str, level: int):
        """Record enchantment activity"""
        self.enchantment_history.append({
            "enchantment_id": enchantment_id,
            "level": level,
            "timestamp": time.time()
        })
        self.popularity_tracking[f"enchant_{enchantment_id}"] += 1

    def record_skill_level_up(self, category: str, level: int):
        """Record skill progression"""
        self.skill_progression[category].append({
            "level": level,
            "timestamp": time.time()
        })

    def record_recipe_discovery(self, recipe_id: str):
        """Record recipe discovery"""
        self.popularity_tracking[f"discover_{recipe_id}"] += 1

    def get_crafting_summary(self) -> Dict[str, Any]:
        """Get crafting analytics summary"""
        total_crafts = sum(entry["quantity"] for entry in self.crafting_history)
        total_enchantments = len(self.enchantment_history)

        return {
            "total_crafts": total_crafts,
            "total_enchantments": total_enchantments,
            "most_crafted_items": sorted(self.popularity_tracking.items(),
                                       key=lambda x: x[1], reverse=True)[:10],
            "quality_distribution": dict(self.quality_distribution),
            "skill_levels": {cat: history[-1]["level"] if history else 0
                           for cat, history in self.skill_progression.items()}
        }

# Utility functions for inventory management
def calculate_inventory_value(inventory: Inventory, item_db: ItemDatabase) -> int:
    """Calculate total value of inventory"""
    total_value = sum(inventory.currency.values())

    for slot in inventory.slots:
        if slot.item_stack:
            item_value = slot.item_stack.item.value * slot.item_stack.quantity
            total_value += item_value

    # Add value of equipped items
    for item_stack in inventory.equipped_items.values():
        if item_stack:
            total_value += item_stack.item.value

    return total_value

def optimize_inventory_layout(inventory: Inventory) -> List[str]:
    """Suggest inventory organization improvements"""
    suggestions = []

    # Check for empty slots between items
    empty_slots = [i for i, slot in enumerate(inventory.slots) if not slot.item_stack]
    if len(empty_slots) > 10:
        suggestions.append("Consider consolidating items to reduce empty slots")

    # Check for overstocked items
    item_counts = defaultdict(int)
    for slot in inventory.slots:
        if slot.item_stack:
            item_counts[slot.item_stack.item.id] += slot.item_stack.quantity

    for item_id, count in item_counts.items():
        if count > 100:
            suggestions.append(f"Consider selling excess {item_id} (have {count})")

    return suggestions

# Export main classes
__all__ = [
    'Inventory',
    'Item',
    'ItemStack',
    'ItemDatabase',
    'CraftingSystem',
    'CraftingRecipe',
    'Enchantment',
    'CraftingAnalytics',
    'calculate_inventory_value',
    'optimize_inventory_layout'
]