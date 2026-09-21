#!/usr/bin/env python3
"""
DMLogn8n Spatial Audio System - 3D Spatial Audio with Realistic Acoustics
Advanced spatial audio system that provides immersive 3D sound positioning and realistic acoustics
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

# Audio Libraries
try:
    import pyaudio
    import scipy.io.wavfile as wavfile
    from scipy import signal
    import soundfile as sf
except ImportError:
    pyaudio = None
    wavfile = None
    signal = None
    sf = None

try:
    import librosa
    import librosa.display
except ImportError:
    librosa = None

# DSP and Audio Processing
try:
    import numba
    from numba import jit, cuda
except ImportError:
    numba = None
    jit = lambda x: x  # Fallback decorator

# Real-time audio processing
try:
    import threading
    import queue
    from collections import deque
except ImportError:
    threading = None
    queue = None
    deque = None


class AudioFormat(Enum):
    """Supported audio formats"""
    PCM_16 = "pcm16"
    PCM_24 = "pcm24"
    PCM_32 = "pcm32"
    FLOAT_32 = "float32"
    FLOAT_64 = "float64"


class HRTFModel(Enum):
    """Head-Related Transfer Function models"""
    MIT = "mit"
    CIPIC = "cipic"
    KEMAR = "kemar"
    LISTEN = "listen"
    CUSTOM = "custom"


class AcousticModel(Enum):
    """Acoustic simulation models"""
    IMAGE_SOURCE = "image_source"
    RAY_TRACING = "ray_tracing"
    WAVE_BASED = "wave_based"
    HYBRID = "hybrid"


class ReverbType(Enum):
    """Types of reverb"""
    HALL = "hall"
    ROOM = "room"
    CHURCH = "church"
    CAVERN = "cavern"
    STUDIO = "studio"
    OUTDOOR = "outdoor"


@dataclass
class Vector3:
    """3D Vector for audio positioning"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Vector3':
        return cls(x=arr[0], y=arr[1], z=arr[2])

    def magnitude(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3()

    def distance_to(self, other: 'Vector3') -> float:
        return (self - other).magnitude()

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)


@dataclass
class AudioListener:
    """Audio listener (player's ears)"""
    position: Vector3
    orientation: Vector3  # Forward direction
    up_vector: Vector3 = Vector3(0, 1, 0)
    velocity: Vector3 = Vector3()
    head_radius: float = 0.0875  # Average head radius in meters


@dataclass
class AudioSource:
    """3D audio source"""
    source_id: str
    position: Vector3
    velocity: Vector3 = Vector3()
    volume: float = 1.0
    pitch: float = 1.0
    is_looping: bool = False
    is_playing: bool = False
    audio_data: Optional[np.ndarray] = None
    sample_rate: int = 44100
    current_position: int = 0
    max_distance: float = 100.0
    reference_distance: float = 1.0
    rolloff_factor: float = 1.0
    cone_inner_angle: float = 360.0
    cone_outer_angle: float = 360.0
    cone_outer_gain: float = 0.0
    directivity: float = 1.0


@dataclass
class AcousticMaterial:
    """Acoustic material properties"""
    name: str
    absorption_low: float  # 125 Hz
    absorption_mid: float  # 1 kHz
    absorption_high: float  # 4 kHz
    scattering: float = 0.0
    transmission: float = 0.0


@dataclass
class RoomGeometry:
    """Room geometry for acoustic simulation"""
    dimensions: Vector3  # Width, Height, Depth
    materials: List[AcousticMaterial]  # 6 materials for 6 walls
    position: Vector3 = Vector3()


