#!/usr/bin/env python3
"""
HOLOGRAPHIC SOUND
Revolutionary system that creates sound as holographic fields in physical space.
Sound that exists as physical phenomena with wave interference and field dynamics.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, ifft, fft2, ifft2
import threading
import queue
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Union
import math
import cmath
from collections import deque
import logging
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HolographicSound")

class HolographicFieldType(Enum):
    """Types of holographic sound fields"""
    STANDING_WAVE = "standing_wave"
    TRAVELING_WAVE = "traveling_wave"
    INTERFERENCE_PATTERN = "interference_pattern"
    VORTEX_FIELD = "vortex_field"
    RESONANCE_FIELD = "resonance_field"
    PHASE_CONJUGATE = "phase_conjugate"
    SOLITON_WAVE = "soliton_wave"
    ACOUSTIC_LENS = "acoustic_lens"

@dataclass
class HolographicPoint:
    """Point in 3D holographic sound space"""
    x: float
    y: float
    z: float
    amplitude: complex
    phase: float
    frequency: float

@dataclass
class WaveFieldSource:
    """Source of holographic wave field"""
    position: Tuple[float, float, float]
    frequency: float
    amplitude: float
    phase: float
    beam_width: float
    field_type: HolographicFieldType

@dataclass
class InterferencePattern:
    """Acoustic interference pattern in 3D space"""
    points: List[HolographicPoint]
    field_strength: np.ndarray
    phase_map: np.ndarray
    frequency_spectrum: np.ndarray

class HolographicFieldGenerator:
    """Generates holographic acoustic fields using wave physics"""

    def __init__(self, room_dimensions: Tuple[float, float, float] = (10, 5, 8),
                 grid_resolution: Tuple[int, int, int] = (64, 32, 48)):
        self.room_dimensions = room_dimensions
        self.grid_resolution = grid_resolution

        # Physical constants
        self.speed_of_sound = 343.0  # m/s at 20°C
        self.air_density = 1.225     # kg/m³
        self.acoustic_impedance = self.speed_of_sound * self.air_density

        # Wave field parameters
        self.wavelength_resolution = 0.1  # meters
        self.max_frequency = 20000  # Hz
        self.min_frequency = 20     # Hz

        # Create 3D spatial grid
        self._create_spatial_grid()

        # Field storage
        self.current_field = np.zeros(self.grid_resolution, dtype=complex)
        self.field_history = deque(maxlen=10)
        self.field_derivatives = {
            'dx': np.zeros(self.grid_resolution, dtype=complex),
            'dy': np.zeros(self.grid_resolution, dtype=complex),
            'dz': np.zeros(self.grid_resolution, dtype=complex),
            'dt': np.zeros(self.grid_resolution, dtype=complex)
        }

    def _create_spatial_grid(self):
        """Create 3D spatial coordinate grid"""
        x = np.linspace(0, self.room_dimensions[0], self.grid_resolution[0])
        y = np.linspace(0, self.room_dimensions[1], self.grid_resolution[1])
        z = np.linspace(0, self.room_dimensions[2], self.grid_resolution[2])

        self.X, self.Y, self.Z = np.meshgrid(x, y, z, indexing='ij')
        self.grid_spacing = (x[1] - x[0], y[1] - y[0], z[1] - z[0])

    def generate_holographic_field(self, sources: List[WaveFieldSource], time: float) -> np.ndarray:
        """Generate holographic acoustic field from multiple sources"""
        # Initialize field
        field = np.zeros(self.grid_resolution, dtype=complex)

        # Calculate contribution from each source
        for source in sources:
            field += self._calculate_source_field(source, time)

        # Apply boundary conditions
        field = self._apply_boundary_conditions(field)

        # Apply non-linear effects
        field = self._apply_nonlinear_effects(field)

        # Store field in history
        self.field_history.append(field.copy())

        # Calculate derivatives
        self._calculate_field_derivatives(field)

        self.current_field = field

        return field

    def _calculate_source_field(self, source: WaveFieldSource, time: float) -> np.ndarray:
        """Calculate field contribution from a single source"""
        # Calculate distance from source to each grid point
        dx = self.X - source.position[0]
        dy = self.Y - source.position[1]
        dz = self.Z - source.position[2]
        distance = np.sqrt(dx**2 + dy**2 + dz**2 + 1e-10)  # Avoid division by zero

        # Calculate wave number
        k = 2 * np.pi * source.frequency / self.speed_of_sound

        # Calculate phase at each point
        phase = k * distance - 2 * np.pi * source.frequency * time + source.phase

        # Calculate amplitude with distance attenuation
        amplitude = source.amplitude / (1 + distance * 0.1)  # Spherical spreading

        # Apply beam shaping
        beam_factor = self._apply_beam_shaping(source, dx, dy, dz, distance)
        amplitude *= beam_factor

        # Generate field based on field type
        if source.field_type == HolographicFieldType.STANDING_WAVE:
            field_contribution = self._generate_standing_wave(amplitude, phase, k)
        elif source.field_type == HolographicFieldType.TRAVELING_WAVE:
            field_contribution = self._generate_traveling_wave(amplitude, phase, distance, k)
        elif source.field_type == HolographicFieldType.INTERFERENCE_PATTERN:
            field_contribution = self._generate_interference_pattern(amplitude, phase, k, source)
        elif source.field_type == HolographicFieldType.VORTEX_FIELD:
            field_contribution = self._generate_vortex_field(amplitude, phase, dx, dy, dz)
        elif source.field_type == HolographicFieldType.RESONANCE_FIELD:
            field_contribution = self._generate_resonance_field(amplitude, phase, k)
        elif source.field_type == HolographicFieldType.PHASE_CONJUGATE:
            field_contribution = self._generate_phase_conjugate(amplitude, phase, distance, k)
        elif source.field_type == HolographicFieldType.SOLITON_WAVE:
            field_contribution = self._generate_soliton_wave(amplitude, phase, distance, k, time)
        elif source.field_type == HolographicFieldType.ACOUSTIC_LENS:
            field_contribution = self._generate_acoustic_lens(amplitude, phase, dx, dy, dz, k)
        else:
            field_contribution = amplitude * np.exp(1j * phase)

        return field_contribution

    def _apply_beam_shaping(self, source: WaveFieldSource, dx: np.ndarray, dy: np.ndarray,
                          dz: np.ndarray, distance: np.ndarray) -> np.ndarray:
        """Apply beam shaping to source field"""
        # Gaussian beam profile
        beam_center_x, beam_center_y = 0, 0
        beam_width = source.beam_width

        # Calculate radial distance from beam axis
        radial_distance = np.sqrt((dx - beam_center_x)**2 + (dy - beam_center_y)**2)

        # Gaussian beam profile
        beam_factor = np.exp(-(radial_distance**2) / (2 * beam_width**2))

        # Add directional preference
        if hasattr(source, 'direction'):
            direction = np.array(source.direction)
            position_vectors = np.stack([dx.flatten(), dy.flatten(), dz.flatten()], axis=1)
            direction_factor = np.dot(position_vectors, direction) / (distance.flatten() + 1e-10)
            direction_factor = direction_factor.reshape(distance.shape)
            beam_factor *= np.maximum(0, direction_factor)

        return beam_factor

    def _generate_standing_wave(self, amplitude: np.ndarray, phase: np.ndarray, k: float) -> np.ndarray:
        """Generate standing wave pattern"""
        # Standing wave: sum of forward and backward traveling waves
        standing_wave = amplitude * (np.exp(1j * phase) + np.exp(-1j * phase)) / 2
        return standing_wave

    def _generate_traveling_wave(self, amplitude: np.ndarray, phase: np.ndarray,
                               distance: np.ndarray, k: float) -> np.ndarray:
        """Generate traveling wave"""
        # Outgoing spherical wave
        traveling_wave = amplitude * np.exp(1j * phase)
        return traveling_wave

    def _generate_interference_pattern(self, amplitude: np.ndarray, phase: np.ndarray,
                                     k: float, source: WaveFieldSource) -> np.ndarray:
        """Generate complex interference pattern"""
        # Create multiple coherent sources for interference
        field = amplitude * np.exp(1j * phase)

        # Add secondary sources for interference
        for i in range(3):
            offset_angle = i * 2 * np.pi / 3
            offset_x = source.position[0] + 0.5 * np.cos(offset_angle)
            offset_y = source.position[1] + 0.5 * np.sin(offset_angle)

            dx = self.X - offset_x
            dy = self.Y - offset_y
            dz = self.Z - source.position[2]
            offset_distance = np.sqrt(dx**2 + dy**2 + dz**2 + 1e-10)

            offset_phase = k * offset_distance - 2 * np.pi * source.frequency * 0 + source.phase + i * np.pi/3
            offset_amplitude = source.amplitude / (1 + offset_distance * 0.1)

            field += offset_amplitude * np.exp(1j * offset_phase)

        return field

    def _generate_vortex_field(self, amplitude: np.ndarray, phase: np.ndarray,
                             dx: np.ndarray, dy: np.ndarray, dz: np.ndarray) -> np.ndarray:
        """Generate acoustic vortex field"""
        # Calculate azimuthal angle
        azimuth = np.arctan2(dy, dx)
        radial_distance = np.sqrt(dx**2 + dy**2)

        # Vortex phase with topological charge
        topological_charge = 2
        vortex_phase = phase + topological_charge * azimuth

        # Amplitude profile with dark core
        vortex_amplitude = amplitude * (radial_distance / (radial_distance + 0.5))

        return vortex_amplitude * np.exp(1j * vortex_phase)

    def _generate_resonance_field(self, amplitude: np.ndarray, phase: np.ndarray, k: float) -> np.ndarray:
        """Generate resonance field with cavity modes"""
        # Calculate cavity resonance frequencies
        room_modes = self._calculate_cavity_modes()

        # Create resonant field pattern
        field = np.zeros_like(amplitude, dtype=complex)

        for mode in room_modes[:5]:  # Use first 5 modes
            mode_amplitude = amplitude * 0.2
            mode_phase = phase + mode['phase_shift']

            # Create standing wave pattern for this mode
            nx, ny, nz = mode['mode_numbers']
            mode_pattern = np.sin(nx * np.pi * self.X / self.room_dimensions[0])
            mode_pattern *= np.sin(ny * np.pi * self.Y / self.room_dimensions[1])
            mode_pattern *= np.sin(nz * np.pi * self.Z / self.room_dimensions[2])

            field += mode_amplitude * mode_pattern * np.exp(1j * mode_phase)

        return field

    def _calculate_cavity_modes(self) -> List[Dict]:
        """Calculate acoustic cavity modes for the room"""
        modes = []
        max_mode_number = 5

        for nx in range(max_mode_number):
            for ny in range(max_mode_number):
                for nz in range(max_mode_number):
                    if nx + ny + nz > 0:  # Skip (0,0,0) mode
                        frequency = (self.speed_of_sound / 2) * np.sqrt(
                            (nx / self.room_dimensions[0])**2 +
                            (ny / self.room_dimensions[1])**2 +
                            (nz / self.room_dimensions[2])**2
                        )

                        if frequency <= self.max_frequency:
                            modes.append({
                                'mode_numbers': (nx, ny, nz),
                                'frequency': frequency,
                                'phase_shift': np.random.uniform(0, 2*np.pi)
                            })

        # Sort by frequency
        modes.sort(key=lambda x: x['frequency'])
        return modes

    def _generate_phase_conjugate(self, amplitude: np.ndarray, phase: np.ndarray,
                                distance: np.ndarray, k: float) -> np.ndarray:
        """Generate phase conjugate wave (time-reversed wave)"""
        # Phase conjugate: complex conjugate of original field
        original_field = amplitude * np.exp(1j * phase)
        conjugate_field = np.conj(original_field)

        # Add focusing effect
        focus_factor = np.exp(-distance**2 / (2 * 1.0**2))  # Focus at 1m
        conjugate_field *= focus_factor

        return conjugate_field

    def _generate_soliton_wave(self, amplitude: np.ndarray, phase: np.ndarray,
                             distance: np.ndarray, k: float, time: float) -> np.ndarray:
        """Generate acoustic soliton (solitary wave)"""
        # Soliton envelope
        soliton_width = 0.5
        soliton_speed = self.speed_of_sound * 0.8
        soliton_position = soliton_speed * time

        # Envelope function
        envelope = amplitude / np.cosh((distance - soliton_position) / soliton_width)

        # Carrier wave
        carrier = np.exp(1j * phase)

        return envelope * carrier

    def _generate_acoustic_lens(self, amplitude: np.ndarray, phase: np.ndarray,
                              dx: np.ndarray, dy: np.ndarray, dz: np.ndarray, k: float) -> np.ndarray:
        """Generate acoustic lens field"""
        # Lens focal length
        focal_length = 2.0  # meters

        # Radial distance from optical axis
        r = np.sqrt(dx**2 + dy**2)

        # Lens phase profile (quadratic)
        lens_phase = -k * r**2 / (2 * focal_length)

        # Total phase
        total_phase = phase + lens_phase

        # Amplitude with lens aperture
        aperture_radius = 1.0
        aperture = np.where(r <= aperture_radius, amplitude, 0)

        return aperture * np.exp(1j * total_phase)

    def _apply_boundary_conditions(self, field: np.ndarray) -> np.ndarray:
        """Apply boundary conditions to field"""
        # Rigid walls (Neumann boundary conditions)
        # Zero normal derivative at boundaries

        # X boundaries
        field[0, :, :] = field[1, :, :]
        field[-1, :, :] = field[-2, :, :]

        # Y boundaries
        field[:, 0, :] = field[:, 1, :]
        field[:, -1, :] = field[:, -2, :]

        # Z boundaries
        field[:, :, 0] = field[:, :, 1]
        field[:, :, -1] = field[:, :, -2]

        return field

    def _apply_nonlinear_effects(self, field: np.ndarray) -> np.ndarray:
        """Apply nonlinear acoustic effects"""
        # Nonlinear propagation (simplified Westervelt equation)
        # Account for harmonic generation and shock formation

        # Calculate pressure amplitude
        pressure_amplitude = np.abs(field)

        # Nonlinear parameter for air
        beta = 1.2  # Nonlinearity parameter

        # Apply nonlinear term
        nonlinear_factor = 1 - beta * pressure_amplitude / (self.acoustic_impedance + 1e-10)
        nonlinear_factor = np.maximum(nonlinear_factor, 0.5)  # Limit nonlinearity

        return field * nonlinear_factor

    def _calculate_field_derivatives(self, field: np.ndarray):
        """Calculate spatial and temporal derivatives of field"""
        # Spatial derivatives using finite differences
        self.field_derivatives['dx'] = np.gradient(field, self.grid_spacing[0], axis=0)
        self.field_derivatives['dy'] = np.gradient(field, self.grid_spacing[1], axis=1)
        self.field_derivatives['dz'] = np.gradient(field, self.grid_spacing[2], axis=2)

        # Temporal derivative using field history
        if len(self.field_history) >= 2:
            dt = 0.001  # Assume 1ms time step
            self.field_derivatives['dt'] = (field - self.field_history[-2]) / dt

    def extract_listener_audio(self, field: np.ndarray, listener_position: Tuple[float, float, float]) -> complex:
        """Extract audio at listener position from holographic field"""
        # Find nearest grid point to listener position
        ix = int(listener_position[0] / self.room_dimensions[0] * self.grid_resolution[0])
        iy = int(listener_position[1] / self.room_dimensions[1] * self.grid_resolution[1])
        iz = int(listener_position[2] / self.room_dimensions[2] * self.grid_resolution[2])

        # Clamp indices to valid range
        ix = np.clip(ix, 0, self.grid_resolution[0] - 1)
        iy = np.clip(iy, 0, self.grid_resolution[1] - 1)
        iz = np.clip(iz, 0, self.grid_resolution[2] - 1)

        # Extract field value at listener position
        return field[ix, iy, iz]

    def calculate_field_intensity(self, field: np.ndarray) -> np.ndarray:
        """Calculate acoustic intensity field"""
        # Intensity is proportional to |field|^2
        intensity = np.abs(field)**2

        # Also consider particle velocity (gradient of pressure)
        velocity_squared = (np.abs(self.field_derivatives['dx'])**2 +
                          np.abs(self.field_derivatives['dy'])**2 +
                          np.abs(self.field_derivatives['dz'])**2)

        # Acoustic intensity
        intensity = (intensity + velocity_squared) / (2 * self.acoustic_impedance)

        return intensity

    def visualize_field_slice(self, field: np.ndarray, axis: str = 'z', position: float = 0.5) -> np.ndarray:
        """Extract 2D slice of 3D field for visualization"""
        if axis == 'x':
            idx = int(position * self.grid_resolution[0])
            slice_field = field[idx, :, :]
        elif axis == 'y':
            idx = int(position * self.grid_resolution[1])
            slice_field = field[:, idx, :]
        elif axis == 'z':
            idx = int(position * self.grid_resolution[2])
            slice_field = field[:, :, idx]
        else:
            raise ValueError("Axis must be 'x', 'y', or 'z'")

        return np.abs(slice_field)

class HolographicSoundRenderer:
    """Renders holographic sound fields to audio"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.field_generator = HolographicFieldGenerator()
        self.listener_positions = [(5, 2.5, 4)]  # Default listener at center
        self.rendering_buffer = deque(maxlen=100)

    def render_holographic_audio(self, sources: List[WaveFieldSource], duration: float,
                               listener_positions: List[Tuple[float, float, float]] = None) -> np.ndarray:
        """Render holographic sound field to audio"""
        if listener_positions is None:
            listener_positions = self.listener_positions

        num_samples = int(duration * self.sample_rate)
        audio_output = np.zeros(num_samples)

        # Time vector
        t = np.linspace(0, duration, num_samples)

        for i, time_point in enumerate(t):
            # Generate holographic field at this time
            field = self.field_generator.generate_holographic_field(sources, time_point)

            # Extract audio at listener positions
            listener_audio = 0
            for listener_pos in listener_positions:
                field_value = self.field_generator.extract_listener_audio(field, listener_pos)
                listener_audio += np.real(field_value)

            # Average over listeners
            if listener_positions:
                listener_audio /= len(listener_positions)

            audio_output[i] = listener_audio

        # Apply post-processing
        audio_output = self._apply_post_processing(audio_output)

        return audio_output

    def _apply_post_processing(self, audio: np.ndarray) -> np.ndarray:
        """Apply post-processing to rendered audio"""
        # High-pass filter to remove DC
        b, a = signal.butter(4, 20 / (self.sample_rate / 2), 'high')
        audio = signal.filtfilt(b, a, audio)

        # Compression
        audio = np.tanh(audio * 0.8)

        # Normalize
        audio = audio / (np.max(np.abs(audio)) + 1e-10)

        return audio

