#!/usr/bin/env python3
"""
DMLogn8n Haptic System - Advanced Haptic Feedback and Touch Simulation
Advanced haptic feedback system with realistic touch simulation and force feedback
"""

import numpy as np
import asyncio
import json
import time
import math
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from abc import ABC, abstractmethod

# Haptic hardware libraries
try:
    import serial
    import pyserial.tools.list_ports
except ImportError:
    serial = None
    pyserial_tools = None

try:
    import pygame
except ImportError:
    pygame = None

# Audio processing for haptics
try:
    import scipy.io.wavfile as wavfile
    from scipy import signal
    import soundfile as sf
except ImportError:
    wavfile = None
    signal = None
    sf = None

# Real-time processing
try:
    import threading
    import queue
    from collections import deque
except ImportError:
    threading = None
    queue = None
    deque = None

# Mathematical utilities
from scipy.interpolate import interp1d


class HapticDeviceType(Enum):
    """Types of haptic devices"""
    VIBRATION_MOTOR = "vibration_motor"
    LINEAR_ACTUATOR = "linear_actuator"
    FORCE_FEEDBACK = "force_feedback"
    TACTILE_ARRAY = "tactile_array"
    ULTRASONIC = "ultrasonic"
    GLOVE = "glove"
    SUIT = "suit"
    CUSTOM = "custom"


class HapticPattern(Enum):
    """Predefined haptic patterns"""
    TAP = "tap"
    PULSE = "pulse"
    BUZZ = "buzz"
    RUMBLE = "rumble"
    WAVE = "wave"
    EXPLOSION = "explosion"
    HEARTBEAT = "heartbeat"
    RAIN = "rain"
    THUNDER = "thunder"
    CUSTOM = "custom"


class TextureType(Enum):
    """Types of surface textures"""
    SMOOTH = "smooth"
    ROUGH = "rough"
    BUMPY = "bumpy"
    GRITTY = "gritty"
    WOOD = "wood"
    METAL = "metal"
    FABRIC = "fabric"
    STONE = "stone"
    WATER = "water"
    SAND = "sand"


