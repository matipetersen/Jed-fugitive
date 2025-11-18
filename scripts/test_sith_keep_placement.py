#!/usr/bin/env python3
"""Test Sith Keep placement to identify crash."""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

def test_sith_keep_placement():
    """Test if Sith Keep placement works with a realistic game state."""
    print("="*60)
    print("SITH KEEP PLACEMENT TEST")
    print("="*60)
    
    try:
        print("\n1. Importing game modules...")
        from jedi_fugitive.game.player import Player
        from jedi_fugitive.game.map_features import generate_world
        from jedi_fugitive.game.level import Display
        print("   ✓ Modules imported successfully")
        
        print("\n2. Creating mock game object...")
        class MockGame:
            def __init__(self):
                self.player = Player(10, 10)
                self.game_map = []
                self.map_biomes = []
                self.map_features = {}
                self.enemies = []
                self.items_on_map = []
                self.tomb_entrances = set()
                self.player_clear_radius = 15
                self.lightsaber_weight = 3
                self.turn_count = 0
        
        game = MockGame()
        print("   ✓ Mock game created")
        
        print("\n3. Generating world with Sith Keep...")
        try:
            generate_world(game)
            print("   ✓ World generated successfully")
            
            # Check if Sith Keep was placed
            has_keep = False
            if hasattr(game, 'game_map'):
                for row in game.game_map:
                    if 'K' in row:
                        has_keep = True
                        break
            
            if has_keep:
                print("   ✓ Sith Keep ('K') found on map")
            else:
                print("   ⚠ Sith Keep not placed (may be intentional)")
            
        except Exception as e:
            print(f"   ✗ World generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n4. Testing direct Sith Keep placement...")
        try:
            from jedi_fugitive.game.sith_keep import place_sith_keep_on_map
            # Reset game for clean test
            game2 = MockGame()
            generate_world(game2)
            
            # Try direct placement
            place_sith_keep_on_map(game2)
            print("   ✓ Direct placement succeeded")
            
        except Exception as e:
            print(f"   ✗ Direct placement failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_sith_keep_placement()
    sys.exit(0 if success else 1)
