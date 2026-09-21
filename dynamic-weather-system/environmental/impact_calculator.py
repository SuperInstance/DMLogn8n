"""
Environmental Impact Calculator

Calculates and manages the effects of weather on gameplay mechanics
including movement, combat, exploration, and environmental interactions.
"""

import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..core.weather_state import WeatherState
from ..core.weather_types import WeatherType, WeatherSeverity, ClimateZone
from .movement_effects import MovementEffects
from .combat_modifiers import CombatModifiers
from .spell_effects import SpellEffects
from .creature_behavior import CreatureBehavior
from .terrain_effects import TerrainEffects
from .visibility_system import VisibilitySystem

@dataclass
class EnvironmentalImpact:
    """Represents the environmental impact of weather conditions."""

    # Movement impacts
    movement_speed_modifier: float = 1.0
    endurance_cost_modifier: float = 1.0
    navigation_difficulty_modifier: float = 1.0
    terrain_difficulty_modifier: float = 1.0

    # Combat impacts
    ranged_attack_modifier: int = 0
    melee_attack_modifier: int = 0
    defense_modifier: int = 0
    initiative_modifier: int = 0
    concentration_dc_modifier: int = 0

    # Spell impacts
    spell_save_dc_modifier: int = 0
    spell_attack_modifier: int = 0
    spell_damage_modifier: float = 1.0
    spell_duration_modifier: float = 1.0
    components_difficulty: Dict[str, int] = None  # verbal, somatic, material

    # Sensory impacts
    visibility_range_modifier: float = 1.0
    perception_modifier: int = 0
    stealth_modifier: int = 0
    investigation_modifier: int = 0

    # Environmental hazards
    damage_per_time: Dict[str, int] = None  # damage_type -> damage_per_interval
    saving_throws_required: List[str] = None
    equipment_risks: Dict[str, float] = None  # equipment_type -> risk_factor

    # Creature impacts
    creature_activity_modifier: float = 1.0
    npc_behavior_modifier: Dict[str, Any] = None
    wildlife_encounter_chance: float = 1.0

    # Special effects
    special_conditions: List[str] = None
    magical_auras: List[str] = None
    environmental_interactions: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.components_difficulty is None:
            self.components_difficulty = {"verbal": 0, "somatic": 0, "material": 0}
        if self.damage_per_time is None:
            self.damage_per_time = {}
        if self.saving_throws_required is None:
            self.saving_throws_required = []
        if self.equipment_risks is None:
            self.equipment_risks = {}
        if self.npc_behavior_modifier is None:
            self.npc_behavior_modifier = {}
        if self.special_conditions is None:
            self.special_conditions = []
        if self.magical_auras is None:
            self.magical_auras = []
        if self.environmental_interactions is None:
            self.environmental_interactions = []

