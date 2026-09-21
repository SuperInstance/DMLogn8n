"""
Advanced Quest Generation System for DMLogn8n
Implements dynamic quest generation with narrative coherence and player adaptation
"""

import random
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math

class QuestType(Enum):
    """Types of quests with different gameplay mechanics"""
    FETCH = "fetch"
    KILL = "kill"
    ESCORT = "escort"
    INVESTIGATE = "investigate"
    DELIVER = "deliver"
    RESCUE = "rescue"
    DIPLOMATIC = "diplomatic"
    EXPLORATION = "exploration"
    CRAFTING = "crafting"
    PUZZLE = "puzzle"
    SURVIVAL = "survival"
    DEFENSE = "defense"
    STEALTH = "stealth"
    SOCIAL = "social"

class QuestDifficulty(Enum):
    """Quest difficulty levels with appropriate rewards"""
    TRIVIAL = 1
    EASY = 2
    NORMAL = 3
    CHALLENGING = 4
    HARD = 5
    EXPERT = 6
    MASTER = 7
    LEGENDARY = 8

class QuestStatus(Enum):
    """Quest progression states"""
    AVAILABLE = "available"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"

@dataclass
class QuestObjective:
    """Individual quest objective with tracking"""
    id: str
    description: str
    type: str
    target: str
    current: int = 0
    required: int = 1
    optional: bool = False
    hidden: bool = False
    completed: bool = False

    def progress(self, amount: int = 1):
        """Progress objective"""
        if not self.completed:
            self.current = min(self.current + amount, self.required)
            self.completed = self.current >= self.required
        return self.completed

    def progress_percentage(self) -> float:
        """Get completion percentage"""
        return (self.current / self.required) * 100 if self.required > 0 else 0

@dataclass
class QuestReward:
    """Quest reward structure"""
    experience: int = 0
    gold: int = 0
    reputation: Dict[str, int] = field(default_factory=dict)
    items: List[Dict[str, Any]] = field(default_factory=list)
    skill_experience: Dict[str, int] = field(default_factory=dict)
    quest_unlocks: List[str] = field(default_factory=list)
    special_rewards: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Quest:
    """Complete quest structure"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty
    level_requirement: int
    objectives: List[QuestObjective]
    rewards: QuestReward
    status: QuestStatus = QuestStatus.AVAILABLE
    time_limit: Optional[timedelta] = None
    start_time: Optional[datetime] = None
    prerequisites: List[str] = field(default_factory=list)
    mutually_exclusive: List[str] = field(default_factory=list)
    repeatable: bool = False
    daily: bool = False
    weekly: bool = False
    seasonal: bool = False

    # Narrative elements
    giver: Optional[str] = None
    giver_dialogue: List[str] = field(default_factory=list)
    completion_dialogue: List[str] = field(default_factory=list)
    failure_dialogue: List[str] = field(default_factory=list)
    lore_tags: List[str] = field(default_factory=list)

    # Dynamic elements
    world_state_requirements: Dict[str, Any] = field(default_factory=dict)
    world_state_changes: Dict[str, Any] = field(default_factory=dict)
    player_choices: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if quest has expired"""
        if self.time_limit and self.start_time:
            return datetime.now() > self.start_time + self.time_limit
        return False

    def can_accept(self, player_level: int, world_state: Dict[str, Any],
                   completed_quests: List[str]) -> bool:
        """Check if player can accept this quest"""
        if self.status != QuestStatus.AVAILABLE:
            return False
        if player_level < self.level_requirement:
            return False
        if self.is_expired():
            return False

        # Check prerequisites
        for prereq in self.prerequisites:
            if prereq not in completed_quests:
                return False

        # Check world state requirements
        for key, value in self.world_state_requirements.items():
            if world_state.get(key) != value:
                return False

        return True

    def update_objective(self, objective_id: str, amount: int = 1) -> bool:
        """Update objective progress"""
        for obj in self.objectives:
            if obj.id == objective_id:
                return obj.progress(amount)
        return False

    def is_completed(self) -> bool:
        """Check if all required objectives are complete"""
        required_objectives = [obj for obj in self.objectives if not obj.optional]
        return all(obj.completed for obj in required_objectives)

    def get_completion_percentage(self) -> float:
        """Get overall quest completion percentage"""
        if not self.objectives:
            return 0.0

        required_objectives = [obj for obj in self.objectives if not obj.optional]
        if not required_objectives:
            return 100.0

        total_progress = sum(obj.progress_percentage() for obj in required_objectives)
        return total_progress / len(required_objectives)

