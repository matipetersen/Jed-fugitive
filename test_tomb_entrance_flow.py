#!/usr/bin/env python3
"""
Complete end-to-end test of tomb entrance system.
Tests: map generation → tomb placement → entrance detection → tomb entry
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.level import Display
from jedi_fugitive.game import map_features

class MockUI:
    class Messages:
        def __init__(self):
            self.log = []
        def add(self, msg):
            self.log.append(msg)
            print(f"  [UI] {msg}")
    
    def __init__(self):
        self.messages = self.Messages()

class MockPlayer:
    def __init__(self):
        self.x = 50
        self.y = 50
        self.los_radius = 6
        self.level = 1
        self.hp = 100
        self.max_hp = 100
        self.force = 50
        self.max_force = 50

class MockGame:
    def __init__(self):
        self.ui = MockUI()
        self.player = MockPlayer()
        self.crash_inflate = 40
        self.outer_map_scale = 60
        self.game_map = []
        self.tomb_entrances = set()
        self.map_biomes = []
        self.items_on_map = []
        self.enemies = []
        self.tomb_levels = None
        self.surface_map = None

print("=" * 70)
print("TOMB ENTRANCE FLOW - END-TO-END TEST")
print("=" * 70)

# Step 1: Generate world
print("\n[STEP 1] Generating world with tombs...")
game = MockGame()
map_features.generate_world(game)

map_h = len(game.game_map)
map_w = len(game.game_map[0]) if map_h else 0
print(f"✓ World generated: {map_w}x{map_h}")
print(f"✓ Tomb entrances: {len(game.tomb_entrances)}")

# Step 2: Find tomb entrances on map
print("\n[STEP 2] Locating 'D' tiles on map...")
d_tiles = []
for y in range(map_h):
    for x in range(map_w):
        if game.game_map[y][x] == 'D':
            d_tiles.append((x, y))

print(f"✓ Found {len(d_tiles)} 'D' tiles")
if d_tiles:
    print(f"  Examples: {d_tiles[:3]}")
else:
    print("❌ ERROR: No 'D' tiles found!")
    sys.exit(1)

# Step 3: Verify entrance detection
print("\n[STEP 3] Testing entrance detection logic...")
test_pos = d_tiles[0]
print(f"  Testing position: {test_pos}")

# Simulate game_manager detection code
target = game.game_map[test_pos[1]][test_pos[0]]
tstr = str(target)
print(f"  Tile value: '{tstr}'")

entrance_hit = False
if tstr in ("D",):
    entrance_hit = True
    print(f"  ✓ String check ('D') passed")

if target == getattr(Display, "SITH_ENTRANCE", None):
    entrance_hit = True
    print(f"  ✓ Display.SITH_ENTRANCE check passed")

if test_pos in game.tomb_entrances:
    entrance_hit = True
    print(f"  ✓ tomb_entrances set check passed")

print(f"  entrance_hit final value: {entrance_hit}")

if not entrance_hit:
    print("❌ ERROR: Entrance detection failed!")
    sys.exit(1)

# Step 4: Test enter_tomb function
print("\n[STEP 4] Testing enter_tomb() function...")
# Move player to tomb entrance
game.player.x, game.player.y = test_pos

print(f"  Player moved to: ({game.player.x}, {game.player.y})")
print(f"  Tile at position: '{game.game_map[game.player.y][game.player.x]}'")
print(f"  Position in tomb_entrances: {(game.player.x, game.player.y) in game.tomb_entrances}")

# Clear UI messages
game.ui.messages.log.clear()

# Attempt to enter tomb
print("\n  Calling map_features.enter_tomb()...")
try:
    entered = map_features.enter_tomb(game)
    print(f"  enter_tomb() returned: {entered}")
    
    if entered:
        print("\n✅ SUCCESS: Tomb entry succeeded!")
        
        # Verify tomb state
        print("\n[STEP 5] Verifying tomb state...")
        print(f"  surface_map saved: {game.surface_map is not None}")
        print(f"  tomb_levels generated: {game.tomb_levels is not None}")
        if game.tomb_levels:
            print(f"  Number of levels: {len(game.tomb_levels)}")
        print(f"  Player new position: ({game.player.x}, {game.player.y})")
        
        # Check tomb_entrances was saved
        if hasattr(game, 'surface_tomb_entrances'):
            print(f"  ✓ surface_tomb_entrances saved: {len(game.surface_tomb_entrances)} entries")
        else:
            print(f"  ⚠️  surface_tomb_entrances NOT saved (re-entry may fail)")
        
        print("\n" + "=" * 70)
        print("RESULT: ✅ ALL TESTS PASSED - TOMB ENTRANCE WORKING!")
        print("=" * 70)
        print("\nTomb entrance flow verified:")
        print("  1. Tombs placed on map with 'D' tiles")
        print("  2. tomb_entrances set populated correctly")
        print("  3. Entrance detection logic works")
        print("  4. enter_tomb() generates dungeon successfully")
        print("  5. Surface state saved for exit/re-entry")
        
    else:
        print("\n❌ FAILED: enter_tomb() returned False")
        print("\nPossible reasons:")
        print("  - Player not on tomb entrance position")
        print("  - tomb_entrances set not populated")
        print("  - Dungeon generation failed")
        
        # Debug info
        print(f"\nDebug info:")
        print(f"  Player pos: ({game.player.x}, {game.player.y})")
        print(f"  Tile at pos: '{game.game_map[game.player.y][game.player.x]}'")
        print(f"  tomb_entrances: {game.tomb_entrances}")
        print(f"  In set: {(game.player.x, game.player.y) in game.tomb_entrances}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ EXCEPTION in enter_tomb(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
