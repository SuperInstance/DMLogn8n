#!/usr/bin/env python3
"""
Test Data Generator
Generates realistic test data for load testing scenarios
"""

import random
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import logging
from faker import Faker
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CharacterData:
    """Character data for testing"""
    character_id: str
    name: str
    class_type: str
    race: str
    level: int
    experience: int
    health: int
    max_health: int
    mana: int
    max_mana: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    armor_class: int
    speed: int
    background: str
    alignment: str
    traits: List[str]
    equipment: List[Dict[str, Any]]
    inventory: List[Dict[str, Any]]
    skills: Dict[str, int]
    spells: List[str]

@dataclass
class CampaignData:
    """Campaign data for testing"""
    campaign_id: str
    name: str
    description: str
    dungeon_master: str
    level_range: tuple
    max_players: int
    current_players: int
    status: str
    setting: str
    theme: str
    difficulty: str
    sessions_completed: int
    total_sessions: int
    created_at: datetime
    last_session: Optional[datetime]
    tags: List[str]

@dataclass
class CombatData:
    """Combat encounter data for testing"""
    combat_id: str
    session_id: str
    participants: List[str]
    turn_order: List[str]
    current_turn: int
    round_number: int
    status: str
    environment: str
    weather: str
    lighting: str
    terrain_features: List[str]
    objectives: List[str]
    rewards: Dict[str, Any]
    started_at: datetime
    duration: int

@dataclass
class DialogueData:
    """Dialogue data for testing"""
    conversation_id: str
    session_id: str
    participants: List[str]
    topic: str
    context: Dict[str, Any]
    messages: List[Dict[str, Any]]
    relationship_changes: Dict[str, int]
    outcomes: List[str]
    started_at: datetime
    ended_at: Optional[datetime]

@dataclass
class QuestData:
    """Quest data for testing"""
    quest_id: str
    title: str
    description: str
    quest_giver: str
    objectives: List[Dict[str, Any]]
    rewards: Dict[str, Any]
    requirements: Dict[str, Any]
    difficulty: str
    estimated_duration: str
    location: str
    tags: List[str]
    status: str
    created_at: datetime
    deadline: Optional[datetime]