class HRIRDatabase:
    """Head-Related Impulse Response database"""

    def __init__(self, model: HRTFModel = HRTFModel.MIT):
        self.model = model
        self.hrirs: Dict[Tuple[float, float], np.ndarray] = {}
        self.sample_rate = 44100
        self.azimuths = []
        self.elevations = []

        # Load HRTF data
        self._load_hrtf_data()

    def _load_hrtf_data(self):
        """Load HRTF impulse responses"""
        # In a real implementation, this would load actual HRTF measurements
        # For now, we'll create synthetic HRIRs
        self.azimuths = np.arange(0, 360, 5)  # 5 degree steps
        self.elevations = np.arange(-45, 46, 15)  # -45 to +45 degrees

        for azimuth in self.azimuths:
            for elevation in self.elevations:
                # Generate synthetic HRIR based on direction
                hrir = self._generate_synthetic_hrir(azimuth, elevation)
                self.hrirs[(azimuth, elevation)] = hrir

    def _generate_synthetic_hrir(self, azimuth: float, elevation: float) -> np.ndarray:
        """Generate synthetic HRIR for testing"""
        duration = 0.002  # 2ms
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)

        # Create simple HRIR with direction-dependent delay
        # Inter-aural time difference (ITD)
        itd = 0.0006 * np.sin(np.radians(azimuth))  # Max 0.6ms ITD

        # Create left and right ear responses
        left_delay = int(-itd * self.sample_rate / 2)
        right_delay = int(itd * self.sample_rate / 2)

        # Simple exponential decay impulse
        impulse = np.exp(-t * 5000) * np.sin(2 * np.pi * 1000 * t)

        # Apply delays
        left_hrir = np.zeros(samples)
        right_hrir = np.zeros(samples)

        if 0 <= left_delay < samples:
            left_hrir[left_delay:] = impulse[:samples-left_delay]
        if 0 <= right_delay < samples:
            right_hrir[right_delay:] = impulse[:samples-right_delay]

        # Stack left and right
        hrir = np.column_stack([left_hrir, right_hrir])

        return hrir

    def get_hrir(self, azimuth: float, elevation: float) -> np.ndarray:
        """Get HRIR for given direction"""
        # Find nearest available azimuth and elevation
        nearest_azimuth = min(self.azimuths, key=lambda x: abs(x - azimuth))
        nearest_elevation = min(self.elevations, key=lambda x: abs(x - elevation))

        # Get HRIR
        hrir = self.hrirs.get((nearest_azimuth, nearest_elevation))

        if hrir is None:
            # Fallback to frontal HRIR
            hrir = self.hrirs.get((0, 0), np.zeros((128, 2)))

        return hrir


