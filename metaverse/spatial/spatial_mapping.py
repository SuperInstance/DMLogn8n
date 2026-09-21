#!/usr/bin/env python3
"""
DMLogn8n Spatial Mapping System - Real-time Environment Scanning and Mapping
Advanced spatial mapping system that scans and maps real environments for mixed reality
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

# 3D Processing Libraries
try:
    import open3d as o3d
    from scipy.spatial import KDTree
    from scipy.spatial.transform import Rotation
    import numpy.linalg as la
except ImportError:
    o3d = None
    KDTree = None
    Rotation = None
    la = None

# Depth sensing libraries
try:
    import pyrealsense2 as rs
except ImportError:
    rs = None

# Machine Learning
try:
    import tensorflow as tf
    from sklearn.cluster import DBSCAN
except ImportError:
    tf = None
    DBSCAN = None

# Real-time processing
try:
    import threading
    import queue
    from collections import deque
except ImportError:
    threading = None
    queue = None
    deque = None


class SensorType(Enum):
    """Types of spatial sensors"""
    RGB_CAMERA = "rgb_camera"
    DEPTH_CAMERA = "depth_camera"
    STEREO_CAMERA = "stereo_camera"
    LIDAR = "lidar"
    TIME_OF_FLIGHT = "time_of_flight"
   STRUCTURED_LIGHT = "structured_light"


class SurfaceType(Enum):
    """Types of detected surfaces"""
    WALL = "wall"
    FLOOR = "floor"
    CEILING = "ceiling"
    TABLE = "table"
    CHAIR = "chair"
    DOOR = "door"
    WINDOW = "window"
    UNKNOWN = "unknown"


@dataclass
class Point3D:
    """3D point representation"""
    x: float
    y: float
    z: float
    color: Optional[Tuple[int, int, int]] = None
    normal: Optional['Vector3'] = None
    confidence: float = 1.0

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Point3D':
        return cls(x=arr[0], y=arr[1], z=arr[2])

    def distance_to(self, other: 'Point3D') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class Vector3:
    """3D Vector for normals and directions"""
    x: float
    y: float
    z: float

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def magnitude(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3(0, 0, 0)

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass
class Plane3D:
    """3D plane representation"""
    normal: Vector3
    distance: float  # Distance from origin along normal
    points: List[Point3D] = None

    def __post_init__(self):
        if self.points is None:
            self.points = []

    def distance_to_point(self, point: Point3D) -> float:
        """Calculate signed distance from point to plane"""
        point_vec = Vector3(point.x, point.y, point.z)
        return point_vec.dot(self.normal) - self.distance

    def project_point(self, point: Point3D) -> Point3D:
        """Project point onto plane"""
        distance = self.distance_to_point(point)
        projected = Point3D(
            point.x - distance * self.normal.x,
            point.y - distance * self.normal.y,
            point.z - distance * self.normal.z
        )
        return projected


@dataclass
class BoundingBox3D:
    """3D bounding box"""
    min_point: Point3D
    max_point: Point3D

    def get_center(self) -> Point3D:
        """Get center of bounding box"""
        return Point3D(
            (self.min_point.x + self.max_point.x) / 2,
            (self.min_point.y + self.max_point.y) / 2,
            (self.min_point.z + self.max_point.z) / 2
        )

    def get_dimensions(self) -> Tuple[float, float, float]:
        """Get dimensions of bounding box"""
        return (
            self.max_point.x - self.min_point.x,
            self.max_point.y - self.min_point.y,
            self.max_point.z - self.min_point.z
        )


@dataclass
class SpatialSurface:
    """Detected surface in the environment"""
    surface_id: str
    surface_type: SurfaceType
    plane: Plane3D
    bounding_box: BoundingBox3D
    points: List[Point3D]
    confidence: float
    timestamp: float


@dataclass
class SpatialMap:
    """Complete spatial map of environment"""
    map_id: str
    points: List[Point3D]
    surfaces: List[SpatialSurface]
    coordinate_frame: np.ndarray  # 4x4 transformation matrix
    timestamp: float
    quality_score: float


class PointCloudProcessor:
    """Process and analyze point clouds"""

    def __init__(self, voxel_size: float = 0.01):
        self.voxel_size = voxel_size
        self.min_points_for_plane = 100
        self.plane_distance_threshold = 0.02
        self.normal_radius = 0.1

    def filter_outliers(self, points: List[Point3D]) -> List[Point3D]:
        """Remove outlier points using statistical filtering"""
        if len(points) < 10:
            return points

        point_arrays = np.array([p.to_array() for p in points])

        # Calculate distances to k-nearest neighbors
        if o3d:
            # Use Open3D for outlier removal
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(point_arrays)

            # Statistical outlier removal
            cl, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
            filtered_points = [points[i] for i in ind]
            return filtered_points
        else:
            # Simple statistical filtering
            distances = []
            k = min(10, len(points) - 1)

            for i, point in enumerate(points):
                point_array = point.to_array()
                # Calculate distances to k nearest neighbors
                other_points = np.delete(point_arrays, i, axis=0)
                if len(other_points) >= k:
                    dists = np.linalg.norm(other_points - point_array, axis=1)
                    nearest_k = np.partition(dists, k)[:k]
                    distances.append(np.mean(nearest_k))

            # Filter points based on distance statistics
            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            threshold = mean_dist + 2 * std_dist

            filtered_points = []
            for i, dist in enumerate(distances):
                if dist <= threshold:
                    filtered_points.append(points[i])

            return filtered_points

    def voxel_downsample(self, points: List[Point3D]) -> List[Point3D]:
        """Downsample point cloud using voxel grid"""
        if len(points) < 2:
            return points

        point_arrays = np.array([p.to_array() for p in points])

        if o3d:
            # Use Open3D for voxel downsampling
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(point_arrays)
            pcd_down = pcd.voxel_down_sample(voxel_size=self.voxel_size)

            down_points = pcd_down.points
            return [Point3D(p[0], p[1], p[2]) for p in down_points]
        else:
            # Simple voxel grid implementation
            # Create voxel grid
            min_coords = np.min(point_arrays, axis=0)
            max_coords = np.max(point_arrays, axis=0)

            voxel_dims = ((max_coords - min_coords) / self.voxel_size).astype(int) + 1

            # Create dictionary to store points per voxel
            voxel_dict = {}

            for i, point in enumerate(points):
                voxel_coords = ((point.to_array() - min_coords) / self.voxel_size).astype(int)
                voxel_key = tuple(voxel_coords)

                if voxel_key not in voxel_dict:
                    voxel_dict[voxel_key] = []
                voxel_dict[voxel_key].append(i)

            # Average points in each voxel
            downsampled_points = []
            for voxel_indices in voxel_dict.values():
                if voxel_indices:
                    avg_point = np.mean([points[i].to_array() for i in voxel_indices], axis=0)
                    avg_color = None
                    if points[voxel_indices[0]].color:
                        avg_color = tuple(np.mean([points[i].color for i in voxel_indices], axis=0).astype(int))

                    downsampled_points.append(Point3D(avg_point[0], avg_point[1], avg_point[2], avg_color))

            return downsampled_points

    def estimate_normals(self, points: List[Point3D]) -> List[Point3D]:
        """Estimate surface normals for points"""
        point_arrays = np.array([p.to_array() for p in points])

        if o3d:
            # Use Open3D for normal estimation
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(point_arrays)
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
                radius=self.normal_radius, max_nn=30))

            normals = np.asarray(pcd.normals)
            for i, point in enumerate(points):
                if i < len(normals):
                    point.normal = Vector3(normals[i][0], normals[i][1], normals[i][2])
        else:
            # Simple normal estimation using local neighborhoods
            tree = KDTree(point_arrays) if KDTree else None

            for i, point in enumerate(points):
                if tree:
                    # Find nearest neighbors
                    distances, indices = tree.query(point.to_array(), k=min(10, len(points)))
                    neighbor_points = [points[j] for j in indices[1:] if j != i]  # Exclude self

                    if len(neighbor_points) >= 3:
                        # Calculate covariance matrix
                        neighbor_arrays = np.array([p.to_array() for p in neighbor_points])
                        centroid = np.mean(neighbor_arrays, axis=0)
                        cov_matrix = np.cov((neighbor_arrays - centroid).T)

                        # Eigendecomposition to find normal
                        eigenvalues, eigenvectors = la.eig(cov_matrix)
                        normal_vector = eigenvectors[:, np.argmin(eigenvalues)]

                        point.normal = Vector3(normal_vector[0], normal_vector[1], normal_vector[2])

        return points

    def detect_planes(self, points: List[Point3D]) -> List[Plane3D]:
        """Detect planar surfaces in point cloud"""
        if len(points) < self.min_points_for_plane:
            return []

        planes = []
        remaining_points = points.copy()

        # Iterative plane detection using RANSAC
        max_iterations = 100
        plane_count = 0
        max_planes = 10

        while len(remaining_points) >= self.min_points_for_plane and plane_count < max_planes:
            best_plane = None
            best_inliers = []

            # RANSAC plane fitting
            for _ in range(max_iterations):
                if len(remaining_points) < 3:
                    break

                # Randomly sample 3 points
                sample_indices = np.random.choice(len(remaining_points), 3, replace=False)
                sample_points = [remaining_points[i] for i in sample_indices]

                # Calculate plane from 3 points
                p1, p2, p3 = sample_points
                v1 = Vector3(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)
                v2 = Vector3(p3.x - p1.x, p3.y - p1.y, p3.z - p1.z)

                # Calculate normal using cross product
                normal = Vector3(
                    v1.y * v2.z - v1.z * v2.y,
                    v1.z * v2.x - v1.x * v2.z,
                    v1.x * v2.y - v1.y * v2.x
                ).normalize()

                # Calculate distance from origin
                distance = normal.x * p1.x + normal.y * p1.y + normal.z * p1.z

                plane = Plane3D(normal, distance)

                # Find inliers
                inliers = []
                for point in remaining_points:
                    if abs(plane.distance_to_point(point)) < self.plane_distance_threshold:
                        inliers.append(point)

                # Keep best plane
                if len(inliers) > len(best_inliers):
                    best_plane = plane
                    best_inliers = inliers

            if best_plane and len(best_inliers) >= self.min_points_for_plane:
                best_plane.points = best_inliers
                planes.append(best_plane)

                # Remove inliers from remaining points
                for point in best_inliers:
                    if point in remaining_points:
                        remaining_points.remove(point)

                plane_count += 1
            else:
                break

        return planes

    def classify_surface(self, plane: Plane3D, all_points: List[Point3D]) -> SurfaceType:
        """Classify surface type based on plane properties"""
        if not plane.points:
            return SurfaceType.UNKNOWN

        # Calculate plane properties
        normal = plane.normal

        # Calculate bounding box
        point_arrays = np.array([p.to_array() for p in plane.points])
        min_coords = np.min(point_arrays, axis=0)
        max_coords = np.max(point_arrays, axis=0)

        dimensions = max_coords - min_coords
        area = dimensions[0] * dimensions[1] if len(dimensions) >= 2 else 0

        # Classify based on normal orientation and size
        # Floor: normal pointing up, large area
        if normal.y > 0.8 and area > 2.0:
            return SurfaceType.FLOOR

        # Ceiling: normal pointing down, large area
        if normal.y < -0.8 and area > 2.0:
            return SurfaceType.CEILING

        # Wall: normal roughly horizontal, large area
        if abs(normal.y) < 0.3 and area > 1.0:
            return SurfaceType.WALL

        # Table: horizontal surface at table height
        if abs(normal.y) > 0.7 and 0.6 < min_coords[1] < 1.2 and area > 0.5:
            return SurfaceType.TABLE

        # Chair: smaller horizontal surface
        if abs(normal.y) > 0.7 and area < 1.0:
            return SurfaceType.CHAIR

        # Door: vertical rectangle
        if abs(normal.y) < 0.3 and 0.5 < dimensions[0] / dimensions[1] < 3.0:
            return SurfaceType.DOOR

        # Window: vertical, typically larger than door but thin
        if abs(normal.y) < 0.3 and dimensions[2] < 0.1:
            return SurfaceType.WINDOW

        return SurfaceType.UNKNOWN


class SpatialSensor:
    """Abstract base class for spatial sensors"""

    def __init__(self, sensor_id: str, sensor_type: SensorType):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.is_active = False
        self.extrinsics = np.eye(4)  # Sensor pose in world coordinates
        self.intrinsics = None  # Camera intrinsics for RGB/depth sensors

    async def start_capture(self) -> bool:
        """Start capturing data from sensor"""
        raise NotImplementedError

    async def stop_capture(self):
        """Stop capturing data from sensor"""
        raise NotImplementedError

    async def get_frame(self) -> Optional[Any]:
        """Get next frame from sensor"""
        raise NotImplementedError

    def set_extrinsics(self, transformation_matrix: np.ndarray):
        """Set sensor extrinsic parameters"""
        self.extrinsics = transformation_matrix

    def set_intrinsics(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        """Set camera intrinsic parameters"""
        self.intrinsics = {
            'camera_matrix': camera_matrix,
            'dist_coeffs': dist_coeffs
        }


class RGBDSensor(SpatialSensor):
    """RGB-D sensor combining color and depth information"""

    def __init__(self, sensor_id: str, camera_id: int = 0):
        super().__init__(sensor_id, SensorType.DEPTH_CAMERA)
        self.camera_id = camera_id
        self.camera = None
        self.depth_scale = 1000.0  # Depth values in mm

    async def start_capture(self) -> bool:
        """Start RGB-D camera capture"""
        try:
            if rs:
                # Use Intel RealSense
                self.pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                self.pipeline.start(config)
                self.is_active = True
                logging.info(f"RealSense camera {self.sensor_id} started")
                return True
            elif cv2:
                # Fallback to regular webcam (mock depth)
                self.camera = cv2.VideoCapture(self.camera_id)
                if self.camera.isOpened():
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 30)
                    self.is_active = True
                    logging.info(f"Webcam {self.sensor_id} started (mock depth)")
                    return True
                else:
                    logging.error(f"Failed to open camera {self.camera_id}")
                    return False
            else:
                # Mock camera for testing
                self.is_active = True
                logging.info(f"Mock camera {self.sensor_id} started")
                return True

        except Exception as e:
            logging.error(f"Failed to start RGB-D sensor {self.sensor_id}: {e}")
            return False

    async def stop_capture(self):
        """Stop RGB-D camera capture"""
        self.is_active = False
        if hasattr(self, 'pipeline'):
            self.pipeline.stop()
        if self.camera:
            self.camera.release()
        logging.info(f"RGB-D sensor {self.sensor_id} stopped")

    async def get_frame(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get RGB and depth frame"""
        if not self.is_active:
            return None

        try:
            if hasattr(self, 'pipeline'):
                # RealSense camera
                frames = self.pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()

                if depth_frame and color_frame:
                    depth_image = np.asanyarray(depth_frame.get_data())
                    color_image = np.asanyarray(color_frame.get_data())
                    return color_image, depth_image

            elif self.camera:
                # Regular webcam with mock depth
                ret, color_image = self.camera.read()
                if ret:
                    # Generate mock depth based on image brightness
                    gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
                    # Invert brightness to create depth (brighter = closer)
                    depth_image = (255 - gray) * 10  # Scale to depth units
                    return color_image, depth_image

            else:
                # Mock frame
                color_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                depth_image = np.random.randint(500, 5000, (480, 640), dtype=np.uint16)
                return color_image, depth_image

        except Exception as e:
            logging.error(f"Error getting frame from {self.sensor_id}: {e}")
            return None

    def depth_to_point_cloud(self, depth_image: np.ndarray, color_image: np.ndarray) -> List[Point3D]:
        """Convert depth image to 3D point cloud"""
        if self.intrinsics is None:
            # Use default intrinsics
            fx, fy = 525.0, 525.0  # Focal lengths
            cx, cy = 320.0, 240.0  # Principal point
        else:
            camera_matrix = self.intrinsics['camera_matrix']
            fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
            cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]

        points = []
        height, width = depth_image.shape

        # Sample points to reduce density
        step = 4  # Sample every 4th pixel

        for y in range(0, height, step):
            for x in range(0, width, step):
                depth = depth_image[y, x] / self.depth_scale  # Convert to meters

                if depth > 0.1 and depth < 10.0:  # Valid depth range
                    # Convert to 3D coordinates
                    world_x = (x - cx) * depth / fx
                    world_y = (y - cy) * depth / fy
                    world_z = depth

                    # Get color
                    color = tuple(color_image[y, x]) if color_image is not None else None

                    point = Point3D(world_x, world_y, world_z, color)
                    points.append(point)

        return points


