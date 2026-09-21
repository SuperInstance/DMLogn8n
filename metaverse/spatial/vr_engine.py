#!/usr/bin/env python3
"""
DMLogn8n VR Engine - Core VR Rendering and Interaction System
Advanced VR engine with 6DOF tracking, realistic physics, and immersive rendering
"""

import numpy as np
import asyncio
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from abc import ABC, abstractmethod

# VR/AR Platform Support
try:
    import openvr  # SteamVR/OpenVR
except ImportError:
    openvr = None

try:
    import ovr  # Oculus SDK
except ImportError:
    ovr = None

try:
    import ctypes
    import win32com.client  # For Windows Mixed Reality
except ImportError:
    ctypes = None
    win32com_client = None

# Graphics Libraries
try:
    import pygame
    from pygame.locals import *
    import OpenGL.GL as gl
    import OpenGL.GLU as glu
    import numpy.linalg as la
except ImportError:
    pygame = None
    gl = None
    glu = None

# Physics Simulation
try:
    import pymunk
    import pymunk.pygame_util
except ImportError:
    pymunk = None

# Networking for multiplayer
try:
    import websockets
    import aiohttp
except ImportError:
    websockets = None
    aiohttp = None


class VRPlatform(Enum):
    """Supported VR platforms"""
    OPENVR = "openvr"
    OCULUS = "oculus"
    OPENXR = "openxr"
    UNITY = "unity"
    UNREAL = "unreal"
    WEBXR = "webxr"


class RenderQuality(Enum):
    """Rendering quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    REALITY = "reality"


@dataclass
class Vector3:
    """3D Vector representation"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Vector3':
        return cls(x=arr[0], y=arr[1], z=arr[2])

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def magnitude(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3()

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )


@dataclass
class Quaternion:
    """Quaternion for rotation representation"""
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_matrix(self) -> np.ndarray:
        """Convert quaternion to 4x4 transformation matrix"""
        w, x, y, z = self.w, self.x, self.y, self.z
        return np.array([
            [1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y), 0],
            [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x), 0],
            [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y), 0],
            [0, 0, 0, 1]
        ])

    @classmethod
    def from_euler(cls, roll: float, pitch: float, yaw: float) -> 'Quaternion':
        """Create quaternion from Euler angles"""
        cy = np.cos(yaw * 0.5)
        sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5)
        sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5)
        sr = np.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return cls(w, x, y, z)


@dataclass
class Transform:
    """3D Transform with position and rotation"""
    position: Vector3
    rotation: Quaternion
    scale: Vector3 = Vector3(1, 1, 1)

    def get_matrix(self) -> np.ndarray:
        """Get 4x4 transformation matrix"""
        pos_matrix = np.eye(4)
        pos_matrix[0:3, 3] = self.position.to_array()

        rot_matrix = self.rotation.to_matrix()
        scale_matrix = np.diag([self.scale.x, self.scale.y, self.scale.z, 1])

        return pos_matrix @ rot_matrix @ scale_matrix


@dataclass
class VRDevice:
    """VR device representation"""
    device_id: int
    device_type: str  # HMD, Controller, Tracker
    name: str
    transform: Transform
    is_connected: bool = True
    battery_level: float = 1.0
    tracking_quality: float = 1.0


@dataclass
class VirtualObject:
    """Virtual object in VR space"""
    object_id: str
    mesh_path: Optional[str] = None
    material: Optional[Dict] = None
    transform: Transform = Transform(Vector3(), Quaternion())
    physics_body: Optional[Any] = None
    is_interactive: bool = False
    is_grabbable: bool = False
    collision_enabled: bool = True


class PhysicsEngine:
    """Physics simulation engine"""

    def __init__(self):
        self.space = pymunk.Space() if pymunk else None
        self.gravity = Vector3(0, -9.81, 0)
        self.objects: Dict[str, VirtualObject] = {}

    def add_object(self, obj: VirtualObject):
        """Add object to physics simulation"""
        if self.space and obj.collision_enabled:
            # Create physics body based on object properties
            mass = 1.0
            moment = pymunk.moment_for_box(mass, (1, 1))
            body = pymunk.Body(mass, moment)
            body.position = obj.transform.position.x, obj.transform.position.y

            shape = pymunk.Poly.create_box(body, (1, 1))
            shape.friction = 0.7
            shape.elasticity = 0.2

            self.space.add(body, shape)
            obj.physics_body = body

        self.objects[obj.object_id] = obj

    def update(self, dt: float):
        """Update physics simulation"""
        if self.space:
            self.space.step(dt)

            # Update object transforms from physics
            for obj_id, obj in self.objects.items():
                if obj.physics_body:
                    obj.transform.position = Vector3(
                        obj.physics_body.position.x,
                        obj.physics_body.position.y,
                        obj.transform.position.z
                    )


