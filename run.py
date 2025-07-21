#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from engagement_analyzer import main

if __name__ == '__main__':
    main()