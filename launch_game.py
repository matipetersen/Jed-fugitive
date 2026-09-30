#!/usr/bin/env python3
"""
Quick Launch Script for Jedi Fugitive
Sets up Python path and launches the game
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Launch game
from jedi_fugitive.main import main

if __name__ == "__main__":
    main()
