#!/usr/bin/env python3
"""
Download ffmpeg binaries for bundling.

This script downloads ffmpeg and ffprobe binaries for different platforms.
Run this before building the application.
"""

import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path


# Download URLs for ffmpeg static builds
FFMPEG_URLS = {
    "windows": {
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "type": "zip",
        "ffmpeg": "ffmpeg.exe",
        "ffprobe": "ffprobe.exe",
        "strip_components": 1,  # Remove top-level folder
    },
    "macos": {
        # Using evermeet.cx builds (single binary)
        "ffmpeg_url": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/7z",
        "ffprobe_url": "https://evermeet.cx/ffmpeg/getrelease/ffprobe/7z",
        "type": "7z",
        "ffmpeg": "ffmpeg",
        "ffprobe": "ffprobe",
    },
    "linux": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        "type": "tar.xz",
        "ffmpeg": "ffmpeg",
        "ffprobe": "ffprobe",
        "strip_components": 1,
    }
}


def download_file(url: str, dest: Path) -> bool:
    """Download a file from URL."""
    print(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def extract_7z(archive_path: Path, dest_dir: Path) -> bool:
    """Extract 7z archive. Requires 7z or 7za command."""
    # Try different 7z commands
    for cmd in ['7z', '7za', '7zr']:
        if shutil.which(cmd):
            import subprocess
            result = subprocess.run([cmd, 'x', str(archive_path), f'-o{dest_dir}'], 
                                    capture_output=True)
            return result.returncode == 0
    
    print("Error: 7z not found. Please install p7zip.")
    return False


def download_for_windows(target_dir: Path) -> bool:
    """Download ffmpeg for Windows."""
    config = FFMPEG_URLS["windows"]
    temp_file = target_dir / "ffmpeg_temp.zip"
    
    if not download_file(config["url"], temp_file):
        return False
    
    print("Extracting...")
    try:
        with zipfile.ZipFile(temp_file, 'r') as zf:
            # Find ffmpeg and ffprobe in the zip
            for name in zf.namelist():
                if name.endswith(config["ffmpeg"]):
                    zf.extract(name, target_dir)
                    shutil.move(target_dir / name, target_dir / config["ffmpeg"])
                elif name.endswith(config["ffprobe"]):
                    zf.extract(name, target_dir)
                    shutil.move(target_dir / name, target_dir / config["ffprobe"])
        
        temp_file.unlink()
        return True
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False


def download_for_macos(target_dir: Path) -> bool:
    """Download ffmpeg for macOS."""
    config = FFMPEG_URLS["macos"]
    
    # Download ffmpeg
    temp_ffmpeg = target_dir / "ffmpeg.7z"
    if download_file(config["ffmpeg_url"], temp_ffmpeg):
        extract_7z(temp_ffmpeg, target_dir)
        temp_ffmpeg.unlink()
    
    # Download ffprobe
    temp_ffprobe = target_dir / "ffprobe.7z"
    if download_file(config["ffprobe_url"], temp_ffprobe):
        extract_7z(temp_ffprobe, target_dir)
        temp_ffprobe.unlink()
    
    # Set executable permission
    ffmpeg_path = target_dir / config["ffmpeg"]
    ffprobe_path = target_dir / config["ffprobe"]
    
    if ffmpeg_path.exists():
        ffmpeg_path.chmod(0o755)
    if ffprobe_path.exists():
        ffprobe_path.chmod(0o755)
    
    return ffmpeg_path.exists() and ffprobe_path.exists()


def download_for_linux(target_dir: Path) -> bool:
    """Download ffmpeg for Linux."""
    config = FFMPEG_URLS["linux"]
    temp_file = target_dir / "ffmpeg_temp.tar.xz"
    
    if not download_file(config["url"], temp_file):
        return False
    
    print("Extracting...")
    try:
        with tarfile.open(temp_file, 'r:xz') as tf:
            # Find ffmpeg and ffprobe
            for member in tf.getmembers():
                if member.name.endswith(config["ffmpeg"]):
                    member.name = config["ffmpeg"]
                    tf.extract(member, target_dir)
                elif member.name.endswith(config["ffprobe"]):
                    member.name = config["ffprobe"]
                    tf.extract(member, target_dir)
        
        temp_file.unlink()
        
        # Set executable permission
        ffmpeg_path = target_dir / config["ffmpeg"]
        ffprobe_path = target_dir / config["ffprobe"]
        
        if ffmpeg_path.exists():
            ffmpeg_path.chmod(0o755)
        if ffprobe_path.exists():
            ffprobe_path.chmod(0o755)
        
        return True
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False


def download_ffmpeg(target_platform: str | None = None) -> bool:
    """
    Download ffmpeg binaries for the specified platform.
    
    Args:
        target_platform: windows, macos, or linux. Auto-detect if None.
    
    Returns:
        True if successful
    """
    if target_platform is None:
        system = platform.system()
        if system == "Windows":
            target_platform = "windows"
        elif system == "Darwin":
            target_platform = "macos"
        else:
            target_platform = "linux"
    
    if target_platform not in FFMPEG_URLS:
        print(f"Unsupported platform: {target_platform}")
        return False
    
    # Create ffmpeg_bin directory
    script_dir = Path(__file__).parent
    target_dir = script_dir / "ffmpeg_bin" / target_platform
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading ffmpeg for {target_platform}...")
    print(f"Target directory: {target_dir}")
    
    if target_platform == "windows":
        success = download_for_windows(target_dir)
    elif target_platform == "macos":
        success = download_for_macos(target_dir)
    else:
        success = download_for_linux(target_dir)
    
    if success:
        print(f"\n✓ ffmpeg binaries downloaded to: {target_dir}")
        print(f"  - ffmpeg: {(target_dir / FFMPEG_URLS[target_platform]['ffmpeg']).exists()}")
        print(f"  - ffprobe: {(target_dir / FFMPEG_URLS[target_platform]['ffprobe']).exists()}")
    else:
        print(f"\n✗ Failed to download ffmpeg")
    
    return success


def download_all_platforms():
    """Download ffmpeg for all platforms."""
    success = True
    for platform_name in ["windows", "macos", "linux"]:
        print(f"\n{'='*50}")
        if not download_ffmpeg(platform_name):
            success = False
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download ffmpeg binaries for bundling")
    parser.add_argument(
        "--platform", "-p",
        choices=["windows", "macos", "linux", "all"],
        default=None,
        help="Target platform (default: auto-detect current system)"
    )
    
    args = parser.parse_args()
    
    if args.platform == "all":
        download_all_platforms()
    else:
        download_ffmpeg(args.platform)
