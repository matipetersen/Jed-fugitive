#!/usr/bin/env python3
"""
Test weapon equipping to verify attack display works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player
from jedi_fugitive.items.weapons import WEAPONS

# Create a player
player = Player(x=5, y=5)

print("="*60)
print("TESTING WEAPON EQUIP SYSTEM")
print("="*60)

print(f"\nInitial state:")
print(f"  player.attack = {player.attack}")
print(f"  player._base_stats['attack'] = {player._base_stats.get('attack', 'NOT SET')}")
print(f"  player.equipped_weapon = {player.equipped_weapon}")

# Get a weapon
test_weapon = WEAPONS[0]  # First weapon
print(f"\nTest weapon: {test_weapon.name}")
print(f"  base_damage = {test_weapon.base_damage}")

# Simulate equipping (we'll do it manually since we don't have a full game object)
print(f"\nEquipping weapon...")

# What _apply_equipment_effects should do:
old_attack = player.attack
player.attack = player.attack + test_weapon.base_damage
player.equipped_weapon = test_weapon

print(f"  old attack: {old_attack}")
print(f"  weapon bonus: {test_weapon.base_damage}")
print(f"  new attack: {player.attack}")

# Now test get_stats_display
print(f"\nget_stats_display output:")
stats_lines = player.get_stats_display()
for line in stats_lines:
    if 'Attack' in line:
        print(f"  {line}")

print(f"\n" + "="*60)
print("Expected: Attack line should show base + bonus")
print(f"Expected format: 'Attack: 10 (+{test_weapon.base_damage} weapon) = {10 + test_weapon.base_damage}'")
print("="*60)
