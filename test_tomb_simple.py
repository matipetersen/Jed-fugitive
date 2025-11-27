#!/usr/bin/env python3
"""
Simple test to check tomb_entrances population without curses.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock curses for headless test
class MockStdscr:
    def getmaxyx(self):
        return (50, 150)
    def timeout(self, ms):
        pass
    def getch(self):
        return -1

# Mock curses module
class MockCurses:
    KEY_UP = 259
    KEY_DOWN = 258
    KEY_LEFT = 260
    KEY_RIGHT = 261
    A_BOLD = 1
    A_REVERSE = 2
    A_DIM = 4
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_BLUE = 4
    COLOR_MAGENTA = 5
    COLOR_CYAN = 6
    COLOR_WHITE = 7
    
    @staticmethod
    def color_pair(n):
        return 0
    @staticmethod
    def init_pair(*args):
        pass
    @staticmethod
    def curs_set(n):
        pass
    @staticmethod
    def newwin(*args):
        return MockStdscr()
    @staticmethod
    def error():
        return Exception("curses error")

sys.modules['curses'] = MockCurses()

from jedi_fugitive.game.level import Display

# Now import game manager after curses mock
from jedi_fugitive.game.game_manager import GameManager

print("=" * 70)
print("TOMB ENTRANCES POPULATION TEST")
print("=" * 70)

# Create mock stdscr
stdscr = MockStdscr()

# Create game
game = GameManager(stdscr)

print("\n1. Checking tomb_entrances set...")
tomb_entrances = getattr(game, 'tomb_entrances', None)
print(f"   tomb_entrances exists: {tomb_entrances is not None}")

if tomb_entrances:
    print(f"   tomb_entrances count: {len(tomb_entrances)}")
    print(f"   First 5 positions: {list(tomb_entrances)[:5]}")
else:
    print("   ✗ tomb_entrances is None or empty!")

print("\n2. Checking 'D' tiles on map...")
d_tiles = []
for y in range(len(game.game_map)):
    for x in range(len(game.game_map[0])):
        if game.game_map[y][x] == 'D':
            d_tiles.append((x, y))

print(f"   Found {len(d_tiles)} 'D' tiles")
print(f"   First 5 positions: {d_tiles[:5]}")

print("\n3. Cross-checking tomb_entrances vs 'D' tiles...")
if tomb_entrances and d_tiles:
    # Check if D tiles are in tomb_entrances
    missing_from_set = [pos for pos in d_tiles if pos not in tomb_entrances]
    extra_in_set = [pos for pos in tomb_entrances if pos not in d_tiles]
    
    print(f"   'D' tiles missing from tomb_entrances: {len(missing_from_set)}")
    if missing_from_set:
        print(f"      Examples: {missing_from_set[:5]}")
    
    print(f"   tomb_entrances not marked as 'D' on map: {len(extra_in_set)}")
    if extra_in_set:
        print(f"      Examples: {extra_in_set[:5]}")
    
    if not missing_from_set and not extra_in_set:
        print("   ✓ Perfect match! All 'D' tiles in tomb_entrances set.")
    else:
        print("   ✗ Mismatch detected!")

print("\n4. Testing entrance detection logic...")
if d_tiles:
    test_pos = d_tiles[0]
    test_x, test_y = test_pos
    tile = game.game_map[test_y][test_x]
    tile_str = str(tile)
    
    print(f"   Testing position: {test_pos}")
    print(f"   Tile: '{tile}' (type: {type(tile).__name__})")
    print(f"   tile_str: '{tile_str}'")
    
    # Test all 3 conditions from game_manager
    check1 = tile_str in ("D",)
    print(f"   Condition 1 - tile_str in ('D',): {check1}")
    
    check2 = tile == getattr(Display, "SITH_ENTRANCE", None)
    print(f"   Condition 2 - tile == Display.SITH_ENTRANCE: {check2}")
    
    check3 = test_pos in getattr(game, "tomb_entrances", set())
    print(f"   Condition 3 - position in tomb_entrances: {check3}")
    
    entrance_hit = check1 or check2 or check3
    print(f"   Overall entrance_hit: {entrance_hit}")
    
    # Test enter_tomb condition
    px, py = test_x, test_y
    tomb_entrances_check = (px, py) in getattr(game, 'tomb_entrances', set())
    print(f"   enter_tomb check - (px,py) in tomb_entrances: {tomb_entrances_check}")
    
    if entrance_hit and not tomb_entrances_check:
        print("   ⚠️  WARNING: entrance_hit=True but enter_tomb check would FAIL!")
    elif entrance_hit and tomb_entrances_check:
        print("   ✓ Both checks pass! Tomb entry should work.")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
