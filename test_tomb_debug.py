#!/usr/bin/env python3
"""
Test tomb entrance mechanism in detail.
"""

import sys
import os
import curses

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_tomb(stdscr):
    from jedi_fugitive.game.game_manager import GameManager
    from jedi_fugitive.game.level import Display
    
    print("=" * 70)
    print("TOMB ENTRANCE DEBUG TEST")
    print("=" * 70)
    
    # Create game instance
    game = GameManager(stdscr)

    print("\n1. Checking tomb generation...")
    tomb_count = 0
    tomb_positions = []
    for y in range(len(game.game_map)):
        for x in range(len(game.game_map[0])):
            if game.game_map[y][x] == 'D':
                tomb_count += 1
                tomb_positions.append((x, y))

    print(f"   Found {tomb_count} 'D' tiles on map")
    print(f"   Positions: {tomb_positions[:5]}...")  # First 5

    print(f"\n2. Checking tomb_entrances set...")
    tomb_entrances = getattr(game, 'tomb_entrances', None)
    print(f"   tomb_entrances attribute exists: {tomb_entrances is not None}")
    if tomb_entrances:
        print(f"   tomb_entrances content: {list(tomb_entrances)[:5]}...")  # First 5
        print(f"   tomb_entrances count: {len(tomb_entrances)}")

    print(f"\n3. Checking Display.SITH_ENTRANCE...")
    sith_entrance = getattr(Display, 'SITH_ENTRANCE', None)
    print(f"   Display.SITH_ENTRANCE = '{sith_entrance}'")

    print(f"\n4. Testing tomb entrance detection logic...")
    if tomb_positions:
        test_pos = tomb_positions[0]
        test_x, test_y = test_pos
        tile = game.game_map[test_y][test_x]
        tile_str = str(tile)
        
        print(f"   Testing position: {test_pos}")
        print(f"   Tile character: '{tile}' (type: {type(tile)})")
        print(f"   Tile as string: '{tile_str}'")
        
        # Check detection conditions
        check1 = tile_str in ("D",)
        print(f"   Check 1 - tile_str in ('D',): {check1}")
        
        check2 = tile == getattr(Display, "SITH_ENTRANCE", None)
        print(f"   Check 2 - tile == Display.SITH_ENTRANCE: {check2}")
        
        check3 = test_pos in getattr(game, "tomb_entrances", set())
        print(f"   Check 3 - position in tomb_entrances: {check3}")
        
        entrance_hit = check1 or check2 or check3
        print(f"   Overall entrance_hit: {entrance_hit}")

    print(f"\n5. Simulating player move to tomb entrance...")
    if tomb_positions:
        test_x, test_y = tomb_positions[0]
        
        # Set player near tomb
        game.player.x = test_x - 1
        game.player.y = test_y
        
        print(f"   Player starting position: ({game.player.x}, {game.player.y})")
        print(f"   Tomb entrance at: ({test_x}, {test_y})")
        print(f"   Attempting to move player to tomb entrance...")
        
        # Try to move
        try:
            result = game._try_move_player(1, 0)
            print(f"   Move result: {result}")
            print(f"   Player new position: ({game.player.x}, {game.player.y})")
            print(f"   Current floor: {getattr(game, 'current_floor', 0)}")
            print(f"   In tomb (tomb_levels exists): {getattr(game, 'tomb_levels', None) is not None}")
            
            # Check if tomb was entered
            if getattr(game, 'tomb_levels', None) is not None:
                print("   ✓ SUCCESS: Player entered tomb!")
                print(f"   Tomb has {len(game.tomb_levels)} levels")
            else:
                print("   ✗ FAILED: Player did NOT enter tomb")
                
                # Debug file check
                try:
                    with open("/tmp/jedi_fugitive_debug.txt", "r") as f:
                        debug_content = f.read()
                        print("\n   Debug log contents:")
                        print("   " + "\n   ".join(debug_content.split("\n")[-20:]))
                except:
                    print("   No debug log found at /tmp/jedi_fugitive_debug.txt")
        except Exception as e:
            print(f"   ✗ ERROR during move: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    curses.wrapper(test_tomb)
