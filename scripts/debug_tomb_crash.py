#!/usr/bin/env python3
"""Debug tomb functionality to identify the crash at level 2."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_tomb_generation():
    """Test tomb generation to see if level 2 has issues."""
    print("=" * 80)
    print("TOMB GENERATION DEBUG TEST")
    print("=" * 80)
    
    import random
    from jedi_fugitive.game.level import generate_dungeon_level, Display
    from jedi_fugitive.game import enemies_sith as sith
    
    # Simulate tomb generation like enter_tomb does
    num_levels = random.randint(3, 5)
    print(f"\nGenerating {num_levels} tomb levels...")
    
    tomb_levels = []
    tomb_rooms = []
    tomb_enemies = []
    tomb_stairs = []
    
    for depth in range(1, num_levels + 1):
        print(f"\n--- Generating Level {depth} ---")
        
        # Generate level
        try:
            level_map, rooms = generate_dungeon_level(depth)
            print(f"  ✓ Map generated: {len(level_map)}x{len(level_map[0])} with {len(rooms)} rooms")
            tomb_levels.append(level_map)
            tomb_rooms.append(rooms)
        except Exception as e:
            print(f"  ✗ ERROR generating map: {e}")
            continue
        
        # Find stairs
        stairs = {}
        try:
            for y in range(len(level_map)):
                for x in range(len(level_map[0])):
                    if level_map[y][x] == Display.STAIRS_UP:
                        stairs['up'] = (x, y)
                    elif level_map[y][x] == Display.STAIRS_DOWN:
                        stairs['down'] = (x, y)
            print(f"  ✓ Stairs found: up={stairs.get('up')}, down={stairs.get('down')}")
            tomb_stairs.append(stairs)
        except Exception as e:
            print(f"  ✗ ERROR finding stairs: {e}")
            tomb_stairs.append({})
        
        # Generate enemies
        level_enemies = []
        try:
            for i, room in enumerate(rooms):
                num_enemies = random.randint(1, 3)
                for _ in range(num_enemies):
                    ex = random.randint(room[0] + 1, room[0] + room[2] - 2)
                    ey = random.randint(room[1] + 1, room[1] + room[3] - 2)
                    if level_map[ey][ex] == Display.FLOOR:
                        # Create enemy based on depth
                        if depth == 1:
                            enemy = sith.create_sith_trooper(level=1)
                        elif depth == 2:
                            enemy = sith.create_sith_acolyte(level=2)
                        else:
                            enemy = sith.create_sith_warrior(level=depth)
                        enemy.x, enemy.y = ex, ey
                        level_enemies.append(enemy)
            print(f"  ✓ Enemies created: {len(level_enemies)} enemies")
            tomb_enemies.append(level_enemies)
        except Exception as e:
            print(f"  ✗ ERROR creating enemies: {e}")
            import traceback
            traceback.print_exc()
            tomb_enemies.append([])
    
    # Test accessing levels like change_floor does
    print("\n" + "=" * 80)
    print("TESTING LEVEL ACCESS (simulating change_floor)")
    print("=" * 80)
    
    for new_level in range(len(tomb_levels)):
        print(f"\nAccessing level {new_level} (floor {new_level + 1})...")
        try:
            # This is what change_floor does
            level_map = tomb_levels[new_level]
            print(f"  ✓ Map loaded: {len(level_map)}x{len(level_map[0])}")
            
            # This is the problematic line
            enemies_result = getattr(type('obj', (), {'tomb_enemies': tomb_enemies})(), 'tomb_enemies', [])[new_level]
            print(f"  ✓ Enemies accessed: {enemies_result}")
            print(f"    Type: {type(enemies_result)}")
            print(f"    Length: {len(enemies_result) if enemies_result else 'None'}")
            
            # The actual enemy loading line from change_floor
            enemies = [e for e in (enemies_result or [])]
            print(f"  ✓ Enemies loaded: {len(enemies)} enemies")
            
        except Exception as e:
            print(f"  ✗ ERROR accessing level {new_level}: {e}")
            import traceback
            traceback.print_exc()
    
    # Check structure
    print("\n" + "=" * 80)
    print("FINAL STRUCTURE CHECK")
    print("=" * 80)
    print(f"tomb_levels: {len(tomb_levels)} levels")
    print(f"tomb_rooms: {len(tomb_rooms)} room lists")
    print(f"tomb_enemies: {len(tomb_enemies)} enemy lists")
    print(f"tomb_stairs: {len(tomb_stairs)} stair dicts")
    
    for i in range(len(tomb_enemies)):
        enemies = tomb_enemies[i]
        print(f"  Level {i}: {len(enemies) if enemies is not None else 'None'} enemies - Type: {type(enemies)}")

if __name__ == "__main__":
    test_tomb_generation()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