class TestDataGenerator:
    """Generates realistic test data for load testing"""

    def __init__(self, seed: Optional[int] = None):
        self.fake = Faker()
        if seed:
            random.seed(seed)
            np.random.seed(seed)
            Faker.seed(seed)

        # Data pools
        self.classes = ["fighter", "wizard", "rogue", "cleric", "ranger", "paladin", "barbarian", "monk", "bard", "druid", "warlock", "sorcerer"]
        self.races = ["human", "elf", "dwarf", "halfling", "gnome", "half-elf", "half-orc", "dragonborn", "tiefling"]
        self.backgrounds = ["soldier", "scholar", "merchant", "noble", "artisan", "farmer", "sailor", "criminal", "entertainer", "hermit"]
        self.alignments = ["lawful good", "neutral good", "chaotic good", "lawful neutral", "true neutral", "chaotic neutral", "lawful evil", "neutral evil", "chaotic evil"]
        self.skills = ["athletics", "acrobatics", "sleight of hand", "stealth", "arcana", "history", "investigation", "nature", "religion", "animal handling", "insight", "medicine", "perception", "survival", "deception", "intimidation", "performance", "persuasion"]
        self.spells = ["fireball", "magic missile", "cure wounds", "shield", "lightning bolt", "teleport", "invisibility", "fly", "haste", "slow", "dispel magic", "counterspell", "fire shield", "ice storm", "chain lightning"]
        self.equipment_types = ["weapon", "armor", "shield", "helmet", "boots", "gloves", "belt", "cloak", "ring", "amulet"]
        self.item_rarities = ["common", "uncommon", "rare", "very rare", "legendary"]

    def generate_character(self, level: Optional[int] = None, class_type: Optional[str] = None) -> CharacterData:
        """Generate a realistic character"""
        character_id = str(uuid.uuid4())

        if level is None:
            level = random.randint(1, 20)

        if class_type is None:
            class_type = random.choice(self.classes)

        race = random.choice(self.races)
        background = random.choice(self.backgrounds)
        alignment = random.choice(self.alignments)

        # Generate ability scores
        abilities = self._generate_ability_scores(race, class_type)

        # Calculate health based on class and level
        hit_dice = {
            "fighter": 10, "wizard": 6, "rogue": 8, "cleric": 8,
            "ranger": 10, "paladin": 10, "barbarian": 12, "monk": 8,
            "bard": 8, "druid": 8, "warlock": 8, "sorcerer": 6
        }.get(class_type, 8)

        max_health = hit_dice + abilities["constitution"] // 2 - 5 + (level - 1) * (hit_dice // 2 + 1)
        health = max_health

        # Calculate mana for magic users
        if class_type in ["wizard", "sorcerer", "warlock", "bard", "druid", "cleric", "paladin", "ranger"]:
            max_mana = 10 + (level * 2) + (abilities["intelligence"] // 2 if class_type in ["wizard", "sorcerer", "warlock", "bard"] else abilities["wisdom"] // 2)
        else:
            max_mana = 0

        mana = max_mana

        # Generate experience based on level
        experience = self._calculate_experience_for_level(level)

        # Generate equipment
        equipment = self._generate_equipment(class_type, level)
        inventory = self._generate_inventory(level)

        # Generate skills
        skills = self._generate_skills(abilities, background)

        # Generate spells for magic users
        spells = self._generate_spells(class_type, level)

        # Generate traits
        traits = self._generate_traits(background, race, class_type)

        return CharacterData(
            character_id=character_id,
            name=f"{race.title()} {self.fake.first_name()}",
            class_type=class_type,
            race=race,
            level=level,
            experience=experience,
            health=health,
            max_health=max_health,
            mana=mana,
            max_mana=max_mana,
            strength=abilities["strength"],
            dexterity=abilities["dexterity"],
            constitution=abilities["constitution"],
            intelligence=abilities["intelligence"],
            wisdom=abilities["wisdom"],
            charisma=abilities["charisma"],
            armor_class=10 + abilities["dexterity"] // 2 - 5 + (5 if "armor" in [eq["type"] for eq in equipment] else 0),
            speed=random.choice([25, 30, 35]),
            background=background,
            alignment=alignment,
            traits=traits,
            equipment=equipment,
            inventory=inventory,
            skills=skills,
            spells=spells
        )

    def _generate_ability_scores(self, race: str, class_type: str) -> Dict[str, int]:
        """Generate ability scores using point buy or standard array"""
        # Standard array method
        scores = [15, 14, 13, 12, 10, 8]
        random.shuffle(scores)

        abilities = {
            "strength": scores[0],
            "dexterity": scores[1],
            "constitution": scores[2],
            "intelligence": scores[3],
            "wisdom": scores[4],
            "charisma": scores[5]
        }

        # Apply racial bonuses
        racial_bonuses = {
            "human": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
            "elf": {"dexterity": 2, "wisdom": 1},
            "dwarf": {"constitution": 2, "strength": 1},
            "halfling": {"dexterity": 2, "charisma": 1},
            "gnome": {"intelligence": 2, "constitution": 1},
            "half-elf": {"charisma": 2, "dexterity": 1, "wisdom": 1},
            "half-orc": {"strength": 2, "constitution": 1},
            "dragonborn": {"strength": 2, "charisma": 1},
            "tiefling": {"charisma": 2, "intelligence": 1}
        }

        if race in racial_bonuses:
            for ability, bonus in racial_bonuses[race].items():
                abilities[ability] += bonus

        # Ensure scores are within valid range
        for ability in abilities:
            abilities[ability] = max(1, min(20, abilities[ability]))

        # Apply class-based adjustments
        class_priorities = {
            "fighter": ["strength", "constitution"],
            "wizard": ["intelligence", "constitution"],
            "rogue": ["dexterity", "intelligence"],
            "cleric": ["wisdom", "constitution"],
            "ranger": ["dexterity", "wisdom"],
            "paladin": ["strength", "charisma"],
            "barbarian": ["strength", "constitution"],
            "monk": ["dexterity", "wisdom"],
            "bard": ["charisma", "dexterity"],
            "druid": ["wisdom", "constitution"],
            "warlock": ["charisma", "constitution"],
            "sorcerer": ["charisma", "constitution"]
        }

        for priority in class_priorities.get(class_type, []):
            if abilities[priority] < 16:
                abilities[priority] = min(20, abilities[priority] + 2)

        return abilities

    def _calculate_experience_for_level(self, level: int) -> int:
        """Calculate experience needed for a given level"""
        # Simplified XP calculation
        xp_thresholds = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]
        if level <= 20:
            return xp_thresholds[level - 1] + random.randint(0, 1000)
        return xp_thresholds[-1]

    def _generate_equipment(self, class_type: str, level: int) -> List[Dict[str, Any]]:
        """Generate equipment for a character"""
        equipment = []

        # Weapons based on class
        if class_type in ["fighter", "paladin", "barbarian"]:
            weapon = {
                "id": str(uuid.uuid4()),
                "name": random.choice(["Longsword", "Greatsword", "Battleaxe", "Warhammer"]),
                "type": "weapon",
                "damage": f"{random.randint(1, 2)}d{random.choice([6, 8, 10, 12])}",
                "rarity": self._get_rarity_for_level(level),
                "value": random.randint(10, 1000) * level,
                "weight": random.randint(1, 10)
            }
            equipment.append(weapon)

        elif class_type in ["rogue", "ranger", "monk"]:
            weapon = {
                "id": str(uuid.uuid4()),
                "name": random.choice(["Shortsword", "Dagger", "Longbow", "Crossbow"]),
                "type": "weapon",
                "damage": f"{random.randint(1, 2)}d{random.choice([4, 6, 8])}",
                "rarity": self._get_rarity_for_level(level),
                "value": random.randint(5, 500) * level,
                "weight": random.randint(1, 5)
            }
            equipment.append(weapon)

        elif class_type in ["wizard", "sorcerer", "warlock", "bard", "druid", "cleric"]:
            weapon = {
                "id": str(uuid.uuid4()),
                "name": random.choice(["Staff", "Wand", "Dagger", "Mace"]),
                "type": "weapon",
                "damage": f"{random.randint(1, 4)}d{random.choice([4, 6])}",
                "rarity": self._get_rarity_for_level(level),
                "value": random.randint(10, 300) * level,
                "weight": random.randint(1, 8)
            }
            equipment.append(weapon)

        # Armor based on class
        if class_type in ["fighter", "paladin", "cleric"]:
            armor = {
                "id": str(uuid.uuid4()),
                "name": random.choice(["Chain Mail", "Plate Armor", "Scale Mail", "Breastplate"]),
                "type": "armor",
                "armor_class": random.randint(14, 18),
                "rarity": self._get_rarity_for_level(level),
                "value": random.randint(50, 2000) * level,
                "weight": random.randint(20, 65)
            }
            equipment.append(armor)

        elif class_type in ["rogue", "ranger", "bard"]:
            armor = {
                "id": str(uuid.uuid4()),
                "name": random.choice(["Leather Armor", "Studded Leather", "Hide Armor"]),
                "type": "armor",
                "armor_class": random.randint(11, 14),
                "rarity": self._get_rarity_for_level(level),
                "value": random.randint(10, 200) * level,
                "weight": random.randint(10, 25)
            }
            equipment.append(armor)

        # Add shield for some classes
        if class_type in ["fighter", "paladin", "cleric"] and random.random() < 0.7:
            shield = {
                "id": str(uuid.uuid4()),
                "name": "Shield",
                "type": "shield",
                "armor_class": 2,
                "rarity": "common",
                "value": random.randint(5, 50),
                "weight": random.randint(5, 10)
            }
            equipment.append(shield)

        return equipment

    def _generate_inventory(self, level: int) -> List[Dict[str, Any]]:
        """Generate inventory items"""
        inventory = []
        num_items = random.randint(5, 20)

        for _ in range(num_items):
            item_type = random.choice(["potion", "scroll", "food", "tool", "misc", "treasure"])

            item = {
                "id": str(uuid.uuid4()),
                "name": self._generate_item_name(item_type),
                "type": item_type,
                "quantity": random.randint(1, 10),
                "value": random.randint(1, 500) * (level // 5 + 1),
                "weight": random.uniform(0.1, 10.0),
                "description": self.fake.sentence()
            }

            if item_type == "potion":
                item["effect"] = random.choice(["healing", "mana restoration", "strength boost", "invisibility", "fire resistance"])
                item["duration"] = random.randint(1, 60)  # minutes

            elif item_type == "scroll":
                item["spell"] = random.choice(self.spells)
                item["level"] = random.randint(1, 9)

            inventory.append(item)

        return inventory

    def _generate_item_name(self, item_type: str) -> str:
        """Generate a realistic item name"""
        prefixes = ["Simple", "Fine", "Superior", "Masterwork", "Enchanted", "Ancient", "Mystic"]
        materials = ["Iron", "Steel", "Silver", "Gold", "Crystal", "Wooden", "Leather"]

        if item_type == "potion":
            return f"{random.choice(prefixes)} {random.choice(['Healing', 'Mana', 'Strength', 'Wisdom'])} Potion"
        elif item_type == "scroll":
            return f"Scroll of {random.choice(self.spells)}"
        elif item_type == "food":
            return random.choice(["Rations", "Dried Meat", "Bread", "Cheese", "Wine"])
        elif item_type == "tool":
            return f"{random.choice(materials)} {random.choice(['Hammer', 'Chisel', 'Pickaxe', 'Lockpick'])}"
        else:
            return f"{random.choice(prefixes)} {random.choice(materials)} {random.choice(['Ring', 'Amulet', 'Gem', 'Orb'])}"

    def _get_rarity_for_level(self, level: int) -> str:
        """Determine item rarity based on character level"""
        if level <= 5:
            return random.choice(["common", "uncommon"])
        elif level <= 10:
            return random.choice(["uncommon", "rare"])
        elif level <= 15:
            return random.choice(["rare", "very rare"])
        else:
            return random.choice(["very rare", "legendary"])

    def _generate_skills(self, abilities: Dict[str, int], background: str) -> Dict[str, int]:
        """Generate character skills"""
        skills = {}

        for skill in self.skills:
            # Base skill value is ability modifier + proficiency bonus
            ability_map = {
                "athletics": "strength", "acrobatics": "dexterity", "sleight of hand": "dexterity", "stealth": "dexterity",
                "arcana": "intelligence", "history": "intelligence", "investigation": "intelligence", "nature": "intelligence", "religion": "intelligence",
                "animal handling": "wisdom", "insight": "wisdom", "medicine": "wisdom", "perception": "wisdom", "survival": "wisdom",
                "deception": "charisma", "intimidation": "charisma", "performance": "charisma", "persuasion": "charisma"
            }

            ability = ability_map.get(skill, "intelligence")
            ability_modifier = (abilities[ability] - 10) // 2

            # Background influences skills
            background_skills = {
                "soldier": ["athletics", "intimidation"],
                "scholar": ["history", "arcana", "investigation"],
                "merchant": ["persuasion", "deception"],
                "noble": ["persuasion", "history"],
                "artisan": ["investigation", "performance"],
                "farmer": ["animal handling", "nature"],
                "sailor": ["athletics", "perception"],
                "criminal": ["stealth", "deception"],
                "entertainer": ["performance", "acrobatics"],
                "hermit": ["medicine", "religion"]
            }

            if skill in background_skills.get(background, []):
                proficiency_bonus = random.randint(2, 5)  # Proficient skills
            else:
                proficiency_bonus = random.randint(0, 2)  # Non-proficient skills

            skills[skill] = ability_modifier + proficiency_bonus

        return skills

    def _generate_spells(self, class_type: str, level: int) -> List[str]:
        """Generate spell list for magic users"""
        if class_type not in ["wizard", "sorcerer", "warlock", "bard", "druid", "cleric", "paladin", "ranger"]:
            return []

        # Determine number of spells based on class and level
        max_spells = min(level + random.randint(0, 5), len(self.spells))

        # Select spells appropriate for class
        class_spells = {
            "wizard": ["fireball", "magic missile", "shield", "lightning bolt", "teleport", "invisibility", "fly", "haste", "slow", "dispel magic", "counterspell"],
            "sorcerer": ["fireball", "magic missile", "shield", "lightning bolt", "invisibility", "fly", "haste", "fire shield", "ice storm"],
            "warlock": ["fireball", "magic missile", "eldritch blast", "darkness", "invisibility", "misty step"],
            "bard": ["shield", "invisibility", "fly", "dispel magic", "haste", "slow", "suggestion", "charm person"],
            "druid": ["fireball", "cure wounds", "shield", "invisibility", "fly", "animal friendship", "entangle"],
            "cleric": ["cure wounds", "shield", "spiritual weapon", "bless", "guiding bolt", "healing word"],
            "paladin": ["cure wounds", "shield", "divine smite", "bless", "lay on hands"],
            "ranger": ["hunter's mark", "cure wounds", "lightning arrow", "hail of thorns"]
        }

        available_spells = class_spells.get(class_type, self.spells)

        if len(available_spells) <= max_spells:
            return available_spells
        else:
            return random.sample(available_spells, max_spells)

    def _generate_traits(self, background: str, race: str, class_type: str) -> List[str]:
        """Generate character traits"""
        traits = []

        # Race traits
        race_traits = {
            "human": ["Versatile", "Ambitious"],
            "elf": ["Keen Senses", "Fey Ancestry", "Trance"],
            "dwarf": ["Darkvision", "Dwarven Resilience", "Stonecunning"],
            "halfling": ["Lucky", "Brave", "Halfling Nimbleness"],
            "gnome": ["Gnome Cunning"],
            "half-elf": ["Fey Ancestry", "Skill Versatility"],
            "half-orc": ["Relentless Endurance", "Savage Attacks"],
            "dragonborn": ["Breath Weapon", "Damage Resistance"],
            "tiefling": ["Hellish Resistance", "Infernal Legacy"]
        }

        if race in race_traits:
            traits.extend(race_traits[race])

        # Background traits
        background_traits = {
            "soldier": ["Military Rank", "Weapon Proficiency"],
            "scholar": ["Researcher", "Language Proficiency"],
            "merchant": ["Insightful", "Negotiator"],
            "noble": ["Position of Privilege", "History Knowledge"],
            "artisan": ["Guild Membership", "Craft Skills"],
            "farmer": ["Nature Knowledge", "Animal Handling"],
            "sailor": ["Ship Knowledge", "Swimmer"],
            "criminal": ["Criminal Contact", "Stealth Skills"],
            "entertainer": ["Performance Skills", "Popular"],
            "hermit": ["Discovery", "Secluded Knowledge"]
        }

        if background in background_traits:
            traits.extend(background_traits[background])

        # Class traits
        class_traits = {
            "fighter": ["Fighting Style", "Second Wind"],
            "wizard": ["Arcane Recovery", "Spellcasting"],
            "rogue": ["Sneak Attack", "Thieves' Cant"],
            "cleric": ["Divine Domain", "Channel Divinity"],
            "ranger": ["Favored Enemy", "Natural Explorer"],
            "paladin": ["Divine Sense", "Lay on Hands"],
            "barbarian": ["Rage", "Unarmored Defense"],
            "monk": ["Unarmored Defense", "Martial Arts"],
            "bard": ["Bardic Inspiration", "Jack of All Trades"],
            "druid": ["Druidic", "Wild Shape"],
            "warlock": ["Otherworldly Patron", "Pact Magic"],
            "sorcerer": ["Sorcerous Origin", "Metamagic"]
        }

        if class_type in class_traits:
            traits.extend(class_traits[class_type])

        return list(set(traits))  # Remove duplicates

    def generate_campaign(self, dungeon_master: Optional[str] = None) -> CampaignData:
        """Generate a campaign"""
        campaign_id = str(uuid.uuid4())

        if dungeon_master is None:
            dungeon_master = f"DM_{self.fake.user_name()}"

        themes = ["fantasy", "horror", "mystery", "political intrigue", "exploration", "war", "personal drama"]
        settings = ["medieval fantasy", "high magic", "low magic", "steampunk", "post-apocalyptic", "urban fantasy"]
        difficulties = ["easy", "normal", "hard", "deadly"]

        level_range = random.choice([(1, 5), (3, 10), (5, 15), (10, 20)])
        max_players = random.randint(3, 8)
        current_players = random.randint(1, max_players)

        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))

        sessions_completed = random.randint(0, 50)
        if sessions_completed > 0:
            last_session = created_at + timedelta(weeks=random.randint(1, sessions_completed))
        else:
            last_session = None

        return CampaignData(
            campaign_id=campaign_id,
            name=f"The {random.choice(['Lost', 'Ancient', 'Cursed', 'Forgotten', 'Legendary'])} {random.choice(['Kingdom', 'Dungeon', 'Artifact', 'Prophecy', 'War'])}",
            description=self.fake.paragraph(nb_sentences=3),
            dungeon_master=dungeon_master,
            level_range=level_range,
            max_players=max_players,
            current_players=current_players,
            status=random.choice(["recruiting", "active", "on_hold", "completed"]),
            setting=random.choice(settings),
            theme=random.choice(themes),
            difficulty=random.choice(difficulties),
            sessions_completed=sessions_completed,
            total_sessions=random.randint(sessions_completed + 1, sessions_completed + 20),
            created_at=created_at,
            last_session=last_session,
            tags=random.sample(["combat-heavy", "roleplay-heavy", "puzzle", "exploration", "politics", "mystery", "horror"], k=random.randint(2, 4))
        )

    def generate_combat_encounter(self, participants: List[str]) -> CombatData:
        """Generate a combat encounter"""
        combat_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        # Generate turn order
        turn_order = participants.copy()
        random.shuffle(turn_order)

        environments = ["dungeon", "forest", "mountain", "city", "desert", "swamp", "arctic", "volcanic", "underwater", "aerial"]
        weather = ["clear", "rain", "storm", "fog", "snow", "windy", "extreme heat", "extreme cold"]
        lighting = ["bright", "dim", "dark", "magical", "natural"]

        terrain_features = random.sample([
            "cover positions", "difficult terrain", "obstacles", "elevation changes",
            "hazards", "traps", "environmental dangers", "interactive objects"
        ], k=random.randint(1, 4))

        objectives = random.sample([
            "defeat all enemies", "protect objective", "escape", "retrieve item",
            "survive waves", "solve puzzle during combat", "rescue hostage", "ritual interruption"
        ], k=random.randint(1, 3))

        started_at = datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 120))
        duration = random.randint(5, 60)  # minutes

        return CombatData(
            combat_id=combat_id,
            session_id=session_id,
            participants=participants,
            turn_order=turn_order,
            current_turn=random.randint(0, len(participants) - 1),
            round_number=random.randint(1, 10),
            status=random.choice(["active", "paused", "completed", "abandoned"]),
            environment=random.choice(environments),
            weather=random.choice(weather),
            lighting=random.choice(lighting),
            terrain_features=terrain_features,
            objectives=objectives,
            rewards={
                "experience": random.randint(100, 5000),
                "gold": random.randint(10, 1000),
                "items": random.randint(0, 5)
            },
            started_at=started_at,
            duration=duration
        )

    def generate_dialogue_conversation(self, participants: List[str]) -> DialogueData:
        """Generate a dialogue conversation"""
        conversation_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        topics = ["quest information", "personal backstory", "world lore", "current events", "negotiation", "conflict resolution", "planning", "social interaction"]

        # Generate messages
        num_messages = random.randint(5, 30)
        messages = []

        for i in range(num_messages):
            speaker = random.choice(participants)
            message_type = random.choice(["statement", "question", "emotion", "action"])

            message = {
                "message_id": str(uuid.uuid4()),
                "speaker_id": speaker,
                "type": message_type,
                "content": self.fake.sentence(),
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60)),
                "emotional_tone": random.choice(["neutral", "happy", "sad", "angry", "excited", "concerned"]),
                "impact": random.randint(1, 5)  # Relationship impact
            }
            messages.append(message)

        # Generate relationship changes
        relationship_changes = {}
        for participant in participants:
            relationship_changes[participant] = random.randint(-5, 10)

        outcomes = random.sample([
            "agreement reached", "information exchanged", "relationship improved", "relationship damaged",
            "quest accepted", "quest declined", "conflict resolved", "new alliance formed"
        ], k=random.randint(1, 2))

        started_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
        ended_at = started_at + timedelta(minutes=random.randint(15, 180))

        return DialogueData(
            conversation_id=conversation_id,
            session_id=session_id,
            participants=participants,
            topic=random.choice(topics),
            context={
                "location": random.choice(["tavern", "castle", "forest", "dungeon", "market", "temple"]),
                "urgency": random.choice(["casual", "important", "urgent"]),
                "privacy": random.choice(["public", "private", "semi-private"])
            },
            messages=messages,
            relationship_changes=relationship_changes,
            outcomes=outcomes,
            started_at=started_at,
            ended_at=ended_at
        )

    def generate_quest(self, quest_giver: Optional[str] = None) -> QuestData:
        """Generate a quest"""
        quest_id = str(uuid.uuid4())

        if quest_giver is None:
            quest_giver = f"NPC_{self.fake.name()}"

        quest_types = ["retrieval", "escort", "investigation", "combat", "diplomacy", "exploration", "rescue", "assassination", "delivery", "protection"]

        objectives = []
        num_objectives = random.randint(1, 4)

        for i in range(num_objectives):
            objective = {
                "id": str(uuid.uuid4()),
                "description": self.fake.sentence(),
                "type": random.choice(["kill", "retrieve", "deliver", "protect", "investigate", "escort"]),
                "target": f"Target_{i+1}",
                "location": self.fake.city(),
                "completed": False,
                "optional": random.choice([True, False])
            }
            objectives.append(objective)

        rewards = {
            "experience": random.randint(100, 5000),
            "gold": random.randint(50, 2000),
            "items": random.randint(0, 3),
            "reputation": random.randint(1, 10)
        }

        requirements = {
            "min_level": random.randint(1, 15),
            "required_skills": random.sample(self.skills, k=random.randint(0, 3)),
            "time_limit": f"{random.randint(1, 30)} days",
            "party_size": f"{random.randint(1, 4)}-{random.randint(2, 8)}"
        }

        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        deadline = created_at + timedelta(days=random.randint(7, 90)) if random.random() < 0.7 else None

        return QuestData(
            quest_id=quest_id,
            title=f"The {random.choice(['Lost', 'Missing', 'Cursed', 'Ancient', 'Stolen'])} {random.choice(['Sword', 'Crown', 'Artifact', 'Person', 'Scroll', 'Treasure'])}",
            description=self.fake.paragraph(nb_sentences=3),
            quest_giver=quest_giver,
            objectives=objectives,
            rewards=rewards,
            requirements=requirements,
            difficulty=random.choice(["trivial", "easy", "medium", "hard", "deadly"]),
            estimated_duration=f"{random.randint(1, 6)} hours",
            location=random.choice([self.fake.city(), "Dungeon of Doom", "Enchanted Forest", "Mountain Peak", "Ancient Ruins"]),
            tags=random.sample(["combat", "roleplay", "puzzle", "exploration", "diplomacy", "stealth"], k=random.randint(2, 4)),
            status=random.choice(["available", "in_progress", "completed", "failed", "abandoned"]),
            created_at=created_at,
            deadline=deadline
        )

    def generate_batch_data(self, num_characters: int = 100, num_campaigns: int = 20, num_quests: int = 50) -> Dict[str, Any]:
        """Generate a batch of test data"""
        logger.info(f"Generating batch data: {num_characters} characters, {num_campaigns} campaigns, {num_quests} quests")

        characters = [self.generate_character() for _ in range(num_characters)]
        campaigns = [self.generate_campaign() for _ in range(num_campaigns)]
        quests = [self.generate_quest() for _ in range(num_quests)]

        # Generate combat encounters and dialogues
        combat_encounters = []
        dialogue_conversations = []

        for _ in range(num_campaigns * 3):  # 3 combat encounters per campaign on average
            participants = random.sample([c.character_id for c in characters], k=random.randint(2, 6))
            combat_encounters.append(self.generate_combat_encounter(participants))

        for _ in range(num_campaigns * 5):  # 5 dialogues per campaign on average
            participants = random.sample([c.character_id for c in characters], k=random.randint(2, 4))
            dialogue_conversations.append(self.generate_dialogue_conversation(participants))

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "characters": len(characters),
                "campaigns": len(campaigns),
                "quests": len(quests),
                "combat_encounters": len(combat_encounters),
                "dialogue_conversations": len(dialogue_conversations)
            },
            "data": {
                "characters": [asdict(char) for char in characters],
                "campaigns": [asdict(campaign) for campaign in campaigns],
                "quests": [asdict(quest) for quest in quests],
                "combat_encounters": [asdict(encounter) for encounter in combat_encounters],
                "dialogue_conversations": [asdict(dialogue) for dialogue in dialogue_conversations]
            }
        }

    def export_data(self, data: Dict[str, Any], filename: str):
        """Export generated data to file"""
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            else:
                return obj

        serializable_data = convert_datetime(data)

        with open(filename, 'w') as f:
            json.dump(serializable_data, f, indent=2)

        logger.info(f"Test data exported to {filename}")

# Example usage
if __name__ == "__main__":
    generator = TestDataGenerator(seed=42)

    # Generate single items
    character = generator.generate_character(level=10)
    print(f"Generated character: {character.name} (Level {character.level} {character.class_type})")

    campaign = generator.generate_campaign()
    print(f"Generated campaign: {campaign.name}")

    quest = generator.generate_quest()
    print(f"Generated quest: {quest.title}")

    # Generate batch data
    batch_data = generator.generate_batch_data(num_characters=10, num_campaigns=3, num_quests=8)
    print(f"\nBatch data summary:")
    for key, value in batch_data["summary"].items():
        print(f"  {key}: {value}")

    # Export data
    generator.export_data(batch_data, "test_data_batch.json")
    print("\nData exported to test_data_batch.json")