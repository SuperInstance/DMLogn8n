#!/usr/bin/env python3
"""
Dynamic Quest Engine for DMLogn8n
Provides branching narratives and adaptive quest systems
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class QuestType(Enum):
    MAIN = "main"
    SIDE = "side"
    DAILY = "daily"
    WEEKLY = "weekly"
    EVENT = "event"
    HIDDEN = "hidden"
    TUTORIAL = "tutorial"

class QuestStatus(Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

class QuestDifficulty(Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"
    LEGENDARY = "legendary"

class ObjectiveType(Enum):
    KILL = "kill"
    COLLECT = "collect"
    DELIVER = "deliver"
    TALK = "talk"
    EXPLORE = "explore"
    ESCORT = "escort"
    CRAFT = "craft"
    SURVIVE = "survive"
    DEFEND = "defend"
    SOLVE = "solve"

class ChoiceType(Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    INVESTIGATION = "investigation"
    MORAL = "moral"
    STRATEGIC = "strategic"

@dataclass
class QuestObjective:
    """Individual quest objective"""
    id: str
    description: str
    type: ObjectiveType
    target: str  # What to kill/collect/talk to etc.
    required_quantity: int = 1
    current_quantity: int = 0
    optional: bool = False
    hidden: bool = False
    time_limit: Optional[int] = None  # seconds
    failure_consequences: List[str] = field(default_factory=list)
    success_rewards: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QuestChoice:
    """Branching choice in quest"""
    id: str
    description: str
    type: ChoiceType
    requirements: Dict[str, Any] = field(default_factory=dict)
    consequences: Dict[str, Any] = field(default_factory=dict)
    next_quest_id: Optional[str] = None
    morality_alignment: Optional[str] = None  # good, evil, neutral
    reputation_changes: Dict[str, int] = field(default_factory=dict)

@dataclass
class Quest:
    """Complete quest definition"""
    id: str
    title: str
    description: str
    quest_type: QuestType
    difficulty: QuestDifficulty
    level_requirement: int = 1
    prerequisites: List[str] = field(default_factory=list)
    objectives: List[QuestObjective] = field(default_factory=list)
    choices: List[QuestChoice] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
    time_limit: Optional[int] = None  # seconds
    repeatable: bool = False
    auto_accept: bool = False
    world_impact: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

@dataclass
class QuestProgress:
    """Player's progress on a quest"""
    quest_id: str
    status: QuestStatus = QuestStatus.LOCKED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    objective_progress: Dict[str, int] = field(default_factory=dict)
    choices_made: List[str] = field(default_factory=list)
    failed_objectives: Set[str] = field(default_factory=set)
    custom_notes: str = ""
    reputation_changes: Dict[str, int] = field(default_factory=dict)

@dataclass
class QuestChain:
    """Connected series of quests"""
    id: str
    name: str
    description: str
    quest_ids: List[str]
    required_completions: int = 1  # How many quests in chain must be completed
    final_reward: Dict[str, Any] = field(default_factory=dict)