class QuestGenerator:
    """Advanced quest generation with narrative coherence"""

    def __init__(self):
        self.quest_templates = self._load_quest_templates()
        self.narrative_chains = self._load_narrative_chains()
        self.quest_history: List[Dict[str, Any]] = []
        self.quest_variations = {}
        self.dynamic_quest_pool = []

    def _load_quest_templates(self) -> Dict[str, Dict]:
        """Load quest templates with narrative hooks"""
        return {
            "fetch_quest": {
                "template": "Retrieve {item} from {location} for {giver}",
                "objectives": [
                    {"type": "travel", "description": "Travel to {location}"},
                    {"type": "fetch", "description": "Find and retrieve {item}"},
                    {"type": "return", "description": "Return to {giver}"}
                ],
                "lore_tags": ["retrieval", "travel", "merchant"],
                "difficulty_modifiers": {"distance": 0.3, "danger": 0.4, "item_rarity": 0.3}
            },
            "kill_quest": {
                "template": "Eliminate {enemy} threatening {location}",
                "objectives": [
                    {"type": "travel", "description": "Travel to {location}"},
                    {"type": "kill", "description": "Defeat {count} {enemy}"},
                    {"type": "optional", "description": "Collect proof of defeat"}
                ],
                "lore_tags": ["combat", "monster", "protection"],
                "difficulty_modifiers": {"enemy_strength": 0.5, "enemy_count": 0.3, "terrain": 0.2}
            },
            "investigation_quest": {
                "template": "Investigate {mystery} at {location}",
                "objectives": [
                    {"type": "travel", "description": "Go to {location}"},
                    {"type": "investigate", "description": "Search for clues about {mystery}"},
                    {"type": "analyze", "description": "Analyze findings"},
                    {"type": "report", "description": "Report findings to {giver}"}
                ],
                "lore_tags": ["mystery", "investigation", "knowledge"],
                "difficulty_modifiers": {"complexity": 0.4, "dangers": 0.3, "clue_rarity": 0.3}
            },
            "escort_quest": {
                "template": "Escort {npc} safely to {destination}",
                "objectives": [
                    {"type": "meet", "description": "Meet {npc} at {start_location}"},
                    {"type": "escort", "description": "Protect {npc} during travel"},
                    {"type": "deliver", "description": "Ensure {npc} reaches {destination}"}
                ],
                "lore_tags": ["escort", "protection", "travel"],
                "difficulty_modifiers": {"distance": 0.3, "threats": 0.5, "npc_importance": 0.2}
            },
            "diplomatic_quest": {
                "template": "Negotiate with {faction} about {issue}",
                "objectives": [
                    {"type": "meet", "description": "Meet {faction_representative}"},
                    {"type": "negotiate", "description": "Discuss {issue}"},
                    {"type": "persuade", "description": "Reach an agreement"},
                    {"type": "report", "description": "Report outcome to {giver}"}
                ],
                "lore_tags": ["diplomacy", "negotiation", "politics"],
                "difficulty_modifiers": {"faction_attitude": 0.4, "issue_complexity": 0.4, "stakes": 0.2}
            }
        }

    def _load_narrative_chains(self) -> Dict[str, List[Dict]]:
        """Load narrative chains for quest series"""
        return {
            "rising_threat": [
                {"stage": 1, "type": "investigation", "scope": "local"},
                {"stage": 2, "type": "combat", "scope": "regional"},
                {"stage": 3, "type": "diplomatic", "scope": "kingdom"},
                {"stage": 4, "type": "epic_combat", "scope": "world"}
            ],
            "political_intrigue": [
                {"stage": 1, "type": "social", "scope": "local"},
                {"stage": 2, "type": "investigation", "scope": "regional"},
                {"stage": 3, "type": "diplomatic", "scope": "kingdom"},
                {"stage": 4, "type": "resolution", "scope": "kingdom"}
            ],
            "ancient_mystery": [
                {"stage": 1, "type": "exploration", "scope": "local"},
                {"stage": 2, "type": "puzzle", "scope": "dungeon"},
                {"stage": 3, "type": "investigation", "scope": "ancient"},
                {"stage": 4, "type": "epic", "scope": "world"}
            ]
        }

    def generate_quest(self,
                      player_level: int,
                      quest_type: Optional[QuestType] = None,
                      difficulty: Optional[QuestDifficulty] = None,
                      world_state: Dict[str, Any] = None,
                      player_history: List[str] = None,
                      narrative_context: Optional[str] = None) -> Quest:
        """Generate a dynamic quest based on parameters"""

        if world_state is None:
            world_state = {}
        if player_history is None:
            player_history = []

        # Select appropriate quest template
        template_name = self._select_quest_template(quest_type, player_level, world_state)
        template = self.quest_templates[template_name]

        # Generate quest details
        quest_details = self._generate_quest_details(
            template, player_level, world_state, player_history, narrative_context
        )

        # Create objectives
        objectives = self._create_objectives(template, quest_details)

        # Generate rewards
        rewards = self._generate_rewards(
            quest_details["difficulty"], player_level, len(objectives)
        )

        # Generate dialogues
        dialogues = self._generate_dialogues(quest_details, template)

        # Create quest
        quest = Quest(
            id=str(uuid.uuid4()),
            title=quest_details["title"],
            description=quest_details["description"],
            quest_type=QuestType(template_name.replace("_quest", "")),
            difficulty=quest_details["difficulty"],
            level_requirement=quest_details["level_requirement"],
            objectives=objectives,
            rewards=rewards,
            giver=quest_details["giver"],
            giver_dialogue=dialogues["giver"],
            completion_dialogue=dialogues["completion"],
            failure_dialogue=dialogues["failure"],
            lore_tags=template["lore_tags"],
            world_state_requirements=quest_details.get("requirements", {}),
            world_state_changes=quest_details.get("changes", {}),
            prerequisites=quest_details.get("prerequisites", [])
        )

        # Add to quest history for coherence tracking
        self.quest_history.append({
            "quest_id": quest.id,
            "type": quest.quest_type.value,
            "difficulty": quest.difficulty.value,
            "player_level": player_level,
            "generated_at": datetime.now().isoformat()
        })

        return quest

    def _select_quest_template(self,
                              quest_type: Optional[QuestType],
                              player_level: int,
                              world_state: Dict[str, Any]) -> str:
        """Select appropriate quest template based on parameters"""

        if quest_type:
            template_name = f"{quest_type.value}_quest"
            if template_name in self.quest_templates:
                return template_name

        # Context-aware template selection
        templates = list(self.quest_templates.keys())

        # Consider world state for thematic selection
        if world_state.get("war_active", False):
            if "combat_quest" in templates:
                return "combat_quest"
        elif world_state.get("mystery_active", False):
            if "investigation_quest" in templates:
                return "investigation_quest"
        elif world_state.get("trade_active", False):
            if "fetch_quest" in templates:
                return "fetch_quest"

        # Weighted random selection based on player level
        weights = []
        for template_name in templates:
            template = self.quest_templates[template_name]
            # Higher level players get more variety
            base_weight = 1.0
            if player_level > 20:
                base_weight += 0.5
            if player_level > 40:
                base_weight += 0.5
            weights.append(base_weight)

        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        return random.choices(templates, weights=weights)[0]

    def _generate_quest_details(self,
                               template: Dict,
                               player_level: int,
                               world_state: Dict[str, Any],
                               player_history: List[str],
                               narrative_context: Optional[str]) -> Dict:
        """Generate specific details for a quest"""

        # Calculate difficulty based on player level
        difficulty = self._calculate_quest_difficulty(player_level, template)

        # Generate quest components
        components = {
            "item": self._generate_item(difficulty),
            "location": self._generate_location(difficulty, world_state),
            "enemy": self._generate_enemy(difficulty, world_state),
            "npc": self._generate_npc(difficulty, world_state),
            "giver": self._generate_giver(difficulty, world_state),
            "mystery": self._generate_mystery(difficulty, world_state),
            "faction": self._generate_faction(difficulty, world_state),
            "issue": self._generate_issue(difficulty, world_state),
            "destination": self._generate_destination(difficulty, world_state)
        }

        # Fill template
        title = template["template"].format(**components)

        # Generate description
        description = self._generate_description(template, components, difficulty, narrative_context)

        # Calculate level requirement
        level_requirement = max(1, player_level - random.randint(1, 3))

        # Generate world state changes
        changes = self._generate_world_state_changes(template, components)

        return {
            "title": title,
            "description": description,
            "difficulty": difficulty,
            "level_requirement": level_requirement,
            "components": components,
            "requirements": self._generate_requirements(template, components),
            "changes": changes,
            "prerequisites": self._generate_prerequisites(template, player_history),
            "giver": components["giver"]
        }

    def _calculate_quest_difficulty(self, player_level: int, template: Dict) -> QuestDifficulty:
        """Calculate appropriate difficulty for the quest"""

        # Base difficulty from player level
        base_difficulty = min(8, max(1, (player_level // 10) + 1))

        # Apply template modifiers
        modifiers = template.get("difficulty_modifiers", {})
        difficulty_modifier = sum(modifiers.values()) / len(modifiers) if modifiers else 0

        # Adjust with randomization
        final_difficulty = base_difficulty + random.uniform(-1, 1) + difficulty_modifier

        # Clamp to valid range
        final_difficulty = max(1, min(8, int(final_difficulty)))

        return QuestDifficulty(final_difficulty)

    def _generate_item(self, difficulty: QuestDifficulty) -> str:
        """Generate item for quest"""
        items = {
            QuestDifficulty.TRIVIAL: ["rusty key", "old map", "common herb", "simple tool"],
            QuestDifficulty.EASY: ["silver ring", "healing potion", "enchanted stone", "merchant ledger"],
            QuestDifficulty.NORMAL: ["golden amulet", "rare spellbook", "ancient artifact", "family heirloom"],
            QuestDifficulty.CHALLENGING: ["magic sword", "dragon scale", "ancient tome", "royal seal"],
            QuestDifficulty.HARD: ["legendary weapon", "divine artifact", "ancient crown", "magic crystal"],
            QuestDifficulty.EXPERT: ["epic armor", "mythical item", "ancient relic", "powerful talisman"],
            QuestDifficulty.MASTER: ["godly weapon", "ancient magic", "divine instrument", "mythical treasure"],
            QuestDifficulty.LEGENDARY: ["world-shaping artifact", "divine weapon", "ancient power", "legendary treasure"]
        }
        return random.choice(items.get(difficulty, items[QuestDifficulty.NORMAL]))

    def _generate_location(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate location for quest"""
        locations = {
            QuestDifficulty.TRIVIAL: ["local tavern", "town square", "nearby forest", "village outskirts"],
            QuestDifficulty.EASY: ["abandoned farm", "old mine", "neighboring village", "forest ruins"],
            QuestDifficulty.NORMAL: ["ancient ruins", "dark cave", "bandit camp", "mysterious grove"],
            QuestDifficulty.CHALLENGING: ["monster lair", "fortress ruins", "forbidden temple", "enchanted forest"],
            QuestDifficulty.HARD: ["dragon's den", "lava caves", "underground city", "cursed lands"],
            QuestDifficulty.EXPERT: ["demon fortress", "ancient library", "celestial realm", "underworld gate"],
            QuestDifficulty.MASTER: ["god's domain", "timeless dimension", "elemental plane", "ancient battlefield"],
            QuestDifficulty.LEGENDARY: ["world's core", "creation forge", "divine realm", "cosmic nexus"]
        }
        return random.choice(locations.get(difficulty, locations[QuestDifficulty.NORMAL]))

    def _generate_enemy(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate enemy for quest"""
        enemies = {
            QuestDifficulty.TRIVIAL: ["giant rat", "wild wolf", "thug", "angry villager"],
            QuestDifficulty.EASY: ["goblin scout", "bandit", "wild boar", "lesser undead"],
            QuestDifficulty.NORMAL: ["orc warrior", "dark wizard", "giant spider", "cursed knight"],
            QuestDifficulty.CHALLENGING: ["dragon whelp", "demon servant", "elemental", "assassin"],
            QuestDifficulty.HARD: ["adult dragon", "lich lord", "giant golem", "demon commander"],
            QuestDifficulty.EXPERT: ["ancient dragon", "archdemon", "elemental lord", "undead king"],
            QuestDifficulty.MASTER: ["divine beast", "primordial entity", "cosmic horror", "ancient evil"],
            QuestDifficulty.LEGENDARY: ["world serpent", "destroyer", "creator's foe", "ultimate evil"]
        }
        return random.choice(enemies.get(difficulty, enemies[QuestDifficulty.NORMAL]))

    def _generate_npc(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate NPC for quest"""
        npcs = {
            QuestDifficulty.TRIVIAL: ["local farmer", "merchant's assistant", "village child", "town guard"],
            QuestDifficulty.EASY: ["traveling merchant", "scholar's apprentice", "healer", "scout"],
            QuestDifficulty.NORMAL: ["noble", "captain", "advisor", "artisan"],
            QuestDifficulty.CHALLENGING: ["prince", "ambassador", "master craftsman", "wizard"],
            QuestDifficulty.HARD: ["king", "archmage", "guild master", "high priest"],
            QuestDifficulty.EXPERT: ["emperor", "divine messenger", "ancient sage", "celestial being"],
            QuestDifficulty.MASTER: ["demigod", "ancient ruler", "cosmic entity", "divine oracle"],
            QuestDifficulty.LEGENDARY: ["god", "creator", "world spirit", "ultimate being"]
        }
        return random.choice(npcs.get(difficulty, npcs[QuestDifficulty.NORMAL]))

    def _generate_giver(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate quest giver"""
        givers = [
            "Old Man Thomas", "Captain Maria", "Wizard Eldrin", "Merchant James",
            "Priestess Sarah", "Blacksmith John", "Scholar Marcus", "Guard Captain",
            "Mayor William", "Healer Anna", "Explorer Robert", "Innkeeper Lisa"
        ]
        return random.choice(givers)

    def _generate_mystery(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate mystery for investigation quests"""
        mysteries = {
            QuestDifficulty.TRIVIAL: ["missing cat", "strange noises", "stolen bread", "ghost story"],
            QuestDifficulty.EASY: ["missing person", "strange illness", "crop failure", "local legend"],
            QuestDifficulty.NORMAL: ["disappearances", "magical plague", "ancient curse", "hidden treasure"],
            QuestDifficulty.CHALLENGING: ["conspiracy", "dark cult", "magical anomaly", "forbidden magic"],
            QuestDifficulty.HARD: ["demonic pact", "ancient evil", "prophecy fulfillment", "realm invasion"],
            QuestDifficulty.EXPERT: ["divine intervention", "time paradox", "dimensional breach", "cosmic alignment"],
            QuestDifficulty.MASTER: ["creation mystery", "divine conspiracy", "reality distortion", "ancient war"],
            QuestDifficulty.LEGENDARY: ["world origin", "divine conflict", "multiverse connection", "ultimate truth"]
        }
        return random.choice(mysteries.get(difficulty, mysteries[QuestDifficulty.NORMAL]))

    def _generate_faction(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate faction for diplomatic quests"""
        factions = [
            "Merchants Guild", "Mages Council", "Warrior Brotherhood", "Thieves Guild",
            "Royal Court", "Church of Light", "Shadow Syndicate", "Nature Wardens",
            "Dragon Knights", "Ancient Order", "Merchant Alliance", "Border Patrol"
        ]
        return random.choice(factions)

    def _generate_issue(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate issue for diplomatic quests"""
        issues = [
            "trade dispute", "border conflict", "resource sharing", "magical artifacts",
            "territorial claims", "ancient treaties", "peace negotiations", "alliance proposals",
            "refugee crisis", "magical contamination", "monster threats", "economic sanctions"
        ]
        return random.choice(issues)

    def _generate_destination(self, difficulty: QuestDifficulty, world_state: Dict[str, Any]) -> str:
        """Generate destination for travel quests"""
        destinations = [
            "royal capital", "sacred temple", "ancient library", "trading post",
            "military fortress", "magical academy", "holy shrine", "border town",
            "port city", "mountain monastery", "desert oasis", "forest sanctuary"
        ]
        return random.choice(destinations)

    def _generate_description(self,
                             template: Dict,
                             components: Dict,
                             difficulty: QuestDifficulty,
                             narrative_context: Optional[str]) -> str:
        """Generate quest description with narrative coherence"""

        base_descriptions = {
            "fetch_quest": [
                "The {giver} desperately needs help retrieving a {item} from {location}. "
                "They mention that time is of the essence and the item holds great importance "
                "to both them and the community.",

                "Word has reached {giver} about a valuable {item} hidden in {location}. "
                "They're willing to pay well for its safe return, but warn of the dangers "
                "that guard the location.",

                "An urgent request comes from {giver} regarding a {item} in {location}. "
                "They speak of ancient powers and mysterious forces surrounding the item."
            ],
            "kill_quest": [
                "The people are terrorized by {enemy} near {location}. {giver} seeks a "
                "brave adventurer to eliminate this threat before more harm comes to the innocent.",

                "Reports speak of {enemy} causing chaos around {location}. {giver} has "
                "offered a substantial reward for anyone who can deal with this menace.",

                "A grave danger emerges as {enemy} establishes territory near {location}. "
                "{giver} believes only a skilled warrior can face this threat and emerge victorious."
            ],
            "investigation_quest": [
                "Strange occurrences have been reported around {mystery} in {location}. "
                "{giver} needs someone with keen investigative skills to uncover the truth "
                "behind these mysterious events.",

                "The {mystery} at {location} has caught the attention of {giver}. "
                "They suspect something sinister is at play and require thorough investigation "
                "to reveal what's really happening.",

                "Local authorities are baffled by the {mystery} plaguing {location}. "
                "{giver} believes an independent investigator might uncover clues others have missed."
            ],
            "escort_quest": [
                "{npc} requires safe passage to {destination}, but the journey is perilous. "
                "{giver} has hired protection for this important mission that could affect "
                "the fate of many.",

                "A crucial mission involves escorting {npc} to {destination}. {giver} warns "
                "that many would seek to prevent this journey, making skilled protection essential.",

                "The safety of {npc} is paramount as they travel to {destination}. {giver} "
                "has chosen only the most capable guardians for this vital task that carries "
                "great consequences."
            ],
            "diplomatic_quest": [
                "Tensions rise between the kingdom and {faction} over {issue}. {giver} believes "
                "a skilled diplomat might resolve this conflict before it escalates to violence.",

                "The {faction} has requested negotiations regarding {issue}. {giver} seeks "
                "someone with diplomatic expertise to handle these delicate discussions that "
                "could shape the future of the realm.",

                "A diplomatic crisis looms as {issue} creates friction with {faction}. "
                "{giver} needs an ambassador who can navigate these treacherous political waters "
                "and secure a peaceful resolution."
            ]
        }

        template_type = template.get("template_type", "fetch_quest")
        descriptions = base_descriptions.get(template_type, base_descriptions["fetch_quest"])

        # Add context from narrative context if provided
        if narrative_context:
            context_addition = f"\n\nThis quest connects to ongoing events: {narrative_context}"
            base_desc = random.choice(descriptions) + context_addition
        else:
            base_desc = random.choice(descriptions)

        # Add difficulty flavor
        difficulty_flavors = {
            QuestDifficulty.TRIVIAL: "This should be a straightforward task.",
            QuestDifficulty.EASY: "The challenge is modest but not without risk.",
            QuestDifficulty.NORMAL: "This requires skill and courage to complete successfully.",
            QuestDifficulty.CHALLENGING: "Only experienced adventurers should attempt this quest.",
            QuestDifficulty.HARD: "This quest will test the limits of even the most skilled heroes.",
            QuestDifficulty.EXPERT: "Legendary courage and skill are needed for this endeavor.",
            QuestDifficulty.MASTER: "This quest borders on the impossible and will require everything.",
            QuestDifficulty.LEGENDARY: "A task of mythic proportions that will be remembered for ages."
        }

        return base_desc + "\n\n" + difficulty_flavors.get(difficulty, "")

    def _create_objectives(self, template: Dict, quest_details: Dict) -> List[QuestObjective]:
        """Create quest objectives from template"""
        objectives = []
        components = quest_details["components"]

        for i, obj_template in enumerate(template["objectives"]):
            description = obj_template["description"].format(**components)

            objective = QuestObjective(
                id=f"obj_{i+1}",
                description=description,
                type=obj_template["type"],
                target=obj_template.get("target", components.get("enemy", components.get("item", ""))),
                required=obj_template.get("count", 1),
                optional=obj_template.get("optional", False),
                hidden=obj_template.get("hidden", False)
            )

            objectives.append(objective)

        return objectives

    def _generate_rewards(self,
                         difficulty: QuestDifficulty,
                         player_level: int,
                         objective_count: int) -> QuestReward:
        """Generate appropriate quest rewards"""

        difficulty_multiplier = difficulty.value
        level_multiplier = 1 + (player_level / 50)
        objective_multiplier = 1 + (objective_count * 0.1)

        base_multiplier = difficulty_multiplier * level_multiplier * objective_multiplier

        rewards = QuestReward(
            experience=int(100 * base_multiplier),
            gold=int(50 * base_multiplier),
            reputation=random.choice([
                {"Merchants Guild": random.randint(5, 20) * difficulty_multiplier},
                {"Royal Court": random.randint(3, 15) * difficulty_multiplier},
                {"Mages Council": random.randint(5, 18) * difficulty_multiplier},
                {"Warrior Brotherhood": random.randint(8, 25) * difficulty_multiplier}
            ]),
            items=self._generate_reward_items(difficulty, player_level),
            skill_experience=self._generate_skill_rewards(difficulty, player_level)
        )

        return rewards

    def _generate_reward_items(self, difficulty: QuestDifficulty, player_level: int) -> List[Dict[str, Any]]:
        """Generate reward items based on difficulty and player level"""
        items = []

        if difficulty.value >= 3:  # Normal difficulty and above
            item_count = min(3, 1 + (difficulty.value // 3))

            for _ in range(item_count):
                item = {
                    "name": self._generate_item(difficulty),
                    "type": random.choice(["weapon", "armor", "accessory", "consumable", "material"]),
                    "rarity": self._get_rarity_for_difficulty(difficulty),
                    "level_requirement": max(1, player_level - random.randint(1, 5)),
                    "value": random.randint(10, 100) * difficulty.value
                }
                items.append(item)

        return items

    def _get_rarity_for_difficulty(self, difficulty: QuestDifficulty) -> str:
        """Get item rarity based on quest difficulty"""
        rarity_map = {
            QuestDifficulty.TRIVIAL: "common",
            QuestDifficulty.EASY: "common",
            QuestDifficulty.NORMAL: "uncommon",
            QuestDifficulty.CHALLENGING: "rare",
            QuestDifficulty.HARD: "rare",
            QuestDifficulty.EXPERT: "epic",
            QuestDifficulty.MASTER: "legendary",
            QuestDifficulty.LEGENDARY: "mythic"
        }
        return rarity_map.get(difficulty, "common")

    def _generate_skill_rewards(self, difficulty: QuestDifficulty, player_level: int) -> Dict[str, int]:
        """Generate skill experience rewards"""
        base_exp = 25 * difficulty.value

        skills = ["combat", "magic", "stealth", "social", "crafting", "survival"]
        selected_skills = random.sample(skills, random.randint(1, 3))

        return {skill: base_exp for skill in selected_skills}

    def _generate_dialogues(self, quest_details: Dict, template: Dict) -> Dict[str, List[str]]:
        """Generate quest dialogues"""
        giver = quest_details["giver"]
        components = quest_details["components"]
        difficulty = quest_details["difficulty"]

        giver_dialogue = [
            f"Ah, adventurer! I have an urgent matter that requires your attention.",
            f"Greetings. I am {giver}, and I come to you with an important request.",
            f"Your reputation precedes you. I need someone of your considerable skill."
        ]

        completion_dialogue = [
            "You've done it! This is exactly what was needed. The realm is safer thanks to you.",
            "Outstanding work! Your efforts have made a real difference.",
            "You've exceeded all expectations. This will be remembered."
        ]

        failure_dialogue = [
            "I understand that not all endeavors succeed. Perhaps another time.",
            "The task proved too challenging. There's no shame in this.",
            "Fortune was not with us this day. The threat remains."
        ]

        return {
            "giver": giver_dialogue,
            "completion": completion_dialogue,
            "failure": failure_dialogue
        }

    def _generate_requirements(self, template: Dict, components: Dict) -> Dict[str, Any]:
        """Generate world state requirements for quest"""
        requirements = {}

        # Sample requirements based on template
        if template["template_type"] == "kill_quest":
            requirements["monster_threat"] = True
        elif template["template_type"] == "diplomatic_quest":
            requirements["faction_active"] = components["faction"]
        elif template["template_type"] == "investigation_quest":
            requirements["mystery_available"] = True

        return requirements

    def _generate_world_state_changes(self, template: Dict, components: Dict) -> Dict[str, Any]:
        """Generate world state changes upon quest completion"""
        changes = {}

        if template["template_type"] == "kill_quest":
            changes["monster_threat"] = False
            changes["region_safety"] = "improved"
        elif template["template_type"] == "diplomatic_quest":
            changes[f"relation_{components['faction']}"] = "improved"
        elif template["template_type"] == "fetch_quest":
            changes["item_recovered"] = components["item"]

        return changes

    def _generate_prerequisites(self, template: Dict, player_history: List[str]) -> List[str]:
        """Generate quest prerequisites based on player history"""
        prerequisites = []

        # Sometimes require previous similar quests
        if random.random() < 0.3 and player_history:
            similar_quests = [q for q in player_history if q["type"] == template["template_type"]]
            if similar_quests:
                prerequisites.append(random.choice(similar_quests)["quest_id"])

        return prerequisites

    def generate_quest_chain(self,
                           player_level: int,
                           chain_type: str,
                           world_state: Dict[str, Any]) -> List[Quest]:
        """Generate a chain of related quests"""

        if chain_type not in self.narrative_chains:
            chain_type = random.choice(list(self.narrative_chains.keys()))

        chain = self.narrative_chains[chain_type]
        quests = []

        for stage in chain:
            quest = self.generate_quest(
                player_level=player_level + (stage["stage"] - 1) * 5,
                quest_type=QuestType(stage["type"]),
                world_state=world_state,
                narrative_context=f"{chain_type} chain - stage {stage['stage']}"
            )

            # Add prerequisites from previous stage
            if quests:
                quest.prerequisites.append(quests[-1].id)

            quests.append(quest)

        return quests

    def get_available_quests(self,
                            player_level: int,
                            world_state: Dict[str, Any],
                            completed_quests: List[str],
                            max_quests: int = 10) -> List[Quest]:
        """Get list of available quests for player"""

        available_quests = []

        # Generate new quests if needed
        while len(self.dynamic_quest_pool) < max_quests:
            quest = self.generate_quest(player_level, world_state=world_state)
            self.dynamic_quest_pool.append(quest)

        # Filter available quests
        for quest in self.dynamic_quest_pool:
            if quest.can_accept(player_level, world_state, completed_quests):
                available_quests.append(quest)

        return available_quests[:max_quests]

    def update_quest_status(self, quest_id: str, new_status: QuestStatus):
        """Update quest status and handle consequences"""

        # Find and update quest in dynamic pool
        for quest in self.dynamic_quest_pool:
            if quest.id == quest_id:
                old_status = quest.status
                quest.status = new_status

                # Handle status change consequences
                if new_status == QuestStatus.COMPLETED and old_status == QuestStatus.ACTIVE:
                    self._handle_quest_completion(quest)
                elif new_status == QuestStatus.FAILED:
                    self._handle_quest_failure(quest)

                break

    def _handle_quest_completion(self, quest: Quest):
        """Handle consequences of quest completion"""
        # Update world state
        for key, value in quest.world_state_changes.items():
            # This would interface with the world state management system
            pass

        # Remove from active pool if not repeatable
        if not quest.repeatable:
            if quest in self.dynamic_quest_pool:
                self.dynamic_quest_pool.remove(quest)

        # Generate follow-up quests if appropriate
        if random.random() < 0.3:  # 30% chance of follow-up
            follow_up = self.generate_quest(
                player_level=quest.level_requirement + 5,
                narrative_context=f"Follow-up to: {quest.title}"
            )
            self.dynamic_quest_pool.append(follow_up)

    def _handle_quest_failure(self, quest: Quest):
        """Handle consequences of quest failure"""
        # May generate rescue quests or related content
        if random.random() < 0.2:  # 20% chance of rescue opportunity
            rescue_quest = self.generate_quest(
                player_level=quest.level_requirement - 2,
                narrative_context=f"Rescue opportunity from: {quest.title}"
            )
            self.dynamic_quest_pool.append(rescue_quest)

    def get_quest_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated quests"""
        if not self.quest_history:
            return {}

        quest_types = {}
        difficulties = {}

        for quest in self.quest_history:
            quest_type = quest["type"]
            difficulty = quest["difficulty"]

            quest_types[quest_type] = quest_types.get(quest_type, 0) + 1
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1

        return {
            "total_quests": len(self.quest_history),
            "quest_types": quest_types,
            "difficulty_distribution": difficulties,
            "average_player_level": sum(q["player_level"] for q in self.quest_history) / len(self.quest_history),
            "dynamic_pool_size": len(self.dynamic_quest_pool)
        }

# Example usage and testing
if __name__ == "__main__":
    generator = QuestGenerator()

    # Test quest generation
    quest = generator.generate_quest(
        player_level=15,
        quest_type=QuestType.INVESTIGATE,
        world_state={"mystery_active": True, "war_active": False}
    )

    print(f"Generated Quest: {quest.title}")
    print(f"Description: {quest.description}")
    print(f"Difficulty: {quest.difficulty.name}")
    print(f"Objectives: {len(quest.objectives)}")
    print(f"Rewards: {quest.rewards.experience} XP, {quest.rewards.gold} gold")

    # Test quest chain generation
    chain = generator.generate_quest_chain(player_level=10, chain_type="rising_threat", world_state={})
    print(f"\nGenerated quest chain with {len(chain)} quests")
    for i, q in enumerate(chain):
        print(f"  {i+1}. {q.title} ({q.quest_type.value})")

    # Test statistics
    stats = generator.get_quest_statistics()
    print(f"\nQuest Statistics: {stats}")