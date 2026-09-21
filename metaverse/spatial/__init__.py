"""
DMLogn8n Spatial VR/AR System

A revolutionary mixed reality system that brings DMLogn8n into virtual and augmented reality
with seamless integration between the virtual and real worlds.
"""

__version__ = "1.0.0"
__author__ = "DMLogn8n Team"
__email__ = "team@dmlogn8n.com"

# Core components
from .vr_engine import VREngine, VRPlatform, RenderQuality
from .ar_overlay import ARSession, ARPlatform, AROverlay, OverlayType
from .spatial_audio import SpatialAudioEngine, AudioSource
from .hand_tracking import HandTracker, HandTrackingMethod, GestureType
from .eye_tracking import EyeTracker, EyeTrackingMethod
from .haptic_system import DMLogn8nHapticSystem, HapticDeviceType
from .spatial_mapping import SpatialMapper, SpatialSensor
from .mixed_reality import MixedRealityEngine, RealityMode, TransitionType

# Main experience
from .mixed_reality import DMLogn8nMixedRealityExperience

# Utility classes
from .vr_engine import Vector3 as VRVector3, Quaternion, Transform, VirtualObject
from .spatial_audio import Vector3 as AudioVector3, AudioListener
from .hand_tracking import Vector3 as HandVector3, HandLandmarks, HandGesture
from .eye_tracking import Point2D, EyeLandmarks, GazeData
from .haptic_system import Vector3 as HapticVector3, HapticEffect, TextureProperties
from .spatial_mapping import Point3D as MapPoint3D, SpatialSurface, SpatialMap

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Core systems
    "VREngine",
    "ARSession",
    "SpatialAudioEngine",
    "HandTracker",
    "EyeTracker",
    "DMLogn8nHapticSystem",
    "SpatialMapper",
    "MixedRealityEngine",

    # Main experience
    "DMLogn8nMixedRealityExperience",

    # Enums and types
    "VRPlatform",
    "RenderQuality",
    "ARPlatform",
    "OverlayType",
    "HandTrackingMethod",
    "GestureType",
    "EyeTrackingMethod",
    "HapticDeviceType",
    "RealityMode",
    "TransitionType",

    # Data structures
    "AudioSource",
    "HandLandmarks",
    "HandGesture",
    "EyeLandmarks",
    "GazeData",
    "HapticEffect",
    "TextureProperties",
    "SpatialSurface",
    "SpatialMap",
    "VirtualObject",
    "Transform",
    "Quaternion",

    # Vector types (specific to each system)
    "VRVector3",
    "AudioVector3",
    "HandVector3",
    "HapticVector3",
    "MapPoint3D",
    "Point2D",
]

# System info
def get_system_info():
    """Get information about the spatial system capabilities"""
    return {
        "version": __version__,
        "components": {
            "vr_engine": VREngine,
            "ar_overlay": ARSession,
            "spatial_audio": SpatialAudioEngine,
            "hand_tracking": HandTracker,
            "eye_tracking": EyeTracker,
            "haptic_system": DMLogn8nHapticSystem,
            "spatial_mapping": SpatialMapper,
            "mixed_reality": MixedRealityEngine
        },
        "platforms": {
            "vr": [platform.value for platform in VRPlatform],
            "ar": [platform.value for platform in ARPlatform]
        }
    }

def create_default_experience():
    """Create a default DMLogn8n mixed reality experience"""
    return DMLogn8nMixedRealityExperience()

# Quick start functions
async def quick_vr_experience():
    """Quick start VR experience"""
    experience = DMLogn8nMixedRealityExperience()
    if await experience.initialize_experience():
        await experience.mr_engine.switch_mode(RealityMode.FULL_VR)
        await experience.mr_engine.start()

async def quick_ar_experience():
    """Quick start AR experience"""
    experience = DMLogn8nMixedRealityExperience()
    if await experience.initialize_experience():
        await experience.mr_engine.switch_mode(RealityMode.FULL_AR)
        await experience.mr_engine.start()

async def quick_mixed_reality_experience():
    """Quick start mixed reality experience"""
    experience = DMLogn8nMixedRealityExperience()
    if await experience.initialize_experience():
        await experience.mr_engine.switch_mode(RealityMode.MIXED_REALITY)
        await experience.mr_engine.start()