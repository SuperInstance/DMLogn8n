"""
Combat Modifiers System

Calculates weather effects on combat mechanics, attacks, defenses,
and tactical considerations.
"""

import math
from typing import Dict, Any, List

from ..core.weather_state import WeatherState
from ..core.weather_types import WeatherType

class CombatModifiers:
    """Handles weather effects on combat mechanics."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Base combat modifiers by weather type
        self.base_combat_modifiers = {
            WeatherType.CLEAR: {
                "ranged": 0, "melee": 0, "defense": 0,
                "initiative": 0, "concentration": 0
            },
            WeatherType.PARTLY_CLOUDY: {
                "ranged": 0, "melee": 0, "defense": 0,
                "initiative": 0, "concentration": 0
            },
            WeatherType.OVERCAST: {
                "ranged": -1, "melee": 0, "defense": 0,
                "initiative": 0, "concentration": 0
            },
            WeatherType.LIGHT_RAIN: {
                "ranged": -1, "melee": 0, "defense": 0,
                "initiative": -1, "concentration": 1
            },
            WeatherType.MODERATE_RAIN: {
                "ranged": -2, "melee": -1, "defense": 0,
                "initiative": -2, "concentration": 2
            },
            WeatherType.HEAVY_RAIN: {
                "ranged": -4, "melee": -2, "defense": -1,
                "initiative": -3, "concentration": 3
            },
            WeatherType.LIGHT_SNOW: {
                "ranged": -1, "melee": -1, "defense": 0,
                "initiative": -1, "concentration": 1
            },
            WeatherType.MODERATE_SNOW: {
                "ranged": -2, "melee": -2, "defense": -1,
                "initiative": -2, "concentration": 2
            },
            WeatherType.HEAVY_SNOW: {
                "ranged": -3, "melee": -3, "defense": -2,
                "initiative": -3, "concentration": 3
            },
            WeatherType.BLIZZARD: {
                "ranged": -6, "melee": -4, "defense": -3,
                "initiative": -5, "concentration": 5
            },
            WeatherType.LIGHT_FOG: {
                "ranged": -1, "melee": 0, "defense": 0,
                "initiative": -1, "concentration": 1
            },
            WeatherType.MODERATE_FOG: {
                "ranged": -3, "melee": -1, "defense": 0,
                "initiative": -2, "concentration": 2
            },
            WeatherType.DENSE_FOG: {
                "ranged": -5, "melee": -2, "defense": -1,
                "initiative": -3, "concentration": 3
            },
            WeatherType.LIGHT_WIND: {
                "ranged": -1, "melee": 0, "defense": 0,
                "initiative": 0, "concentration": 1
            },
            WeatherType.MODERATE_WIND: {
                "ranged": -2, "melee": 0, "defense": 0,
                "initiative": 0, "concentration": 2
            },
            WeatherType.STRONG_WIND: {
                "ranged": -4, "melee": -1, "defense": -1,
                "initiative": -1, "concentration": 3
            },
            WeatherType.GALE_FORCE: {
                "ranged": -6, "melee": -3, "defense": -2,
                "initiative": -2, "concentration": 4
            },
            WeatherType.DUST_STORM: {
                "ranged": -4, "melee": -3, "defense": -2,
                "initiative": -3, "concentration": 4
            },
            WeatherType.SANDSTORM: {
                "ranged": -5, "melee": -4, "defense": -3,
                "initiative": -4, "concentration": 5
            },
        }

    def calculate_combat_impact(self, weather_state: WeatherState,
                               terrain_type: str = "plains") -> Dict[str, int]:
        """Calculate comprehensive combat impact."""

        # Get base modifiers
        base_mods = self.base_combat_modifiers.get(
            weather_state.weather_type,
            {"ranged": 0, "melee": 0, "defense": 0,
             "initiative": 0, "concentration": 0}
        )

        # Apply severity scaling
        severity_multiplier = weather_state.severity.value / 2.0  # Scale from 0-2.5

        combat_impact = {
            "ranged_modifier": int(base_mods["ranged"] * severity_multiplier),
            "melee_modifier": int(base_mods["melee"] * severity_multiplier),
            "defense_modifier": int(base_mods["defense"] * severity_multiplier),
            "initiative_modifier": int(base_mods["initiative"] * severity_multiplier),
            "concentration_dc": int(base_mods["concentration"] * severity_multiplier)
        }

        # Apply visibility effects
        visibility_mods = self._calculate_visibility_combat_effects(weather_state)
        combat_impact["ranged_modifier"] += visibility_mods["ranged"]
        combat_impact["melee_modifier"] += visibility_mods["melee"]
        combat_impact["defense_modifier"] += visibility_mods["defense"]

        # Apply wind effects
        wind_mods = self._calculate_wind_combat_effects(weather_state)
        combat_impact["ranged_modifier"] += wind_mods["ranged"]
        combat_impact["melee_modifier"] += wind_mods["melee"]
        combat_impact["initiative_modifier"] += wind_mods["initiative"]
        combat_impact["concentration_dc"] += wind_mods["concentration"]

        # Apply temperature effects
        temp_mods = self._calculate_temperature_combat_effects(weather_state)
        combat_impact["melee_modifier"] += temp_mods["melee"]
        combat_impact["initiative_modifier"] += temp_mods["initiative"]
        combat_impact["concentration_dc"] += temp_mods["concentration"]

        # Apply precipitation effects
        if weather_state.precipitation_intensity > 0:
            precip_mods = self._calculate_precipitation_combat_effects(weather_state)
            combat_impact["ranged_modifier"] += precip_mods["ranged"]
            combat_impact["melee_modifier"] += precip_mods["melee"]
            combat_impact["defense_modifier"] += precip_mods["defense"]

        # Apply magical effects
        if weather_state.magical_intensity > 0:
            magic_mods = self._calculate_magical_combat_effects(weather_state)
            combat_impact["ranged_modifier"] += magic_mods["ranged"]
            combat_impact["melee_modifier"] += magic_mods["melee"]
            combat_impact["defense_modifier"] += magic_mods["defense"]
            combat_impact["concentration_dc"] += magic_mods["concentration"]

        # Apply terrain effects
        terrain_mods = self._calculate_terrain_combat_effects(terrain_type)
        combat_impact["melee_modifier"] += terrain_mods["melee"]
        combat_impact["defense_modifier"] += terrain_mods["defense"]

        return combat_impact

    def _calculate_visibility_combat_effects(self, weather_state: WeatherState) -> Dict[str, int]:
        """Calculate visibility effects on combat."""

        effects = {"ranged": 0, "melee": 0, "defense": 0}

        if weather_state.visibility < 1.0:
            # Very poor visibility
            effects["ranged"] = -5
            effects["melee"] = -3
            effects["defense"] = -2
        elif weather_state.visibility < 3.0:
            # Poor visibility
            effects["ranged"] = -3
            effects["melee"] = -2
            effects["defense"] = -1
        elif weather_state.visibility < 5.0:
            # Reduced visibility
            effects["ranged"] = -2
            effects["melee"] = -1
        elif weather_state.visibility < 8.0:
            # Slightly reduced visibility
            effects["ranged"] = -1

        return effects

    def _calculate_wind_combat_effects(self, weather_state: WeatherState) -> Dict[str, int]:
        """Calculate wind effects on combat."""

        effects = {"ranged": 0, "melee": 0, "initiative": 0, "concentration": 0}

        if weather_state.wind_speed > 40:
            # Strong winds significantly affect ranged combat
            effects["ranged"] = -3
            effects["melee"] = -1  # Balance issues
            effects["initiative"] = -1  # Fighting against wind
            effects["concentration"] = 2  # Wind noise and physical strain
        elif weather_state.wind_speed > 25:
            # Moderate winds
            effects["ranged"] = -2
            effects["concentration"] = 1
        elif weather_state.wind_speed > 15:
            # Light winds
            effects["ranged"] = -1

        return effects

    def _calculate_temperature_combat_effects(self, weather_state: WeatherState) -> Dict[str, int]:
        """Calculate temperature effects on combat."""

        effects = {"melee": 0, "initiative": 0, "concentration": 0}

        feels_like = weather_state.get_feels_like_temperature()

        if feels_like < -20:
            # Extreme cold
            effects["melee"] = -2  # Stiff joints, reduced dexterity
            effects["initiative"] = -2  # Slowed reactions
            effects["concentration"] = 3  # Shivering, physical discomfort
        elif feels_like < -10:
            # Severe cold
            effects["melee"] = -1
            effects["initiative"] = -1
            effects["concentration"] = 2
        elif feels_like > 40:
            # Extreme heat
            effects["melee"] = -1  # Fatigue
            effects["initiative"] = -1  # Slowed by heat
            effects["concentration"] = 3  # Heat exhaustion
        elif feels_like > 35:
            # Severe heat
            effects["melee"] = -1
            effects["concentration"] = 2

        return effects

    def _calculate_precipitation_combat_effects(self, weather_state: WeatherState) -> Dict[str, int]:
        """Calculate precipitation effects on combat."""

        effects = {"ranged": 0, "melee": 0, "defense": 0}

        if weather_state.precipitation_intensity > 30:
            # Heavy precipitation
            effects["ranged"] = -2
            effects["melee"] = -1  # Slippery footing
            effects["defense"] = -1  # Reduced visibility
        elif weather_state.precipitation_intensity > 15:
            # Moderate precipitation
            effects["ranged"] = -1
            effects["defense"] = -1

        # Freezing rain creates icy conditions
        if weather_state.precipitation_type.value == "freezing_rain":
            effects["melee"] -= 2  # Very slippery
            effects["defense"] -= 1  # Hard to maintain footing

        return effects

    def _calculate_magical_combat_effects(self, weather_state: WeatherState) -> Dict[str, int]:
        """Calculate magical weather effects on combat."""

        effects = {"ranged": 0, "melee": 0, "defense": 0, "concentration": 0}

        if weather_state.magical_intensity > 0.5:
            if weather_state.weather_type == WeatherType.MAGICAL_STORM:
                effects["ranged"] = -2  # Arcane interference
                effects["melee"] = -1
                effects["concentration"] = 3  # Chaotic energy
            elif weather_state.weather_type == WeatherType.UNDEAD_FOG:
                effects["melee"] = -2  # Life-draining effects
                effects["defense"] = -1
                effects["concentration"] = 2  # Chilling presence
            elif weather_state.weather_type == WeatherType.FAE_MIST:
                effects["ranged"] = -1  # Disorientation
                effects["concentration"] = 2  # Confusing effects
            elif weather_state.magical_source and "shadow" in weather_state.magical_source.value:
                effects["melee"] = -1  # Weakening effects
                effects["defense"] = -1
                effects["concentration"] = 2  # Oppressive atmosphere

        return effects

    def _calculate_terrain_combat_effects(self, terrain_type: str) -> Dict[str, int]:
        """Calculate terrain effects on combat."""

        effects = {"melee": 0, "defense": 0}

        terrain_effects = {
            "forest": {"melee": -1, "defense": 1},  # Cover but difficult movement
            "hills": {"melee": 1, "defense": 0},    # High ground advantage
            "mountains": {"melee": 1, "defense": 2}, # Significant high ground
            "swamp": {"melee": -2, "defense": -1},  # Difficult footing
            "snow": {"melee": -1, "defense": 0},    # Slippery conditions
            "ice": {"melee": -2, "defense": -1},    # Very slippery
            "urban": {"melee": 0, "defense": 1},    # Cover available
            "dungeon": {"melee": 0, "defense": 1},  # Confined spaces
        }

        return terrain_effects.get(terrain_type, {"melee": 0, "defense": 0})

    def calculate_advantage_disadvantage(self, weather_state: WeatherState,
                                        action_type: str) -> List[str]:
        """Calculate advantage/disadvantage conditions for different actions."""

        conditions = []

        # Visibility-based effects
        if weather_state.visibility < 3.0:
            if action_type in ["perception", "investigation", "ranged_attack"]:
                conditions.append("disadvantage")
        elif weather_state.visibility < 1.0:
            if action_type in ["melee_attack", "spell_attack"]:
                conditions.append("disadvantage")

        # Wind effects
        if weather_state.wind_speed > 30:
            if action_type == "ranged_attack":
                conditions.append("disadvantage")
        elif weather_state.wind_speed > 50:
            if action_type in ["ranged_attack", "spell_attack"]:
                conditions.append("disadvantage")

        # Precipitation effects
        if weather_state.precipitation_intensity > 20:
            if action_type == "ranged_attack":
                conditions.append("disadvantage")
        elif weather_state.precipitation_type.value == "freezing_rain":
            if action_type in ["athletics", "acrobatics"]:
                conditions.append("disadvantage")

        # Temperature effects
        feels_like = weather_state.get_feels_like_temperature()
        if feels_like < -15 or feels_like > 38:
            if action_type in ["concentration", "endurance"]:
                conditions.append("disadvantage")

        # Magical effects
        if weather_state.magical_intensity > 0.6:
            if weather_state.weather_type == WeatherType.UNDEAD_FOG:
                if action_type in ["constitution_save", "life_drain_resistance"]:
                    conditions.append("disadvantage")
            elif weather_state.weather_type == WeatherType.FAE_MIST:
                if action_type in ["wisdom_save", "charisma_check"]:
                    conditions.append("disadvantage")

        return conditions

    def calculate_critical_hit_effects(self, weather_state: WeatherState) -> Dict[str, Any]:
        """Calculate additional effects on critical hits due to weather."""

        effects = {
            "additional_damage": 0,
            "special_effects": [],
            "failure_chances": {}
        }

        # Wind effects on critical hits
        if weather_state.wind_speed > 40:
            effects["failure_chances"]["balance"] = 0.3  # 30% chance to fall
            effects["special_effects"].append("pushed_back")

        # Precipitation effects
        if weather_state.precipitation_type.value == "freezing_rain":
            effects["failure_chances"]["slip"] = 0.4
            effects["special_effects"].append("fall_prone")

        # Lightning effects
        if weather_state.weather_type == WeatherType.THUNDERSTORM:
            if weather_state.severity.value >= 3:
                effects["additional_damage"] = "2d6 lightning"
                effects["special_effects"].append("lightning_strike")

        # Magical effects
        if weather_state.magical_intensity > 0.7:
            if weather_state.weather_type == WeatherType.MAGICAL_STORM:
                effects["additional_damage"] = "1d8 force"
                effects["special_effects"].append("wild_magic_surge")

        return effects

    def calculate_tactical_situation_modifiers(self, weather_state: WeatherState,
                                              situation: str) -> Dict[str, int]:
        """Calculate modifiers for specific tactical situations."""

        modifiers = {}

        if situation == "charge":
            # Charging is difficult in bad weather
            if weather_state.wind_speed > 30:
                modifiers["speed"] = -2
            if weather_state.precipitation_intensity > 20:
                modifiers["speed"] = -1
            if weather_state.visibility < 5.0:
                modifiers["speed"] = -1

        elif situation == "flanking":
            # Flanking affected by visibility
            if weather_state.visibility < 3.0:
                modifiers["coordination"] = -2
            elif weather_state.visibility < 8.0:
                modifiers["coordination"] = -1

        elif situation == "retreat":
            # Retreat affected by movement conditions
            if weather_state.precipitation_intensity > 15:
                modifiers["speed"] = -2
            if weather_state.wind_speed > 25:
                modifiers["speed"] = -1
            if weather_state.temperature < -10:
                modifiers["endurance"] = -2

        elif situation == "cover":
            # Weather can provide or negate cover
            if weather_state.weather_type in [WeatherType.HEAVY_RAIN, WeatherType.BLIZZARD]:
                modifiers["concealment"] = 2  # Weather provides partial cover
            elif weather_state.visibility < 1.0:
                modifiers["concealment"] = 3  # Near total concealment

        elif situation == "stealth":
            # Weather affects stealth attempts
            if weather_state.visibility < 5.0:
                modifiers["stealth"] = 2
            if weather_state.wind_speed > 20:
                modifiers["stealth"] = -1  # Noise from wind
            if weather_state.precipitation_intensity > 10:
                modifiers["stealth"] = 1  # Noise masks movement

        return modifiers