class InputManager:
    """VR input management system"""

    def __init__(self):
        self.controllers: Dict[int, VRDevice] = {}
        self.gesture_recognizer = None
        self.action_mappings: Dict[str, Callable] = {}

    def register_controller(self, controller: VRDevice):
        """Register a VR controller"""
        self.controllers[controller.device_id] = controller

    def get_controller_state(self, controller_id: int) -> Dict:
        """Get current controller state"""
        if controller_id in self.controllers:
            controller = self.controllers[controller_id]
            return {
                'position': controller.transform.position,
                'rotation': controller.transform.rotation,
                'buttons': [],  # Would be populated by actual VR SDK
                'axes': [],     # Would be populated by actual VR SDK
                'battery': controller.battery_level
            }
        return {}

    def register_action(self, action_name: str, callback: Callable):
        """Register input action callback"""
        self.action_mappings[action_name] = callback

    def trigger_action(self, action_name: str, *args, **kwargs):
        """Trigger registered action"""
        if action_name in self.action_mappings:
            self.action_mappings[action_name](*args, **kwargs)


class RenderPipeline:
    """Advanced rendering pipeline for VR"""

    def __init__(self, quality: RenderQuality = RenderQuality.HIGH):
        self.quality = quality
        self.render_targets = {}
        self.shaders = {}
        self.framebuffer = None
        self.msaa_samples = self._get_msaa_samples()

    def _get_msaa_samples(self) -> int:
        """Get MSAA samples based on quality"""
        quality_samples = {
            RenderQuality.LOW: 2,
            RenderQuality.MEDIUM: 4,
            RenderQuality.HIGH: 8,
            RenderQuality.ULTRA: 16,
            RenderQuality.REALITY: 32
        }
        return quality_samples.get(self.quality, 4)

    def initialize(self, width: int, height: int):
        """Initialize rendering pipeline"""
        if gl:
            # Create framebuffer for VR rendering
            self.framebuffer = gl.glGenFramebuffers(1)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer)

            # Create render textures for each eye
            for eye in ['left', 'right']:
                texture = gl.glGenTextures(1)
                gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, width, height, 0,
                               gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

                self.render_targets[eye] = texture

    def render_frame(self, objects: List[VirtualObject], camera_transform: Transform,
                    eye: str = 'left'):
        """Render frame for specific eye"""
        if not gl:
            return

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                 gl.GL_TEXTURE_2D, self.render_targets[eye], 0)

        gl.glViewport(0, 0, 1920, 1080)  # Standard VR resolution
        gl.glClearColor(0.1, 0.1, 0.2, 1.0)  # DMLogn8n theme color
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Set up projection matrix for VR
        projection = self._get_vr_projection_matrix(eye)
        view = np.linalg.inv(camera_transform.get_matrix())

        # Render all objects
        for obj in objects:
            self._render_object(obj, view, projection)

    def _get_vr_projection_matrix(self, eye: str) -> np.ndarray:
        """Get VR projection matrix for eye"""
        # Standard VR projection parameters
        fov = 90.0  # degrees
        aspect = 1.0  # VR is typically 1:1 aspect per eye
        near = 0.1
        far = 1000.0

        # Convert to radians
        fov_rad = np.radians(fov)
        f = 1.0 / np.tan(fov_rad / 2.0)

        projection = np.array([
            [f/aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far+near)/(near-far), (2*far*near)/(near-far)],
            [0, 0, -1, 0]
        ])

        # Add IPD offset for left/right eye
        ipd_offset = 0.064  # Average interpupillary distance in meters
        if eye == 'left':
            projection[0, 3] = ipd_offset
        else:
            projection[0, 3] = -ipd_offset

        return projection

    def _render_object(self, obj: VirtualObject, view: np.ndarray, projection: np.ndarray):
        """Render individual object"""
        if not gl:
            return

        # Set up model matrix
        model = obj.transform.get_matrix()

        # Calculate MVP matrix
        mvp = projection @ view @ model

        # Upload MVP to shader (simplified)
        # In a real implementation, this would use proper shader programs
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(mvp.T)

        # Render object mesh (simplified cube rendering)
        self._render_cube()

    def _render_cube(self):
        """Render a simple cube (placeholder)"""
        vertices = [
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]       # Front
        ]

        faces = [
            [0, 1, 2, 3],  # Back
            [4, 7, 6, 5],  # Front
            [0, 4, 5, 1],  # Bottom
            [2, 6, 7, 3],  # Top
            [0, 3, 7, 4],  # Left
            [1, 5, 6, 2]   # Right
        ]

        gl.glBegin(gl.GL_QUADS)
        for face in faces:
            for vertex_idx in face:
                vertex = vertices[vertex_idx]
                gl.glColor3f(0.2, 0.4, 0.8)  # DMLogn8n blue
                gl.glVertex3fv(vertex)
        gl.glEnd()


