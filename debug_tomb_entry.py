#!/usr/bin/env python3
"""Debug tomb entry issues"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display

class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

def main():
    print("=== TOMB ENTRY DIAGNOSIS ===")
    
    # Initialize game
    stdscr = DummyStdscr()
    game = GameManager(stdscr)
    game.initialize()
    
    # Check player position and tomb entrances
    px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
    print(f"Player position: ({px}, {py})")
    
    # Check tomb entrances
    tomb_entrances = getattr(game, 'tomb_entrances', set())
    print(f"Tomb entrances found: {len(tomb_entrances)}")
    print(f"Tomb entrance positions: {list(tomb_entrances)[:5]}...")  # First 5
    
    # Check what's at player position
    if hasattr(game, 'game_map') and game.game_map:
        max_y = len(game.game_map)
        max_x = len(game.game_map[0]) if max_y > 0 else 0
        if 0 <= py < max_y and 0 <= px < max_x:
            tile_at_player = game.game_map[py][px]
            print(f"Tile at player position: '{tile_at_player}' (type: {type(tile_at_player)})")
            print(f"SITH_ENTRANCE constant: '{getattr(Display, 'SITH_ENTRANCE', 'NOT_FOUND')}'")
        else:
            print("Player position is out of bounds!")
    
    # Check nearby area for tomb entrances
    print("\nNearby area (5x5 around player):")
    for dy in range(-2, 3):
        row = ""
        for dx in range(-2, 3):
            nx, ny = px + dx, py + dy
            if 0 <= ny < len(game.game_map) and 0 <= nx < len(game.game_map[0]):
                tile = game.game_map[ny][nx]
                if (nx, ny) == (px, py):
                    row += f"[{tile}]"  # Mark player position
                elif (nx, ny) in tomb_entrances:
                    row += f"({tile})"  # Mark tomb entrance
                else:
                    row += f" {tile} "
            else:
                row += " ? "
        print(f"  {row}")
    
    # Try to find nearest tomb entrance
    if tomb_entrances:
        nearest = min(tomb_entrances, key=lambda pos: abs(pos[0] - px) + abs(pos[1] - py))
        dist = abs(nearest[0] - px) + abs(nearest[1] - py)
        print(f"\nNearest tomb entrance: {nearest} (distance: {dist})")
        
        # Show path to nearest tomb
        tx, ty = nearest
        if hasattr(game, 'game_map') and 0 <= ty < len(game.game_map) and 0 <= tx < len(game.game_map[0]):
            print(f"Tile at nearest tomb: '{game.game_map[ty][tx]}'")
    else:
        print("\nNo tomb entrances found on map!")
    
    # Test manual tomb entry at current position
    print(f"\nTesting tomb entry at current position...")
    try:
        result = game.enter_tomb()
        print(f"Tomb entry result: {result}")
        if result:
            print("SUCCESS: Entered tomb!")
        else:
            print("FAILED: Could not enter tomb")
            print("  Checking requirements...")
            print(f"  - Player on tomb entrance: {(px, py) in tomb_entrances}")
            print(f"  - Map features module available: {'map_features' in sys.modules or 'available'}")
    except Exception as e:
        print(f"ERROR during tomb entry: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()