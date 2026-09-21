#!/usr/bin/env python3
"""
DMLogn8n Hand Tracking System - Advanced Hand and Gesture Recognition
Advanced hand tracking system with precise finger tracking and gesture recognition
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

# Computer Vision Libraries
try:
    import cv2
    import mediapipe as mp
    from PIL import Image, ImageDraw
except ImportError:
    cv2 = None
    mp = None
    Image = None

# Machine Learning Libraries
try:
    import tensorflow as tf
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    tf = None
    torch = None
    nn = None
    F = None

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
from scipy.spatial.distance import euclidean
from scipy.signal import savgol_filter


class HandTrackingMethod(Enum):
    """Hand tracking methods"""
    MEDIAPIPE = "mediapipe"
    OPENPOSE = "openpose"
    CUSTOM_CNN = "custom_cnn"
    DEPTH_CAMERA = "depth_camera"
    LEAP_MOTION = "leap_motion"


class GestureType(Enum):
    """Types of gestures"""
    PINCH = "pinch"
    POINT = "point"
    THUMBS_UP = "thumbs_up"
    VICTORY = "victory"
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"
    FIST = "fist"
    OPEN_PALM = "open_palm"
    OK = "ok"
    CALL = "call"
    GRAB = "grab"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    CIRCLE = "circle"
    CUSTOM = "custom"


@dataclass
class Vector3:
    """3D Vector for hand landmarks"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Vector3':
        return cls(x=arr[0], y=arr[1], z=arr[2])

    def distance_to(self, other: 'Vector3') -> float:
        return euclidean([self.x, self.y, self.z], [other.x, other.y, other.z])

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)


@dataclass
class FingerLandmarks:
    """Landmarks for a single finger"""
    finger_id: int  # 0=Thumb, 1=Index, 2=Middle, 3=Ring, 4=Pinky
    tip: Vector3
    dip: Vector3  # Distal interphalangeal joint
    pip: Vector3  # Proximal interphalangeal joint
    mcp: Vector3  # Metacarpophalangeal joint
    is_extended: bool = False
    curl_amount: float = 0.0  # 0=fully extended, 1=fully curled


@dataclass
class HandLandmarks:
    """Complete hand landmarks"""
    wrist: Vector3
    fingers: List[FingerLandmarks]
    palm_center: Vector3
    bounding_box: Optional[Tuple[float, float, float, float]] = None
    confidence: float = 0.0
    handedness: str = "unknown"  # left or right


@dataclass
class HandGesture:
    """Detected hand gesture"""
    gesture_type: GestureType
    confidence: float
    hand_id: int
    timestamp: float
    landmarks: HandLandmarks
    gesture_data: Optional[Dict] = None


@dataclass
class HandTrackingEvent:
    """Hand tracking event"""
    event_type: str  # "hand_detected", "hand_lost", "gesture_detected"
    hand_id: int
    timestamp: float
    data: Optional[Dict] = None


