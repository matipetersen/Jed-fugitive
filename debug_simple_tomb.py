#!/usr/bin/env python3
"""Simple test to check tomb placement"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=== SIMPLE TOMB TEST ===")
    
    # Test the exact same script from the scripts directory  
    from copy import deepcopy
    from jedi_fugitive.game.game_manager import GameManager
    
    class DummyStdscr:
        def getmaxyx(self): return (40, 140)
        def getch(self): return -1
        def clear(self): pass
        def refresh(self): pass
    
    # Use the same initialization as the working test script
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    
    print(f"After initialization:")
    print(f"  Player position: ({getattr(gm.player, 'x', 0)}, {getattr(gm.player, 'y', 0)})")
    print(f"  Tomb entrances: {len(getattr(gm, 'tomb_entrances', set()))}")
    print(f"  Map size: {len(gm.game_map[0]) if hasattr(gm, 'game_map') and gm.game_map else 0}x{len(gm.game_map) if hasattr(gm, 'game_map') and gm.game_map else 0}")
    print(f"  Biomes available: {hasattr(gm, 'map_biomes') and gm.map_biomes is not None}")
    
    if hasattr(gm, 'tomb_entrances') and gm.tomb_entrances:
        print(f"  SUCCESS: Found {len(gm.tomb_entrances)} tomb entrances!")
        for i, (tx, ty) in enumerate(list(gm.tomb_entrances)[:3]):
            print(f"    Tomb {i+1}: ({tx}, {ty})")
        
        # Test entering the first tomb
        first_tomb = list(gm.tomb_entrances)[0]
        print(f"\nTesting entry to tomb at {first_tomb}")
        
        # Move player to tomb entrance
        gm.player.x, gm.player.y = first_tomb
        
        result = gm.enter_tomb()
        print(f"  Tomb entry result: {result}")
        
        if result:
            print("  SUCCESS: Entered tomb successfully!")
            print(f"  Current tomb floor: {getattr(gm, 'tomb_floor', 'unknown')}")
            print(f"  Tomb levels generated: {len(getattr(gm, 'tomb_levels', []))}")
        else:
            print("  FAILED: Could not enter tomb")
    else:
        print("  ERROR: No tomb entrances found!")
        
        # Try to manually call tomb placement
        print("\nTrying manual tomb placement...")
        try:
            from jedi_fugitive.game import map_features
            
            # Check if biomes exist
            if hasattr(gm, 'map_biomes') and gm.map_biomes:
                print("  Biomes exist, calling placement...")
                # Reset tomb entrances
                gm.tomb_entrances = set()
                
                # Call the tomb placement part manually
                map_features.place_map_features(gm)
                
                print(f"  After manual placement: {len(getattr(gm, 'tomb_entrances', set()))} tomb entrances")
            else:
                print("  No biomes found - this may be the issue!")
        except Exception as e:
            print(f"  Manual placement failed: {e}")

if __name__ == '__main__':
    main()