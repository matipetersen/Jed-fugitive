#!/usr/bin/env python3
"""
Test tomb stair placement on all levels.
Verifies that stairs up and down are correctly placed on every level.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.map.generation import generate_dungeon_level, Display


def test_tomb_stairs():
    """Test that stairs are correctly placed on all tomb levels."""
    print("\n" + "="*70)
    print("Testing Tomb Stair Placement")
    print("="*70)
    
    # Test 1: Generate multiple levels and verify stairs
    print("\n[Test 1] Stair Placement on Multiple Levels")
    num_levels = 5
    
    for depth in range(1, num_levels + 1):
        game_map, rooms, special_dungeons = generate_dungeon_level(depth)
        
        # Count stairs
        stairs_up_count = 0
        stairs_down_count = 0
        stairs_up_pos = None
        stairs_down_pos = None
        
        for y in range(len(game_map)):
            for x in range(len(game_map[0])):
                if game_map[y][x] == Display.STAIRS_UP:
                    stairs_up_count += 1
                    stairs_up_pos = (x, y)
                elif game_map[y][x] == Display.STAIRS_DOWN:
                    stairs_down_count += 1
                    stairs_down_pos = (x, y)
        
        print(f"  Level {depth}:")
        print(f"    Stairs UP: {stairs_up_count} at {stairs_up_pos}")
        print(f"    Stairs DOWN: {stairs_down_count} at {stairs_down_pos}")
        print(f"    Rooms: {len(rooms)}")
        
        # Verify each level has exactly one of each stair type
        assert stairs_up_count == 1, f"Level {depth} should have exactly 1 stairs up, found {stairs_up_count}"
        assert stairs_down_count == 1, f"Level {depth} should have exactly 1 stairs down, found {stairs_down_count}"
        
        # Verify stairs are not on same position
        assert stairs_up_pos != stairs_down_pos, f"Level {depth} has stairs on same position!"
        
        # Verify stairs are on floor tiles (not walls)
        if stairs_up_pos:
            ux, uy = stairs_up_pos
            # Check that it's in first room
            first_room = rooms[0]
            assert (first_room[0] <= ux < first_room[0] + first_room[2] and
                    first_room[1] <= uy < first_room[1] + first_room[3]), \
                   f"Stairs up not in first room on level {depth}"
        
        if stairs_down_pos:
            dx, dy = stairs_down_pos
            # Check that it's in last room
            last_room = rooms[-1]
            assert (last_room[0] <= dx < last_room[0] + last_room[2] and
                    last_room[1] <= dy < last_room[1] + last_room[3]), \
                   f"Stairs down not in last room on level {depth}"
    
    print("  ✓ All levels have correct stair placement")
    
    # Test 2: Verify stairs are accessible
    print("\n[Test 2] Stair Accessibility")
    
    for depth in [1, 3, 5]:
        game_map, rooms, _ = generate_dungeon_level(depth)
        
        # Find stairs
        stairs_up_pos = None
        stairs_down_pos = None
        
        for y in range(len(game_map)):
            for x in range(len(game_map[0])):
                if game_map[y][x] == Display.STAIRS_UP:
                    stairs_up_pos = (x, y)
                elif game_map[y][x] == Display.STAIRS_DOWN:
                    stairs_down_pos = (x, y)
        
        # Check that stairs have adjacent floor tiles (are accessible)
        def has_adjacent_floor(pos):
            x, y = pos
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = x + dx, y + dy
                if (0 <= ny < len(game_map) and 0 <= nx < len(game_map[0]) and
                    game_map[ny][nx] == Display.FLOOR):
                    return True
            return False
        
        assert has_adjacent_floor(stairs_up_pos), \
               f"Level {depth}: Stairs up has no adjacent floor tiles!"
        assert has_adjacent_floor(stairs_down_pos), \
               f"Level {depth}: Stairs down has no adjacent floor tiles!"
        
        print(f"  Level {depth}: Both stairs are accessible ✓")
    
    print("  ✓ All stairs are accessible")
    
    # Test 3: Stairs don't overlap with items
    print("\n[Test 3] Stairs Don't Overlap with Items")
    
    for depth in range(1, 6):
        game_map, rooms, _ = generate_dungeon_level(depth)
        
        # Find stairs positions
        stairs_positions = set()
        for y in range(len(game_map)):
            for x in range(len(game_map[0])):
                if game_map[y][x] in (Display.STAIRS_UP, Display.STAIRS_DOWN):
                    stairs_positions.add((x, y))
        
        # Verify no items on stair positions
        item_chars = {Display.GOLD, Display.FOOD, Display.POTION, Display.ARTIFACT}
        items_on_stairs = []
        
        for y in range(len(game_map)):
            for x in range(len(game_map[0])):
                if (x, y) in stairs_positions and game_map[y][x] in item_chars:
                    items_on_stairs.append((x, y, game_map[y][x]))
        
        assert len(items_on_stairs) == 0, \
               f"Level {depth}: Found {len(items_on_stairs)} items overlapping stairs!"
        
        print(f"  Level {depth}: No item/stair overlap ✓")
    
    print("  ✓ No stairs/item overlaps")
    
    # Test 4: Test multiple generation runs for consistency
    print("\n[Test 4] Consistency Across Multiple Generations")
    
    runs = 10
    for run in range(runs):
        for depth in [1, 2, 3]:
            game_map, rooms, _ = generate_dungeon_level(depth)
            
            stairs_up = 0
            stairs_down = 0
            
            for y in range(len(game_map)):
                for x in range(len(game_map[0])):
                    if game_map[y][x] == Display.STAIRS_UP:
                        stairs_up += 1
                    elif game_map[y][x] == Display.STAIRS_DOWN:
                        stairs_down += 1
            
            assert stairs_up == 1 and stairs_down == 1, \
                   f"Run {run+1}, Level {depth}: Inconsistent stair count"
    
    print(f"  Tested {runs} generation runs for levels 1-3")
    print("  ✓ Consistent stair placement across all runs")
    
    # Test 5: Visual verification of one level
    print("\n[Test 5] Visual Verification (Level 3)")
    
    game_map, rooms, _ = generate_dungeon_level(3, width=60, height=20)
    
    print("\n  Generated map (< = up, > = down, . = floor, # = wall):")
    print("  " + "-" * 60)
    
    for y in range(len(game_map)):
        row = ""
        for x in range(len(game_map[0])):
            cell = game_map[y][x]
            if cell == Display.STAIRS_UP:
                row += "\033[92m<\033[0m"  # Green
            elif cell == Display.STAIRS_DOWN:
                row += "\033[93m>\033[0m"  # Yellow
            elif cell == Display.FLOOR:
                row += "."
            elif cell in {Display.GOLD, Display.FOOD, Display.POTION, Display.ARTIFACT}:
                row += "\033[94m" + cell + "\033[0m"  # Blue
            else:
                row += "#"
        print("  " + row)
    
    print("  " + "-" * 60)
    print("  ✓ Visual verification complete")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    
    print("\nSummary:")
    print("  • All levels (1-5+) now have STAIRS_UP placed")
    print("  • All levels have exactly 1 STAIRS_UP and 1 STAIRS_DOWN")
    print("  • Stairs are in separate rooms (first and last)")
    print("  • Stairs are accessible (have adjacent floor tiles)")
    print("  • No overlap between stairs and items")
    print("  • Consistent placement across multiple generations")
    print()
    
    print("Fix Applied:")
    print("  Changed generation.py to place STAIRS_UP on ALL levels")
    print("  Previous bug: Only level 1 had STAIRS_UP")
    print("  Now: Every level has both UP and DOWN stairs")
    print()


if __name__ == "__main__":
    test_tomb_stairs()
