#!/usr/bin/env python3
"""Test player starting stats."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player

player = Player(x=0, y=0)

print("="*50)
print("PLAYER STARTING STATS TEST")
print("="*50)

print(f"\n✓ Starting HP: {player.hp}")
print(f"✓ Max HP: {player.max_hp}")
print(f"✓ Attack: {player.attack}")
print(f"✓ Defense: {player.defense}")
print(f"✓ Evasion: {player.evasion}")
print(f"✓ Accuracy: {player.accuracy}")

assert player.hp == 15, f"Expected starting HP 15, got {player.hp}"
assert player.max_hp == 15, f"Expected max HP 15, got {player.max_hp}"

print("\n" + "="*50)
print("✅ Player starts with 15 HP (was 10)")
print("="*50)