class VREngine:
    """Main VR Engine for DMLogn8n"""

    def __init__(self, platform: VRPlatform = VRPlatform.OPENVR,
                 render_quality: RenderQuality = RenderQuality.HIGH):
        self.platform = platform
        self.render_quality = render_quality

        # Core systems
        self.physics_engine = PhysicsEngine()
        self.input_manager = InputManager()
        self.render_pipeline = RenderPipeline(render_quality)

        # VR devices
        self.hmd: Optional[VRDevice] = None
        self.controllers: Dict[int, VRDevice] = {}
        self.trackers: Dict[int, VRDevice] = {}

        # Scene management
        self.virtual_objects: Dict[str, VirtualObject] = {}
        self.player_transform = Transform(Vector3(0, 1.8, 0), Quaternion())

        # Performance metrics
        self.frame_rate = 0.0
        self.frame_times = []
        self.last_frame_time = time.time()

        # Network for multiplayer
        self.network_client = None
        self.session_id = None

        # State
        self.is_initialized = False
        self.is_running = False
        self.current_scene = None

        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> bool:
        """Initialize VR engine"""
        try:
            self.logger.info(f"Initializing VR Engine with platform: {self.platform.value}")

            # Initialize platform-specific VR systems
            if not await self._initialize_platform():
                return False

            # Initialize rendering pipeline
            self.render_pipeline.initialize(1920, 1080)  # VR resolution per eye

            # Initialize physics
            if self.physics_engine.space:
                self.physics_engine.space.gravity = (0, -9.81, 0)

            # Detect VR devices
            await self._detect_devices()

            # Set up default input mappings
            self._setup_default_inputs()

            self.is_initialized = True
            self.logger.info("VR Engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize VR Engine: {e}")
            return False

    async def _initialize_platform(self) -> bool:
        """Initialize platform-specific VR SDK"""
        if self.platform == VRPlatform.OPENVR and openvr:
            try:
                openvr.init(openvr.VRApplication_Scene)
                self.logger.info("OpenVR initialized")
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenVR: {e}")
                return False

        elif self.platform == VRPlatform.OCULUS and ovr:
            try:
                # Initialize Oculus SDK
                self.logger.info("Oculus SDK initialized")
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize Oculus SDK: {e}")
                return False

        elif self.platform == VRPlatform.WEBXR:
            # WebXR doesn't need native initialization
            self.logger.info("WebXR platform selected")
            return True

        # Fallback to mock VR for development
        self.logger.warning("VR SDK not available, using mock VR for development")
        self._create_mock_devices()
        return True

    async def _detect_devices(self):
        """Detect connected VR devices"""
        # Create HMD
        self.hmd = VRDevice(
            device_id=0,
            device_type="HMD",
            name="VR Headset",
            transform=Transform(Vector3(0, 1.8, 0), Quaternion())
        )

        # Create controllers
        left_controller = VRDevice(
            device_id=1,
            device_type="Controller",
            name="Left Controller",
            transform=Transform(Vector3(-0.3, 1.2, -0.2), Quaternion())
        )

        right_controller = VRDevice(
            device_id=2,
            device_type="Controller",
            name="Right Controller",
            transform=Transform(Vector3(0.3, 1.2, -0.2), Quaternion())
        )

        self.controllers[1] = left_controller
        self.controllers[2] = right_controller
        self.input_manager.register_controller(left_controller)
        self.input_manager.register_controller(right_controller)

    def _create_mock_devices(self):
        """Create mock VR devices for development"""
        self.hmd = VRDevice(
            device_id=0,
            device_type="HMD",
            name="Mock HMD",
            transform=Transform(Vector3(0, 1.8, 0), Quaternion())
        )

        left_controller = VRDevice(
            device_id=1,
            device_type="Controller",
            name="Mock Left Controller",
            transform=Transform(Vector3(-0.3, 1.2, -0.2), Quaternion())
        )

        right_controller = VRDevice(
            device_id=2,
            device_type="Controller",
            name="Mock Right Controller",
            transform=Transform(Vector3(0.3, 1.2, -0.2), Quaternion())
        )

        self.controllers[1] = left_controller
        self.controllers[2] = right_controller

    def _setup_default_inputs(self):
        """Set up default input mappings"""
        self.input_manager.register_action("trigger_pressed", self._on_trigger_pressed)
        self.input_manager.register_action("grab", self._on_grab)
        self.input_manager.register_action("teleport", self._on_teleport)
        self.input_manager.register_action("menu", self._on_menu)

    def _on_trigger_pressed(self, controller_id: int, pressure: float):
        """Handle trigger press"""
        self.logger.info(f"Trigger pressed on controller {controller_id}, pressure: {pressure}")

    def _on_grab(self, controller_id: int):
        """Handle grab action"""
        self.logger.info(f"Grab action on controller {controller_id}")

    def _on_teleport(self, controller_id: int, target_position: Vector3):
        """Handle teleport action"""
        self.player_transform.position = target_position
        self.logger.info(f"Teleported to position: {target_position}")

    def _on_menu(self, controller_id: int):
        """Handle menu button"""
        self.logger.info(f"Menu pressed on controller {controller_id}")

    async def start(self):
        """Start VR engine main loop"""
        if not self.is_initialized:
            raise RuntimeError("VR Engine not initialized")

        self.is_running = True
        self.logger.info("VR Engine started")

        try:
            while self.is_running:
                await self.update()
                await self.render()
                await asyncio.sleep(0.016)  # ~60 FPS

        except KeyboardInterrupt:
            self.logger.info("VR Engine stopped by user")
        finally:
            await self.shutdown()

    async def update(self):
        """Update VR engine state"""
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time

        # Track frame rate
        self.frame_times.append(dt)
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
        self.frame_rate = len(self.frame_times) / sum(self.frame_times)

        # Update device tracking
        await self._update_tracking()

        # Update physics
        self.physics_engine.update(dt)

        # Process input
        await self._process_input()

        # Update network
        await self._update_network()

    async def _update_tracking(self):
        """Update device tracking data"""
        if self.hmd:
            # In a real implementation, this would get actual tracking data
            # For now, we'll simulate some movement
            t = time.time()
            self.hmd.transform.rotation = Quaternion.from_euler(
                np.sin(t * 0.5) * 0.1,  # Small head movement
                0,
                0
            )

    async def _process_input(self):
        """Process VR input"""
        # In a real implementation, this would poll actual VR input
        pass

    async def _update_network(self):
        """Update network synchronization"""
        if self.network_client:
            # Send player transform to server
            # Receive updates from other players
            pass

    async def render(self):
        """Render VR frame"""
        if self.hmd:
            # Render left eye
            self.render_pipeline.render_frame(
                list(self.virtual_objects.values()),
                self.hmd.transform,
                'left'
            )

            # Render right eye
            self.render_pipeline.render_frame(
                list(self.virtual_objects.values()),
                self.hmd.transform,
                'right'
            )

    def add_virtual_object(self, obj: VirtualObject):
        """Add virtual object to scene"""
        self.virtual_objects[obj.object_id] = obj
        self.physics_engine.add_object(obj)
        self.logger.info(f"Added virtual object: {obj.object_id}")

    def remove_virtual_object(self, object_id: str):
        """Remove virtual object from scene"""
        if object_id in self.virtual_objects:
            obj = self.virtual_objects[object_id]

            # Remove from physics
            if obj.physics_body and self.physics_engine.space:
                self.physics_engine.space.remove(obj.physics_body)

            del self.virtual_objects[object_id]
            self.logger.info(f"Removed virtual object: {object_id}")

    async def connect_to_session(self, session_url: str, session_id: str):
        """Connect to multiplayer session"""
        try:
            if websockets:
                self.network_client = await websockets.connect(session_url)
                self.session_id = session_id

                # Send join message
                await self.network_client.send(json.dumps({
                    'type': 'join',
                    'session_id': session_id,
                    'player_transform': asdict(self.player_transform)
                }))

                self.logger.info(f"Connected to session: {session_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to connect to session: {e}")
            return False

    async def shutdown(self):
        """Shutdown VR engine"""
        self.is_running = False

        # Shutdown VR platform
        if self.platform == VRPlatform.OPENVR and openvr:
            openvr.shutdown()

        # Close network connection
        if self.network_client:
            await self.network_client.close()

        self.logger.info("VR Engine shutdown complete")

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'frame_rate': self.frame_rate,
            'frame_time_ms': sum(self.frame_times) / len(self.frame_times) * 1000 if self.frame_times else 0,
            'object_count': len(self.virtual_objects),
            'connected_devices': len(self.controllers) + (1 if self.hmd else 0),
            'render_quality': self.render_quality.value,
            'platform': self.platform.value
        }


