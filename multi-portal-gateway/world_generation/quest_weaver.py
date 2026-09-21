"""
Dynamic Quest and Story Integration System
Creates procedurally generated quests that naturally emerge from world features,
cultures, locations, and historical events. Generates meaningful narratives
that integrate with the game world's geography and inhabitants.
"""

import numpy as np
import random
from collections import defaultdict, deque
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class QuestType(Enum):
    MAIN_STORY = "main_story"
    SIDE_QUEST = "side_quest"
    PERSONAL = "personal"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    CRAFTING = "crafting"
    DIPLOMATIC = "diplomatic"
    MYSTERY = "mystery"
    RESCUE = "rescue"
    ESCORT = "escort"
    DELIVERY = "delivery"
    INVESTIGATION = "investigation"
    COLLECTION = "collection"
    BOSS_HUNT = "boss_hunt"
    DUNGEON_CRAWL = "dungeon_crawl"
    TRADE = "trade"

class QuestDifficulty(Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    VERY_HARD = "very_hard"
    LEGENDARY = "legendary"
    IMPOSSIBLE = "impossible"

class QuestStatus(Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    LOCKED = "locked"

class QuestRewardType(Enum):
    GOLD = "gold"
    EXPERIENCE = "experience"
    ITEM = "item"
    REPUTATION = "reputation"
    RELATIONSHIP = "relationship"
    SKILL_POINT = "skill_point"
    ABILITY = "ability"
    INFORMATION = "information"
    ACCESS = "access"
    TITLE = "title"

class QuestObjectiveType(Enum):
    KILL = "kill"
    COLLECT = "collect"
    DELIVER = "deliver"
    TALK_TO = "talk_to"
    ESCORT = "escort"
    PROTECT = "protect"
    INVESTIGATE = "investigate"
    FIND = "find"
    ACTIVATE = "activate"
    CRAFT = "craft"
    PERSUADE = "persuade"
    STEAL = "steal"
    SURVIVE = "survive"
    REACH = "reach"
    DEFEAT = "defeat"

class NPCAttitude(Enum):
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    SUSPICIOUS = "suspicious"
    HOSTILE = "hostile"
    DESPERATE = "desperate"
    MYSTERIOUS = "mysterious"
    ARROGANT = "arrogant"
    WISE = "wise"

@dataclass
class QuestObjective:
    """Represents a single quest objective"""
    objective_type: QuestObjectiveType
    description: str
    target: str  # What needs to be done
    quantity: int = 1
    location: Optional[Tuple[int, int]] = None
    completed: bool = False
    required_items: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None  # In game time units
    hidden: bool = False  # Hidden from player until discovered

@dataclass
class QuestReward:
    """Represents a quest reward"""
    reward_type: QuestRewardType
    description: str
    value: int  # Numerical value (gold amount, exp points, etc.)
    item_name: Optional[str] = None
    relationship_change: Optional[Tuple[str, int]] = None  # faction and amount

@dataclass
class QuestGiver:
    """Represents an NPC who gives quests"""
    name: str
    location: Tuple[int, int]
    attitude: NPCAttitude
    background: str
    motivation: str
    secrets: List[str] = field(default_factory=list)
    relationship_value: int = 0  # -100 to 100
    quest_giver_type: str = "villager"  # villager, noble, merchant, guard, etc.

@dataclass
class Quest:
    """Complete quest representation"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty
    status: QuestStatus
    quest_giver: QuestGiver
    objectives: List[QuestObjective]
    rewards: List[QuestReward]
    prerequisites: List[str] = field(default_factory=list)  # Other quest IDs
    consequences: List[str] = field(default_factory=list)  # Results of completion
    time_sensitive: bool = False
    repeatable: bool = False
    story_beat: bool = False  # Is this part of main story?
    world_impact: List[str] = field(default_factory=list)  # Changes to world state
    required_level: int = 1
    recommended_level: int = 1
    tags: List[str] = field(default_factory=list)
    faction_reputation_changes: Dict[str, int] = field(default_factory=dict)

@dataclass
class StoryArc:
    """Represents a connected series of quests"""
    name: str
    description: str
    quest_ids: List[str]
    arc_type: str  # main, side, character, location
    theme: str
    major_choices: List[str] = field(default_factory=list)
    branching_points: List[str] = field(default_factory=list)

class WorldContext:
    """Context about the world for quest generation"""
    def __init__(self):
        self.locations = {}  # location_id -> location_data
        self.npcs = {}  # npc_id -> npc_data
        self.factions = {}  # faction_id -> faction_data
        self.items = {}  # item_id -> item_data
        self.events = []  # Recent world events
        self.player_level = 1
        self.player_location = (0, 0)
        self.completed_quests = set()
        self.active_quests = set()
        self.world_state = {}  # Global world state variables
        self.season = "spring"
        self.time_of_day = "day"

class QuestTemplate:
    """Template for generating specific types of quests"""
    def __init__(self, name: str, quest_type: QuestType, objectives_template: List[Dict],
                 rewards_template: List[Dict], difficulty_range: Tuple[int, int],
                 prerequisites_template: List[str] = None):
        self.name = name
        self.quest_type = quest_type
        self.objectives_template = objectives_template
        self.rewards_template = rewards_template
        self.difficulty_range = difficulty_range
        self.prerequisites_template = prerequisites_template or []

class QuestNarrativeEngine:
    """Generates narrative content for quests"""

    def __init__(self):
        self.quest_intros = {
            QuestType.RESCUE: [
                "A {emotion} {quest_giver} approaches you with {urgency} in their eyes.",
                "Word has reached you that {target} is in grave danger.",
                "Rumors speak of someone in need of rescue at {location}.",
                "A desperate plea echoes through the {region}: help is needed."
            ],
            QuestType.COLLECTION: [
                "A {adjective} {quest_giver} seeks {items} for a {purpose}.",
                "The demand for {items} has never been higher in {location}.",
                "A reward is offered for gathering {items} from the dangerous {region}.",
                "Local {quest_giver_type} are requesting assistance with collecting {items}."
            ],
            QuestType.INVESTIGATION: [
                "Strange occurrences have been reported near {location}.",
                "A {mystery} has puzzled the residents of {location} for days.",
                "Evidence suggests something {suspicious} is happening at {location}.",
                "The local {authority} has requested an investigation into {situation}."
            ],
            QuestType.BOSS_HUNT: [
                "A fearsome {monster} terrorizes the {region}.",
                "Legends speak of a {adjective} {monster} dwelling in {location}.",
                "The {monster} has claimed its latest victim in the {region}.",
                "Bounties are posted for whoever can defeat the {monster}."
            ]
        }

        self.objective_descriptions = {
            QuestObjectiveType.KILL: [
                "Defeat {quantity} {target}",
                "Eliminate the {target} threat",
                "Slay {quantity} {target}",
                "Hunt down and kill {target}"
            ],
            QuestObjectiveType.COLLECT: [
                "Gather {quantity} {target}",
                "Collect {quantity} {target} from {location}",
                "Find and retrieve {quantity} {target}",
                "Acquire {quantity} {target}"
            ],
            QuestObjectiveType.TALK_TO: [
                "Speak with {target}",
                "Consult with {target} about {topic}",
                "Question {target} regarding {situation}",
                "Interview {target}"
            ],
            QuestObjectiveType.FIND: [
                "Locate the {target}",
                "Discover the whereabouts of {target}",
                "Search for {target} in {location}",
                "Find the missing {target}"
            ]
        }

        self.resolution_texts = {
            "success": [
                "With the task completed, you return to {quest_giver}.",
                "Your success is celebrated by the people of {location}.",
                "The {quest_giver} expresses gratitude for your help.",
                "News of your accomplishment spreads throughout the {region}."
            ],
            "failure": [
                "Despite your efforts, the task remains incomplete.",
                "The {quest_giver} is disappointed by the outcome.",
                "Your failure has consequences for the people of {location}.",
                "The situation in {location} remains unresolved."
            ]
        }

    def generate_quest_introduction(self, quest_type: QuestType, quest_giver: QuestGiver,
                                  context: WorldContext) -> str:
        """Generate quest introduction text"""
        intro_templates = self.quest_intros.get(quest_type, [
            "A {quest_giver} has a task for you."
        ])

        template = random.choice(intro_templates)

        # Fill in template with context
        intro = template.format(
            emotion=random.choice(["desperate", "worried", "hopeful", "determined", "anxious"]),
            quest_giver=quest_giver.name,
            urgency=random.choice(["great urgency", "desperation", "hope", "concern"]),
            location=random.choice(list(context.locations.keys())) if context.locations else "the local area",
            region=random.choice(["region", "area", "district", "quarter"]),
            items=random.choice(["rare materials", "valuable items", "ancient artifacts", "precious resources"]),
            adjective=random.choice(["wise", "elderly", "respected", "influential", "knowledgeable"]),
            quest_giver_type=random.choice(["merchants", "craftsmen", "scholars", "farmers", "guards"]),
            mystery=random.choice(["disappearance", "theft", "strange lights", "unusual sounds", "mysterious illness"]),
            suspicious=random.choice(["suspicious", "concerning", "worrying", "disturbing", "unsettling"]),
            authority=random.choice(["guard captain", "town elder", "merchant guild", "temple priests"]),
            situation=random.choice(["recent events", "local disturbances", "security concerns", "unusual activities"]),
            monster=random.choice(["beast", "creature", "monster", "menace", "terror"]),
            adjective_monster=random.choice(["ancient", "powerful", "terrifying", "dreaded", "legendary"])
        )

        return intro

    def generate_objective_description(self, objective_type: QuestObjectiveType,
                                     target: str, quantity: int = 1,
                                     location: Optional[str] = None) -> str:
        """Generate description for quest objective"""
        templates = self.objective_descriptions.get(objective_type, [
            "Deal with {target}"
        ])

        template = random.choice(templates)

        description = template.format(
            quantity=quantity,
            target=target,
            location=location or "the designated area"
        )

        if quantity > 1:
            description = description.replace("{quantity}", str(quantity))

        return description

    def generate_quest_resolution(self, success: bool, quest_giver: QuestGiver,
                               quest_type: QuestType, location: str) -> str:
        """Generate quest resolution text"""
        resolution_type = "success" if success else "failure"
        templates = self.resolution_texts.get(resolution_type, [
            "The quest is {result}."
        ])

        template = random.choice(templates)

        resolution = template.format(
            quest_giver=quest_giver.name,
            location=location,
            region=random.choice(["region", "area", "district"]),
            result="completed" if success else "failed"
        )

        return resolution

class QuestWeaver:
    """Main quest generation system"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.narrative_engine = QuestNarrativeEngine()
        self.quest_templates = self._initialize_quest_templates()
        self.generated_quests = {}
        self.story_arcs = []
        self.quest_id_counter = 0

    def _initialize_quest_templates(self) -> Dict[str, QuestTemplate]:
        """Initialize quest templates for different quest types"""
        templates = {}

        # Rescue quest template
        templates["rescue"] = QuestTemplate(
            name="Rescue Mission",
            quest_type=QuestType.RESCUE,
            objectives_template=[
                {"type": QuestObjectiveType.FIND, "quantity": 1},
                {"type": QuestObjectiveType.ESCORT, "quantity": 1}
            ],
            rewards_template=[
                {"type": QuestRewardType.GOLD, "multiplier": 100},
                {"type": QuestRewardType.EXPERIENCE, "multiplier": 150},
                {"type": QuestRewardType.REPUTATION, "multiplier": 10}
            ],
            difficulty_range=(1, 20)
        )

        # Collection quest template
        templates["collection"] = QuestTemplate(
            name="Collection Task",
            quest_type=QuestType.COLLECTION,
            objectives_template=[
                {"type": QuestObjectiveType.COLLECT, "quantity": 5}
            ],
            rewards_template=[
                {"type": QuestRewardType.GOLD, "multiplier": 50},
                {"type": QuestRewardType.EXPERIENCE, "multiplier": 80}
            ],
            difficulty_range=(1, 15)
        )

        # Monster hunt quest template
        templates["monster_hunt"] = QuestTemplate(
            name="Monster Hunt",
            quest_type=QuestType.BOSS_HUNT,
            objectives_template=[
                {"type": QuestObjectiveType.DEFEAT, "quantity": 1}
            ],
            rewards_template=[
                {"type": QuestRewardType.GOLD, "multiplier": 200},
                {"type": QuestRewardType.EXPERIENCE, "multiplier": 250},
                {"type": QuestRewardType.ITEM, "chance": 0.3}
            ],
            difficulty_range=(5, 30)
        )

        # Investigation quest template
        templates["investigation"] = QuestTemplate(
            name="Investigation",
            quest_type=QuestType.INVESTIGATION,
            objectives_template=[
                {"type": QuestObjectiveType.INVESTIGATE, "quantity": 1},
                {"type": QuestObjectiveType.TALK_TO, "quantity": 3}
            ],
            rewards_template=[
                {"type": QuestRewardType.INFORMATION, "value": 1},
                {"type": QuestRewardType.EXPERIENCE, "multiplier": 120},
                {"type": QuestRewardType.REPUTATION, "multiplier": 5}
            ],
            difficulty_range=(3, 25)
        )

        # Delivery quest template
        templates["delivery"] = QuestTemplate(
            name="Delivery Service",
            quest_type=QuestType.DELIVERY,
            objectives_template=[
                {"type": QuestObjectiveType.DELIVER, "quantity": 1}
            ],
            rewards_template=[
                {"type": QuestRewardType.GOLD, "multiplier": 30},
                {"type": QuestRewardType.EXPERIENCE, "multiplier": 40}
            ],
            difficulty_range=(1, 10)
        )

        return templates

    def generate_quest(self, quest_type: QuestType, quest_giver: QuestGiver,
                      context: WorldContext, difficulty: Optional[QuestDifficulty] = None) -> Quest:
        """Generate a complete quest"""
        quest_id = f"quest_{self.quest_id_counter}"
        self.quest_id_counter += 1

        # Determine difficulty
        if difficulty is None:
            difficulty = self._determine_quest_difficulty(context, quest_type)

        # Select template
        template_name = self._select_template_for_quest_type(quest_type)
        template = self.quest_templates.get(template_name)

        # Generate title
        title = self._generate_quest_title(quest_type, quest_giver, difficulty)

        # Generate description
        description = self.narrative_engine.generate_quest_introduction(
            quest_type, quest_giver, context
        )

        # Generate objectives
        objectives = self._generate_quest_objectives(template, quest_giver, context, difficulty)

        # Generate rewards
        rewards = self._generate_quest_rewards(template, difficulty, context)

        # Determine prerequisites
        prerequisites = self._generate_quest_prerequisites(quest_type, difficulty, context)

        # Generate world impact
        world_impact = self._generate_world_impact(quest_type, difficulty, context)

        # Generate tags
        tags = self._generate_quest_tags(quest_type, difficulty)

        quest = Quest(
            id=quest_id,
            title=title,
            description=description,
            quest_type=quest_type,
            difficulty=difficulty,
            status=QuestStatus.AVAILABLE,
            quest_giver=quest_giver,
            objectives=objectives,
            rewards=rewards,
            prerequisites=prerequisites,
            world_impact=world_impact,
            tags=tags,
            required_level=self._get_required_level(difficulty),
            recommended_level=self._get_recommended_level(difficulty),
            time_sensitive=random.random() < 0.2,  # 20% chance of being time-sensitive
            story_beat=random.random() < 0.1   # 10% chance of being story-critical
        )

        self.generated_quests[quest_id] = quest
        return quest

    def _determine_quest_difficulty(self, context: WorldContext, quest_type: QuestType) -> QuestDifficulty:
        """Determine quest difficulty based on context and player level"""
        player_level = context.player_level

        # Base difficulty on player level
        if player_level <= 5:
            base_difficulties = [QuestDifficulty.TRIVIAL, QuestDifficulty.EASY, QuestDifficulty.NORMAL]
        elif player_level <= 15:
            base_difficulties = [QuestDifficulty.EASY, QuestDifficulty.NORMAL, QuestDifficulty.HARD]
        elif player_level <= 30:
            base_difficulties = [QuestDifficulty.NORMAL, QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]
        else:
            base_difficulties = [QuestDifficulty.HARD, QuestDifficulty.VERY_HARD, QuestDifficulty.LEGENDARY]

        # Adjust based on quest type
        if quest_type in [QuestType.BOSS_HUNT, QuestType.DUNGEON_CRAWL]:
            # These are generally harder
            base_difficulties = [d for d in base_difficulties if d.value not in ["trivial", "easy"]]
        elif quest_type in [QuestType.DELIVERY, QuestType.COLLECTION]:
            # These are generally easier
            base_difficulties = [d for d in base_difficulties if d.value not in ["legendary", "impossible"]]

        return random.choice(base_difficulties)

    def _select_template_for_quest_type(self, quest_type: QuestType) -> str:
        """Select appropriate template for quest type"""
        template_mapping = {
            QuestType.RESCUE: "rescue",
            QuestType.COLLECTION: "collection",
            QuestType.BOSS_HUNT: "monster_hunt",
            QuestType.INVESTIGATION: "investigation",
            QuestType.DELIVERY: "delivery"
        }

        return template_mapping.get(quest_type, "collection")

    def _generate_quest_title(self, quest_type: QuestType, quest_giver: QuestGiver,
                            difficulty: QuestDifficulty) -> str:
        """Generate quest title"""
        title_templates = {
            QuestType.RESCUE: [
                "Rescue {target}",
                "The Missing {target}",
                "Save {target} from {danger}",
                "A Desperate Rescue"
            ],
            QuestType.COLLECTION: [
                "Gathering {items}",
                "The {adjective} Collection",
                "{quantity} {items} Needed",
                "Supply Run"
            ],
            QuestType.BOSS_HUNT: [
                "Hunt the {monster}",
                "The {adjective} {monster}",
                "Slay the {monster} of {location}",
                "Monster Bounty"
            ],
            QuestType.INVESTIGATION: [
                "Investigate {mystery}",
                "The {adjective} Case",
                "Uncovering the Truth",
                "Strange Occurrences"
            ],
            QuestType.DELIVERY: [
                "Deliver {item}",
                "A Special Delivery",
                "Package to {location}",
                "Express Delivery"
            ]
        }

        templates = title_templates.get(quest_type, ["A {adjective} Task"])

        template = random.choice(templates)

        # Generate dynamic components
        title = template.format(
            target=random.choice(["child", "merchant", "scholar", "noble", "craftsman", "heir"]),
            items=random.choice(["herbs", "ores", "crystals", "artifacts", "rare materials"]),
            item=random.choice(["package", "letter", "artifact", "weapon", "medicine"]),
            quantity=random.choice(["Five", "Ten", "Fifteen", "Twenty"]),
            danger=random.choice(["danger", "peril", "doom", "captivity", "threat"]),
            adjective=random.choice(["Desperate", "Urgent", "Important", "Critical", "Special"]),
            monster=random.choice(["Beast", "Creature", "Menace", "Terror", "Fiend"]),
            location=random.choice(["the Forest", "the Mountains", "the Dungeon", "the Ruins"]),
            mystery=random.choice(["Disappearance", "Theft", "Murder", "Conspiracy", "Curse"])
        )

        return title

    def _generate_quest_objectives(self, template: Optional[QuestTemplate],
                                 quest_giver: QuestGiver, context: WorldContext,
                                 difficulty: QuestDifficulty) -> List[QuestObjective]:
        """Generate quest objectives"""
        objectives = []

        if template:
            # Use template objectives
            for obj_template in template.objectives_template:
                objective = self._create_objective_from_template(
                    obj_template, quest_giver, context, difficulty
                )
                objectives.append(objective)
        else:
            # Generate generic objective
            objective = QuestObjective(
                objective_type=QuestObjectiveType.TALK_TO,
                description="Speak with the quest giver",
                target=quest_giver.name,
                location=quest_giver.location
            )
            objectives.append(objective)

        return objectives

    def _create_objective_from_template(self, obj_template: Dict,
                                      quest_giver: QuestGiver, context: WorldContext,
                                      difficulty: QuestDifficulty) -> QuestObjective:
        """Create objective from template"""
        objective_type = obj_template["type"]
        quantity = obj_template.get("quantity", 1)

        # Generate target based on objective type
        target = self._generate_objective_target(objective_type, quest_giver, context, difficulty)
        location = self._generate_objective_location(objective_type, quest_giver, context)

        description = self.narrative_engine.generate_objective_description(
            objective_type, target, quantity, location
        )

        return QuestObjective(
            objective_type=objective_type,
            description=description,
            target=target,
            quantity=quantity,
            location=location
        )

    def _generate_objective_target(self, objective_type: QuestObjectiveType,
                                 quest_giver: QuestGiver, context: WorldContext,
                                 difficulty: QuestDifficulty) -> str:
        """Generate target for objective"""
        if objective_type == QuestObjectiveType.KILL:
            targets = ["goblins", "bandits", "wolves", "undead", "orcs", "spiders"]
            return random.choice(targets)
        elif objective_type == QuestObjectiveType.COLLECT:
            targets = ["herbs", "ores", "crystals", "artifacts", "rare materials", "ancient coins"]
            return random.choice(targets)
        elif objective_type == QuestObjectiveType.TALK_TO:
            # Generate NPC name
            return f"{random.choice(['Merchant', 'Guard', "Scholar", 'Healer', 'Blacksmith'])} {random.choice(['John', 'Mary', 'William', 'Sarah', 'Robert', 'Emma'])}"
        elif objective_type == QuestObjectiveType.FIND:
            targets = ["missing person", "ancient artifact", "lost document", "hidden treasure", "secret passage"]
            return random.choice(targets)
        elif objective_type == QuestObjectiveType.DEFEAT:
            targets = ["dragon", "demon", "lich", "giant", "hydra", "minotaur"]
            return f"{random.choice(['Ancient', 'Powerful', 'Dreaded', 'Dark'])} {random.choice(targets)}"
        else:
            return "target"

    def _generate_objective_location(self, objective_type: QuestObjectiveType,
                                   quest_giver: QuestGiver, context: WorldContext) -> Optional[str]:
        """Generate location for objective"""
        if context.locations:
            locations = list(context.locations.keys())
            # Choose location not too far from quest giver
            return random.choice(locations)
        return None

    def _generate_quest_rewards(self, template: Optional[QuestTemplate],
                              difficulty: QuestDifficulty, context: WorldContext) -> List[QuestReward]:
        """Generate quest rewards"""
        rewards = []

        if template:
            # Use template rewards
            for reward_template in template.rewards_template:
                reward = self._create_reward_from_template(
                    reward_template, difficulty, context
                )
                rewards.append(reward)
        else:
            # Generate default rewards
            gold_amount = self._calculate_gold_reward(difficulty)
            exp_amount = self._calculate_experience_reward(difficulty)

            rewards.append(QuestReward(
                reward_type=QuestRewardType.GOLD,
                description=f"{gold_amount} gold",
                value=gold_amount
            ))
            rewards.append(QuestReward(
                reward_type=QuestRewardType.EXPERIENCE,
                description=f"{exp_amount} experience points",
                value=exp_amount
            ))

        return rewards

    def _create_reward_from_template(self, reward_template: Dict,
                                   difficulty: QuestDifficulty, context: WorldContext) -> QuestReward:
        """Create reward from template"""
        reward_type = reward_template["type"]

        if reward_type == QuestRewardType.GOLD:
            multiplier = reward_template.get("multiplier", 100)
            value = self._calculate_gold_reward(difficulty, multiplier)
            return QuestReward(
                reward_type=reward_type,
                description=f"{value} gold",
                value=value
            )
        elif reward_type == QuestRewardType.EXPERIENCE:
            multiplier = reward_template.get("multiplier", 100)
            value = self._calculate_experience_reward(difficulty, multiplier)
            return QuestReward(
                reward_type=reward_type,
                description=f"{value} experience points",
                value=value
            )
        elif reward_type == QuestRewardType.REPUTATION:
            multiplier = reward_template.get("multiplier", 10)
            value = self._calculate_reputation_reward(difficulty, multiplier)
            return QuestReward(
                reward_type=reward_type,
                description=f"{value} reputation",
                value=value
            )
        elif reward_type == QuestRewardType.ITEM:
            # Generate item reward
            item_name = self._generate_reward_item(difficulty)
            return QuestReward(
                reward_type=reward_type,
                description=item_name,
                value=1,
                item_name=item_name
            )
        else:
            return QuestReward(
                reward_type=reward_type,
                description="Reward",
                value=1
            )

    def _calculate_gold_reward(self, difficulty: QuestDifficulty, multiplier: int = 100) -> int:
        """Calculate gold reward based on difficulty"""
        difficulty_multipliers = {
            QuestDifficulty.TRIVIAL: 0.2,
            QuestDifficulty.EASY: 0.5,
            QuestDifficulty.NORMAL: 1.0,
            QuestDifficulty.HARD: 2.0,
            QuestDifficulty.VERY_HARD: 5.0,
            QuestDifficulty.LEGENDARY: 10.0,
            QuestDifficulty.IMPOSSIBLE: 20.0
        }

        base_multiplier = difficulty_multipliers.get(difficulty, 1.0)
        return int(multiplier * base_multiplier * random.uniform(0.8, 1.2))

    def _calculate_experience_reward(self, difficulty: QuestDifficulty, multiplier: int = 100) -> int:
        """Calculate experience reward based on difficulty"""
        difficulty_multipliers = {
            QuestDifficulty.TRIVIAL: 0.3,
            QuestDifficulty.EASY: 0.6,
            QuestDifficulty.NORMAL: 1.0,
            QuestDifficulty.HARD: 1.8,
            QuestDifficulty.VERY_HARD: 3.0,
            QuestDifficulty.LEGENDARY: 5.0,
            QuestDifficulty.IMPOSSIBLE: 8.0
        }

        base_multiplier = difficulty_multipliers.get(difficulty, 1.0)
        return int(multiplier * base_multiplier * random.uniform(0.8, 1.2))

    def _calculate_reputation_reward(self, difficulty: QuestDifficulty, multiplier: int = 10) -> int:
        """Calculate reputation reward based on difficulty"""
        difficulty_multipliers = {
            QuestDifficulty.TRIVIAL: 0.2,
            QuestDifficulty.EASY: 0.5,
            QuestDifficulty.NORMAL: 1.0,
            QuestDifficulty.HARD: 1.5,
            QuestDifficulty.VERY_HARD: 2.0,
            QuestDifficulty.LEGENDARY: 3.0,
            QuestDifficulty.IMPOSSIBLE: 5.0
        }

        base_multiplier = difficulty_multipliers.get(difficulty, 1.0)
        return int(multiplier * base_multiplier * random.uniform(0.8, 1.2))

    def _generate_reward_item(self, difficulty: QuestDifficulty) -> str:
        """Generate item reward based on difficulty"""
        item_prefixes = {
            QuestDifficulty.TRIVIAL: ["Simple", "Basic"],
            QuestDifficulty.EASY: ["Common", "Standard"],
            QuestDifficulty.NORMAL: ["Quality", "Fine"],
            QuestDifficulty.HARD: ["Superior", "Masterwork"],
            QuestDifficulty.VERY_HARD: ["Exceptional", "Magnificent"],
            QuestDifficulty.LEGENDARY: ["Legendary", "Mythic"],
            QuestDifficulty.IMPOSSIBLE: ["Divine", "Ethereal"]
        }

        item_types = ["Sword", "Armor", "Potion", "Ring", "Amulet", "Staff", "Bow", "Shield"]
        prefixes = item_prefixes.get(difficulty, ["Normal"])

        prefix = random.choice(prefixes)
        item_type = random.choice(item_types)

        return f"{prefix} {item_type}"

    def _generate_quest_prerequisites(self, quest_type: QuestType,
                                    difficulty: QuestDifficulty,
                                    context: WorldContext) -> List[str]:
        """Generate quest prerequisites"""
        prerequisites = []

        # Higher difficulty quests might require previous quests
        if difficulty in [QuestDifficulty.VERY_HARD, QuestDifficulty.LEGENDARY, QuestDifficulty.IMPOSSIBLE]:
            if context.completed_quests:
                # Require completion of some previous quests
                num_prereqs = min(2, len(context.completed_quests))
                prerequisites.extend(random.sample(list(context.completed_quests), num_prereqs))

        # Some quest types have specific prerequisites
        if quest_type == QuestType.BOSS_HUNT and difficulty != QuestDifficulty.TRIVIAL:
            # Might require specific equipment or level
            if context.player_level < self._get_recommended_level(difficulty):
                prerequisites.append(f"Level {self._get_recommended_level(difficulty)}")

        return prerequisites

    def _generate_world_impact(self, quest_type: QuestType,
                             difficulty: QuestDifficulty,
                             context: WorldContext) -> List[str]:
        """Generate world impact from quest completion"""
        impacts = []

        if quest_type == QuestType.RESCUE:
            impacts.append("NPC rescued and returned to community")
            impacts.append("Increased local reputation")
        elif quest_type == QuestType.BOSS_HUNT:
            impacts.append("Monster threat eliminated")
            impacts.append("Area becomes safer for travel")
            if difficulty in [QuestDifficulty.LEGENDARY, QuestDifficulty.IMPOSSIBLE]:
                impacts.append("Region celebrates monster's defeat")
        elif quest_type == QuestType.INVESTIGATION:
            impacts.append("Mystery solved")
            impacts.append("New information revealed")
        elif quest_type == QuestType.COLLECTION:
            impacts.append("Resources gathered and delivered")
            impacts.append("Local economy improved")

        # High difficulty quests have bigger impacts
        if difficulty in [QuestDifficulty.VERY_HARD, QuestDifficulty.LEGENDARY, QuestDifficulty.IMPOSSIBLE]:
            impacts.append("Major world event triggered")
            impacts.append("New opportunities unlocked")

        return impacts

    def _generate_quest_tags(self, quest_type: QuestType, difficulty: QuestDifficulty) -> List[str]:
        """Generate quest tags for categorization"""
        tags = [quest_type.value]

        # Difficulty tags
        if difficulty in [QuestDifficulty.TRIVIAL, QuestDifficulty.EASY]:
            tags.append("beginner")
        elif difficulty in [QuestDifficulty.HARD, QuestDifficulty.VERY_HARD]:
            tags.append("challenging")
        elif difficulty in [QuestDifficulty.LEGENDARY, QuestDifficulty.IMPOSSIBLE]:
            tags.append("epic")

        # Add contextual tags
        if random.random() < 0.3:
            tags.append("combat")
        if random.random() < 0.3:
            tags.append("exploration")
        if random.random() < 0.2:
            tags.append("time_sensitive")
        if random.random() < 0.1:
            tags.append("story_critical")

        return tags

    def _get_required_level(self, difficulty: QuestDifficulty) -> int:
        """Get required level for quest difficulty"""
        level_map = {
            QuestDifficulty.TRIVIAL: 1,
            QuestDifficulty.EASY: 3,
            QuestDifficulty.NORMAL: 8,
            QuestDifficulty.HARD: 15,
            QuestDifficulty.VERY_HARD: 25,
            QuestDifficulty.LEGENDARY: 40,
            QuestDifficulty.IMPOSSIBLE: 60
        }
        return level_map.get(difficulty, 1)

    def _get_recommended_level(self, difficulty: QuestDifficulty) -> int:
        """Get recommended level for quest difficulty"""
        level_map = {
            QuestDifficulty.TRIVIAL: 3,
            QuestDifficulty.EASY: 5,
            QuestDifficulty.NORMAL: 10,
            QuestDifficulty.HARD: 18,
            QuestDifficulty.VERY_HARD: 30,
            QuestDifficulty.LEGENDARY: 45,
            QuestDifficulty.IMPOSSIBLE: 65
        }
        return level_map.get(difficulty, 1)

    def generate_story_arc(self, theme: str, num_quests: int,
                          quest_givers: List[QuestGiver],
                          context: WorldContext) -> StoryArc:
        """Generate a connected story arc"""
        arc_name = self._generate_arc_name(theme)
        arc_description = self._generate_arc_description(theme)

        # Generate quests for the arc
        quest_ids = []
        quest_types = self._select_quest_types_for_arc(theme, num_quests)

        for i, quest_type in enumerate(quest_types):
            quest_giver = quest_givers[i % len(quest_givers)]

            # Make later quests in arc more difficult
            difficulty_modifier = min(i * 2, 20)
            adjusted_context = context
            adjusted_context.player_level += difficulty_modifier

            quest = self.generate_quest(quest_type, quest_giver, adjusted_context)

            # Make quests dependent on previous ones in arc
            if i > 0:
                quest.prerequisites.append(quest_ids[i-1])

            quest_ids.append(quest.id)

        story_arc = StoryArc(
            name=arc_name,
            description=arc_description,
            quest_ids=quest_ids,
            arc_type="side",
            theme=theme
        )

        self.story_arcs.append(story_arc)
        return story_arc

    def _generate_arc_name(self, theme: str) -> str:
        """Generate story arc name"""
        name_templates = {
            "corruption": ["The {adjective} Corruption", "Shadows of {location}", "The {adjective} Blight"],
            "revenge": ["Vengeance of {npc}", "The {adjective} Revenge", "Blood Debts"],
            "mystery": ["The {adjective} Mystery", "Secrets of {location}", "The {adjective} Enigma"],
            "war": ["The {adjective} War", "Battle for {location}", "The {adjective} Conflict"],
            "exploration": ["The {adjective} Expedition", "Discovering {location}", "The {adjective} Journey"],
            "rescue": ["The Great Rescue", "Saving {location}", "The {adjective} Recovery"]
        }

        templates = name_templates.get(theme, ["The {adjective} Adventure"])

        return random.choice(templates).format(
            adjective=random.choice(["Ancient", "Dark", "Hidden", "Lost", "Forgotten", "Mysterious", "Epic"]),
            location=random.choice(["the North", "the East", "the Mountains", "the Forest", "the Kingdom"]),
            npc=random.choice(["the King", "the Queen", "the Merchant", "the Scholar", "the Warrior"])
        )

    def _generate_arc_description(self, theme: str) -> str:
        """Generate story arc description"""
        descriptions = {
            "corruption": "A mysterious corruption spreads through the land, twisting creatures and people alike. Someone must uncover its source before it's too late.",
            "revenge": "An old enemy seeks vengeance for past wrongs, drawing innocents into their conflict. The cycle of violence must be broken.",
            "mystery": "Strange occurrences puzzle the local population, hinting at deeper secrets beneath the surface.",
            "war": "Conflict erupts between factions, threatening to engulf the entire region in chaos.",
            "exploration": "Ancient ruins and forgotten lands call to brave adventurers, promising treasures and dangers untold.",
            "rescue": "Kidnappings and disappearances plague the region, requiring heroes to venture into dangerous territory to save the innocent."
        }

        return descriptions.get(theme, "An adventure unfolds, testing the courage and wisdom of those who answer the call.")

    def _select_quest_types_for_arc(self, theme: str, num_quests: int) -> List[QuestType]:
        """Select appropriate quest types for story arc theme"""
        quest_type_pools = {
            "corruption": [QuestType.INVESTIGATION, QuestType.COLLECTION, QuestType.BOSS_HUNT],
            "revenge": [QuestType.COMBAT, QuestType.INVESTIGATION, QuestType.ESCORT],
            "mystery": [QuestType.INVESTIGATION, QuestType.COLLECTION, QuestType.TALK_TO],
            "war": [QuestType.COMBAT, QuestType.ESCORT, QuestType.DUNGEON_CRAWL],
            "exploration": [QuestType.EXPLORATION, QuestType.COLLECTION, QuestType.DUNGEON_CRAWL],
            "rescue": [QuestType.RESCUE, QuestType.COMBAT, QuestType.INVESTIGATION]
        }

        available_types = quest_type_pools.get(theme, list(QuestType))
        return [random.choice(available_types) for _ in range(num_quests)]

    def generate_quest_giver(self, location: Tuple[int, int], context: WorldContext) -> QuestGiver:
        """Generate a quest giver NPC"""
        name = self._generate_npc_name()
        attitude = random.choice(list(NPCAttitude))
        background = self._generate_npc_background(attitude)
        motivation = self._generate_npc_motivation(attitude)
        quest_giver_type = random.choice(["villager", "merchant", "noble", "guard", "scholar", "healer"])

        return QuestGiver(
            name=name,
            location=location,
            attitude=attitude,
            background=background,
            motivation=motivation,
            quest_giver_type=quest_giver_type,
            relationship_value=random.randint(-20, 20)
        )

    def _generate_npc_name(self) -> str:
        """Generate NPC name"""
        first_names = ["John", "Mary", "William", "Sarah", "Robert", "Emma", "James", "Elizabeth",
                      "Michael", "Jennifer", "David", "Lisa", "Richard", "Patricia", "Joseph", "Linda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                     "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas"]

        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_npc_background(self, attitude: NPCAttitude) -> str:
        """Generate NPC background story"""
        backgrounds = {
            NPCAttitude.FRIENDLY: "A warm and welcoming member of the community who always tries to help others.",
            NPCAttitude.NEUTRAL: "An ordinary person just trying to get by in these challenging times.",
            NPCAttitude.SUSPICIOUS: "Someone who has learned to be cautious after past betrayals and disappointments.",
            NPCAttitude.HOSTILE: "A bitter individual who has seen too much hardship and trusts no one.",
            NPCAttitude.DESPERATE: "Someone at their wit's end, willing to do anything to solve their problems.",
            NPCAttitude.MYSTERIOUS: "An enigmatic figure with a hidden past and unclear motives.",
            NPCAttitude.ARROGANT: "Someone who believes themselves superior to others and looks down on common folk.",
            NPCAttitude.WISE: "An experienced individual who has seen much of the world and learned from it."
        }

        return backgrounds.get(attitude, "A person with their own story and motivations.")

    def _generate_npc_motivation(self, attitude: NPCAttitude) -> str:
        """Generate NPC motivation for seeking help"""
        motivations = {
            NPCAttitude.FRIENDLY: "Wants to help the community and believes working together is the answer.",
            NPCAttitude.NEUTRAL: "Seeks practical solutions to everyday problems affecting everyone.",
            NPCAttitude.SUSPICIOUS: "Needs help but is wary of being betrayed or taken advantage of.",
            NPCAttitude.HOSTILE: "Reluctantly admits they need assistance, though it pains them to ask.",
            NPCAttitude.DESPERATE: "Has exhausted all other options and is willing to try anything.",
            NPCAttitude.MYSTERIOUS: "Offers a task but keeps their true reasons hidden.",
            NPCAttitude.ARROGANT: "Believes only someone of sufficient skill is worthy of their task.",
            NPCAttitude.WISE: "Recognizes the gravity of the situation and seeks capable assistance."
        }

        return motivations.get(attitude, "Has a problem that needs solving.")

# Utility functions
def create_sample_context() -> WorldContext:
    """Create sample world context for testing"""
    context = WorldContext()

    # Add sample locations
    context.locations = {
        "Village Square": {"type": "settlement", "population": 500, "danger": 0.1},
        "Dark Forest": {"type": "forest", "population": 0, "danger": 0.7},
        "Abandoned Mine": {"type": "dungeon", "population": 0, "danger": 0.8},
        "Merchant's Guild": {"type": "building", "population": 50, "danger": 0.2},
        "Ancient Ruins": {"type": "ruins", "population": 0, "danger": 0.9}
    }

    # Add sample events
    context.events = [
        "Goblin sightings in the Dark Forest",
        "Trade caravan missing near Ancient Ruins",
        "Strange lights at Abandoned Mine"
    ]

    context.player_level = 10
    context.player_location = (25, 25)

    return context

def analyze_quests(quests: List[Quest]) -> Dict:
    """Analyze generated quests"""
    analysis = {
        'total_quests': len(quests),
        'quest_types': defaultdict(int),
        'difficulty_distribution': defaultdict(int),
        'status_distribution': defaultdict(int),
        'avg_objectives': 0,
        'avg_rewards': 0,
        'time_sensitive': 0,
        'story_beats': 0,
        'unique_quest_givers': set(),
        'total_world_impact': 0
    }

    total_objectives = 0
    total_rewards = 0
    total_impact = 0

    for quest in quests:
        analysis['quest_types'][quest.quest_type.value] += 1
        analysis['difficulty_distribution'][quest.difficulty.value] += 1
        analysis['status_distribution'][quest.status.value] += 1

        total_objectives += len(quest.objectives)
        total_rewards += len(quest.rewards)
        total_impact += len(quest.world_impact)

        if quest.time_sensitive:
            analysis['time_sensitive'] += 1
        if quest.story_beat:
            analysis['story_beats'] += 1

        analysis['unique_quest_givers'].add(quest.quest_giver.name)

    if quests:
        analysis['avg_objectives'] = total_objectives / len(quests)
        analysis['avg_rewards'] = total_rewards / len(quests)
        analysis['total_world_impact'] = total_impact
        analysis['unique_quest_givers'] = len(analysis['unique_quest_givers'])

    return analysis

if __name__ == "__main__":
    # Example usage
    print("Initializing Quest Weaver...")
    quest_weaver = QuestWeaver(seed=42)

    # Create sample context
    context = create_sample_context()

    # Generate some quest givers
    quest_givers = []
    for i in range(3):
        location = (random.randint(0, 50), random.randint(0, 50))
        quest_giver = quest_weaver.generate_quest_giver(location, context)
        quest_givers.append(quest_giver)

    print(f"\nGenerated {len(quest_givers)} quest givers:")
    for qg in quest_givers:
        print(f"  - {qg.name} ({qg.quest_giver_type}) at {qg.location}")

    # Generate individual quests
    print("\nGenerating individual quests...")
    individual_quests = []
    quest_types = [QuestType.RESCUE, QuestType.COLLECTION, QuestType.BOSS_HUNT, QuestType.INVESTIGATION]

    for quest_type in quest_types:
        quest_giver = random.choice(quest_givers)
        quest = quest_weaver.generate_quest(quest_type, quest_giver, context)
        individual_quests.append(quest)
        print(f"  - {quest.title} ({quest.quest_type.value}, {quest.difficulty.value})")

    # Generate story arc
    print("\nGenerating story arc...")
    story_arc = quest_weaver.generate_story_arc(
        theme="mystery",
        num_quests=4,
        quest_givers=quest_givers,
        context=context
    )
    print(f"  - {story_arc.name}: {story_arc.description}")
    print(f"    Quests: {len(story_arc.quest_ids)}")

    # Analyze all quests
    all_quests = individual_quests
    for quest_id in story_arc.quest_ids:
        if quest_id in quest_weaver.generated_quests:
            all_quests.append(quest_weaver.generated_quests[quest_id])

    analysis = analyze_quests(all_quests)
    print(f"\nQuest Analysis:")
    print(f"  Total quests: {analysis['total_quests']}")
    print(f"  Average objectives per quest: {analysis['avg_objectives']:.1f}")
    print(f"  Average rewards per quest: {analysis['avg_rewards']:.1f}")
    print(f"  Time-sensitive quests: {analysis['time_sensitive']}")
    print(f"  Story-critical quests: {analysis['story_beats']}")
    print(f"  Unique quest givers: {analysis['unique_quest_givers']}")
    print(f"  Total world impact points: {analysis['total_world_impact']}")

    print(f"\nQuest type distribution:")
    for qtype, count in analysis['quest_types'].items():
        print(f"  {qtype}: {count}")

    print(f"\nDifficulty distribution:")
    for diff, count in analysis['difficulty_distribution'].items():
        print(f"  {diff}: {count}")