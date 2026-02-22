#!/usr/bin/env python3
"""Video Cutter - A tool for extracting video clips based on time ranges."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from .gui import main

if __name__ == "__main__":
    main()
