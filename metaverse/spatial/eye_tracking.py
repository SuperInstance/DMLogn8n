#!/usr/bin/env python3
"""
DMLogn8n Eye Tracking System - Eye Tracking for Foveated Rendering
Advanced eye tracking system with foveated rendering and attention analysis
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
    import dlib
    from PIL import Image, ImageDraw
except ImportError:
    cv2 = None
    dlib = None
    Image = None

# Eye tracking libraries
try:
    import mediapipe as mp
except ImportError:
    mp = None

try:
    import tobii_research as tr
except ImportError:
    tr = None

# Machine Learning
try:
    import tensorflow as tf
    from sklearn.cluster import KMeans
except ImportError:
    tf = None
    KMeans = None

# Statistical processing
from scipy import stats
from scipy.signal import savgol_filter
from collections import deque


class EyeTrackingMethod(Enum):
    """Eye tracking methods"""
    OPENCV_DLIB = "opencv_dlib"
    MEDIAPIPE_FACE = "mediapipe_face"
    TOBII = "tobii"
    CUSTOM_CNN = "custom_cnn"
    WEBCAM_BASED = "webcam_based"


class GazeType(Enum):
    """Types of gaze patterns"""
    FIXATION = "fixation"
    SACCADE = "saccade"
    SMOOTH_PURSUIT = "smooth_pursuit"
    BLINK = "blink"


class AttentionLevel(Enum):
    """Attention levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FOCUSED = "focused"


@dataclass
class Point2D:
    """2D point for gaze coordinates"""
    x: float
    y: float

    def distance_to(self, other: 'Point2D') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y])


@dataclass
class EyeLandmarks:
    """Eye facial landmarks"""
    eye_id: str  # 'left' or 'right'
    eye_corners: Tuple[Point2D, Point2D]  # Inner and outer corners
    eye_center: Point2D
    top_eyelid: Point2D
    bottom_eyelid: Point2D
    pupil_center: Optional[Point2D] = None
    pupil_radius: Optional[float] = None
    is_blinking: bool = False
    blink_strength: float = 0.0
    eye_openness: float = 1.0  # 0=closed, 1=fully open


@dataclass
class GazePoint:
    """Gaze point with timestamp"""
    point: Point2D
    timestamp: float
    confidence: float
    fixation_duration: float = 0.0


@dataclass
class GazeData:
    """Complete gaze data for both eyes"""
    left_gaze: Optional[GazePoint]
    right_gaze: Optional[GazePoint]
    combined_gaze: Point2D
    timestamp: float
    confidence: float
    gaze_type: GazeType
    attention_level: AttentionLevel


@dataclass
class Fixation:
    """Eye fixation data"""
    center: Point2D
    duration: float
    start_time: float
    end_time: float
    gaze_points: List[GazePoint]
    dispersion: float  # Spatial dispersion of fixation


@dataclass
class Saccade:
    """Eye saccade data"""
    start_point: Point2D
    end_point: Point2D
    duration: float
    amplitude: float
    peak_velocity: float
    timestamp: float


@dataclass
class AttentionMap:
    """Attention heatmap"""
    width: int
    height: int
    data: np.ndarray  # 2D array of attention values
    total_samples: int
    last_updated: float


