#!/usr/bin/env python3
"""Debug tomb entrance registration"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=== TOMB ENTRANCE DEBUG ===")
    
    from jedi_fugitive.game.game_manager import GameManager
    
    class DummyStdscr:
        def getmaxyx(self): return (40, 140)
        def getch(self): return -1
        def clear(self): pass
        def refresh(self): pass

    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    
    # Full initialization
    print("Initializing and generating world...")
    gm.initialize()
    gm.generate_world()
    
    # Check tomb entrances
    tomb_entrances = getattr(gm, 'tomb_entrances', set())
    print(f"\n📍 TOMB ENTRANCE ANALYSIS:")
    print(f"  Total tomb entrances registered: {len(tomb_entrances)}")
    
    if tomb_entrances:
        # Check if registered positions actually have 'D' on the map
        print(f"\n🔍 CHECKING ENTRANCE REGISTRATION:")
        
        for i, (tx, ty) in enumerate(list(tomb_entrances)[:5]):
            if 0 <= ty < len(gm.game_map) and 0 <= tx < len(gm.game_map[0]):
                tile_char = gm.game_map[ty][tx]
                is_correct = tile_char == 'D'
                status = "✅ CORRECT" if is_correct else f"❌ WRONG (found '{tile_char}')"
                print(f"    Tomb {i+1}: ({tx}, {ty}) = '{tile_char}' {status}")
            else:
                print(f"    Tomb {i+1}: ({tx}, {ty}) = OUT OF BOUNDS ❌")
        
        # Now scan the map for all 'D' tiles and see if they're registered
        print(f"\n🗺️  SCANNING MAP FOR 'D' TILES:")
        found_d_tiles = []
        
        for y in range(len(gm.game_map)):
            for x in range(len(gm.game_map[0])):
                if gm.game_map[y][x] == 'D':
                    found_d_tiles.append((x, y))
        
        print(f"  Total 'D' tiles found on map: {len(found_d_tiles)}")
        
        # Check if all 'D' tiles are registered
        unregistered_tiles = []
        for x, y in found_d_tiles:
            if (x, y) not in tomb_entrances:
                unregistered_tiles.append((x, y))
        
        if unregistered_tiles:
            print(f"  ❌ PROBLEM: {len(unregistered_tiles)} 'D' tiles NOT registered as entrances:")
            for x, y in unregistered_tiles[:3]:  # Show first 3
                print(f"     Unregistered 'D' at ({x}, {y})")
        else:
            print(f"  ✅ ALL 'D' tiles are properly registered as tomb entrances")
        
        # Test movement to first tomb entrance
        if tomb_entrances:
            test_pos = list(tomb_entrances)[0]
            print(f"\n🚶 TESTING MOVEMENT TO TOMB ENTRANCE {test_pos}:")
            
            # Save original position
            orig_x, orig_y = gm.player.x, gm.player.y
            
            # Move to tomb entrance
            gm.player.x, gm.player.y = test_pos
            
            # Get the tile character and test entrance detection
            tile_char = gm.game_map[test_pos[1]][test_pos[0]]
            print(f"  Player moved to ({test_pos[0]}, {test_pos[1]}) = '{tile_char}'")
            
            # Test the entrance hit logic manually
            tstr = str(tile_char)
            entrance_hit = False
            
            if tstr in ("D",):
                entrance_hit = True
                print(f"  ✅ Tile 'D' correctly triggers entrance_hit")
            
            if test_pos in tomb_entrances:
                entrance_hit = True
                print(f"  ✅ Position is registered in tomb_entrances")
            
            if entrance_hit:
                print(f"  ✅ ENTRANCE DETECTION WORKS - tomb entry should succeed")
                
                # Try the actual tomb entry
                result = gm.enter_tomb()
                if result:
                    print(f"  🎉 SUCCESS: Tomb entry worked!")
                else:
                    print(f"  ❌ FAILED: enter_tomb() returned False")
            else:
                print(f"  ❌ ENTRANCE NOT DETECTED - this is the problem!")
            
            # Restore position
            gm.player.x, gm.player.y = orig_x, orig_y
    else:
        print("  ❌ NO TOMB ENTRANCES FOUND!")
        print("  This means tomb generation failed completely.")

if __name__ == '__main__':
    main()