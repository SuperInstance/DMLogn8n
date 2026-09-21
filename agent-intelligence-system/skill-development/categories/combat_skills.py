"""
Combat Skills implementation for DMlogn8n

This module defines all combat-related skills including targeting,
positioning, timing, and weapon-specific abilities.
"""

from typing import List, Dict, Any, Optional
from ..core.skill import (
    Skill, SkillCategory, MasteryLevel, SkillPrerequisite,
    SynergyBonus, SpecialAbility
)


class CombatSkills:
    """Factory class for creating combat skills"""

    @staticmethod
    def create_all_combat_skills() -> List[Skill]:
        """Create all combat skills"""
        return [
            CombatSkills.create_weapon_mastery(),
            CombatSkills.create_targeting_precision(),
            CombatSkills.create_positional_awareness(),
            CombatSkills.create_combat_timing(),
            CombatSkills.create_defensive_stance(),
            CombatSkills.create_tactical_retreat(),
            CombatSkills.create_flanking_maneuvers(),
            CombatSkills.create_critical_strike(),
            CombatSkills.create_weapon_specialization(),
            CombatSkills.create_armor_mastery(),
            CombatSkills.create_shield_techniques(),
            CombatSkills.create_two_weapon_fighting(),
            CombatSkills.create_ranged_combat(),
            CombatSkills.create_unarmed_combat(),
            CombatSkills.create_mounted_combat()
        ]

    @staticmethod
    def create_weapon_mastery() -> Skill:
        """General weapon mastery skill"""
        return Skill(
            name="Weapon Mastery",
            category=SkillCategory.COMBAT,
            description="General proficiency with all types of weapons",
            base_difficulty=0.4,
            dnd_skill="Weapon Attack",
            synergies=[
                SynergyBonus(
                    skill_name="Targeting Precision",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Better targeting with weapon mastery"
                ),
                SynergyBonus(
                    skill_name="Critical Strike",
                    bonus_type="critical_chance",
                    bonus_value=0.10,
                    description="Increased critical chance with weapon mastery"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Weapon Adaptation",
                    description="Can use any weapon without penalty",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="No weapon penalties"
                ),
                SpecialAbility(
                    name="Master Strike",
                    description="Once per combat, add mastery bonus to damage",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="+1d6 damage",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Perfect Form",
                    description="All attacks have advantage for one round",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Advantage on all attacks",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_targeting_precision() -> Skill:
        """Precision targeting skill"""
        return Skill(
            name="Targeting Precision",
            category=SkillCategory.COMBAT,
            description="Ability to target specific locations and weak points",
            base_difficulty=0.6,
            dnd_skill="Attack Roll",
            synergies=[
                SynergyBonus(
                    skill_name="Weapon Mastery",
                    bonus_type="success_chance",
                    bonus_value=0.12,
                    description="Weapon mastery improves targeting"
                ),
                SynergyBonus(
                    skill_name="Ranged Combat",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Critical for ranged combat"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Called Shot",
                    description="Target specific body part for special effects",
                    required_level=MasteryLevel.APPRENTICE,
                    effect_type="active",
                    effect_value="Target specific location"
                ),
                SpecialAbility(
                    name="Weak Point Analysis",
                    description="Automatically identify enemy weaknesses",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="+2 to hit against weak points"
                )
            ]
        )

    @staticmethod
    def create_positional_awareness() -> Skill:
        """Positional awareness in combat"""
        return Skill(
            name="Positional Awareness",
            category=SkillCategory.COMBAT,
            description="Understanding and controlling battlefield positioning",
            base_difficulty=0.5,
            dnd_skill="Acrobatics",
            synergies=[
                SynergyBonus(
                    skill_name="Flanking Maneuvers",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Essential for flanking"
                ),
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Better defense with good positioning"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Opportunity Position",
                    description="Always find optimal positioning",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="+1 to AC from positioning"
                ),
                SpecialAbility(
                    name="Battlefield Control",
                    description="Control movement in 10ft radius",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Difficult terrain control",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_combat_timing() -> Skill:
        """Timing and rhythm in combat"""
        return Skill(
            name="Combat Timing",
            category=SkillCategory.COMBAT,
            description="Perfect timing for attacks, parries, and dodges",
            base_difficulty=0.7,
            dnd_skill="Initiative",
            synergies=[
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Better timing improves defense"
                ),
                SynergyBonus(
                    skill_name="Critical Strike",
                    bonus_type="critical_chance",
                    bonus_value=0.12,
                    description="Perfect timing enables criticals"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Riposte",
                    description="Counter-attack when enemy misses",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="triggered",
                    effect_value="Free attack on miss",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Combat Flow",
                    description="Action doesn't provoke opportunity attacks",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="No opportunity attacks",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_defensive_stance() -> Skill:
        """Defensive combat techniques"""
        return Skill(
            name="Defensive Stance",
            category=SkillCategory.COMBAT,
            description="Techniques for defense and protection",
            base_difficulty=0.4,
            dnd_skill="Armor Class",
            synergies=[
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Good positioning enhances defense"
                ),
                SynergyBonus(
                    skill_name="Shield Techniques",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Shield mastery improves defense"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Iron Wall",
                    description="Resist half damage from one attack",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Half damage resistance",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Perfect Defense",
                    description="Automatic success on one saving throw",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Auto-success on save",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_tactical_retreat() -> Skill:
        """Tactical withdrawal and repositioning"""
        return Skill(
            name="Tactical Retreat",
            category=SkillCategory.COMBAT,
            description="Strategic withdrawal and repositioning in combat",
            base_difficulty=0.5,
            dnd_skill="Disengage",
            synergies=[
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Position awareness aids retreat"
                ),
                SynergyBonus(
                    skill_name="Combat Timing",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Good timing for safe retreat"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Fighting Withdrawal",
                    description="Make attack while disengaging",
                    required_level=MasteryLevel.APPRENTICE,
                    effect_type="active",
                    effect_value="Attack + Disengage"
                ),
                SpecialAbility(
                    name="Tactical Reposition",
                    description="Move and grant ally movement",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Move ally with you",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_flanking_maneuvers() -> Skill:
        """Flanking and coordinated attacks"""
        return Skill(
            name="Flanking Maneuvers",
            category=SkillCategory.COMBAT,
            description="Coordinated attacks and flanking techniques",
            base_difficulty=0.6,
            dnd_skill="Advantage Attack",
            synergies=[
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Essential for flanking"
                ),
                SynergyBonus(
                    skill_name="Targeting Precision",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Precision enhances flanking"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Coordinated Strike",
                    description="Grant ally advantage on attack",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Ally gains advantage",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Pincer Attack",
                    description="Attack with advantage from any position",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Always have advantage",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_critical_strike() -> Skill:
        """Landing critical hits"""
        return Skill(
            name="Critical Strike",
            category=SkillCategory.COMBAT,
            description="Techniques for landing critical hits",
            base_difficulty=0.8,
            dnd_skill="Critical Hit",
            synergies=[
                SynergyBonus(
                    skill_name="Weapon Mastery",
                    bonus_type="critical_chance",
                    bonus_value=0.10,
                    description="Weapon mastery enables criticals"
                ),
                SynergyBonus(
                    skill_name="Combat Timing",
                    bonus_type="critical_chance",
                    bonus_value=0.12,
                    description="Perfect timing for criticals"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Vital Strike",
                    description="Increased critical hit range",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Critical on 19-20"
                ),
                SpecialAbility(
                    name="Devastating Critical",
                    description="Triple damage on critical hits",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="3x critical damage"
                )
            ]
        )

    @staticmethod
    def create_weapon_specialization() -> Skill:
        """Specialization in specific weapon types"""
        return Skill(
            name="Weapon Specialization",
            category=SkillCategory.COMBAT,
            description="Deep expertise with specific weapon types",
            base_difficulty=0.6,
            prerequisites=[
                SkillPrerequisite("Weapon Mastery", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Weapon Mastery",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Specialization builds on mastery"
                ),
                SynergyBonus(
                    skill_name="Targeting Precision",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Precision with specialized weapons"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Weapon Expertise",
                    description="Proficiency bonus doubled",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="2x proficiency bonus"
                ),
                SpecialAbility(
                    name="Signature Move",
                    description="Unique attack with specialized weapon",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Special weapon attack",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_armor_mastery() -> Skill:
        """Armor proficiency and mastery"""
        return Skill(
            name="Armor Mastery",
            category=SkillCategory.COMBAT,
            description="Expertise in wearing and maintaining armor",
            base_difficulty=0.3,
            dnd_skill="Armor Class",
            synergies=[
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Armor enhances defensive stance"
                ),
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.10,
                    description="Better positioning with armor"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Armor Optimization",
                    description="No armor penalty to stealth",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="No stealth penalty"
                ),
                SpecialAbility(
                    name="Living Fortress",
                    description="Resistance to non-magical damage",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Resist non-magical damage"
                )
            ]
        )

    @staticmethod
    def create_shield_techniques() -> Skill:
        """Shield combat techniques"""
        return Skill(
            name="Shield Techniques",
            category=SkillCategory.COMBAT,
            description="Advanced shield usage in combat",
            base_difficulty=0.5,
            dnd_skill="Shield",
            synergies=[
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Shields enhance defense"
                ),
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Shield positioning"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Shield Bash",
                    description="Attack with shield as bonus action",
                    required_level=MasteryLevel.APPRENTICE,
                    effect_type="active",
                    effect_value="Shield attack",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Shield Wall",
                    description="Provide cover to allies",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Half cover for allies",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_two_weapon_fighting() -> Skill:
        """Two-weapon combat style"""
        return Skill(
            name="Two-Weapon Fighting",
            category=SkillCategory.COMBAT,
            description="Fighting with two weapons simultaneously",
            base_difficulty=0.7,
            dnd_skill="Two-Weapon Fighting",
            synergies=[
                SynergyBonus(
                    skill_name="Combat Timing",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Timing critical for dual wielding"
                ),
                SynergyBonus(
                    skill_name="Targeting Precision",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Precision with multiple weapons"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Dual Strike",
                    description="Attack with both weapons as one action",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Two attacks one action",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Whirlwind Attack",
                    description="Attack all adjacent enemies",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Attack all in reach",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_ranged_combat() -> Skill:
        """Ranged weapon combat"""
        return Skill(
            name="Ranged Combat",
            category=SkillCategory.COMBAT,
            description="Expertise with ranged weapons",
            base_difficulty=0.6,
            dnd_skill="Ranged Attack",
            synergies=[
                SynergyBonus(
                    skill_name="Targeting Precision",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Critical for ranged accuracy"
                ),
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Positioning for ranged combat"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Long Shot",
                    description="No penalty for long range",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="No long range penalty"
                ),
                SpecialAbility(
                    name="Trick Shot",
                    description="Perform special ranged maneuvers",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Special ranged effects",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_unarmed_combat() -> Skill:
        """Unarmed and natural weapon combat"""
        return Skill(
            name="Unarmed Combat",
            category=SkillCategory.COMBAT,
            description="Fighting without weapons",
            base_difficulty=0.5,
            dnd_skill="Unarmed Strike",
            synergies=[
                SynergyBonus(
                    skill_name="Combat Timing",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Timing for unarmed strikes"
                ),
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.10,
                    description="Defense without weapons"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Stunning Strike",
                    description="Chance to stun opponent",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Stun save DC",
                    cooldown=1
                ),
                SpecialAbility(
                    name="One-Inch Punch",
                    description="Devastating close-range strike",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Extra damage",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_mounted_combat() -> Skill:
        """Combat while mounted"""
        return Skill(
            name="Mounted Combat",
            category=SkillCategory.COMBAT,
            description="Fighting from mountback",
            base_difficulty=0.6,
            dnd_skill="Mounted Combat",
            synergies=[
                SynergyBonus(
                    skill_name="Weapon Mastery",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description "Weapon use from mount"
                ),
                SynergyBonus(
                    skill_name="Positional Awareness",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Mount positioning"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Mounted Charge",
                    description="Devastating charge attack",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Charge with bonus damage",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Trample",
                    description="Mount can attack during movement",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Mount attack + move",
                    cooldown=2
                )
            ]
        )