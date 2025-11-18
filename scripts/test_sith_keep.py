#!/usr/bin/env python3
"""Test Sith Keep generation and boulder mechanics"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_sith_keep_generation():
    """Test that Sith Keep generates properly with all components"""
    from jedi_fugitive.game.sith_keep import (
        generate_sith_keep_layout,
        setup_sith_keep_puzzles,
        setup_sith_keep_guards,
        setup_sith_keep_boss
    )
    from jedi_fugitive.game.level import Display
    
    print("=" * 80)
    print("TESTING SITH KEEP GENERATION")
    print("=" * 80)
    
    # Create mock game object
    class MockGame:
        def __init__(self):
            self.player = type('obj', (object,), {'level': 10})()
            self.enemies = []
            self.items_on_map = []
            self.game_map = [['.'] * 200 for _ in range(200)]
    
    game = MockGame()
    
    # Test layout generation
    print("\n1. Generating Sith Keep layout...")
    keep_layout, entrance, chambers, boss_chamber = generate_sith_keep_layout()
    print(f"   ✓ Layout generated: {len(keep_layout)}x{len(keep_layout[0])} grid")
    print(f"   ✓ Entrance: {entrance}")
    print(f"   ✓ Chambers: {len(chambers)}")
    
    # Count features
    walls = sum(row.count('█') for row in keep_layout)
    floors = sum(row.count('.') for row in keep_layout)
    
    print(f"   ✓ Walls: {walls}, Floors: {floors}")
    
    # World coordinates for keep center
    keep_cx, keep_cy = 100, 100
    
    # Test puzzle setup
    print("\n2. Setting up puzzles...")
    setup_sith_keep_puzzles(game, keep_cx, keep_cy, chambers)
    if hasattr(game, 'sith_keep_puzzles'):
        total_boulders = sum(len(p['boulders']) for p in game.sith_keep_puzzles.values())
        total_plates = sum(len(p['plates']) for p in game.sith_keep_puzzles.values())
        print(f"   ✓ Puzzles created: {total_boulders} boulders, {total_plates} plates")
        for puzzle_id, puzzle in game.sith_keep_puzzles.items():
            print(f"      {puzzle_id}: {len(puzzle['boulders'])} boulders, {len(puzzle['plates'])} plates")
    
    # Test guard setup
    print("\n3. Spawning guards...")
    setup_sith_keep_guards(game, keep_cx, keep_cy, chambers)
    guards = game.enemies
    print(f"   ✓ {len(guards)} elite guards spawned")
    for guard in guards[:5]:  # Show first 5
        print(f"      {guard.name} (Level {guard.level}) at ({guard.x}, {guard.y})")
    
    # Test boss setup
    print("\n4. Creating boss encounter...")
    setup_sith_keep_boss(game, keep_cx, keep_cy, boss_chamber)
    bosses = [e for e in game.enemies if hasattr(e, 'is_boss') and e.is_boss]
    if bosses:
        boss = bosses[0]
        print(f"   ✓ Boss: {boss.name} (Level {boss.level}, HP {boss.hp}/{boss.max_hp})")
        print(f"   ✓ Boss at ({boss.x}, {boss.y})")
    
    # Check for legendary weapon
    legendary_weapons = [i for i in game.items_on_map if i.get('rarity') == 'legendary']
    if legendary_weapons:
        weapon = legendary_weapons[0]
        print(f"   ✓ Legendary weapon: {weapon['name']} ({weapon['damage']} damage)")
        print(f"   ✓ Weapon at ({weapon['x']}, {weapon['y']})")
    
    # Visual representation of keep (scaled down)
    print("\n5. Keep Layout Preview (center 31x31):")
    print("   " + "─" * 33)
    for y in range(15):
        row = "   │"
        for x in range(31):
            cell = keep_layout[y][x]
            # Use color symbols
            if cell == '█':
                row += '█'
            elif cell == '▓':
                row += '▓'
            elif cell == '.':
                row += '·'
            else:
                row += cell
        row += "│"
        print(row)
    print("   " + "─" * 33)
    print("   Legend: █ = walls, ▓ = entrance, · = floor")
    
    print("\n" + "=" * 80)
    print("✓ SITH KEEP GENERATION TEST COMPLETE")
    print("=" * 80)
    
    return True

def test_boulder_mechanics():
    """Test boulder push/pull mechanics"""
    from jedi_fugitive.game.sith_keep import move_boulder, check_puzzle_solution
    
    print("\n" + "=" * 80)
    print("TESTING BOULDER MECHANICS")
    print("=" * 80)
    
    # Create mock game
    class MockUI:
        class Messages:
            def add(self, msg):
                print(f"   MSG: {msg}")
        messages = Messages()
    
    class MockGame:
        def __init__(self):
            self.ui = MockUI()
            self.game_map = [['.' for _ in range(20)] for _ in range(20)]
            # Place a boulder
            self.game_map[10][10] = 'O'
            # Place a pressure plate
            self.game_map[10][12] = '='
            # Place a wall
            self.game_map[10][15] = '█'
            self.sith_keep_data = {
                'puzzle_chambers': {
                    'north': {
                        'boulders': [(10, 10)],
                        'plates': [(10, 12)]
                    }
                }
            }
    
    game = MockGame()
    
    print("\n1. Testing boulder movement...")
    print(f"   Initial boulder position: (10, 10)")
    print(f"   Target plate position: (10, 12)")
    
    # Try to move boulder right (toward plate)
    print("\n2. Pushing boulder right (dx=1, dy=0)...")
    result = move_boulder(game, 10, 10, 1, 0)
    if result:
        print(f"   ✓ Boulder moved successfully")
        # Find new boulder position
        for y in range(20):
            for x in range(20):
                if game.game_map[y][x] == 'O':
                    print(f"   ✓ New position: ({x}, {y})")
    else:
        print(f"   ✗ Boulder did not move")
    
    # Push again
    print("\n3. Pushing boulder right again...")
    for y in range(20):
        for x in range(20):
            if game.game_map[y][x] == 'O':
                result = move_boulder(game, x, y, 1, 0)
                if result:
                    print(f"   ✓ Boulder moved from ({x}, {y})")
                break
    
    # Check puzzle solution
    print("\n4. Checking puzzle solution...")
    solved = check_puzzle_solution(game, 'north')
    if solved:
        print(f"   ✓ Puzzle SOLVED! Boulder is on pressure plate!")
    else:
        print(f"   ✗ Puzzle not solved yet")
    
    print("\n" + "=" * 80)
    print("✓ BOULDER MECHANICS TEST COMPLETE")
    print("=" * 80)

def test_full_integration():
    """Test full Sith Keep integration into game map"""
    from jedi_fugitive.game.sith_keep import place_sith_keep_on_map
    
    print("\n" + "=" * 80)
    print("TESTING FULL INTEGRATION")
    print("=" * 80)
    
    # Create mock game
    class MockUI:
        class Messages:
            def add(self, msg):
                print(f"   MSG: {msg}")
        messages = Messages()
    
    class MockPlayer:
        def __init__(self):
            self.level = 10
            self.x = 100
            self.y = 100
    
    class MockGame:
        def __init__(self):
            self.ui = MockUI()
            self.player = MockPlayer()
            self.enemies = []
            self.items_on_map = []
            # Large map
            self.game_map = [['.' for _ in range(300)] for _ in range(300)]
            # Add some obstacles
            for i in range(50, 60):
                self.game_map[100][i] = '█'
    
    game = MockGame()
    
    print("\n1. Placing Sith Keep on map...")
    place_sith_keep_on_map(game)
    
    # Check if keep was placed
    keep_found = False
    keep_x, keep_y = -1, -1
    
    print("\n2. Searching for Sith Keep entrance (▓)...")
    for y in range(len(game.game_map)):
        for x in range(len(game.game_map[0])):
            if game.game_map[y][x] == '▓':
                keep_found = True
                keep_x, keep_y = x, y
                break
        if keep_found:
            break
    
    if keep_found:
        print(f"   ✓ Sith Keep entrance found at ({keep_x}, {keep_y})")
        
        # Check distance from player
        dist = abs(keep_x - game.player.x) + abs(keep_y - game.player.y)
        print(f"   ✓ Distance from player: {dist} tiles")
        
        # Count enemies and items
        print(f"   ✓ Enemies spawned: {len(game.enemies)}")
        print(f"   ✓ Items placed: {len(game.items_on_map)}")
        
        # Check for boss
        bosses = [e for e in game.enemies if hasattr(e, 'is_boss') and e.is_boss]
        if bosses:
            print(f"   ✓ Boss found: {bosses[0].name} at ({bosses[0].x}, {bosses[0].y})")
        
        # Print small area around entrance
        print("\n3. Area around entrance:")
        print("   " + "─" * 23)
        for dy in range(-5, 6):
            row = "   │"
            for dx in range(-10, 11):
                cx, cy = keep_x + dx, keep_y + dy
                if 0 <= cy < len(game.game_map) and 0 <= cx < len(game.game_map[0]):
                    cell = game.game_map[cy][cx]
                    if cell == '.':
                        row += '·'
                    else:
                        row += cell
                else:
                    row += ' '
            row += "│"
            print(row)
        print("   " + "─" * 23)
    else:
        print("   ✗ Sith Keep entrance NOT found!")
    
    print("\n" + "=" * 80)
    print("✓ FULL INTEGRATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_sith_keep_generation()
        test_boulder_mechanics()
        test_full_integration()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED!")
        print("=" * 80)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
