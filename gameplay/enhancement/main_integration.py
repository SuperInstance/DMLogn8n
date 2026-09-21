#!/usr/bin/env python3
"""
Main Integration System for Enhanced DMLogn8n Gameplay
Integrates all gameplay systems into a cohesive experience
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import threading

# Import all our enhanced systems
from combat_system import TacticalCombatSystem, CombatEntity, CombatStats
from skill_system import SkillSystem, CharacterSkills, Skill
from inventory_manager import Inventory, ItemDatabase, CraftingSystem
from quest_engine import QuestEngine, Quest, QuestProgress
from social_gameplay import SocialGameplaySystem, Relationship, Group
from progression_system import ProgressionSystem, CharacterProgress, ClassType
from event_system import EventSystem, WorldEvent
from achievement_system import AchievementSystem, PlayerAchievements
from balance_optimizer import BalanceOptimizer
from game_analytics import GameAnalytics, Event

@dataclass
class Player:
    """Complete player profile integrating all systems"""
    player_id: str
    name: str
    created_at: float

    # System references
    combat_entity: Optional[CombatEntity] = None
    character_skills: Optional[CharacterSkills] = None
    inventory: Optional[Inventory] = None
    quest_progress: Optional[Dict[str, QuestProgress]] = None
    character_progress: Optional[CharacterProgress] = None
    achievements: Optional[PlayerAchievements] = None
    relationships: Optional[Dict[str, Relationship]] = None

class EnhancedGameplayEngine:
    """Main integration engine for all enhanced gameplay systems"""

    def __init__(self):
        print("Initializing Enhanced DMLogn8n Gameplay Engine...")

        # Core gameplay systems
        self.combat_system = TacticalCombatSystem()
        self.skill_system = SkillSystem()
        self.item_database = ItemDatabase()
        self.crafting_system = CraftingSystem()
        self.quest_engine = QuestEngine()
        self.social_system = SocialGameplaySystem()
        self.progression_system = ProgressionSystem()
        self.event_system = EventSystem()
        self.achievement_system = AchievementSystem()
        self.balance_optimizer = BalanceOptimizer()
        self.analytics_system = GameAnalytics()

        # Player management
        self.players: Dict[str, Player] = {}
        self.active_sessions: Dict[str, str] = {}  # session_id -> player_id

        # Cross-system integration
        self.event_handlers: Dict[str, List[callable]] = {}
        self.system_bridges: Dict[str, Any] = {}

        # Performance monitoring
        self.performance_metrics = {
            "last_update": time.time(),
            "players_online": 0,
            "active_combats": 0,
            "daily_events": 0,
            "quests_completed_today": 0
        }

        # Background tasks
        self.running = False
        self.background_thread = None

        self._initialize_system_bridges()
        self._register_event_handlers()
        self._start_background_tasks()

        print("Enhanced Gameplay Engine initialized successfully!")

    def _initialize_system_bridges(self):
        """Initialize connections between systems"""
        # Combat <-> Skills bridge
        self.system_bridges["combat_skills"] = {
            "apply_skill_effects": self._apply_combat_skill_effects,
            "calculate_combat_power": self._calculate_total_combat_power
        }

        # Inventory <-> Crafting bridge
        self.system_bridges["inventory_crafting"] = {
            "check_crafting_materials": self._check_crafting_materials,
            "add_crafted_items": self._add_crafted_items_to_inventory
        }

        # Quest <-> Progression bridge
        self.system_bridges["quest_progression"] = {
            "award_quest_xp": self._award_quest_experience,
            "check_quest_requirements": self._check_quest_requirements
        }

        # Social <-> Events bridge
        self.system_bridges["social_events"] = {
            "create_social_events": self._create_social_events,
            "award_social_rewards": self._award_social_event_rewards
        }

        # Achievement <-> All Systems bridge
        self.system_bridges["achievements"] = {
            "track_all_achievements": self._track_cross_system_achievements,
            "check_milestone_achievements": self._check_milestone_achievements
        }

    def _register_event_handlers(self):
        """Register cross-system event handlers"""
        self.event_handlers["combat_victory"] = [
            self._handle_combat_victory,
            self.achievement_system.update_progress,
            self.progression_system.add_experience
        ]

        self.event_handlers["quest_completed"] = [
            self._handle_quest_completion,
            self.achievement_system.update_progress,
            self.social_system.award_reputation
        ]

        self.event_handlers["skill_level_up"] = [
            self._handle_skill_level_up,
            self.achievement_system.update_progress,
            self._update_combat_stats
        ]

        self.event_handlers["item_crafted"] = [
            self._handle_item_crafted,
            self.achievement_system.update_progress,
            self._check_crafting_achievements
        ]

        self.event_handlers["relationship_formed"] = [
            self._handle_relationship_formed,
            self.achievement_system.update_progress
        ]

    def create_player(self, player_id: str, name: str, class_type: ClassType) -> Player:
        """Create a new player with all systems initialized"""
        print(f"Creating new player: {name} ({class_type.value})")

        # Create player profile
        player = Player(
            player_id=player_id,
            name=name,
            created_at=time.time()
        )

        # Initialize progression system
        player.character_progress = self.progression_system.create_character(player_id, class_type)

        # Initialize combat entity based on progression
        progress = player.character_progress
        combat_stats = CombatStats(
            health=progress.stats.health,
            max_health=progress.stats.max_health,
            attack=progress.stats.attack_power,
            defense=progress.stats.defense,
            speed=10,
            critical_chance=progress.stats.critical_chance
        )

        player.combat_entity = CombatEntity(
            id=player_id,
            name=name,
            stats=combat_stats,
            team="player"
        )

        # Initialize skills
        player.character_skills = self.skill_system.create_character_skills(player_id)

        # Initialize inventory
        player.inventory = Inventory(capacity=100)
        self._add_starter_items(player.inventory)

        # Initialize quests
        self.quest_engine.create_player_profile(player_id)
        player.quest_progress = self.quest_engine.player_progress[player_id]

        # Initialize social profile
        self.social_system.create_character_profile(player_id)
        player.relationships = self.social_system.relationships

        # Initialize achievements
        player.achievements = self.achievement_system.create_player_profile(player_id)

        # Start analytics tracking
        self.analytics_system.start_session(player_id, f"session_{player_id}_{int(time.time())}")

        # Track in analytics
        self.analytics_system.track_player_action(
            player_id,
            "player_created",
            {"class": class_type.value, "name": name}
        )

        self.players[player_id] = player
        self.performance_metrics["players_online"] += 1

        print(f"Player {name} created successfully!")
        return player

    def _add_starter_items(self, inventory: Inventory):
        """Add starter items to new player inventory"""
        starter_items = [
            ("health_potion", 3),
            ("basic_sword", 1),
            ("gold_coin", 100)
        ]

        for item_id, quantity in starter_items:
            item = self.item_database.get_item(item_id)
            if item:
                inventory.add_item(item, quantity)

    def handle_player_action(self, player_id: str, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle player action and route to appropriate systems"""
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]
        data = data or {}
        result = {"success": False, "message": "Unknown action"}

        # Track action
        self.analytics_system.track_player_action(player_id, action, data)

        # Route to appropriate system
        if action.startswith("combat_"):
            result = self._handle_combat_action(player, action, data)
        elif action.startswith("skill_"):
            result = self._handle_skill_action(player, action, data)
        elif action.startswith("inventory_"):
            result = self._handle_inventory_action(player, action, data)
        elif action.startswith("quest_"):
            result = self._handle_quest_action(player, action, data)
        elif action.startswith("social_"):
            result = self._handle_social_action(player, action, data)
        elif action.startswith("craft_"):
            result = self._handle_crafting_action(player, action, data)
        elif action.startswith("event_"):
            result = self._handle_event_action(player, action, data)
        else:
            result = {"error": f"Unknown action type: {action}"}

        # Check for achievements
        self.achievement_system.update_progress(player_id, "player_action", action, 1, {"action": action})

        return result

    def _handle_combat_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle combat-related actions"""
        if action == "combat_start":
            # Start combat with enemy
            enemy_id = data.get("enemy_id", "goblin")
            enemy = self._create_enemy(enemy_id)

            self.combat_system.add_entity(player.combat_entity, 0, 2)
            self.combat_system.add_entity(enemy, 0, 5)

            success = self.combat_system.start_combat()
            self.performance_metrics["active_combats"] += 1

            return {
                "success": success,
                "message": "Combat started!" if success else "Failed to start combat",
                "combat_id": f"combat_{int(time.time())}"
            }

        elif action == "combat_attack":
            target_id = data.get("target_id")
            if target_id:
                result = self.combat_system.execute_action({
                    "actor_id": player.player_id,
                    "action_type": "attack",
                    "target_id": target_id
                })
                return {"success": result.success, "message": result.description, "damage": result.damage}

        return {"error": "Invalid combat action"}

    def _handle_skill_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill-related actions"""
        if action == "skill_learn":
            skill_id = data.get("skill_id")
            if skill_id:
                success, message = self.skill_system.learn_skill(player.player_id, skill_id)
                return {"success": success, "message": message}

        elif action == "skill_upgrade":
            skill_id = data.get("skill_id")
            if skill_id:
                success, message = self.skill_system.upgrade_skill(player.player_id, skill_id)
                return {"success": success, "message": message}

        elif action == "skill_use":
            skill_id = data.get("skill_id")
            target_id = data.get("target_id")
            if skill_id:
                # Apply skill effects through bridge
                bridge_result = self.system_bridges["combat_skills"]["apply_skill_effects"](
                    player, skill_id, target_id
                )
                return bridge_result

        return {"error": "Invalid skill action"}

    def _handle_inventory_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory-related actions"""
        if action == "inventory_use":
            item_id = data.get("item_id")
            if item_id:
                success, message = player.inventory.remove_item(item_id, 1)
                return {"success": success, "message": message}

        elif action == "inventory_equip":
            item_slot = data.get("slot")
            equipment_slot = data.get("equipment_slot")
            if item_slot is not None and equipment_slot:
                success, message = player.inventory.equip_item(item_slot, equipment_slot)
                return {"success": success, "message": message}

        return {"error": "Invalid inventory action"}

    def _handle_quest_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quest-related actions"""
        if action == "quest_accept":
            quest_id = data.get("quest_id")
            if quest_id:
                success, message = self.quest_engine.accept_quest(player.player_id, quest_id)
                return {"success": success, "message": message}

        elif action == "quest_progress":
            objective_type = data.get("objective_type")
            target = data.get("target")
            quantity = data.get("quantity", 1)
            if objective_type and target:
                completed = self.quest_engine.update_objective(
                    player.player_id, objective_type, target, quantity
                )
                return {"success": True, "completed_quests": completed}

        return {"error": "Invalid quest action"}

    def _handle_social_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social-related actions"""
        if action == "social_interact":
            target_id = data.get("target_id")
            interaction_type = data.get("type", "conversation")
            if target_id:
                success, message = self.social_system.interact(
                    player.player_id, target_id, interaction_type,
                    data.get("description", "Social interaction")
                )
                return {"success": success, "message": message}

        elif action == "group_join":
            group_id = data.get("group_id")
            if group_id:
                success, message = self.social_system.join_group(player.player_id, group_id)
                return {"success": success, "message": message}

        return {"error": "Invalid social action"}

    def _handle_crafting_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle crafting-related actions"""
        if action == "craft_item":
            recipe_id = data.get("recipe_id")
            quantity = data.get("quantity", 1)
            if recipe_id:
                success, message, item = self.crafting_system.craft_item(
                    recipe_id, player.inventory, quantity
                )
                return {"success": success, "message": message, "item": item.__dict__ if item else None}

        return {"error": "Invalid crafting action"}

    def _handle_event_action(self, player: Player, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event-related actions"""
        if action == "event_join":
            event_id = data.get("event_id")
            if event_id:
                success, message = self.event_system.join_event(player.player_id, event_id)
                return {"success": success, "message": message}

        return {"error": "Invalid event action"}

    # System bridge implementations
    def _apply_combat_skill_effects(self, player: Player, skill_id: str, target_id: str) -> Dict[str, Any]:
        """Apply skill effects in combat"""
        if not player.character_skills or skill_id not in player.character_skills.learned_skills:
            return {"success": False, "message": "Skill not learned"}

        skill_node = player.character_skills.learned_skills[skill_id]
        power = self.skill_system.get_skill_power(player.player_id, skill_id)

        # Apply damage based on skill power
        damage = int(power * 10)  # Base damage multiplier

        # Track in combat system if active
        result = {"success": True, "message": f"Used {skill_id} for {damage} damage", "damage": damage}

        # Trigger combat victory event if this defeated enemy
        if target_id and damage > 100:  # Simplified victory condition
            self._trigger_event("combat_victory", player.player_id, {"damage": damage, "skill": skill_id})

        return result

    def _calculate_total_combat_power(self, player: Player) -> float:
        """Calculate total combat power from all systems"""
        base_power = self.progression_system.calculate_character_power(player.player_id)
        skill_power = sum(
            self.skill_system.get_skill_power(player.player_id, skill_id)
            for skill_id in player.character_skills.learned_skills.keys()
        )
        item_power = self._calculate_item_power(player.inventory)

        return base_power + skill_power + item_power

    def _calculate_item_power(self, inventory: Inventory) -> float:
        """Calculate power from equipped items"""
        power = 0
        for slot, item_stack in inventory.equipped_items.items():
            if item_stack and item_stack.item:
                # Simplified item power calculation
                power += item_stack.item.value * 0.1
        return power

    def _award_quest_experience(self, player_id: str, experience: int, quest_data: Dict[str, Any]):
        """Award experience from quest completion"""
        self.progression_system.add_experience(player_id, experience, "quest")

    def _check_quest_requirements(self, player_id: str, quest: Quest) -> bool:
        """Check if player meets quest requirements"""
        player = self.players.get(player_id)
        if not player:
            return False

        # Check level requirement
        if player.character_progress.level < quest.level_requirement:
            return False

        # Check other requirements through systems
        return True

    def _create_enemy(self, enemy_id: str) -> CombatEntity:
        """Create an enemy for combat"""
        enemy_stats = {
            "goblin": CombatStats(health=30, attack=8, defense=5),
            "orc": CombatStats(health=50, attack=12, defense=8),
            "dragon": CombatStats(health=200, attack=25, defense=15)
        }

        stats = enemy_stats.get(enemy_id, CombatStats(health=20, attack=5, defense=3))

        return CombatEntity(
            id=f"{enemy_id}_{int(time.time())}",
            name=enemy_id.title(),
            stats=stats,
            team="enemy"
        )

    def _trigger_event(self, event_name: str, player_id: str, data: Dict[str, Any]):
        """Trigger cross-system event"""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    if hasattr(handler, '__self__'):
                        # Method with self
                        handler(player_id, **data)
                    else:
                        # Standalone function
                        handler(player_id, data)
                except Exception as e:
                    print(f"Error in event handler for {event_name}: {e}")

    def _start_background_tasks(self):
        """Start background processing tasks"""
        self.running = True
        self.background_thread = threading.Thread(target=self._background_loop, daemon=True)
        self.background_thread.start()

    def _background_loop(self):
        """Main background processing loop"""
        while self.running:
            try:
                # Update performance metrics
                self._update_performance_metrics()

                # Process world events
                self._process_world_events()

                # Check system balance
                if int(time.time()) % 3600 == 0:  # Every hour
                    self._run_balance_check()

                # Clean up inactive players
                self._cleanup_inactive_players()

                time.sleep(60)  # Update every minute

            except Exception as e:
                print(f"Error in background loop: {e}")
                time.sleep(60)

    def _update_performance_metrics(self):
        """Update performance metrics"""
        self.performance_metrics["last_update"] = time.time()
        self.performance_metrics["active_combats"] = len(self.combat_system.active_quests)
        self.performance_metrics["players_online"] = len(self.players)

    def _process_world_events(self):
        """Process dynamic world events"""
        # Generate random events
        if random.random() < 0.01:  # 1% chance per update
            event_types = ["invasion", "merchant", "discovery"]
            event_type = random.choice(event_types)
            self.event_system.generate_dynamic_event(event_type)

    def _run_balance_check(self):
        """Run balance analysis"""
        try:
            report = self.balance_optimizer.run_comprehensive_balance_test()
            if report.overall_score < 0.7:
                print(f"Balance issues detected! Overall score: {report.overall_score:.2f}")
                print(f"Recommendations: {', '.join(report.recommendations[:3])}")
        except Exception as e:
            print(f"Error running balance check: {e}")

    def _cleanup_inactive_players(self):
        """Clean up inactive player sessions"""
        current_time = time.time()
        inactive_timeout = 3600  # 1 hour

        inactive_players = []
        for player_id, player in self.players.items():
            last_activity = getattr(player, 'last_activity', player.created_at)
            if current_time - last_activity > inactive_timeout:
                inactive_players.append(player_id)

        for player_id in inactive_players:
            self.remove_player(player_id)

    def remove_player(self, player_id: str):
        """Remove player and clean up their data"""
        if player_id in self.players:
            # End analytics session
            self.analytics_system.end_session(f"session_{player_id}")

            # Remove from active players
            del self.players[player_id]
            self.performance_metrics["players_online"] -= 1

            print(f"Player {player_id} removed due to inactivity")

    def get_player_status(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive player status"""
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]

        return {
            "player_id": player_id,
            "name": player.name,
            "created_at": player.created_at,
            "progression": self.progression_system.get_progression_summary(player_id),
            "skills": self.skill_system.get_character_skill_summary(player_id),
            "inventory": player.inventory.get_inventory_summary(),
            "quests": {
                "active": len(self.quest_engine.get_active_quests(player_id)),
                "completed": len(self.quest_engine.completed_quests.get(player_id, set()))
            },
            "social": {
                "relationships": len(player.relationships or {}),
                "status": self.social_system.get_social_status(player_id).value
            },
            "achievements": self.achievement_system.get_player_progress(player_id),
            "combat_power": self._calculate_total_combat_power(player)
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "engine": "Enhanced DMLogn8n Gameplay Engine",
            "version": "1.0.0",
            "uptime": time.time() - getattr(self, 'start_time', time.time()),
            "players_online": len(self.players),
            "active_sessions": len(self.active_sessions),
            "active_combats": len(self.combat_system.active_quests),
            "world_events": len(self.event_system.active_events),
            "systems": {
                "combat": "running",
                "skills": "running",
                "inventory": "running",
                "quests": "running",
                "social": "running",
                "progression": "running",
                "events": "running",
                "achievements": "running",
                "analytics": "running",
                "balance": "idle"
            },
            "performance": self.performance_metrics,
            "health": self.analytics_system.get_system_health()
        }

    def shutdown(self):
        """Shutdown the gameplay engine"""
        print("Shutting down Enhanced Gameplay Engine...")

        self.running = False

        # End all player sessions
        for player_id in list(self.players.keys()):
            self.remove_player(player_id)

        # Stop all systems
        self.event_system.stop_event_system()
        self.analytics_system.stop_analytics()

        # Wait for background thread
        if self.background_thread:
            self.background_thread.join(timeout=10)

        print("Enhanced Gameplay Engine shutdown complete.")

# Export the main class
__all__ = ['EnhancedGameplayEngine', 'Player']