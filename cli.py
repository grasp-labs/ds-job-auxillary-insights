#!/usr/bin/env python3
"""Convenience wrapper for the CLI - sets PYTHONPATH and runs the main CLI."""

import os
import sys
from pathlib import Path

# Add src/ to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the main CLI
from cli.main import main

if __name__ == "__main__":
    sys.exit(main())

