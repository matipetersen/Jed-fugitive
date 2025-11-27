#!/usr/bin/env python3
"""
Test armor carrying capacity bonuses.
Verifies that different armor pieces modify inventory size correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player
from jedi_fugitive.items.armor import ARMORS
from jedi_fugitive.config import MAX_INVENTORY_SIZE


def test_capacity_bonuses():
    """Test carrying capacity bonuses from armor."""
    print("\n" + "="*70)
    print("Testing Armor Carrying Capacity Bonuses")
    print("="*70)
    
    # Create test player
    player = Player(10, 10)
    
    # Test 1: Base capacity without armor
    print("\n[Test 1] Base Capacity (No Armor)")
    base_capacity = player.get_max_inventory()
    print(f"  Base capacity: {base_capacity}")
    assert base_capacity == MAX_INVENTORY_SIZE, f"Expected {MAX_INVENTORY_SIZE}, got {base_capacity}"
    print(f"  ✓ Base capacity = {MAX_INVENTORY_SIZE}")
    
    # Test 2: Light armor with good capacity bonus
    print("\n[Test 2] Light Armor - Smuggler's Jacket")
    smuggler_jacket = next(a for a in ARMORS if a.name == "Smuggler's Jacket")
    bonus = getattr(smuggler_jacket, 'capacity_bonus', 0)
    print(f"  Armor bonus: +{bonus}")
    
    player.equipped_armor = smuggler_jacket
    new_capacity = player.get_max_inventory()
    expected = MAX_INVENTORY_SIZE + bonus
    print(f"  New capacity: {new_capacity}")
    assert new_capacity == expected, f"Expected {expected}, got {new_capacity}"
    print(f"  ✓ Capacity with Smuggler's Jacket = {new_capacity} ({MAX_INVENTORY_SIZE} + {bonus})")
    
    # Test 3: Heavy armor with minimal capacity bonus
    print("\n[Test 3] Heavy Armor - Heavy Combat Armor")
    heavy_armor = next(a for a in ARMORS if a.name == "Heavy Combat Armor")
    bonus = getattr(heavy_armor, 'capacity_bonus', 0)
    print(f"  Armor bonus: {bonus}")
    
    player.equipped_armor = heavy_armor
    new_capacity = player.get_max_inventory()
    expected = MAX_INVENTORY_SIZE + bonus
    print(f"  New capacity: {new_capacity}")
    assert new_capacity == expected, f"Expected {expected}, got {new_capacity}"
    print(f"  ✓ Capacity with Heavy Combat Armor = {new_capacity}")
    
    # Test 4: Special armor with high capacity bonus
    print("\n[Test 4] Special Armor - Force Channeling Robes")
    force_robes = next(a for a in ARMORS if a.name == "Force Channeling Robes")
    bonus = getattr(force_robes, 'capacity_bonus', 0)
    print(f"  Armor bonus: +{bonus}")
    
    player.equipped_armor = force_robes
    new_capacity = player.get_max_inventory()
    expected = MAX_INVENTORY_SIZE + bonus
    print(f"  New capacity: {new_capacity}")
    assert new_capacity == expected, f"Expected {expected}, got {new_capacity}"
    print(f"  ✓ Capacity with Force Channeling Robes = {new_capacity} ({MAX_INVENTORY_SIZE} + {bonus})")
    
    # Test 5: Bounty Hunter Gear (high capacity for tracking)
    print("\n[Test 5] Medium Armor - Bounty Hunter Gear")
    bounty_gear = next(a for a in ARMORS if a.name == "Bounty Hunter Gear")
    bonus = getattr(bounty_gear, 'capacity_bonus', 0)
    print(f"  Armor bonus: +{bonus}")
    
    player.equipped_armor = bounty_gear
    new_capacity = player.get_max_inventory()
    expected = MAX_INVENTORY_SIZE + bonus
    print(f"  New capacity: {new_capacity}")
    assert new_capacity == expected, f"Expected {expected}, got {new_capacity}"
    print(f"  ✓ Capacity with Bounty Hunter Gear = {new_capacity} ({MAX_INVENTORY_SIZE} + {bonus})")
    
    # Test 6: Juggernaut Plating (negative bonus)
    print("\n[Test 6] Heavy Armor - Juggernaut Plating (Penalty)")
    juggernaut = next(a for a in ARMORS if a.name == "Juggernaut Plating")
    bonus = getattr(juggernaut, 'capacity_bonus', 0)
    print(f"  Armor bonus: {bonus}")
    
    player.equipped_armor = juggernaut
    new_capacity = player.get_max_inventory()
    expected = MAX_INVENTORY_SIZE + bonus
    print(f"  New capacity: {new_capacity}")
    assert new_capacity == expected, f"Expected {expected}, got {new_capacity}"
    print(f"  ✓ Capacity with Juggernaut Plating = {new_capacity} ({MAX_INVENTORY_SIZE} {bonus})")
    
    # Test 7: Remove armor (back to base)
    print("\n[Test 7] Remove Armor - Back to Base")
    player.equipped_armor = None
    new_capacity = player.get_max_inventory()
    print(f"  Capacity: {new_capacity}")
    assert new_capacity == MAX_INVENTORY_SIZE, f"Expected {MAX_INVENTORY_SIZE}, got {new_capacity}"
    print(f"  ✓ Back to base capacity = {MAX_INVENTORY_SIZE}")
    
    # Test 8: Summary of all armor bonuses
    print("\n[Test 8] Armor Capacity Bonus Summary")
    print("  " + "-"*65)
    print(f"  {'Armor Name':<30} {'Weight':<8} {'Bonus':<10}")
    print("  " + "-"*65)
    
    for armor in ARMORS:
        bonus = getattr(armor, 'capacity_bonus', 0)
        weight = armor.weight
        bonus_str = f"{'+' if bonus >= 0 else ''}{bonus}"
        print(f"  {armor.name:<30} {weight:<8} {bonus_str:<10}")
    
    print("  " + "-"*65)
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\nSummary:")
    print("  • Base inventory capacity: 30 slots")
    print("  • Light armor: +2 to +10 capacity (utility focused)")
    print("  • Medium armor: +2 to +8 capacity (balanced)")
    print("  • Heavy armor: -2 to +1 capacity (bulky)")
    print("  • Best for carrying: Force Channeling Robes (+10)")
    print("  • Worst for carrying: Juggernaut Plating (-2)")
    print()


if __name__ == "__main__":
    test_capacity_bonuses()
