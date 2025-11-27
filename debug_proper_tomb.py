#!/usr/bin/env python3
"""Test tomb generation with proper world setup"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=== PROPER TOMB TEST ===")
    
    from jedi_fugitive.game.game_manager import GameManager
    
    class DummyStdscr:
        def getmaxyx(self): return (40, 140)
        def getch(self): return -1
        def clear(self): pass
        def refresh(self): pass

    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    
    # Do the full initialization 
    print("Step 1: Initialize game...")
    gm.initialize()
    
    print("Step 2: Generate world (this should create tomb entrances)...")
    gm.generate_world()
    
    # Now check results
    print(f"\nAfter full initialization:")
    print(f"  Map size: {len(gm.game_map[0])}x{len(gm.game_map)} (should be > 0)")
    print(f"  Tomb entrances: {len(getattr(gm, 'tomb_entrances', set()))} (should be > 0)")
    print(f"  Biomes exist: {hasattr(gm, 'map_biomes') and gm.map_biomes is not None}")
    
    tomb_entrances = getattr(gm, 'tomb_entrances', set())
    if tomb_entrances:
        print(f"\n✅ SUCCESS: {len(tomb_entrances)} tomb entrances found!")
        
        # Show first few tomb locations
        for i, (tx, ty) in enumerate(list(tomb_entrances)[:5]):
            tile_char = gm.game_map[ty][tx] if (0 <= ty < len(gm.game_map) and 0 <= tx < len(gm.game_map[0])) else '?'
            print(f"  Tomb {i+1}: ({tx}, {ty}) = '{tile_char}'")
        
        # Test entering a tomb
        first_tomb = list(tomb_entrances)[0]
        print(f"\n🚪 Testing tomb entry at {first_tomb}...")
        
        # Move player to tomb entrance
        gm.player.x, gm.player.y = first_tomb
        
        result = gm.enter_tomb()
        if result:
            print("✅ SUCCESS: Entered tomb!")
            print(f"   Tomb floors: {len(getattr(gm, 'tomb_levels', []))}")
            print("   🎉 TOMB ENTRY WORKS!")
        else:
            print("❌ FAILED: Could not enter tomb")
            
    else:
        print("❌ ERROR: Still no tomb entrances after world generation!")
        
        # Debug info
        if hasattr(gm, 'game_map') and gm.game_map:
            print(f"   Map was created: {len(gm.game_map[0])}x{len(gm.game_map)}")
        else:
            print("   No game map created!")
            
        if hasattr(gm, 'map_biomes') and gm.map_biomes:
            # Count biomes
            biome_counts = {}
            for row in gm.map_biomes:
                for biome in row:
                    if biome:
                        biome_counts[biome] = biome_counts.get(biome, 0) + 1
            print(f"   Biomes found: {biome_counts}")
        else:
            print("   No biomes created!")

if __name__ == '__main__':
    main()