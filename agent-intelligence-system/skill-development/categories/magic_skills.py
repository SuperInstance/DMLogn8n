"""
Magic Skills implementation for DMlogn8n

This module defines all magic-related skills including spell selection,
mana management, combos, and magical abilities.
"""

from typing import List, Dict, Any, Optional
from ..core.skill import (
    Skill, SkillCategory, MasteryLevel, SkillPrerequisite,
    SynergyBonus, SpecialAbility
)


class MagicSkills:
    """Factory class for creating magic skills"""

    @staticmethod
    def create_all_magic_skills() -> List[Skill]:
        """Create all magic skills"""
        return [
            MagicSkills.create_spell_selection(),
            MagicSkills.create_mana_management(),
            MagicSkills.create_spell_combos(),
            MagicSkills.create_magical_theory(),
            MagicSkills.create_arcane_focus(),
            MagicSkills.create_elemental_mastery(),
            MagicSkills.create_enchantment(),
            MagicSkills.create_illusion(),
            MagicSkills.create_necromancy(),
            MagicSkills.create_divination(),
            MagicSkills.create_abjuration(),
            MagicSkills.create_conjuration(),
            MagicSkills.create_transmutation(),
            MagicSkills.create_ritual_magic(),
            MagicSkills.create_spell_crafting()
        ]

    @staticmethod
    def create_spell_selection() -> Skill:
        """Spell selection and preparation skills"""
        return Skill(
            name="Spell Selection",
            category=SkillCategory.MAGIC,
            description="Ability to choose optimal spells for situations",
            base_difficulty=0.6,
            dnd_skill="Spell Preparation",
            synergies=[
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Theory informs spell selection"
                ),
                SynergyBonus(
                    skill_name="Mana Management",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Efficiency affects spell choices"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Preparation",
                    description="Always have right spell prepared",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Perfect spell selection",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Spell Mastery",
                    description="Cast signature spell without using slot",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Free signature spell"
                )
            ]
        )

    @staticmethod
    def create_mana_management() -> Skill:
        """Mana and magical resource management"""
        return Skill(
            name="Mana Management",
            category=SkillCategory.MAGIC,
            description="Efficient use and conservation of magical energy",
            base_difficulty=0.5,
            dnd_skill="Mana Control",
            synergies=[
                SynergyBonus(
                    skill_name="Arcane Focus",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Focus improves mana efficiency"
                ),
                SynergyBonus(
                    skill_name="Spell Combos",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Efficient combos save mana"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Mana Efficiency",
                    description="Reduce mana cost of spells",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="-1 spell slot cost"
                ),
                SpecialAbility(
                    name="Mana Regeneration",
                    description="Recover spell slots during rest",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Recover spell slots",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Infinite Mana",
                    description="Never run out of magical energy",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Unlimited casting"
                )
            ]
        )

    @staticmethod
    def create_spell_combos() -> Skill:
        """Spell combination and chaining skills"""
        return Skill(
            name="Spell Combos",
            category=SkillCategory.MAGIC,
            description="Ability to combine spells for greater effect",
            base_difficulty=0.7,
            dnd_skill="Spell Combination",
            prerequisites=[
                SkillPrerequisite("Spell Selection", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Mana Management", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Theory enables combos"
                ),
                SynergyBonus(
                    skill_name="Arcane Focus",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Focus required for combos"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Spell Chain",
                    description="Cast two spells as one action",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Dual spell casting",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Meta-Magic",
                    description="Enhance spells with additional effects",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Spell enhancement",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_magical_theory() -> Skill:
        """Understanding of magical principles"""
        return Skill(
            name="Magical Theory",
            category=SkillCategory.MAGIC,
            description="Deep understanding of how magic works",
            base_difficulty=0.6,
            dnd_skill="Arcana",
            synergies=[
                SynergyBonus(
                    skill_name="Spell Selection",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Theory informs selection"
                ),
                SynergyBonus(
                    skill_name="Spell Crafting",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Theory essential for crafting"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Magical Analysis",
                    description="Understand any magical effect",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Analyze magic",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Archmage Knowledge",
                    description="Know all magical secrets",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Complete magical knowledge"
                )
            ]
        )

    @staticmethod
    def create_arcane_focus() -> Skill:
        """Concentration and magical focus"""
        return Skill(
            name="Arcane Focus",
            category=SkillCategory.MAGIC,
            description="Ability to maintain concentration and magical focus",
            base_difficulty=0.5,
            dnd_skill="Concentration",
            synergies=[
                SynergyBonus(
                    skill_name="Mana Management",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Focus improves mana efficiency"
                ),
                SynergyBonus(
                    skill_name="Spell Combos",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Focus required for combos"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Iron Will",
                    description="Cannot lose concentration",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Perfect concentration"
                ),
                SpecialAbility(
                    name="Arcane Trance",
                    description="Enhanced magical abilities",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Enhanced casting",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_elemental_mastery() -> Skill:
        """Mastery of elemental magic"""
        return Skill(
            name="Elemental Mastery",
            category=SkillCategory.MAGIC,
            description="Control over natural elements",
            base_difficulty=0.6,
            dnd_skill="Elemental Magic",
            synergies=[
                SynergyBonus(
                    skill_name="Spell Selection",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Element knowledge aids selection"
                ),
                SynergyBonus(
                    skill_name="Natural Knowledge",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Nature understanding helps elements"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Elemental Command",
                    description="Control element completely",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Element control",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Elemental Immunity",
                    description="Immune to elemental damage",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Elemental immunity"
                )
            ]
        )

    @staticmethod
    def create_enchantment() -> Skill:
        """Enchantment and charm magic"""
        return Skill(
            name="Enchantment",
            category=SkillCategory.MAGIC,
            description="Magic that influences minds and behavior",
            base_difficulty=0.7,
            dnd_skill="Enchantment",
            synergies=[
                SynergyBonus(
                    skill_name="Persuasion",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Social skills enhance enchantment"
                ),
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Theory informs enchantment"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Mass Charm",
                    description="Charm multiple targets",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Area charm",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Absolute Control",
                    description="Complete mental domination",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Mind control",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_illusion() -> Skill:
        """Illusion and phantom magic"""
        return Skill(
            name="Illusion",
            category=SkillCategory.MAGIC,
            description="Creating false images and sensations",
            base_difficulty=0.6,
            dnd_skill="Illusion",
            synergies=[
                SynergyBonus(
                    skill_name="Deception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Deception aids illusion"
                ),
                SynergyBonus(
                    skill_name="Performance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Performance enhances illusion"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Illusion",
                    description="Create indistinguishable illusions",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Perfect illusion",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Reality Warping",
                    description="Illusions become temporarily real",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Reality bending",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_necromancy() -> Skill:
        """Necromancy and death magic"""
        return Skill(
            name="Necromancy",
            category=SkillCategory.MAGIC,
            description="Magic dealing with death, undeath, and life force",
            base_difficulty=0.8,
            dnd_skill="Necromancy",
            synergies=[
                SynergyBonus(
                    skill_name="Intimidation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Necromancy intimidates"
                ),
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Dark theory knowledge"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Command Undead",
                    description="Control undead creatures",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Undead control",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Touch of Death",
                    description="Instantly kill weak targets",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Death touch",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_divination() -> Skill:
        """Divination and knowledge magic"""
        return Skill(
            name="Divination",
            category=SkillCategory.MAGIC,
            description="Magic that reveals information and secrets",
            base_difficulty=0.6,
            dnd_skill="Divination",
            synergies=[
                SynergyBonus(
                    skill_name="Investigation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Investigation complements divination"
                ),
                SynergyBonus(
                    skill_name="Perception",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Perception enhanced by divination"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="True Sight",
                    description="See all things as they truly are",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Perfect sight",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Omniscience",
                    description="Know anything you desire",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Complete knowledge",
                    cooldown=5
                )
            ]
        )

    @staticmethod
    def create_abjuration() -> Skill:
        """Abjuration and protective magic"""
        return Skill(
            name="Abjuration",
            category=SkillCategory.MAGIC,
            description="Magic that protects and wards",
            base_difficulty=0.5,
            dnd_skill="Abjuration",
            synergies=[
                SynergyBonus(
                    skill_name="Defensive Stance",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Defense complements abjuration"
                ),
                SynergyBonus(
                    skill_name="Arcane Focus",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Focus enhances protection"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Ward",
                    description="Immunity to spell type",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Spell immunity",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Absolute Defense",
                    description="Cannot be harmed by magic",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Magic immunity",
                    cooldown=5
                )
            ]
        )

    @staticmethod
    def create_conjuration() -> Skill:
        """Conjuration and summoning magic"""
        return Skill(
            name="Conjuration",
            category=SkillCategory.MAGIC,
            description="Magic that creates objects and summons creatures",
            base_difficulty=0.6,
            dnd_skill="Conjuration",
            synergies=[
                SynergyBonus(
                    skill_name="Natural Knowledge",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Nature aids summoning"
                ),
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Theory informs conjuration"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Summon",
                    description="Summon any creature",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Universal summoning",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Creation Master",
                    description="Create anything from nothing",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="True creation",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_transmutation() -> Skill:
        """Transmutation and alteration magic"""
        return Skill(
            name="Transmutation",
            category=SkillCategory.MAGIC,
            description="Magic that changes and transforms",
            base_difficulty=0.6,
            dnd_skill="Transmutation",
            synergies=[
                SynergyBonus(
                    skill_name="Natural Knowledge",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Understanding transformation"
                ),
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Theory of transformation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Transform",
                    description="Change anything to anything",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Universal transformation",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Reality Shaping",
                    description="Reshape reality itself",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Reality alteration",
                    cooldown=5
                )
            ]
        )

    @staticmethod
    def create_ritual_magic() -> Skill:
        """Ritual and ceremonial magic"""
        return Skill(
            name="Ritual Magic",
            category=SkillCategory.MAGIC,
            description="Complex magical ceremonies and rituals",
            base_difficulty=0.7,
            dnd_skill="Ritual Casting",
            prerequisites=[
                SkillPrerequisite("Magical Theory", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Arcane Focus", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Theory essential for rituals"
                ),
                SynergyBonus(
                    skill_name="Arcane Focus",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Focus required for rituals"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Quick Ritual",
                    description="Perform rituals instantly",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Instant ritual",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Grand Ritual",
                    description="Perform world-changing rituals",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Major effect",
                    cooldown=10
                )
            ]
        )

    @staticmethod
    def create_spell_crafting() -> Skill:
        """Creating new spells and magical items"""
        return Skill(
            name="Spell Crafting",
            category=SkillCategory.MAGIC,
            description="Creating new spells and magical items",
            base_difficulty=0.8,
            dnd_skill="Spellcraft",
            prerequisites=[
                SkillPrerequisite("Magical Theory", MasteryLevel.JOURNEYMAN),
                SkillPrerequisite("Spell Selection", MasteryLevel.JOURNEYMAN)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Magical Theory",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Theory essential for crafting"
                ),
                SynergyBonus(
                    skill_name="Elemental Mastery",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Elements help crafting"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Spell Innovation",
                    description="Create new spells instantly",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Instant spell creation",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Archmage Creation",
                    description="Create legendary magical items",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Legendary crafting",
                    cooldown=5
                )
            ]
        )