class EyeDetector:
    """Eye detection and landmark extraction"""

    def __init__(self, method: EyeTrackingMethod = EyeTrackingMethod.MEDIAPIPE_FACE):
        self.method = method
        self.face_detector = None
        self.face_landmarker = None
        self.shape_predictor = None

        # Detection parameters
        self.detection_confidence = 0.5
        self.tracking_confidence = 0.5

        self._initialize_detector()

    def _initialize_detector(self):
        """Initialize eye detector based on method"""
        if self.method == EyeTrackingMethod.MEDIAPIPE_FACE and mp:
            self.face_landmarker = mp.solutions.face_mesh
            mp.solutions.drawing_utils
            mp.solutions.face_mesh_connections
        elif self.method == EyeTrackingMethod.OPENCV_DLIB and dlib:
            # Initialize dlib face detector and shape predictor
            try:
                self.face_detector = dlib.get_frontal_face_detector()
                # In a real implementation, you would load the shape predictor file
                # self.shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
            except Exception as e:
                logging.error(f"Failed to initialize dlib detector: {e}")
        else:
            logging.warning(f"Eye tracking method {self.method.value} not fully supported")

    def detect_eyes(self, frame: np.ndarray) -> Tuple[List[EyeLandmarks], float]:
        """Detect eyes in frame"""
        if self.method == EyeTrackingMethod.MEDIAPIPE_FACE:
            return self._detect_eyes_mediapipe(frame)
        elif self.method == EyeTrackingMethod.OPENCV_DLIB:
            return self._detect_eyes_dlib(frame)
        else:
            return self._detect_eyes_mock(frame)

    def _detect_eyes_mediapipe(self, frame: np.ndarray) -> Tuple[List[EyeLandmarks], float]:
        """Detect eyes using MediaPipe Face Mesh"""
        if not self.face_landmarker:
            return [], 0.0

        eyes = []
        total_confidence = 0.0

        with self.face_landmarker.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence) as face_mesh:

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]

                # Extract eye landmarks
                # MediaPipe face mesh indices for eyes
                # Left eye landmarks: 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246
                # Right eye landmarks: 362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382

                h, w, _ = frame.shape

                # Left eye
                left_eye = self._extract_eye_landmarks(face_landmarks, w, h, 'left')
                if left_eye:
                    eyes.append(left_eye)

                # Right eye
                right_eye = self._extract_eye_landmarks(face_landmarks, w, h, 'right')
                if right_eye:
                    eyes.append(right_eye)

                total_confidence = 1.0  # MediaPipe doesn't provide per-face confidence

        return eyes, total_confidence

    def _extract_eye_landmarks(self, face_landmarks, width: int, height: int,
                              eye_side: str) -> Optional[EyeLandmarks]:
        """Extract eye landmarks from MediaPipe face mesh"""
        try:
            if eye_side == 'left':
                # Left eye landmark indices
                corner_indices = [33, 133]  # Inner and outer corners
                center_indices = [159, 145]  # Top and bottom center
                eyelid_indices = [159, 145]  # Top and bottom eyelid
                iris_indices = [468, 469, 470, 471, 472]  # Iris landmarks
            else:  # right
                # Right eye landmark indices
                corner_indices = [362, 263]  # Inner and outer corners
                center_indices = [386, 374]  # Top and bottom center
                eyelid_indices = [386, 374]  # Top and bottom eyelid
                iris_indices = [473, 474, 475, 476, 477]  # Iris landmarks

            # Convert normalized coordinates to pixel coordinates
            def get_point(idx):
                landmark = face_landmarks.landmark[idx]
                return Point2D(landmark.x * width, landmark.y * height)

            # Extract landmarks
            inner_corner = get_point(corner_indices[0])
            outer_corner = get_point(corner_indices[1])
            eye_center = Point2D(
                (inner_corner.x + outer_corner.x) / 2,
                (inner_corner.y + outer_corner.y) / 2
            )
            top_eyelid = get_point(eyelid_indices[0])
            bottom_eyelid = get_point(eyelid_indices[1])

            # Extract pupil/iris center
            pupil_center = None
            pupil_radius = None
            if all(i < len(face_landmarks.landmark) for i in iris_indices):
                iris_points = [get_point(i) for i in iris_indices]
                iris_x = np.mean([p.x for p in iris_points])
                iris_y = np.mean([p.y for p in iris_points])
                pupil_center = Point2D(iris_x, iris_y)

                # Estimate pupil radius
                distances = [pupil_center.distance_to(p) for p in iris_points]
                pupil_radius = np.mean(distances)

            # Calculate eye openness (vertical distance between eyelids)
            eye_openness = top_eyelid.distance_to(bottom_eyelid) / inner_corner.distance_to(outer_corner)
            eye_openness = np.clip(eye_openness, 0.0, 1.0)

            # Detect blinking
            is_blinking = eye_openness < 0.2
            blink_strength = max(0, 1 - eye_openness / 0.2)

            return EyeLandmarks(
                eye_id=eye_side,
                eye_corners=(inner_corner, outer_corner),
                eye_center=eye_center,
                top_eyelid=top_eyelid,
                bottom_eyelid=bottom_eyelid,
                pupil_center=pupil_center,
                pupil_radius=pupil_radius,
                is_blinking=is_blinking,
                blink_strength=blink_strength,
                eye_openness=eye_openness
            )

        except Exception as e:
            logging.error(f"Error extracting {eye_side} eye landmarks: {e}")
            return None

    def _detect_eyes_dlib(self, frame: np.ndarray) -> Tuple[List[EyeLandmarks], float]:
        """Detect eyes using dlib"""
        if not self.face_detector or not self.shape_predictor:
            return [], 0.0

        eyes = []
        total_confidence = 0.0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector(gray, 1)

        if faces:
            face = faces[0]  # Use first detected face
            shape = self.shape_predictor(gray, face)

            # Extract eye landmarks from dlib's 68-point model
            # Left eye: points 36-41
            # Right eye: points 42-47

            # This would need implementation based on dlib's landmark indices
            # For now, return empty list

        return eyes, total_confidence

    def _detect_eyes_mock(self, frame: np.ndarray) -> Tuple[List[EyeLandmarks], float]:
        """Generate mock eye data for testing"""
        h, w, _ = frame.shape

        # Create mock left eye
        left_eye = EyeLandmarks(
            eye_id='left',
            eye_corners=(
                Point2D(w * 0.35, h * 0.4),  # Inner corner
                Point2D(w * 0.45, h * 0.4)   # Outer corner
            ),
            eye_center=Point2D(w * 0.4, h * 0.4),
            top_eyelid=Point2D(w * 0.4, h * 0.38),
            bottom_eyelid=Point2D(w * 0.4, h * 0.42),
            pupil_center=Point2D(w * 0.4, h * 0.4),
            pupil_radius=15.0,
            is_blinking=False,
            blink_strength=0.0,
            eye_openness=1.0
        )

        # Create mock right eye
        right_eye = EyeLandmarks(
            eye_id='right',
            eye_corners=(
                Point2D(w * 0.55, h * 0.4),  # Inner corner
                Point2D(w * 0.65, h * 0.4)   # Outer corner
            ),
            eye_center=Point2D(w * 0.6, h * 0.4),
            top_eyelid=Point2D(w * 0.6, h * 0.38),
            bottom_eyelid=Point2D(w * 0.6, h * 0.42),
            pupil_center=Point2D(w * 0.6, h * 0.4),
            pupil_radius=15.0,
            is_blinking=False,
            blink_strength=0.0,
            eye_openness=1.0
        )

        # Add some movement
        t = time.time()
        left_eye.pupil_center.x += np.sin(t * 2) * 20
        left_eye.pupil_center.y += np.cos(t * 3) * 10
        right_eye.pupil_center.x += np.sin(t * 2) * 20
        right_eye.pupil_center.y += np.cos(t * 3) * 10

        # Simulate occasional blinking
        if np.random.random() < 0.02:  # 2% chance per frame
            left_eye.is_blinking = True
            left_eye.blink_strength = 1.0
            left_eye.eye_openness = 0.0
            right_eye.is_blinking = True
            right_eye.blink_strength = 1.0
            right_eye.eye_openness = 0.0

        return [left_eye, right_eye], 0.9


