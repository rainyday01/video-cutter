#!/usr/bin/env python3
"""
Build script for Video Cutter application.
Creates standalone executables for Windows, macOS, and Linux.
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent


def get_platform_name() -> str:
    """Get current platform name."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"


def get_ffmpeg_bin_dir() -> Path:
    """Get ffmpeg binary directory for current platform."""
    return get_project_root() / "ffmpeg_bin" / get_platform_name()


def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    root = get_project_root()
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_remove:
        dir_path = root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    # Remove .spec files
    for spec_file in root.glob("*.spec"):
        spec_file.unlink()
        print(f"  Removed: {spec_file}")
    
    # Remove __pycache__ in src
    src_pycache = root / "src" / "__pycache__"
    if src_pycache.exists():
        shutil.rmtree(src_pycache)
        print(f"  Removed: {src_pycache}")


def check_ffmpeg_bundled() -> bool:
    """Check if ffmpeg binaries are bundled."""
    ffmpeg_dir = get_ffmpeg_bin_dir()
    system = platform.system()
    
    if system == "Windows":
        ffmpeg = ffmpeg_dir / "ffmpeg.exe"
        ffprobe = ffmpeg_dir / "ffprobe.exe"
    else:
        ffmpeg = ffmpeg_dir / "ffmpeg"
        ffprobe = ffmpeg_dir / "ffprobe"
    
    if ffmpeg.exists() and ffprobe.exists():
        print(f"[OK] Found bundled ffmpeg: {ffmpeg_dir}")
        return True
    else:
        print(f"[WARN] Bundled ffmpeg not found: {ffmpeg_dir}")
        print("  Run 'python download_ffmpeg.py' to download ffmpeg binaries")
        return False


def build_pyinstaller(one_file: bool = True, windowed: bool = True):
    """Build application using PyInstaller."""
    root = get_project_root()
    
    # Check PyInstaller
    if not shutil.which("pyinstaller"):
        print("Error: PyInstaller not found. Install with: pip install pyinstaller")
        return False
    
    # Build command - use ASCII-safe name
    cmd = [
        "pyinstaller",
        "--name", "VideoCutter",
        "--clean",
    ]
    
    # Add bundled ffmpeg if available
    ffmpeg_dir = get_ffmpeg_bin_dir()
    if ffmpeg_dir.exists():
        # Add ffmpeg binaries
        system = platform.system()
        if system == "Windows":
            ffmpeg = ffmpeg_dir / "ffmpeg.exe"
            ffprobe = ffmpeg_dir / "ffprobe.exe"
        else:
            ffmpeg = ffmpeg_dir / "ffmpeg"
            ffprobe = ffmpeg_dir / "ffprobe"
        
        if ffmpeg.exists():
            cmd.extend(["--add-binary", f"{ffmpeg}:ffmpeg_bin"])
        if ffprobe.exists():
            cmd.extend(["--add-binary", f"{ffprobe}:ffmpeg_bin"])
    
    # Platform-specific options
    if platform.system() == "Darwin":
        # macOS specific
        cmd.extend(["--osx-bundle-identifier", "com.video-cutter.app"])
    
    # One file or directory
    if one_file:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Windowed or console
    if windowed:
        cmd.append("--windowed")
    else:
        cmd.append("--console")
    
    # Add icon if exists
    icon_path = root / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Entry point
    cmd.append("main.py")
    
    print("Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=root)
    
    if result.returncode == 0:
        print("\n[OK] Build successful!")
        dist_dir = root / "dist"
        if one_file:
            print(f"  Executable: {dist_dir}")
        else:
            print(f"  App bundle: {dist_dir}")
        return True
    else:
        print("\n[FAIL] Build failed!")
        return False


def build_windows_installer():
    """Build Windows installer using NSIS or Inno Setup."""
    # This would require NSIS or Inno Setup to be installed
    print("Windows installer creation requires NSIS or Inno Setup")
    print("Using PyInstaller output is sufficient for distribution")
    return False


def build_macos_dmg():
    """Build macOS DMG."""
    # Use hdiutil to create DMG
    print("macOS DMG creation requires additional tools")
    print("Using PyInstaller .app bundle is sufficient for distribution")
    return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Video Cutter application")
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--dir", "-d",
        action="store_true",
        help="Build as directory (not single file)"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with console window (for debugging)"
    )
    parser.add_argument(
        "--check-ffmpeg",
        action="store_true",
        help="Only check if ffmpeg is bundled"
    )
    
    args = parser.parse_args()
    
    if args.check_ffmpeg:
        check_ffmpeg_bundled()
        return
    
    if args.clean:
        clean_build()
    
    print(f"\n{'='*50}")
    print(f"Building for: {get_platform_name()}")
    print(f"{'='*50}\n")
    
    check_ffmpeg_bundled()
    
    success = build_pyinstaller(
        one_file=not args.dir,
        windowed=not args.console
    )
    
    if success:
        print("\n" + "="*50)
        print("Build complete!")
        print("="*50)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
