"""Video processing using ffmpeg."""
import json
import subprocess
import platform
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from .utils import parse_video_filename
from .ffmpeg_manager import get_ffmpeg_path, get_ffprobe_path, get_subprocess_args


@dataclass
class VideoInfo:
    """Video file information."""
    path: Path
    start_time: datetime
    duration: float  # seconds
    width: int
    height: int
    bitrate: int  # bits per second
    fps: float


@dataclass
class ClipTask:
    """A video clip extraction task."""
    clip_start: datetime
    clip_end: datetime
    description: str
    output_path: Path
    video_info: VideoInfo | None = None
    status: str = "pending"  # pending, processing, completed, failed, skipped
    progress: float = 0.0
    error: str | None = None


@dataclass
class QualitySettings:
    """Video quality settings."""
    name: str
    bitrate_ratio: float  # ratio of original bitrate
    
    @classmethod
    def high(cls) -> 'QualitySettings':
        return cls("高", 1.0)
    
    @classmethod
    def medium(cls) -> 'QualitySettings':
        return cls("中", 0.5)
    
    @classmethod
    def low(cls) -> 'QualitySettings':
        return cls("低", 0.3)


@dataclass
class OffsetSettings:
    """Global time offset settings for clips."""
    start_offset: float = 0.0  # seconds (positive = earlier, negative = later)
    end_offset: float = 0.0    # seconds (positive = later, negative = earlier)
    min_duration: float = 10.0  # minimum clip duration in seconds
    
    @classmethod
    def default(cls) -> 'OffsetSettings':
        return cls(start_offset=0.0, end_offset=0.0, min_duration=10.0)