class QuestEngine:
    """Dynamic quest management system"""

    def __init__(self):
        self.quests: Dict[str, Quest] = {}
        self.quest_chains: Dict[str, QuestChain] = {}
        self.player_progress: Dict[str, Dict[str, QuestProgress]] = defaultdict(dict)
        self.active_quests: Dict[str, Set[str]] = defaultdict(set)
        self.completed_quests: Dict[str, Set[str]] = defaultdict(set)
        self.world_state: Dict[str, Any] = {}
        self.quest_variables: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.dynamic_quests: Dict[str, Callable] = {}
        self.analytics = QuestAnalytics()

        # Quest generation parameters
        self.difficulty_scaling = {
            QuestDifficulty.TRIVIAL: 0.5,
            QuestDifficulty.EASY: 0.8,
            QuestDifficulty.NORMAL: 1.0,
            QuestDifficulty.HARD: 1.3,
            QuestDifficulty.EXPERT: 1.6,
            QuestDifficulty.LEGENDARY: 2.0
        }

        self._initialize_default_quests()

    def _initialize_default_quests(self):
        """Initialize default quest set"""
        default_quests = [
            Quest(
                id="tutorial_basics",
                title="Welcome to DMLogn8n",
                description="Learn the basics of the game",
                quest_type=QuestType.TUTORIAL,
                difficulty=QuestDifficulty.TRIVIAL,
                level_requirement=1,
                objectives=[
                    QuestObjective(
                        id="talk_guide",
                        description="Speak with the Guide",
                        type=ObjectiveType.TALK,
                        target="guide"
                    ),
                    QuestObjective(
                        id="complete_tutorial_combat",
                        description="Complete the tutorial combat",
                        type=ObjectiveType.KILL,
                        target="training_dummy",
                        required_quantity=3
                    )
                ],
                rewards={
                    "experience": 100,
                    "gold": 50,
                    "items": ["health_potion", "basic_sword"]
                },
                auto_accept=True
            ),
            Quest(
                id="missing_supplies",
                title="Missing Supplies",
                description="Help the merchant find their missing supplies",
                quest_type=QuestType.SIDE,
                difficulty=QuestDifficulty.EASY,
                level_requirement=2,
                prerequisites=["tutorial_basics"],
                objectives=[
                    QuestObjective(
                        id="find_clues",
                        description="Search for clues near the road",
                        type=ObjectiveType.EXPLORE,
                        target="road_location"
                    ),
                    QuestObjective(
                        id="recover_supplies",
                        description="Recover the stolen supplies",
                        type=ObjectiveType.COLLECT,
                        target="supply_crate",
                        required_quantity=5
                    )
                ],
                choices=[
                    QuestChoice(
                        id="keep_supplies",
                        description="Keep some supplies for yourself",
                        type=ChoiceType.MORAL,
                        morality_alignment="neutral",
                        reputation_changes={"merchant": -10, "thieves": 5},
                        next_quest_id="merchant_revenge"
                    ),
                    QuestChoice(
                        id="return_all",
                        description="Return all supplies to the merchant",
                        type=ChoiceType.MORAL,
                        morality_alignment="good",
                        reputation_changes={"merchant": 20, "thieves": -5},
                        next_quest_id="merchant_gratitude"
                    )
                ],
                rewards={
                    "experience": 200,
                    "gold": 100,
                    "reputation": {"merchant": 10}
                }
            )
        ]

        for quest in default_quests:
            self.quests[quest.id] = quest

        # Create quest chain
        merchant_chain = QuestChain(
            id="merchant_quests",
            name="Merchant's Troubles",
            description="A series of quests involving the local merchant",
            quest_ids=["missing_supplies", "merchant_revenge", "merchant_gratitude"],
            final_reward={"gold": 500, "unique_item": "merchant_ring"}
        )
        self.quest_chains[merchant_chain.id] = merchant_chain

    def create_player_profile(self, player_id: str) -> Dict[str, Any]:
        """Create quest profile for new player"""
        # Auto-accept tutorial quests
        tutorial_quests = [
            quest_id for quest_id, quest in self.quests.items()
            if quest.quest_type == QuestType.TUTORIAL and quest.auto_accept
        ]

        for quest_id in tutorial_quests:
            self.accept_quest(player_id, quest_id)

        self.analytics.record_player_start(player_id)
        return {"accepted_quests": tutorial_quests}

    def accept_quest(self, player_id: str, quest_id: str) -> Tuple[bool, str]:
        """Accept a quest for a player"""
        if quest_id not in self.quests:
            return False, "Quest not found"

        quest = self.quests[quest_id]

        # Check if player already has this quest
        if quest_id in self.player_progress[player_id]:
            return False, "Quest already accepted"

        # Check prerequisites
        if not self.check_quest_prerequisites(player_id, quest):
            return False, "Quest prerequisites not met"

        # Check level requirement
        player_level = self.get_player_level(player_id)
        if player_level < quest.level_requirement:
            return False, f"Level requirement not met (need {quest.level_requirement})"

        # Accept quest
        progress = QuestProgress(
            quest_id=quest_id,
            status=QuestStatus.ACTIVE,
            started_at=time.time()
        )

        # Initialize objective progress
        for objective in quest.objectives:
            progress.objective_progress[objective.id] = 0

        self.player_progress[player_id][quest_id] = progress
        self.active_quests[player_id].add(quest_id)

        self.analytics.record_quest_accept(player_id, quest_id)

        return True, f"Accepted quest: {quest.title}"

    def check_quest_prerequisites(self, player_id: str, quest: Quest) -> bool:
        """Check if player meets quest prerequisites"""
        for prereq_quest_id in quest.prerequisites:
            if (prereq_quest_id not in self.completed_quests[player_id] and
                prereq_quest_id not in self.player_progress[player_id]):
                return False

        # Check world state prerequisites
        for condition, required_value in quest.world_impact.items():
            if self.world_state.get(condition, 0) < required_value:
                return False

        return True

    def update_objective(self, player_id: str, objective_type: ObjectiveType,
                        target: str, quantity: int = 1) -> List[str]:
        """Update quest objectives based on player actions"""
        completed_quests = []

        for quest_id in self.active_quests[player_id]:
            if quest_id not in self.quests:
                continue

            quest = self.quests[quest_id]
            progress = self.player_progress[player_id][quest_id]

            # Find matching objectives
            for objective in quest.objectives:
                if (objective.type == objective_type and
                    objective.target == target and
                    objective.id not in progress.failed_objectives):

                    current_progress = progress.objective_progress.get(objective.id, 0)
                    new_progress = min(current_progress + quantity, objective.required_quantity)
                    progress.objective_progress[objective.id] = new_progress

                    # Check if objective is completed
                    if new_progress >= objective.required_quantity:
                        self.analytics.record_objective_complete(player_id, quest_id, objective.id)

            # Check if quest is complete
            if self.check_quest_completion(player_id, quest_id):
                completed_quests.append(quest_id)

        return completed_quests

    def check_quest_completion(self, player_id: str, quest_id: str) -> bool:
        """Check if a quest is completed"""
        if quest_id not in self.quests or quest_id not in self.player_progress[player_id]:
            return False

        quest = self.quests[quest_id]
        progress = self.player_progress[player_id][quest_id]

        # Check all required objectives
        for objective in quest.objectives:
            if not objective.optional:
                current_progress = progress.objective_progress.get(objective.id, 0)
                if current_progress < objective.required_quantity:
                    return False

        # Check time limit
        if quest.time_limit and progress.started_at:
            elapsed = time.time() - progress.started_at
            if elapsed > quest.time_limit:
                self.fail_quest(player_id, quest_id, "Time limit exceeded")
                return False

        # Complete the quest
        self.complete_quest(player_id, quest_id)
        return True

    def complete_quest(self, player_id: str, quest_id: str, choices: List[str] = None) -> Tuple[bool, str]:
        """Complete a quest and grant rewards"""
        if quest_id not in self.player_progress[player_id]:
            return False, "Quest not found"

        quest = self.quests[quest_id]
        progress = self.player_progress[player_id][quest_id]

        # Apply choices if any
        if choices:
            for choice_id in choices:
                self.apply_quest_choice(player_id, quest_id, choice_id)

        # Grant rewards
        rewards_granted = self.grant_quest_rewards(player_id, quest)

        # Update progress
        progress.status = QuestStatus.COMPLETED
        progress.completed_at = time.time()

        # Move from active to completed
        self.active_quests[player_id].discard(quest_id)
        self.completed_quests[player_id].add(quest_id)

        # Check for quest chain completion
        self.check_quest_chain_completion(player_id)

        # Apply world impact
        for impact, value in quest.world_impact.items():
            self.world_state[impact] = self.world_state.get(impact, 0) + value

        # Unlock new quests
        self.unlock_dependent_quests(player_id, quest_id)

        # Generate dynamic quests based on completion
        self.generate_dynamic_quests(player_id, quest_id)

        self.analytics.record_quest_complete(player_id, quest_id, rewards_granted)

        return True, f"Completed quest: {quest.title}. Rewards: {rewards_granted}"

    def fail_quest(self, player_id: str, quest_id: str, reason: str = "") -> Tuple[bool, str]:
        """Fail a quest"""
        if quest_id not in self.player_progress[player_id]:
            return False, "Quest not found"

        quest = self.quests[quest_id]
        progress = self.player_progress[player_id][quest_id]

        progress.status = QuestStatus.FAILED

        # Move from active to failed
        self.active_quests[player_id].discard(quest_id)

        self.analytics.record_quest_fail(player_id, quest_id, reason)

        return True, f"Failed quest: {quest.title}. Reason: {reason}"

    def apply_quest_choice(self, player_id: str, quest_id: str, choice_id: str) -> bool:
        """Apply a quest choice"""
        if quest_id not in self.quests:
            return False

        quest = self.quests[quest_id]
        progress = self.player_progress[player_id][quest_id]

        # Find the choice
        choice = None
        for c in quest.choices:
            if c.id == choice_id:
                choice = c
                break

        if not choice:
            return False

        # Check requirements
        if not self.check_choice_requirements(player_id, choice):
            return False

        # Apply consequences
        if choice.reputation_changes:
            for faction, change in choice.reputation_changes.items():
                progress.reputation_changes[faction] = progress.reputation_changes.get(faction, 0) + change

        # Track choice
        progress.choices_made.append(choice_id)

        # Trigger next quest if specified
        if choice.next_quest_id:
            self.accept_quest(player_id, choice.next_quest_id)

        self.analytics.record_quest_choice(player_id, quest_id, choice_id)

        return True

    def check_choice_requirements(self, player_id: str, choice: QuestChoice) -> bool:
        """Check if player meets choice requirements"""
        for requirement, value in choice.requirements.items():
            if requirement == "level":
                if self.get_player_level(player_id) < value:
                    return False
            elif requirement == "skill":
                if self.get_player_skill(player_id, value) < choice.requirements.get("skill_level", 1):
                    return False
            # Add more requirement checks as needed

        return True

    def grant_quest_rewards(self, player_id: str, quest: Quest) -> Dict[str, Any]:
        """Grant quest rewards to player"""
        rewards_granted = {}

        # Scale rewards based on difficulty
        scaling = self.difficulty_scaling[quest.difficulty]

        if "experience" in quest.rewards:
            xp = int(quest.rewards["experience"] * scaling)
            self.award_experience(player_id, xp)
            rewards_granted["experience"] = xp

        if "gold" in quest.rewards:
            gold = int(quest.rewards["gold"] * scaling)
            self.award_gold(player_id, gold)
            rewards_granted["gold"] = gold

        if "items" in quest.rewards:
            items = quest.rewards["items"].copy()
            self.award_items(player_id, items)
            rewards_granted["items"] = items

        if "reputation" in quest.rewards:
            reputation = quest.rewards["reputation"]
            self.award_reputation(player_id, reputation)
            rewards_granted["reputation"] = reputation

        return rewards_granted

    def generate_dynamic_quests(self, player_id: str, completed_quest_id: str):
        """Generate dynamic quests based on player actions"""
        player_level = self.get_player_level(player_id)
        player_reputation = self.get_player_reputation(player_id)

        # Example dynamic quest generation
        if "goblin" in completed_quest_id and random.random() < 0.3:
            # Generate follow-up goblin quest
            self.create_dynamic_goblin_quest(player_id, player_level)

        if player_reputation.get("merchants", 0) > 50 and random.random() < 0.2:
            # Generate merchant guild quest
            self.create_dynamic_merchant_quest(player_id, player_level)

    def create_dynamic_goblin_quest(self, player_id: str, level: int):
        """Create a dynamic goblin-related quest"""
        quest_id = f"dynamic_goblin_{int(time.time())}"

        quest = Quest(
            id=quest_id,
            title="Goblin Troubles Continue",
            description="More goblin activity has been reported nearby",
            quest_type=QuestType.SIDE,
            difficulty=QuestDifficulty.NORMAL if level > 10 else QuestDifficulty.EASY,
            level_requirement=max(1, level - 2),
            objectives=[
                QuestObjective(
                    id="kill_goblins",
                    description="Defeat the goblin attackers",
                    type=ObjectiveType.KILL,
                    target="goblin_warrior",
                    required_quantity=5 + level // 5
                )
            ],
            rewards={
                "experience": 100 + level * 10,
                "gold": 50 + level * 5
            },
            tags={"dynamic", "goblin", "combat"}
        )

        self.quests[quest_id] = quest
        self.accept_quest(player_id, quest_id)

    def create_dynamic_merchant_quest(self, player_id: str, level: int):
        """Create a dynamic merchant guild quest"""
        quest_id = f"dynamic_merchant_{int(time.time())}"

        quest = Quest(
            id=quest_id,
            title="Merchant Guild Request",
            description="The merchant guild has a special request for you",
            quest_type=QuestType.SIDE,
            difficulty=QuestDifficulty.HARD if level > 20 else QuestDifficulty.NORMAL,
            level_requirement=max(5, level - 3),
            objectives=[
                QuestObjective(
                    id="deliver_package",
                    description="Deliver a special package",
                    type=ObjectiveType.DELIVER,
                    target="rival_merchant"
                ),
                QuestObjective(
                    id="collect_payment",
                    description="Collect payment from the recipient",
                    type=ObjectiveType.TALK,
                    target="rival_merchant"
                )
            ],
            rewards={
                "experience": 200 + level * 15,
                "gold": 150 + level * 10,
                "reputation": {"merchants": 15, "nobles": 5}
            },
            tags={"dynamic", "merchant", "social"}
        )

        self.quests[quest_id] = quest
        self.accept_quest(player_id, quest_id)

    def get_available_quests(self, player_id: str) -> List[Quest]:
        """Get list of quests available to player"""
        available = []
        player_level = self.get_player_level(player_id)

        for quest_id, quest in self.quests.items():
            # Skip if already accepted or completed
            if quest_id in self.player_progress[player_id]:
                continue

            # Check prerequisites
            if not self.check_quest_prerequisites(player_id, quest):
                continue

            # Check level requirement
            if player_level < quest.level_requirement:
                continue

            available.append(quest)

        return available

    def get_active_quests(self, player_id: str) -> List[Tuple[Quest, QuestProgress]]:
        """Get player's active quests with progress"""
        active = []
        for quest_id in self.active_quests[player_id]:
            if quest_id in self.quests and quest_id in self.player_progress[player_id]:
                quest = self.quests[quest_id]
                progress = self.player_progress[player_id][quest_id]
                active.append((quest, progress))

        return active

    def check_quest_chain_completion(self, player_id: str):
        """Check if any quest chains are completed"""
        for chain_id, chain in self.quest_chains.items():
            completed_in_chain = sum(1 for quest_id in chain.quest_ids
                                   if quest_id in self.completed_quests[player_id])

            if completed_in_chain >= chain.required_completions:
                # Grant chain reward
                self.grant_quest_rewards(player_id, type('obj', (object,), {
                    'rewards': chain.final_reward,
                    'difficulty': QuestDifficulty.NORMAL
                })())

                self.analytics.record_quest_chain_complete(player_id, chain_id)

    def unlock_dependent_quests(self, player_id: str, completed_quest_id: str):
        """Unlock quests that depend on completed quest"""
        for quest_id, quest in self.quests.items():
            if (completed_quest_id in quest.prerequisites and
                quest_id not in self.player_progress[player_id] and
                self.check_quest_prerequisites(player_id, quest)):

                # Auto-accept if it's a continuation quest
                if quest.auto_accept:
                    self.accept_quest(player_id, quest_id)

    def get_quest_recommendations(self, player_id: str) -> List[Quest]:
        """Get recommended quests for player based on level and preferences"""
        available = self.get_available_quests(player_id)
        player_level = self.get_player_level(player_id)

        # Sort by level appropriateness and difficulty
        recommended = []
        for quest in available:
            level_diff = abs(quest.level_requirement - player_level)
            difficulty_score = {
                QuestDifficulty.TRIVIAL: 0,
                QuestDifficulty.EASY: 1,
                QuestDifficulty.NORMAL: 2,
                QuestDifficulty.HARD: 3,
                QuestDifficulty.EXPERT: 4,
                QuestDifficulty.LEGENDARY: 5
            }[quest.difficulty]

            score = (10 - level_diff) + difficulty_score
            recommended.append((score, quest))

        # Sort by score (higher is better recommendation)
        recommended.sort(key=lambda x: x[0], reverse=True)

        return [quest for score, quest in recommended[:5]]

    # Placeholder methods for integration
    def get_player_level(self, player_id: str) -> int:
        """Get player level (placeholder)"""
        return 1

    def get_player_skill(self, player_id: str, skill: str) -> int:
        """Get player skill level (placeholder)"""
        return 1

    def get_player_reputation(self, player_id: str) -> Dict[str, int]:
        """Get player reputation (placeholder)"""
        return {}

    def award_experience(self, player_id: str, amount: int):
        """Award experience to player (placeholder)"""
        pass

    def award_gold(self, player_id: str, amount: int):
        """Award gold to player (placeholder)"""
        pass

    def award_items(self, player_id: str, items: List[str]):
        """Award items to player (placeholder)"""
        pass

    def award_reputation(self, player_id: str, reputation: Dict[str, int]):
        """Award reputation to player (placeholder)"""
        pass

