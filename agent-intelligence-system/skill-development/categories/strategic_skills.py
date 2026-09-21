"""
Strategic Skills implementation for DMlogn8n

This module defines all strategic-related skills including planning,
tactics, resource management, and leadership abilities.
"""

from typing import List, Dict, Any, Optional
from ..core.skill import (
    Skill, SkillCategory, MasteryLevel, SkillPrerequisite,
    SynergyBonus, SpecialAbility
)


class StrategicSkills:
    """Factory class for creating strategic skills"""

    @staticmethod
    def create_all_strategic_skills() -> List[Skill]:
        """Create all strategic skills"""
        return [
            StrategicSkills.create_tactical_planning(),
            StrategicSkills.create_resource_management(),
            StrategicSkills.create_battlefield_strategy(),
            StrategicSkills.create_party_coordination(),
            StrategicSkills.create_risk_assessment(),
            StrategicSkills.create_contingency_planning(),
            StrategicSkills.create_logistics(),
            StrategicSkills.create_psychological_warfare(),
            StrategicSkills.create_scouting_strategy(),
            StrategicSkills.create_siege_warfare(),
            StrategicSkills.create_diplomatic_strategy(),
            StrategicSkills.create_economic_planning(),
            StrategicSkills.create_long_term_planning(),
            StrategicSkills.create_crisis_management(),
            StrategicSkills.create_alliance_building()
        ]

    @staticmethod
    def create_tactical_planning() -> Skill:
        """Tactical planning and battlefield tactics"""
        return Skill(
            name="Tactical Planning",
            category=SkillCategory.STRATEGIC,
            description="Ability to plan and execute effective combat tactics",
            base_difficulty=0.6,
            dnd_skill="Tactics",
            synergies=[
                SynergyBonus(
                    skill_name="Battlefield Strategy",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Planning enhances strategy"
                ),
                SynergyBonus(
                    skill_name="Risk Assessment",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Risk analysis improves planning"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Tactic",
                    description="Execute flawless tactical plan",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Optimal tactics",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Tactical Genius",
                    description="Instantly analyze any combat situation",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Combat analysis"
                )
            ]
        )

    @staticmethod
    def create_resource_management() -> Skill:
        """Resource and inventory management"""
        return Skill(
            name="Resource Management",
            category=SkillCategory.STRATEGIC,
            description="Efficient management of resources, supplies, and equipment",
            base_difficulty=0.5,
            dnd_skill="Resource Management",
            synergies=[
                SynergyBonus(
                    skill_name="Logistics",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Management enhances logistics"
                ),
                SynergyBonus(
                    skill_name="Long Term Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Planning aids resource use"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Efficiency",
                    description="No waste of resources",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Resource efficiency"
                ),
                SpecialAbility(
                    name="Abundant Resources",
                    description="Find resources where none exist",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Resource discovery",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_battlefield_strategy() -> Skill:
        """Battlefield strategy and positioning"""
        return Skill(
            name="Battlefield Strategy",
            category=SkillCategory.STRATEGIC,
            description="Large-scale battlefield strategy and positioning",
            base_difficulty=0.7,
            dnd_skill="Strategy",
            prerequisites=[
                SkillPrerequisite("Tactical Planning", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Tactical Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Tactics support strategy"
                ),
                SynergyBonus(
                    skill_name="Party Coordination",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Coordination enables strategy"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Battlefield Control",
                    description="Control flow of entire battle",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Battle control",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Strategic Master",
                    description="Cannot be strategically outmaneuvered",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Strategic immunity"
                )
            ]
        )

    @staticmethod
    def create_party_coordination() -> Skill:
        """Party coordination and teamwork"""
        return Skill(
            name="Party Coordination",
            category=SkillCategory.STRATEGIC,
            description="Ability to coordinate party actions and teamwork",
            base_difficulty=0.5,
            dnd_skill="Coordination",
            synergies=[
                SynergyBonus(
                    skill_name="Leadership",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Leadership enables coordination"
                ),
                SynergyBonus(
                    skill_name="Battlefield Strategy",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Strategy requires coordination"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Teamwork",
                    description="Party acts as single unit",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Unity bonus",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Symbiotic Coordination",
                    description="Party members share abilities",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Ability sharing",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_risk_assessment() -> Skill:
        """Risk assessment and threat analysis"""
        return Skill(
            name="Risk Assessment",
            category=SkillCategory.STRATEGIC,
            description="Ability to evaluate risks and threats accurately",
            base_difficulty=0.6,
            dnd_skill="Risk Analysis",
            synergies=[
                SynergyBonus(
                    skill_name="Contingency Planning",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Risk assessment enables planning"
                ),
                SynergyBonus(
                    skill_name="Tactical Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Risk analysis improves tactics"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Prediction",
                    description="Accurately predict all outcomes",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Future sight",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Risk Immunity",
                    description="Cannot be surprised by threats",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Threat awareness"
                )
            ]
        )

    @staticmethod
    def create_contingency_planning() -> Skill:
        """Contingency planning and backup strategies"""
        return Skill(
            name="Contingency Planning",
            category=SkillCategory.STRATEGIC,
            description="Planning for unexpected events and backup strategies",
            base_difficulty=0.6,
            dnd_skill="Contingency Planning",
            synergies=[
                SynergyBonus(
                    skill_name="Risk Assessment",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Risk assessment informs contingencies"
                ),
                SynergyBonus(
                    skill_name="Crisis Management",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Planning aids crisis response"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Backup",
                    description="Always have perfect contingency",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Backup plan",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Plan B Master",
                    description="Never fail, always have backup",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Always prepared"
                )
            ]
        )

    @staticmethod
    def create_logistics() -> Skill:
        """Logistics and supply chain management"""
        return Skill(
            name="Logistics",
            category=SkillCategory.STRATEGIC,
            description="Management of supplies, transportation, and distribution",
            base_difficulty=0.5,
            dnd_skill="Logistics",
            synergies=[
                SynergyBonus(
                    skill_name="Resource Management",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Management enables logistics"
                ),
                SynergyBonus(
                    skill_name="Long Term Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Planning supports logistics"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Supply",
                    description="Never run out of supplies",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="passive",
                    effect_value="Unlimited supplies"
                ),
                SpecialAbility(
                    name="Logistical Master",
                    description="Supply entire army effortlessly",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Mass logistics",
                    cooldown=1
                )
            ]
        )

    @staticmethod
    def create_psychological_warfare() -> Skill:
        """Psychological warfare and morale manipulation"""
        return Skill(
            name="Psychological Warfare",
            category=SkillCategory.STRATEGIC,
            description="Use of psychological tactics to weaken enemies",
            base_difficulty=0.7,
            dnd_skill="Psychological Tactics",
            synergies=[
                SynergyBonus(
                    skill_name="Intimidation",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Intimidation aids psychological warfare"
                ),
                SynergyBonus(
                    skill_name="Deception",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Deception supports psychological tactics"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Terror Tactics",
                    description="Break enemy morale completely",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Morale destruction",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Mind Games",
                    description="Drive enemies insane",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Psychological damage",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_scouting_strategy() -> Skill:
        """Strategic scouting and intelligence gathering"""
        return Skill(
            name="Scouting Strategy",
            category=SkillCategory.STRATEGIC,
            description="Strategic use of scouts and intelligence gathering",
            base_difficulty=0.6,
            dnd_skill="Scouting",
            synergies=[
                SynergyBonus(
                    skill_name="Scouting",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Scouting skills enable strategy"
                ),
                SynergyBonus(
                    skill_name="Risk Assessment",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Intelligence informs risk assessment"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Intelligence",
                    description="Know everything about enemy",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Complete intelligence",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Spy Network",
                    description="Network of informers everywhere",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Intelligence network"
                )
            ]
        )

    @staticmethod
    def create_siege_warfare() -> Skill:
        """Siege warfare and fortification strategies"""
        return Skill(
            name="Siege Warfare",
            category=SkillCategory.STRATEGIC,
            description="Strategies for sieges and fortification assaults",
            base_difficulty=0.7,
            dnd_skill="Siege Tactics",
            prerequisites=[
                SkillPrerequisite("Tactical Planning", MasteryLevel.APPRENTICE),
                SkillPrerequisite("Battlefield Strategy", MasteryLevel.APPRENTICE)
            ],
            synergies=[
                SynergyBonus(
                    skill_name="Battlefield Strategy",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Strategy essential for sieges"
                ),
                SynergyBonus(
                    skill_name="Logistics",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Sieges require logistics"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Siege",
                    description="Take any fortress",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Fortress breaker",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Siege Master",
                    description="Impossible to besiege",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Siege immunity"
                )
            ]
        )

    @staticmethod
    def create_diplomatic_strategy() -> Skill:
        """Strategic diplomacy and negotiations"""
        return Skill(
            name="Diplomatic Strategy",
            category=SkillCategory.STRATEGIC,
            description="Long-term diplomatic planning and alliance management",
            base_difficulty=0.6,
            dnd_skill="Diplomatic Strategy",
            synergies=[
                SynergyBonus(
                    skill_name="Diplomacy",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Diplomacy enables strategy"
                ),
                SynergyBonus(
                    skill_name="Alliance Building",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Strategy builds alliances"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Master Diplomat",
                    description="Resolve any diplomatic situation",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Diplomatic solution",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Peace Maker",
                    description="Force peace between enemies",
                    required_level=MasteryLevel.MASTER,
                    effect_type="active",
                    effect_value="Enforced peace",
                    cooldown=3
                )
            ]
        )

    @staticmethod
    def create_economic_planning() -> Skill:
        """Economic strategy and resource planning"""
        return Skill(
            name="Economic Planning",
            category=SkillCategory.STRATEGIC,
            description="Long-term economic strategy and wealth management",
            base_difficulty=0.6,
            dnd_skill="Economic Strategy",
            synergies=[
                SynergyBonus(
                    skill_name="Resource Management",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Management enables economics"
                ),
                SynergyBonus(
                    skill_name="Long Term Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Planning supports economics"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Economic Genius",
                    description="Create wealth from nothing",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Wealth creation",
                    cooldown=2
                ),
                SpecialAbility(
                    name="Fortune Maker",
                    description="Unlimited economic resources",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Economic mastery"
                )
            ]
        )

    @staticmethod
    def create_long_term_planning() -> Skill:
        """Long-term strategic planning"""
        return Skill(
            name="Long Term Planning",
            category=SkillCategory.STRATEGIC,
            description="Ability to plan and execute long-term strategies",
            base_difficulty=0.7,
            dnd_skill="Long Term Strategy",
            synergies=[
                SynergyBonus(
                    skill_name="Tactical Planning",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Tactics support long-term plans"
                ),
                SynergyBonus(
                    skill_name="Resource Management",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Management enables long-term planning"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Perfect Plan",
                    description="Execute flawless long-term strategy",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Strategic perfection",
                    cooldown=5
                ),
                SpecialAbility(
                    name="Strategic Vision",
                    description="See all consequences of actions",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Future consequences"
                )
            ]
        )

    @staticmethod
    def create_crisis_management() -> Skill:
        """Crisis management and emergency response"""
        return Skill(
            name="Crisis Management",
            category=SkillCategory.STRATEGIC,
            description="Ability to handle emergencies and crisis situations",
            base_difficulty=0.6,
            dnd_skill="Crisis Response",
            synergies=[
                SynergyBonus(
                    skill_name="Contingency Planning",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Planning aids crisis response"
                ),
                SynergyBonus(
                    skill_name="Risk Assessment",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Risk assessment prevents crises"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Crisis Master",
                    description="Handle any crisis perfectly",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Crisis solution",
                    cooldown=1
                ),
                SpecialAbility(
                    name="Disaster Prevention",
                    description="Prevent crises before they happen",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Crisis prevention"
                )
            ]
        )

    @staticmethod
    def create_alliance_building() -> Skill:
        """Alliance building and network management"""
        return Skill(
            name="Alliance Building",
            category=SkillCategory.STRATEGIC,
            description="Building and maintaining strategic alliances",
            base_difficulty=0.6,
            dnd_skill="Alliance Building",
            synergies=[
                SynergyBonus(
                    skill_name="Diplomatic Strategy",
                    bonus_type="success_chance",
                    bonus_value=0.20,
                    description="Diplomacy builds alliances"
                ),
                SynergyBonus(
                    skill_name="Leadership",
                    bonus_type="success_chance",
                    bonus_value=0.15,
                    description="Leadership enables alliance building"
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Master Alliance",
                    description="Build perfect strategic alliance",
                    required_level=MasteryLevel.EXPERT,
                    effect_type="active",
                    effect_value="Perfect alliance",
                    cooldown=3
                ),
                SpecialAbility(
                    name="Network Master",
                    description="Allies everywhere, always",
                    required_level=MasteryLevel.MASTER,
                    effect_type="passive",
                    effect_value="Universal alliance"
                )
            ]
        )