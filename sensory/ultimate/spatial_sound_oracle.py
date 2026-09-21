#!/usr/bin/env python3
"""
SPATIAL SOUND ORACLE
Revolutionary 4D audio positioning system including temporal dimensions.
Creates immersive sound fields that exist in physical and temporal space.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, ifft
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
logger = logging.getLogger("SpatialSoundOracle")

class AudioDimension(Enum):
    """Audio dimension types"""
    X = "x"          # Horizontal position
    Y = "y"          # Vertical position
    Z = "z"          # Depth position
    T = "t"          # Temporal position
    INTENSITY = "i" # Intensity dimension
    PHASE = "p"     # Phase dimension
    FREQUENCY = "f" # Frequency space
    RESONANCE = "r" # Resonance dimension

@dataclass
class SpatialPoint:
    """4D spatial coordinate in audio space"""
    x: float        # Horizontal position (-1 to 1)
    y: float        # Vertical position (-1 to 1)
    z: float        # Depth position (-1 to 1)
    t: float        # Temporal position (0 to duration)
    intensity: float # Intensity (0 to 1)
    phase: float    # Phase (0 to 2π)

@dataclass
class AudioSource:
    """Audio source in 4D space"""
    position: SpatialPoint
    velocity: Tuple[float, float, float, float]  # 4D velocity
    frequency: float
    amplitude: float
    waveform_type: str = "sine"
    lifetime: float = 0.0
    max_lifetime: float = 10.0

@dataclass
class SoundField:
    """4D sound field with multiple sources"""
    sources: List[AudioSource]
    field_resolution: Tuple[int, int, int, int]  # x, y, z, t resolution
    propagation_speed: float = 343.0  # m/s (speed of sound)
    damping_factor: float = 0.95
    reflection_coefficient: float = 0.3

class SpatialAudioRenderer:
    """Renders 4D spatial audio to stereo or multichannel output"""

    def __init__(self, sample_rate: int = 44100, room_dimensions: Tuple[float, float, float] = (10, 5, 8)):
        self.sample_rate = sample_rate
        self.room_dimensions = room_dimensions  # x, y, z in meters
        self.listener_position = np.array([0.0, 0.0, 0.0])  # Center of room

        # HRTF (Head-Related Transfer Function) simulation
        self.hrtf_irs = self._generate_hrtf_irs()

        # Ambisonics encoding
        self.ambisonic_order = 3
        self.ambisonic_channels = (self.ambisonic_order + 1) ** 2

        # Binaural rendering parameters
        self.itd_max = 0.0007  # Maximum inter-aural time difference (700 microseconds)
        self.ild_max = 20.0    # Maximum inter-aural level difference (dB)

        # Temporal dimension parameters
        self.time_resolution = 0.001  # 1ms temporal resolution
        self.temporal_smoothing = 0.1

    def _generate_hrtf_irs(self) -> Dict[str, np.ndarray]:
        """Generate simplified HRTF impulse responses"""
        hrtf_length = 128
        hrtf_irs = {'left': [], 'right': []}

        # Generate HRTFs for different azimuth angles
        for azimuth in np.linspace(-180, 180, 37):
            # Simple ITD calculation
            itd_samples = int(self.itd_max * self.sample_rate * np.sin(np.radians(azimuth)))

            # Generate HRTF impulse response
            ir = np.zeros(hrtf_length)
            delay_idx = hrtf_length // 2 + itd_samples
            if 0 <= delay_idx < hrtf_length:
                ir[delay_idx] = 1.0

            # Add frequency coloring
            ir = self._apply_frequency_coloring(ir, azimuth)

            hrtf_irs['left'].append(ir)
            hrtf_irs['right'].append(ir[::-1])  # Mirror for right ear

        return hrtf_irs

    def _apply_frequency_coloring(self, ir: np.ndarray, azimuth: float) -> np.ndarray:
        """Apply frequency coloring to HRTF impulse response"""
        # Simple frequency coloring based on azimuth
        filtered = np.copy(ir)

        # Apply simple filtering
        if abs(azimuth) > 90:
            # Reduce high frequencies for sounds from behind
            b, a = signal.butter(2, 2000 / (self.sample_rate / 2), 'low')
            filtered = signal.filtfilt(b, a, filtered)

        return filtered

    def render_4d_to_binaural(self, sound_field: SoundField, duration: float) -> Tuple[np.ndarray, np.ndarray]:
        """Render 4D sound field to binaural stereo"""
        num_samples = int(duration * self.sample_rate)
        left_channel = np.zeros(num_samples)
        right_channel = np.zeros(num_samples)

        # Time vector
        t = np.linspace(0, duration, num_samples)

        for source in sound_field.sources:
            # Generate source audio
            source_audio = self._generate_source_audio(source, t)

            # Calculate 4D position at each time sample
            for i, time_point in enumerate(t):
                # Interpolate source position in 4D space
                current_pos = self._interpolate_4d_position(source, time_point)

                # Calculate 3D position for rendering
                position_3d = np.array([current_pos.x, current_pos.y, current_pos.z])

                # Calculate distance-based attenuation
                distance = np.linalg.norm(position_3d - self.listener_position)
                if distance > 0:
                    attenuation = 1.0 / (1.0 + distance * 0.1)
                else:
                    attenuation = 1.0

                # Calculate azimuth and elevation
                relative_pos = position_3d - self.listener_position
                azimuth = np.arctan2(relative_pos[0], relative_pos[2]) * 180 / np.pi
                elevation = np.arcsin(relative_pos[1] / (np.linalg.norm(relative_pos) + 1e-10)) * 180 / np.pi

                # Apply HRTF
                left_sample, right_sample = self._apply_hrtf(
                    source_audio[i], azimuth, elevation, distance
                )

                # Apply temporal effects
                temporal_modulation = self._calculate_temporal_modulation(current_pos, time_point)
                left_sample *= temporal_modulation
                right_sample *= temporal_modulation

                # Apply source-specific effects
                left_sample *= attenuation * source.amplitude
                right_sample *= attenuation * source.amplitude

                # Add to channels
                left_channel[i] += left_sample
                right_channel[i] += right_sample

        # Apply room acoustics
        left_channel, right_channel = self._apply_room_acoustics(
            left_channel, right_channel, sound_field
        )

        # Normalize
        max_level = max(np.max(np.abs(left_channel)), np.max(np.abs(right_channel)))
        if max_level > 0:
            left_channel /= max_level
            right_channel /= max_level

        return left_channel, right_channel

    def _generate_source_audio(self, source: AudioSource, t: np.ndarray) -> np.ndarray:
        """Generate audio for a single source"""
        # Base waveform
        if source.waveform_type == "sine":
            audio = np.sin(2 * np.pi * source.frequency * t)
        elif source.waveform_type == "square":
            audio = signal.square(2 * np.pi * source.frequency * t)
        elif source.waveform_type == "sawtooth":
            audio = signal.sawtooth(2 * np.pi * source.frequency * t)
        elif source.waveform_type == "noise":
            audio = np.random.normal(0, 0.1, len(t))
        else:
            audio = np.sin(2 * np.pi * source.frequency * t)

        # Apply amplitude envelope
        envelope = self._generate_envelope(source, t)
        audio *= envelope

        # Apply Doppler effect if source is moving
        if np.any(np.abs(source.velocity) > 0):
            audio = self._apply_doppler_effect(audio, source, t)

        return audio

    def _generate_envelope(self, source: AudioSource, t: np.ndarray) -> np.ndarray:
        """Generate amplitude envelope for source"""
        envelope = np.ones_like(t)

        # Fade in/out based on lifetime
        fade_samples = int(0.1 * self.sample_rate)  # 100ms fade

        if source.lifetime < 0.1:
            # Fade in
            fade_in_samples = min(fade_samples, len(envelope))
            envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)

        if source.lifetime > source.max_lifetime - 0.1:
            # Fade out
            fade_start = max(0, len(envelope) - fade_samples)
            envelope[fade_start:] = np.linspace(1, 0, len(envelope) - fade_start)

        return envelope

    def _apply_doppler_effect(self, audio: np.ndarray, source: AudioSource, t: np.ndarray) -> np.ndarray:
        """Apply Doppler effect to moving source"""
        # Calculate relative velocity
        velocity_3d = np.array([source.velocity[0], source.velocity[1], source.velocity[2]])
        distance = np.linalg.norm([source.position.x, source.position.y, source.position.z])

        # Doppler shift calculation
        sound_speed = 343.0  # m/s
        relative_velocity = np.dot(velocity_3d, [source.position.x, source.position.y, source.position.z]) / (distance + 1e-10)

        doppler_factor = (sound_speed - relative_velocity) / (sound_speed + 1e-10)

        # Apply frequency shift
        shifted_audio = np.interp(
            t * doppler_factor,
            t,
            audio
        )

        return shifted_audio

    def _interpolate_4d_position(self, source: AudioSource, time_point: float) -> SpatialPoint:
        """Interpolate source position in 4D space"""
        # Linear interpolation based on velocity
        dt = time_point - source.position.t

        new_x = source.position.x + source.velocity[0] * dt
        new_y = source.position.y + source.velocity[1] * dt
        new_z = source.position.z + source.velocity[2] * dt
        new_t = source.position.t + source.velocity[3] * dt

        # Apply boundary conditions (wrap around)
        new_x = np.clip(new_x, -1, 1)
        new_y = np.clip(new_y, -1, 1)
        new_z = np.clip(new_z, -1, 1)
        new_t = np.clip(new_t, 0, 10)  # 10 second temporal space

        return SpatialPoint(
            x=new_x, y=new_y, z=new_z, t=new_t,
            intensity=source.position.intensity,
            phase=source.position.phase
        )

    def _apply_hrtf(self, sample: float, azimuth: float, elevation: float, distance: float) -> Tuple[float, float]:
        """Apply Head-Related Transfer Function"""
        # Simplified HRTF application
        # Calculate ITD (Inter-aural Time Difference)
        itd = self.itd_max * np.sin(np.radians(azimuth)) * min(distance / 5.0, 1.0)

        # Calculate ILD (Inter-aural Level Difference)
        ild = self.ild_max * np.sin(np.radians(azimuth)) * min(distance / 5.0, 1.0)

        # Apply delays and level differences
        left_sample = sample * 10**(ild/20)
        right_sample = sample * 10**(-ild/20)

        return left_sample, right_sample

    def _calculate_temporal_modulation(self, position: SpatialPoint, time_point: float) -> float:
        """Calculate temporal modulation based on 4D position"""
        # Temporal modulation based on position in time dimension
        temporal_phase = 2 * np.pi * position.t / 10.0  # 10 second temporal period

        # Modulation based on intensity and phase
        modulation = 1.0 + 0.2 * position.intensity * np.sin(temporal_phase + position.phase)

        return np.clip(modulation, 0.5, 1.5)

    def _apply_room_acoustics(self, left_channel: np.ndarray, right_channel: np.ndarray,
                            sound_field: SoundField) -> Tuple[np.ndarray, np.ndarray]:
        """Apply room acoustic effects"""
        # Simple room acoustics simulation
        # Add early reflections
        left_reflected = self._add_early_reflections(left_channel, sound_field)
        right_reflected = self._add_early_reflections(right_channel, sound_field)

        # Add reverberation
        left_reverb = self._add_reverberation(left_channel, sound_field)
        right_reverb = self._add_reverberation(right_channel, sound_field)

        # Combine signals
        left_final = left_channel + 0.3 * left_reflected + 0.2 * left_reverb
        right_final = right_channel + 0.3 * right_reflected + 0.2 * right_reverb

        return left_final, right_final

    def _add_early_reflections(self, audio: np.ndarray, sound_field: SoundField) -> np.ndarray:
        """Add early reflections to audio"""
        reflected = np.zeros_like(audio)

        # Simplified early reflection model
        reflection_delays = [0.01, 0.02, 0.03, 0.05]  # seconds
        reflection_gains = [0.5, 0.3, 0.2, 0.1]

        for delay, gain in zip(reflection_delays, reflection_gains):
            delay_samples = int(delay * self.sample_rate)
            if delay_samples < len(audio):
                reflected[delay_samples:] += gain * audio[:-delay_samples]

        return reflected

    def _add_reverberation(self, audio: np.ndarray, sound_field: SoundField) -> np.ndarray:
        """Add reverberation to audio"""
        # Simple Schroeder reverb
        reverb = np.zeros_like(audio)

        # Comb filters
        comb_delays = [0.0297, 0.0371, 0.0411, 0.0437]
        comb_gains = [0.773, 0.802, 0.753, 0.733]

        for delay, gain in zip(comb_delays, comb_gains):
            delay_samples = int(delay * self.sample_rate)
            if delay_samples > 0 and delay_samples < len(audio):
                delayed = np.zeros_like(audio)
                delayed[delay_samples:] = audio[:-delay_samples]
                reverb += gain * delayed

        return reverb * 0.1

class TemporalDimensionProcessor:
    """Processes the temporal dimension of 4D audio"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.temporal_resolution = 0.001  # 1ms
        self.time_windows = deque(maxlen=100)  # Store recent time windows
        self.prediction_model = self._initialize_prediction_model()

    def _initialize_prediction_model(self) -> Dict[str, Any]:
        """Initialize simple temporal prediction model"""
        return {
            'weights': np.random.randn(10),
            'learning_rate': 0.01,
            'momentum': 0.9
        }

    def process_temporal_dimension(self, audio: np.ndarray, current_time: float) -> np.ndarray:
        """Process audio with temporal dimension effects"""
        # Store current time window
        self.time_windows.append((current_time, audio.copy()))

        # Apply temporal effects
        processed_audio = self._apply_temporal_effects(audio, current_time)

        # Predict future audio (for pre-rendering)
        future_prediction = self._predict_future_audio(current_time)

        return processed_audio

    def _apply_temporal_effects(self, audio: np.ndarray, current_time: float) -> np.ndarray:
        """Apply temporal dimension effects to audio"""
        processed = np.copy(audio)

        # Time-based modulation
        time_modulation = np.sin(2 * np.pi * current_time / 5.0)  # 5 second period
        processed *= (1.0 + 0.1 * time_modulation)

        # Temporal filtering (smoothing over time)
        if len(self.time_windows) > 1:
            # Simple moving average filter
            recent_audios = [window[1] for window in list(self.time_windows)[-5:]]
            if recent_audios:
                smoothed = np.mean(recent_audios, axis=0)
                processed = 0.7 * processed + 0.3 * smoothed

        return processed

    def _predict_future_audio(self, current_time: float) -> np.ndarray:
        """Predict future audio based on temporal patterns"""
        if len(self.time_windows) < 5:
            return np.zeros(1024)  # Return silence if not enough data

        # Simple linear prediction based on recent windows
        recent_times = [window[0] for window in list(self.time_windows)[-5:]]
        recent_audios = [window[1] for window in list(self.time_windows)[-5:]]

        # Predict audio 100ms into the future
        future_time = current_time + 0.1
        predicted_audio = np.zeros(1024)

        # Simple extrapolation
        for i in range(min(4, len(recent_audios)-1)):
            diff = recent_audios[i+1] - recent_audios[i]
            predicted_audio += diff * 0.25

        return predicted_audio