class SpatialMapper:
    """Main spatial mapping system"""

    def __init__(self, map_id: str = "default_map"):
        self.map_id = map_id
        self.sensors: Dict[str, SpatialSensor] = {}
        self.point_cloud_processor = PointCloudProcessor()

        # Mapping state
        self.is_mapping = False
        self.current_map = None
        self.map_update_queue = queue.Queue() if queue else None
        self.mapping_thread = None

        # Map quality metrics
        self.coverage_area = 0.0
        self.point_density = 0.0
        self.surface_count = 0

        # Event callbacks
        self.event_callbacks: Dict[str, Callable] = {}

        self.logger = logging.getLogger(__name__)

    def add_sensor(self, sensor: SpatialSensor):
        """Add spatial sensor to mapper"""
        self.sensors[sensor.sensor_id] = sensor
        self.logger.info(f"Added sensor: {sensor.sensor_id} ({sensor.sensor_type.value})")

    async def start_mapping(self) -> bool:
        """Start spatial mapping"""
        try:
            self.logger.info(f"Starting spatial mapping for map: {self.map_id}")

            # Initialize current map
            self.current_map = SpatialMap(
                map_id=self.map_id,
                points=[],
                surfaces=[],
                coordinate_frame=np.eye(4),
                timestamp=time.time(),
                quality_score=0.0
            )

            # Start all sensors
            for sensor in self.sensors.values():
                if not await sensor.start_capture():
                    self.logger.error(f"Failed to start sensor: {sensor.sensor_id}")
                    return False

            self.is_mapping = True

            # Start mapping thread
            self.mapping_thread = threading.Thread(target=self._mapping_loop)
            self.mapping_thread.daemon = True
            self.mapping_thread.start()

            self.logger.info("Spatial mapping started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start spatial mapping: {e}")
            return False

    def _mapping_loop(self):
        """Main mapping loop"""
        frame_count = 0
        last_update_time = time.time()

        while self.is_mapping:
            try:
                # Get frames from all sensors
                all_points = []

                for sensor in self.sensors.values():
                    if sensor.is_active:
                        frame = asyncio.run(sensor.get_frame())
                        if frame:
                            if isinstance(sensor, RGBDSensor):
                                color_image, depth_image = frame
                                sensor_points = sensor.depth_to_point_cloud(depth_image, color_image)
                                all_points.extend(sensor_points)

                if all_points:
                    # Process point cloud
                    processed_points = self._process_point_cloud(all_points)

                    # Detect surfaces
                    surfaces = self._detect_surfaces(processed_points)

                    # Update map
                    self._update_map(processed_points, surfaces)

                    frame_count += 1

                    # Trigger update events periodically
                    current_time = time.time()
                    if current_time - last_update_time > 1.0:  # Update every second
                        self._trigger_map_update_event()
                        last_update_time = current_time

                # Control frame rate
                time.sleep(0.1)  # 10 FPS for mapping

            except Exception as e:
                self.logger.error(f"Error in mapping loop: {e}")

    def _process_point_cloud(self, points: List[Point3D]) -> List[Point3D]:
        """Process raw point cloud"""
        # Filter outliers
        filtered_points = self.point_cloud_processor.filter_outliers(points)

        # Voxel downsampling
        downsampled_points = self.point_cloud_processor.voxel_downsample(filtered_points)

        # Estimate normals
        points_with_normals = self.point_cloud_processor.estimate_normals(downsampled_points)

        return points_with_normals

    def _detect_surfaces(self, points: List[Point3D]) -> List[SpatialSurface]:
        """Detect surfaces from point cloud"""
        surfaces = []

        # Detect planes
        planes = self.point_cloud_processor.detect_planes(points)

        # Classify and create surface objects
        for i, plane in enumerate(planes):
            if plane.points:
                surface_type = self.point_cloud_processor.classify_surface(plane, points)

                # Calculate bounding box
                point_arrays = np.array([p.to_array() for p in plane.points])
                min_coords = np.min(point_arrays, axis=0)
                max_coords = np.max(point_arrays, axis=0)

                bounding_box = BoundingBox3D(
                    Point3D(min_coords[0], min_coords[1], min_coords[2]),
                    Point3D(max_coords[0], max_coords[1], max_coords[2])
                )

                surface = SpatialSurface(
                    surface_id=f"surface_{i}_{int(time.time())}",
                    surface_type=surface_type,
                    plane=plane,
                    bounding_box=bounding_box,
                    points=plane.points,
                    confidence=min(1.0, len(plane.points) / 1000),  # More points = higher confidence
                    timestamp=time.time()
                )

                surfaces.append(surface)

        return surfaces

    def _update_map(self, points: List[Point3D], surfaces: List[SpatialSurface]):
        """Update current spatial map"""
        if not self.current_map:
            return

        # Add new points (limit total number to prevent memory issues)
        max_points = 100000
        if len(self.current_map.points) + len(points) > max_points:
            # Keep most recent points
            self.current_map.points = self.current_map.points[-max_points//2:] + points[-max_points//2:]
        else:
            self.current_map.points.extend(points)

        # Update surfaces (merge nearby surfaces)
        self._merge_surfaces(surfaces)

        # Update quality metrics
        self._update_quality_metrics()

        # Update timestamp
        self.current_map.timestamp = time.time()

    def _merge_surfaces(self, new_surfaces: List[SpatialSurface]):
        """Merge new surfaces with existing ones"""
        # Simple merging based on proximity and type
        merge_threshold = 0.1  # 10cm

        for new_surface in new_surfaces:
            merged = False

            for existing_surface in self.current_map.surfaces:
                if (existing_surface.surface_type == new_surface.surface_type and
                    abs(existing_surface.plane.distance - new_surface.plane.distance) < merge_threshold):

                    # Check normal similarity
                    normal_dot = existing_surface.plane.normal.dot(new_surface.plane.normal)
                    if normal_dot > 0.9:  # Very similar normals
                        # Merge surfaces
                        existing_surface.points.extend(new_surface.points)
                        existing_surface.confidence = max(existing_surface.confidence, new_surface.confidence)
                        existing_surface.timestamp = time.time()
                        merged = True
                        break

            if not merged:
                self.current_map.surfaces.append(new_surface)

    def _update_quality_metrics(self):
        """Update map quality metrics"""
        if not self.current_map:
            return

        # Coverage area (bounding box area)
        if self.current_map.points:
            point_arrays = np.array([p.to_array() for p in self.current_map.points])
            min_coords = np.min(point_arrays, axis=0)
            max_coords = np.max(point_arrays, axis=0)
            dimensions = max_coords - min_coords
            self.coverage_area = dimensions[0] * dimensions[2]  # X * Z area

        # Point density
        if self.coverage_area > 0:
            self.point_density = len(self.current_map.points) / self.coverage_area

        # Surface count
        self.surface_count = len(self.current_map.surfaces)

        # Overall quality score
        quality_factors = [
            min(1.0, self.point_density / 1000),  # Point density factor
            min(1.0, self.surface_count / 20),     # Surface count factor
            min(1.0, len(self.current_map.points) / 10000)  # Point count factor
        ]
        self.current_map.quality_score = np.mean(quality_factors)

    def _trigger_map_update_event(self):
        """Trigger map update event"""
        if 'map_update' in self.event_callbacks:
            try:
                self.event_callbacks['map_update'](self.current_map)
            except Exception as e:
                self.logger.error(f"Error in map_update callback: {e}")

    async def stop_mapping(self):
        """Stop spatial mapping"""
        self.is_mapping = False

        # Stop all sensors
        for sensor in self.sensors.values():
            await sensor.stop_capture()

        # Stop mapping thread
        if self.mapping_thread:
            self.mapping_thread.join(timeout=1.0)

        self.logger.info("Spatial mapping stopped")

    def get_current_map(self) -> Optional[SpatialMap]:
        """Get current spatial map"""
        return self.current_map

    def save_map(self, filepath: str) -> bool:
        """Save spatial map to file"""
        if not self.current_map:
            return False

        try:
            map_data = {
                'map_id': self.current_map.map_id,
                'timestamp': self.current_map.timestamp,
                'quality_score': self.current_map.quality_score,
                'coordinate_frame': self.current_map.coordinate_frame.tolist(),
                'points': [
                    {
                        'x': p.x, 'y': p.y, 'z': p.z,
                        'color': p.color,
                        'confidence': p.confidence
                    } for p in self.current_map.points
                ],
                'surfaces': [
                    {
                        'surface_id': s.surface_id,
                        'surface_type': s.surface_type.value,
                        'normal': {
                            'x': s.plane.normal.x,
                            'y': s.plane.normal.y,
                            'z': s.plane.normal.z
                        },
                        'distance': s.plane.distance,
                        'confidence': s.confidence,
                        'timestamp': s.timestamp
                    } for s in self.current_map.surfaces
                ]
            }

            with open(filepath, 'w') as f:
                json.dump(map_data, f, indent=2)

            self.logger.info(f"Map saved to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save map: {e}")
            return False

    def load_map(self, filepath: str) -> bool:
        """Load spatial map from file"""
        try:
            with open(filepath, 'r') as f:
                map_data = json.load(f)

            # Recreate points
            points = []
            for p_data in map_data.get('points', []):
                point = Point3D(
                    x=p_data['x'],
                    y=p_data['y'],
                    z=p_data['z'],
                    color=tuple(p_data['color']) if p_data['color'] else None,
                    confidence=p_data.get('confidence', 1.0)
                )
                points.append(point)

            # Recreate surfaces
            surfaces = []
            for s_data in map_data.get('surfaces', []):
                normal = Vector3(
                    s_data['normal']['x'],
                    s_data['normal']['y'],
                    s_data['normal']['z']
                )
                plane = Plane3D(normal, s_data['distance'])

                surface = SpatialSurface(
                    surface_id=s_data['surface_id'],
                    surface_type=SurfaceType(s_data['surface_type']),
                    plane=plane,
                    bounding_box=BoundingBox3D(Point3D(0,0,0), Point3D(1,1,1)),  # Placeholder
                    points=[],  # Points not stored in save file
                    confidence=s_data.get('confidence', 1.0),
                    timestamp=s_data.get('timestamp', time.time())
                )
                surfaces.append(surface)

            # Create map object
            self.current_map = SpatialMap(
                map_id=map_data['map_id'],
                points=points,
                surfaces=surfaces,
                coordinate_frame=np.array(map_data['coordinate_frame']),
                timestamp=map_data.get('timestamp', time.time()),
                quality_score=map_data.get('quality_score', 0.0)
            )

            self.logger.info(f"Map loaded from {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load map: {e}")
            return False

    def register_callback(self, event_type: str, callback: Callable):
        """Register event callback"""
        self.event_callbacks[event_type] = callback
        self.logger.info(f"Registered callback for event: {event_type}")

    def get_mapping_statistics(self) -> Dict:
        """Get mapping statistics"""
        return {
            'map_id': self.map_id,
            'total_points': len(self.current_map.points) if self.current_map else 0,
            'total_surfaces': len(self.current_map.surfaces) if self.current_map else 0,
            'coverage_area': self.coverage_area,
            'point_density': self.point_density,
            'surface_count': self.surface_count,
            'quality_score': self.current_map.quality_score if self.current_map else 0.0,
            'active_sensors': len([s for s in self.sensors.values() if s.is_active]),
            'is_mapping': self.is_mapping
        }


class DMLogn8nEnvironmentMapper:
    """DMLogn8n-specific environment mapping integration"""

    def __init__(self):
        self.spatial_mapper = SpatialMapper("dmlogn8n_environment")
        self.environment_objects: Dict[str, Any] = {}
        self.interaction_zones: Dict[str, BoundingBox3D] = {}

        # Environment-specific classification
        self.game_surface_mapping = {
            "bar_counter": SurfaceType.TABLE,
            "tables": SurfaceType.TABLE,
            "chairs": SurfaceType.CHAIR,
            "fireplace": SurfaceType.WALL,
            "walls": SurfaceType.WALL,
            "floor": SurfaceType.FLOOR,
            "ceiling": SurfaceType.CEILING
        }

    async def initialize_environment_mapping(self):
        """Initialize environment mapping for DMLogn8n"""
        # Add RGB-D sensor
        rgbd_sensor = RGBDSensor("main_camera", camera_id=0)
        self.spatial_mapper.add_sensor(rgbd_sensor)

        # Register callbacks
        self.spatial_mapper.register_callback('map_update', self._on_map_update)

        # Start mapping
        success = await self.spatial_mapper.start_mapping()
        if success:
            print("Environment mapping initialized successfully")
        else:
            print("Failed to initialize environment mapping")

        return success

    def _on_map_update(self, spatial_map: SpatialMap):
        """Handle map update events"""
        # Classify game objects from detected surfaces
        self._classify_game_objects(spatial_map)

        # Update interaction zones
        self._update_interaction_zones(spatial_map)

        # Print mapping progress
        stats = self.spatial_mapper.get_mapping_statistics()
        print(f"Mapping progress: {stats['total_points']} points, "
              f"{stats['total_surfaces']} surfaces, quality: {stats['quality_score']:.2f}")

    def _classify_game_objects(self, spatial_map: SpatialMap):
        """Classify detected surfaces as game objects"""
        for surface in spatial_map.surfaces:
            if surface.surface_type == SurfaceType.TABLE:
                # Check if it could be a bar counter
                if surface.bounding_box.get_dimensions()[0] > 2.0:  # Long table
                    self.environment_objects["bar_counter"] = surface
                    print("Detected bar counter")

                # Check if it could be a dining table
                elif 0.8 < surface.bounding_box.get_dimensions()[0] < 1.5:
                    table_id = f"table_{len(self.environment_objects)}"
                    self.environment_objects[table_id] = surface
                    print(f"Detected dining table: {table_id}")

            elif surface.surface_type == SurfaceType.CHAIR:
                chair_id = f"chair_{len(self.environment_objects)}"
                self.environment_objects[chair_id] = surface
                print(f"Detected chair: {chair_id}")

    def _update_interaction_zones(self, spatial_map: SpatialMap):
        """Update interaction zones based on mapped environment"""
        # Create interaction zones around key objects
        for obj_name, surface in self.environment_objects.items():
            # Expand bounding box for interaction
            bbox = surface.bounding_box
            expanded_bbox = BoundingBox3D(
                Point3D(bbox.min_point.x - 0.2, bbox.min_point.y - 0.1, bbox.min_point.z - 0.2),
                Point3D(bbox.max_point.x + 0.2, bbox.max_point.y + 0.3, bbox.max_point.z + 0.2)
            )
            self.interaction_zones[obj_name] = expanded_bbox

    def get_object_at_position(self, position: Vector3) -> Optional[str]:
        """Get game object at specific position"""
        point = Point3D(position.x, position.y, position.z)

        for obj_name, bbox in self.interaction_zones.items():
            if (bbox.min_point.x <= point.x <= bbox.max_point.x and
                bbox.min_point.y <= point.y <= bbox.max_point.y and
                bbox.min_point.z <= point.z <= bbox.max_point.z):
                return obj_name

        return None

    def export_environment_data(self, filepath: str) -> bool:
        """Export environment data for game use"""
        try:
            environment_data = {
                'objects': {},
                'interaction_zones': {},
                'surfaces': {}
            }

            # Export objects
            for obj_name, surface in self.environment_objects.items():
                center = surface.bounding_box.get_center()
                dimensions = surface.bounding_box.get_dimensions()

                environment_data['objects'][obj_name] = {
                    'type': surface.surface_type.value,
                    'position': {'x': center.x, 'y': center.y, 'z': center.z},
                    'dimensions': {'x': dimensions[0], 'y': dimensions[1], 'z': dimensions[2]},
                    'normal': {
                        'x': surface.plane.normal.x,
                        'y': surface.plane.normal.y,
                        'z': surface.plane.normal.z
                    },
                    'confidence': surface.confidence
                }

            # Export interaction zones
            for zone_name, bbox in self.interaction_zones.items():
                center = bbox.get_center()
                dimensions = bbox.get_dimensions()

                environment_data['interaction_zones'][zone_name] = {
                    'position': {'x': center.x, 'y': center.y, 'z': center.z},
                    'dimensions': {'x': dimensions[0], 'y': dimensions[1], 'z': dimensions[2]}
                }

            # Export all surfaces
            for surface in self.spatial_mapper.current_map.surfaces:
                center = surface.bounding_box.get_center()
                dimensions = surface.bounding_box.get_dimensions()

                environment_data['surfaces'][surface.surface_id] = {
                    'type': surface.surface_type.value,
                    'position': {'x': center.x, 'y': center.y, 'z': center.z},
                    'dimensions': {'x': dimensions[0], 'y': dimensions[1], 'z': dimensions[2]},
                    'normal': {
                        'x': surface.plane.normal.x,
                        'y': surface.plane.normal.y,
                        'z': surface.plane.normal.z
                    }
                }

            with open(filepath, 'w') as f:
                json.dump(environment_data, f, indent=2)

            print(f"Environment data exported to {filepath}")
            return True

        except Exception as e:
            print(f"Failed to export environment data: {e}")
            return False

    async def shutdown(self):
        """Shutdown environment mapping"""
        await self.spatial_mapper.stop_mapping()
        print("Environment mapping shutdown complete")


async def main():
    """Main function to test spatial mapping system"""
    logging.basicConfig(level=logging.INFO)

    # Create DMLogn8n environment mapper
    env_mapper = DMLogn8nEnvironmentMapper()

    # Initialize mapping
    if await env_mapper.initialize_environment_mapping():
        try:
            print("DMLogn8n Spatial Mapping System")
            print("Scanning environment... Move camera around to map the space.")
            print("Try to capture the tavern environment:")
            print("- Walk around the room")
            print("- Focus on the bar counter")
            print("- Capture tables and chairs")
            print("- Map the fireplace area")

            # Run for 60 seconds to allow mapping
            await asyncio.sleep(60)

            # Print final statistics
            stats = env_mapper.spatial_mapper.get_mapping_statistics()
            print(f"\nFinal mapping statistics:")
            print(f"  Total points: {stats['total_points']}")
            print(f"  Total surfaces: {stats['total_surfaces']}")
            print(f"  Coverage area: {stats['coverage_area']:.2f} m²")
            print(f"  Point density: {stats['point_density']:.2f} points/m²")
            print(f"  Quality score: {stats['quality_score']:.2f}")

            # Save the map
            map_saved = env_mapper.spatial_mapper.save_map("dmlogn8n_environment_map.json")
            if map_saved:
                print("Environment map saved to dmlogn8n_environment_map.json")

            # Export environment data
            env_saved = env_mapper.export_environment_data("dmlogn8n_environment.json")
            if env_saved:
                print("Environment data exported to dmlogn8n_environment.json")

            print("\nDetected objects:")
            for obj_name in env_mapper.environment_objects:
                print(f"  - {obj_name}")

        except KeyboardInterrupt:
            print("\nMapping interrupted by user")
        finally:
            await env_mapper.shutdown()
    else:
        print("Failed to initialize environment mapping")


if __name__ == "__main__":
    asyncio.run(main())