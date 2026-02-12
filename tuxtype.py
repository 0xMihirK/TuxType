#!/usr/bin/env python3
"""
TuxType - Terminal Typing Test Application

A terminal-based typing speed test application inspired by monkeytype.com.
Built with Python using Textual and Rich.

Usage:
    python tuxtype.py
    python tuxtype.py --mode words --count 100
    python tuxtype.py --mode time --time 60
    python tuxtype.py --help
"""

import sys
from src.main import main

if __name__ == "__main__":
    sys.exit(main())
