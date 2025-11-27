#!/usr/bin/env python3
"""
Quick helper script to find nearest tomb entrance from player position.
Run this while playing to locate tombs.
"""

import sys
import os

# Mock game state - replace these with actual values when testing
print("=" * 70)
print("TOMB FINDER - Locate nearest tomb entrance")
print("=" * 70)

print("\nTo use this while playing:")
print("1. Note your player position (x, y)")
print("2. Check the debug file: /tmp/jedi_fugitive_debug.txt")
print("3. Look for lines like: 'tomb_entrances={...}'")
print("")
print("Or check the game UI message at start:")
print("  'World ready: X items placed, Y tomb entrances.'")
print("")
print("Tomb entrances are marked with 'D' on the map.")
print("They appear in BOLD RED color.")
print("")
print("TIP: Use the compass feature (press 'c') to scan for nearby tombs!")
print("=" * 70)