class ReverbProcessor:
    """Reverb and acoustic effects processor"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.impulse_responses: Dict[ReverbType, np.ndarray] = {}
        self._load_impulse_responses()

    def _load_impulse_responses(self):
        """Load impulse responses for different reverb types"""
        # Generate synthetic impulse responses
        for reverb_type in ReverbType:
            self.impulse_responses[reverb_type] = self._generate_impulse_response(reverb_type)

    def _generate_impulse_response(self, reverb_type: ReverbType) -> np.ndarray:
        """Generate synthetic impulse response"""
        duration = 2.0  # 2 seconds
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)

        if reverb_type == ReverbType.HALL:
            # Large hall reverb - long decay, early reflections
            decay_time = 2.0
            pre_delay = 0.03
            early_reflections = self._generate_early_reflections(t, pre_delay)
        elif reverb_type == ReverbType.ROOM:
            # Small room reverb - shorter decay
            decay_time = 0.5
            pre_delay = 0.01
            early_reflections = self._generate_early_reflections(t, pre_delay)
        elif reverb_type == ReverbType.CHURCH:
            # Church reverb - very long decay
            decay_time = 4.0
            pre_delay = 0.05
            early_reflections = self._generate_early_reflections(t, pre_delay)
        elif reverb_type == ReverbType.CAVERN:
            # Cavern reverb - very long decay, echoes
            decay_time = 6.0
            pre_delay = 0.1
            early_reflections = self._generate_echoes(t, pre_delay)
        elif reverb_type == ReverbType.STUDIO:
            # Studio reverb - very short decay
            decay_time = 0.2
            pre_delay = 0.005
            early_reflections = self._generate_early_reflections(t, pre_delay)
        else:  # OUTDOOR
            # Outdoor - minimal reverb
            decay_time = 0.1
            pre_delay = 0.0
            early_reflections = np.zeros_like(t)

        # Generate decay
        decay = np.exp(-t * (1.0 / decay_time))

        # Add some randomness for natural sound
        noise = np.random.normal(0, 0.01, len(t))

        # Combine all components
        impulse_response = early_reflections + decay + noise

        # Normalize
        impulse_response = impulse_response / np.max(np.abs(impulse_response))

        return impulse_response

    def _generate_early_reflections(self, t: np.ndarray, pre_delay: float) -> np.ndarray:
        """Generate early reflections"""
        reflections = np.zeros_like(t)
        pre_delay_samples = int(pre_delay * self.sample_rate)

        # Add early reflections at specific delays
        reflection_times = [0.03, 0.05, 0.07, 0.11, 0.13, 0.17]  # seconds
        reflection_gains = [0.7, 0.5, 0.4, 0.3, 0.2, 0.1]

        for delay, gain in zip(reflection_times, reflection_gains):
            delay_samples = int(delay * self.sample_rate)
            if pre_delay_samples + delay_samples < len(reflections):
                reflections[pre_delay_samples + delay_samples] = gain

        return reflections

    def _generate_echoes(self, t: np.ndarray, pre_delay: float) -> np.ndarray:
        """Generate echo effects for cavern/cave sounds"""
        echoes = np.zeros_like(t)
        pre_delay_samples = int(pre_delay * self.sample_rate)

        # Add distinct echoes
        echo_times = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2]  # seconds
        echo_gains = [0.6, 0.4, 0.3, 0.2, 0.15, 0.1]

        for delay, gain in zip(echo_times, echo_gains):
            delay_samples = int(delay * self.sample_rate)
            if pre_delay_samples + delay_samples < len(echoes):
                echoes[pre_delay_samples + delay_samples] = gain

        return echoes

    def apply_reverb(self, audio: np.ndarray, reverb_type: ReverbType,
                     wet_level: float = 0.3, dry_level: float = 0.7) -> np.ndarray:
        """Apply reverb to audio"""
        if reverb_type not in self.impulse_responses:
            return audio

        impulse_response = self.impulse_responses[reverb_type]

        # Convolve audio with impulse response
        if len(audio.shape) == 1:
            # Mono audio
            wet = signal.convolve(audio, impulse_response, mode='same')
        else:
            # Stereo audio
            wet = np.zeros_like(audio)
            for channel in range(audio.shape[1]):
                wet[:, channel] = signal.convolve(audio[:, channel], impulse_response, mode='same')

        # Mix wet and dry signals
        result = wet_level * wet + dry_level * audio

        return result


@jit(nopython=True)
def calculate_distance_attenuation(distance: float, max_distance: float,
                                 reference_distance: float, rolloff_factor: float) -> float:
    """Calculate distance-based volume attenuation"""
    if distance <= reference_distance:
        return 1.0
    elif distance >= max_distance:
        return 0.0
    else:
        # Inverse distance attenuation
        return reference_distance / (reference_distance + rolloff_factor * (distance - reference_distance))


@jit(nopython=True)
def calculate_doppler_shift(source_pos: np.ndarray, listener_pos: np.ndarray,
                           source_vel: np.ndarray, listener_vel: np.ndarray,
                           speed_of_sound: float = 343.0) -> float:
    """Calculate Doppler shift frequency ratio"""
    # Vector from source to listener
    relative_pos = listener_pos - source_pos
    distance = np.linalg.norm(relative_pos)

    if distance < 0.001:  # Avoid division by zero
        return 1.0

    # Unit vector from source to listener
    relative_pos_normalized = relative_pos / distance

    # Relative velocity
    relative_vel = listener_vel - source_vel

    # Radial velocity component
    radial_vel = np.dot(relative_vel, relative_pos_normalized)

    # Doppler shift formula
    doppler_factor = (speed_of_sound - radial_vel) / speed_of_sound

    # Clamp to reasonable range
    return np.clip(doppler_factor, 0.5, 2.0)


class SpatialAudioEngine:
    """Main spatial audio engine"""

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 512,
                 output_channels: int = 2):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.output_channels = output_channels

        # Core components
        self.listener = AudioListener(Vector3(0, 0, 0), Vector3(0, 0, -1))
        self.sources: Dict[str, AudioSource] = {}
        self.hrir_database = HRIRDatabase()
        self.reverb_processor = ReverbProcessor(sample_rate)

        # Audio output
        self.audio_stream = None
        self.output_queue = queue.Queue() if queue else None
        self.is_streaming = False

        # Room acoustics
        self.current_room = None
        self.reverb_type = ReverbType.ROOM
        self.reverb_wet_level = 0.3

        # Performance
        self.max_concurrent_sources = 32
        self.processing_time = 0.0

        self.logger = logging.getLogger(__name__)

    def set_listener(self, position: Vector3, orientation: Vector3, up_vector: Vector3 = None):
        """Set listener position and orientation"""
        self.listener.position = position
        self.listener.orientation = orientation
        if up_vector:
            self.listener.up_vector = up_vector

    def add_source(self, source: AudioSource):
        """Add audio source"""
        self.sources[source.source_id] = source
        self.logger.info(f"Added audio source: {source.source_id}")

    def remove_source(self, source_id: str):
        """Remove audio source"""
        if source_id in self.sources:
            del self.sources[source_id]
            self.logger.info(f"Removed audio source: {source_id}")

    def load_audio_file(self, file_path: str) -> Optional[np.ndarray]:
        """Load audio file"""
        try:
            if librosa:
                audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=False)
                return audio.T  # Transpose to (samples, channels)
            elif sf:
                audio, sr = sf.read(file_path, dtype='float32')
                if sr != self.sample_rate:
                    # Resample if needed
                    audio = signal.resample(audio, int(len(audio) * self.sample_rate / sr))
                return audio
            elif wavfile:
                sr, audio = wavfile.read(file_path)
                if sr != self.sample_rate:
                    audio = signal.resample(audio, int(len(audio) * self.sample_rate / sr))
                return audio.astype(np.float32) / 32768.0
            else:
                self.logger.error("No audio loading library available")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load audio file {file_path}: {e}")
            return None

    def generate_test_tone(self, frequency: float = 440.0, duration: float = 1.0) -> np.ndarray:
        """Generate test tone"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        tone = np.sin(2 * np.pi * frequency * t) * 0.3
        return tone

    def process_audio_buffer(self) -> np.ndarray:
        """Process one buffer of spatial audio"""
        start_time = time.time()

        # Initialize output buffer
        output = np.zeros((self.buffer_size, self.output_channels))

        # Process each source
        for source in list(self.sources.values())[:self.max_concurrent_sources]:
            if source.is_playing and source.audio_data is not None:
                # Get source audio segment
                source_audio = self._get_source_audio_segment(source)

                if source_audio is not None and len(source_audio) > 0:
                    # Apply spatial processing
                    processed_audio = self._process_source_audio(source, source_audio)

                    # Mix into output
                    output += processed_audio

        # Apply room reverb if needed
        if self.current_room and self.reverb_wet_level > 0:
            output = self.reverb_processor.apply_reverb(
                output, self.reverb_type, self.reverb_wet_level, 1.0 - self.reverb_wet_level
            )

        # Apply limiting to prevent clipping
        output = np.tanh(output) * 0.95

        self.processing_time = time.time() - start_time

        return output

    def _get_source_audio_segment(self, source: AudioSource) -> Optional[np.ndarray]:
        """Get audio segment from source"""
        if source.audio_data is None:
            return None

        start_sample = source.current_position
        end_sample = min(start_sample + self.buffer_size, len(source.audio_data))

        if start_sample >= len(source.audio_data):
            if source.is_looping:
                source.current_position = 0
                return self._get_source_audio_segment(source)
            else:
                source.is_playing = False
                return None

        audio_segment = source.audio_data[start_sample:end_sample]

        # Handle looping
        if source.is_looping and len(audio_segment) < self.buffer_size:
            remaining_samples = self.buffer_size - len(audio_segment)
            looped_segment = source.audio_data[:remaining_samples]
            audio_segment = np.concatenate([audio_segment, looped_segment])

        source.current_position += self.buffer_size

        return audio_segment

    def _process_source_audio(self, source: AudioSource, audio: np.ndarray) -> np.ndarray:
        """Apply spatial audio processing to source"""
        # Calculate relative position
        relative_pos = source.position - self.listener.position
        distance = relative_pos.magnitude()

        # Calculate direction to source
        if distance > 0.001:
            direction = relative_pos.normalize()
        else:
            direction = Vector3(0, 0, -1)

        # Convert to spherical coordinates for HRTF lookup
        azimuth, elevation = self._cartesian_to_spherical(direction)

        # Get HRTF
        hrir = self.hrir_database.get_hrir(azimuth, elevation)

        # Apply distance attenuation
        attenuation = calculate_distance_attenuation(
            distance, source.max_distance, source.reference_distance, source.rolloff_factor
        )

        # Apply Doppler shift
        doppler_factor = calculate_doppler_shift(
            source.position.to_array(), self.listener.position.to_array(),
            source.velocity.to_array(), self.listener.velocity.to_array()
        )

        # Apply effects
        processed_audio = self._apply_spatial_effects(
            audio, hrir, attenuation, doppler_factor, source
        )

        return processed_audio

    def _cartesian_to_spherical(self, direction: Vector3) -> Tuple[float, float]:
        """Convert Cartesian direction to spherical coordinates"""
        # Calculate azimuth (horizontal angle)
        azimuth = np.degrees(np.arctan2(direction.x, direction.z))
        if azimuth < 0:
            azimuth += 360

        # Calculate elevation (vertical angle)
        horizontal_dist = np.sqrt(direction.x**2 + direction.z**2)
        elevation = np.degrees(np.arctan2(direction.y, horizontal_dist))

        return azimuth, elevation

    def _apply_spatial_effects(self, audio: np.ndarray, hrir: np.ndarray,
                              attenuation: float, doppler_factor: float,
                              source: AudioSource) -> np.ndarray:
        """Apply spatial audio effects"""
        # Apply pitch shift (Doppler effect)
        if abs(doppler_factor - 1.0) > 0.01:
            audio = self._pitch_shift(audio, doppler_factor)

        # Apply volume
        audio = audio * attenuation * source.volume

        # Apply HRIR convolution for binaural audio
        if len(audio.shape) == 1:
            # Mono source - convolve with HRIR
            if len(hrir.shape) == 2 and hrir.shape[1] == 2:
                # Convolve with left and right ear responses
                left_output = signal.convolve(audio, hrir[:, 0], mode='same')
                right_output = signal.convolve(audio, hrir[:, 1], mode='same')
                processed_audio = np.column_stack([left_output, right_output])
            else:
                # Fallback to mono
                processed_audio = np.column_stack([audio, audio])
        else:
            # Stereo source - apply simple panning based on direction
            processed_audio = audio

        # Apply cone attenuation if applicable
        if source.cone_inner_angle < 360.0:
            processed_audio = self._apply_cone_attenuation(processed_audio, source)

        return processed_audio

    def _pitch_shift(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """Apply pitch shift using resampling"""
        if factor == 1.0:
            return audio

        # Resample audio for pitch shift
        if librosa:
            pitched = librosa.effects.pitch_shift(
                audio.flatten(), self.sample_rate, n_steps=12 * np.log2(factor)
            )
            return pitched.reshape(audio.shape)
        else:
            # Simple linear interpolation fallback
            old_length = len(audio)
            new_length = int(old_length / factor)
            indices = np.linspace(0, old_length - 1, new_length)
            pitched = np.interp(indices, np.arange(old_length), audio)
            return pitched

    def _apply_cone_attenuation(self, audio: np.ndarray, source: AudioSource) -> np.ndarray:
        """Apply cone-based directivity"""
        # Calculate angle between source forward vector and direction to listener
        to_listener = self.listener.position - source.position
        distance = to_listener.magnitude()

        if distance > 0.001:
            # Simple cone attenuation (would use actual source orientation in full implementation)
            # For now, assume source points toward listener
            angle = 0.0  # Would calculate actual angle

            if abs(angle) <= source.cone_inner_angle / 2:
                # Inside inner cone - no attenuation
                cone_gain = 1.0
            elif abs(angle) >= source.cone_outer_angle / 2:
                # Outside outer cone - maximum attenuation
                cone_gain = source.cone_outer_gain
            else:
                # Between cones - interpolate
                inner_rad = np.radians(source.cone_inner_angle / 2)
                outer_rad = np.radians(source.cone_outer_angle / 2)
                angle_rad = np.radians(abs(angle))

                t = (angle_rad - inner_rad) / (outer_rad - inner_rad)
                cone_gain = 1.0 - t * (1.0 - source.cone_outer_gain)

            return audio * cone_gain

        return audio

    async def start_streaming(self):
        """Start audio streaming"""
        if not pyaudio:
            self.logger.error("PyAudio not available")
            return False

        try:
            p = pyaudio.PyAudio()

            # Open audio stream
            self.audio_stream = p.open(
                format=pyaudio.paFloat32,
                channels=self.output_channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.buffer_size,
                stream_callback=self._audio_callback
            )

            self.is_streaming = True
            self.audio_stream.start_stream()
            self.logger.info("Spatial audio streaming started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start audio streaming: {e}")
            return False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        # Process audio buffer
        output_buffer = self.process_audio_buffer()

        # Convert to bytes
        output_bytes = (output_buffer * 32767).astype(np.int16).tobytes()

        return (output_bytes, pyaudio.paContinue)

    async def stop_streaming(self):
        """Stop audio streaming"""
        self.is_streaming = False

        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None

        self.logger.info("Spatial audio streaming stopped")

    def set_room_acoustics(self, room: RoomGeometry, reverb_type: ReverbType,
                          wet_level: float = 0.3):
        """Set room acoustics"""
        self.current_room = room
        self.reverb_type = reverb_type
        self.reverb_wet_level = wet_level
        self.logger.info(f"Set room acoustics: {room.dimensions}")

    def play_source(self, source_id: str):
        """Start playing audio source"""
        if source_id in self.sources:
            source = self.sources[source_id]
            source.is_playing = True
            source.current_position = 0
            self.logger.info(f"Started playing source: {source_id}")

    def stop_source(self, source_id: str):
        """Stop playing audio source"""
        if source_id in self.sources:
            self.sources[source_id].is_playing = False
            self.logger.info(f"Stopped playing source: {source_id}")

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'active_sources': len([s for s in self.sources.values() if s.is_playing]),
            'total_sources': len(self.sources),
            'processing_time_ms': self.processing_time * 1000,
            'sample_rate': self.sample_rate,
            'buffer_size': self.buffer_size,
            'listener_position': asdict(self.listener.position),
            'current_room': asdict(self.current_room.dimensions) if self.current_room else None
        }


