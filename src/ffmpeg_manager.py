"""FFmpeg binary manager - handles bundled or system ffmpeg."""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path


def get_subprocess_args(**kwargs) -> dict:
    """
    Get subprocess arguments with Windows console window hidden.
    
    On Windows, this prevents command prompt windows from appearing
    when running ffmpeg/ffprobe commands.
    
    Args:
        **kwargs: Additional subprocess arguments
    
    Returns:
        Dict of subprocess arguments
    """
    args = {
        'capture_output': kwargs.get('capture_output', True),
        'text': kwargs.get('text', True),
        'timeout': kwargs.get('timeout', 30),
    }
    
    # On Windows, hide the console window
    if platform.system() == 'Windows':
        args['creationflags'] = subprocess.CREATE_NO_WINDOW
    else:
        # On Unix, we can use start_new_session to detach from terminal
        args['start_new_session'] = True
    
    # Merge with any additional kwargs
    for key, value in kwargs.items():
        if key not in ['capture_output', 'text', 'timeout']:
            args[key] = value
    
    return args


def get_bundled_ffmpeg_dir() -> Path | None:
    """Get the directory containing bundled ffmpeg binaries."""
    system = platform.system()
    if system == "Windows":
        platform_name = "windows"
    elif system == "Darwin":
        platform_name = "macos"
    else:
        platform_name = "linux"
    
    # When running from source
    source_dir = Path(__file__).parent.parent / "ffmpeg_bin" / platform_name
    if source_dir.exists():
        return source_dir
    
    # Also check flat structure (ffmpeg_bin directly)
    flat_dir = Path(__file__).parent.parent / "ffmpeg_bin"
    if flat_dir.exists():
        return flat_dir
    
    # When running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Check platform-specific directory first
        bundle_dir = Path(sys._MEIPASS) / "ffmpeg_bin" / platform_name
        if bundle_dir.exists():
            return bundle_dir
        # Then check flat structure
        flat_bundle = Path(sys._MEIPASS) / "ffmpeg_bin"
        if flat_bundle.exists():
            return flat_bundle
    
    return None


def get_ffmpeg_path() -> str:
    """
    Get the path to ffmpeg executable.
    
    Priority:
    1. Bundled ffmpeg binary
    2. System ffmpeg in PATH
    
    Returns:
        Path to ffmpeg executable
    """
    bundled_dir = get_bundled_ffmpeg_dir()
    
    if bundled_dir:
        system = platform.system()
        if system == "Windows":
            ffmpeg_path = bundled_dir / "ffmpeg.exe"
        else:
            ffmpeg_path = bundled_dir / "ffmpeg"
        
        if ffmpeg_path.exists():
            return str(ffmpeg_path)
    
    # Fall back to system ffmpeg
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """
    Get the path to ffprobe executable.
    
    Priority:
    1. Bundled ffprobe binary
    2. System ffprobe in PATH
    
    Returns:
        Path to ffprobe executable
    """
    bundled_dir = get_bundled_ffmpeg_dir()
    
    if bundled_dir:
        system = platform.system()
        if system == "Windows":
            ffprobe_path = bundled_dir / "ffprobe.exe"
        else:
            ffprobe_path = bundled_dir / "ffprobe"
        
        if ffprobe_path.exists():
            return str(ffprobe_path)
    
    # Fall back to system ffprobe
    return "ffprobe"


def check_ffmpeg() -> tuple[bool, str]:
    """
    Check if ffmpeg is available.
    
    Returns:
        Tuple of (is_available, version_or_error_message)
    """
    ffmpeg_path = get_ffmpeg_path()
    
    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            **get_subprocess_args(timeout=10)
        )
        
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            return True, first_line
        else:
            return False, f"ffmpeg 执行失败: {result.stderr[:100] if result.stderr else 'Unknown error'}"
            
    except FileNotFoundError:
        return False, "未找到 ffmpeg，请安装 ffmpeg 或使用包含 ffmpeg 的打包版本"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg 响应超时"
    except Exception as e:
        return False, f"检查 ffmpeg 时出错: {str(e)}"


def check_ffprobe() -> tuple[bool, str]:
    """
    Check if ffprobe is available.
    
    Returns:
        Tuple of (is_available, version_or_error_message)
    """
    ffprobe_path = get_ffprobe_path()
    
    try:
        result = subprocess.run(
            [ffprobe_path, "-version"],
            **get_subprocess_args(timeout=10)
        )
        
        if result.returncode == 0:
            first_line = result.stdout.split('\n')[0]
            return True, first_line
        else:
            return False, f"ffprobe 执行失败: {result.stderr[:100] if result.stderr else 'Unknown error'}"
            
    except FileNotFoundError:
        return False, "未找到 ffprobe"
    except subprocess.TimeoutExpired:
        return False, "ffprobe 响应超时"
    except Exception as e:
        return False, f"检查 ffprobe 时出错: {str(e)}"


def download_ffmpeg(target_dir: Path, platform_name: str | None = None) -> bool:
    """
    Download ffmpeg binaries for the current platform.
    
    Args:
        target_dir: Directory to save ffmpeg binaries
        platform_name: Override platform detection (windows/macos/linux)
    
    Returns:
        True if download successful
    """
    import urllib.request
    import zipfile
    import tarfile
    
    if platform_name is None:
        system = platform.system()
        if system == "Windows":
            platform_name = "windows"
        elif system == "Darwin":
            platform_name = "macos"
        else:
            platform_name = "linux"
    
    # FFmpeg download URLs (using github releases or official builds)
    urls = {
        "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "macos": "https://evermeet.cx/ffmpeg/getrelease/7z",  # Or use homebrew bottle
        "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    }
    
    if platform_name not in urls:
        print(f"Unsupported platform: {platform_name}")
        return False
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading ffmpeg for {platform_name}...")
    
    # This is a placeholder - actual implementation would need to:
    # 1. Download the archive
    # 2. Extract ffmpeg and ffprobe binaries
    # 3. Set executable permissions on Unix
    
    print("Note: Please download ffmpeg manually for now.")
    print(f"Place ffmpeg and ffprobe binaries in: {target_dir}")
    
    return False


if __name__ == "__main__":
    # Test ffmpeg detection
    print("Checking ffmpeg...")
    available, msg = check_ffmpeg()
    print(f"  Available: {available}")
    print(f"  Message: {msg}")
    print(f"  Path: {get_ffmpeg_path()}")
    
    print("\nChecking ffprobe...")
    available, msg = check_ffprobe()
    print(f"  Available: {available}")
    print(f"  Message: {msg}")
    print(f"  Path: {get_ffprobe_path()}")