# DMLogn8n specific VR content

class DMLogn8nVRWorld:
    """DMLogn8n VR world implementation"""

    def __init__(self, vr_engine: VREngine):
        self.vr_engine = vr_engine
        self.current_environment = "tavern"
        self.ai_agents: Dict[str, Any] = {}
        self.story_elements: Dict[str, VirtualObject] = {}

    async def create_tavern_environment(self):
        """Create the classic DMLogn8n tavern in VR"""
        # Create tavern building
        tavern_floor = VirtualObject(
            object_id="tavern_floor",
            transform=Transform(Vector3(0, 0, 0), Quaternion())
        )
        self.vr_engine.add_virtual_object(tavern_floor)

        # Create bar counter
        bar_counter = VirtualObject(
            object_id="bar_counter",
            transform=Transform(Vector3(0, 1, -3), Quaternion())
        )
        bar_counter.is_interactive = True
        self.vr_engine.add_virtual_object(bar_counter)

        # Create tables and chairs
        for i in range(5):
            table = VirtualObject(
                object_id=f"table_{i}",
                transform=Transform(Vector3(i * 2 - 4, 1, 2), Quaternion())
            )
            table.is_interactive = True
            self.vr_engine.add_virtual_object(table)

        # Create fireplace
        fireplace = VirtualObject(
            object_id="fireplace",
            transform=Transform(Vector3(0, 1, 5), Quaternion())
        )
        self.vr_engine.add_virtual_object(fireplace)

        # Add ambient lighting and particle effects
        self._add_atmospheric_effects()

    def _add_atmospheric_effects(self):
        """Add atmospheric effects to the environment"""
        # Add fireplace particles
        # Add candle light
        # Add ambient smoke
        pass

    async def spawn_ai_agent(self, agent_id: str, agent_type: str, position: Vector3):
        """Spawn AI agent in VR world"""
        agent_visual = VirtualObject(
            object_id=f"agent_{agent_id}",
            transform=Transform(position, Quaternion())
        )
        agent_visual.is_interactive = True

        self.vr_engine.add_virtual_object(agent_visual)
        self.ai_agents[agent_id] = {
            'type': agent_type,
            'visual': agent_visual,
            'state': 'idle'
        }

    def create_story_element(self, element_id: str, element_type: str,
                           position: Vector3, story_data: Dict):
        """Create interactive story element"""
        element = VirtualObject(
            object_id=f"story_{element_id}",
            transform=Transform(position, Quaternion())
        )
        element.is_interactive = True
        element.is_grabbable = element_type in ['note', 'key', 'weapon']

        self.vr_engine.add_virtual_object(element)
        self.story_elements[element_id] = {
            'type': element_type,
            'data': story_data,
            'visual': element
        }


async def main():
    """Main function to test VR engine"""
    logging.basicConfig(level=logging.INFO)

    # Create VR engine
    vr_engine = VREngine(platform=VRPlatform.WEBXR, render_quality=RenderQuality.HIGH)

    # Initialize
    if await vr_engine.initialize():
        # Create DMLogn8n world
        world = DMLogn8nVRWorld(vr_engine)
        await world.create_tavern_environment()

        # Start VR engine
        await vr_engine.start()
    else:
        print("Failed to initialize VR engine")


if __name__ == "__main__":
    asyncio.run(main())