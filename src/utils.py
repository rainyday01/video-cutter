"""Utility functions for video cutter."""
import re
from datetime import datetime
from pathlib import Path


def parse_video_filename(filename: str) -> datetime | None:
    """
    Parse video filename to extract start time.
    
    Supports formats:
    - 2026-01-15 10-45-02.mkv (OBS style)
    - 2026.01.15 10.45.02.mp4
    - 2026-01-15_10-45-00.MOV
    - 2026/2/1 16:01:33.mp4 (dashcam style, flexible month/day)
    - 2026/02/01 16:01:33.mkv
    - abcxyz_20260201_090101.mp4 (compact format with prefix)
    - Directory path like: /path/to/2026/2/1 16:01:33.mp4
    
    Args:
        filename: Video filename (with or without extension), can be full path
    
    Returns:
        datetime object or None if parsing fails
    """
    # Remove extension
    stem = Path(filename).stem
    
    # Also try full path string for dashcam style with directories
    full_str = str(filename)
    
    # Try different patterns
    patterns = [
        # yyyymmdd_hhmmss (compact format, may have prefix/suffix)
        r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',
        # yyyymmdd_hhmm (compact format, no seconds)
        r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})',
        # yyyy-mm-dd hh-mm-ss or yyyy.mm.dd hh.mm.ss (OBS style, 2-digit required)
        r'(\d{4})[-.](\d{2})[-.](\d{2})[\s_](\d{2})[-.](\d{2})[-.](\d{2})',
        # yyyy-mm-dd hh-mm (no seconds)
        r'(\d{4})[-.](\d{2})[-.](\d{2})[\s_](\d{2})[-.](\d{2})',
        # yyyy/m/d h:m:s or yyyy/mm/dd hh:mm:ss (dashcam style, flexible digits)
        # This can match both standalone filename and path with date directories
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})',
        # yyyy/m/d h:m (no seconds, dashcam style)
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})',
    ]
    
    # Try full path first (for dashcam style with directories), then stem
    for search_str in [full_str, stem]:
        for pattern in patterns:
            match = re.search(pattern, search_str)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 6:
                        return datetime(
                            int(groups[0]), int(groups[1]), int(groups[2]),
                            int(groups[3]), int(groups[4]), int(groups[5])
                        )
                    elif len(groups) == 5:
                        return datetime(
                            int(groups[0]), int(groups[1]), int(groups[2]),
                            int(groups[3]), int(groups[4]), 0
                        )
                except ValueError:
                    continue
    
    return None


def format_duration(seconds: float) -> str:
    """Format seconds to HH:MM:SS string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_video_files(folder_path: Path) -> list[Path]:
    """
    Get all video files from a folder.
    
    Args:
        folder_path: Path to folder containing videos
    
    Returns:
        List of video file paths
    """
    video_extensions = {'.mkv', '.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm'}
    videos = []
    
    if folder_path.exists() and folder_path.is_dir():
        for file in folder_path.iterdir():
            if file.is_file() and file.suffix.lower() in video_extensions:
                videos.append(file)
    
    return sorted(videos)


def find_video_for_time(videos: list[tuple[Path, datetime]], target_time: datetime) -> Path | None:
    """
    Find the video file that contains the target time.
    
    Args:
        videos: List of (video_path, start_time) tuples
        target_time: Target datetime to find
    
    Returns:
        Video path or None if not found
    """
    # Sort videos by start time
    sorted_videos = sorted(videos, key=lambda x: x[1])
    
    # Find video that should contain target time
    # We need video duration info, but for now use heuristics
    # Assume each video covers time until the next video starts
    
    for i, (video_path, start_time) in enumerate(sorted_videos):
        # If there's a next video, this one covers until that starts
        if i + 1 < len(sorted_videos):
            end_time = sorted_videos[i + 1][1]
        else:
            # Last video - assume it's long enough (we'll verify with ffmpeg)
            from datetime import timedelta
            end_time = start_time + timedelta(hours=24)  # Generous default
        
        if start_time <= target_time < end_time:
            return video_path
    
    return None
