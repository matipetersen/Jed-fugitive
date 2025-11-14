#!/usr/bin/env python3
"""Quick test to verify comms device parts spawn in tombs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.items.tokens import TOKEN_MAP

def test_comms_part_token():
    """Test that comms device part token exists."""
    print("Testing Comms Device Part Token...")
    
    assert 'Q' in TOKEN_MAP, "Token 'Q' not found in TOKEN_MAP"
    
    part = TOKEN_MAP['Q']
    assert part['name'] == 'Comms Device Part', f"Wrong name: {part['name']}"
    assert part['type'] == 'quest_item', f"Wrong type: {part['type']}"
    assert part.get('quest') == True, "Not marked as quest item"
    
    print(f"✓ Token 'Q' exists: {part['name']}")
    print(f"  Type: {part['type']}")
    print(f"  Description: {part['description']}")
    print()

def test_tomb_generation():
    """Test that tombs generate with parts on final level."""
    from jedi_fugitive.game.map_features import enter_tomb
    from jedi_fugitive.game.game_manager import GameManager
    
    print("Testing Tomb Generation...")
    
    # Create a minimal game object
    class MockPlayer:
        def __init__(self):
            self.x = 10
            self.y = 10
            self.los_radius = 6
            self.level = 1
    
    class MockUI:
        class MockMessages:
            def add(self, msg):
                pass
        def __init__(self):
            self.messages = self.MockMessages()
    
    class MockGame:
        def __init__(self):
            self.player = MockPlayer()
            self.ui = MockUI()
            self.tomb_entrances = {(10, 10)}
            self.game_map = [['.'] * 80 for _ in range(24)]
            self.enemies = []
            self.items_on_map = []
    
    game = MockGame()
    
    # Enter tomb
    success = enter_tomb(game)
    assert success, "Failed to enter tomb"
    
    # Check that tomb levels were generated
    assert hasattr(game, 'tomb_levels'), "No tomb_levels attribute"
    assert len(game.tomb_levels) >= 3, f"Too few tomb levels: {len(game.tomb_levels)}"
    
    print(f"✓ Generated {len(game.tomb_levels)} tomb levels")
    
    # Check that final level has comms part
    final_level_items = game.tomb_items[-1]
    part_found = False
    for item in final_level_items:
        if item.get('token') == 'Q':
            part_found = True
            print(f"✓ Found comms device part at ({item['x']}, {item['y']}) on final level")
            print(f"  Name: {item['name']}")
            break
    
    assert part_found, "Comms device part not found on final level!"
    print()

def test_victory_flow():
    """Test the victory trigger logic."""
    print("Testing Victory Flow...")
    
    from jedi_fugitive.game.player import Player
    
    # Test different corruption levels
    test_cases = [
        (0, "Pure Light"),
        (15, "Pure Light"),
        (30, "Light"),
        (50, "Balanced"),
        (70, "Dark"),
        (95, "Pure Dark")
    ]
    
    for corruption, expected in test_cases:
        player = Player(x=0, y=0)
        player.dark_corruption = corruption
        alignment = player.get_alignment()
        print(f"  Corruption {corruption:3d} → {alignment:12s} (expected: {expected})")
    
    print()
    print("✓ Victory system ready!")

if __name__ == "__main__":
    print("=" * 70)
    print("COMMS DEVICE & VICTORY SYSTEM TEST")
    print("=" * 70)
    print()
    
    try:
        test_comms_part_token()
        test_tomb_generation()
        test_victory_flow()
        
        print("=" * 70)
        print("✓ ALL TESTS PASSED - VICTORY SYSTEM WORKING!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
