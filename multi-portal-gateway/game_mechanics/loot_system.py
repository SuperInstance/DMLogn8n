"""
Intelligent Loot and Itemization System for DMLogn8n
Creates contextually appropriate rewards with smart generation algorithms
"""

import random
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class ItemType(Enum):
    """Types of items that can be generated"""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST_ITEM = "quest_item"
    CURRENCY = "currency"
    SCROLL = "scroll"
    POTION = "potion"
    FOOD = "food"
    TOOL = "tool"
    KEY = "key"
    BOOK = "book"
    ARTIFACT = "artifact"
    JEWELRY = "jewelry"

class ItemRarity(Enum):
    """Item rarity levels affecting generation and properties"""
    POOR = 0
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    MYTHIC = 6
    UNIQUE = 7

class Quality(Enum):
    """Quality levels affecting item stats"""
    DAMAGED = -1
    POOR = 0
    NORMAL = 1
    FINE = 2
    SUPERIOR = 3
    EXCEPTIONAL = 4
    MASTERWORK = 5
    FLAWLESS = 6

class ItemSlot(Enum):
    """Equipment slots for items"""
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    FEET = "feet"
    NECK = "neck"
    RING = "ring"
    TRINKET = "trinket"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    TWO_HAND = "two_hand"
    RANGED = "ranged"
    AMMO = "ammo"
    BACKPACK = "backpack"
    BELT = "belt"

class WeaponType(Enum):
    """Types of weapons"""
    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"
    DAGGER = "dagger"
    SPEAR = "spear"
    STAFF = "staff"
    WAND = "wand"
    BOW = "bow"
    CROSSBOW = "crossbow"
    SLING = "sling"
    CLAW = "claw"
    WHIP = "whip"
    POLEARM = "polearm"
    THROWN = "thrown"

class ArmorType(Enum):
    """Types of armor"""
    CLOTH = "cloth"
    LEATHER = "leather"
    CHAIN = "chain"
    PLATE = "plate"
    ROBES = "robes"
    LIGHT_ARMOR = "light_armor"
    MEDIUM_ARMOR = "medium_armor"
    HEAVY_ARMOR = "heavy_armor"
    SHIELD = "shield"

class StatType(Enum):
    """Types of stats items can have"""
    HEALTH = "health"
    MANA = "mana"
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"
    CONSTITUTION = "constitution"
    ATTACK_POWER = "attack_power"
    SPELL_POWER = "spell_power"
    ARMOR = "armor"
    RESISTANCE = "resistance"
    CRIT_CHANCE = "crit_chance"
    CRIT_DAMAGE = "crit_damage"
    HASTE = "haste"
    DODGE = "dodge"
    PARRY = "parry"
    BLOCK = "block"
    LIFE_STEAL = "life_steal"
    MANA_STEAL = "mana_steal"
    ACCURACY = "accuracy"

class AffixType(Enum):
    """Types of magical affixes"""
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    DARK = "dark"
    ARCANE = "arcane"
    NATURE = "nature"
    SHADOW = "shadow"
    BLOOD = "blood"
    STORM = "storm"
    EARTH = "earth"

@dataclass
class ItemStat:
    """Individual stat on an item"""
    stat_type: StatType
    value: float
    scaling: Optional[str] = None  # What this stat scales with
    requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ItemAffix:
    """Magical affix on an item"""
    affix_type: AffixType
    tier: int  # 1-5, higher is better
    value: float
    description: str

@dataclass
class ItemSet:
    """Set of items with bonus effects"""
    id: str
    name: str
    description: str
    item_ids: List[str]
    bonuses: Dict[int, List[ItemStat]]  # pieces_needed -> stats

@dataclass
class Item:
    """Complete item definition"""
    id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity
    quality: Quality
    level: int

    # Equipment properties
    slot: Optional[ItemSlot] = None
    weapon_type: Optional[WeaponType] = None
    armor_type: Optional[ArmorType] = None
    damage_range: Optional[Tuple[float, float]] = None
    armor_value: float = 0
    durability: int = 100
    max_durability: int = 100

    # Stats and properties
    base_stats: List[ItemStat] = field(default_factory=list)
    affixes: List[ItemAffix] = field(default_factory=list)
    set_id: Optional[str] = None

    # Requirements
    level_requirement: int = 1
    skill_requirements: Dict[str, int] = field(default_factory=dict)
    attribute_requirements: Dict[StatType, int] = field(default_factory=dict)
    class_requirements: List[str] = field(default_factory=list)
    faction_requirements: Dict[str, int] = field(default_factory=dict)

    # Economic properties
    base_value: int = 0
    sell_price: int = 0
    buy_price: int = 0
    stackable: bool = False
    max_stack: int = 1
    consumable: bool = False
    unique: bool = False

    # Special properties
    cursed: bool = False
    soulbound: bool = False
    account_bound: bool = False
    tradeable: bool = True
    sellable: bool = True
    droppable: bool = True

    # Lore and flavor
    lore: str = ""
    flavor_text: str = ""
    origin: str = ""
    creator: Optional[str] = None

    # Dynamic properties
    identified: bool = True
    enchantable: bool = True
    sockets: int = 0
    socketed_items: List[str] = field(default_factory=list)
    custom_enchantments: List[str] = field(default_factory=list)

    def get_total_stat(self, stat_type: StatType) -> float:
        """Get total value of a specific stat"""
        total = 0.0
        for stat in self.base_stats:
            if stat.stat_type == stat_type:
                total += stat.value

        for affix in self.affixes:
            # Add affix contributions to stats
            pass  # Would calculate affix stat contributions

        return total

    def meets_requirements(self, player_context: Dict[str, Any]) -> bool:
        """Check if player meets item requirements"""
        # Level requirement
        player_level = player_context.get("level", 1)
        if player_level < self.level_requirement:
            return False

        # Attribute requirements
        player_attributes = player_context.get("attributes", {})
        for attr, required_value in self.attribute_requirements.items():
            player_value = player_attributes.get(attr.value, 0)
            if player_value < required_value:
                return False

        # Class requirements
        player_class = player_context.get("class", "")
        if self.class_requirements and player_class not in self.class_requirements:
            return False

        # Skill requirements
        player_skills = player_context.get("skills", {})
        for skill, required_level in self.skill_requirements.items():
            player_skill_level = player_skills.get(skill, 0)
            if player_skill_level < required_level:
                return False

        # Faction requirements
        player_factions = player_context.get("factions", {})
        for faction, required_rep in self.faction_requirements.items():
            player_rep = player_factions.get(faction, 0)
            if player_rep < required_rep:
                return False

        return True