def get_video_info(video_path: Path) -> VideoInfo | None:
    """
    Get video information using ffprobe.
    
    Args:
        video_path: Path to video file
    
    Returns:
        VideoInfo object or None if failed
    """
    try:
        ffprobe_path = get_ffprobe_path()
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, **get_subprocess_args(timeout=30))
        
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        # Parse start time from filename
        start_time = parse_video_filename(video_path.name)
        if not start_time:
            return None
        
        duration = float(data.get('format', {}).get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        bitrate = int(data.get('format', {}).get('bit_rate', 0))
        
        # Parse fps
        fps_str = video_stream.get('r_frame_rate', '30/1')
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = float(num) / float(den) if float(den) > 0 else 30.0
        else:
            fps = float(fps_str)
        
        return VideoInfo(
            path=video_path,
            start_time=start_time,
            duration=duration,
            width=width,
            height=height,
            bitrate=bitrate,
            fps=fps
        )
        
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


class VideoProcessor:
    """Handles video cutting operations."""
    
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._paused: bool = False
        self._stopped: bool = False
        self.current_task: ClipTask | None = None
    
    def apply_time_offset(
        self,
        clip_start: datetime,
        clip_end: datetime,
        offset: OffsetSettings
    ) -> tuple[datetime, datetime]:
        """
        Apply global time offset to clip times.
        
        Args:
            clip_start: Original clip start time
            clip_end: Original clip end time
            offset: Offset settings
        
        Returns:
            Tuple of (adjusted_start, adjusted_end)
        """
        # Apply offsets (positive start_offset = earlier, positive end_offset = later)
        adjusted_start = clip_start - timedelta(seconds=offset.start_offset)
        adjusted_end = clip_end + timedelta(seconds=offset.end_offset)
        
        # Ensure minimum duration
        duration = (adjusted_end - adjusted_start).total_seconds()
        if duration < offset.min_duration:
            # Extend from start to meet minimum duration
            adjusted_end = adjusted_start + timedelta(seconds=offset.min_duration)
        
        return adjusted_start, adjusted_end
    
    def find_video_for_clip(
        self,
        videos: list[VideoInfo],
        clip_start: datetime,
        clip_end: datetime
    ) -> VideoInfo | None:
        """
        Find the source video that contains the clip time range.
        
        Args:
            videos: List of available video info
            clip_start: Clip start time
            clip_end: Clip end time
        
        Returns:
            VideoInfo or None if no video covers the time range
        """
        clip_duration = (clip_end - clip_start).total_seconds()
        
        # Sort videos by start time for better matching
        sorted_videos = sorted(videos, key=lambda v: v.start_time)
        
        for i, video in enumerate(sorted_videos):
            # Handle videos with unknown duration (duration=0)
            if video.duration <= 0:
                # Use next video's start time as end time, or assume 24 hours
                if i + 1 < len(sorted_videos):
                    video_end = sorted_videos[i + 1].start_time
                else:
                    # Last video: assume it covers until end of day + 1
                    video_end = video.start_time + timedelta(hours=25)
            else:
                video_end = video.start_time + timedelta(seconds=video.duration)
            
            # Check if video covers the clip time range
            if video.start_time <= clip_start and clip_end <= video_end:
                return video
        
        return None
    
    def calculate_seek_time(self, video: VideoInfo, clip_start: datetime) -> float:
        """Calculate seek time in seconds from video start."""
        delta = clip_start - video.start_time
        return delta.total_seconds()
    
    def cut_clip(
        self,
        task: ClipTask,
        quality: QualitySettings,
        progress_callback: Callable[[float], None] | None = None,
        log_callback: Callable[[str], None] | None = None
    ) -> bool:
        """
        Cut a video clip using ffmpeg.
        
        Args:
            task: ClipTask to process
            quality: Quality settings
            progress_callback: Callback for progress updates (0.0 - 1.0)
            log_callback: Callback for log messages
        
        Returns:
            True if successful, False otherwise
        """
        from .logger import get_logger
        logger = get_logger()
        
        if not task.video_info:
            task.status = "failed"
            task.error = "No source video found"
            logger.error(f"No video_info for task: {task.description}")
            return False
        
        video = task.video_info
        logger.info(f"cut_clip: {task.description}")
        logger.info(f"  Source: {video.path}")
        logger.info(f"  Clip times: {task.clip_start} ~ {task.clip_end}")
        
        # Calculate seek time and duration
        seek_time = self.calculate_seek_time(video, task.clip_start)
        duration = (task.clip_end - task.clip_start).total_seconds()
        
        logger.info(f"  Seek time: {seek_time:.2f}s, Duration: {duration:.2f}s")
        
        # Calculate output bitrate
        output_bitrate = int(video.bitrate * quality.bitrate_ratio)
        
        # Ensure output directory exists
        task.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command
        ffmpeg_path = get_ffmpeg_path()
        cmd = [
            ffmpeg_path,
            '-y',  # Overwrite output
            '-ss', str(seek_time),  # Seek to start
            '-i', str(video.path),  # Input file
            '-t', str(duration),  # Duration
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Encoding speed
            '-b:v', str(output_bitrate),  # Video bitrate
            '-c:a', 'aac',  # Audio codec
            '-b:a', '128k',  # Audio bitrate
            '-movflags', '+faststart',  # Enable streaming
            '-progress', 'pipe:1',  # Progress output
            str(task.output_path)
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        if log_callback:
            log_callback(f"开始生成: {task.description}.mp4")
        
        # Prepare subprocess arguments - hide console on Windows
        popen_kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True
        }
        if platform.system() == 'Windows':
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        try:
            self._process = subprocess.Popen(cmd, **popen_kwargs)
            logger.info(f"FFmpeg process started (PID: {self._process.pid})")
            
            task.status = "processing"
            
            # Parse progress from ffmpeg output
            while True:
                if self._stopped:
                    logger.warning("Task stopped during processing")
                    self._process.kill()
                    task.status = "failed"
                    task.error = "Task stopped"
                    return False
                
                while self._paused:
                    import time
                    time.sleep(0.1)
                
                line = self._process.stdout.readline()
                if not line:
                    break
                
                # Parse progress
                if line.startswith('out_time_ms'):
                    try:
                        out_time_us = int(line.split('=')[1])
                        progress = min(1.0, out_time_us / 1000000 / duration)
                        task.progress = progress
                        if progress_callback:
                            progress_callback(progress)
                    except (ValueError, ZeroDivisionError):
                        pass
            
            return_code = self._process.wait()
            logger.info(f"FFmpeg process finished with return code: {return_code}")
            
            if return_code == 0:
                task.status = "completed"
                task.progress = 1.0
                if progress_callback:
                    progress_callback(1.0)
                logger.info(f"Successfully created: {task.output_path.name}")
                return True
            else:
                task.status = "failed"
                stderr = self._process.stderr.read() if self._process.stderr else ""
                task.error = stderr[:500] if stderr else "Unknown error"
                logger.error(f"FFmpeg failed: {task.error}")
                return False
                
        except Exception as e:
            logger.exception(f"Exception during cut_clip: {str(e)}")
            task.status = "failed"
            task.error = str(e)
            return False
        finally:
            logger.debug("cut_clip finally block executed")
            self._process = None
    
    def pause(self):
        """Pause current task."""
        self._paused = True
    
    def resume(self):
        """Resume paused task."""
        self._paused = False
    
    def stop(self):
        """Stop current task."""
        self._stopped = True
        if self._process:
            self._process.kill()
    
    def reset(self):
        """Reset processor state."""
        self._paused = False
        self._stopped = False  # Important: reset stopped flag
        self._process = None
        self._stopped = False
