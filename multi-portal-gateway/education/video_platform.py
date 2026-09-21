#!/usr/bin/env python3
"""
DMLogn8n Video Platform - Video Tutorials and Live Streaming System
Comprehensive video platform with transcoding, streaming, recording, and interactive features
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import re

# Third-party imports
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import yaml
import aiofiles
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import whisper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_platform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class VideoType(Enum):
    TUTORIAL = "tutorial"
    LECTURE = "lecture"
    DEMO = "demo"
    INTERVIEW = "interview"
    WORKSHOP = "workshop"
    SCREENCAST = "screencast"
    PRESENTATION = "presentation"
    RECORDING = "recording"

class VideoStatus(Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    PRIVATE = "private"
    ARCHIVED = "archived"
    ERROR = "error"

class StreamStatus(Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"
    ERROR = "error"

class VideoQuality(Enum):
    AUTO = "auto"
    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LOWEST = "lowest"

@dataclass
class VideoMetadata:
    duration_seconds: float
    width: int
    height: int
    fps: float
    file_size_mb: float
    format: str
    codec: str
    bitrate_kbps: int
    has_audio: bool
    audio_codec: str
    audio_bitrate_kbps: int
    thumbnail_path: str
    preview_path: str

@dataclass
class Video:
    id: str
    title: str
    description: str
    video_type: VideoType
    status: VideoStatus
    author_id: str
    category_id: Optional[str]
    tags: List[str]
    metadata: VideoMetadata
    file_path: str
    thumbnail_url: str
    stream_url: str
    download_url: str
    view_count: int
    like_count: int
    duration_seconds: float
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

@dataclass
class LiveStream:
    id: str
    title: str
    description: str
    stream_key: str
    stream_status: StreamStatus
    host_id: str
    category_id: Optional[str]
    tags: List[str]
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    viewer_count: int
    max_viewers: int
    recording_enabled: bool
    recording_path: Optional[str]
    chat_enabled: bool
    created_at: datetime
    updated_at: datetime

class VideoDB(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    video_type = Column(String, nullable=False)
    status = Column(String, default=VideoStatus.UPLOADING.value)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("video_categories.id"))
    tags = Column(Text)  # JSON string
    metadata = Column(Text)  # JSON string
    file_path = Column(String, nullable=False)
    thumbnail_url = Column(String)
    stream_url = Column(String)
    download_url = Column(String)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)

    # Relationships
    author = relationship("User")
    category = relationship("VideoCategory")
    transcripts = relationship("VideoTranscript", back_populates="video")
    chapters = relationship("VideoChapter", back_populates="video")

class LiveStreamDB(Base):
    __tablename__ = "live_streams"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    stream_key = Column(String, unique=True, nullable=False)
    stream_status = Column(String, default=StreamStatus.SCHEDULED.value)
    host_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("video_categories.id"))
    tags = Column(Text)  # JSON string
    scheduled_start = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    viewer_count = Column(Integer, default=0)
    max_viewers = Column(Integer, default=0)
    recording_enabled = Column(Boolean, default=False)
    recording_path = Column(String)
    chat_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    host = relationship("User")
    category = relationship("VideoCategory")

class VideoCategory(Base):
    __tablename__ = "video_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String)
    color = Column(String)
    parent_id = Column(String, ForeignKey("video_categories.id"))
    sort_order = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("VideoCategory", remote_side=[id])
    children = relationship("VideoCategory")

class VideoTranscript(Base):
    __tablename__ = "video_transcripts"

    id = Column(String, primary_key=True)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    language = Column(String, default="en")
    content = Column(Text, nullable=False)
    confidence_score = Column(Float)
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("VideoDB", back_populates="transcripts")

class VideoChapter(Base):
    __tablename__ = "video_chapters"

    id = Column(String, primary_key=True)
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    title = Column(String, nullable=False)
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float)
    description = Column(Text)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("VideoDB", back_populates="chapters")

class VideoProcessor:
    """Advanced video processing and transcoding system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.upload_dir = Path(self.config.get("upload_dir", "uploads"))
        self.processed_dir = Path(self.config.get("processed_dir", "processed"))
        self.temp_dir = Path(self.config.get("temp_dir", "temp"))

        # Create directories
        for dir_path in [self.upload_dir, self.processed_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True)

        self.whisper_model = None  # Lazy load
        self.processing_queue = asyncio.Queue()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration"""
        default_config = {
            "upload_dir": "uploads",
            "processed_dir": "processed",
            "temp_dir": "temp",
            "ffmpeg_path": "ffmpeg",
            "ffprobe_path": "ffprobe",
            "max_file_size_mb": 2048,
            "supported_formats": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
            "output_formats": {
                "h264": {"codec": "libx264", "extension": ".mp4"},
                "webm": {"codec": "libvpx-vp9", "extension": ".webm"},
                "hls": {"codec": "libx264", "extension": ".m3u8"}
            },
            "thumbnail_settings": {
                "width": 1280,
                "height": 720,
                "quality": 85
            },
            "transcribe_enabled": True,
            "whisper_model": "base"
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def process_video(self, video_id: str, file_path: str) -> Dict[str, Any]:
        """Process uploaded video file"""
        try:
            logger.info(f"Starting video processing for {video_id}")

            # Get video metadata
            metadata = await self._extract_metadata(file_path)

            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(file_path, video_id)

            # Generate preview
            preview_path = await self._generate_preview(file_path, video_id)

            # Transcode to different formats
            transcoded_files = await self._transcode_video(file_path, video_id)

            # Generate chapters (if enabled)
            chapters = await self._generate_chapters(file_path)

            # Generate transcript (if enabled)
            transcript = None
            if self.config.get("transcribe_enabled"):
                transcript = await self._generate_transcript(file_path)

            # Update metadata
            updated_metadata = VideoMetadata(
                duration_seconds=metadata["duration"],
                width=metadata["width"],
                height=metadata["height"],
                fps=metadata["fps"],
                file_size_mb=metadata["size_mb"],
                format=metadata["format"],
                codec=metadata["codec"],
                bitrate_kbps=metadata["bitrate_kbps"],
                has_audio=metadata["has_audio"],
                audio_codec=metadata["audio_codec"],
                audio_bitrate_kbps=metadata["audio_bitrate_kbps"],
                thumbnail_path=thumbnail_path,
                preview_path=preview_path
            )

            result = {
                "metadata": asdict(updated_metadata),
                "transcoded_files": transcoded_files,
                "chapters": chapters,
                "transcript": transcript,
                "status": "completed"
            }

            logger.info(f"Video processing completed for {video_id}")
            return result

        except Exception as e:
            logger.error(f"Video processing failed for {video_id}: {e}")
            return {"status": "error", "error": str(e)}

        finally:
            # Cleanup temporary files
            await self._cleanup_temp_files(video_id)

    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract video metadata using FFprobe"""
        cmd = [
            self.config["ffprobe_path"],
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFprobe failed: {stderr.decode()}")

        probe_data = json.loads(stdout.decode())

        # Extract video stream info
        video_stream = None
        audio_stream = None

        for stream in probe_data.get("streams", []):
            if stream["codec_type"] == "video" and not video_stream:
                video_stream = stream
            elif stream["codec_type"] == "audio" and not audio_stream:
                audio_stream = stream

        if not video_stream:
            raise Exception("No video stream found")

        # Extract format info
        format_info = probe_data.get("format", {})

        return {
            "duration": float(format_info.get("duration", 0)),
            "size_mb": float(format_info.get("size", 0)) / (1024 * 1024),
            "format": format_info.get("format_name", ""),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "0/1")),
            "codec": video_stream.get("codec_name", ""),
            "bitrate_kbps": int(format_info.get("bit_rate", 0)) / 1000,
            "has_audio": audio_stream is not None,
            "audio_codec": audio_stream.get("codec_name", "") if audio_stream else "",
            "audio_bitrate_kbps": int(audio_stream.get("bit_rate", 0)) / 1000 if audio_stream else 0
        }

    async def _generate_thumbnail(self, file_path: str, video_id: str) -> str:
        """Generate video thumbnail"""
        thumbnail_dir = self.processed_dir / "thumbnails"
        thumbnail_dir.mkdir(exist_ok=True)

        thumbnail_path = thumbnail_dir / f"{video_id}.jpg"

        # Extract thumbnail at 10% of video duration
        cmd = [
            self.config["ffmpeg_path"],
            "-i", file_path,
            "-ss", "00:00:01",  # 1 second mark
            "-vframes", "1",
            "-vf", f"scale={self.config['thumbnail_settings']['width']}:{self.config['thumbnail_settings']['height']}",
            "-q:v", str(self.config['thumbnail_settings']['quality']),
            "-y",
            str(thumbnail_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Thumbnail generation failed: {stderr.decode()}")

        return str(thumbnail_path)

    async def _generate_preview(self, file_path: str, video_id: str) -> str:
        """Generate video preview (short clip)"""
        preview_dir = self.processed_dir / "previews"
        preview_dir.mkdir(exist_ok=True)

        preview_path = preview_dir / f"{video_id}_preview.mp4"

        # Extract 30-second preview from the middle
        cmd = [
            self.config["ffmpeg_path"],
            "-i", file_path,
            "-ss", "00:00:30",  # Start at 30 seconds
            "-t", "00:00:30",   # 30 seconds duration
            "-vf", "scale=640:360",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            str(preview_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.warning(f"Preview generation failed: {stderr.decode()}")
            return ""

        return str(preview_path)

    async def _transcode_video(self, file_path: str, video_id: str) -> Dict[str, str]:
        """Transcode video to multiple formats"""
        transcoded_files = {}
        output_dir = self.processed_dir / "videos"
        output_dir.mkdir(exist_ok=True)

        for format_name, format_config in self.config["output_formats"].items():
            output_path = output_dir / f"{video_id}{format_config['extension']}"

            if format_name == "hls":
                # HLS transcoding
                await self._transcode_to_hls(file_path, output_dir / video_id)
                transcoded_files[format_name] = f"/videos/{video_id}/playlist.m3u8"
            else:
                # Standard transcoding
                await self._transcode_to_format(
                    file_path,
                    str(output_path),
                    format_config["codec"]
                )
                transcoded_files[format_name] = f"/videos/{video_id}{format_config['extension']}"

        return transcoded_files

    async def _transcode_to_format(self, input_path: str, output_path: str, codec: str):
        """Transcode video to specific format"""
        cmd = [
            self.config["ffmpeg_path"],
            "-i", input_path,
            "-c:v", codec,
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Transcoding failed: {stderr.decode()}")

    async def _transcode_to_hls(self, input_path: str, output_dir: Path):
        """Transcode video to HLS format"""
        output_dir.mkdir(exist_ok=True)

        cmd = [
            self.config["ffmpeg_path"],
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", str(output_dir / "segment%03d.ts"),
            str(output_dir / "playlist.m3u8")
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"HLS transcoding failed: {stderr.decode()}")

    async def _generate_chapters(self, file_path: str) -> List[Dict[str, Any]]:
        """Generate video chapters using scene detection"""
        try:
            # Use OpenCV for scene detection
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Sample frames every 30 seconds
            sample_interval = int(30 * fps)
            chapters = []
            current_chapter = None

            for frame_num in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if ret:
                    # Simple scene detection using histogram difference
                    if current_chapter is None:
                        current_chapter = {
                            "start_time": frame_num / fps,
                            "title": f"Chapter {len(chapters) + 1}",
                            "description": ""
                        }
                    else:
                        # Could implement more sophisticated scene detection here
                        pass

                    # End chapter after 5 minutes
                    if current_chapter and (frame_num / fps - current_chapter["start_time"]) >= 300:
                        current_chapter["end_time"] = frame_num / fps
                        chapters.append(current_chapter)
                        current_chapter = None

            cap.release()

            # Add final chapter if it exists
            if current_chapter:
                current_chapter["end_time"] = total_frames / fps
                chapters.append(current_chapter)

            return chapters

        except Exception as e:
            logger.warning(f"Chapter generation failed: {e}")
            return []

    async def _generate_transcript(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Generate video transcript using Whisper"""
        try:
            # Load Whisper model
            if self.whisper_model is None:
                import whisper
                self.whisper_model = whisper.load_model(self.config["whisper_model"])

            # Extract audio from video
            audio_path = await self._extract_audio(file_path)

            # Transcribe audio
            result = self.whisper_model.transcribe(audio_path)

            # Process transcript
            transcript = {
                "text": result["text"],
                "language": result["language"],
                "segments": [
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"]
                    }
                    for segment in result["segments"]
                ],
                "word_count": len(result["text"].split())
            }

            # Cleanup audio file
            os.unlink(audio_path)

            return transcript

        except Exception as e:
            logger.warning(f"Transcript generation failed: {e}")
            return None

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file"""
        audio_path = self.temp_dir / f"audio_{uuid.uuid4()}.wav"

        cmd = [
            self.config["ffmpeg_path"],
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(audio_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Audio extraction failed: {stderr.decode()}")

        return str(audio_path)

    async def _cleanup_temp_files(self, video_id: str):
        """Clean up temporary files for a video"""
        temp_pattern = self.temp_dir / f"*{video_id}*"
        for temp_file in self.temp_dir.glob(f"*{video_id}*"):
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

class StreamingService:
    """Live streaming service with RTMP and WebRTC support"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.active_streams = {}
        self.stream_viewers = {}

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load streaming configuration"""
        default_config = {
            "rtmp_host": "localhost",
            "rtmp_port": 1935,
            "webrtc_port": 8080,
            "hls_segment_duration": 4,
            "max_viewers_per_stream": 1000,
            "recording_enabled": True,
            "recording_dir": "recordings",
            "chat_enabled": True,
            "stream_timeout_minutes": 240
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def start_stream(self, stream_id: str, stream_key: str) -> Dict[str, Any]:
        """Start a live stream"""
        if stream_id in self.active_streams:
            raise ValueError("Stream already active")

        # Validate stream key
        if not await self._validate_stream_key(stream_id, stream_key):
            raise ValueError("Invalid stream key")

        stream_info = {
            "stream_id": stream_id,
            "stream_key": stream_key,
            "status": StreamStatus.LIVE.value,
            "start_time": datetime.utcnow(),
            "viewer_count": 0,
            "recording": False,
            "rtmp_url": f"rtmp://{self.config['rtmp_host']}:{self.config['rtmp_port']}/live/{stream_key}",
            "hls_url": f"http://{self.config['rtmp_host']}:{self.config['rtmp_port']}/hls/{stream_id}.m3u8",
            "webrtc_url": f"http://{self.config['rtmp_host']}:{self.config['webrtc_port']}/{stream_id}"
        }

        self.active_streams[stream_id] = stream_info
        self.stream_viewers[stream_id] = set()

        logger.info(f"Started stream {stream_id}")

        return stream_info

    async def end_stream(self, stream_id: str) -> Dict[str, Any]:
        """End a live stream"""
        if stream_id not in self.active_streams:
            raise ValueError("Stream not found")

        stream_info = self.active_streams[stream_id]
        stream_info["status"] = StreamStatus.ENDED.value
        stream_info["end_time"] = datetime.utcnow()

        # Stop recording if enabled
        if stream_info.get("recording"):
            await self._stop_recording(stream_id)

        # Remove from active streams
        del self.active_streams[stream_id]
        del self.stream_viewers[stream_id]

        logger.info(f"Ended stream {stream_id}")

        return stream_info

    async def add_viewer(self, stream_id: str, viewer_id: str) -> bool:
        """Add viewer to stream"""
        if stream_id not in self.active_streams:
            return False

        if len(self.stream_viewers[stream_id]) >= self.config["max_viewers_per_stream"]:
            return False

        self.stream_viewers[stream_id].add(viewer_id)
        self.active_streams[stream_id]["viewer_count"] = len(self.stream_viewers[stream_id])

        return True

    async def remove_viewer(self, stream_id: str, viewer_id: str):
        """Remove viewer from stream"""
        if stream_id in self.stream_viewers:
            self.stream_viewers[stream_id].discard(viewer_id)
            if stream_id in self.active_streams:
                self.active_streams[stream_id]["viewer_count"] = len(self.stream_viewers[stream_id])

    async def start_recording(self, stream_id: str, recording_path: str):
        """Start recording a stream"""
        if stream_id not in self.active_streams:
            raise ValueError("Stream not found")

        stream_info = self.active_streams[stream_id]
        stream_info["recording"] = True
        stream_info["recording_path"] = recording_path

        # Start FFmpeg recording process
        rtmp_url = stream_info["rtmp_url"]
        cmd = [
            "ffmpeg",
            "-i", rtmp_url,
            "-c", "copy",
            "-f", "mp4",
            recording_path
        ]

        process = await asyncio.create_subprocess_exec(*cmd)
        stream_info["recording_process"] = process

        logger.info(f"Started recording stream {stream_id} to {recording_path}")

    async def _stop_recording(self, stream_id: str):
        """Stop recording a stream"""
        if stream_id in self.active_streams:
            stream_info = self.active_streams[stream_id]
            if stream_info.get("recording_process"):
                stream_info["recording_process"].terminate()
                await stream_info["recording_process"].wait()
                stream_info["recording"] = False

    async def _validate_stream_key(self, stream_id: str, stream_key: str) -> bool:
        """Validate stream key"""
        # In production, this would check against database
        return True  # Placeholder

    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get stream information"""
        return self.active_streams.get(stream_id)

    def get_active_streams(self) -> List[Dict[str, Any]]:
        """Get all active streams"""
        return list(self.active_streams.values())

class VideoAnalytics:
    """Video analytics and engagement tracking"""

    def __init__(self, db_session: Session, redis_client):
        self.db = db_session
        self.redis = redis_client

    async def track_view(self, video_id: str, user_id: Optional[str] = None, watch_time_seconds: float = 0):
        """Track video view"""
        # Update view count in database
        video = self.db.query(VideoDB).filter(VideoDB.id == video_id).first()
        if video:
            video.view_count += 1
            self.db.commit()

        # Track detailed analytics in Redis
        analytics_key = f"video_analytics:{video_id}"
        timestamp = datetime.utcnow().isoformat()

        view_data = {
            "user_id": user_id,
            "timestamp": timestamp,
            "watch_time_seconds": watch_time_seconds
        }

        self.redis.lpush(analytics_key, json.dumps(view_data))
        self.redis.expire(analytics_key, 86400 * 30)  # Keep for 30 days

        # Update daily stats
        daily_key = f"daily_views:{datetime.utcnow().strftime('%Y-%m-%d')}"
        self.redis.hincrby(daily_key, video_id, 1)
        self.redis.expire(daily_key, 86400 * 365)

    async def track_engagement(self, video_id: str, user_id: str, action: str, metadata: Dict[str, Any] = None):
        """Track user engagement with video"""
        engagement_key = f"engagement:{video_id}:{user_id}"

        engagement_data = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        self.redis.lpush(engagement_key, json.dumps(engagement_data))
        self.redis.expire(engagement_key, 86400 * 7)  # Keep for 7 days

    async def get_video_analytics(self, video_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a video"""
        # Get basic stats from database
        video = self.db.query(VideoDB).filter(VideoDB.id == video_id).first()
        if not video:
            return {}

        # Get view trends
        view_trends = await self._get_view_trends(video_id, days)

        # Get engagement metrics
        engagement_metrics = await self._get_engagement_metrics(video_id)

        # Get watch time distribution
        watch_time_distribution = await self._get_watch_time_distribution(video_id)

        return {
            "video_id": video_id,
            "total_views": video.view_count,
            "total_likes": video.like_count,
            "duration_seconds": video.duration_seconds,
            "view_trends": view_trends,
            "engagement_metrics": engagement_metrics,
            "watch_time_distribution": watch_time_distribution,
            "average_watch_time": await self._get_average_watch_time(video_id)
        }

    async def _get_view_trends(self, video_id: str, days: int) -> List[Dict[str, Any]]:
        """Get daily view trends"""
        trends = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_key = f"daily_views:{date}"
            views = self.redis.hget(daily_key, video_id)
            views = int(views) if views else 0

            trends.append({
                "date": date,
                "views": views
            })

        return list(reversed(trends))

    async def _get_engagement_metrics(self, video_id: str) -> Dict[str, Any]:
        """Get engagement metrics"""
        engagement_key = f"engagement:{video_id}:*"
        keys = self.redis.keys(engagement_key)

        total_engagements = 0
        engagement_types = {}

        for key in keys:
            engagements = self.redis.lrange(key, 0, -1)
            total_engagements += len(engagements)

            for engagement_json in engagements:
                engagement = json.loads(engagement_json)
                action = engagement["action"]
                engagement_types[action] = engagement_types.get(action, 0) + 1

        return {
            "total_engagements": total_engagements,
            "engagement_types": engagement_types
        }

    async def _get_watch_time_distribution(self, video_id: str) -> Dict[str, int]:
        """Get distribution of watch times"""
        analytics_key = f"video_analytics:{video_id}"
        views = self.redis.lrange(analytics_key, 0, -1)

        watch_time_buckets = {
            "0-30s": 0,
            "30s-1m": 0,
            "1m-5m": 0,
            "5m-10m": 0,
            "10m+": 0
        }

        for view_json in views:
            view = json.loads(view_json)
            watch_time = view.get("watch_time_seconds", 0)

            if watch_time < 30:
                watch_time_buckets["0-30s"] += 1
            elif watch_time < 60:
                watch_time_buckets["30s-1m"] += 1
            elif watch_time < 300:
                watch_time_buckets["1m-5m"] += 1
            elif watch_time < 600:
                watch_time_buckets["5m-10m"] += 1
            else:
                watch_time_buckets["10m+"] += 1

        return watch_time_buckets

    async def _get_average_watch_time(self, video_id: str) -> float:
        """Get average watch time for a video"""
        analytics_key = f"video_analytics:{video_id}"
        views = self.redis.lrange(analytics_key, 0, -1)

        if not views:
            return 0.0

        total_watch_time = 0
        for view_json in views:
            view = json.loads(view_json)
            total_watch_time += view.get("watch_time_seconds", 0)

        return total_watch_time / len(views)

# API Models
class UploadVideoRequest(BaseModel):
    title: str
    description: str
    video_type: str
    category_id: Optional[str] = None
    tags: List[str] = []
    status: str = "draft"

class CreateStreamRequest(BaseModel):
    title: str
    description: str
    category_id: Optional[str] = None
    tags: List[str] = []
    scheduled_start: Optional[datetime] = None
    recording_enabled: bool = True
    chat_enabled: bool = True

class VideoAnalyticsRequest(BaseModel):
    video_id: str
    days: int = 30

class VideoPlatformApp:
    """Main Video Platform Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Video Platform", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///video_platform.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.video_processor = VideoProcessor()
        self.streaming_service = StreamingService()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=3)

        # Templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
        self.app.mount("/processed", StaticFiles(directory="processed"), name="processed")

    def setup_middleware(self):
        """Setup FastAPI middleware"""
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "DMLogn8n Video Platform API"}

        @self.app.post("/videos/upload")
        async def upload_video(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            title: str = Form(...),
            description: str = Form(...),
            video_type: str = Form(...),
            category_id: Optional[str] = Form(None),
            tags: str = Form("[]"),
            author_id: str = Form(...)
        ):
            """Upload video file"""
            # Validate file
            if not self._validate_video_file(file):
                raise HTTPException(status_code=400, detail="Invalid video file")

            # Generate unique ID
            video_id = str(uuid.uuid4())

            # Save uploaded file
            upload_path = self.video_processor.upload_dir / f"{video_id}_{file.filename}"
            async with aiofiles.open(upload_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            # Create video record
            db = self.SessionLocal()
            try:
                video_db = VideoDB(
                    id=video_id,
                    title=title,
                    description=description,
                    video_type=video_type,
                    status=VideoStatus.UPLOADING.value,
                    author_id=author_id,
                    category_id=category_id,
                    tags=tags,
                    file_path=str(upload_path)
                )
                db.add(video_db)
                db.commit()
            finally:
                db.close()

            # Start processing in background
            background_tasks.add_task(self._process_uploaded_video, video_id, str(upload_path))

            return {"video_id": video_id, "message": "Video uploaded successfully"}

        @self.app.get("/videos")
        async def get_videos(
            video_type: Optional[str] = None,
            category_id: Optional[str] = None,
            tags: Optional[str] = None,
            status: str = "published",
            limit: int = 20,
            offset: int = 0
        ):
            """Get videos with filtering"""
            db = self.SessionLocal()
            try:
                query = db.query(VideoDB).filter(VideoDB.status == status)

                if video_type:
                    query = query.filter(VideoDB.video_type == video_type)
                if category_id:
                    query = query.filter(VideoDB.category_id == category_id)

                videos = query.offset(offset).limit(limit).all()

                return {
                    "videos": [
                        {
                            "id": video.id,
                            "title": video.title,
                            "description": video.description,
                            "video_type": video.video_type,
                            "thumbnail_url": video.thumbnail_url,
                            "duration_seconds": video.duration_seconds,
                            "view_count": video.view_count,
                            "created_at": video.created_at,
                            "author_id": video.author_id
                        }
                        for video in videos
                    ],
                    "total": len(videos)
                }
            finally:
                db.close()

        @self.app.get("/videos/{video_id}")
        async def get_video(video_id: str):
            """Get video details"""
            db = self.SessionLocal()
            try:
                video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
                if not video:
                    raise HTTPException(status_code=404, detail="Video not found")

                # Get chapters
                chapters = db.query(VideoChapter).filter(
                    VideoChapter.video_id == video_id
                ).order_by(VideoChapter.start_time_seconds).all()

                # Get transcript
                transcript = db.query(VideoTranscript).filter(
                    VideoTranscript.video_id == video_id
                ).first()

                return {
                    "id": video.id,
                    "title": video.title,
                    "description": video.description,
                    "video_type": video.video_type,
                    "status": video.status,
                    "author_id": video.author_id,
                    "metadata": json.loads(video.metadata or "{}"),
                    "thumbnail_url": video.thumbnail_url,
                    "stream_url": video.stream_url,
                    "download_url": video.download_url,
                    "view_count": video.view_count,
                    "like_count": video.like_count,
                    "duration_seconds": video.duration_seconds,
                    "created_at": video.created_at,
                    "chapters": [
                        {
                            "id": chapter.id,
                            "title": chapter.title,
                            "start_time_seconds": chapter.start_time_seconds,
                            "end_time_seconds": chapter.end_time_seconds,
                            "description": chapter.description,
                            "thumbnail_url": chapter.thumbnail_url
                        }
                        for chapter in chapters
                    ],
                    "transcript": {
                        "id": transcript.id,
                        "content": transcript.content,
                        "language": transcript.language
                    } if transcript else None
                }
            finally:
                db.close()

        @self.app.post("/streams/create")
        async def create_stream(request: CreateStreamRequest, host_id: str):
            """Create live stream"""
            stream_id = str(uuid.uuid4())
            stream_key = self._generate_stream_key()

            db = self.SessionLocal()
            try:
                stream_db = LiveStreamDB(
                    id=stream_id,
                    title=request.title,
                    description=request.description,
                    stream_key=stream_key,
                    host_id=host_id,
                    category_id=request.category_id,
                    tags=json.dumps(request.tags),
                    scheduled_start=request.scheduled_start,
                    recording_enabled=request.recording_enabled,
                    chat_enabled=request.chat_enabled
                )
                db.add(stream_db)
                db.commit()
            finally:
                db.close()

            return {
                "stream_id": stream_id,
                "stream_key": stream_key,
                "rtmp_url": f"rtmp://localhost:1935/live/{stream_key}",
                "message": "Stream created successfully"
            }

        @self.app.post("/streams/{stream_id}/start")
        async def start_stream(stream_id: str, stream_key: str):
            """Start live stream"""
            try:
                stream_info = await self.streaming_service.start_stream(stream_id, stream_key)

                # Update database
                db = self.SessionLocal()
                try:
                    stream = db.query(LiveStreamDB).filter(LiveStreamDB.id == stream_id).first()
                    if stream:
                        stream.stream_status = StreamStatus.LIVE.value
                        stream.actual_start = datetime.utcnow()
                        db.commit()
                finally:
                    db.close()

                return stream_info

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/streams/{stream_id}/end")
        async def end_stream(stream_id: str):
            """End live stream"""
            try:
                stream_info = await self.streaming_service.end_stream(stream_id)

                # Update database
                db = self.SessionLocal()
                try:
                    stream = db.query(LiveStreamDB).filter(LiveStreamDB.id == stream_id).first()
                    if stream:
                        stream.stream_status = StreamStatus.ENDED.value
                        stream.actual_end = datetime.utcnow()
                        db.commit()
                finally:
                    db.close()

                return stream_info

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/streams/active")
        async def get_active_streams():
            """Get all active streams"""
            active_streams = self.streaming_service.get_active_streams()
            return {"streams": active_streams}

        @self.app.post("/videos/{video_id}/analytics")
        async def get_video_analytics(request: VideoAnalyticsRequest):
            """Get video analytics"""
            db = self.SessionLocal()
            try:
                analytics = VideoAnalytics(db, self.redis_client)
                data = await analytics.get_video_analytics(request.video_id, request.days)
                return data
            finally:
                db.close()

        @self.app.post("/videos/{video_id}/track-view")
        async def track_view(video_id: str, user_id: Optional[str] = None, watch_time_seconds: float = 0):
            """Track video view"""
            db = self.SessionLocal()
            try:
                analytics = VideoAnalytics(db, self.redis_client)
                await analytics.track_view(video_id, user_id, watch_time_seconds)
                return {"message": "View tracked"}
            finally:
                db.close()

        @self.app.websocket("/ws/stream/{stream_id}")
        async def websocket_stream_endpoint(websocket: WebSocket, stream_id: str):
            """WebSocket for live stream interaction"""
            await websocket.accept()

            viewer_id = str(uuid.uuid4())

            # Add viewer to stream
            await self.streaming_service.add_viewer(stream_id, viewer_id)

            try:
                while True:
                    # Keep connection alive
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")

            except WebSocketDisconnect:
                # Remove viewer from stream
                await self.streaming_service.remove_viewer(stream_id, viewer_id)
                logger.info(f"Viewer {viewer_id} disconnected from stream {stream_id}")

    async def _process_uploaded_video(self, video_id: str, file_path: str):
        """Process uploaded video in background"""
        try:
            # Update status to processing
            db = self.SessionLocal()
            try:
                video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
                if video:
                    video.status = VideoStatus.PROCESSING.value
                    db.commit()
            finally:
                db.close()

            # Process video
            result = await self.video_processor.process_video(video_id, file_path)

            # Update video record
            db = self.SessionLocal()
            try:
                video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
                if video:
                    video.status = VideoStatus.READY.value if result["status"] == "completed" else VideoStatus.ERROR.value
                    video.metadata = json.dumps(result["metadata"])
                    video.duration_seconds = result["metadata"]["duration_seconds"]
                    video.thumbnail_url = f"/processed/thumbnails/{video_id}.jpg"
                    video.stream_url = f"/processed/videos/{video_id}.mp4"

                    # Save chapters
                    if result.get("chapters"):
                        for chapter_data in result["chapters"]:
                            chapter = VideoChapter(
                                id=str(uuid.uuid4()),
                                video_id=video_id,
                                title=chapter_data["title"],
                                start_time_seconds=chapter_data["start_time"],
                                end_time_seconds=chapter_data.get("end_time"),
                                description=chapter_data.get("description", "")
                            )
                            db.add(chapter)

                    # Save transcript
                    if result.get("transcript"):
                        transcript = VideoTranscript(
                            id=str(uuid.uuid4()),
                            video_id=video_id,
                            language=result["transcript"]["language"],
                            content=result["transcript"]["text"],
                            confidence_score=0.9,  # Placeholder
                            word_count=result["transcript"]["word_count"]
                        )
                        db.add(transcript)

                    db.commit()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Video processing failed for {video_id}: {e}")

            # Update status to error
            db = self.SessionLocal()
            try:
                video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
                if video:
                    video.status = VideoStatus.ERROR.value
                    db.commit()
            finally:
                db.close()

    def _validate_video_file(self, file: UploadFile) -> bool:
        """Validate uploaded video file"""
        # Check file extension
        allowed_extensions = self.video_processor.config["supported_formats"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return False

        # Check file size
        max_size_mb = self.video_processor.config["max_file_size_mb"]
        if file.size and file.size > max_size_mb * 1024 * 1024:
            return False

        return True

    def _generate_stream_key(self) -> str:
        """Generate unique stream key"""
        return str(uuid.uuid4()).replace('-', '')[:16]

    def run(self, host: str = "0.0.0.0", port: int = 8003):
        """Run the video platform server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = VideoPlatformApp()
    app.run()