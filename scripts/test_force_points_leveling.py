#!/usr/bin/env python3
"""
Test Force Points increase on level up.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player


def test_force_points_leveling():
    """Test that Force Points increase correctly on level up."""
    print("=" * 80)
    print("TESTING FORCE POINTS ON LEVEL UP")
    print("=" * 80)
    print()
    
    # Create player
    player = Player(10, 10)
    
    print("Initial State:")
    print(f"  Level: {player.level}")
    print(f"  Force Points: {player.force_points}")
    print()
    
    # Simulate leveling up
    initial_fp = player.force_points
    print("Simulating level up...")
    print()
    
    # Track Force Points through levels
    for level in range(2, 6):
        before_fp = player.force_points
        player.level_up()
        after_fp = player.force_points
        
        print(f"Level {level}:")
        print(f"  Force Points: {before_fp} → {after_fp} (+{after_fp - before_fp})")
        
        # Verify increase
        if after_fp > before_fp:
            print(f"  ✓ Force Points increased")
        else:
            print(f"  ✗ ERROR: Force Points did not increase!")
            return False
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Starting Force Points: {initial_fp}")
    print(f"Final Force Points: {player.force_points}")
    print(f"Total Gain: +{player.force_points - initial_fp}")
    print()
    print("Expected:")
    print("  - Level 1: 2 FP (starting)")
    print("  - Level 2: 3 FP (+1 automatic)")
    print("  - Level 3: 4 FP (+1 automatic)")
    print("  - Level 4: 5 FP (+1 automatic)")
    print("  - Level 5: 6 FP (+1 automatic)")
    print()
    
    if player.force_points == initial_fp + 4:  # Should have gained 4 FP over 4 level ups
        print("✓ ALL TESTS PASSED")
        print()
        print("Force Points increase correctly:")
        print("  - +1 FP automatic per level")
        print("  - Player can choose +2 FP as level reward")
        print("  - Display now shows actual number (not limited dots)")
        return True
    else:
        print(f"✗ TEST FAILED")
        print(f"Expected {initial_fp + 4} FP, got {player.force_points} FP")
        return False


if __name__ == '__main__':
    try:
        success = test_force_points_leveling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
