"""
Exploration Skills implementation for DMlogn8n

This module defines all exploration-related skills including perception,
investigation, navigation, and environmental awareness.
"""

from typing import List, Dict, Any, Optional
from ..core.skill import (
    Skill, SkillCategory, MasteryLevel, SkillPrerequisite,
    SynergyBonus, SpecialAbility
)


class ExplorationSkills:
    """Factory class for creating exploration skills"""

    @staticmethod
    def create_all_exploration_skills() -> List[Skill]:
        """Create all exploration skills"""
        return [
            ExplorationSkills.create_perception(),
            ExplorationSkills.create_investigation(),
            ExplorationSkills.create_navigation(),
            ExplorationSkills.create_survival(),
            ExplorationSkills.create_stealth(),
            ExplorationSkills.create_traps(),
            ExplorationSkills.create_lockpicking(),
            ExplorationSkills.create_tracking(),
            ExplorationSkills.create_cartography(),
            ExplorationSkills.create_natural_knowledge(),
            ExplorationSkills.create_dungeon_crawling(),
            ExplorationSkills.create_pathfinding(),
            ExplorationSkills.create_scouting(),
            ExplorationSkills.create_wilderness_survival(),
            ExplorationSkills.create_urban_exploration()
        ]

    @staticmethod
    def create_perception() -> Skill:
        """Perception and awareness skills"""
        return Skill(
            name="Perception",
            category=SkillCategory.EXPLORATION,
            description="Ability to notice details and detect hidden things",
            base_difficulty=0.5,
            dnd_skill="Perception",
            synergies=[
                SynergyBonus(
                    skill_name="Investigation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Perception enhances investigation"
                ),
                SynergyBonus(
                    skill_name="Stealth",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Awareness helps stealth"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Eagle Eye",
                    description="See details at extreme distances",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Extended vision"
                ),
                SpecialAbility(
                    name="True Sight",
                    description="See through illusions and invisibility",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="See hidden things"
                ),
                SpecialAbility(
                    name="Perfect Awareness",
                    description="Cannot be surprised",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Always alert"
                )
            ]
        )

    @staticmethod
    def create_investigation() -> Skill:
        """Investigation and analytical skills"""
        return Skill(
            name="Investigation",
            category=SkillCategory.EXPLORATION,
            description="Ability to analyze clues and deduce information",
            base_difficulty=0.6,
            dnd_skill="Investigation",
            synergies=[
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Perception provides clues for investigation"
                ),
                SynergyBonus(
                    skill_name="Tracking",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Tracking aids investigation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Deductive Reasoning",
                    description="Instantly understand complex clues",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Instant analysis",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Sherlock Scan",
                    description="Learn everything about person/object in moments",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Complete analysis",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_navigation() -> Skill:
        """Navigation and orientation skills"""
        return Skill(
            name="Navigation",
            category=SkillCategory.EXPLORATION,
            description="Ability to find way and avoid getting lost",
            base_difficulty=0.4,
            dnd_skill="Navigation",
            synergies=[
                SynergyBonus(
                    skill_name="Cartography",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Map reading aids navigation"
                ),
                SynergyBonus(
                    skill_name="Pathfinding",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Pathfinding enhances navigation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Natural Compass",
                    description="Always know cardinal directions",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Always oriented"
                ),
                SpecialAbility(
                    name="Mental Map",
                    description="Perfect memory of locations visited",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Perfect location memory"
                )
            ]
        )

    @staticmethod
    def create_survival() -> Skill:
        """Survival and wilderness living skills"""
        return Skill(
            name="Survival",
            category=SkillCategory.EXPLORATION,
            description="Ability to survive in harsh environments",
            base_difficulty=0.5,
            dnd_skill="Survival",
            synergies=[
                SynergyBonus(
                    skill_name="Natural Knowledge",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Nature knowledge aids survival"
                ),
                SynergyBonus(
                    skill_name="Tracking",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Tracking helps find food"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Master Survivor",
                    description="Survive indefinitely in wilderness",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Self-sufficient"
                ),
                SpecialAbility(
                    name="One with Nature",
                    description="Gain benefits from natural environment",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Environmental harmony"
                )
            ]
        )

    @staticmethod
    def create_stealth() -> Skill:
        """Stealth and concealment skills"""
        return Skill(
            name="Stealth",
            category=SkillCategory.EXPLORATION,
            description="Ability to move unseen and unheard",
            base_difficulty=0.5,
            dnd_skill="Stealth",
            synergies=[
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Awareness helps stealth"
                ),
                SynergyBonus(
                    skill_name="Scouting",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Scouting uses stealth"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Shadow Step",
                    description="Move between shadows",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Teleport between shadows",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Invisibility",
                    description="Become completely invisible",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="True invisibility",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_traps() -> Skill:
        """Trap detection and disarming skills"""
        return Skill(
            name="Traps",
            category=SkillCategory.EXPLORATION,
            description="Ability to detect, disarm, and create traps",
            base_difficulty=0.6,
            dnd_skill="Traps",
            synergies=[
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Perception reveals traps"
                ),
                SynergyBonus(
                    skill_name="Investigation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Analysis reveals trap mechanisms"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Trap Sense",
                    description="Always know when traps are near",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Trap detection aura"
                ),
                SpecialAbility(
                    name="Master Trapper",
                    description="Create masterwork traps",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Create deadly traps",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_lockpicking() -> Skill:
        """Lockpicking and security bypass skills"""
        return Skill(
            name="Lockpicking",
            category=SkillCategory.EXPLORATION,
            description="Ability to pick locks and bypass security",
            base_difficulty=0.6,
            dnd_skill="Lockpicking",
            synergies=[
                SynergyBonus(
                    skill_name="Investigation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Analysis reveals lock mechanisms"
                ),
                SynergyBonus(
                    skill_name="Traps",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Trap knowledge helps with trapped locks"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Master Key",
                    description="Open any non-magical lock",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Open any lock",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Ghost Touch",
                    description="Phase through locked doors",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Phase through barriers",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_tracking() -> Skill:
        """Tracking and hunting skills"""
        return Skill(
            name="Tracking",
            category=SkillCategory.EXPLORATION,
            description="Ability to follow tracks and hunt prey",
            base_difficulty=0.5,
            dnd_skill="Tracking",
            synergies=[
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Perception reveals tracks"
                ),
                SynergyBonus(
                    skill_name="Survival",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Survival aids tracking"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Bloodhound",
                    description="Follow tracks days old",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Enhanced tracking"
                ),
                SpecialAbility(
                    name="Prey Sense",
                    description="Sense location of specific targets",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Locate specific creature",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_cartography() -> Skill:
        """Cartography and map-making skills"""
        return Skill(
            name="Cartography",
            category=SkillCategory.EXPLORATION,
            description="Ability to create and read maps",
            base_difficulty=0.4,
            dnd_skill="Cartography",
            synergies=[
                SynergyBonus(
                    skill_name="Navigation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Maps aid navigation"
                ),
                SynergyBonus(
                    skill_name="Investigation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Maps reveal information"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Map",
                    description="Create magical map that updates itself",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Living map",
                    cooldown=5
                ),
                SpecialAbility(
                    name="Cartographic Memory",
                    description="Never forget any location mapped",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Perfect map memory"
                )
            ]
        )

    @staticmethod
    def create_natural_knowledge() -> Skill:
        """Knowledge of natural world"""
        return Skill(
            name="Natural Knowledge",
            category=SkillCategory.EXPLORATION,
            description="Understanding of plants, animals, and natural phenomena",
            base_difficulty=0.4,
            dnd_skill="Nature",
            synergies=[
                SynergyBonus(
                    skill_name="Survival",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Nature knowledge aids survival"
                ),
                SynergyBonus(
                    skill_name="Tracking",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Animal knowledge helps tracking"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Speak with Animals",
                    description="Communicate with animals",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Animal communication",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Nature's Gift",
                    description="Gain benefits from natural environment",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Environmental bonuses"
                )
            ]
        )

    @staticmethod
    def create_dungeon_crawling() -> Skill:
        """Dungeon exploration expertise"""
        return Skill(
            name="Dungeon Crawling",
            category=SkillCategory.EXPLORATION,
            description="Specialized knowledge of dungeon exploration",
            base_difficulty=0.6,
            dnd_skill="Dungeon Lore",
            prerequisites=[
                SkillPrerequisite("Perception", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Traps", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Traps",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Dungeons are full of traps"
                ),
                SynergyBonus(
                    skill_name="Stealth",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Stealth essential in dungeons"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Dungeon Sense",
                    description="Sense dungeon layout and dangers",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Dungeon awareness"
                ),
                SpecialAbility(
                    name="Dungeon Master",
                    description="Understand any dungeon instantly",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Complete dungeon knowledge",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_pathfinding() -> Skill:
        """Pathfinding and route optimization"""
        return Skill(
            name="Pathfinding",
            category=SkillCategory.EXPLORATION,
            description="Ability to find optimal routes through difficult terrain",
            base_difficulty=0.5,
            dnd_skill="Pathfinding",
            synergies=[
                SynergyBonus(
                    skill_name="Navigation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Pathfinding enhances navigation"
                ),
                SynergyBonus(
                    skill_name="Survival",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Route planning aids survival"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Optimal Path",
                    description="Always find safest/fastest route",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Perfect routing",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Trailblazer",
                    description="Create paths through impassable terrain",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Path creation",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_scouting() -> Skill:
        """Scouting and reconnaissance skills"""
        return Skill(
            name="Scouting",
            category=SkillCategory.EXPLORATION,
            description="Ability to gather information about areas and enemies",
            base_difficulty=0.6,
            dnd_skill="Scouting",
            synergies=[
                SynergyBonus(
                    skill_name="Stealth",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Stealth essential for scouting"
                ),
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Perception vital for scouting"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Eagle Scout",
                    description="Survey large area quickly",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Area survey",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Ghost Recon",
                    description="Scout without being detected",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Undetectable scouting",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_wilderness_survival() -> Skill:
        """Advanced wilderness survival"""
        return Skill(
            name="Wilderness Survival",
            category=SkillCategory.EXPLORATION,
            description="Expert survival in natural environments",
            base_difficulty=0.6,
            dnd_skill="Wilderness Survival",
            prerequisites=[
                SkillPrerequisite("Survival", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Natural Knowledge", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Survival",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Foundation for wilderness survival"
                ),
                SynergyBonus(
                    skill_name="Natural Knowledge",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Nature aids wilderness survival"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Wilderness Master",
                    description="Thrive in any natural environment",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Environmental adaptation"
                ),
                SpecialAbility(
                    name="One with Wild",
                    description="Command animals and plants",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Control nature",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_urban_exploration() -> Skill:
        """Urban and city exploration skills"""
        return Skill(
            name="Urban Exploration",
            category=SkillCategory.EXPLORATION,
            description="Specialized exploration of cities and structures",
            base_difficulty=0.5,
            dnd_skill="Urban Lore",
            synergies=[
                SynergyBonus(
                    skill_name="Stealth",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Stealth in urban environments"
                ),
                SynergyBonus(
                    skill_name="Lockpicking",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Locks common in urban areas"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Urban Camouflage",
                    description="Blend into any urban environment",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Urban stealth",
                    cooldown=1
                ),
                SpecialAbility(
                    name="City Master",
                    description="Know secrets of any city",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Urban knowledge"
                )
            ]
        )