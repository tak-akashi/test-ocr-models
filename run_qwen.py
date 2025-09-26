#!/usr/bin/env python
"""Entry point for running Qwen model tests from project root."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.run_qwen import main

if __name__ == "__main__":
    main()