class HandGestureRecognizer:
    """Gesture recognition system"""

    def __init__(self):
        self.gesture_history: Dict[int, deque] = {}  # hand_id -> gesture history
        self.history_length = 10
        self.gesture_callbacks: Dict[GestureType, Callable] = {}

        # Gesture recognition parameters
        self.pinch_threshold = 0.05  # Distance threshold for pinch detection
        self.finger_extension_threshold = 0.15  # Threshold for finger extension
        self.gesture_smoothing_window = 3

    def recognize_gesture(self, landmarks: HandLandmarks, hand_id: int) -> Optional[HandGesture]:
        """Recognize gesture from hand landmarks"""
        # Calculate finger extensions
        finger_states = self._calculate_finger_states(landmarks)

        # Recognize static gestures
        gesture = self._recognize_static_gesture(landmarks, finger_states, hand_id)

        # Recognize dynamic gestures
        if not gesture:
            gesture = self._recognize_dynamic_gesture(landmarks, hand_id)

        # Update gesture history
        if hand_id not in self.gesture_history:
            self.gesture_history[hand_id] = deque(maxlen=self.history_length)

        if gesture:
            self.gesture_history[hand_id].append(gesture)

        return gesture

    def _calculate_finger_states(self, landmarks: HandLandmarks) -> List[bool]:
        """Calculate which fingers are extended"""
        finger_states = []

        for finger in landmarks.fingers:
            # Calculate finger extension based on joint angles
            # Simple heuristic: finger is extended if tip is further from palm than base
            palm_to_tip_dist = landmarks.palm_center.distance_to(finger.tip)
            palm_to_base_dist = landmarks.palm_center.distance_to(finger.mcp)

            # Normalize by finger length
            finger_length = finger.mcp.distance_to(finger.tip)
            if finger_length > 0:
                extension_ratio = (palm_to_tip_dist - palm_to_base_dist) / finger_length
                is_extended = extension_ratio > self.finger_extension_threshold
            else:
                is_extended = False

            finger_states.append(is_extended)
            finger.is_extended = is_extended

            # Calculate curl amount
            curl_amount = max(0, 1 - extension_ratio)
            finger.curl_amount = curl_amount

        return finger_states

    def _recognize_static_gesture(self, landmarks: HandLandmarks,
                                finger_states: List[bool], hand_id: int) -> Optional[HandGesture]:
        """Recognize static (pose-based) gestures"""
        extended_count = sum(finger_states)

        # Check for specific gestures
        if self._is_pinch(landmarks):
            return HandGesture(
                gesture_type=GestureType.PINCH,
                confidence=0.9,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks,
                gesture_data={'pinch_strength': self._calculate_pinch_strength(landmarks)}
            )

        elif self._is_point(finger_states):
            return HandGesture(
                gesture_type=GestureType.POINT,
                confidence=0.85,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_thumbs_up(finger_states):
            return HandGesture(
                gesture_type=GestureType.THUMBS_UP,
                confidence=0.8,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_victory(finger_states):
            return HandGesture(
                gesture_type=GestureType.VICTORY,
                confidence=0.85,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_rock(finger_states):
            return HandGesture(
                gesture_type=GestureType.ROCK,
                confidence=0.9,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_paper(finger_states):
            return HandGesture(
                gesture_type=GestureType.PAPER,
                confidence=0.9,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_scissors(finger_states):
            return HandGesture(
                gesture_type=GestureType.SCISSORS,
                confidence=0.9,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_fist(finger_states):
            return HandGesture(
                gesture_type=GestureType.FIST,
                confidence=0.85,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_open_palm(finger_states):
            return HandGesture(
                gesture_type=GestureType.OPEN_PALM,
                confidence=0.9,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_ok(landmarks):
            return HandGesture(
                gesture_type=GestureType.OK,
                confidence=0.85,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        elif self._is_call(finger_states):
            return HandGesture(
                gesture_type=GestureType.CALL,
                confidence=0.8,
                hand_id=hand_id,
                timestamp=time.time(),
                landmarks=landmarks
            )

        return None

    def _recognize_dynamic_gesture(self, landmarks: HandLandmarks, hand_id: int) -> Optional[HandGesture]:
        """Recognize dynamic (motion-based) gestures"""
        if hand_id not in self.gesture_history or len(self.gesture_history[hand_id]) < 3:
            return None

        # Get recent positions
        recent_positions = [g.landmarks.palm_center.to_array()
                           for g in list(self.gesture_history[hand_id])[-5:]]

        if len(recent_positions) < 3:
            return None

        # Calculate motion vectors
        motion_vectors = []
        for i in range(1, len(recent_positions)):
            vector = recent_positions[i] - recent_positions[i-1]
            motion_vectors.append(vector)

        if not motion_vectors:
            return None

        # Analyze motion pattern
        avg_motion = np.mean(motion_vectors, axis=0)

        # Detect swipe gestures
        if np.linalg.norm(avg_motion) > 0.02:  # Minimum motion threshold
            angle = np.degrees(np.arctan2(avg_motion[1], avg_motion[0]))

            if -45 <= angle <= 45:  # Right
                return HandGesture(
                    gesture_type=GestureType.SWIPE_RIGHT,
                    confidence=0.7,
                    hand_id=hand_id,
                    timestamp=time.time(),
                    landmarks=landmarks,
                    gesture_data={'direction': 'right', 'velocity': np.linalg.norm(avg_motion)}
                )
            elif 45 < angle <= 135:  # Down
                return HandGesture(
                    gesture_type=GestureType.SWIPE_DOWN,
                    confidence=0.7,
                    hand_id=hand_id,
                    timestamp=time.time(),
                    landmarks=landmarks,
                    gesture_data={'direction': 'down', 'velocity': np.linalg.norm(avg_motion)}
                )
            elif -135 <= angle < -45:  # Up
                return HandGesture(
                    gesture_type=GestureType.SWIPE_UP,
                    confidence=0.7,
                    hand_id=hand_id,
                    timestamp=time.time(),
                    landmarks=landmarks,
                    gesture_data={'direction': 'up', 'velocity': np.linalg.norm(avg_motion)}
                )
            else:  # Left
                return HandGesture(
                    gesture_type=GestureType.SWIPE_LEFT,
                    confidence=0.7,
                    hand_id=hand_id,
                    timestamp=time.time(),
                    landmarks=landmarks,
                    gesture_data={'direction': 'left', 'velocity': np.linalg.norm(avg_motion)}
                )

        return None

    def _is_pinch(self, landmarks: HandLandmarks) -> bool:
        """Check if hand is making pinch gesture"""
        thumb_tip = landmarks.fingers[0].tip
        index_tip = landmarks.fingers[1].tip
        distance = thumb_tip.distance_to(index_tip)
        return distance < self.pinch_threshold

    def _calculate_pinch_strength(self, landmarks: HandLandmarks) -> float:
        """Calculate pinch strength (0.0 to 1.0)"""
        thumb_tip = landmarks.fingers[0].tip
        index_tip = landmarks.fingers[1].tip
        distance = thumb_tip.distance_to(index_tip)
        # Inverse relationship: closer = stronger pinch
        strength = max(0, 1 - (distance / self.pinch_threshold))
        return min(1, strength)

    def _is_point(self, finger_states: List[bool]) -> bool:
        """Check if hand is pointing"""
        return (finger_states[1] and  # Index finger extended
                not any(finger_states[i] for i in [0, 2, 3, 4] if i != 1))  # Others not extended

    def _is_thumbs_up(self, finger_states: List[bool]) -> bool:
        """Check if hand is giving thumbs up"""
        return (finger_states[0] and  # Thumb extended
                not any(finger_states[i] for i in [1, 2, 3, 4]))  # Others not extended

    def _is_victory(self, finger_states: List[bool]) -> bool:
        """Check if hand is making victory sign"""
        return (finger_states[1] and finger_states[2] and  # Index and middle extended
                not any(finger_states[i] for i in [0, 3, 4]))  # Others not extended

    def _is_rock(self, finger_states: List[bool]) -> bool:
        """Check if hand is making rock sign"""
        return (finger_states[0] and finger_states[3] and  # Thumb and ring extended
                not any(finger_states[i] for i in [1, 2, 4]))  # Others not extended

    def _is_paper(self, finger_states: List[bool]) -> bool:
        """Check if hand is open (paper)"""
        return all(finger_states)  # All fingers extended

    def _is_scissors(self, finger_states: List[bool]) -> bool:
        """Check if hand is making scissors sign"""
        return (finger_states[1] and finger_states[2] and  # Index and middle extended
                not any(finger_states[i] for i in [0, 3, 4]))  # Others not extended

    def _is_fist(self, finger_states: List[bool]) -> bool:
        """Check if hand is in fist"""
        return not any(finger_states)  # No fingers extended

    def _is_open_palm(self, finger_states: List[bool]) -> bool:
        """Check if hand is open palm"""
        return all(finger_states)  # All fingers extended

    def _is_ok(self, landmarks: HandLandmarks) -> bool:
        """Check if hand is making OK sign"""
        # Thumb and index form circle
        thumb_tip = landmarks.fingers[0].tip
        index_tip = landmarks.fingers[1].tip
        distance = thumb_tip.distance_to(index_tip)

        # Other fingers extended
        other_fingers_extended = all(landmarks.fingers[i].is_extended for i in [2, 3, 4])

        return distance < self.pinch_threshold * 1.5 and other_fingers_extended

    def _is_call(self, finger_states: List[bool]) -> bool:
        """Check if hand is making call gesture"""
        # Thumb and pinky extended
        return (finger_states[0] and finger_states[4] and
                not any(finger_states[i] for i in [1, 2, 3]))


class HandTracker:
    """Main hand tracking system"""

    def __init__(self, method: HandTrackingMethod = HandTrackingMethod.MEDIAPIPE,
                 max_hands: int = 2):
        self.method = method
        self.max_hands = max_hands

        # Core components
        self.gesture_recognizer = HandGestureRecognizer()
        self.mediapipe_hands = None
        self.current_hands: Dict[int, HandLandmarks] = {}
        self.hand_id_counter = 0

        # Camera and processing
        self.camera = None
        self.is_running = False
        self.processing_thread = None

        # Event callbacks
        self.event_callbacks: Dict[str, Callable] = {}

        # Performance tracking
        self.frame_count = 0
        self.processing_times = deque(maxlen=30)
        self.last_frame_time = time.time()

        self.logger = logging.getLogger(__name__)

        # Initialize tracking method
        self._initialize_tracking_method()

    def _initialize_tracking_method(self):
        """Initialize the specified tracking method"""
        if self.method == HandTrackingMethod.MEDIAPIPE and mp:
            self.mediapipe_hands = mp.solutions.hands
            self.logger.info("Initialized MediaPipe hand tracking")
        else:
            self.logger.warning(f"Tracking method {self.method.value} not available, using fallback")

    async def start_tracking(self, camera_source: int = 0) -> bool:
        """Start hand tracking"""
        try:
            self.logger.info(f"Starting hand tracking with camera: {camera_source}")

            # Initialize camera
            if cv2:
                self.camera = cv2.VideoCapture(camera_source)
                if not self.camera.isOpened():
                    self.logger.error("Failed to open camera")
                    return False

                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
            else:
                self.logger.warning("OpenCV not available, using mock camera")

            self.is_running = True

            # Start processing thread
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()

            self.logger.info("Hand tracking started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start hand tracking: {e}")
            return False

    def _processing_loop(self):
        """Main processing loop"""
        while self.is_running:
            start_time = time.time()

            # Capture frame
            frame = self._capture_frame()
            if frame is not None:
                # Process frame for hand detection
                self._process_frame(frame)

            # Track performance
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)

            # Control frame rate (target 30 FPS)
            elapsed = time.time() - self.last_frame_time
            sleep_time = max(0, (1.0 / 30.0) - elapsed)
            time.sleep(sleep_time)

            self.last_frame_time = time.time()
            self.frame_count += 1

    def _capture_frame(self) -> Optional[np.ndarray]:
        """Capture frame from camera"""
        if self.camera and cv2:
            ret, frame = self.camera.read()
            if ret:
                return cv2.flip(frame, 1)  # Mirror image
            else:
                return None
        else:
            # Generate mock frame for testing
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            frame[:] = (50, 50, 80)  # Dark blue background
            return frame

    def _process_frame(self, frame: np.ndarray):
        """Process frame for hand detection"""
        if self.method == HandTrackingMethod.MEDIAPIPE and self.mediapipe_hands:
            self._process_with_mediapipe(frame)
        else:
            self._process_mock_frame(frame)

    def _process_with_mediapipe(self, frame: np.ndarray):
        """Process frame using MediaPipe"""
        with self.mediapipe_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as hands:

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            detected_hands = []

            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Extract landmarks
                    landmarks = self._extract_mediapipe_landmarks(hand_landmarks, frame.shape)

                    if landmarks:
                        # Determine handedness
                        handedness = "right"  # MediaPipe provides this in results.multi_handedness
                        if results.multi_handedness and hand_idx < len(results.multi_handedness):
                            handedness_label = results.multi_handedness[hand_idx].classification[0].label
                            handedness = handedness_label.lower()

                        landmarks.handedness = handedness
                        detected_hands.append(landmarks)

            # Update current hands
            self._update_hand_tracking(detected_hands)

    def _extract_mediapipe_landmarks(self, hand_landmarks, image_shape: Tuple[int, int, int]) -> Optional[HandLandmarks]:
        """Extract landmarks from MediaPipe hand detection"""
        try:
            h, w, _ = image_shape

            # MediaPipe hand landmark indices
            # 0: Wrist
            # 1-4: Thumb (MCP, IP, PIP, TIP)
            # 5-8: Index finger (MCP, PIP, DIP, TIP)
            # 9-12: Middle finger (MCP, PIP, DIP, TIP)
            # 13-16: Ring finger (MCP, PIP, DIP, TIP)
            # 17-20: Pinky finger (MCP, PIP, DIP, TIP)

            landmarks = []
            for landmark in hand_landmarks.landmark:
                x = landmark.x * w
                y = landmark.y * h
                z = landmark.z * w  # Approximate depth
                landmarks.append(Vector3(x, y, z))

            # Create wrist
            wrist = landmarks[0]

            # Create finger landmarks
            fingers = []
            finger_indices = [
                [1, 2, 3, 4],   # Thumb (MCP, IP, PIP, TIP) - adjusted for MediaPipe
                [5, 6, 7, 8],   # Index finger (MCP, PIP, DIP, TIP)
                [9, 10, 11, 12], # Middle finger
                [13, 14, 15, 16], # Ring finger
                [17, 18, 19, 20]  # Pinky finger
            ]

            for finger_idx, indices in enumerate(finger_indices):
                if len(indices) >= 4:
                    finger_landmarks = FingerLandmarks(
                        finger_id=finger_idx,
                        tip=landmarks[indices[3]],
                        dip=landmarks[indices[2]],
                        pip=landmarks[indices[1]],
                        mcp=landmarks[indices[0]]
                    )
                    fingers.append(finger_landmarks)

            # Calculate palm center (average of finger MCP joints)
            palm_x = sum(finger.mcp.x for finger in fingers) / len(fingers)
            palm_y = sum(finger.mcp.y for finger in fingers) / len(fingers)
            palm_z = sum(finger.mcp.z for finger in fingers) / len(fingers)
            palm_center = Vector3(palm_x, palm_y, palm_z)

            # Calculate bounding box
            all_points = [wrist] + [finger.tip for finger in fingers]
            min_x = min(p.x for p in all_points)
            max_x = max(p.x for p in all_points)
            min_y = min(p.y for p in all_points)
            max_y = max(p.y for p in all_points)
            bounding_box = (min_x, min_y, max_x - min_x, max_y - min_y)

            return HandLandmarks(
                wrist=wrist,
                fingers=fingers,
                palm_center=palm_center,
                bounding_box=bounding_box,
                confidence=1.0  # MediaPipe doesn't provide per-hand confidence
            )

        except Exception as e:
            self.logger.error(f"Error extracting MediaPipe landmarks: {e}")
            return None

    def _process_mock_frame(self, frame: np.ndarray):
        """Process mock frame for testing"""
        # Generate mock hand data for testing
        mock_hands = []

        # Create mock right hand
        mock_landmarks = self._create_mock_hand_landmarks(400, 300, "right")
        if mock_landmarks:
            mock_hands.append(mock_landmarks)

        # Create mock left hand occasionally
        if self.frame_count % 120 < 60:  # Visible for 2 seconds every 4 seconds
            mock_landmarks_left = self._create_mock_hand_landmarks(800, 300, "left")
            if mock_landmarks_left:
                mock_hands.append(mock_landmarks_left)

        self._update_hand_tracking(mock_hands)

    def _create_mock_hand_landmarks(self, center_x: float, center_y: float,
                                  handedness: str) -> Optional[HandLandmarks]:
        """Create mock hand landmarks for testing"""
        try:
            # Create wrist at center
            wrist = Vector3(center_x, center_y, 0)

            # Create fingers with simple geometry
            fingers = []
            finger_positions = [
                (center_x - 40, center_y - 60),   # Thumb
                (center_x - 20, center_y - 100),  # Index
                (center_x, center_y - 110),       # Middle
                (center_x + 20, center_y - 100),  # Ring
                (center_x + 40, center_y - 80)    # Pinky
            ]

            for finger_idx, (fx, fy) in enumerate(finger_positions):
                # Create finger landmarks
                mcp = Vector3(fx, fy + 40, 0)
                pip = Vector3(fx, fy + 20, 0)
                dip = Vector3(fx, fy + 10, 0)
                tip = Vector3(fx, fy, 0)

                finger_landmarks = FingerLandmarks(
                    finger_id=finger_idx,
                    tip=tip,
                    dip=dip,
                    pip=pip,
                    mcp=mcp
                )
                fingers.append(finger_landmarks)

            # Palm center
            palm_center = Vector3(center_x, center_y - 50, 0)

            # Bounding box
            min_x = center_x - 60
            min_y = center_y - 120
            bounding_box = (min_x, min_y, 120, 120)

            return HandLandmarks(
                wrist=wrist,
                fingers=fingers,
                palm_center=palm_center,
                bounding_box=bounding_box,
                confidence=0.9,
                handedness=handedness
            )

        except Exception as e:
            self.logger.error(f"Error creating mock hand landmarks: {e}")
            return None

    def _update_hand_tracking(self, detected_hands: List[HandLandmarks]):
        """Update hand tracking with new detections"""
        # Simple hand assignment based on proximity to previous positions
        current_hand_ids = list(self.current_hands.keys())

        if not detected_hands:
            # No hands detected - remove all current hands
            for hand_id in current_hand_ids:
                self._trigger_event("hand_lost", hand_id, None)
            self.current_hands.clear()
            return

        # Assign hand IDs to detected hands
        assigned_ids = set()

        for detected_hand in detected_hands:
            # Find closest existing hand
            best_id = None
            best_distance = float('inf')

            for hand_id in current_hand_ids:
                if hand_id not in assigned_ids:
                    current_hand = self.current_hands[hand_id]
                    distance = detected_hand.palm_center.distance_to(current_hand.palm_center)

                    if distance < best_distance and distance < 100:  # Threshold for hand continuity
                        best_distance = distance
                        best_id = hand_id

            if best_id is not None:
                # Update existing hand
                self.current_hands[best_id] = detected_hand
                assigned_ids.add(best_id)
            else:
                # Create new hand
                new_id = self.hand_id_counter
                self.hand_id_counter += 1
                self.current_hands[new_id] = detected_hand
                assigned_ids.add(new_id)
                self._trigger_event("hand_detected", new_id, detected_hand)

        # Remove lost hands
        for hand_id in current_hand_ids:
            if hand_id not in assigned_ids:
                del self.current_hands[hand_id]
                self._trigger_event("hand_lost", hand_id, None)

        # Process gestures for all current hands
        for hand_id, hand_landmarks in self.current_hands.items():
            gesture = self.gesture_recognizer.recognize_gesture(hand_landmarks, hand_id)
            if gesture:
                self._trigger_event("gesture_detected", hand_id, gesture)

    def _trigger_event(self, event_type: str, hand_id: int, data: Any):
        """Trigger hand tracking event"""
        event = HandTrackingEvent(
            event_type=event_type,
            hand_id=hand_id,
            timestamp=time.time(),
            data=data
        )

        # Call registered callbacks
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type](event)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event_type}: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for hand tracking events"""
        self.event_callbacks[event_type] = callback
        self.logger.info(f"Registered callback for event: {event_type}")

    def register_gesture_callback(self, gesture_type: GestureType, callback: Callable):
        """Register callback for specific gesture"""
        self.gesture_recognizer.gesture_callbacks[gesture_type] = callback
        self.logger.info(f"Registered callback for gesture: {gesture_type.value}")

    async def stop_tracking(self):
        """Stop hand tracking"""
        self.is_running = False

        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        if self.camera:
            self.camera.release()

        self.logger.info("Hand tracking stopped")

    def get_current_hands(self) -> Dict[int, HandLandmarks]:
        """Get currently tracked hands"""
        return self.current_hands.copy()

    def get_hand_landmarks_2d(self, hand_id: int) -> Optional[List[Tuple[float, float]]]:
        """Get 2D landmark positions for drawing"""
        if hand_id not in self.current_hands:
            return None

        landmarks = self.current_hands[hand_id]
        points_2d = []

        # Add wrist
        points_2d.append((landmarks.wrist.x, landmarks.wrist.y))

        # Add finger landmarks
        for finger in landmarks.fingers:
            points_2d.append((finger.mcp.x, finger.mcp.y))
            points_2d.append((finger.pip.x, finger.pip.y))
            points_2d.append((finger.dip.x, finger.dip.y))
            points_2d.append((finger.tip.x, finger.tip.y))

        return points_2d

    def draw_hand_landmarks(self, frame: np.ndarray, hand_id: int,
                           color: Tuple[int, int, int] = (0, 255, 0)):
        """Draw hand landmarks on frame"""
        points_2d = self.get_hand_landmarks_2d(hand_id)
        if not points_2d or not cv2:
            return

        # Draw connections
        connections = [
            # Wrist to thumb
            (0, 1),
            # Thumb
            (1, 2), (2, 3), (3, 4),
            # Index finger
            (0, 5), (5, 6), (6, 7), (7, 8),
            # Middle finger
            (0, 9), (9, 10), (10, 11), (11, 12),
            # Ring finger
            (0, 13), (13, 14), (14, 15), (15, 16),
            # Pinky finger
            (0, 17), (17, 18), (18, 19), (19, 20)
        ]

        for start_idx, end_idx in connections:
            if start_idx < len(points_2d) and end_idx < len(points_2d):
                start_point = (int(points_2d[start_idx][0]), int(points_2d[start_idx][1]))
                end_point = (int(points_2d[end_idx][0]), int(points_2d[end_idx][1]))
                cv2.line(frame, start_point, end_point, color, 2)

        # Draw landmarks
        for point in points_2d:
            cv2.circle(frame, (int(point[0]), int(point[1])), 5, color, -1)

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
        fps = 1.0 / avg_processing_time if avg_processing_time > 0 else 0

        return {
            'fps': fps,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'frame_count': self.frame_count,
            'tracked_hands': len(self.current_hands),
            'tracking_method': self.method.value,
            'max_hands': self.max_hands
        }


class DMLogn8nHandInteraction:
    """DMLogn8n-specific hand interaction system"""

    def __init__(self, hand_tracker: HandTracker):
        self.hand_tracker = hand_tracker
        self.interaction_zones: Dict[str, Dict] = {}
        self.grabbed_objects: Dict[int, str] = {}  # hand_id -> object_id
        self.gesture_actions: Dict[GestureType, Callable] = {}

        # Register event callbacks
        self._setup_interaction_callbacks()

    def _setup_interaction_callbacks(self):
        """Setup interaction callbacks"""
        self.hand_tracker.register_event_callback("hand_detected", self._on_hand_detected)
        self.hand_tracker.register_event_callback("hand_lost", self._on_hand_lost)
        self.hand_tracker.register_event_callback("gesture_detected", self._on_gesture_detected)

        # Register specific gesture callbacks
        self.hand_tracker.register_gesture_callback(GestureType.PINCH, self._on_pinch)
        self.hand_tracker.register_gesture_callback(GestureType.POINT, self._on_point)
        self.hand_tracker.register_gesture_callback(GestureType.GRAB, self._on_grab)
        self.hand_tracker.register_gesture_callback(GestureType.SWIPE_RIGHT, self._on_swipe_right)
        self.hand_tracker.register_gesture_callback(GestureType.SWIPE_LEFT, self._on_swipe_left)

    def _on_hand_detected(self, event: HandTrackingEvent):
        """Handle hand detection"""
        print(f"Hand detected: {event.hand_id} ({event.data.handedness})")

    def _on_hand_lost(self, event: HandTrackingEvent):
        """Handle hand loss"""
        print(f"Hand lost: {event.hand_id}")
        # Release any grabbed objects
        if event.hand_id in self.grabbed_objects:
            object_id = self.grabbed_objects[event.hand_id]
            del self.grabbed_objects[event.hand_id]
            print(f"Released object: {object_id}")

    def _on_gesture_detected(self, event: HandTrackingEvent):
        """Handle gesture detection"""
        gesture = event.data
        print(f"Gesture detected: {gesture.gesture_type.value} (confidence: {gesture.confidence:.2f})")

    def _on_pinch(self, event: HandTrackingEvent):
        """Handle pinch gesture"""
        gesture = event.data
        hand_landmarks = gesture.landmarks

        # Check if pinching at any interaction zone
        pinch_position = hand_landmarks.fingers[0].tip  # Thumb tip
        for zone_id, zone in self.interaction_zones.items():
            zone_center = zone['position']
            distance = pinch_position.distance_to(zone_center)

            if distance < zone['radius']:
                print(f"Pinched interaction zone: {zone_id}")
                zone['callback'](zone_id, "pinch")

    def _on_point(self, event: HandTrackingEvent):
        """Handle point gesture"""
        gesture = event.data
        hand_landmarks = gesture.landmarks

        # Check what the hand is pointing at
        pointing_direction = self._calculate_pointing_direction(hand_landmarks)
        print(f"Pointing direction: {pointing_direction}")

    def _on_grab(self, event: HandTrackingEvent):
        """Handle grab gesture"""
        gesture = event.data
        hand_landmarks = gesture.landmarks

        # Find nearest grabbable object
        hand_position = hand_landmarks.palm_center
        nearest_object = self._find_nearest_grabbable_object(hand_position)

        if nearest_object:
            self.grabbed_objects[event.hand_id] = nearest_object
            print(f"Grabbed object: {nearest_object}")

    def _on_swipe_right(self, event: HandTrackingEvent):
        """Handle swipe right gesture"""
        print("Swipe right detected - maybe navigate to next page")

    def _on_swipe_left(self, event: HandTrackingEvent):
        """Handle swipe left gesture"""
        print("Swipe left detected - maybe navigate to previous page")

    def _calculate_pointing_direction(self, hand_landmarks: HandLandmarks) -> Vector3:
        """Calculate pointing direction from hand landmarks"""
        # Use index finger direction
        index_finger = hand_landmarks.fingers[1]
        direction = index_finger.tip - index_finger.mcp
        return direction.normalize()

    def _find_nearest_grabbable_object(self, position: Vector3) -> Optional[str]:
        """Find nearest grabbable object to position"""
        # In a real implementation, this would check actual game objects
        # For now, return a mock object ID
        return "object_001"

    def add_interaction_zone(self, zone_id: str, position: Vector3, radius: float,
                           callback: Callable):
        """Add interaction zone"""
        self.interaction_zones[zone_id] = {
            'position': position,
            'radius': radius,
            'callback': callback
        }
        print(f"Added interaction zone: {zone_id}")

    def remove_interaction_zone(self, zone_id: str):
        """Remove interaction zone"""
        if zone_id in self.interaction_zones:
            del self.interaction_zones[zone_id]
            print(f"Removed interaction zone: {zone_id}")

    def create_tavern_interaction_zones(self):
        """Create interaction zones for tavern environment"""
        # Bar interaction zone
        self.add_interaction_zone(
            "bar",
            Vector3(400, 300, 0),
            50,
            lambda zone_id, action: print(f"Interacted with {zone_id}: {action}")
        )

        # Fireplace interaction zone
        self.add_interaction_zone(
            "fireplace",
            Vector3(200, 200, 0),
            60,
            lambda zone_id, action: print(f"Interacted with {zone_id}: {action}")
        )

        # Door interaction zone
        self.add_interaction_zone(
            "door",
            Vector3(1000, 400, 0),
            40,
            lambda zone_id, action: print(f"Interacted with {zone_id}: {action}")
        )


async def main():
    """Main function to test hand tracking system"""
    logging.basicConfig(level=logging.INFO)

    # Create hand tracker
    hand_tracker = HandTracker(method=HandTrackingMethod.MEDIAPIPE, max_hands=2)

    # Create DMLogn8n interaction system
    interaction_system = DMLogn8nHandInteraction(hand_tracker)

    # Create interaction zones
    interaction_system.create_tavern_interaction_zones()

    # Start tracking
    if await hand_tracker.start_tracking():
        try:
            print("Hand tracking started. Show your hands to the camera!")
            print("Try these gestures:")
            print("- Pinch (thumb and index together)")
            print("- Point (index finger extended)")
            print("- Thumbs up")
            print("- Victory (peace sign)")
            print("- Open palm")
            print("- Fist")
            print("- Swipe left/right")

            # Run for 30 seconds
            await asyncio.sleep(30)

            # Print performance stats
            stats = hand_tracker.get_performance_stats()
            print(f"\nPerformance stats: {stats}")

        except KeyboardInterrupt:
            pass
        finally:
            await hand_tracker.stop_tracking()
    else:
        print("Failed to start hand tracking")


if __name__ == "__main__":
    asyncio.run(main())