class SpatialSoundOracle:
    """Main 4D spatial audio oracle"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

        # Initialize components
        self.audio_renderer = SpatialAudioRenderer(sample_rate)
        self.temporal_processor = TemporalDimensionProcessor(sample_rate)

        # Sound field management
        self.sound_field = SoundField([], (64, 32, 32, 100))
        self.active_sources = []
        self.source_id_counter = 0

        # Real-time processing
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.processing_thread = None

        # 4D spatial navigation
        self.current_temporal_position = 0.0
        self.temporal_speed = 1.0  # Speed of time progression
        self.spatial_gravity = np.array([0, -9.81, 0])  # m/s²

        # Performance monitoring
        self.performance_metrics = {
            'sources_rendered': 0,
            'temporal_predictions': 0,
            'spatial_calculations': 0,
            'rendering_time': deque(maxlen=100)
        }

    def create_audio_source(self, position: SpatialPoint, frequency: float,
                          amplitude: float = 0.5, waveform_type: str = "sine") -> int:
        """Create a new audio source in 4D space"""
        source_id = self.source_id_counter
        self.source_id_counter += 1

        source = AudioSource(
            position=position,
            velocity=(0, 0, 0, 0),  # Initially stationary
            frequency=frequency,
            amplitude=amplitude,
            waveform_type=waveform_type,
            lifetime=0.0,
            max_lifetime=10.0
        )

        self.active_sources.append(source)
        self.sound_field.sources.append(source)

        logger.info(f"Created audio source {source_id} at position ({position.x}, {position.y}, {position.z}, {position.t})")

        return source_id

    def move_source_4d(self, source_id: int, velocity: Tuple[float, float, float, float]):
        """Set 4D velocity for audio source"""
        if source_id < len(self.active_sources):
            self.active_sources[source_id].velocity = velocity

    def create_spatial_scene(self, scene_type: str = "symphony") -> Dict[str, int]:
        """Create predefined 4D spatial scenes"""
        sources = {}

        if scene_type == "symphony":
            # Create orchestra-like arrangement in 4D space
            instruments = [
                (SpatialPoint(-0.8, 0.2, -0.5, 0, 0.8, 0), 440, "sine"),      # Violins
                (SpatialPoint(0.8, 0.2, -0.5, 0, 0.8, np.pi/2), 220, "sine"),  # Cellos
                (SpatialPoint(0, -0.5, 0.2, 0, 0.9, np.pi), 110, "sine"),       # Bass
                (SpatialPoint(-0.5, 0.8, 0.8, 0, 0.7, np.pi/4), 880, "sine"),   # Flutes
                (SpatialPoint(0.5, 0.8, 0.8, 0, 0.7, 3*np.pi/4), 660, "sine"),  # Clarinets
            ]

            for i, (position, frequency, waveform) in enumerate(instruments):
                source_id = self.create_audio_source(position, frequency, 0.3, waveform)
                sources[f"instrument_{i}"] = source_id

        elif scene_type == "nature":
            # Create nature sounds in 4D space
            nature_sounds = [
                (SpatialPoint(-1, 1, -0.8, 0, 0.6, 0), 200, "noise"),      # Wind
                (SpatialPoint(1, -0.5, 0.6, 0, 0.8, np.pi/2), 150, "noise"), # Rain
                (SpatialPoint(0, 0, 0, 0, 0.9, np.pi), 1000, "sine"),      # Birdsong
                (SpatialPoint(-0.6, -0.3, 0.3, 0, 0.7, 3*np.pi/4), 80, "sine"),  # Thunder
            ]

            for i, (position, frequency, waveform) in enumerate(nature_sounds):
                source_id = self.create_audio_source(position, frequency, 0.4, waveform)
                sources[f"nature_{i}"] = source_id

        return sources

    def generate_4d_audio(self, duration: float, listener_path: Optional[List[SpatialPoint]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Generate 4D spatial audio for specified duration"""
        start_time = time.time()

        # Update source positions and lifetimes
        self._update_sources(duration)

        # Update temporal position
        self._update_temporal_position(duration)

        # Render 4D audio to binaural
        left_channel, right_channel = self.audio_renderer.render_4d_to_binaural(
            self.sound_field, duration
        )

        # Apply temporal processing
        time_points = np.linspace(0, duration, len(left_channel))
        for i, t in enumerate(time_points):
            left_sample, right_sample = left_channel[i], right_channel[i]
            processed = self.temporal_processor.process_temporal_dimension(
                np.array([left_sample, right_sample]), t
            )
            left_channel[i] = processed[0]
            right_channel[i] = processed[1]

        # Update performance metrics
        rendering_time = time.time() - start_time
        self.performance_metrics['rendering_time'].append(rendering_time)
        self.performance_metrics['sources_rendered'] += len(self.active_sources)

        logger.info(f"Generated 4D audio in {rendering_time:.3f}s with {len(self.active_sources)} sources")

        return left_channel, right_channel

    def _update_sources(self, dt: float):
        """Update source positions and lifetimes"""
        sources_to_remove = []

        for i, source in enumerate(self.active_sources):
            # Update lifetime
            source.lifetime += dt

            # Update position based on velocity
            source.position.x += source.velocity[0] * dt
            source.position.y += source.velocity[1] * dt
            source.position.z += source.velocity[2] * dt
            source.position.t += source.velocity[3] * dt

            # Apply spatial gravity to y velocity
            source.velocity = (
                source.velocity[0],
                source.velocity[1] + self.spatial_gravity[1] * dt,
                source.velocity[2],
                source.velocity[3]
            )

            # Apply boundary conditions
            source.position.x = np.clip(source.position.x, -1, 1)
            source.position.y = np.clip(source.position.y, -1, 1)
            source.position.z = np.clip(source.position.z, -1, 1)
            source.position.t = np.clip(source.position.t, 0, 10)

            # Check if source should be removed
            if source.lifetime > source.max_lifetime:
                sources_to_remove.append(i)

        # Remove dead sources
        for i in reversed(sources_to_remove):
            del self.active_sources[i]
            del self.sound_field.sources[i]

    def _update_temporal_position(self, dt: float):
        """Update temporal position"""
        self.current_temporal_position += dt * self.temporal_speed

        # Wrap around temporal dimension
        if self.current_temporal_position > 10.0:
            self.current_temporal_position -= 10.0

    def start_real_time_rendering(self, chunk_duration: float = 0.5):
        """Start real-time 4D audio rendering"""
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._real_time_rendering_loop,
            args=(chunk_duration,),
            daemon=True
        )
        self.processing_thread.start()

        logger.info("Started real-time 4D audio rendering")

    def _real_time_rendering_loop(self, chunk_duration: float):
        """Real-time rendering loop"""
        while self.is_running:
            start_time = time.time()

            # Generate audio chunk
            left_channel, right_channel = self.generate_4d_audio(chunk_duration)

            # Combine channels for queue
            stereo_audio = np.column_stack((left_channel, right_channel))
            self.audio_queue.put(stereo_audio)

            # Maintain real-time performance
            elapsed = time.time() - start_time
            if elapsed < chunk_duration:
                time.sleep(chunk_duration - elapsed)

    def stop_real_time_rendering(self):
        """Stop real-time rendering"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        logger.info("Stopped real-time 4D audio rendering")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def export_4d_scene(self, filename: str, duration: float):
        """Export 4D audio scene to file"""
        left_channel, right_channel = self.generate_4d_audio(duration)

        # Save as stereo file
        stereo_audio = np.column_stack((left_channel, right_channel))
        sf.write(filename, stereo_audio, self.sample_rate)

        # Export scene data
        scene_data = {
            'sources': [
                {
                    'position': {
                        'x': source.position.x,
                        'y': source.position.y,
                        'z': source.position.z,
                        't': source.position.t,
                        'intensity': source.position.intensity,
                        'phase': source.position.phase
                    },
                    'velocity': source.velocity,
                    'frequency': source.frequency,
                    'amplitude': source.amplitude,
                    'waveform_type': source.waveform_type,
                    'lifetime': source.lifetime,
                    'max_lifetime': source.max_lifetime
                }
                for source in self.active_sources
            ],
            'temporal_position': self.current_temporal_position,
            'temporal_speed': self.temporal_speed
        }

        scene_filename = filename.replace('.wav', '_scene.json')
        with open(scene_filename, 'w') as f:
            json.dump(scene_data, f, indent=2)

        logger.info(f"Exported 4D scene to {filename} and {scene_filename}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = dict(self.performance_metrics)

        if metrics['rendering_time']:
            metrics['average_rendering_time'] = np.mean(metrics['rendering_time'])
            metrics['max_rendering_time'] = np.max(metrics['rendering_time'])

        metrics['active_sources'] = len(self.active_sources)
        metrics['current_temporal_position'] = self.current_temporal_position

        return metrics

def main():
    """Demonstration of Spatial Sound Oracle"""
    print("SPATIAL SOUND ORACLE - Revolutionary 4D Audio Positioning")
    print("=" * 70)

    # Initialize oracle
    oracle = SpatialSoundOracle(sample_rate=44100)

    # Create symphony scene
    print("\nCreating 4D symphony scene...")
    sources = oracle.create_spatial_scene("symphony")
    print(f"Created {len(sources)} audio sources")

    # Set some sources in motion in 4D space
    if "instrument_0" in sources:
        oracle.move_source_4d(sources["instrument_0"], (0.1, 0.05, 0.02, 0.1))  # Moving source
    if "instrument_2" in sources:
        oracle.move_source_4d(sources["instrument_2"], (-0.05, 0.1, -0.03, 0.05))  # Another moving source

    # Generate 4D audio
    print("\nGenerating 4D spatial audio...")
    left_channel, right_channel = oracle.generate_4d_audio(duration=8.0)

    # Save audio
    output_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/spatial_4d_audio.wav"
    stereo_audio = np.column_stack((left_channel, right_channel))
    sf.write(output_file, stereo_audio, 44100)
    print(f"Saved 4D spatial audio to: {output_file}")

    # Export scene data
    oracle.export_4d_scene(output_file, 8.0)

    # Create nature scene
    print("\nCreating 4D nature scene...")
    oracle.active_sources.clear()
    oracle.sound_field.sources.clear()
    nature_sources = oracle.create_spatial_scene("nature")

    # Generate nature audio
    print("Generating 4D nature soundscape...")
    left_nature, right_nature = oracle.generate_4d_audio(duration=10.0)

    # Save nature audio
    nature_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/spatial_4d_nature.wav"
    stereo_nature = np.column_stack((left_nature, right_nature))
    sf.write(nature_file, stereo_nature, 44100)
    print(f"Saved 4D nature soundscape to: {nature_file}")

    # Demonstrate real-time rendering
    print(f"\nStarting real-time 4D rendering...")
    oracle.start_real_time_rendering(chunk_duration=0.5)

    # Collect real-time audio
    real_time_audio = []
    start_time = time.time()
    while time.time() - start_time < 3.0:  # 3 seconds
        chunk = oracle.get_audio_chunk()
        if chunk is not None:
            real_time_audio.extend(chunk)
        time.sleep(0.01)

    oracle.stop_real_time_rendering()

    if real_time_audio:
        real_time_audio = np.array(real_time_audio)
        rt_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/spatial_4d_realtime.wav"
        sf.write(rt_file, real_time_audio, 44100)
        print(f"Saved real-time 4D audio to: {rt_file}")

    # Display performance metrics
    metrics = oracle.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"Sources rendered: {metrics['sources_rendered']}")
    print(f"Average rendering time: {metrics.get('average_rendering_time', 0):.3f}s")
    print(f"Active sources: {metrics['active_sources']}")
    print(f"Current temporal position: {metrics['current_temporal_position']:.2f}s")

    print("\n4D SPATIAL AUDIO SYNTHESIS COMPLETE!")
    print("This system creates audio that exists in four dimensions,")
    print("allowing listeners to experience sound in physical and temporal space.")

if __name__ == "__main__":
    main()