class DMLogn8nAudioManager:
    """DMLogn8n-specific audio management"""

    def __init__(self, audio_engine: SpatialAudioEngine):
        self.audio_engine = audio_engine
        self.ambient_sounds: Dict[str, str] = {}
        self.character_voices: Dict[str, AudioSource] = {}
        self.story_sounds: Dict[str, AudioSource] = {}

    async def initialize_tavern_audio(self):
        """Initialize tavern-specific audio"""
        # Create room acoustics for tavern
        tavern_room = RoomGeometry(
            dimensions=Vector3(10, 4, 8),  # 10x4x8 meters
            materials=[
                AcousticMaterial("Wooden Floor", 0.1, 0.15, 0.2, 0.1, 0.0),   # Floor
                AcousticMaterial("Wooden Ceiling", 0.15, 0.2, 0.25, 0.1, 0.0),  # Ceiling
                AcousticMaterial("Stone Wall", 0.3, 0.4, 0.5, 0.2, 0.0),       # Front wall
                AcousticMaterial("Stone Wall", 0.3, 0.4, 0.5, 0.2, 0.0),       # Back wall
                AcousticMaterial("Wooden Wall", 0.2, 0.3, 0.35, 0.15, 0.0),     # Left wall
                AcousticMaterial("Wooden Wall", 0.2, 0.3, 0.35, 0.15, 0.0)      # Right wall
            ]
        )

        self.audio_engine.set_room_acoustics(tavern_room, ReverbType.ROOM, wet_level=0.4)

        # Create ambient sounds
        await self._create_ambient_sounds()

        # Create character voices
        await self._create_character_voices()

    async def _create_ambient_sounds(self):
        """Create ambient tavern sounds"""
        # Fireplace crackling
        fireplace_source = AudioSource(
            source_id="fireplace",
            position=Vector3(0, 1, 3),  # Near fireplace
            volume=0.3,
            is_looping=True,
            max_distance=15.0
        )

        # Generate fireplace sound (synthetic)
        fireplace_audio = self._generate_fireplace_sound()
        fireplace_source.audio_data = fireplace_audio

        self.audio_engine.add_source(fireplace_source)

        # Background chatter
        chatter_source = AudioSource(
            source_id="chatter",
            position=Vector3(0, 1.5, 0),  # Center of tavern
            volume=0.2,
            is_looping=True,
            max_distance=20.0
        )

        # Generate chatter sound
        chatter_audio = self._generate_chatter_sound()
        chatter_source.audio_data = chatter_audio

        self.audio_engine.add_source(chatter_source)

    def _generate_fireplace_sound(self) -> np.ndarray:
        """Generate synthetic fireplace crackling sound"""
        duration = 10.0  # 10 seconds
        samples = int(duration * self.audio_engine.sample_rate)
        t = np.linspace(0, duration, samples)

        # Combine multiple noise sources for crackling effect
        noise1 = np.random.normal(0, 0.1, samples)
        noise2 = np.random.normal(0, 0.05, samples)

        # Apply low-pass filtering
        from scipy.signal import butter, filtfilt
        b, a = butter(4, 0.1, 'low')
        filtered_noise = filtfilt(b, a, noise1 + noise2)

        # Add some crackling impulses
        crackle_times = np.random.uniform(0, duration, 50)
        crackle_audio = np.zeros(samples)

        for crackle_time in crackle_times:
            crackle_sample = int(crackle_time * self.audio_engine.sample_rate)
            if crackle_sample < samples:
                # Create short crackle burst
                burst_length = int(0.05 * self.audio_engine.sample_rate)
                burst = np.random.normal(0, 0.3, burst_length) * np.exp(-np.linspace(0, 10, burst_length))
                end_sample = min(crackle_sample + burst_length, samples)
                crackle_audio[crackle_sample:end_sample] = burst[:end_sample - crackle_sample]

        # Combine all components
        fireplace_sound = filtered_noise + crackle_audio

        return fireplace_sound

    def _generate_chatter_sound(self) -> np.ndarray:
        """Generate synthetic background chatter sound"""
        duration = 8.0
        samples = int(duration * self.audio_engine.sample_rate)

        # Create multiple "voice" sources
        chatter = np.zeros(samples)

        # Generate 4 different voice-like sounds
        for voice_num in range(4):
            # Random frequency for each voice
            base_freq = np.random.uniform(100, 300)
            freq_variation = np.random.uniform(0, 50, samples)

            # Create voice-like sound with frequency modulation
            t = np.linspace(0, duration, samples)
            voice_freq = base_freq + freq_variation
            voice = np.sin(2 * np.pi * np.cumsum(voice_freq) / self.audio_engine.sample_rate)

            # Apply envelope
            envelope = np.random.uniform(0.1, 1.0, samples)
            voice = voice * envelope * 0.05

            # Add to chatter mix
            start_time = np.random.uniform(0, duration * 0.7)
            start_sample = int(start_time * self.audio_engine.sample_rate)
            end_sample = min(start_sample + len(voice), samples)
            chatter[start_sample:end_sample] += voice[:end_sample - start_sample]

        return chatter

    async def _create_character_voices(self):
        """Create character voice sources"""
        # This would load actual voice files in a real implementation
        # For now, create synthetic voices

        characters = ["bartender", "patron1", "patron2", "musician"]

        for character in characters:
            voice_source = AudioSource(
                source_id=f"voice_{character}",
                position=Vector3(
                    np.random.uniform(-3, 3),
                    1.6,
                    np.random.uniform(-2, 2)
                ),
                volume=0.5,
                is_looping=False,
                max_distance=10.0
            )

            # Generate synthetic voice
            voice_audio = self._generate_speech_sound(duration=3.0)
            voice_source.audio_data = voice_audio

            self.audio_engine.add_source(voice_source)
            self.character_voices[character] = voice_source

    def _generate_speech_sound(self, duration: float = 2.0) -> np.ndarray:
        """Generate synthetic speech-like sound"""
        samples = int(duration * self.audio_engine.sample_rate)
        t = np.linspace(0, duration, samples)

        # Create vowel-like sounds
        vowels = ['a', 'e', 'i', 'o', 'u']
        speech = np.zeros(samples)

        for i in range(5):
            # Formant frequencies for vowels
            if i == 0:  # 'a' sound
                f1, f2, f3 = 730, 1090, 2440
            elif i == 1:  # 'e' sound
                f1, f2, f3 = 660, 1700, 2410
            elif i == 2:  # 'i' sound
                f1, f2, f3 = 270, 2140, 2950
            elif i == 3:  # 'o' sound
                f1, f2, f3 = 570, 840, 2410
            else:  # 'u' sound
                f1, f2, f3 = 440, 1170, 2410

            # Generate vowel sound
            vowel_start = i * duration / 5
            vowel_end = (i + 1) * duration / 5
            vowel_samples = int((vowel_end - vowel_start) * self.audio_engine.sample_rate)
            vowel_t = np.linspace(vowel_start, vowel_end, vowel_samples)

            # Combine formants
            vowel = (0.5 * np.sin(2 * np.pi * f1 * vowel_t) +
                    0.3 * np.sin(2 * np.pi * f2 * vowel_t) +
                    0.2 * np.sin(2 * np.pi * f3 * vowel_t))

            # Apply envelope
            envelope = np.exp(-np.linspace(0, 2, vowel_samples))
            vowel = vowel * envelope * 0.1

            start_sample = int(vowel_start * self.audio_engine.sample_rate)
            end_sample = min(start_sample + len(vowel), samples)
            speech[start_sample:end_sample] = vowel[:end_sample - start_sample]

        return speech

    def play_character_dialogue(self, character: str, position: Vector3):
        """Play character dialogue at specific position"""
        voice_id = f"voice_{character}"
        if voice_id in self.character_voices:
            voice_source = self.character_voices[voice_id]
            voice_source.position = position
            voice_source.current_position = 0
            voice_source.is_playing = True

    def play_story_sound(self, sound_name: str, position: Vector3):
        """Play story-related sound effect"""
        # Create temporary sound source
        sound_source = AudioSource(
            source_id=f"story_{sound_name}",
            position=position,
            volume=0.7,
            is_looping=False,
            max_distance=15.0
        )

        # Generate or load sound
        if sound_name == "door_creak":
            sound_source.audio_data = self._generate_door_creak()
        elif sound_name == "glass_clink":
            sound_source.audio_data = self._generate_glass_clink()
        else:
            sound_source.audio_data = self._generate_test_tone(440, 1.0)

        self.audio_engine.add_source(sound_source)
        sound_source.is_playing = True

    def _generate_door_creak(self) -> np.ndarray:
        """Generate door creaking sound"""
        duration = 2.0
        samples = int(duration * self.audio_engine.sample_rate)
        t = np.linspace(0, duration, samples)

        # Low frequency creak with frequency modulation
        base_freq = 50
        freq_mod = 20 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
        creak = np.sin(2 * np.pi * (base_freq + freq_mod) * t)

        # Add noise for texture
        noise = np.random.normal(0, 0.1, samples)

        # Apply envelope
        envelope = np.exp(-t * 0.5)
        sound = (creak + noise) * envelope * 0.3

        return sound

    def _generate_glass_clink(self) -> np.ndarray:
        """Generate glass clinking sound"""
        duration = 0.5
        samples = int(duration * self.audio_engine.sample_rate)
        t = np.linspace(0, duration, samples)

        # High frequency ting sound
        ting = np.sin(2 * np.pi * 3000 * t) * np.exp(-t * 10)

        # Add some harmonics
        harmonic1 = 0.3 * np.sin(2 * np.pi * 6000 * t) * np.exp(-t * 12)
        harmonic2 = 0.2 * np.sin(2 * np.pi * 9000 * t) * np.exp(-t * 15)

        sound = (ting + harmonic1 + harmonic2) * 0.2

        return sound