class GazeEstimator:
    """Gaze estimation from eye landmarks"""

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calibration parameters
        self.calibration_points = []
        self.calibration_data = {}
        self.is_calibrated = False

        # Gaze estimation model
        self.gaze_model = None
        self._initialize_gaze_model()

    def _initialize_gaze_model(self):
        """Initialize gaze estimation model"""
        # Simple linear model for gaze estimation
        # In a real implementation, this would use more sophisticated methods
        self.gaze_model = {
            'left_eye_offset': {'x': 0, 'y': 0},
            'right_eye_offset': {'x': 0, 'y': 0},
            'scale_x': 1.0,
            'scale_y': 1.0
        }

    def estimate_gaze(self, eyes: List[EyeLandmarks]) -> Optional[GazeData]:
        """Estimate gaze point from eye landmarks"""
        if len(eyes) < 1:
            return None

        timestamp = time.time()
        gaze_points = []

        for eye in eyes:
            if eye.pupil_center:
                # Simple gaze estimation based on pupil position
                gaze_point = self._estimate_gaze_from_eye(eye)
                gaze_points.append(gaze_point)

        if not gaze_points:
            return None

        # Calculate combined gaze point
        combined_x = np.mean([gp.point.x for gp in gaze_points])
        combined_y = np.mean([gp.point.y for gp in gaze_points])
        combined_gaze = Point2D(combined_x, combined_y)

        # Determine gaze type
        gaze_type = self._classify_gaze_type(gaze_points)

        # Calculate attention level
        attention_level = self._calculate_attention_level(eyes, gaze_points)

        # Create gaze data
        left_gaze = gaze_points[0] if len(gaze_points) > 0 and gaze_points[0] else None
        right_gaze = gaze_points[1] if len(gaze_points) > 1 else None

        return GazeData(
            left_gaze=left_gaze,
            right_gaze=right_gaze,
            combined_gaze=combined_gaze,
            timestamp=timestamp,
            confidence=np.mean([gp.confidence for gp in gaze_points]) if gaze_points else 0.0,
            gaze_type=gaze_type,
            attention_level=attention_level
        )

    def _estimate_gaze_from_eye(self, eye: EyeLandmarks) -> GazePoint:
        """Estimate gaze point from single eye"""
        if not eye.pupil_center:
            return GazePoint(Point2D(0, 0), time.time(), 0.0)

        # Calculate pupil offset from eye center
        pupil_offset_x = eye.pupil_center.x - eye.eye_center.x
        pupil_offset_y = eye.pupil_center.y - eye.eye_center.y

        # Normalize by eye size
        eye_width = eye.eye_corners[0].distance_to(eye.eye_corners[1])
        normalized_x = pupil_offset_x / eye_width
        normalized_y = pupil_offset_y / eye_width

        # Apply calibration and scaling
        gaze_x = (normalized_x * self.gaze_model['scale_x'] * 500 +
                  self.screen_width / 2 + self.gaze_model['left_eye_offset']['x'])
        gaze_y = (normalized_y * self.gaze_model['scale_y'] * 500 +
                  self.screen_height / 2 + self.gaze_model['left_eye_offset']['y'])

        # Clamp to screen bounds
        gaze_x = np.clip(gaze_x, 0, self.screen_width)
        gaze_y = np.clip(gaze_y, 0, self.screen_height)

        return GazePoint(
            point=Point2D(gaze_x, gaze_y),
            timestamp=time.time(),
            confidence=0.8 if not eye.is_blinking else 0.1
        )

    def _classify_gaze_type(self, gaze_points: List[GazePoint]) -> GazeType:
        """Classify gaze type based on movement patterns"""
        # This is a simplified classification
        # In a real implementation, this would analyze velocity and acceleration patterns

        if len(gaze_points) < 2:
            return GazeType.FIXATION

        # Calculate velocity between recent points
        velocities = []
        for i in range(1, len(gaze_points)):
            dt = gaze_points[i].timestamp - gaze_points[i-1].timestamp
            if dt > 0:
                distance = gaze_points[i].point.distance_to(gaze_points[i-1].point)
                velocity = distance / dt
                velocities.append(velocity)

        if not velocities:
            return GazeType.FIXATION

        avg_velocity = np.mean(velocities)

        # Classification thresholds (pixels per second)
        if avg_velocity < 30:
            return GazeType.FIXATION
        elif avg_velocity < 300:
            return GazeType.SMOOTH_PURSUIT
        else:
            return GazeType.SACCADE

    def _calculate_attention_level(self, eyes: List[EyeLandmarks],
                                 gaze_points: List[GazePoint]) -> AttentionLevel:
        """Calculate attention level from eye and gaze data"""
        # Check for blinks
        blink_ratio = sum(1 for eye in eyes if eye.is_blinking) / len(eyes) if eyes else 0

        # Check gaze stability
        if len(gaze_points) >= 2:
            gaze_variance = np.var([gp.point.x for gp in gaze_points] +
                                  [gp.point.y for gp in gaze_points])
        else:
            gaze_variance = 0

        # Calculate attention score
        attention_score = 1.0 - blink_ratio * 0.5 - min(gaze_variance / 10000, 0.5)

        if attention_score > 0.8:
            return AttentionLevel.HIGH
        elif attention_score > 0.6:
            return AttentionLevel.MEDIUM
        elif attention_score > 0.3:
            return AttentionLevel.LOW
        else:
            return AttentionLevel.FOCUSED

    def calibrate(self, calibration_points: List[Point2D],
                 recorded_gaze_data: List[List[GazeData]]) -> bool:
        """Calibrate gaze estimation"""
        if len(calibration_points) != len(recorded_gaze_data):
            return False

        # Simple calibration: average offsets
        all_offsets_x = []
        all_offsets_y = []

        for target_point, gaze_data_list in zip(calibration_points, recorded_gaze_data):
            if gaze_data_list:
                avg_gaze_x = np.mean([gd.combined_gaze.x for gd in gaze_data_list])
                avg_gaze_y = np.mean([gd.combined_gaze.y for gd in gaze_data_list])

                offset_x = target_point.x - avg_gaze_x
                offset_y = target_point.y - avg_gaze_y

                all_offsets_x.append(offset_x)
                all_offsets_y.append(offset_y)

        if all_offsets_x and all_offsets_y:
            self.gaze_model['left_eye_offset']['x'] = np.mean(all_offsets_x)
            self.gaze_model['left_eye_offset']['y'] = np.mean(all_offsets_y)
            self.gaze_model['right_eye_offset']['x'] = np.mean(all_offsets_x)
            self.gaze_model['right_eye_offset']['y'] = np.mean(all_offsets_y)

            self.is_calibrated = True
            return True

        return False


