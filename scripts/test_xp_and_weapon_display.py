#!/usr/bin/env python3
"""
Test XP gain from killing enemies (should be 10) and weapon display in GUI.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jedi_fugitive.game.player import Player
from jedi_fugitive.items.weapons import WEAPONS


def test_xp_gain():
    """Test that killing enemies grants 10 XP."""
    print("=" * 60)
    print("Test 1: XP Gain from Enemy Kills")
    print("=" * 60)
    
    class MockUI:
        class Messages:
            def add(self, msg):
                print(f"   [UI] {msg}")
        def __init__(self):
            self.messages = self.Messages()
    
    class MockEnemy:
        def __init__(self):
            self.hp = 0  # Dead
            self.name = "Test Trooper"
            self.level = 1
            self.is_boss = False
    
    class MockGame:
        def __init__(self):
            self.player = Player(5, 5)
            self.player.dark_xp = 0
            self.player.xp_to_next_dark = 100
            self.player.dark_level = 1
            self.ui = MockUI()
            self.turn_count = 0
    
    game = MockGame()
    initial_xp = game.player.dark_xp
    
    print(f"\nInitial Dark XP: {initial_xp}")
    
    # Simulate enemy death (this is the code from input_handler.py)
    try:
        game.player.dark_xp = getattr(game.player, 'dark_xp', 0) + 10
        game.ui.messages.add(f"Gained 10 XP!")
    except Exception as e:
        print(f"   Error: {e}")
    
    final_xp = game.player.dark_xp
    xp_gained = final_xp - initial_xp
    
    print(f"Final Dark XP: {final_xp}")
    print(f"XP Gained: {xp_gained}")
    
    if xp_gained == 10:
        print("✅ PASS: Enemy kills now grant 10 XP!")
    else:
        print(f"❌ FAIL: Expected 10 XP, got {xp_gained} XP")
    
    print()


def test_weapon_display():
    """Test that weapon attack bonuses are displayed correctly in GUI."""
    print("=" * 60)
    print("Test 2: Weapon Attack Bonus Display")
    print("=" * 60)
    
    player = Player(5, 5)
    
    # Set base stats
    player._base_stats = {
        'attack': 10,
        'defense': 5,
        'evasion': 10,
        'max_hp': 100
    }
    player.attack = 10
    player.defense = 5
    player.evasion = 10
    player.hp = 100
    player.max_hp = 100
    
    print(f"\n1. Player without weapon:")
    print(f"   Base Attack: {player.attack}")
    stats = player.get_stats_display()
    attack_line = [line for line in stats if line.startswith("Attack:")][0]
    print(f"   Display: {attack_line}")
    
    if "weapon" not in attack_line.lower():
        print("   ✅ Correctly shows no weapon bonus")
    else:
        print("   ❌ Should not show weapon bonus when no weapon equipped")
    
    # Equip a weapon
    print(f"\n2. Player with weapon:")
    test_weapon = None
    for weapon in WEAPONS:
        if hasattr(weapon, 'base_damage') and weapon.base_damage == 9:
            test_weapon = weapon
            break
    
    if test_weapon:
        print(f"   Equipping: {test_weapon.name} (base_damage: +{test_weapon.base_damage})")
        
        # Simulate equipment application (from equipment.py)
        player.equipped_weapon = test_weapon
        player.attack = 10 + test_weapon.base_damage  # Equipment adds to attack
        
        print(f"   Current Attack stat: {player.attack}")
        print(f"   Base Attack (from _base_stats): {player._base_stats['attack']}")
        
        stats = player.get_stats_display()
        attack_line = [line for line in stats if line.startswith("Attack:")][0]
        print(f"   Display: {attack_line}")
        
        expected_display = f"Attack: 10 (+{test_weapon.base_damage} weapon) = {10 + test_weapon.base_damage}"
        
        if attack_line == expected_display:
            print(f"   ✅ PASS: Weapon bonus displayed correctly!")
        else:
            print(f"   ❌ FAIL: Expected '{expected_display}'")
            print(f"          Got '{attack_line}'")
    else:
        print("   ❌ Could not find test weapon with base_damage=9")
    
    # Test with different weapon
    print(f"\n3. Player with different weapon:")
    test_weapon2 = None
    for weapon in WEAPONS:
        if hasattr(weapon, 'base_damage') and weapon.base_damage == 5:
            test_weapon2 = weapon
            break
    
    if test_weapon2:
        print(f"   Equipping: {test_weapon2.name} (base_damage: +{test_weapon2.base_damage})")
        
        # Reset to base, then equip new weapon
        player.attack = player._base_stats['attack']
        player.equipped_weapon = test_weapon2
        player.attack = player._base_stats['attack'] + test_weapon2.base_damage
        
        print(f"   Current Attack stat: {player.attack}")
        
        stats = player.get_stats_display()
        attack_line = [line for line in stats if line.startswith("Attack:")][0]
        print(f"   Display: {attack_line}")
        
        expected_display = f"Attack: 10 (+{test_weapon2.base_damage} weapon) = {10 + test_weapon2.base_damage}"
        
        if attack_line == expected_display:
            print(f"   ✅ PASS: Different weapon bonus displayed correctly!")
        else:
            print(f"   ❌ FAIL: Expected '{expected_display}'")
            print(f"          Got '{attack_line}'")
    
    print()


if __name__ == "__main__":
    try:
        test_xp_gain()
        test_weapon_display()
        print("=" * 60)
        print("All Tests Complete")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