class EnvironmentalImpactCalculator:
    """Calculates comprehensive environmental impacts from weather conditions."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Initialize sub-systems
        self.movement_effects = MovementEffects(config.get('movement', {}))
        self.combat_modifiers = CombatModifiers(config.get('combat', {}))
        self.spell_effects = SpellEffects(config.get('spells', {}))
        self.creature_behavior = CreatureBehavior(config.get('creatures', {}))
        self.terrain_effects = TerrainEffects(config.get('terrain', {}))
        self.visibility_system = VisibilitySystem(config.get('visibility', {}))

        # Impact multipliers
        self.severity_multipliers = {
            WeatherSeverity.CALM: 0.0,
            WeatherSeverity.MILD: 0.3,
            WeatherSeverity.MODERATE: 0.6,
            WeatherSeverity.SEVERE: 1.0,
            WeatherSeverity.EXTREME: 1.5,
            WeatherSeverity.CATASTROPHIC: 2.0
        }

    def calculate_impact(self, weather_state: WeatherState,
                        terrain_type: str = "plains",
                        time_of_day: str = "day",
                        character_level: int = 1) -> EnvironmentalImpact:
        """Calculate comprehensive environmental impact."""

        impact = EnvironmentalImpact()

        # Get severity multiplier
        severity_multiplier = self.severity_multipliers[weather_state.severity]

        # Calculate movement impacts
        movement_impact = self.movement_effects.calculate_movement_impact(
            weather_state, terrain_type
        )
        impact.movement_speed_modifier = movement_impact['speed_modifier']
        impact.endurance_cost_modifier = movement_impact['endurance_modifier']
        impact.navigation_difficulty_modifier = movement_impact['navigation_modifier']
        impact.terrain_difficulty_modifier = movement_impact['terrain_modifier']

        # Calculate combat impacts
        combat_impact = self.combat_modifiers.calculate_combat_impact(
            weather_state, terrain_type
        )
        impact.ranged_attack_modifier = combat_impact['ranged_modifier']
        impact.melee_attack_modifier = combat_impact['melee_modifier']
        impact.defense_modifier = combat_impact['defense_modifier']
        impact.initiative_modifier = combat_impact['initiative_modifier']
        impact.concentration_dc_modifier = combat_impact['concentration_dc']

        # Calculate spell impacts
        spell_impact = self.spell_effects.calculate_spell_impact(
            weather_state, character_level
        )
        impact.spell_save_dc_modifier = spell_impact['save_dc_modifier']
        impact.spell_attack_modifier = spell_impact['attack_modifier']
        impact.spell_damage_modifier = spell_impact['damage_modifier']
        impact.spell_duration_modifier = spell_impact['duration_modifier']
        impact.components_difficulty = spell_impact['components_difficulty']

        # Calculate sensory impacts
        sensory_impact = self._calculate_sensory_impact(weather_state, time_of_day)
        impact.visibility_range_modifier = sensory_impact['visibility_modifier']
        impact.perception_modifier = sensory_impact['perception_modifier']
        impact.stealth_modifier = sensory_impact['stealth_modifier']
        impact.investigation_modifier = sensory_impact['investigation_modifier']

        # Calculate environmental hazards
        hazard_impact = self._calculate_hazard_impact(weather_state)
        impact.damage_per_time = hazard_impact['damage_per_time']
        impact.saving_throws_required = hazard_impact['saving_throws']
        impact.equipment_risks = hazard_impact['equipment_risks']

        # Calculate creature impacts
        creature_impact = self.creature_behavior.calculate_creature_impact(
            weather_state, terrain_type
        )
        impact.creature_activity_modifier = creature_impact['activity_modifier']
        impact.npc_behavior_modifier = creature_impact['npc_behavior']
        impact.wildlife_encounter_chance = creature_impact['encounter_modifier']

        # Apply terrain effects
        terrain_impact = self.terrain_effects.calculate_terrain_impact(
            weather_state, terrain_type
        )
        impact.special_conditions.extend(terrain_impact['special_conditions'])
        impact.environmental_interactions.extend(terrain_impact['interactions'])

        # Apply magical effects
        if weather_state.magical_intensity > 0:
            magical_impact = self._calculate_magical_impact(weather_state)
            impact.magical_auras.extend(magical_impact['auras'])
            impact.special_conditions.extend(magical_impact['conditions'])

        # Apply severity scaling
        self._apply_severity_scaling(impact, severity_multiplier)

        return impact

    def _calculate_sensory_impact(self, weather_state: WeatherState,
                                 time_of_day: str) -> Dict[str, Any]:
        """Calculate impacts on senses and perception."""

        impact = {
            'visibility_modifier': 1.0,
            'perception_modifier': 0,
            'stealth_modifier': 0,
            'investigation_modifier': 0
        }

        # Visibility impact
        if weather_state.visibility < 1.0:
            impact['visibility_modifier'] = weather_state.visibility / 10.0
            impact['perception_modifier'] -= 5
            impact['investigation_modifier'] -= 3
        elif weather_state.visibility < 5.0:
            impact['visibility_modifier'] = weather_state.visibility / 10.0
            impact['perception_modifier'] -= 2
            impact['stealth_modifier'] += 2
        elif weather_state.visibility < 10.0:
            impact['visibility_modifier'] = 0.8
            impact['stealth_modifier'] += 1

        # Time of day modifiers
        if time_of_day == "night":
            impact['visibility_modifier'] *= 0.5
            impact['perception_modifier'] -= 2
            impact['stealth_modifier'] += 2
        elif time_of_day == "dawn" or time_of_day == "dusk":
            impact['visibility_modifier'] *= 0.7
            impact['perception_modifier'] -= 1

        # Weather type specific sensory effects
        weather_sensory_effects = {
            WeatherType.DENSE_FOG: {'perception': -5, 'investigation': -3, 'stealth': +3},
            WeatherType.MODERATE_FOG: {'perception': -3, 'investigation': -2, 'stealth': +2},
            WeatherType.BLIZZARD: {'perception': -4, 'investigation': -2, 'stealth': +1},
            WeatherType.HEAVY_RAIN: {'perception': -2, 'investigation': -1, 'stealth': +1},
            WeatherType.HEAVY_SNOW: {'perception': -3, 'investigation': -2, 'stealth': +2},
            WeatherType.DUST_STORM: {'perception': -4, 'investigation': -2, 'stealth': +1},
            WeatherType.SANDSTORM: {'perception': -5, 'investigation': -3, 'stealth': +2},
        }

        if weather_state.weather_type in weather_sensory_effects:
            effects = weather_sensory_effects[weather_state.weather_type]
            impact['perception_modifier'] += effects.get('perception', 0)
            impact['investigation_modifier'] += effects.get('investigation', 0)
            impact['stealth_modifier'] += effects.get('stealth', 0)

        # Wind effects on hearing
        if weather_state.wind_speed > 30:
            impact['perception_modifier'] -= 2  # Wind noise
        elif weather_state.wind_speed > 50:
            impact['perception_modifier'] -= 4

        return impact

    def _calculate_hazard_impact(self, weather_state: WeatherState) -> Dict[str, Any]:
        """Calculate environmental hazards from weather."""

        impact = {
            'damage_per_time': {},
            'saving_throws': [],
            'equipment_risks': {}
        }

        # Temperature hazards
        feels_like = weather_state.get_feels_like_temperature()
        if feels_like < -20:
            impact['damage_per_time']['cold'] = max(1, int((-20 - feels_like) / 10))
            impact['saving_throws'].append('constitution')
            impact['special_conditions'] = ['extreme_cold']
        elif feels_like < -10:
            impact['damage_per_time']['cold'] = 1
            impact['saving_throws'].append('constitution')
        elif feels_like > 40:
            impact['damage_per_time']['heat'] = max(1, int((feels_like - 40) / 5))
            impact['saving_throws'].append('constitution')
            impact['special_conditions'] = ['extreme_heat']
        elif feels_like > 35:
            impact['damage_per_time']['heat'] = 1
            impact['saving_throws'].append('constitution')

        # Wind hazards
        if weather_state.wind_speed > 60:
            impact['saving_throws'].append('strength')  # Against being blown away
            impact['special_conditions'] = ['gale_force_winds']
            impact['equipment_risks']['light_objects'] = 0.5  # 50% chance of loss
        elif weather_state.wind_speed > 40:
            impact['saving_throws'].append('dexterity')  # To maintain balance
            impact['equipment_risks']['loose_items'] = 0.2

        # Precipitation hazards
        if weather_state.precipitation_intensity > 20:  # Heavy precipitation
            impact['special_conditions'] = ['heavy_precipitation']
            impact['equipment_risks']['electronic'] = 0.3
            impact['equipment_risks']['paper'] = 0.8
            if weather_state.precipitation_type.value == 'freezing_rain':
                impact['special_conditions'].append('icing_conditions')
                impact['equipment_risks']['metal'] = 0.2

        # Lightning hazards
        if weather_state.weather_type == WeatherType.THUNDERSTORM:
            if weather_state.severity in [WeatherSeverity.SEVERE, WeatherSeverity.EXTREME]:
                impact['saving_throws'].append('dexterity')  # Lightning strike
                impact['special_conditions'] = ['lightning_risk']

        # Magical hazards
        if weather_state.magical_intensity > 0.7:
            if weather_state.magical_source:
                if 'shadow' in weather_state.magical_source.value:
                    impact['damage_per_time']['necrotic'] = int(weather_state.magical_intensity * 3)
                    impact['special_conditions'] = ['shadow_energy']
                elif 'fire' in weather_state.magical_source.value:
                    impact['damage_per_time']['fire'] = int(weather_state.magical_intensity * 2)
                    impact['special_conditions'] = ['magical_fire']
                elif 'divine' in weather_state.magical_source.value:
                    impact['special_conditions'] = ['divine_presence']

        return impact

    def _calculate_magical_impact(self, weather_state: WeatherState) -> Dict[str, Any]:
        """Calculate magical weather effects."""

        impact = {
            'auras': [],
            'conditions': []
        }

        if weather_state.magical_intensity > 0.3:
            # Magical aura based on source
            if weather_state.magical_source:
                aura_type = f"{weather_state.magical_source.value}_aura"
                impact['auras'].append({
                    'type': aura_type,
                    'intensity': weather_state.magical_intensity,
                    'radius': 100 * weather_state.magical_intensity  # meters
                })

            # Wild magic effects
            if weather_state.magical_intensity > 0.6:
                impact['conditions'].append('wild_magic_zone')
                impact['special_conditions'] = ['unpredictable_magic']

            # Planar influence
            if weather_state.atmospheric_conditions.magical_atmosphere.rift_activity > 0.5:
                impact['conditions'].append('planar_instability')
                impact['special_conditions'] = ['reality_ripples']

        return impact

    def _apply_severity_scaling(self, impact: EnvironmentalImpact, multiplier: float):
        """Apply severity scaling to all impact values."""

        # Movement impacts
        if multiplier > 0:
            speed_reduction = (1.0 - impact.movement_speed_modifier) * multiplier
            impact.movement_speed_modifier = max(0.1, 1.0 - speed_reduction)

            endurance_increase = (impact.endurance_cost_modifier - 1.0) * multiplier
            impact.endurance_cost_modifier = 1.0 + endurance_increase

        # Combat modifiers
        impact.ranged_attack_modifier = int(impact.ranged_attack_modifier * multiplier)
        impact.melee_attack_modifier = int(impact.melee_attack_modifier * multiplier)
        impact.defense_modifier = int(impact.defense_modifier * multiplier)
        impact.initiative_modifier = int(impact.initiative_modifier * multiplier)
        impact.concentration_dc_modifier = int(impact.concentration_dc_modifier * multiplier)

        # Spell modifiers
        impact.spell_save_dc_modifier = int(impact.spell_save_dc_modifier * multiplier)
        impact.spell_attack_modifier = int(impact.spell_attack_modifier * multiplier)

        # Sensory modifiers
        impact.perception_modifier = int(impact.perception_modifier * multiplier)
        impact.stealth_modifier = int(impact.stealth_modifier * multiplier)
        impact.investigation_modifier = int(impact.investigation_modifier * multiplier)

        # Scale damage
        for damage_type in impact.damage_per_time:
            impact.damage_per_time[damage_type] = int(
                impact.damage_per_time[damage_type] * multiplier
            )

    def get_description(self, impact: EnvironmentalImpact) -> str:
        """Generate human-readable description of environmental impact."""

        descriptions = []

        # Movement effects
        if impact.movement_speed_modifier < 0.5:
            descriptions.append("Movement severely hampered")
        elif impact.movement_speed_modifier < 0.8:
            descriptions.append("Movement significantly reduced")
        elif impact.movement_speed_modifier < 1.0:
            descriptions.append("Movement slightly reduced")

        if impact.endurance_cost_modifier > 1.5:
            descriptions.append("Rapidly exhausting conditions")
        elif impact.endurance_cost_modifier > 1.2:
            descriptions.append("Increased fatigue")

        # Combat effects
        if impact.ranged_attack_modifier < -3:
            descriptions.append("Ranged combat extremely difficult")
        elif impact.ranged_attack_modifier < -1:
            descriptions.append("Ranged attacks impaired")

        if impact.concentration_dc_modifier > 5:
            descriptions.append("Maintaining concentration very difficult")
        elif impact.concentration_dc_modifier > 2:
            descriptions.append("Concentration checks required")

        # Sensory effects
        if impact.visibility_range_modifier < 0.2:
            descriptions.append("Nearly zero visibility")
        elif impact.visibility_range_modifier < 0.5:
            descriptions.append("Severely limited visibility")
        elif impact.visibility_range_modifier < 0.8:
            descriptions.append("Reduced visibility")

        # Hazards
        if impact.damage_per_time:
            damage_types = list(impact.damage_per_time.keys())
            descriptions.append(f"Environmental damage: {', '.join(damage_types)}")

        if impact.saving_throws_required:
            descriptions.append(f"Saving throws required: {', '.join(impact.saving_throws_required)}")

        # Special conditions
        if impact.special_conditions:
            descriptions.append(f"Special conditions: {', '.join(impact.special_conditions)}")

        return "; ".join(descriptions) if descriptions else "Minimal environmental impact"

    def calculate_encounter_difficulty_modifier(self, impact: EnvironmentalImpact,
                                              creature_type: str = "any") -> int:
        """Calculate difficulty modifier for encounters based on environmental impact."""

        modifier = 0

        # Movement and visibility affect creature difficulty
        if impact.movement_speed_modifier < 0.5:
            modifier += 2  # Player movement severely hampered
        elif impact.movement_speed_modifier < 0.8:
            modifier += 1

        if impact.visibility_range_modifier < 0.3:
            modifier += 2  # Severely limited visibility
        elif impact.visibility_range_modifier < 0.7:
            modifier += 1

        # Environmental hazards affect difficulty
        if impact.damage_per_time:
            modifier += len(impact.damage_per_time)

        if impact.saving_throws_required:
            modifier += len(impact.saving_throws_required)

        # Combat penalties affect difficulty
        if impact.ranged_attack_modifier < -2:
            modifier += 1
        if impact.concentration_dc_modifier > 3:
            modifier += 1

        # Creature-specific adjustments
        if creature_type == "flying" and impact.wind_speed > 30:
            modifier += 2  # Flying creatures affected by wind
        elif creature_type == "aquatic" and impact.movement_speed_modifier < 0.5:
            modifier -= 1  # Aquatic creatures less affected by terrain

        return modifier

    def get_travel_time_modifier(self, impact: EnvironmentalImpact,
                                travel_distance: float) -> float:
        """Calculate travel time modifier based on environmental impact."""

        base_time = travel_distance  # Base time in hours

        # Movement speed affects travel time
        speed_factor = 1.0 / impact.movement_speed_modifier

        # Endurance costs may require rest
        if impact.endurance_cost_modifier > 1.5:
            speed_factor *= 1.5  # Additional rest time
        elif impact.endurance_cost_modifier > 1.2:
            speed_factor *= 1.2

        # Navigation difficulties increase travel time
        if impact.navigation_difficulty_modifier > 1.5:
            speed_factor *= 1.3  # Getting lost or taking longer routes

        # Weather hazards may require shelter
        if impact.damage_per_time or impact.saving_throws_required:
            speed_factor *= 1.2  # Seeking shelter periodically

        return speed_factor