class FoveatedRenderer:
    """Foveated rendering based on eye tracking"""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

        # Foveated rendering parameters
        self.fovea_radius = 100  # High quality region radius
        self.periphery_radius = 300  # Medium quality region radius
        self.quality_levels = {
            'fovea': 1.0,      # Full resolution
            'parafovea': 0.6,  # 60% resolution
            'periphery': 0.3   # 30% resolution
        }

        # Quality map for current gaze
        self.quality_map = np.ones((height, width))
        self.current_gaze = Point2D(width // 2, height // 2)

    def update_gaze(self, gaze_point: Point2D):
        """Update current gaze point"""
        self.current_gaze = gaze_point
        self._update_quality_map()

    def _update_quality_map(self):
        """Update quality map based on gaze position"""
        # Create distance map from gaze point
        y_coords, x_coords = np.ogrid[:self.height, :self.width]
        distances = np.sqrt((x_coords - self.current_gaze.x)**2 +
                           (y_coords - self.current_gaze.y)**2)

        # Create quality map
        self.quality_map = np.ones((self.height, self.width))

        # Fovea region - full quality
        fovea_mask = distances <= self.fovea_radius
        self.quality_map[fovea_mask] = self.quality_levels['fovea']

        # Parafovea region - medium quality
        parafovea_mask = (distances > self.fovea_radius) & (distances <= self.periphery_radius)
        self.quality_map[parafovea_mask] = self.quality_levels['parafovea']

        # Periphery region - low quality
        periphery_mask = distances > self.periphery_radius
        self.quality_map[periphery_mask] = self.quality_levels['periphery']

    def get_quality_map(self) -> np.ndarray:
        """Get current quality map"""
        return self.quality_map.copy()

    def apply_foveated_sampling(self, image: np.ndarray) -> np.ndarray:
        """Apply foveated sampling to image"""
        if image.shape[:2] != (self.height, self.width):
            return image

        # Create foveated image
        foveated_image = np.zeros_like(image)

        # Apply different sampling rates based on quality map
        for y in range(0, self.height, 2):
            for x in range(0, self.width, 2):
                quality = self.quality_map[y, x]

                if quality == self.quality_levels['fovea']:
                    # Full resolution
                    foveated_image[y, x] = image[y, x]
                    if x + 1 < self.width:
                        foveated_image[y, x + 1] = image[y, x + 1]
                    if y + 1 < self.height:
                        foveated_image[y + 1, x] = image[y + 1, x]
                        if x + 1 < self.width:
                            foveated_image[y + 1, x + 1] = image[y + 1, x + 1]

                elif quality == self.quality_levels['parafovea']:
                    # 2x2 sampling
                    avg_color = np.mean(image[y:y+2, x:x+2], axis=(0, 1))
                    foveated_image[y:y+2, x:x+2] = avg_color

                else:
                    # 4x4 sampling
                    avg_color = np.mean(image[y:y+4, x:x+4], axis=(0, 1))
                    if y + 4 <= self.height and x + 4 <= self.width:
                        foveated_image[y:y+4, x:x+4] = avg_color

        return foveated_image


class AttentionAnalyzer:
    """Attention pattern analysis"""

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Gaze history
        self.gaze_history = deque(maxlen=1000)  # Last 1000 gaze points
        self.fixations = []
        self.saccades = []

        # Attention heatmap
        self.attention_map = AttentionMap(
            width=screen_width // 10,  # Lower resolution heatmap
            height=screen_height // 10,
            data=np.zeros((screen_height // 10, screen_width // 10)),
            total_samples=0,
            last_updated=time.time()
        )

        # Analysis parameters
        self.fixation_threshold = 30  # pixels
        self.fixation_min_duration = 0.1  # seconds

    def add_gaze_point(self, gaze_data: GazeData):
        """Add gaze point for analysis"""
        if gaze_data.combined_gaze:
            self.gaze_history.append(gaze_data)
            self._update_attention_map(gaze_data.combined_gaze)
            self._detect_fixations_and_saccades()

    def _update_attention_map(self, gaze_point: Point2D):
        """Update attention heatmap"""
        # Convert to heatmap coordinates
        heatmap_x = int(gaze_point.x / 10)
        heatmap_y = int(gaze_point.y / 10)

        if 0 <= heatmap_x < self.attention_map.width and 0 <= heatmap_y < self.attention_map.height:
            # Add Gaussian kernel around gaze point
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    hx = heatmap_x + dx
                    hy = heatmap_y + dy

                    if 0 <= hx < self.attention_map.width and 0 <= hy < self.attention_map.height:
                        distance = np.sqrt(dx**2 + dy**2)
                        weight = np.exp(-distance**2 / 2)  # Gaussian weight
                        self.attention_map.data[hy, hx] += weight

            self.attention_map.total_samples += 1
            self.attention_map.last_updated = time.time()

    def _detect_fixations_and_saccades(self):
        """Detect fixations and saccades in gaze history"""
        if len(self.gaze_history) < 3:
            return

        # Get recent gaze points
        recent_gaze = list(self.gaze_history)[-10:]  # Last 10 points

        # Check for fixation (low velocity)
        if len(recent_gaze) >= 2:
            current_point = recent_gaze[-1].combined_gaze
            previous_point = recent_gaze[-2].combined_gaze
            distance = current_point.distance_to(previous_point)
            time_diff = recent_gaze[-1].timestamp - recent_gaze[-2].timestamp

            if time_diff > 0:
                velocity = distance / time_diff

                if velocity < 30:  # Low velocity threshold
                    # Potential fixation
                    if not self.fixations or self.fixations[-1].end_time < recent_gaze[-2].timestamp:
                        # Start new fixation
                        fixation = Fixation(
                            center=current_point,
                            duration=0,
                            start_time=recent_gaze[-1].timestamp,
                            end_time=recent_gaze[-1].timestamp,
                            gaze_points=[recent_gaze[-1]],
                            dispersion=0
                        )
                        self.fixations.append(fixation)
                    else:
                        # Update existing fixation
                        current_fixation = self.fixations[-1]
                        current_fixation.end_time = recent_gaze[-1].timestamp
                        current_fixation.duration = current_fixation.end_time - current_fixation.start_time
                        current_fixation.gaze_points.append(recent_gaze[-1])

                        # Recalculate center and dispersion
                        points = [gp.combined_gaze for gp in current_fixation.gaze_points]
                        center_x = np.mean([p.x for p in points])
                        center_y = np.mean([p.y for p in points])
                        current_fixation.center = Point2D(center_x, center_y)

                        distances = [p.distance_to(current_fixation.center) for p in points]
                        current_fixation.dispersion = np.std(distances)

    def get_attention_hotspots(self, threshold: float = 0.5) -> List[Tuple[Point2D, float]]:
        """Get attention hotspots from heatmap"""
        # Normalize attention map
        if self.attention_map.total_samples > 0:
            normalized_map = self.attention_map.data / self.attention_map.total_samples
        else:
            normalized_map = self.attention_map.data

        # Find hotspots above threshold
        hotspots = []
        max_value = np.max(normalized_map)

        if max_value > 0:
            threshold_value = max_value * threshold

            # Find connected regions above threshold
            from scipy import ndimage
            binary_map = normalized_map > threshold_value
            labeled_map, num_features = ndimage.label(binary_map)

            for i in range(1, num_features + 1):
                region_mask = labeled_map == i
                region_values = normalized_map[region_mask]

                if len(region_values) > 0:
                    # Calculate center of mass
                    y_coords, x_coords = np.where(region_mask)
                    center_y = np.mean(y_coords) * 10  # Convert back to screen coordinates
                    center_x = np.mean(x_coords) * 10
                    intensity = np.mean(region_values)

                    hotspots.append((Point2D(center_x, center_y), intensity))

        # Sort by intensity
        hotspots.sort(key=lambda x: x[1], reverse=True)

        return hotspots

    def get_attention_statistics(self) -> Dict:
        """Get attention analysis statistics"""
        stats = {
            'total_gaze_points': len(self.gaze_history),
            'total_fixations': len(self.fixations),
            'avg_fixation_duration': 0,
            'total_saccades': len(self.saccades),
            'attention_hotspots': 0,
            'attention_coverage': 0
        }

        if self.fixations:
            stats['avg_fixation_duration'] = np.mean([f.duration for f in self.fixations])

        hotspots = self.get_attention_hotspots(0.3)
        stats['attention_hotspots'] = len(hotspots)

        # Calculate attention coverage (percentage of screen with attention)
        if self.attention_map.total_samples > 0:
            nonzero_pixels = np.count_nonzero(self.attention_map.data)
            total_pixels = self.attention_map.width * self.attention_map.height
            stats['attention_coverage'] = (nonzero_pixels / total_pixels) * 100

        return stats


class EyeTracker:
    """Main eye tracking system"""

    def __init__(self, method: EyeTrackingMethod = EyeTrackingMethod.MEDIAPIPE_FACE,
                 screen_width: int = 1920, screen_height: int = 1080):
        self.method = method
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Core components
        self.eye_detector = EyeDetector(method)
        self.gaze_estimator = GazeEstimator(screen_width, screen_height)
        self.foveated_renderer = FoveatedRenderer(screen_width, screen_height)
        self.attention_analyzer = AttentionAnalyzer(screen_width, screen_height)

        # Tracking state
        self.is_tracking = False
        self.current_gaze_data = None
        self.tracking_thread = None
        self.camera = None

        # Event callbacks
        self.event_callbacks: Dict[str, Callable] = {}

        # Performance tracking
        self.frame_count = 0
        self.processing_times = deque(maxlen=30)

        self.logger = logging.getLogger(__name__)

    async def start_tracking(self, camera_source: int = 0) -> bool:
        """Start eye tracking"""
        try:
            self.logger.info(f"Starting eye tracking with camera: {camera_source}")

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

            self.is_tracking = True

            # Start processing thread
            self.tracking_thread = threading.Thread(target=self._tracking_loop)
            self.tracking_thread.daemon = True
            self.tracking_thread.start()

            self.logger.info("Eye tracking started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start eye tracking: {e}")
            return False

    def _tracking_loop(self):
        """Main tracking loop"""
        while self.is_tracking:
            start_time = time.time()

            # Capture frame
            frame = self._capture_frame()
            if frame is not None:
                # Process frame for eye tracking
                gaze_data = self._process_frame(frame)
                if gaze_data:
                    self.current_gaze_data = gaze_data

                    # Update foveated rendering
                    self.foveated_renderer.update_gaze(gaze_data.combined_gaze)

                    # Update attention analysis
                    self.attention_analyzer.add_gaze_point(gaze_data)

                    # Trigger events
                    self._trigger_events(gaze_data)

            # Track performance
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)

            # Control frame rate
            time.sleep(max(0, 0.033 - processing_time))  # Target 30 FPS

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

    def _process_frame(self, frame: np.ndarray) -> Optional[GazeData]:
        """Process frame for eye tracking"""
        # Detect eyes
        eyes, confidence = self.eye_detector.detect_eyes(frame)

        if not eyes:
            return None

        # Estimate gaze
        gaze_data = self.gaze_estimator.estimate_gaze(eyes)

        return gaze_data

    def _trigger_events(self, gaze_data: GazeData):
        """Trigger eye tracking events"""
        # Trigger gaze update event
        if 'gaze_update' in self.event_callbacks:
            try:
                self.event_callbacks['gaze_update'](gaze_data)
            except Exception as e:
                self.logger.error(f"Error in gaze_update callback: {e}")

        # Trigger attention level change event
        if hasattr(self, '_last_attention_level'):
            if self._last_attention_level != gaze_data.attention_level:
                if 'attention_change' in self.event_callbacks:
                    try:
                        self.event_callbacks['attention_change'](gaze_data.attention_level)
                    except Exception as e:
                        self.logger.error(f"Error in attention_change callback: {e}")
        self._last_attention_level = gaze_data.attention_level

    def register_callback(self, event_type: str, callback: Callable):
        """Register event callback"""
        self.event_callbacks[event_type] = callback
        self.logger.info(f"Registered callback for event: {event_type}")

    async def calibrate(self) -> bool:
        """Run calibration routine"""
        self.logger.info("Starting eye tracker calibration")

        # Define calibration points (9-point calibration)
        screen_w, screen_h = self.screen_width, self.screen_height
        margin = 100

        calibration_points = [
            Point2D(margin, margin),  # Top-left
            Point2D(screen_w // 2, margin),  # Top-center
            Point2D(screen_w - margin, margin),  # Top-right
            Point2D(margin, screen_h // 2),  # Center-left
            Point2D(screen_w // 2, screen_h // 2),  # Center
            Point2D(screen_w - margin, screen_h // 2),  # Center-right
            Point2D(margin, screen_h - margin),  # Bottom-left
            Point2D(screen_w // 2, screen_h - margin),  # Bottom-center
            Point2D(screen_w - margin, screen_h - margin),  # Bottom-right
        ]

        # Record gaze data for each calibration point
        recorded_data = []
        collection_time = 2.0  # seconds per point

        for i, point in enumerate(calibration_points):
            print(f"Look at point {i+1}/9: ({int(point.x)}, {int(point.y)})")
            time.sleep(1.0)  # Give user time to look at point

            # Collect gaze data
            point_data = []
            start_time = time.time()
            while time.time() - start_time < collection_time:
                if self.current_gaze_data:
                    point_data.append(self.current_gaze_data)
                time.sleep(0.1)

            recorded_data.append(point_data)
            print(f"Recorded {len(point_data)} gaze samples")

        # Perform calibration
        success = self.gaze_estimator.calibrate(calibration_points, recorded_data)

        if success:
            self.logger.info("Calibration completed successfully")
        else:
            self.logger.error("Calibration failed")

        return success

    async def stop_tracking(self):
        """Stop eye tracking"""
        self.is_tracking = False

        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)

        if self.camera:
            self.camera.release()

        self.logger.info("Eye tracking stopped")

    def get_current_gaze(self) -> Optional[GazeData]:
        """Get current gaze data"""
        return self.current_gaze_data

    def get_foveated_quality_map(self) -> np.ndarray:
        """Get foveated rendering quality map"""
        return self.foveated_renderer.get_quality_map()

    def get_attention_heatmap(self) -> np.ndarray:
        """Get attention heatmap"""
        return self.attention_analyzer.attention_map.data

    def get_attention_hotspots(self) -> List[Tuple[Point2D, float]]:
        """Get current attention hotspots"""
        return self.attention_analyzer.get_attention_hotspots()

    def draw_gaze_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw gaze overlay on frame"""
        if not self.current_gaze_data or not cv2:
            return frame

        gaze_point = self.current_gaze_data.combined_gaze

        # Draw gaze point
        cv2.circle(frame, (int(gaze_point.x), int(gaze_point.y)), 10, (0, 255, 0), -1)

        # Draw confidence indicator
        confidence = self.current_gaze_data.confidence
        color = (0, int(255 * confidence), int(255 * (1 - confidence)))
        cv2.circle(frame, (int(gaze_point.x), int(gaze_point.y)), 20, color, 2)

        # Draw attention level
        attention_text = f"Attention: {self.current_gaze_data.attention_level.value}"
        cv2.putText(frame, attention_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
        fps = 1.0 / avg_processing_time if avg_processing_time > 0 else 0

        attention_stats = self.attention_analyzer.get_attention_statistics()

        return {
            'fps': fps,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'frame_count': self.frame_count,
            'tracking_method': self.method.value,
            'is_calibrated': self.gaze_estimator.is_calibrated,
            'current_gaze': asdict(self.current_gaze_data.combined_gaze) if self.current_gaze_data else None,
            'attention_stats': attention_stats
        }


async def main():
    """Main function to test eye tracking system"""
    logging.basicConfig(level=logging.INFO)

    # Create eye tracker
    eye_tracker = EyeTracker(method=EyeTrackingMethod.MEDIAPIPE_FACE,
                            screen_width=1920, screen_height=1080)

    # Register callbacks
    def on_gaze_update(gaze_data: GazeData):
        print(f"Gaze: ({int(gaze_data.combined_gaze.x)}, {int(gaze_data.combined_gaze.y)}) "
              f"Attention: {gaze_data.attention_level.value}")

    def on_attention_change(attention_level: AttentionLevel):
        print(f"Attention level changed to: {attention_level.value}")

    eye_tracker.register_callback('gaze_update', on_gaze_update)
    eye_tracker.register_callback('attention_change', on_attention_change)

    # Start tracking
    if await eye_tracker.start_tracking():
        try:
            print("Eye tracking started. Look around the screen!")

            # Calibrate after a few seconds
            await asyncio.sleep(3)
            print("\nStarting calibration...")
            calibration_success = await eye_tracker.calibrate()

            if calibration_success:
                print("Calibration successful! Eye tracking is now active.")
            else:
                print("Calibration failed. Eye tracking will use default settings.")

            # Run for 30 seconds
            await asyncio.sleep(30)

            # Print performance stats
            stats = eye_tracker.get_performance_stats()
            print(f"\nPerformance stats: {stats}")

            # Print attention analysis
            hotspots = eye_tracker.get_attention_hotspots()
            print(f"\nAttention hotspots ({len(hotspots)} found):")
            for i, (point, intensity) in enumerate(hotspots[:5]):
                print(f"  {i+1}. Position: ({int(point.x)}, {int(point.y)}), Intensity: {intensity:.3f}")

        except KeyboardInterrupt:
            pass
        finally:
            await eye_tracker.stop_tracking()
    else:
        print("Failed to start eye tracking")


if __name__ == "__main__":
    asyncio.run(main())