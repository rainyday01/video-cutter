#!/usr/bin/env python3
"""Video Cutter - A tool for extracting video clips based on time ranges."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.gui import main

if __name__ == "__main__":
    main()
