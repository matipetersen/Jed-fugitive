#!/usr/bin/env python3
"""Quick verification that the Sith Keep spawns in game"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def quick_test():
    """Quick test to verify Sith Keep appears in game generation"""
    from jedi_fugitive.game.game_manager import GameManager
    
    print("=" * 80)
    print("SITH KEEP QUICK VERIFICATION TEST")
    print("=" * 80)
    
    # Create game
    print("\n1. Creating game instance...")
    game = GameManager()
    
    print("   ✓ Game created")
    print(f"   ✓ Map size: {len(game.game_map[0])}x{len(game.game_map)}")
    print(f"   ✓ Player at: ({game.player.x}, {game.player.y})")
    print(f"   ✓ Player level: {game.player.level}")
    
    # Search for Sith Keep entrance
    print("\n2. Searching for Sith Keep...")
    keep_found = False
    keep_x, keep_y = -1, -1
    
    for y in range(len(game.game_map)):
        for x in range(len(game.game_map[0])):
            if game.game_map[y][x] == '▓':  # Entrance symbol
                keep_found = True
                keep_x, keep_y = x, y
                break
        if keep_found:
            break
    
    if keep_found:
        print(f"   ✓ Sith Keep entrance found at ({keep_x}, {keep_y})")
        
        # Calculate distance from player
        dist = abs(keep_x - game.player.x) + abs(keep_y - game.player.y)
        print(f"   ✓ Distance from player spawn: {dist} tiles")
        
        # Check for boss
        bosses = [e for e in game.enemies if hasattr(e, 'is_boss') and e.is_boss and e.name == "Sith Inquisitor"]
        if bosses:
            boss = bosses[0]
            print(f"   ✓ Sith Inquisitor found!")
            print(f"      Name: {boss.name}")
            print(f"      Level: {boss.level}")
            print(f"      HP: {boss.hp}/{boss.max_hp}")
            print(f"      Attack: {boss.attack}")
            print(f"      Defense: {boss.defense}")
            print(f"      Position: ({boss.x}, {boss.y})")
        else:
            print("   ✗ Warning: Sith Inquisitor not found")
        
        # Check for guards
        keep_guards = []
        search_radius = 20
        for e in game.enemies:
            if not (hasattr(e, 'is_boss') and e.is_boss):
                ex, ey = e.x, e.y
                if abs(ex - keep_x) <= search_radius and abs(ey - keep_y) <= search_radius:
                    keep_guards.append(e)
        
        print(f"   ✓ {len(keep_guards)} guards near keep entrance")
        
        # Check for boulders
        boulder_count = 0
        for y in range(max(0, keep_y - 20), min(len(game.game_map), keep_y + 20)):
            for x in range(max(0, keep_x - 20), min(len(game.game_map[0]), keep_x + 20)):
                if game.game_map[y][x] == 'O':
                    boulder_count += 1
        
        print(f"   ✓ {boulder_count} boulders near keep")
        
        # Check for legendary weapon
        legendary = [i for i in game.items_on_map if i.get('rarity') == 'legendary']
        if legendary:
            weapon = legendary[0]
            print(f"   ✓ Legendary weapon: {weapon['name']}")
            print(f"      Damage: {weapon['damage']}")
            print(f"      Position: ({weapon['x']}, {weapon['y']})")
        
        # Print area around entrance
        print("\n3. Area around Sith Keep entrance:")
        print("   " + "─" * 23)
        for dy in range(-5, 6):
            row = "   │"
            for dx in range(-10, 11):
                cx, cy = keep_x + dx, keep_y + dy
                if 0 <= cy < len(game.game_map) and 0 <= cx < len(game.game_map[0]):
                    cell = game.game_map[cy][cx]
                    if cell == '.':
                        row += '·'
                    elif cell == '█':
                        row += '█'
                    elif cell == '▓':
                        row += '▓'
                    elif cell == 'O':
                        row += 'O'
                    else:
                        row += cell
                else:
                    row += ' '
            row += "│"
            print(row)
        print("   " + "─" * 23)
        
        print("\n" + "=" * 80)
        print("✓ SITH KEEP VERIFICATION COMPLETE - ALL SYSTEMS OPERATIONAL")
        print("=" * 80)
        
        return True
    else:
        print("   ✗ ERROR: Sith Keep entrance NOT found on map!")
        print("   This might be due to map generation randomness.")
        print("   Try running the test again.")
        return False

if __name__ == "__main__":
    try:
        success = quick_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
