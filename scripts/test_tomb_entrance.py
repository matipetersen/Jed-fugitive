#!/usr/bin/env python3
"""Test tomb entrance functionality."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from jedi_fugitive.game import map_features
from jedi_fugitive.game.player import Player
from jedi_fugitive.game.level import Display

# Mock UI
class MockMessages:
    def add(self, msg):
        print(f"[MSG] {msg}")

class MockUI:
    messages = MockMessages()

# Mock game
class MockGame:
    def __init__(self):
        self.player = Player(5, 5)
        self.player.inventory = []
        self.player.los_radius = 6
        self.ui = MockUI()
        self.game_map = [['.' for _ in range(80)] for _ in range(24)]
        self.items_on_map = []
        self.enemies = []
        self.tomb_entrances = {(5, 5)}  # Player is on a tomb entrance
        self.turn_count = 0
        
def test_tomb_entrance():
    """Test entering a tomb."""
    print("\n" + "="*60)
    print("TEST: TOMB ENTRANCE")
    print("="*60)
    
    game = MockGame()
    
    print(f"\nBefore entering tomb:")
    print(f"  Player position: ({game.player.x}, {game.player.y})")
    print(f"  Tomb entrances: {game.tomb_entrances}")
    print(f"  LOS radius: {game.player.los_radius}")
    print(f"  Game map size: {len(game.game_map)}x{len(game.game_map[0])}")
    
    try:
        print(f"\nCalling enter_tomb()...")
        result = map_features.enter_tomb(game)
        print(f"Result: {result}")
        
        if result:
            print(f"\n✓ Successfully entered tomb!")
            print(f"\nAfter entering tomb:")
            print(f"  Player position: ({game.player.x}, {game.player.y})")
            print(f"  LOS radius: {game.player.los_radius}")
            print(f"  Tomb floor: {getattr(game, 'tomb_floor', 'NOT SET')}")
            print(f"  Number of tomb levels: {len(getattr(game, 'tomb_levels', []))}")
            print(f"  Current map size: {len(game.game_map)}x{len(game.game_map[0])}")
            print(f"  Number of enemies: {len(game.enemies)}")
            print(f"  Surface map saved: {hasattr(game, 'surface_map')}")
            
            # Check if tomb levels were generated
            if hasattr(game, 'tomb_levels') and game.tomb_levels:
                print(f"\n  Tomb level details:")
                for i, level in enumerate(game.tomb_levels):
                    print(f"    Level {i}: {len(level)}x{len(level[0])}")
                    
                # Check stairs
                if hasattr(game, 'tomb_stairs'):
                    print(f"\n  Stairs positions:")
                    for i, stairs in enumerate(game.tomb_stairs):
                        print(f"    Level {i}: {stairs}")
        else:
            print(f"\n✗ Failed to enter tomb")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run test."""
    print("\n" + "#"*60)
    print("# TESTING TOMB ENTRANCE")
    print("#"*60)
    
    test_tomb_entrance()
    
    print("\n" + "#"*60)
    print("# TEST COMPLETE")
    print("#"*60)

if __name__ == "__main__":
    main()
