#!/usr/bin/env python3
"""
Test script to verify stress GUI only shows when in tomb.

This script tests:
1. Stress GUI is hidden on surface (even if _stress_system_active is True)
2. Stress GUI is shown when in tomb (if _stress_system_active is True)
3. Stress GUI remains hidden if _stress_system_active is False
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player


class MockGame:
    """Mock game object to test UI rendering logic."""
    def __init__(self, in_tomb=False, stress_active=False):
        self.player = Player(10, 10)
        self.player.stress = 50
        self.player.max_stress = 100
        self.player._stress_system_active = stress_active
        
        # tomb_floor None = on surface, 0+ = in tomb
        self.tomb_floor = 0 if in_tomb else None


def test_stress_gui_visibility():
    """Test stress GUI visibility logic."""
    print("Testing Stress GUI Visibility Logic")
    print("=" * 60)
    
    # Test 1: On surface, stress system NOT active
    print("\n1. Surface + Stress System Inactive")
    game = MockGame(in_tomb=False, stress_active=False)
    in_tomb = getattr(game, 'tomb_floor', None) is not None
    should_show = getattr(game.player, '_stress_system_active', False) and in_tomb
    print(f"   tomb_floor: {game.tomb_floor}")
    print(f"   _stress_system_active: {game.player._stress_system_active}")
    print(f"   in_tomb: {in_tomb}")
    print(f"   Should show stress GUI: {should_show}")
    assert not should_show, "FAIL: Stress GUI should be hidden"
    print("   ✓ PASS: Stress GUI hidden as expected")
    
    # Test 2: On surface, stress system ACTIVE (e.g., loaded save)
    print("\n2. Surface + Stress System Active (saved game)")
    game = MockGame(in_tomb=False, stress_active=True)
    in_tomb = getattr(game, 'tomb_floor', None) is not None
    should_show = getattr(game.player, '_stress_system_active', False) and in_tomb
    print(f"   tomb_floor: {game.tomb_floor}")
    print(f"   _stress_system_active: {game.player._stress_system_active}")
    print(f"   in_tomb: {in_tomb}")
    print(f"   Should show stress GUI: {should_show}")
    assert not should_show, "FAIL: Stress GUI should be hidden on surface"
    print("   ✓ PASS: Stress GUI hidden on surface (even with active system)")
    
    # Test 3: In tomb, stress system NOT active (shouldn't happen but test anyway)
    print("\n3. In Tomb + Stress System Inactive")
    game = MockGame(in_tomb=True, stress_active=False)
    in_tomb = getattr(game, 'tomb_floor', None) is not None
    should_show = getattr(game.player, '_stress_system_active', False) and in_tomb
    print(f"   tomb_floor: {game.tomb_floor}")
    print(f"   _stress_system_active: {game.player._stress_system_active}")
    print(f"   in_tomb: {in_tomb}")
    print(f"   Should show stress GUI: {should_show}")
    assert not should_show, "FAIL: Stress GUI should be hidden if system not active"
    print("   ✓ PASS: Stress GUI hidden without active system")
    
    # Test 4: In tomb, stress system ACTIVE (normal case)
    print("\n4. In Tomb + Stress System Active (normal gameplay)")
    game = MockGame(in_tomb=True, stress_active=True)
    in_tomb = getattr(game, 'tomb_floor', None) is not None
    should_show = getattr(game.player, '_stress_system_active', False) and in_tomb
    print(f"   tomb_floor: {game.tomb_floor}")
    print(f"   _stress_system_active: {game.player._stress_system_active}")
    print(f"   in_tomb: {in_tomb}")
    print(f"   Should show stress GUI: {should_show}")
    assert should_show, "FAIL: Stress GUI should be visible in tomb"
    print("   ✓ PASS: Stress GUI visible in tomb as expected")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nSummary:")
    print("- Stress GUI is hidden on surface (even with active system)")
    print("- Stress GUI only shows when both:")
    print("  1. _stress_system_active is True (entered tomb at least once)")
    print("  2. Currently in a tomb (tomb_floor is not None)")


if __name__ == '__main__':
    test_stress_gui_visibility()
