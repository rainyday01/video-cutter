#!/usr/bin/env python3
"""Test script for Excel parser debugging."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.excel_parser import parse_excel_clips

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_excel_parser.py <excel_file>")
        print("\nThis script will parse the Excel file and show detailed debug logs.")
        sys.exit(1)
    
    excel_path = Path(sys.argv[1])
    
    if not excel_path.exists():
        print(f"Error: File not found: {excel_path}")
        sys.exit(1)
    
    print(f"=" * 60)
    print(f"Testing Excel Parser")
    print(f"=" * 60)
    print(f"File: {excel_path}")
    print(f"=" * 60)
    print()
    
    clips = parse_excel_clips(excel_path, debug=True)
    
    print()
    print(f"=" * 60)
    print(f"Results: {len(clips)} clips found")
    print(f"=" * 60)
    
    for i, clip in enumerate(clips, 1):
        print(f"\n{i}. {clip.description}")
        print(f"   开始: {clip.start_time}")
        print(f"   结束: {clip.end_time}")
        print(f"   时长: {clip.duration_seconds:.1f} 秒")
