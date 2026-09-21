"""
Social Skills implementation for DMlogn8n

This module defines all social-related skills including persuasion,
deception, intimidation, and interpersonal abilities.
"""

from typing import List, Dict, Any, Optional
from ..core.skill import (
    Skill, SkillCategory, MasteryLevel, SkillPrerequisite,
    SynergyBonus, SpecialAbility
)


class SocialSkills:
    """Factory class for creating social skills"""

    @staticmethod
    def create_all_social_skills() -> List[Skill]:
        """Create all social skills"""
        return [
            SocialSkills.create_persuasion(),
            SocialSkills.create_deception(),
            SocialSkills.create_intimidation(),
            SocialSkills.create_performance(),
            SocialSkills.create_negotiation(),
            SocialSkills.create_empathy(),
            SocialSkills.create_leadership(),
            SocialSkills.create_diplomacy(),
            SocialSkills.create_seduction(),
            SocialSkills.create_intimidation_presence(),
            SocialSkills.create_public_speaking(),
            SocialSkills.create_lie_detection(),
            SocialSkills.create_charisma(),
            SocialSkills.create_social_manipulation(),
            SocialSkills.create_mediation()
        ]

    @staticmethod
    def create_persuasion() -> Skill:
        """Persuasion and influence skills"""
        return Skill(
            name="Persuasion",
            category=SkillCategory.SOCIAL,
            description="Ability to convince others through logical arguments and appeal",
            base_difficulty=0.5,
            dnd_skill="Persuasion",
            synergies=[
                SynergyBonus(
                    skill_name="Negotiation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Persuasion enhances negotiation"
                ),
                SynergyBonus(
                    skill_name="Diplomacy",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Diplomatic persuasion"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Silver Tongue",
                    description="Reroll failed persuasion check",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Reroll persuasion",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Compelling Argument",
                    description="Force target to consider your point",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Advantage on persuasion",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Master Orator",
                    description="Cannot fail persuasion against willing targets",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Auto-success on willing targets"
                )
            ]
        )

    @staticmethod
    def create_deception() -> Skill:
        """Deception and lying skills"""
        return Skill(
            name="Deception",
            category=SkillCategory.SOCIAL,
            description="Ability to convincingly lie and mislead others",
            base_difficulty=0.6,
            dnd_skill="Deception",
            synergies=[
                SynergyBonus(
                    skill_name="Social Manipulation",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Manipulation enhances deception"
                ),
                SynergyBonus(
                    skill_name="Lie Detection",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Understanding lies helps create them"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Lie",
                    description="Lie cannot be detected by normal means",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Undetectable lie",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Misdirection",
                    description="Redirect attention from your actions",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Create diversion",
                    cooldown=2
                )
            ]
        )

    @staticmethod
    def create_intimidation() -> Skill:
        """Intimidation and coercion skills"""
        return Skill(
            name="Intimidation",
            category=SkillCategory.SOCIAL,
            description="Ability to frighten and coerce others through threats",
            base_difficulty=0.4,
            dnd_skill="Intimidation",
            synergies=[
                SynergyBonus(
                    skill_name="Intimidation Presence",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Presence enhances intimidation"
                ),
                SynergyBonus(
                    skill_name="Leadership",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Leadership adds to intimidation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Fearsome Presence",
                    description="Cause fear in weaker targets",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Frighten target",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Broken Will",
                    description="Force truth from intimidated target",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Force truth",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_performance() -> Skill:
        """Performance and entertainment skills"""
        return Skill(
            name="Performance",
            category=SkillCategory.SOCIAL,
            description="Ability to entertain and captivate audiences",
            base_difficulty=0.5,
            dnd_skill="Performance",
            synergies=[
                SynergyBonus(
                    skill_name="Public Speaking",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Speaking enhances performance"
                ),
                SynergyBonus(
                    skill_name="Charisma",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Charisma improves performance"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Captivating Performance",
                    description="Hold audience completely enthralled",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Charm all viewers",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Legend Maker",
                    description="Create performance that becomes legend",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Legendary effect",
                    cooldown=5
                )
            ]
        )

    @staticmethod
    def create_negotiation() -> Skill:
        """Negotiation and bargaining skills"""
        return Skill(
            name="Negotiation",
            category=SkillCategory.SOCIAL,
            description="Ability to broker deals and reach favorable agreements",
            base_difficulty=0.6,
            dnd_skill="Negotiation",
            synergies=[
                SynergyBonus(
                    skill_name="Persuasion",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Persuasion aids negotiation"
                ),
                SynergyBonus(
                    skill_name="Mediation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Mediation skills help negotiation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Win-Win Deal",
                    description="Both parties gain from negotiation",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Mutual benefit",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Ironclad Contract",
                    description="Create unbreakable agreement",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Magically binding contract",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_empathy() -> Skill:
        """Empathy and emotional intelligence"""
        return Skill(
            name="Empathy",
            category=SkillCategory.SOCIAL,
            description="Ability to understand and share feelings of others",
            base_difficulty=0.4,
            dnd_skill="Insight",
            synergies=[
                SynergyBonus(
                    skill_name="Lie Detection",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Empathy reveals truth"
                ),
                SynergyBonus(
                    skill_name="Mediation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Understanding emotions aids mediation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Emotional Resonance",
                    description="Feel others' emotions as your own",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Sense emotions"
                ),
                SpecialAbility(
                    name="Empathic Healing",
                    description="Heal emotional trauma",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Cure emotional effects",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_leadership() -> Skill:
        """Leadership and command skills"""
        return Skill(
            name="Leadership",
            category=SkillCategory.SOCIAL,
            description="Ability to lead and inspire others",
            base_difficulty=0.5,
            dnd_skill="Leadership",
            synergies=[
                SynergyBonus(
                    skill_name="Charisma",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Charisma enhances leadership"
                ),
                SynergyBonus(
                    skill_name="Public Speaking",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Speaking skills help leadership"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Rallying Cry",
                    description="Inspire allies to fight harder",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Buff allies",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Born Leader",
                    description="Followers gain bonuses near you",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Aura of leadership"
                )
            ]
        )

    @staticmethod
    def create_diplomacy() -> Skill:
        """Diplomacy and statecraft"""
        return Skill(
            name="Diplomacy",
            category=SkillCategory.SOCIAL,
            description="Ability to navigate complex political and social situations",
            base_difficulty=0.7,
            dnd_skill="Diplomacy",
            prerequisites=[
                SkillPrerequisite("Persuasion", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Negotiation", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Persuasion",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Persuasion fundamental to diplomacy"
                ),
                SynergyBonus(
                    skill_name="Negotiation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Negotiation essential in diplomacy"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Diplomatic Immunity",
                    description="Protected from hostile actions",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Protection from harm"
                ),
                SpecialAbility(
                    name="Peace Treaty",
                    description="Force peaceful resolution",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Enforce peace",
                    cooldown=5
                )
            ]
        )

    @staticmethod
    def create_seduction() -> Skill:
        """Seduction and charm skills"""
        return Skill(
            name="Seduction",
            category=SkillCategory.SOCIAL,
            description="Ability to charm and attract others romantically",
            base_difficulty=0.6,
            dnd_skill="Seduction",
            synergies=[
                SynergyBonus(
                    skill_name="Charisma",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Charisma enhances seduction"
                ),
                SynergyBonus(
                    skill_name="Performance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Performance aids seduction"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Irresistible Charm",
                    description="Target cannot refuse reasonable requests",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Charm effect",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Heartbreaker",
                    description="Can end relationships cleanly",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Clean breakup",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_intimidation_presence() -> Skill:
        """Physical presence and intimidation"""
        return Skill(
            name="Intimidation Presence",
            category=SkillCategory.SOCIAL,
            description="Physical presence that naturally intimidates others",
            base_difficulty=0.3,
            dnd_skill="Presence",
            synergies=[
                SynergyBonus(
                    skill_name="Intimidation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Presence enhances intimidation"
                ),
                SynergyBonus(
                    skill_name="Leadership",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Commanding presence"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Aura of Fear",
                    description="Weak enemies avoid you",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Fear aura"
                ),
                SpecialAbility(
                    name="Terrifying Presence",
                    description="Paralyze with fear",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Paralyze target",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_public_speaking() -> Skill:
        """Public speaking and oratory"""
        return Skill(
            name="Public Speaking",
            category=SkillCategory.SOCIAL,
            description="Ability to address and move crowds",
            base_difficulty=0.5,
            dnd_skill="Public Speaking",
            synergies=[
                SynergyBonus(
                    skill_name="Leadership",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Speaking enhances leadership"
                ),
                SynergyBonus(
                    skill_name="Performance",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Performance aids speaking"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Rousing Speech",
                    description="Inspire crowd to action",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="active",
                    effect_value="Inspire crowd",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Silver Voice",
                    description="Voice carries magical persuasive power",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Magical voice"
                )
            ]
        )

    @staticmethod
    def create_lie_detection() -> Skill:
        """Detecting lies and deception"""
        return Skill(
            name="Lie Detection",
            category=SkillCategory.SOCIAL,
            description="Ability to detect when others are lying",
            base_difficulty=0.6,
            dnd_skill="Insight",
            synergies=[
                SynergyBonus(
                    skill_name="Empathy",
                    bonus_type="success_chance",
                    bonus_value=0.25,
                    description="Empathy reveals deception"
                ),
                SynergyBonus(
                    skill_name="Deception",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Understanding lies helps detect them"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Truth Sense",
                    description="Always know when directly lied to",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Detect lies"
                ),
                SpecialAbility(
                    name="Compel Truth",
                    description="Force target to speak truth",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Force truth",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_charisma() -> Skill:
        """General charisma and social grace"""
        return Skill(
            name="Charisma",
            category=SkillCategory.SOCIAL,
            description="Natural charm and social attractiveness",
            base_difficulty=0.4,
            dnd_skill="Charisma",
            synergies=[
                SynergyBonus(
                    skill_name="Persuasion",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Charisma enhances persuasion"
                ),
                SynergyBonus(
                    skill_name="Seduction",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Charisma aids seduction"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Natural Charm",
                    description="People naturally like and trust you",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Natural attraction"
                ),
                SpecialAbility(
                    name="Divine Charisma",
                    description="Almost supernatural charm",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Superhuman charm"
                )
            ]
        )

    @staticmethod
    def create_social_manipulation() -> Skill:
        """Social manipulation and intrigue"""
        return Skill(
            name="Social Manipulation",
            category=SkillCategory.SOCIAL,
            description="Ability to manipulate social situations and people",
            base_difficulty=0.8,
            dnd_skill="Manipulation",
            prerequisites=[
                SkillPrerequisite("Deception", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Persuasion", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Deception",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Deception essential for manipulation"
                ),
                SynergyBonus(
                    skill_name="Lie Detection",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Understanding truth helps manipulation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Puppet Master",
                    description="Manipulate others without their knowledge",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Secret manipulation",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Social Web",
                    description="Understand and control social networks",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Network control"
                )
            ]
        )

    @staticmethod
    def create_mediation() -> Skill:
        """Mediation and conflict resolution"""
        return Skill(
            name="Mediation",
            category=SkillCategory.SOCIAL,
            description="Ability to resolve conflicts between others",
            base_difficulty=0.6,
            dnd_skill="Mediation",
            synergies=[
                SynergyBonus(
                    skill_name="Empathy",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Empathy essential for mediation"
                ),
                SynergyBonus(
                    skill_name="Negotiation",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Negotiation aids mediation"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Mediator",
                    description="Always find common ground",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Guaranteed resolution",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Peacekeeper",
                    description="Cannot fail to stop conflicts",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Conflict prevention"
                )
            ]
        )