class LootTable:
    """Table for generating loot with weighted chances"""

    def __init__(self, name: str):
        self.name = name
        self.entries: List[Dict[str, Any]] = []
        self.rolls: int = 1
        self.unique_items: bool = False
        self.conditions: Dict[str, Any] = {}

    def add_entry(self, item_id: str, weight: float, quantity_range: Tuple[int, int] = (1, 1),
                  conditions: Optional[Dict[str, Any]] = None):
        """Add entry to loot table"""
        entry = {
            "item_id": item_id,
            "weight": weight,
            "quantity_range": quantity_range,
            "conditions": conditions or {}
        }
        self.entries.append(entry)

    def generate_loot(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate loot from this table"""
        loot = []

        for _ in range(self.rolls):
            if not self.entries:
                continue

            # Filter entries by conditions
            valid_entries = []
            for entry in self.entries:
                if self._check_conditions(entry["conditions"], context):
                    valid_entries.append(entry)

            if not valid_entries:
                continue

            # Select entry by weight
            total_weight = sum(entry["weight"] for entry in valid_entries)
            if total_weight <= 0:
                continue

            rand = random.random() * total_weight
            cumulative = 0
            selected_entry = valid_entries[0]

            for entry in valid_entries:
                cumulative += entry["weight"]
                if rand <= cumulative:
                    selected_entry = entry
                    break

            # Generate quantity
            min_qty, max_qty = selected_entry["quantity_range"]
            quantity = random.randint(min_qty, max_qty)

            loot.append({
                "item_id": selected_entry["item_id"],
                "quantity": quantity,
                "source": self.name
            })

        return loot

    def _check_conditions(self, conditions: Dict[str, Any],
                         context: Dict[str, Any]) -> bool:
        """Check if conditions are met"""
        for key, value in conditions.items():
            if key not in context:
                return False

            if isinstance(value, (list, tuple)):
                if context[key] not in value:
                    return False
            elif isinstance(value, dict):
                if "min" in value and context[key] < value["min"]:
                    return False
                if "max" in value and context[key] > value["max"]:
                    return False
            else:
                if context[key] != value:
                    return False

        return True

class LootGenerator:
    """Generates intelligent loot based on context"""

    def __init__(self):
        self.item_templates = self._load_item_templates()
        self.affix_templates = self._load_affix_templates()
        self.set_templates = self._load_set_templates()
        self.loot_tables: Dict[str, LootTable] = {}
        self.rarity_weights = self._calculate_rarity_weights()

    def _load_item_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load item generation templates"""
        return {
            # Weapon templates
            "iron_sword": {
                "name": "Iron Sword",
                "item_type": ItemType.WEAPON,
                "weapon_type": WeaponType.SWORD,
                "slot": ItemSlot.MAIN_HAND,
                "damage_range": (15, 25),
                "base_stats": [{"stat_type": StatType.ATTACK_POWER, "value": 10}],
                "level_range": (5, 15),
                "rarity_weights": {ItemRarity.COMMON: 0.7, ItemRarity.UNCOMMON: 0.3}
            },
            "steel_axe": {
                "name": "Steel Axe",
                "item_type": ItemType.WEAPON,
                "weapon_type": WeaponType.AXE,
                "slot": ItemSlot.MAIN_HAND,
                "damage_range": (20, 35),
                "base_stats": [{"stat_type": StatType.ATTACK_POWER, "value": 15}],
                "level_range": (10, 20),
                "rarity_weights": {ItemRarity.COMMON: 0.6, ItemRarity.UNCOMMON: 0.4}
            },
            "magic_staff": {
                "name": "Magic Staff",
                "item_type": ItemType.WEAPON,
                "weapon_type": WeaponType.STAFF,
                "slot": ItemSlot.MAIN_HAND,
                "damage_range": (10, 20),
                "base_stats": [{"stat_type": StatType.SPELL_POWER, "value": 12}],
                "level_range": (8, 18),
                "rarity_weights": {ItemRarity.UNCOMMON: 0.6, ItemRarity.RARE: 0.3, ItemRarity.EPIC: 0.1}
            },
            "hunter_bow": {
                "name": "Hunter Bow",
                "item_type": ItemType.WEAPON,
                "weapon_type": WeaponType.BOW,
                "slot": ItemSlot.RANGED,
                "damage_range": (18, 30),
                "base_stats": [{"stat_type": StatType.ATTACK_POWER, "value": 14}],
                "level_range": (12, 22),
                "rarity_weights": {ItemRarity.COMMON: 0.5, ItemRarity.UNCOMMON: 0.4, ItemRarity.RARE: 0.1}
            },

            # Armor templates
            "leather_armor": {
                "name": "Leather Armor",
                "item_type": ItemType.ARMOR,
                "armor_type": ArmorType.LEATHER,
                "slot": ItemSlot.CHEST,
                "armor_value": 15,
                "base_stats": [{"stat_type": StatType.ARMOR, "value": 15}],
                "level_range": (3, 10),
                "rarity_weights": {ItemRarity.POOR: 0.2, ItemRarity.COMMON: 0.6, ItemRarity.UNCOMMON: 0.2}
            },
            "chain_mail": {
                "name": "Chain Mail",
                "item_type": ItemType.ARMOR,
                "armor_type": ArmorType.CHAIN,
                "slot": ItemSlot.CHEST,
                "armor_value": 25,
                "base_stats": [{"stat_type": StatType.ARMOR, "value": 25}],
                "level_range": (8, 18),
                "rarity_weights": {ItemRarity.COMMON: 0.6, ItemRarity.UNCOMMON: 0.35, ItemRarity.RARE: 0.05}
            },
            "plate_armor": {
                "name": "Plate Armor",
                "item_type": ItemType.ARMOR,
                "armor_type": ArmorType.PLATE,
                "slot": ItemSlot.CHEST,
                "armor_value": 40,
                "base_stats": [{"stat_type": StatType.ARMOR, "value": 40}],
                "level_range": (15, 30),
                "rarity_weights": {ItemRarity.UNCOMMON: 0.4, ItemRarity.RARE: 0.4, ItemRarity.EPIC: 0.2}
            },
            "mage_robes": {
                "name": "Mage Robes",
                "item_type": ItemType.ARMOR,
                "armor_type": ArmorType.ROBES,
                "slot": ItemSlot.CHEST,
                "armor_value": 8,
                "base_stats": [
                    {"stat_type": StatType.ARMOR, "value": 8},
                    {"stat_type": StatType.SPELL_POWER, "value": 8}
                ],
                "level_range": (5, 15),
                "rarity_weights": {ItemRarity.COMMON: 0.5, ItemRarity.UNCOMMON: 0.35, ItemRarity.RARE: 0.15}
            },

            # Accessory templates
            "health_ring": {
                "name": "Ring of Health",
                "item_type": ItemType.ACCESSORY,
                "slot": ItemSlot.RING,
                "base_stats": [{"stat_type": StatType.HEALTH, "value": 20}],
                "level_range": (5, 15),
                "rarity_weights": {ItemRarity.UNCOMMON: 0.7, ItemRarity.RARE: 0.3}
            },
            "mana_amulet": {
                "name": "Amulet of Mana",
                "item_type": ItemType.ACCESSORY,
                "slot": ItemSlot.NECK,
                "base_stats": [{"stat_type": StatType.MANA, "value": 30}],
                "level_range": (8, 18),
                "rarity_weights": {ItemRarity.UNCOMMON: 0.6, ItemRarity.RARE: 0.35, ItemRarity.EPIC: 0.05}
            },

            # Consumable templates
            "health_potion": {
                "name": "Health Potion",
                "item_type": ItemType.CONSUMABLE,
                "consumable": True,
                "stackable": True,
                "max_stack": 20,
                "effect": {"heal": 50},
                "level_range": (1, 20),
                "rarity_weights": {ItemRarity.COMMON: 0.8, ItemRarity.UNCOMMON: 0.2}
            },
            "mana_potion": {
                "name": "Mana Potion",
                "item_type": ItemType.CONSUMABLE,
                "consumable": True,
                "stackable": True,
                "max_stack": 20,
                "effect": {"restore_mana": 40},
                "level_range": (1, 20),
                "rarity_weights": {ItemRarity.COMMON: 0.8, ItemRarity.UNCOMMON: 0.2}
            },

            # Material templates
            "iron_ore": {
                "name": "Iron Ore",
                "item_type": ItemType.MATERIAL,
                "stackable": True,
                "max_stack": 100,
                "crafting_uses": ["weapon_smithing", "armor_smithing"],
                "level_range": (1, 10),
                "rarity_weights": {ItemRarity.COMMON: 1.0}
            },
            "herbs": {
                "name": "Healing Herbs",
                "item_type": ItemType.MATERIAL,
                "stackable": True,
                "max_stack": 50,
                "crafting_uses": ["alchemy", "potion_making"],
                "level_range": (1, 15),
                "rarity_weights": {ItemRarity.COMMON: 0.7, ItemRarity.UNCOMMON: 0.3}
            }
        }

    def _load_affix_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load affix templates for magical properties"""
        return {
            "flaming": {
                "name": "Flaming",
                "affix_type": AffixType.FIRE,
                "description": "Adds fire damage",
                "stat_modifiers": [{"stat_type": StatType.ATTACK_POWER, "value": 5}],
                "requirements": {"level": 10}
            },
            "frost": {
                "name": "Frost",
                "affix_type": AffixType.ICE,
                "description": "Slows enemies and adds ice damage",
                "stat_modifiers": [{"stat_type": StatType.ATTACK_POWER, "value": 4}],
                "requirements": {"level": 12}
            },
            "lightning": {
                "name": "Lightning",
                "affix_type": AffixType.LIGHTNING,
                "description": "Chain lightning effect",
                "stat_modifiers": [{"stat_type": StatType.ATTACK_POWER, "value": 6}],
                "requirements": {"level": 15}
            },
            "vitality": {
                "name": "Vitality",
                "affix_type": AffixType.EARTH,
                "description": "Increases health",
                "stat_modifiers": [{"stat_type": StatType.HEALTH, "value": 25}],
                "requirements": {"level": 8}
            },
            "wisdom": {
                "name": "Wisdom",
                "affix_type": AffixType.ARCANE,
                "description": "Increases mana and spell power",
                "stat_modifiers": [
                    {"stat_type": StatType.MANA, "value": 20},
                    {"stat_type": StatType.SPELL_POWER, "value": 8}
                ],
                "requirements": {"level": 10}
            },
            "precision": {
                "name": "Precision",
                "affix_type": AffixType.ARCANE,
                "description": "Increases critical chance",
                "stat_modifiers": [{"stat_type": StatType.CRIT_CHANCE, "value": 3}],
                "requirements": {"level": 12}
            }
        }

    def _load_set_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load item set templates"""
        return {
            "iron_avenger_set": {
                "name": "Iron Avenger Set",
                "description": "A complete set of iron armor for warriors",
                "items": ["iron_helmet", "iron_chestplate", "iron_gauntlets", "iron_boots"],
                "bonuses": {
                    2: [{"stat_type": StatType.STRENGTH, "value": 5}],
                    3: [{"stat_type": StatType.ARMOR, "value": 10}],
                    4: [{"stat_type": StatType.STRENGTH, "value": 10},
                        {"stat_type": StatType.CONSTITUTION, "value": 5}]
                }
            },
            "mage_apprentice_set": {
                "name": "Mage Apprentice Set",
                "description": "Basic magical attire for aspiring mages",
                "items": ["apprentice_robes", "apprentice_hat", "apprentice_boots"],
                "bonuses": {
                    2: [{"stat_type": StatType.INTELLIGENCE, "value": 8}],
                    3: [{"stat_type": StatType.SPELL_POWER, "value": 15},
                        {"stat_type": StatType.MANA, "value": 30}]
                }
            }
        }

    def _calculate_rarity_weights(self) -> Dict[ItemRarity, float]:
        """Calculate base weights for rarity distribution"""
        return {
            ItemRarity.POOR: 0.05,
            ItemRarity.COMMON: 0.60,
            ItemRarity.UNCOMMON: 0.25,
            ItemRarity.RARE: 0.08,
            ItemRarity.EPIC: 0.015,
            ItemRarity.LEGENDARY: 0.004,
            ItemRarity.MYTHIC: 0.001,
            ItemRarity.UNIQUE: 0.000
        }

    def generate_item(self, template_name: str, level: int,
                     context: Optional[Dict[str, Any]] = None,
                     rarity_override: Optional[ItemRarity] = None) -> Optional[Item]:
        """Generate an item from template"""
        template = self.item_templates.get(template_name)
        if not template:
            return None

        context = context or {}

        # Determine rarity
        if rarity_override:
            rarity = rarity_override
        else:
            rarity = self._determine_rarity(template, level, context)

        # Determine quality
        quality = self._determine_quality(rarity, context)

        # Generate base item
        item = Item(
            id=str(uuid.uuid4()),
            name=template["name"],
            description=self._generate_description(template, rarity, quality),
            item_type=template["item_type"],
            rarity=rarity,
            quality=quality,
            level=level
        )

        # Copy template properties
        if "weapon_type" in template:
            item.weapon_type = template["weapon_type"]
        if "armor_type" in template:
            item.armor_type = template["armor_type"]
        if "slot" in template:
            item.slot = template["slot"]
        if "damage_range" in template:
            item.damage_range = template["damage_range"]
        if "armor_value" in template:
            item.armor_value = template["armor_value"]

        # Set consumable and stackable properties
        item.consumable = template.get("consumable", False)
        item.stackable = template.get("stackable", False)
        item.max_stack = template.get("max_stack", 1)

        # Generate base stats with scaling
        item.base_stats = self._generate_base_stats(template, level, rarity, quality)

        # Generate affixes for magical items
        if rarity.value >= ItemRarity.UNCOMMON.value:
            item.affixes = self._generate_affixes(template, rarity, level, context)

        # Set requirements
        item.level_requirement = max(1, level - random.randint(0, 3))
        self._generate_requirements(item, template, level, rarity)

        # Set economic values
        item.base_value = self._calculate_base_value(template, level, rarity)
        item.sell_price = int(item.base_value * 0.4)
        item.buy_price = int(item.base_value * 1.2)

        # Set durability
        if not item.consumable:
            max_durability = 100 + (level * 2) + (rarity.value * 20)
            item.max_durability = max_durability
            item.durability = random.randint(int(max_durability * 0.7), max_durability)

        # Set special properties
        item.soulbound = rarity.value >= ItemRarity.LEGENDARY.value
        item.unique = rarity == ItemRarity.UNIQUE

        # Generate lore and flavor
        item.flavor_text = self._generate_flavor_text(template, rarity, context)

        # Modify name based on rarity and affixes
        item.name = self._generate_item_name(item, template, rarity)

        return item

    def _determine_rarity(self, template: Dict[str, Any], level: int,
                         context: Dict[str, Any]) -> ItemRarity:
        """Determine item rarity based on template and context"""
        # Get template rarity weights
        template_weights = template.get("rarity_weights", self.rarity_weights)

        # Apply modifiers from context
        modifiers = 1.0
        if context.get("lucky", False):
            modifiers *= 2.0
        if context.get("boss_loot", False):
            modifiers *= 3.0
        if context.get("treasure_chest", False):
            modifiers *= 1.5

        # Apply level scaling
        level_modifier = 1.0 + (level / 100)

        # Calculate weights
        weights = {}
        for rarity, base_weight in template_weights.items():
            weight = base_weight * modifiers * level_modifier

            # Adjust weights for high rarities based on level
            if rarity.value >= ItemRarity.RARE.value and level < 20:
                weight *= 0.5
            elif rarity.value >= ItemRarity.EPIC.value and level < 40:
                weight *= 0.3
            elif rarity.value >= ItemRarity.LEGENDARY.value and level < 60:
                weight *= 0.1

            weights[rarity] = weight

        # Normalize weights
        total_weight = sum(weights.values())
        for rarity in weights:
            weights[rarity] /= total_weight

        # Select rarity
        rand = random.random()
        cumulative = 0
        for rarity, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return rarity

        return ItemRarity.COMMON

    def _determine_quality(self, rarity: ItemRarity,
                          context: Dict[str, Any]) -> Quality:
        """Determine item quality based on rarity"""
        quality_weights = {
            Quality.POOR: 0.05,
            Quality.NORMAL: 0.70,
            Quality.FINE: 0.20,
            Quality.SUPERIOR: 0.04,
            Quality.EXCEPTIONAL: 0.01
        }

        # Adjust weights based on rarity
        if rarity.value >= ItemRarity.RARE.value:
            quality_weights[Quality.POOR] = 0
            quality_weights[Quality.NORMAL] = 0.3
            quality_weights[Quality.FINE] = 0.4
            quality_weights[Quality.SUPERIOR] = 0.25
            quality_weights[Quality.EXCEPTIONAL] = 0.05

        if rarity.value >= ItemRarity.EPIC.value:
            quality_weights[Quality.NORMAL] = 0.1
            quality_weights[Quality.FINE] = 0.2
            quality_weights[Quality.SUPERIOR] = 0.5
            quality_weights[Quality.EXCEPTIONAL] = 0.2

        # Select quality
        rand = random.random()
        cumulative = 0
        for quality, weight in quality_weights.items():
            cumulative += weight
            if rand <= cumulative:
                return quality

        return Quality.NORMAL

    def _generate_base_stats(self, template: Dict[str, Any], level: int,
                            rarity: ItemRarity, quality: Quality) -> List[ItemStat]:
        """Generate base stats for item"""
        base_stats = []

        # Get template base stats
        template_stats = template.get("base_stats", [])

        for stat_template in template_stats:
            # Calculate base value
            base_value = stat_template["value"]

            # Apply level scaling
            level_scaling = 1.0 + (level / 20)

            # Apply rarity multiplier
            rarity_multiplier = 1.0 + (rarity.value * 0.2)

            # Apply quality multiplier
            quality_multipliers = {
                Quality.POOR: 0.7,
                Quality.NORMAL: 1.0,
                Quality.FINE: 1.2,
                Quality.SUPERIOR: 1.5,
                Quality.EXCEPTIONAL: 2.0
            }
            quality_multiplier = quality_multipliers.get(quality, 1.0)

            # Calculate final value
            final_value = base_value * level_scaling * rarity_multiplier * quality_multiplier
            final_value = max(1, int(final_value))

            stat = ItemStat(
                stat_type=stat_template["stat_type"],
                value=final_value,
                scaling=stat_template.get("scaling")
            )
            base_stats.append(stat)

        return base_stats

    def _generate_affixes(self, template: Dict[str, Any], rarity: ItemRarity,
                         level: int, context: Dict[str, Any]) -> List[ItemAffix]:
        """Generate magical affixes for item"""
        affixes = []

        # Determine number of affixes based on rarity
        affix_counts = {
            ItemRarity.POOR: 0,
            ItemRarity.COMMON: 0,
            ItemRarity.UNCOMMON: 1,
            ItemRarity.RARE: 2,
            ItemRarity.EPIC: 3,
            ItemRarity.LEGENDARY: 4,
            ItemRarity.MYTHIC: 5,
            ItemRarity.UNIQUE: 6
        }

        num_affixes = affix_counts.get(rarity, 0)
        if num_affixes == 0:
            return affixes

        # Select appropriate affixes
        available_affixes = list(self.affix_templates.values())

        # Filter affixes by item type and level
        suitable_affixes = []
        for affix_template in available_affixes:
            required_level = affix_template.get("requirements", {}).get("level", 1)
            if level >= required_level:
                suitable_affixes.append(affix_template)

        if not suitable_affixes:
            return affixes

        # Select affixes
        selected_affixes = random.sample(suitable_affixes,
                                        min(num_affixes, len(suitable_affixes)))

        for affix_template in selected_affixes:
            affix = ItemAffix(
                affix_type=affix_template["affix_type"],
                tier=min(5, 1 + level // 10),
                value=1.0,
                description=affix_template["description"]
            )
            affixes.append(affix)

        return affixes

    def _generate_requirements(self, item: Item, template: Dict[str, Any],
                              level: int, rarity: ItemRarity):
        """Generate item requirements"""
        # Level requirement
        item.level_requirement = max(1, level - random.randint(0, 3))

        # Attribute requirements based on item type
        if item.item_type == ItemType.WEAPON:
            if item.weapon_type in [WeaponType.SWORD, WeaponType.AXE, WeaponType.MACE]:
                item.attribute_requirements[StatType.STRENGTH] = max(10, level - 5)
            elif item.weapon_type in [WeaponType.DAGGER, WeaponType.BOW]:
                item.attribute_requirements[StatType.DEXTERITY] = max(10, level - 5)
            elif item.weapon_type in [WeaponType.STAFF, WeaponType.WAND]:
                item.attribute_requirements[StatType.INTELLIGENCE] = max(10, level - 5)

        elif item.item_type == ItemType.ARMOR:
            if item.armor_type in [ArmorType.CHAIN, ArmorType.PLATE]:
                item.attribute_requirements[StatType.STRENGTH] = max(15, level - 3)
            elif item.armor_type == ArmorType.LEATHER:
                item.attribute_requirements[StatType.DEXTERITY] = max(10, level - 5)
            elif item.armor_type == ArmorType.ROBES:
                item.attribute_requirements[StatType.INTELLIGENCE] = max(10, level - 5)

        # Skill requirements for higher rarity items
        if rarity.value >= ItemRarity.RARE.value:
            skill_requirements = {
                ItemType.WEAPON: "weapon_mastery",
                ItemType.ARMOR: "armor_mastery",
                ItemType.ACCESSORY: "magic_affinity"
            }
            skill = skill_requirements.get(item.item_type)
            if skill:
                item.skill_requirements[skill] = max(1, level // 5)

    def _calculate_base_value(self, template: Dict[str, Any], level: int,
                             rarity: ItemRarity) -> int:
        """Calculate base value of item"""
        base_value = 10

        # Apply level scaling
        level_modifier = 1.0 + (level / 10)

        # Apply rarity multiplier
        rarity_multipliers = {
            ItemRarity.POOR: 0.2,
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 2.5,
            ItemRarity.RARE: 8.0,
            ItemRarity.EPIC: 25.0,
            ItemRarity.LEGENDARY: 100.0,
            ItemRarity.MYTHIC: 500.0,
            ItemRarity.UNIQUE: 1000.0
        }

        rarity_multiplier = rarity_multipliers.get(rarity, 1.0)

        # Apply item type modifier
        type_multipliers = {
            ItemType.WEAPON: 1.5,
            ItemType.ARMOR: 1.3,
            ItemType.ACCESSORY: 1.8,
            ItemType.CONSUMABLE: 0.3,
            ItemType.MATERIAL: 0.5
        }

        type_multiplier = type_multipliers.get(template["item_type"], 1.0)

        # Calculate final value
        final_value = int(base_value * level_modifier * rarity_multiplier * type_multiplier)
        return max(1, final_value)

    def _generate_item_name(self, item: Item, template: Dict[str, Any],
                           rarity: ItemRarity) -> str:
        """Generate item name with prefixes/suffixes"""
        base_name = template["name"]

        if rarity.value >= ItemRarity.UNCOMMON.value and item.affixes:
            # Add affix prefix
            affix_names = [affix.description.split()[0] for affix in item.affixes[:2]]
            if affix_names:
                prefix = " ".join(affix_names)
                return f"{prefix} {base_name}"

        return base_name

    def _generate_description(self, template: Dict[str, Any], rarity: ItemRarity,
                             quality: Quality) -> str:
        """Generate item description"""
        base_desc = f"A {template['item_type'].value} of fine craftsmanship."

        if rarity.value >= ItemRarity.RARE.value:
            base_desc += f" This {rarity.value.lower()} item radiates magical energy."

        if quality == Quality.EXCEPTIONAL:
            base_desc += " Crafted with exceptional skill and attention to detail."

        return base_desc

    def _generate_flavor_text(self, template: Dict[str, Any], rarity: ItemRarity,
                             context: Dict[str, Any]) -> str:
        """Generate flavor text for item"""
        flavor_texts = {
            ItemType.WEAPON: [
                "Forged in the fires of Mount Doom.",
                "A warrior's trusted companion.",
                "Sharp enough to cut through steel.",
                "Once wielded by a legendary hero.",
                "Cold to the touch, warm in battle."
            ],
            ItemType.ARMOR: [
                "Forged by master smiths of old.",
                "Has seen countless battles.",
                "Offers protection beyond measure.",
                "Once belonged to a noble knight.",
                "Stronger than the mountains themselves."
            ],
            ItemType.ACCESSORY: [
                "Glows with an inner light.",
                "Humming with latent power.",
                "A gift from the gods themselves.",
                "Passed down through generations.",
                "Contains ancient wisdom within."
            ]
        }

        item_flavors = flavor_texts.get(template["item_type"], ["A mysterious item."])

        # Select more epic flavor text for higher rarity
        if rarity.value >= ItemRarity.EPIC.value:
            epic_flavors = [
                "An artifact of immense power.",
                "Legends speak of its might.",
                "Fate itself bends to its will.",
                "The stuff of myths and legends.",
                "Power beyond mortal comprehension."
            ]
            return random.choice(epic_flavors)

        return random.choice(item_flavors)

    def create_loot_table(self, name: str, entries: List[Dict[str, Any]],
                         rolls: int = 1, unique_items: bool = False) -> LootTable:
        """Create a custom loot table"""
        table = LootTable(name)
        table.rolls = rolls
        table.unique_items = unique_items

        for entry in entries:
            table.add_entry(**entry)

        self.loot_tables[name] = table
        return table

    def generate_loot_from_table(self, table_name: str,
                                 context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate loot from a predefined table"""
        table = self.loot_tables.get(table_name)
        if not table:
            return []

        return table.generate_loot(context)

    def generate_loot_for_context(self, context: Dict[str, Any]) -> List[Item]:
        """Generate intelligent loot based on context"""
        loot = []

        # Get context parameters
        level = context.get("level", 1)
        source_type = context.get("source_type", "generic")  # chest, enemy, boss, quest
        player_class = context.get("player_class", None)
        dungeon_type = context.get("dungeon_type", None)
        num_items = context.get("num_items", random.randint(1, 3))

        # Select appropriate item templates
        suitable_templates = self._select_templates_for_context(context)

        for _ in range(num_items):
            if not suitable_templates:
                continue

            # Select template
            template_name = random.choice(suitable_templates)

            # Generate item
            item = self.generate_item(template_name, level, context)
            if item:
                loot.append(item)

        return loot

    def _select_templates_for_context(self, context: Dict[str, Any]) -> List[str]:
        """Select appropriate item templates based on context"""
        all_templates = list(self.item_templates.keys())
        suitable_templates = []

        player_class = context.get("player_class")
        source_type = context.get("source_type")
        dungeon_type = context.get("dungeon_type")

        # Filter by player class
        if player_class:
            class_preferences = {
                "warrior": ["iron_sword", "steel_axe", "chain_mail", "plate_armor", "health_ring"],
                "mage": ["magic_staff", "mage_robes", "mana_amulet"],
                "ranger": ["hunter_bow", "leather_armor"],
                "rogue": ["iron_sword", "leather_armor"]
            }
            preferred = class_preferences.get(player_class, [])
            suitable_templates.extend([t for t in preferred if t in all_templates])

        # Filter by source type
        if source_type == "boss":
            # Higher chance for rare items
            boss_templates = [t for t in all_templates if "sword" in t or "armor" in t or "staff" in t]
            suitable_templates.extend(boss_templates)
        elif source_type == "chest":
            # Balanced selection
            suitable_templates.extend(all_templates)
        elif source_type == "enemy":
            # Common items mostly
            common_templates = [t for t in all_templates if "potion" in t or "ore" in t]
            suitable_templates.extend(common_templates)

        # If no specific templates found, use all
        if not suitable_templates:
            suitable_templates = all_templates

        return list(set(suitable_templates))

    def create_creature_loot_table(self, creature_type: str, level: int,
                                  difficulty: str = "normal") -> str:
        """Create loot table for creature type"""
        table_name = f"{creature_type}_loot_{level}"

        table = LootTable(table_name)
        table.rolls = random.randint(1, 3)

        # Add creature-specific loot
        if creature_type == "goblin":
            table.add_entry("health_potion", 0.3)
            table.add_entry("iron_ore", 0.2, (1, 3))
            table.add_entry("iron_sword", 0.1)
        elif creature_type == "orc":
            table.add_entry("health_potion", 0.2)
            table.add_entry("steel_axe", 0.15)
            table.add_entry("leather_armor", 0.1)
        elif creature_type == "skeleton":
            table.add_entry("mana_potion", 0.2)
            table.add_entry("magic_staff", 0.1)
            table.add_entry("herbs", 0.3, (1, 2))

        # Add currency
        gold_amount = level * random.randint(5, 20)
        table.add_entry("gold", 0.8, (gold_amount // 2, gold_amount))

        # Add quality bonus for difficulty
        if difficulty == "elite":
            table.rolls += 1
        elif difficulty == "boss":
            table.rolls += 2
            # Add rare item chance
            table.add_entry("health_potion", 0.1, conditions={"rarity": "rare"})

        self.loot_tables[table_name] = table
        return table_name

    def get_loot_statistics(self, items: List[Item]) -> Dict[str, Any]:
        """Get statistics about generated loot"""
        if not items:
            return {}

        # Count by type
        type_counts = {}
        for item in items:
            item_type = item.item_type.value
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        # Count by rarity
        rarity_counts = {}
        for item in items:
            rarity = item.rarity.value
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

        # Calculate total value
        total_value = sum(item.base_value for item in items)

        # Find most valuable
        most_valuable = max(items, key=lambda x: x.base_value) if items else None

        return {
            "total_items": len(items),
            "type_distribution": type_counts,
            "rarity_distribution": rarity_counts,
            "total_value": total_value,
            "average_value": total_value / len(items) if items else 0,
            "most_valuable": {
                "name": most_valuable.name,
                "value": most_valuable.base_value,
                "rarity": most_valuable.rarity.value
            } if most_valuable else None,
            "highest_level": max(item.level for item in items) if items else 0,
            "lowest_level": min(item.level for item in items) if items else 0
        }

# Example usage and testing
if __name__ == "__main__":
    # Create loot generator
    generator = LootGenerator()

    print("=== INTELLIGENT LOOT SYSTEM ===")
    print(f"Available Templates: {len(generator.item_templates)}")
    print(f"Available Affixes: {len(generator.affix_templates)}")
    print(f"Available Sets: {len(generator.set_templates)}")

    # Generate some items
    print(f"\n=== GENERATING SAMPLE ITEMS ===")

    # Generate items for different contexts
    contexts = [
        {
            "name": "Low Level Warrior",
            "level": 10,
            "player_class": "warrior",
            "source_type": "enemy"
        },
        {
            "name": "High Level Mage",
            "level": 50,
            "player_class": "mage",
            "source_type": "boss",
            "lucky": True
        },
        {
            "name": "Treasure Chest",
            "level": 25,
            "source_type": "treasure_chest",
            "num_items": 5
        },
        {
            "name": "Quest Reward",
            "level": 30,
            "source_type": "quest",
            "player_class": "ranger"
        }
    ]

    generated_items = []
    for context in contexts:
        print(f"\n--- {context['name']} (Level {context['level']}) ---")
        items = generator.generate_loot_for_context(context)
        generated_items.extend(items)

        for item in items:
            print(f"{item.name} ({item.rarity.value}, {item.quality.value})")
            print(f"  Level: {item.level_requirement}, Value: {item.base_value}g")
            print(f"  Type: {item.item_type.value}")
            if item.base_stats:
                stats = ", ".join([f"{stat.stat_type.value}: +{stat.value}" for stat in item.base_stats])
                print(f"  Stats: {stats}")
            if item.affixes:
                affixes = ", ".join([affix.description for affix in item.affixes])
                print(f"  Affixes: {affixes}")
            print(f"  Description: {item.description}")
            if item.flavor_text:
                print(f"  Flavor: \"{item.flavor_text}\"")

    # Generate specific items
    print(f"\n=== SPECIFIC ITEM GENERATION ===")

    # Generate a legendary sword
    legendary_sword = generator.generate_item(
        "steel_axe",
        level=60,
        context={"boss_loot": True, "lucky": True},
        rarity_override=ItemRarity.LEGENDARY
    )
    if legendary_sword:
        print(f"\nLegendary Sword: {legendary_sword.name}")
        print(f"  Rarity: {legendary_sword.rarity.value}")
        print(f"  Level: {legendary_sword.level_requirement}")
        print(f"  Value: {legendary_sword.base_value}g")
        print(f"  Stats: {[(stat.stat_type.value, stat.value) for stat in legendary_sword.base_stats]}")
        print(f"  Affixes: {[affix.description for affix in legendary_sword.affixes]}")

    # Create creature loot tables
    print(f"\n=== CREATURE LOOT TABLES ===")

    goblin_table = generator.create_creature_loot_table("goblin", 5)
    orc_table = generator.create_creature_loot_table("orc", 15, "elite")
    dragon_table = generator.create_creature_loot_table("dragon", 80, "boss")

    # Generate loot from tables
    goblin_loot = generator.generate_loot_from_table(goblin_table, {"level": 5})
    print(f"\nGoblin Loot ({len(goblin_loot)} items):")
    for loot_entry in goblin_loot:
        print(f"  {loot_entry['item_id']} x{loot_entry['quantity']}")

    # Generate statistics
    print(f"\n=== LOOT STATISTICS ===")
    stats = generator.get_loot_statistics(generated_items)
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    print(f"\n=== GENERATION COMPLETE ===")
    print(f"Generated {len(generated_items)} items across different contexts")
    print(f"Total value: {sum(item.base_value for item in generated_items)}g")