@dataclass
class Vector3:
    """3D Vector for haptic positioning"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def magnitude(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass
class HapticDevice:
    """Haptic device representation"""
    device_id: str
    device_type: HapticDeviceType
    name: str
    position: Vector3
    is_connected: bool = True
    max_intensity: float = 1.0
    frequency_range: Tuple[float, float] = (20, 500)
    capabilities: List[str] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class HapticEffect:
    """Haptic effect definition"""
    effect_id: str
    pattern: HapticPattern
    intensity: float = 1.0
    duration: float = 1.0
    frequency: float = 100.0
    attack_time: float = 0.1
    decay_time: float = 0.1
    sustain_time: float = 0.8
    fade_in: bool = True
    fade_out: bool = True
    loop: bool = False
    custom_waveform: Optional[np.ndarray] = None


@dataclass
class HapticEvent:
    """Haptic event to be played"""
    event_id: str
    device_id: str
    effect: HapticEffect
    position: Optional[Vector3] = None
    timestamp: float = 0.0
    priority: int = 0
    data: Optional[Dict] = None


@dataclass
class TextureProperties:
    """Surface texture properties for haptic simulation"""
    texture_type: TextureType
    roughness: float = 0.5  # 0=smooth, 1=very rough
    friction: float = 0.5   # 0=no friction, 1=high friction
    stiffness: float = 0.5  # 0=soft, 1=hard
    damping: float = 0.3    # 0=no damping, 1=high damping
    frequency_components: List[float] = None

    def __post_init__(self):
        if self.frequency_components is None:
            # Generate default frequency components based on texture type
            self.frequency_components = self._generate_frequency_components()

    def _generate_frequency_components(self) -> List[float]:
        """Generate frequency components for texture type"""
        components = []

        if self.texture_type == TextureType.SMOOTH:
            components = [50, 100]
        elif self.texture_type == TextureType.ROUGH:
            components = [30, 80, 150, 250]
        elif self.texture_type == TextureType.BUMPY:
            components = [40, 120, 200]
        elif self.texture_type == TextureType.GRITTY:
            components = [60, 180, 300]
        elif self.texture_type == TextureType.WOOD:
            components = [80, 160, 240]
        elif self.texture_type == TextureType.METAL:
            components = [100, 200, 400]
        elif self.texture_type == TextureType.FABRIC:
            components = [40, 80, 120]
        elif self.texture_type == TextureType.STONE:
            components = [60, 150, 300]
        elif self.texture_type == TextureType.WATER:
            components = [20, 60, 120]
        elif self.texture_type == TextureType.SAND:
            components = [30, 90, 180]

        return components


class HapticWaveformGenerator:
    """Generate haptic waveforms for different patterns and textures"""

    def __init__(self, sample_rate: int = 1000):
        self.sample_rate = sample_rate

    def generate_waveform(self, effect: HapticEffect) -> np.ndarray:
        """Generate waveform for haptic effect"""
        duration_samples = int(effect.duration * self.sample_rate)
        t = np.linspace(0, effect.duration, duration_samples)

        if effect.custom_waveform is not None:
            waveform = effect.custom_waveform
        else:
            waveform = self._generate_pattern_waveform(effect.pattern, t)

        # Apply envelope (ADSR)
        waveform = self._apply_adsr_envelope(waveform, effect)

        # Apply frequency modulation if specified
        if effect.frequency != 100.0:
            waveform = self._apply_frequency_modulation(waveform, effect.frequency)

        # Scale by intensity
        waveform = waveform * effect.intensity

        return waveform

    def _generate_pattern_waveform(self, pattern: HapticPattern, t: np.ndarray) -> np.ndarray:
        """Generate waveform based on pattern type"""
        if pattern == HapticPattern.TAP:
            # Short, sharp impulse
            waveform = np.zeros_like(t)
            tap_samples = int(0.05 * self.sample_rate)  # 50ms tap
            waveform[:tap_samples] = np.exp(-np.linspace(0, 10, tap_samples))

        elif pattern == HapticPattern.PULSE:
            # Series of pulses
            pulse_freq = 5  # 5 Hz
            waveform = np.sin(2 * np.pi * pulse_freq * t)
            waveform *= np.exp(-t * 2)  # Exponential decay

        elif pattern == HapticPattern.BUZZ:
            # High frequency vibration
            buzz_freq = 200  # 200 Hz
            waveform = np.sin(2 * np.pi * buzz_freq * t)
            waveform *= np.random.normal(1, 0.1, len(t))  # Add noise

        elif pattern == HapticPattern.RUMBLE:
            # Low frequency vibration
            rumble_freq = 30  # 30 Hz
            waveform = np.sin(2 * np.pi * rumble_freq * t)
            # Add harmonics
            waveform += 0.5 * np.sin(2 * np.pi * rumble_freq * 2 * t)
            waveform += 0.3 * np.sin(2 * np.pi * rumble_freq * 3 * t)

        elif pattern == HapticPattern.WAVE:
            # Smooth wave pattern
            wave_freq = 2  # 2 Hz
            waveform = np.sin(2 * np.pi * wave_freq * t)
            # Add some harmonics for richness
            waveform += 0.3 * np.sin(2 * np.pi * wave_freq * 3 * t)

        elif pattern == HapticPattern.EXPLOSION:
            # Sharp attack with decay
            attack_samples = int(0.1 * self.sample_rate)
            waveform = np.zeros_like(t)
            # Sharp attack
            waveform[:attack_samples] = np.exp(-np.linspace(0, 20, attack_samples))
            # Add noise for explosion effect
            noise = np.random.normal(0, 0.2, len(t))
            waveform += noise * np.exp(-t * 3)

        elif pattern == HapticPattern.HEARTBEAT:
            # Heartbeat pattern
            heartbeat_freq = 1.2  # 72 BPM
            # Double pulse pattern (lub-dub)
            pulse1 = np.exp(-((t % (1/heartbeat_freq)) * 50)**2)
            pulse2 = np.exp(-(((t % (1/heartbeat_freq)) - 0.3) * 50)**2) * 0.7
            waveform = pulse1 + pulse2

        elif pattern == HapticPattern.RAIN:
            # Random droplet pattern
            waveform = np.zeros_like(t)
            num_drops = int(len(t) * 0.1)  # 10% of samples have drops
            drop_positions = np.random.choice(len(t), num_drops, replace=False)
            for pos in drop_positions:
                # Create small droplet impulse
                drop_length = min(20, len(t) - pos)
                waveform[pos:pos+drop_length] = np.exp(-np.linspace(0, 10, drop_length))

        elif pattern == HapticPattern.THUNDER:
            # Low frequency rumble with cracks
            # Rumble component
            rumble = np.sin(2 * np.pi * 20 * t) * np.exp(-t * 0.5)
            # Crack components
            cracks = np.zeros_like(t)
            num_cracks = 5
            for i in range(num_cracks):
                crack_time = np.random.uniform(0, effect.duration * 0.7)
                crack_sample = int(crack_time * self.sample_rate)
                if crack_sample < len(t):
                    crack_length = min(10, len(t) - crack_sample)
                    cracks[crack_sample:crack_sample+crack_length] = np.random.normal(0, 1, crack_length)

            waveform = rumble + cracks * 0.5

        else:  # CUSTOM or default
            waveform = np.sin(2 * np.pi * 100 * t)  # Default 100 Hz sine wave

        return waveform

    def _apply_adsr_envelope(self, waveform: np.ndarray, effect: HapticEffect) -> np.ndarray:
        """Apply ADSR (Attack, Decay, Sustain, Release) envelope"""
        samples = len(waveform)
        attack_samples = int(effect.attack_time * self.sample_rate)
        decay_samples = int(effect.decay_time * self.sample_rate)
        sustain_samples = int(effect.sustain_time * self.sample_rate)
        release_samples = samples - attack_samples - decay_samples - sustain_samples

        envelope = np.ones(samples)

        # Attack phase
        if effect.fade_in and attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay phase
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = decay_start + decay_samples
            envelope[decay_start:decay_end] = np.linspace(1, 0.7, decay_samples)

        # Sustain phase (already at 1.0 or decayed value)
        # Release phase
        if effect.fade_out and release_samples > 0:
            release_start = attack_samples + decay_samples + sustain_samples
            envelope[release_start:] = np.linspace(envelope[release_start-1], 0, release_samples)

        return waveform * envelope

    def _apply_frequency_modulation(self, waveform: np.ndarray, frequency: float) -> np.ndarray:
        """Apply frequency modulation to waveform"""
        # Simple frequency scaling by resampling
        if frequency == 100.0:  # No change needed
            return waveform

        # Calculate resampling factor
        resample_factor = frequency / 100.0

        if resample_factor != 1.0:
            # Resample the waveform
            new_length = int(len(waveform) / resample_factor)
            original_indices = np.linspace(0, len(waveform) - 1, len(waveform))
            new_indices = np.linspace(0, len(waveform) - 1, new_length)

            if signal:
                # Use scipy interpolation
                interpolator = interp1d(original_indices, waveform, kind='cubic',
                                      bounds_error=False, fill_value=0)
                resampled_waveform = interpolator(new_indices)
            else:
                # Fallback to simple interpolation
                resampled_waveform = np.interp(new_indices, original_indices, waveform)

            # Pad or trim to original length
            if len(resampled_waveform) < len(waveform):
                padded_waveform = np.zeros(len(waveform))
                padded_waveform[:len(resampled_waveform)] = resampled_waveform
                waveform = padded_waveform
            else:
                waveform = resampled_waveform[:len(waveform)]

        return waveform

    def generate_texture_waveform(self, texture: TextureProperties,
                                 interaction_speed: float = 1.0,
                                 duration: float = 1.0) -> np.ndarray:
        """Generate waveform for surface texture interaction"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)

        # Base waveform combining frequency components
        waveform = np.zeros(samples)

        for freq in texture.frequency_components:
            # Scale frequency by interaction speed
            scaled_freq = freq * interaction_speed

            # Add frequency component with amplitude based on texture properties
            amplitude = texture.roughness * np.exp(-freq / 200)  # Higher frequencies have less amplitude
            component = amplitude * np.sin(2 * np.pi * scaled_freq * t)

            # Add randomness for natural feel
            noise_factor = texture.roughness * 0.3
            component += noise_factor * np.random.normal(0, 1, samples) * np.exp(-freq / 100)

            waveform += component

        # Apply friction modulation
        friction_modulation = 1 + 0.2 * texture.friction * np.sin(2 * np.pi * 10 * t)
        waveform *= friction_modulation

        # Apply damping
        damping_factor = np.exp(-texture.damping * t * 2)
        waveform *= damping_factor

        # Normalize
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))

        return waveform