class QuestAnalytics:
    """Analytics for quest system balance and engagement"""

    def __init__(self):
        self.quest_stats = defaultdict(lambda: {
            "accepts": 0,
            "completions": 0,
            "fails": 0,
            "abandons": 0,
            "completion_time": [],
            "choice_distribution": defaultdict(int)
        })
        self.player_engagement = defaultdict(list)
        self.difficulty_completion = defaultdict(lambda: defaultdict(int))

    def record_player_start(self, player_id: str):
        """Record new player starting quests"""
        self.player_engagement[player_id].append({
            "event": "start",
            "timestamp": time.time()
        })

    def record_quest_accept(self, player_id: str, quest_id: str):
        """Record quest acceptance"""
        self.quest_stats[quest_id]["accepts"] += 1
        self.player_engagement[player_id].append({
            "event": "accept",
            "quest_id": quest_id,
            "timestamp": time.time()
        })

    def record_quest_complete(self, player_id: str, quest_id: str, rewards: Dict[str, Any]):
        """Record quest completion"""
        self.quest_stats[quest_id]["completions"] += 1
        self.player_engagement[player_id].append({
            "event": "complete",
            "quest_id": quest_id,
            "rewards": rewards,
            "timestamp": time.time()
        })

    def record_quest_fail(self, player_id: str, quest_id: str, reason: str):
        """Record quest failure"""
        self.quest_stats[quest_id]["fails"] += 1
        self.player_engagement[player_id].append({
            "event": "fail",
            "quest_id": quest_id,
            "reason": reason,
            "timestamp": time.time()
        })

    def record_quest_choice(self, player_id: str, quest_id: str, choice_id: str):
        """Record quest choice made"""
        self.quest_stats[quest_id]["choice_distribution"][choice_id] += 1

    def record_objective_complete(self, player_id: str, quest_id: str, objective_id: str):
        """Record objective completion"""
        pass  # Could track objective completion rates

    def record_quest_chain_complete(self, player_id: str, chain_id: str):
        """Record quest chain completion"""
        self.player_engagement[player_id].append({
            "event": "chain_complete",
            "chain_id": chain_id,
            "timestamp": time.time()
        })

    def get_quest_performance(self, quest_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific quest"""
        if quest_id not in self.quest_stats:
            return {"error": "Quest not found"}

        stats = self.quest_stats[quest_id]
        total_attempts = stats["accepts"]
        completions = stats["completions"]
        fails = stats["fails"]

        completion_rate = completions / total_attempts if total_attempts > 0 else 0
        fail_rate = fails / total_attempts if total_attempts > 0 else 0

        return {
            "quest_id": quest_id,
            "total_attempts": total_attempts,
            "completion_rate": completion_rate,
            "fail_rate": fail_rate,
            "choice_distribution": dict(stats["choice_distribution"]),
            "engagement_score": (completions * 2 + total_attempts) / 3
        }

# Utility functions for quest balance
def calculate_quest_difficulty_curve(base_xp: int, difficulty: QuestDifficulty, player_level: int) -> int:
    """Calculate appropriate XP reward based on difficulty and player level"""
    difficulty_multiplier = {
        QuestDifficulty.TRIVIAL: 0.5,
        QuestDifficulty.EASY: 0.8,
        QuestDifficulty.NORMAL: 1.0,
        QuestDifficulty.HARD: 1.3,
        QuestDifficulty.EXPERT: 1.6,
        QuestDifficulty.LEGENDARY: 2.0
    }

    level_multiplier = 1 + (player_level - 1) * 0.1
    return int(base_xp * difficulty_multiplier[difficulty] * level_multiplier)

def analyze_quest_flow(quests: List[Quest]) -> Dict[str, Any]:
    """Analyze quest flow and dependencies"""
    dependency_graph = {}
    level_distribution = defaultdict(int)
    difficulty_distribution = defaultdict(int)

    for quest in quests:
        level_distribution[quest.level_requirement] += 1
        difficulty_distribution[quest.difficulty.value] += 1
        dependency_graph[quest.id] = quest.prerequisites

    # Calculate maximum depth of quest chains
    max_depth = 0
    for quest_id in dependency_graph:
        depth = calculate_quest_depth(quest_id, dependency_graph, set())
        max_depth = max(max_depth, depth)

    return {
        "total_quests": len(quests),
        "level_distribution": dict(level_distribution),
        "difficulty_distribution": dict(difficulty_distribution),
        "max_chain_depth": max_depth,
        "average_prerequisites": sum(len(prereqs) for prereqs in dependency_graph.values()) / len(dependency_graph) if dependency_graph else 0
    }

def calculate_quest_depth(quest_id: str, dependency_graph: Dict[str, List[str]], visited: Set[str]) -> int:
    """Calculate depth of quest in dependency chain"""
    if quest_id in visited:
        return 0  # Circular dependency

    visited.add(quest_id)
    prerequisites = dependency_graph.get(quest_id, [])

    if not prerequisites:
        return 1

    max_depth = 0
    for prereq in prerequisites:
        depth = calculate_quest_depth(prereq, dependency_graph, visited.copy())
        max_depth = max(max_depth, depth)

    return max_depth + 1

# Export main classes
__all__ = [
    'QuestEngine',
    'Quest',
    'QuestObjective',
    'QuestChoice',
    'QuestProgress',
    'QuestChain',
    'QuestAnalytics',
    'calculate_quest_difficulty_curve',
    'analyze_quest_flow'
]