async def main():
    """Main function to test spatial audio system"""
    logging.basicConfig(level=logging.INFO)

    # Create spatial audio engine
    audio_engine = SpatialAudioEngine(sample_rate=44100, buffer_size=512)

    # Create DMLogn8n audio manager
    audio_manager = DMLogn8nAudioManager(audio_engine)

    # Initialize tavern audio
    await audio_manager.initialize_tavern_audio()

    # Start audio streaming
    if await audio_engine.start_streaming():
        try:
            # Set listener position (center of tavern)
            audio_engine.set_listener(Vector3(0, 1.7, 0), Vector3(0, 0, -1))

            # Play ambient sounds
            audio_engine.play_source("fireplace")
            audio_engine.play_source("chatter")

            # Move listener around to test spatial audio
            positions = [
                Vector3(0, 1.7, 0),
                Vector3(2, 1.7, 0),
                Vector3(-2, 1.7, 0),
                Vector3(0, 1.7, 2),
                Vector3(0, 1.7, -2)
            ]

            for i, pos in enumerate(positions):
                print(f"Moving to position {i+1}: {pos}")
                audio_engine.set_listener(pos, Vector3(0, 0, -1))
                await asyncio.sleep(2)

                # Play some character dialogue
                audio_manager.play_character_dialogue("bartender", Vector3(0, 1.7, 3))
                await asyncio.sleep(1)

                # Play story sound
                audio_manager.play_story_sound("glass_clink", Vector3(1, 1, 1))
                await asyncio.sleep(2)

            # Print performance stats
            stats = audio_engine.get_performance_stats()
            print(f"Performance stats: {stats}")

        except KeyboardInterrupt:
            pass
        finally:
            await audio_engine.stop_streaming()
    else:
        print("Failed to start audio streaming")


if __name__ == "__main__":
    asyncio.run(main())