class HapticRenderer:
    """Render haptic effects to physical devices"""

    def __init__(self, sample_rate: int = 1000):
        self.sample_rate = sample_rate
        self.devices: Dict[str, HapticDevice] = {}
        self.active_effects: Dict[str, HapticEvent] = {}
        self.output_buffer = queue.Queue() if queue else None
        self.is_rendering = False
        self.render_thread = None

        # Device-specific interfaces
        self.serial_connections: Dict[str, serial.Serial] = {}
        self.pygame_initialized = False

    def add_device(self, device: HapticDevice):
        """Add haptic device"""
        self.devices[device.device_id] = device

        # Initialize device connection
        if device.device_type == HapticDeviceType.VIBRATION_MOTOR:
            self._initialize_vibration_device(device)
        elif device.device_type == HapticDeviceType.LINEAR_ACTUATOR:
            self._initialize_linear_actuator(device)
        elif device.device_type == HapticDeviceType.FORCE_FEEDBACK:
            self._initialize_force_feedback_device(device)

        logging.info(f"Added haptic device: {device.name}")

    def _initialize_vibration_device(self, device: HapticDevice):
        """Initialize vibration motor device"""
        if not pygame:
            # Try to initialize pygame for gamepad rumble
            try:
                pygame.init()
                pygame.joystick.init()
                self.pygame_initialized = True

                # Try to find joysticks
                if pygame.joystick.get_count() > 0:
                    joystick = pygame.joystick.Joystick(0)
                    joystick.init()
                    logging.info(f"Initialized joystick: {joystick.get_name()}")
            except Exception as e:
                logging.warning(f"Failed to initialize pygame: {e}")

    def _initialize_linear_actuator(self, device: HapticDevice):
        """Initialize linear actuator via serial"""
        if serial:
            try:
                # Try to find the device by name
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    if device.name.lower() in port.description.lower():
                        connection = serial.Serial(port.device, 115200, timeout=0.1)
                        self.serial_connections[device.device_id] = connection
                        logging.info(f"Connected to {device.name} on {port.device}")
                        break
            except Exception as e:
                logging.warning(f"Failed to connect to {device.name}: {e}")

    def _initialize_force_feedback_device(self, device: HapticDevice):
        """Initialize force feedback device"""
        # This would be device-specific initialization
        # Could be for devices like Novint Falcon, haptic gloves, etc.
        logging.info(f"Force feedback device {device.name} initialized (mock)")

    def play_effect(self, event: HapticEvent):
        """Play haptic effect on device"""
        if event.device_id not in self.devices:
            logging.warning(f"Device {event.device_id} not found")
            return

        device = self.devices[event.device_id]

        if not device.is_connected:
            logging.warning(f"Device {device.device_id} not connected")
            return

        # Add to active effects
        self.active_effects[event.event_id] = event

        # Queue for rendering
        if self.output_buffer:
            self.output_buffer.put(event)

        logging.info(f"Playing effect {event.effect.pattern.value} on {device.name}")

    def stop_effect(self, event_id: str):
        """Stop specific haptic effect"""
        if event_id in self.active_effects:
            del self.active_effects[event_id]
            logging.info(f"Stopped effect: {event_id}")

    def stop_all_effects(self, device_id: Optional[str] = None):
        """Stop all effects, optionally for specific device"""
        if device_id:
            effects_to_stop = [eid for eid, event in self.active_effects.items()
                             if event.device_id == device_id]
            for effect_id in effects_to_stop:
                self.stop_effect(effect_id)
        else:
            self.active_effects.clear()
            logging.info("Stopped all haptic effects")

    def start_rendering(self):
        """Start haptic rendering thread"""
        if self.is_rendering:
            return

        self.is_rendering = True
        self.render_thread = threading.Thread(target=self._render_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        logging.info("Started haptic rendering")

    def stop_rendering(self):
        """Stop haptic rendering"""
        self.is_rendering = False
        if self.render_thread:
            self.render_thread.join(timeout=1.0)
        logging.info("Stopped haptic rendering")

    def _render_loop(self):
        """Main haptic rendering loop"""
        waveform_generator = HapticWaveformGenerator(self.sample_rate)

        while self.is_rendering:
            try:
                # Get next effect to render
                if self.output_buffer:
                    try:
                        event = self.output_buffer.get_nowait()
                    except queue.Empty:
                        event = None
                else:
                    event = None

                if event:
                    # Generate waveform
                    waveform = waveform_generator.generate_waveform(event.effect)

                    # Send to device
                    self._send_to_device(event.device_id, waveform)

                    # Handle effect duration
                    if not event.effect.loop:
                        # Schedule effect removal
                        threading.Timer(event.effect.duration,
                                      lambda: self.stop_effect(event.event_id)).start()

                # Process active effects for continuous updates
                current_time = time.time()
                expired_effects = []

                for effect_id, effect_event in self.active_effects.items():
                    if not effect_event.effect.loop:
                        if current_time - effect_event.timestamp > effect_event.effect.duration:
                            expired_effects.append(effect_id)

                # Remove expired effects
                for effect_id in expired_effects:
                    self.stop_effect(effect_id)

                # Small delay to prevent excessive CPU usage
                time.sleep(0.001)

            except Exception as e:
                logging.error(f"Error in haptic rendering loop: {e}")

    def _send_to_device(self, device_id: str, waveform: np.ndarray):
        """Send waveform to specific device"""
        device = self.devices.get(device_id)
        if not device or not device.is_connected:
            return

        try:
            if device.device_type == HapticDeviceType.VIBRATION_MOTOR:
                self._send_to_vibration_device(device_id, waveform)
            elif device.device_type == HapticDeviceType.LINEAR_ACTUATOR:
                self._send_to_linear_actuator(device_id, waveform)
            elif device.device_type == HapticDeviceType.FORCE_FEEDBACK:
                self._send_to_force_feedback_device(device_id, waveform)
            elif device.device_type == HapticDeviceType.TACTILE_ARRAY:
                self._send_to_tactile_array(device_id, waveform)
        except Exception as e:
            logging.error(f"Error sending to device {device_id}: {e}")

    def _send_to_vibration_device(self, device_id: str, waveform: np.ndarray):
        """Send to vibration motor (gamepad rumble, etc.)"""
        if self.pygame_initialized and pygame:
            # Convert waveform to rumble intensity
            # Take the RMS of waveform chunks
            chunk_size = self.sample_rate // 30  # 30 FPS updates
            num_chunks = len(waveform) // chunk_size

            for i in range(num_chunks):
                chunk = waveform[i * chunk_size:(i + 1) * chunk_size]
                if len(chunk) > 0:
                    # Calculate RMS intensity
                    intensity = np.sqrt(np.mean(chunk**2))
                    # Scale to 0-65535 (pygame rumble range)
                    rumble_value = int(intensity * device.max_intensity * 65535)

                    # Apply rumble (simplified - would need actual gamepad interface)
                    # pygame.joystick.Joystick(0).rumble(rumble_value, rumble_value, 100)
                    pass

                time.sleep(1/30)  # 30 FPS update rate

    def _send_to_linear_actuator(self, device_id: str, waveform: np.ndarray):
        """Send to linear actuator via serial"""
        if device_id in self.serial_connections:
            connection = self.serial_connections[device_id]

            # Convert waveform to actuator commands
            # Sample at lower rate for actuator control
            sample_rate = 100  # 100 Hz for actuator
            sample_interval = len(waveform) // sample_rate

            for i in range(0, len(waveform), sample_interval):
                if i < len(waveform):
                    # Get sample value
                    value = waveform[i]

                    # Convert to actuator position/speed
                    # This would depend on the specific actuator
                    position = int(value * 127 + 128)  # 0-255 range

                    # Send command
                    command = f"POS:{position}\n"
                    connection.write(command.encode())

                time.sleep(1/sample_rate)

    def _send_to_force_feedback_device(self, device_id: str, waveform: np.ndarray):
        """Send to force feedback device"""
        # This would be device-specific implementation
        # Could include force vectors, stiffness, damping, etc.
        pass

    def _send_to_tactile_array(self, device_id: str, waveform: np.ndarray):
        """Send to tactile array (multiple vibration points)"""
        # Distribute waveform across array elements
        # This would depend on the specific array configuration
        pass


class PhysicsSimulator:
    """Physics simulation for realistic haptic feedback"""

    def __init__(self):
        self.materials: Dict[str, TextureProperties] = {}
        self.collision_threshold = 0.01
        self.force_scale = 1.0

        # Predefined materials
        self._create_materials()

    def _create_materials(self):
        """Create predefined material properties"""
        materials = {
            "wood": TextureProperties(TextureType.WOOD, roughness=0.6, friction=0.7, stiffness=0.8),
            "metal": TextureProperties(TextureType.METAL, roughness=0.2, friction=0.3, stiffness=0.9),
            "stone": TextureProperties(TextureType.STONE, roughness=0.8, friction=0.8, stiffness=0.95),
            "fabric": TextureProperties(TextureType.FABRIC, roughness=0.4, friction=0.6, stiffness=0.3),
            "glass": TextureProperties(TextureType.SMOOTH, roughness=0.1, friction=0.2, stiffness=0.7),
            "sand": TextureProperties(TextureType.SAND, roughness=0.9, friction=0.9, stiffness=0.2),
            "water": TextureProperties(TextureType.WATER, roughness=0.0, friction=0.1, stiffness=0.1)
        }

        self.materials.update(materials)

    def add_material(self, name: str, properties: TextureProperties):
        """Add custom material"""
        self.materials[name] = properties

    def calculate_collision_force(self, position: Vector3, velocity: Vector3,
                                material: str, normal: Vector3) -> Tuple[float, Vector3]:
        """Calculate collision force for haptic feedback"""
        if material not in self.materials:
            material = "wood"  # Default material

        mat_props = self.materials[material]

        # Calculate relative velocity along collision normal
        velocity_magnitude = velocity.magnitude()
        normal_magnitude = normal.magnitude()

        if normal_magnitude > 0:
            normal_normalized = Vector3(
                normal.x / normal_magnitude,
                normal.y / normal_magnitude,
                normal.z / normal_magnitude
            )
        else:
            normal_normalized = Vector3(0, 1, 0)

        # Impact force based on velocity and material stiffness
        impact_force = velocity_magnitude * mat_props.stiffness * self.force_scale

        # Add friction component
        tangent_velocity = velocity_magnitude * mat_props.friction

        # Total force magnitude
        total_force = impact_force + tangent_velocity

        # Apply force direction (mostly along normal)
        force_vector = normal_normalized * total_force

        return total_force, force_vector

    def simulate_surface_interaction(self, position: Vector3, velocity: Vector3,
                                   material: str, contact_area: float = 0.01) -> HapticEffect:
        """Simulate surface interaction and return haptic effect"""
        if material not in self.materials:
            material = "wood"

        mat_props = self.materials[material]

        # Calculate interaction parameters
        speed = velocity.magnitude()
        interaction_strength = min(speed * mat_props.roughness, 1.0)

        # Determine pattern based on material and speed
        if speed < 0.1:
            pattern = HapticPattern.TAP
        elif speed < 0.5:
            pattern = HapticPattern.PULSE
        else:
            pattern = HapticPattern.BUZZ

        # Calculate frequency based on material properties
        base_frequency = np.mean(mat_props.frequency_components)
        frequency = base_frequency * (1 + speed * 0.5)

        # Create haptic effect
        effect = HapticEffect(
            effect_id=f"surface_{material}_{int(time.time() * 1000)}",
            pattern=pattern,
            intensity=interaction_strength,
            duration=min(0.5, 0.1 + speed * 0.2),
            frequency=frequency,
            attack_time=0.02,
            decay_time=0.05,
            fade_in=True,
            fade_out=True
        )

        return effect


class DMLogn8nHapticSystem:
    """DMLogn8n-specific haptic system integration"""

    def __init__(self):
        self.renderer = HapticRenderer()
        self.physics_simulator = PhysicsSimulator()
        self.waveform_generator = HapticWaveformGenerator()

        # Game-specific haptic profiles
        self.action_effects: Dict[str, HapticEffect] = {}
        self.environment_materials: Dict[str, str] = {}

        # Player state
        self.player_position = Vector3()
        self.player_velocity = Vector3()
        self.is_touching_surface = False
        self.current_surface = None

        self._create_action_effects()
        self._setup_environment_materials()

    def _create_action_effects(self):
        """Create haptic effects for game actions"""
        # Combat actions
        self.action_effects["sword_hit"] = HapticEffect(
            effect_id="sword_hit",
            pattern=HapticPattern.EXPLOSION,
            intensity=0.8,
            duration=0.3,
            frequency=150,
            attack_time=0.01,
            decay_time=0.1
        )

        self.action_effects["spell_cast"] = HapticEffect(
            effect_id="spell_cast",
            pattern=HapticPattern.WAVE,
            intensity=0.6,
            duration=1.5,
            frequency=80,
            fade_in=True,
            fade_out=True
        )

        self.action_effects["arrow_release"] = HapticEffect(
            effect_id="arrow_release",
            pattern=HapticPattern.PULSE,
            intensity=0.5,
            duration=0.2,
            frequency=200
        )

        # Environmental effects
        self.action_effects["door_open"] = HapticEffect(
            effect_id="door_open",
            pattern=HapticPattern.RUMBLE,
            intensity=0.4,
            duration=0.8,
            frequency=40
        )

        self.action_effects["footstep"] = HapticEffect(
            effect_id="footstep",
            pattern=HapticPattern.TAP,
            intensity=0.3,
            duration=0.15,
            frequency=60
        )

        self.action_effects["heartbeat"] = HapticEffect(
            effect_id="heartbeat",
            pattern=HapticPattern.HEARTBEAT,
            intensity=0.4,
            duration=2.0,
            frequency=1.2,
            loop=True
        )

        # UI interactions
        self.action_effects["button_click"] = HapticEffect(
            effect_id="button_click",
            pattern=HapticPattern.TAP,
            intensity=0.5,
            duration=0.1,
            frequency=100
        )

        self.action_effects["notification"] = HapticEffect(
            effect_id="notification",
            pattern=HapticPattern.PULSE,
            intensity=0.3,
            duration=0.5,
            frequency=120
        )

    def _setup_environment_materials(self):
        """Setup material properties for game environment"""
        self.environment_materials.update({
            "tavern_floor": "wood",
            "tavern_bar": "wood",
            "tavern_table": "wood",
            "tavern_chair": "wood",
            "fireplace": "stone",
            "walls": "stone",
            "glasses": "glass",
            "bottles": "glass",
            "armor": "metal",
            "weapons": "metal",
            "clothing": "fabric",
            "ground_outside": "sand",
            "water": "water"
        })

    def initialize_default_devices(self):
        """Initialize common haptic devices"""
        # Game controller vibration motors
        left_controller = HapticDevice(
            device_id="controller_left",
            device_type=HapticDeviceType.VIBRATION_MOTOR,
            name="Left Controller",
            position=Vector3(-0.3, 1.2, -0.2)
        )

        right_controller = HapticDevice(
            device_id="controller_right",
            device_type=HapticDeviceType.VIBRATION_MOTOR,
            name="Right Controller",
            position=Vector3(0.3, 1.2, -0.2)
        )

        self.renderer.add_device(left_controller)
        self.renderer.add_device(right_controller)

        # Haptic vest (mock)
        haptic_vest = HapticDevice(
            device_id="haptic_vest",
            device_type=HapticDeviceType.TACTILE_ARRAY,
            name="Haptic Vest",
            position=Vector3(0, 1.0, 0)
        )

        self.renderer.add_device(haptic_vest)

        # Start rendering
        self.renderer.start_rendering()

    def play_action_effect(self, action_name: str, device_id: str = "controller_right"):
        """Play haptic effect for game action"""
        if action_name in self.action_effects:
            effect = self.action_effects[action_name]
            event = HapticEvent(
                event_id=f"{action_name}_{int(time.time() * 1000)}",
                device_id=device_id,
                effect=effect
            )
            self.renderer.play_effect(event)

    def simulate_surface_touch(self, surface_name: str, contact_position: Vector3,
                              hand_velocity: Vector3, device_id: str = "controller_right"):
        """Simulate touching a surface"""
        material_name = self.environment_materials.get(surface_name, "wood")

        # Calculate haptic effect based on surface interaction
        haptic_effect = self.physics_simulator.simulate_surface_interaction(
            contact_position, hand_velocity, material_name
        )

        event = HapticEvent(
            event_id=f"surface_{surface_name}_{int(time.time() * 1000)}",
            device_id=device_id,
            effect=haptic_effect,
            position=contact_position
        )

        self.renderer.play_effect(event)

    def simulate_collision(self, object_name: str, collision_position: Vector3,
                          impact_velocity: Vector3, device_id: str = "controller_right"):
        """Simulate collision with object"""
        material_name = self.environment_materials.get(object_name, "wood")

        # Calculate collision force
        force, force_vector = self.physics_simulator.calculate_collision_force(
            collision_position, impact_velocity, material_name, Vector3(0, 1, 0)
        )

        # Create impact effect
        impact_effect = HapticEffect(
            effect_id=f"collision_{object_name}_{int(time.time() * 1000)}",
            pattern=HapticPattern.EXPLOSION if force > 0.5 else HapticPattern.TAP,
            intensity=min(force, 1.0),
            duration=0.1 + force * 0.2,
            frequency=100 + force * 200,
            attack_time=0.01,
            decay_time=0.05
        )

        event = HapticEvent(
            event_id=f"collision_event_{int(time.time() * 1000)}",
            device_id=device_id,
            effect=impact_effect,
            position=collision_position
        )

        self.renderer.play_effect(event)

    def create_ambient_effect(self, environment: str, device_id: str = "haptic_vest"):
        """Create ambient haptic effect for environment"""
        if environment == "tavern":
            # Low rumble from fireplace and activity
            ambient_effect = HapticEffect(
                effect_id="tavern_ambient",
                pattern=HapticPattern.RUMBLE,
                intensity=0.2,
                duration=10.0,
                frequency=30,
                loop=True
            )
        elif environment == "combat":
            # Occasional impacts
            ambient_effect = HapticEffect(
                effect_id="combat_ambient",
                pattern=HapticPattern.PULSE,
                intensity=0.4,
                duration=5.0,
                frequency=80,
                loop=True
            )
        elif environment == "magic":
            # Magical tingling
            ambient_effect = HapticEffect(
                effect_id="magic_ambient",
                pattern=HapticPattern.WAVE,
                intensity=0.3,
                duration=8.0,
                frequency=120,
                loop=True
            )
        else:
            return

        event = HapticEvent(
            event_id=f"ambient_{environment}_{int(time.time() * 1000)}",
            device_id=device_id,
            effect=ambient_effect
        )

        self.renderer.play_effect(event)

    def stop_ambient_effects(self, device_id: Optional[str] = None):
        """Stop ambient effects"""
        # Stop all looping effects
        effects_to_stop = []
        for effect_id, event in self.renderer.active_effects.items():
            if event.effect.loop:
                if device_id is None or event.device_id == device_id:
                    effects_to_stop.append(effect_id)

        for effect_id in effects_to_stop:
            self.renderer.stop_effect(effect_id)

    def update_player_state(self, position: Vector3, velocity: Vector3):
        """Update player state for physics simulation"""
        self.player_position = position
        self.player_velocity = velocity

        # Check for footstep effects
        if velocity.magnitude() > 0.1:
            # Simulate footstep at regular intervals based on speed
            step_interval = 0.5 / velocity.magnitude()  # Faster movement = more frequent steps
            if not hasattr(self, '_last_step_time'):
                self._last_step_time = 0

            if time.time() - self._last_step_time > step_interval:
                self.play_action_effect("footstep", "controller_left" if np.random.random() > 0.5 else "controller_right")
                self._last_step_time = time.time()

    def shutdown(self):
        """Shutdown haptic system"""
        self.renderer.stop_rendering()
        self.renderer.stop_all_effects()
        logging.info("Haptic system shutdown complete")


async def main():
    """Main function to test haptic system"""
    logging.basicConfig(level=logging.INFO)

    # Create DMLogn8n haptic system
    haptic_system = DMLogn8nHapticSystem()

    # Initialize default devices
    haptic_system.initialize_default_devices()

    try:
        print("DMLogn8n Haptic System Test")
        print("Testing various haptic effects...")

        # Test action effects
        print("\nTesting action effects:")
        haptic_system.play_action_effect("sword_hit")
        await asyncio.sleep(1.0)

        haptic_system.play_action_effect("spell_cast")
        await asyncio.sleep(2.0)

        haptic_system.play_action_effect("door_open")
        await asyncio.sleep(1.0)

        # Test surface interactions
        print("\nTesting surface interactions:")
        haptic_system.simulate_surface_touch(
            "tavern_bar",
            Vector3(0, 1, 0),
            Vector3(0.1, 0, 0),
            "controller_right"
        )
        await asyncio.sleep(1.0)

        haptic_system.simulate_surface_touch(
            "fireplace",
            Vector3(0, 1, 0),
            Vector3(0.05, 0, 0),
            "controller_right"
        )
        await asyncio.sleep(1.0)

        # Test collisions
        print("\nTesting collisions:")
        haptic_system.simulate_collision(
            "armor",
            Vector3(0, 1, 0),
            Vector3(0.5, 0, 0),
            "controller_right"
        )
        await asyncio.sleep(1.0)

        # Test ambient effects
        print("\nTesting ambient effects:")
        haptic_system.create_ambient_effect("tavern")
        await asyncio.sleep(3.0)
        haptic_system.stop_ambient_effects()

        # Test continuous player movement
        print("\nTesting player movement:")
        for i in range(10):
            haptic_system.update_player_state(
                Vector3(i * 0.1, 0, 0),
                Vector3(0.2, 0, 0)
            )
            await asyncio.sleep(0.5)

        print("\nHaptic system test completed!")

    except KeyboardInterrupt:
        pass
    finally:
        haptic_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())