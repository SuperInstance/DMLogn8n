"""
Weather Events System

Manages extreme weather events, magical phenomena, and dynamic weather
occurrences that impact gameplay and atmosphere.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from .weather_types import (
    WeatherType, WeatherSeverity, ClimateZone, MagicalWeatherSource,
    get_severity_from_intensity
)
from .weather_state import WeatherState

class EventType(Enum):
    """Types of weather events."""

    EXTREME_WEATHER = "extreme_weather"
    MAGICAL_PHENOMENON = "magical_phenomenon"
    CLIMATE_EVENT = "climate_event"
    SEASONAL_TRANSITION = "seasonal_transition"
    DIVINE_INTERVENTION = "divine_intervention"
    PLANETARY_ALIGNMENT = "planetary_alignment"
    MAGICAL_CATASTROPHE = "magical_catastrophe"

class EventCategory(Enum):
    """Categories for event classification."""

    DANGEROUS = "dangerous"      # Poses immediate threat
    BENEFICIAL = "beneficial"    # Provides advantage
    NEUTRAL = "neutral"          # No inherent bias
    MYSTERIOUS = "mysterious"    # Unknown effects
    TRANSFORMATIVE = "transformative"  # Changes environment

@dataclass
class WeatherEvent:
    """Base class for weather events."""

    event_id: str
    name: str
    description: str
    event_type: EventType
    category: EventCategory
    start_time: datetime
    duration: timedelta
    severity: WeatherSeverity
    probability: float  # 0-1

    # Event effects
    weather_type_override: Optional[WeatherType] = None
    temperature_change: float = 0.0
    humidity_change: float = 0.0
    pressure_change: float = 0.0
    wind_speed_change: float = 0.0
    visibility_change: float = 0.0
    precipitation_change: float = 0.0

    # Event-specific data
    affected_area_radius: float = 10.0  # kilometers
    movement_speed: float = 0.0  # km/h
    movement_direction: float = 0.0  # degrees

    # Event state
    is_active: bool = True
    intensity: float = 1.0  # 0-1
    phase: str = "building"  # building, peak, weakening, ended

    # Effects on gameplay
    gameplay_effects: Dict[str, Any] = field(default_factory=dict)
    creature_effects: Dict[str, Any] = field(default_factory=dict)
    spell_effects: Dict[str, Any] = field(default_factory=dict)

    # Event-specific methods
    def get_effects(self) -> Dict[str, Any]:
        """Get all effects of this event."""

        return {
            'weather_type': self.weather_type_override,
            'severity': self.severity,
            'temperature_change': self.temperature_change,
            'humidity_change': self.humidity_change,
            'pressure_change': self.pressure_change,
            'wind_speed_change': self.wind_speed_change,
            'visibility_change': self.visibility_change,
            'precipitation_change': self.precipitation_change,
            'gameplay_effects': self.gameplay_effects,
            'creature_effects': self.creature_effects,
            'spell_effects': self.spell_effects
        }

    def update_phase(self, elapsed_time: timedelta):
        """Update event phase based on elapsed time."""

        progress = elapsed_time.total_seconds() / self.duration.total_seconds()

        if progress < 0.3:
            self.phase = "building"
            self.intensity = progress / 0.3
        elif progress < 0.7:
            self.phase = "peak"
            self.intensity = 1.0
        elif progress < 1.0:
            self.phase = "weakening"
            self.intensity = (1.0 - progress) / 0.3
        else:
            self.phase = "ended"
            self.is_active = False
            self.intensity = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""

        return {
            'event_id': self.event_id,
            'name': self.name,
            'description': self.description,
            'event_type': self.event_type.value,
            'category': self.category.value,
            'start_time': self.start_time.isoformat(),
            'duration': self.duration.total_seconds(),
            'severity': self.severity.value,
            'probability': self.probability,
            'weather_type_override': self.weather_type_override.value if self.weather_type_override else None,
            'temperature_change': self.temperature_change,
            'humidity_change': self.humidity_change,
            'pressure_change': self.pressure_change,
            'wind_speed_change': self.wind_speed_change,
            'visibility_change': self.visibility_change,
            'precipitation_change': self.precipitation_change,
            'affected_area_radius': self.affected_area_radius,
            'movement_speed': self.movement_speed,
            'movement_direction': self.movement_direction,
            'is_active': self.is_active,
            'intensity': self.intensity,
            'phase': self.phase,
            'gameplay_effects': self.gameplay_effects,
            'creature_effects': self.creature_effects,
            'spell_effects': self.spell_effects
        }

@dataclass
class ExtremeWeatherEvent(WeatherEvent):
    """Extreme weather events with dangerous conditions."""

    storm_type: str = "unknown"  # hurricane, blizzard, tornado, etc.
    wind_gusts: float = 0.0  # Maximum wind gust speed
    precipitation_rate: float = 0.0  # mm/hour
    hail_size: float = 0.0  # cm
    lightning_frequency: float = 0.0  # strikes per minute

    # Hazard ratings
    hazard_level: int = 1  # 1-5
    evacuation_required: bool = False
    structural_damage_risk: float = 0.0  # 0-1

    def __post_init__(self):
        """Initialize extreme weather specific properties."""
        self.event_type = EventType.EXTREME_WEATHER
        self.category = EventCategory.DANGEROUS

@dataclass
class MagicalWeatherEvent(WeatherEvent):
    """Magical weather phenomena with supernatural effects."""

    magical_source: MagicalWeatherSource = MagicalWeatherSource.ARCANE_ENERGY
    magical_school: str = "general"  # evocation, abjuration, etc.
    planar_origin: Optional[str] = None  # plane of origin
    resonance_frequency: float = 0.0  # magical frequency

    # Magical properties
    spellcasting_modifier: float = 0.0  # spell DC/attack roll modifier
    antimagic_field_strength: float = 0.0  # 0-1
    summoning_portal_strength: float = 0.0  # 0-1
    transformation_effects: List[str] = field(default_factory=list)

    # Interaction with magic
    magic_item_effectiveness: float = 1.0  # multiplier
    magical_creature_activity: float = 1.0  # multiplier
    planar_barrier_weakness: float = 0.0  # 0-1

    def __post_init__(self):
        """Initialize magical weather specific properties."""
        self.event_type = EventType.MAGICAL_PHENOMENON
        self.category = EventCategory.MYSTERIOUS

class WeatherEventManager:
    """Manages weather events and their lifecycle."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_events: Dict[str, WeatherEvent] = {}
        self.event_history: List[WeatherEvent] = []
        self.event_templates = self._load_event_templates()
        self.event_callbacks: Dict[str, List[Callable]] = {}

    def _load_event_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined event templates."""

        return {
            # Extreme weather events
            'hurricane': {
                'name': 'Hurricane',
                'description': 'A massive tropical cyclone with destructive winds and torrential rain',
                'storm_type': 'hurricane',
                'weather_type_override': WeatherType.HURRICANE,
                'severity': WeatherSeverity.EXTREME,
                'wind_speed_change': 80.0,
                'visibility_change': -8.0,
                'precipitation_change': 50.0,
                'hazard_level': 5,
                'evacuation_required': True,
                'duration': timedelta(hours=24),
                'affected_area_radius': 100.0,
                'movement_speed': 20.0,
                'gameplay_effects': {
                    'movement_speed_modifier': 0.3,
                    'visibility_range_modifier': 0.2,
                    'ranged_attack_penalty': -4,
                    'concentration_checks_required': True
                }
            },
            'blizzard': {
                'name': 'Blizzard',
                'description': 'Severe snowstorm with strong winds and zero visibility',
                'storm_type': 'blizzard',
                'weather_type_override': WeatherType.BLIZZARD,
                'severity': WeatherSeverity.EXTREME,
                'temperature_change': -15.0,
                'wind_speed_change': 50.0,
                'visibility_change': -9.5,
                'precipitation_change': 30.0,
                'hazard_level': 4,
                'duration': timedelta(hours=12),
                'affected_area_radius': 50.0,
                'gameplay_effects': {
                    'movement_speed_modifier': 0.2,
                    'visibility_range_modifier': 0.05,
                    'cold_damage_per_hour': 10,
                    'exhaustion_checks_required': True,
                    'navigation_impossible': True
                }
            },
            'tornado': {
                'name': 'Tornado',
                'description': 'Violent rotating column of air with extreme destructive power',
                'storm_type': 'tornado',
                'weather_type_override': WeatherType.SEVERE_THUNDERSTORM,
                'severity': WeatherSeverity.CATASTROPHIC,
                'wind_speed_change': 150.0,
                'wind_gusts': 200.0,
                'visibility_change': -9.0,
                'hazard_level': 5,
                'duration': timedelta(minutes=30),
                'affected_area_radius': 5.0,
                'movement_speed': 60.0,
                'gameplay_effects': {
                    'structural_damage_likely': True,
                    'debris_projectiles': True,
                    'strength_save_required': 20,
                    'movement_impossible': True
                }
            },
            'flash_flood': {
                'name': 'Flash Flood',
                'description': 'Rapid flooding with powerful water currents',
                'storm_type': 'flash_flood',
                'weather_type_override': WeatherType.HEAVY_RAIN,
                'severity': WeatherSeverity.SEVERE,
                'precipitation_change': 100.0,
                'visibility_change': -3.0,
                'duration': timedelta(hours=4),
                'affected_area_radius': 20.0,
                'gameplay_effects': {
                    'water_depth_rising': True,
                    'swimming_checks_required': True,
                    'equipment_damage_risk': 0.5,
                    'movement_speed_modifier': 0.4
                }
            },

            # Magical weather events
            'arcane_storm': {
                'name': 'Arcane Storm',
                'description': 'A storm crackling with raw magical energy',
                'magical_source': MagicalWeatherSource.ARCANE_ENERGY,
                'weather_type_override': WeatherType.MAGICAL_STORM,
                'severity': WeatherSeverity.SEVERE,
                'magical_school': 'evocation',
                'spellcasting_modifier': 2,
                'lightning_frequency': 10.0,
                'duration': timedelta(hours=6),
                'affected_area_radius': 30.0,
                'gameplay_effects': {
                    'wild_magic_surge_chance': 0.25,
                    'spell_damage_boost': 1.5,
                    'concentration_dc_increase': 5,
                    'magical_aura_visible': True
                },
                'spell_effects': {
                    'elemental_spells_enhanced': ['lightning', 'thunder'],
                    'concentration_checks_disadvantage': True,
                    'metamagic_free': True
                }
            },
            'fae_mist': {
                'name': "Fae Mist",
                'description': 'Ethereal mist that warps perception and reality',
                'magical_source': MagicalWeatherSource.FAE_MAGIC,
                'weather_type_override': WeatherType.FAE_MIST,
                'severity': WeatherSeverity.MODERATE,
                'planar_origin': 'feywild',
                'visibility_change': -5.0,
                'duration': timedelta(hours=8),
                'affected_area_radius': 40.0,
                'gameplay_effects': {
                    'illusions_more_persistent': True,
                    'charisma_checks_advantage': True,
                    'wisdom_checks_disadvantage': True,
                    'time_distortion': True
                },
                'creature_effects': {
                    'fey_creatures_emboldened': True,
                    'mortals_confused': True,
                    'plant_life_enhanced': True
                }
            },
            'undead_fog': {
                'name': 'Undead Fog',
                'description': 'Chilling fog that animates the dead and drains life',
                'magical_source': MagicalWeatherSource.SHADOW_MAGIC,
                'weather_type_override': WeatherType.UNDEAD_FOG,
                'severity': WeatherSeverity.SEVERE,
                'magical_school': 'necromancy',
                'planar_origin': 'shadow_fell',
                'temperature_change': -10.0,
                'visibility_change': -7.0,
                'duration': timedelta(hours=12),
                'affected_area_radius': 60.0,
                'gameplay_effects': {
                    'negative_energy_damage': True,
                    'healing_spells_halved': True,
                    'undead_spawn_chance': 0.3,
                    'constitution_saving_throws_disadvantage': True
                },
                'creature_effects': {
                    'undead_strength_doubled': True,
                    'living_creatures_weakened': True,
                    'necromantic_spells_enhanced': True
                }
            },
            'celestial_shower': {
                'name': 'Celestial Shower',
                'description': 'Falling stars and cosmic energy rain from the heavens',
                'magical_source': MagicalWeatherSource.DIVINE_POWER,
                'weather_type_override': WeatherType.CELESTIAL_SHOWER,
                'severity': WeatherSeverity.MODERATE,
                'planar_origin': 'celestial_plane',
                'duration': timedelta(hours=4),
                'affected_area_radius': 100.0,
                'gameplay_effects': {
                    'divine_spells_enhanced': True,
                    'healing_spells_boosted': 1.5,
                    'celestial_damage_available': True,
                    'temporary_blessings': True
                },
                'spell_effects': {
                    'radiant_spells_enhanced': True,
                    'divine_intervention_more_likely': True,
                    'summoning_celestial_easier': True
                }
            },
            'elemental_rift': {
                'name': 'Elemental Rift',
                'description': 'A tear in reality spewing raw elemental energy',
                'magical_source': MagicalWeatherSource.ELEMENTAL_FORCE,
                'weather_type_override': WeatherType.ELEMENTAL_RIFT,
                'severity': WeatherSeverity.EXTREME,
                'planar_origin': 'elemental_planes',
                'duration': timedelta(hours=18),
                'affected_area_radius': 25.0,
                'summoning_portal_strength': 0.8,
                'planar_barrier_weakness': 0.7,
                'gameplay_effects': {
                    'elemental_spells_wild': True,
                    'elemental_creatures_attracted': True,
                    'environment_transformation': True,
                    'magical_instability': True
                },
                'transformation_effects': [
                    'terrain_converted_to_element',
                    'atmosphere_charged',
                    'physics_laws_altered'
                ]
            }
        }

    def check_extreme_event(self, current_state: WeatherState, climate_zone: ClimateZone, time_step_minutes: float) -> Optional[ExtremeWeatherEvent]:
        """Check for extreme weather event generation."""

        if not self.config.get('enabled', True):
            return None

        # Base probability from configuration
        base_probability = self.config.get('extreme_weather_probability', 0.1)

        # Adjust probability based on current conditions
        probability_modifier = self._calculate_extreme_event_probability(current_state, climate_zone)

        adjusted_probability = base_probability * probability_modifier * (time_step_minutes / 60.0)

        if random.random() > adjusted_probability:
            return None

        # Select appropriate extreme event
        event_template = self._select_extreme_event(current_state, climate_zone)
        if not event_template:
            return None

        # Create event
        event = self._create_extreme_event(event_template, current_state)

        # Store event
        self.active_events[event.event_id] = event

        return event

    def check_magical_phenomenon(self, current_state: WeatherState, location: str, time_step_minutes: float) -> Optional[MagicalWeatherEvent]:
        """Check for magical weather phenomenon generation."""

        if not self.config.get('enabled', True):
            return None

        # Base probability from configuration
        base_probability = self.config.get('magical_phenomena_probability', 0.05)

        # Adjust probability based on magical factors
        probability_modifier = self._calculate_magical_event_probability(current_state, location)

        adjusted_probability = base_probability * probability_modifier * (time_step_minutes / 60.0)

        if random.random() > adjusted_probability:
            return None

        # Select appropriate magical event
        event_template = self._select_magical_event(current_state, location)
        if not event_template:
            return None

        # Create event
        event = self._create_magical_event(event_template, current_state)

        # Store event
        self.active_events[event.event_id] = event

        return event

    def _calculate_extreme_event_probability(self, state: WeatherState, climate_zone: ClimateZone) -> float:
        """Calculate probability modifier for extreme events."""

        modifier = 1.0

        # Climate zone modifiers
        climate_modifiers = {
            ClimateZone.TROPICAL: 2.0,      # Hurricanes
            ClimateZone.TEMPERATE: 1.0,
            ClimateZone.ARCTIC: 1.5,        # Blizzards
            ClimateZone.MOUNTAINOUS: 1.3,   # Severe storms
            ClimateZone.COASTAL: 1.4,       # Hurricanes, nor'easters
            ClimateZone.DESERT: 0.8,        # Fewer storms but dust storms
        }

        modifier *= climate_modifiers.get(climate_zone, 1.0)

        # Weather condition modifiers
        if state.pressure < 1000:  # Low pressure system
            modifier *= 2.5
        elif state.pressure < 1010:
            modifier *= 1.5

        if state.wind_speed > 30:
            modifier *= 2.0
        elif state.wind_speed > 20:
            modifier *= 1.3

        if state.humidity > 0.8:
            modifier *= 1.4

        # Temperature extremes
        if state.temperature > 35 or state.temperature < -20:
            modifier *= 1.5

        # Seasonal modifiers
        if state.season.value in ['summer', 'autumn']:
            modifier *= 1.3

        return modifier

    def _calculate_magical_event_probability(self, state: WeatherState, location: str) -> float:
        """Calculate probability modifier for magical events."""

        modifier = 1.0

        # Location-based modifiers
        magical_locations = {
            'ancient_ruins': 3.0,
            'wizard_tower': 2.5,
            'sacred_grove': 2.0,
            'battlefield': 1.5,
            'planar_rift': 5.0,
            'dragon_lair': 2.0,
            'fae_circle': 3.0,
        }

        for loc, mod in magical_locations.items():
            if loc in location.lower():
                modifier *= mod
                break

        # Current magical conditions
        if state.magical_intensity > 0.5:
            modifier *= 3.0
        elif state.magical_intensity > 0.2:
            modifier *= 1.5

        # Planar influences
        if state.atmospheric_conditions.magical_atmosphere.rift_activity > 0.5:
            modifier *= 4.0

        if state.atmospheric_conditions.magical_atmosphere.arcane_energy > 0.7:
            modifier *= 2.5

        # Time-based modifiers
        hour = state.timestamp.hour
        if hour >= 22 or hour <= 4:  # Night time
            modifier *= 1.3

        # Planetary positions (simplified)
        if state.atmospheric_conditions.lunar_phase > 0.8:  # Full moon
            modifier *= 1.5

        return modifier

    def _select_extreme_event(self, state: WeatherState, climate_zone: ClimateZone) -> Optional[Dict[str, Any]]:
        """Select appropriate extreme event based on conditions."""

        # Filter suitable events
        suitable_events = []

        for event_key, template in self.event_templates.items():
            if 'storm_type' not in template:
                continue

            # Climate zone compatibility
            if climate_zone == ClimateZone.TROPICAL and template['storm_type'] == 'blizzard':
                continue
            elif climate_zone == ClimateZone.ARCTIC and template['storm_type'] == 'hurricane':
                continue

            # Temperature compatibility
            if template['storm_type'] == 'blizzard' and state.temperature > 5:
                continue
            elif template['storm_type'] == 'hurricane' and state.temperature < 20:
                continue

            suitable_events.append((event_key, template))

        if not suitable_events:
            return None

        # Weight selection based on conditions
        weights = []
        for event_key, template in suitable_events:
            weight = 1.0

            # Favor events that match current conditions
            if template['storm_type'] == 'flash_flood' and state.humidity > 0.8:
                weight *= 2.0
            elif template['storm_type'] == 'tornado' and state.pressure < 1005:
                weight *= 1.8
            elif template['storm_type'] == 'blizzard' and state.temperature < -10:
                weight *= 2.0

            weights.append(weight)

        # Select weighted random event
        total_weight = sum(weights)
        if total_weight == 0:
            return None

        normalized_weights = [w / total_weight for w in weights]
        selected_index = random.choices(range(len(suitable_events)), weights=normalized_weights)[0]

        return suitable_events[selected_index][1]

    def _select_magical_event(self, state: WeatherState, location: str) -> Optional[Dict[str, Any]]:
        """Select appropriate magical event based on conditions."""

        # Filter suitable events
        suitable_events = []

        for event_key, template in self.event_templates.items():
            if 'magical_source' not in template:
                continue

            suitable_events.append((event_key, template))

        if not suitable_events:
            return None

        # Weight selection based on conditions
        weights = []
        for event_key, template in suitable_events:
            weight = 1.0

            # Favor events that match current magical conditions
            if state.magical_source == template.get('magical_source'):
                weight *= 2.0

            if 'ruins' in location.lower() and event_key == 'arcane_storm':
                weight *= 1.5
            elif 'grove' in location.lower() and event_key == 'fae_mist':
                weight *= 2.0
            elif 'graveyard' in location.lower() and event_key == 'undead_fog':
                weight *= 2.0

            weights.append(weight)

        # Select weighted random event
        total_weight = sum(weights)
        if total_weight == 0:
            return None

        normalized_weights = [w / total_weight for w in weights]
        selected_index = random.choices(range(len(suitable_events)), weights=normalized_weights)[0]

        return suitable_events[selected_index][1]

    def _create_extreme_event(self, template: Dict[str, Any], current_state: WeatherState) -> ExtremeWeatherEvent:
        """Create extreme weather event from template."""

        event_id = f"extreme_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"

        event = ExtremeWeatherEvent(
            event_id=event_id,
            name=template['name'],
            description=template['description'],
            event_type=EventType.EXTREME_WEATHER,
            category=EventCategory.DANGEROUS,
            start_time=current_state.timestamp,
            duration=template['duration'],
            severity=template['severity'],
            probability=1.0,  # This event is happening
            weather_type_override=template['weather_type_override'],
            temperature_change=template.get('temperature_change', 0.0),
            wind_speed_change=template.get('wind_speed_change', 0.0),
            visibility_change=template.get('visibility_change', 0.0),
            precipitation_change=template.get('precipitation_change', 0.0),
            affected_area_radius=template.get('affected_area_radius', 10.0),
            movement_speed=template.get('movement_speed', 0.0),
            gameplay_effects=template.get('gameplay_effects', {}),
            creature_effects=template.get('creature_effects', {}),
            spell_effects=template.get('spell_effects', {})
        )

        # Add extreme weather specific properties
        event.storm_type = template.get('storm_type', 'unknown')
        event.hazard_level = template.get('hazard_level', 1)
        event.evacuation_required = template.get('evacuation_required', False)

        return event

    def _create_magical_event(self, template: Dict[str, Any], current_state: WeatherState) -> MagicalWeatherEvent:
        """Create magical weather event from template."""

        event_id = f"magical_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"

        event = MagicalWeatherEvent(
            event_id=event_id,
            name=template['name'],
            description=template['description'],
            event_type=EventType.MAGICAL_PHENOMENON,
            category=EventCategory.MYSTERIOUS,
            start_time=current_state.timestamp,
            duration=template['duration'],
            severity=template['severity'],
            probability=1.0,  # This event is happening
            weather_type_override=template['weather_type_override'],
            temperature_change=template.get('temperature_change', 0.0),
            visibility_change=template.get('visibility_change', 0.0),
            affected_area_radius=template.get('affected_area_radius', 10.0),
            gameplay_effects=template.get('gameplay_effects', {}),
            creature_effects=template.get('creature_effects', {}),
            spell_effects=template.get('spell_effects', {})
        )

        # Add magical weather specific properties
        event.magical_source = template.get('magical_source', MagicalWeatherSource.ARCANE_ENERGY)
        event.magical_school = template.get('magical_school', 'general')
        event.planar_origin = template.get('planar_origin')
        event.spellcasting_modifier = template.get('spellcasting_modifier', 0.0)
        event.summoning_portal_strength = template.get('summoning_portal_strength', 0.0)
        event.planar_barrier_weakness = template.get('planar_barrier_weakness', 0.0)
        event.transformation_effects = template.get('transformation_effects', [])

        return event

    def update_events(self, current_time: datetime):
        """Update all active events."""

        events_to_remove = []

        for event_id, event in self.active_events.items():
            # Update event phase
            elapsed_time = current_time - event.start_time
            event.update_phase(elapsed_time)

            # Check if event has ended
            if not event.is_active:
                events_to_remove.append(event_id)
                self.event_history.append(event)

        # Remove ended events
        for event_id in events_to_remove:
            del self.active_events[event_id]

        # Limit history size
        if len(self.event_history) > 100:
            self.event_history = self.event_history[-100:]

    def get_active_events(self) -> List[WeatherEvent]:
        """Get list of all active events."""

        return list(self.active_events.values())

    def get_events_at_location(self, location: str, radius: float = 10.0) -> List[WeatherEvent]:
        """Get events affecting a specific location."""

        # This would need location data to calculate distances
        # For now, return all active events
        return list(self.active_events.values())

    def cancel_event(self, event_id: str) -> bool:
        """Cancel an active event."""

        if event_id in self.active_events:
            event = self.active_events[event_id]
            event.is_active = False
            event.phase = "ended"
            event.intensity = 0.0
            self.event_history.append(event)
            del self.active_events[event_id]
            return True
        return False

    def trigger_custom_event(self, event_template: Dict[str, Any], current_state: WeatherState) -> WeatherEvent:
        """Trigger a custom weather event."""

        if 'magical_source' in event_template:
            event = self._create_magical_event(event_template, current_state)
        else:
            event = self._create_extreme_event(event_template, current_state)

        self.active_events[event.event_id] = event
        return event

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for specific event types."""

        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about weather events."""

        if not self.event_history:
            return {}

        # Count event types
        event_type_counts = {}
        for event in self.event_history:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        # Average duration and severity
        durations = [event.duration.total_seconds() / 3600 for event in self.event_history]  # hours
        severities = [event.severity.value for event in self.event_history]

        return {
            'total_events': len(self.event_history),
            'active_events': len(self.active_events),
            'event_type_distribution': event_type_counts,
            'average_duration_hours': sum(durations) / len(durations) if durations else 0,
            'average_severity': sum(severities) / len(severities) if severities else 0,
            'most_common_event': max(event_type_counts.items(), key=lambda x: x[1])[0] if event_type_counts else None
        }