class HolographicSoundSystem:
    """Main holographic sound system"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.renderer = HolographicSoundRenderer(sample_rate)
        self.active_sources = []
        self.source_id_counter = 0

        # Real-time processing
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.processing_thread = None

        # Field visualization
        self.field_slices = {}
        self.intensity_field = None

        # Performance monitoring
        self.performance_metrics = {
            'fields_generated': 0,
            'sources_rendered': 0,
            'rendering_time': deque(maxlen=100)
        }

    def create_holographic_source(self, position: Tuple[float, float, float],
                                frequency: float, amplitude: float = 0.5,
                                field_type: HolographicFieldType = HolographicFieldType.STANDING_WAVE,
                                beam_width: float = 1.0) -> int:
        """Create a holographic sound source"""
        source_id = self.source_id_counter
        self.source_id_counter += 1

        source = WaveFieldSource(
            position=position,
            frequency=frequency,
            amplitude=amplitude,
            phase=np.random.uniform(0, 2*np.pi),
            beam_width=beam_width,
            field_type=field_type
        )

        self.active_sources.append(source)

        logger.info(f"Created holographic source {source_id} at {position} with {field_type.value} field")

        return source_id

    def create_holographic_scene(self, scene_type: str = "symphony") -> Dict[str, int]:
        """Create predefined holographic scenes"""
        sources = {}

        if scene_type == "symphony":
            # Symphony orchestra with different field types
            instruments = [
                ((2, 3, 2), 440, HolographicFieldType.STANDING_WAVE, "violins"),
                ((8, 3, 2), 220, HolographicFieldType.RESONANCE_FIELD, "cellos"),
                ((5, 1, 1), 110, HolographicFieldType.VORTEX_FIELD, "bass"),
                ((2, 4, 6), 880, HolographicFieldType.INTERFERENCE_PATTERN, "flutes"),
                ((8, 4, 6), 660, HolographicFieldType.ACOUSTIC_LENS, "clarinets"),
                ((5, 2.5, 8), 1000, HolographicFieldType.TRAVELING_WAVE, "trumpets"),
                ((3, 1, 4), 550, HolographicFieldType.SOLITON_WAVE, "horns"),
                ((7, 1, 4), 330, HolographicFieldType.PHASE_CONJUGATE, "trombones"),
            ]

            for i, (position, frequency, field_type, name) in enumerate(instruments):
                source_id = self.create_holographic_source(position, frequency, 0.3, field_type)
                sources[name] = source_id

        elif scene_type == "vortex_concert":
            # Vortex-based musical experience
            vortex_sources = []
            for i in range(6):
                angle = i * 2 * np.pi / 6
                radius = 2.0
                x = 5 + radius * np.cos(angle)
                y = 2.5 + radius * np.sin(angle)
                z = 4
                frequency = 220 * (1 + i * 0.25)  # Harmonic series

                source_id = self.create_holographic_source(
                    (x, y, z), frequency, 0.4, HolographicFieldType.VORTEX_FIELD
                )
                sources[f"vortex_{i}"] = source_id

        elif scene_type == "resonance_chamber":
            # Acoustic resonance patterns
            for i in range(4):
                for j in range(3):
                    x = (i + 1) * 2
                    y = (j + 1) * 1.5
                    z = 4
                    frequency = 100 + i * 50 + j * 100

                    source_id = self.create_holographic_source(
                        (x, y, z), frequency, 0.3, HolographicFieldType.RESONANCE_FIELD
                    )
                    sources[f"resonance_{i}_{j}"] = source_id

        return sources

    def move_source(self, source_id: int, new_position: Tuple[float, float, float]):
        """Move holographic source to new position"""
        if source_id < len(self.active_sources):
            self.active_sources[source_id].position = new_position

    def set_source_field_type(self, source_id: int, field_type: HolographicFieldType):
        """Change field type of holographic source"""
        if source_id < len(self.active_sources):
            self.active_sources[source_id].field_type = field_type

    def generate_holographic_audio(self, duration: float,
                                 listener_positions: List[Tuple[float, float, float]] = None) -> np.ndarray:
        """Generate holographic audio for specified duration"""
        start_time = time.time()

        audio = self.renderer.render_holographic_audio(
            self.active_sources, duration, listener_positions
        )

        # Update performance metrics
        rendering_time = time.time() - start_time
        self.performance_metrics['rendering_time'].append(rendering_time)
        self.performance_metrics['fields_generated'] += 1
        self.performance_metrics['sources_rendered'] += len(self.active_sources)

        # Store intensity field for visualization
        if self.renderer.field_generator.current_field is not None:
            self.intensity_field = self.renderer.field_generator.calculate_field_intensity(
                self.renderer.field_generator.current_field
            )

        logger.info(f"Generated holographic audio in {rendering_time:.3f}s with {len(self.active_sources)} sources")

        return audio

    def start_real_time_rendering(self, chunk_duration: float = 0.5):
        """Start real-time holographic audio rendering"""
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._real_time_rendering_loop,
            args=(chunk_duration,),
            daemon=True
        )
        self.processing_thread.start()

        logger.info("Started real-time holographic audio rendering")

    def _real_time_rendering_loop(self, chunk_duration: float):
        """Real-time rendering loop"""
        while self.is_running:
            start_time = time.time()

            # Generate audio chunk
            audio_chunk = self.generate_holographic_audio(chunk_duration)
            self.audio_queue.put(audio_chunk)

            # Maintain real-time performance
            elapsed = time.time() - start_time
            if elapsed < chunk_duration:
                time.sleep(chunk_duration - elapsed)

    def stop_real_time_rendering(self):
        """Stop real-time rendering"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        logger.info("Stopped real-time holographic audio rendering")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def get_field_visualization(self, axis: str = 'z', position: float = 0.5) -> Optional[np.ndarray]:
        """Get visualization slice of current holographic field"""
        if self.renderer.field_generator.current_field is not None:
            return self.renderer.field_generator.visualize_field_slice(
                self.renderer.field_generator.current_field, axis, position
            )
        return None

    def save_holographic_audio(self, audio: np.ndarray, filename: str):
        """Save holographic audio to file"""
        sf.write(filename, audio, self.sample_rate)
        logger.info(f"Saved holographic audio to {filename}")

    def save_field_data(self, filename: str):
        """Save holographic field data"""
        if self.intensity_field is not None:
            np.save(filename.replace('.npy', '_intensity.npy'), self.intensity_field)
            logger.info(f"Saved field intensity data to {filename}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = dict(self.performance_metrics)

        if metrics['rendering_time']:
            metrics['average_rendering_time'] = np.mean(metrics['rendering_time'])
            metrics['max_rendering_time'] = np.max(metrics['rendering_time'])

        metrics['active_sources'] = len(self.active_sources)
        metrics['field_resolution'] = self.renderer.field_generator.grid_resolution

        return metrics

def main():
    """Demonstration of Holographic Sound System"""
    print("HOLOGRAPHIC SOUND - Revolutionary Acoustic Field Generation")
    print("=" * 70)

    # Initialize system
    system = HolographicSoundSystem(sample_rate=44100)

    # Create symphony scene
    print("\nCreating holographic symphony scene...")
    sources = system.create_holographic_scene("symphony")
    print(f"Created {len(sources)} holographic sources")

    # Generate holographic audio
    print("\nGenerating holographic audio...")
    audio = system.generate_holographic_audio(duration=10.0)

    # Save audio
    output_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/holographic_symphony.wav"
    system.save_holographic_audio(audio, output_file)
    print(f"Saved holographic symphony to: {output_file}")

    # Save field data
    system.save_field_data("/home/activeloguser/DMLogn8n/sensory/ultimate/holographic_field")

    # Create vortex concert scene
    print("\nCreating vortex concert scene...")
    system.active_sources.clear()
    vortex_sources = system.create_holographic_scene("vortex_concert")

    # Generate vortex audio
    print("Generating vortex field audio...")
    vortex_audio = system.generate_holographic_audio(duration=8.0)

    # Save vortex audio
    vortex_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/holographic_vortex.wav"
    system.save_holographic_audio(vortex_audio, vortex_file)
    print(f"Saved vortex concert to: {vortex_file}")

    # Create resonance chamber scene
    print("\nCreating resonance chamber scene...")
    system.active_sources.clear()
    resonance_sources = system.create_holographic_scene("resonance_chamber")

    # Generate resonance audio
    print("Generating resonance field audio...")
    resonance_audio = system.generate_holographic_audio(duration=12.0)

    # Save resonance audio
    resonance_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/holographic_resonance.wav"
    system.save_holographic_audio(resonance_audio, resonance_file)
    print(f"Saved resonance chamber to: {resonance_file}")

    # Demonstrate real-time rendering
    print(f"\nStarting real-time holographic rendering...")
    system.start_real_time_rendering(chunk_duration=0.5)

    # Collect real-time audio
    real_time_audio = []
    start_time = time.time()
    while time.time() - start_time < 3.0:  # 3 seconds
        chunk = system.get_audio_chunk()
        if chunk is not None:
            real_time_audio.extend(chunk)
        time.sleep(0.01)

    system.stop_real_time_rendering()

    if real_time_audio:
        real_time_audio = np.array(real_time_audio)
        rt_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/holographic_realtime.wav"
        system.save_holographic_audio(real_time_audio, rt_file)
        print(f"Saved real-time holographic audio to: {rt_file}")

    # Get field visualization
    field_slice = system.get_field_visualization('z', 0.5)
    if field_slice is not None:
        print(f"Generated field visualization slice with shape: {field_slice.shape}")

    # Display performance metrics
    metrics = system.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"Fields generated: {metrics['fields_generated']}")
    print(f"Sources rendered: {metrics['sources_rendered']}")
    print(f"Average rendering time: {metrics.get('average_rendering_time', 0):.3f}s")
    print(f"Active sources: {metrics['active_sources']}")
    print(f"Field resolution: {metrics['field_resolution']}")

    print("\nHOLOGRAPHIC SOUND SYNTHESIS COMPLETE!")
    print("This system creates sound as physical phenomena in space,")
    print("allowing for unprecedented control over acoustic fields and wave patterns.")

if __name__ == "__main__":
    main()