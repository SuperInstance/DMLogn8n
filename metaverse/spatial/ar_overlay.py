#!/usr/bin/env python3
"""
DMLogn8n AR Overlay System - Augmented Reality Enhancement
Advanced AR overlay system that enhances real-world environments with game elements
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

# Computer Vision Libraries
try:
    import cv2
    import mediapipe as mp
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    cv2 = None
    mp = None
    Image = None

# AR Platform Support
try:
    import aruco
except ImportError:
    aruco = None

try:
    import open3d as o3d
except ImportError:
    o3d = None

# WebRTC for camera access
try:
    import aiortc
    from aiortc import VideoStreamTrack
except ImportError:
    aiortc = None
    VideoStreamTrack = None

# Mobile AR frameworks (would require native bindings)
# ARKit (iOS)
# ARCore (Android)
# HoloLens (Windows Mixed Reality)


class ARPlatform(Enum):
    """Supported AR platforms"""
    ARKIT = "arkit"          # Apple ARKit
    ARCORE = "arcore"        # Google ARCore
    HOLOLENS = "hololens"    # Microsoft HoloLens
    MAGICLEAP = "magicleap"  # Magic Leap
    WEBAR = "webar"          # WebXR AR
    OPENCV = "opencv"        # OpenCV-based AR


class OverlayType(Enum):
    """Types of AR overlays"""
    UI_ELEMENT = "ui_element"
    GAME_OBJECT = "game_object"
    INFORMATION = "information"
    NAVIGATION = "navigation"
    EFFECT = "effect"
    INTERACTION = "interaction"


class DetectionType(Enum):
    """Types of real-world detection"""
    FACE = "face"
    HAND = "hand"
    BODY = "body"
    QR_CODE = "qr_code"
    AR_MARKER = "ar_marker"
    OBJECT = "object"
    TEXT = "text"
    PLANE = "plane"


@dataclass
class ARCamera:
    """AR camera parameters"""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    fov: float = 60.0  # Field of view in degrees
    intrinsics: Optional[np.ndarray] = None
    distortion: Optional[np.ndarray] = None
    exposure: float = 0.0
    white_balance: float = 0.0


@dataclass
class ARLandmark:
    """Real-world landmark for AR anchoring"""
    landmark_id: str
    detection_type: DetectionType
    position_2d: Tuple[float, float]  # Screen coordinates
    position_3d: Optional[np.ndarray] = None  # World coordinates
    confidence: float = 1.0
    timestamp: float = 0.0
    bounding_box: Optional[Tuple[float, float, float, float]] = None


@dataclass
class AROverlay:
    """AR overlay element"""
    overlay_id: str
    overlay_type: OverlayType
    content: Any  # Text, image, 3D model, etc.
    position_2d: Tuple[float, float]  # Screen coordinates
    position_3d: Optional[np.ndarray] = None  # World coordinates
    anchor_landmark_id: Optional[str] = None
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    is_visible: bool = True
    is_interactive: bool = False
    z_order: int = 0
    animation_data: Optional[Dict] = None


@dataclass
class ARInteraction:
    """AR interaction event"""
    interaction_id: str
    interaction_type: str  # tap, gesture, voice, etc.
    overlay_id: str
    position_2d: Tuple[float, float]
    timestamp: float
    data: Optional[Dict] = None


class ComputerVisionProcessor:
    """Computer vision processing for AR"""

    def __init__(self):
        self.face_detector = None
        self.hand_detector = None
        self.body_detector = None
        self.object_detector = None
        self.qr_detector = None

        # Initialize MediaPipe
        if mp:
            self.face_detector = mp.solutions.face_detection
            self.hand_detector = mp.solutions.hands
            self.body_detector = mp.solutions.pose
            self.object_detector = mp.solutions.object_detection

        # Initialize OpenCV detectors
        if cv2:
            self.qr_detector = cv2.QRCodeDetector()

    def detect_faces(self, image: np.ndarray) -> List[ARLandmark]:
        """Detect faces in image"""
        landmarks = []

        if self.face_detector and mp:
            with self.face_detector.FaceDetection(
                model_selection=0, min_detection_confidence=0.5) as face_detection:

                results = face_detection.process(image)
                if results.detections:
                    for detection in results.detections:
                        bbox = detection.location_data.relative_bounding_box
                        h, w, _ = image.shape

                        x = bbox.xmin * w
                        y = bbox.ymin * h
                        width = bbox.width * w
                        height = bbox.height * h

                        landmark = ARLandmark(
                            landmark_id=f"face_{len(landmarks)}",
                            detection_type=DetectionType.FACE,
                            position_2d=(x + width/2, y + height/2),
                            confidence=detection.score[0],
                            timestamp=time.time(),
                            bounding_box=(x, y, x + width, y + height)
                        )
                        landmarks.append(landmark)

        return landmarks

    def detect_hands(self, image: np.ndarray) -> List[ARLandmark]:
        """Detect hands in image"""
        landmarks = []

        if self.hand_detector and mp:
            with self.hand_detector.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as hands:

                results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if results.multi_hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                        # Get palm center (landmark 9)
                        palm = hand_landmarks.landmark[9]
                        h, w, _ = image.shape

                        landmark = ARLandmark(
                            landmark_id=f"hand_{hand_idx}",
                            detection_type=DetectionType.HAND,
                            position_2d=(palm.x * w, palm.y * h),
                            confidence=0.8,  # MediaPipe doesn't provide hand confidence
                            timestamp=time.time()
                        )
                        landmarks.append(landmark)

        return landmarks

    def detect_qr_codes(self, image: np.ndarray) -> List[ARLandmark]:
        """Detect QR codes in image"""
        landmarks = []

        if self.qr_detector and cv2:
            data, points, _ = self.qr_detector.detectAndDecode(image)
            if data and points is not None:
                # Get center of QR code
                points = points[0]
                center_x = np.mean(points[:, 0])
                center_y = np.mean(points[:, 1])

                landmark = ARLandmark(
                    landmark_id=f"qr_{hash(data) % 10000}",
                    detection_type=DetectionType.QR_CODE,
                    position_2d=(center_x, center_y),
                    confidence=1.0,
                    timestamp=time.time(),
                    bounding_box=(np.min(points[:, 0]), np.min(points[:, 1]),
                                 np.max(points[:, 0]), np.max(points[:, 1]))
                )
                landmarks.append(landmark)

        return landmarks

    def detect_ar_markers(self, image: np.ndarray) -> List[ARLandmark]:
        """Detect AR markers in image"""
        landmarks = []

        if aruco and cv2:
            dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
            parameters = aruco.DetectorParameters()
            marker_corners, marker_ids, rejected = aruco.detectMarkers(
                image, dictionary, parameters=parameters)

            if marker_ids is not None:
                for i, (corners, marker_id) in enumerate(zip(marker_corners, marker_ids)):
                    # Get center of marker
                    points = corners[0]
                    center_x = np.mean(points[:, 0])
                    center_y = np.mean(points[:, 1])

                    landmark = ARLandmark(
                        landmark_id=f"marker_{marker_id[0]}",
                        detection_type=DetectionType.AR_MARKER,
                        position_2d=(center_x, center_y),
                        confidence=1.0,
                        timestamp=time.time(),
                        bounding_box=(np.min(points[:, 0]), np.min(points[:, 1]),
                                     np.max(points[:, 0]), np.max(points[:, 1]))
                    )
                    landmarks.append(landmark)

        return landmarks


class ARRenderer:
    """AR overlay rendering system"""

    def __init__(self, camera: ARCamera):
        self.camera = camera
        self.overlays: Dict[str, AROverlay] = {}
        self.landmarks: Dict[str, ARLandmark] = {}

        # Create transparent overlay surface
        self.overlay_surface = None
        self.font = None

        # Initialize PIL for rendering
        if Image:
            self.overlay_surface = Image.new('RGBA', (camera.width, camera.height), (0, 0, 0, 0))
            try:
                self.font = ImageFont.truetype("arial.ttf", 24)
            except:
                self.font = ImageFont.load_default()

    def add_overlay(self, overlay: AROverlay):
        """Add overlay to renderer"""
        self.overlays[overlay.overlay_id] = overlay

    def remove_overlay(self, overlay_id: str):
        """Remove overlay from renderer"""
        if overlay_id in self.overlays:
            del self.overlays[overlay_id]

    def update_landmark(self, landmark: ARLandmark):
        """Update landmark position"""
        self.landmarks[landmark.landmark_id] = landmark

        # Update anchored overlays
        for overlay in self.overlays.values():
            if overlay.anchor_landmark_id == landmark.landmark_id:
                overlay.position_2d = landmark.position_2d
                if landmark.position_3d is not None:
                    overlay.position_3d = landmark.position_3d

    def render_frame(self, camera_image: np.ndarray) -> np.ndarray:
        """Render AR overlays on camera image"""
        if not Image:
            return camera_image

        # Create overlay image
        overlay_img = Image.new('RGBA', (self.camera.width, self.camera.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        # Sort overlays by z-order
        sorted_overlays = sorted(self.overlays.values(), key=lambda x: x.z_order)

        for overlay in sorted_overlays:
            if not overlay.is_visible:
                continue

            self._render_overlay(draw, overlay)

        # Convert camera image to PIL
        camera_pil = Image.fromarray(cv2.cvtColor(camera_image, cv2.COLOR_BGR2RGB))

        # Composite overlay onto camera image
        result = Image.alpha_composite(camera_pil.convert('RGBA'), overlay_img)

        # Convert back to OpenCV format
        result = cv2.cvtColor(np.array(result), cv2.COLOR_RGBA2BGR)

        return result

    def _render_overlay(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render individual overlay"""
        x, y = overlay.position_2d

        # Apply opacity
        if overlay.overlay_type == OverlayType.UI_ELEMENT:
            self._render_ui_element(draw, overlay)
        elif overlay.overlay_type == OverlayType.GAME_OBJECT:
            self._render_game_object(draw, overlay)
        elif overlay.overlay_type == OverlayType.INFORMATION:
            self._render_information(draw, overlay)
        elif overlay.overlay_type == OverlayType.NAVIGATION:
            self._render_navigation(draw, overlay)
        elif overlay.overlay_type == OverlayType.EFFECT:
            self._render_effect(draw, overlay)
        elif overlay.overlay_type == OverlayType.INTERACTION:
            self._render_interaction(draw, overlay)

    def _render_ui_element(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render UI element overlay"""
        x, y = overlay.position_2d

        if isinstance(overlay.content, str):
            # Render text
            text = overlay.content
            if self.font:
                bbox = draw.textbbox((0, 0), text, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(text) * 10
                text_height = 24

            # Background
            draw.rectangle([
                (x - text_width//2 - 10, y - text_height//2 - 5),
                (x + text_width//2 + 10, y + text_height//2 + 5)
            ], fill=(50, 50, 80, int(200 * overlay.opacity)))

            # Text
            if self.font:
                draw.text((x - text_width//2, y - text_height//2), text,
                         font=self.font, fill=(255, 255, 255, int(255 * overlay.opacity)))

    def _render_game_object(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render game object overlay"""
        x, y = overlay.position_2d
        size = 50 * overlay.scale

        # Render a simple game object (could be 3D model in full implementation)
        draw.ellipse([
            (x - size//2, y - size//2),
            (x + size//2, y + size//2)
        ], fill=(100, 200, 100, int(200 * overlay.opacity)),
           outline=(255, 255, 255, int(255 * overlay.opacity)))

    def _render_information(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render information overlay"""
        x, y = overlay.position_2d

        if isinstance(overlay.content, dict):
            title = overlay.content.get('title', '')
            description = overlay.content.get('description', '')

            # Title
            if self.font:
                draw.text((x, y), title, font=self.font,
                         fill=(255, 255, 100, int(255 * overlay.opacity)))

            # Description (smaller font)
            if description:
                draw.text((x, y + 30), description,
                         fill=(200, 200, 200, int(200 * overlay.opacity)))

    def _render_navigation(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render navigation overlay"""
        x, y = overlay.position_2d
        size = 30 * overlay.scale

        # Render arrow or navigation indicator
        points = [
            (x, y - size),
            (x - size//2, y + size//2),
            (x, y),
            (x + size//2, y + size//2)
        ]
        draw.polygon(points, fill=(255, 200, 0, int(200 * overlay.opacity)))

    def _render_effect(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render effect overlay"""
        x, y = overlay.position_2d

        # Render particle effects, glows, etc.
        if overlay.animation_data:
            # Simple pulsing effect
            t = time.time()
            pulse = np.sin(t * 3) * 0.3 + 0.7
            size = 40 * overlay.scale * pulse

            draw.ellipse([
                (x - size//2, y - size//2),
                (x + size//2, y + size//2)
            ], fill=(255, 150, 255, int(100 * overlay.opacity * pulse)))

    def _render_interaction(self, draw: ImageDraw.Draw, overlay: AROverlay):
        """Render interaction hint overlay"""
        x, y = overlay.position_2d

        # Render interactive hint
        draw.rectangle([
            (x - 40, y - 20),
            (x + 40, y + 20)
        ], fill=(100, 150, 255, int(150 * overlay.opacity)),
           outline=(255, 255, 255, int(255 * overlay.opacity)), width=2)

        if isinstance(overlay.content, str):
            draw.text((x - 30, y - 10), overlay.content,
                     fill=(255, 255, 255, int(255 * overlay.opacity)))


class ARSession:
    """AR session manager"""

    def __init__(self, platform: ARPlatform = ARPlatform.OPENCV,
                 camera: Optional[ARCamera] = None):
        self.platform = platform
        self.camera = camera or ARCamera()

        # Core systems
        self.cv_processor = ComputerVisionProcessor()
        self.renderer = ARRenderer(self.camera)

        # Session state
        self.is_running = False
        self.camera_capture = None
        self.current_frame = None

        # Detection configuration
        self.enabled_detections = {
            DetectionType.FACE: True,
            DetectionType.HAND: True,
            DetectionType.QR_CODE: True,
            DetectionType.AR_MARKER: True
        }

        # Interaction callbacks
        self.interaction_callbacks: Dict[str, Callable] = {}

        self.logger = logging.getLogger(__name__)

    async def start_session(self) -> bool:
        """Start AR session"""
        try:
            self.logger.info(f"Starting AR session with platform: {self.platform.value}")

            # Initialize camera
            if not await self._initialize_camera():
                return False

            # Initialize platform-specific AR
            if not await self._initialize_platform():
                return False

            self.is_running = True
            self.logger.info("AR session started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start AR session: {e}")
            return False

    async def _initialize_camera(self) -> bool:
        """Initialize camera capture"""
        if cv2:
            # Try to open default camera
            self.camera_capture = cv2.VideoCapture(0)
            if self.camera_capture.isOpened():
                # Set camera properties
                self.camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera.width)
                self.camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera.height)
                self.camera_capture.set(cv2.CAP_PROP_FPS, self.camera.fps)
                self.logger.info("Camera initialized successfully")
                return True
            else:
                self.logger.error("Failed to open camera")
                return False
        else:
            self.logger.warning("OpenCV not available, using mock camera")
            return True

    async def _initialize_platform(self) -> bool:
        """Initialize platform-specific AR"""
        if self.platform == ARPlatform.ARKit:
            # Would initialize ARKit here
            self.logger.info("ARKit platform selected")
            return True
        elif self.platform == ARPlatform.ARCORE:
            # Would initialize ARCore here
            self.logger.info("ARCore platform selected")
            return True
        elif self.platform == ARPlatform.HOLOLENS:
            # Would initialize HoloLens here
            self.logger.info("HoloLens platform selected")
            return True
        else:
            # Fallback to computer vision-based AR
            self.logger.info(f"Using computer vision-based AR for platform: {self.platform.value}")
            return True

    async def process_frame(self) -> Optional[np.ndarray]:
        """Process a single camera frame"""
        if not self.is_running:
            return None

        # Capture frame from camera
        if self.camera_capture and cv2:
            ret, frame = self.camera_capture.read()
            if not ret:
                return None
        else:
            # Generate mock frame for testing
            frame = np.zeros((self.camera.height, self.camera.width, 3), dtype=np.uint8)
            frame[:] = (50, 50, 80)  # Dark blue background

        self.current_frame = frame

        # Process computer vision detections
        await self._process_detections(frame)

        # Render overlays
        rendered_frame = self.renderer.render_frame(frame)

        return rendered_frame

    async def _process_detections(self, frame: np.ndarray):
        """Process all enabled detections"""
        detected_landmarks = []

        # Face detection
        if self.enabled_detections.get(DetectionType.FACE, False):
            faces = self.cv_processor.detect_faces(frame)
            detected_landmarks.extend(faces)

        # Hand detection
        if self.enabled_detections.get(DetectionType.HAND, False):
            hands = self.cv_processor.detect_hands(frame)
            detected_landmarks.extend(hands)

        # QR code detection
        if self.enabled_detections.get(DetectionType.QR_CODE, False):
            qr_codes = self.cv_processor.detect_qr_codes(frame)
            detected_landmarks.extend(qr_codes)

        # AR marker detection
        if self.enabled_detections.get(DetectionType.AR_MARKER, False):
            ar_markers = self.cv_processor.detect_ar_markers(frame)
            detected_landmarks.extend(ar_markers)

        # Update renderer with detected landmarks
        for landmark in detected_landmarks:
            self.renderer.update_landmark(landmark)

    def add_overlay(self, overlay: AROverlay):
        """Add overlay to AR session"""
        self.renderer.add_overlay(overlay)
        self.logger.info(f"Added AR overlay: {overlay.overlay_id}")

    def remove_overlay(self, overlay_id: str):
        """Remove overlay from AR session"""
        self.renderer.remove_overlay(overlay_id)
        self.logger.info(f"Removed AR overlay: {overlay_id}")

    def create_dmlogn8n_ui(self):
        """Create DMLogn8n-specific UI overlays"""
        # Health/status overlay
        health_overlay = AROverlay(
            overlay_id="health_status",
            overlay_type=OverlayType.UI_ELEMENT,
            content="Health: 100%",
            position_2d=(100, 100),
            z_order=100
        )
        self.add_overlay(health_overlay)

        # Character info overlay
        character_overlay = AROverlay(
            overlay_id="character_info",
            overlay_type=OverlayType.INFORMATION,
            content={
                'title': 'Character',
                'description': 'Level 5 Bard'
            },
            position_2d=(100, 200),
            z_order=99
        )
        self.add_overlay(character_overlay)

        # Action buttons overlay
        actions_overlay = AROverlay(
            overlay_id="action_buttons",
            overlay_type=OverlayType.INTERACTION,
            content="Actions",
            position_2d=(self.camera.width - 150, 100),
            z_order=101
        )
        self.add_overlay(actions_overlay)

    def create_interaction_zones(self):
        """Create interactive zones in real world"""
        # Create interaction hints for detected faces
        for landmark_id, landmark in self.renderer.landmarks.items():
            if landmark.detection_type == DetectionType.FACE:
                interaction_overlay = AROverlay(
                    overlay_id=f"face_interaction_{landmark_id}",
                    overlay_type=OverlayType.INTERACTION,
                    content="Talk",
                    position_2d=landmark.position_2d,
                    anchor_landmark_id=landmark_id,
                    z_order=50
                )
                self.add_overlay(interaction_overlay)

    def register_interaction_callback(self, interaction_type: str, callback: Callable):
        """Register interaction callback"""
        self.interaction_callbacks[interaction_type] = callback

    async def handle_interaction(self, interaction: ARInteraction):
        """Handle AR interaction"""
        self.logger.info(f"AR Interaction: {interaction.interaction_type} on {interaction.overlay_id}")

        # Call registered callback
        if interaction.interaction_type in self.interaction_callbacks:
            await self.interaction_callbacks[interaction.interaction_type](interaction)

    async def stop_session(self):
        """Stop AR session"""
        self.is_running = False

        # Release camera
        if self.camera_capture:
            self.camera_capture.release()

        self.logger.info("AR session stopped")


class DMLogn8nARIntegration:
    """DMLogn8n AR integration system"""

    def __init__(self, ar_session: ARSession):
        self.ar_session = ar_session
        self.game_elements: Dict[str, Any] = {}
        self.story_overlays: Dict[str, AROverlay] = {}

    async def initialize_game_ar(self):
        """Initialize DMLogn8n AR elements"""
        # Create game UI
        self.ar_session.create_dmlogn8n_ui()

        # Create story elements that appear based on QR codes
        self._create_qr_story_elements()

        # Create AR markers for game objects
        self._create_ar_markers()

        # Set up interaction callbacks
        self._setup_interactions()

    def _create_qr_story_elements(self):
        """Create story elements triggered by QR codes"""
        # Example: QR code triggers story overlay
        story_overlay = AROverlay(
            overlay_id="qr_story_trigger",
            overlay_type=OverlayType.INFORMATION,
            content={
                'title': 'Story Discovery',
                'description': 'Scan QR codes to reveal story elements'
            },
            position_2d=(0, 0),  # Will be anchored to QR code
            z_order=80
        )
        self.story_overlays['qr_trigger'] = story_overlay

    def _create_ar_markers(self):
        """Create AR markers for game objects"""
        # Marker for tavern location
        tavern_marker = AROverlay(
            overlay_id="tavern_marker",
            overlay_type=OverlayType.GAME_OBJECT,
            content="Tavern",
            position_2d=(0, 0),  # Will be anchored to AR marker
            z_order=70
        )
        self.story_overlays['tavern_marker'] = tavern_marker

    def _setup_interactions(self):
        """Set up AR interaction callbacks"""
        self.ar_session.register_interaction_callback('tap', self._handle_tap)
        self.ar_session.register_interaction_callback('gesture', self._handle_gesture)

    async def _handle_tap(self, interaction: ARInteraction):
        """Handle tap interaction"""
        overlay_id = interaction.overlay_id

        if overlay_id == 'action_buttons':
            # Show action menu
            self._show_action_menu(interaction.position_2d)
        elif overlay_id.startswith('face_interaction_'):
            # Start conversation with detected person
            await self._start_conversation(overlay_id)
        elif overlay_id in self.story_overlays:
            # Interact with story element
            await self._interact_with_story_element(overlay_id)

    async def _handle_gesture(self, interaction: ARInteraction):
        """Handle gesture interaction"""
        gesture_data = interaction.data or {}
        gesture_type = gesture_data.get('type', 'unknown')

        if gesture_type == 'wave':
            # Trigger wave response
            self._trigger_wave_response()
        elif gesture_type == 'point':
            # Point at object for information
            await self._point_at_object(interaction.position_2d)

    def _show_action_menu(self, position: Tuple[float, float]):
        """Show action menu at position"""
        actions_overlay = AROverlay(
            overlay_id="actions_menu",
            overlay_type=OverlayType.UI_ELEMENT,
            content="• Talk\n• Examine\n• Use\n• Inventory",
            position_2d=position,
            z_order=150
        )
        self.ar_session.add_overlay(actions_overlay)

    async def _start_conversation(self, face_id: str):
        """Start conversation with detected person"""
        # Create conversation overlay
        conversation_overlay = AROverlay(
            overlay_id=f"conversation_{face_id}",
            overlay_type=OverlayType.INFORMATION,
            content={
                'title': 'Conversation',
                'description': 'Hello! Welcome to our tavern.'
            },
            position_2d=(self.ar_session.camera.width // 2, self.ar_session.camera.height - 200),
            z_order=120
        )
        self.ar_session.add_overlay(conversation_overlay)

    async def _interact_with_story_element(self, element_id: str):
        """Interact with story element"""
        # Update story element content based on interaction
        if element_id in self.story_overlays:
            element = self.story_overlays[element_id]
            if isinstance(element.content, dict):
                element.content['description'] = "You discovered something interesting!"
            self.ar_session.add_overlay(element)  # Update overlay

    def _trigger_wave_response(self):
        """Trigger wave response from AI characters"""
        # Create wave effect overlay
        wave_overlay = AROverlay(
            overlay_id="wave_response",
            overlay_type=OverlayType.EFFECT,
            content={},
            position_2d=(self.ar_session.camera.width // 2, 100),
            z_order=90
        )
        self.ar_session.add_overlay(wave_overlay)

    async def _point_at_object(self, position: Tuple[float, float]):
        """Show information about pointed object"""
        info_overlay = AROverlay(
            overlay_id="pointed_object_info",
            overlay_type=OverlayType.INFORMATION,
            content={
                'title': 'Object',
                'description': 'This looks interesting...'
            },
            position_2d=position,
            z_order=110
        )
        self.ar_session.add_overlay(info_overlay)


async def main():
    """Main function to test AR overlay system"""
    logging.basicConfig(level=logging.INFO)

    # Create AR session
    camera = ARCamera(width=1280, height=720, fps=30)
    ar_session = ARSession(platform=ARPlatform.OPENCV, camera=camera)

    # Initialize session
    if await ar_session.start_session():
        # Initialize DMLogn8n AR integration
        ar_integration = DMLogn8nARIntegration(ar_session)
        await ar_integration.initialize_game_ar()

        # Process frames
        try:
            while True:
                frame = await ar_session.process_frame()
                if frame is not None:
                    # Display frame (in a real implementation, would send to display)
                    cv2.imshow('DMLogn8n AR', frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                await asyncio.sleep(0.033)  # ~30 FPS

        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()
            await ar_session.stop_session()
    else:
        print("Failed to start AR session")


if __name__ == "__main__":
    asyncio.run(main())