#!/usr/bin/env python3
"""Test special dungeon generation on surface"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=== SPECIAL DUNGEON TEST ===")
    
    from jedi_fugitive.game.game_manager import GameManager
    
    class DummyStdscr:
        def getmaxyx(self): return (40, 140)
        def getch(self): return -1
        def clear(self): pass
        def refresh(self): pass

    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    
    # Full initialization including world generation
    print("Step 1: Initialize game...")
    gm.initialize()
    
    print("Step 2: Generate world with special dungeons...")
    gm.generate_world()
    
    # Check for special dungeons
    print(f"\n🔮 SPECIAL DUNGEON RESULTS:")
    print(f"  Map size: {len(gm.game_map[0])}x{len(gm.game_map)}")
    print(f"  Regular tomb entrances: {len(getattr(gm, 'tomb_entrances', set()))}")
    
    surface_special_dungeons = getattr(gm, 'surface_special_dungeons', {})
    print(f"  🌟 SPECIAL dungeons on surface: {len(surface_special_dungeons)}")
    
    if surface_special_dungeons:
        print(f"\n✨ SUCCESS: Found {len(surface_special_dungeons)} special dungeons!")
        
        for i, ((x, y), dungeon_data) in enumerate(surface_special_dungeons.items()):
            tile_char = gm.game_map[y][x] if (0 <= y < len(gm.game_map) and 0 <= x < len(gm.game_map[0])) else '?'
            print(f"  🏛️  Special Dungeon {i+1}: {dungeon_data['name']}")
            print(f"      Location: ({x}, {y}) = '{tile_char}'")
            print(f"      Type: {dungeon_data['type']}")
            print(f"      Discovered: {dungeon_data['discovered']}")
        
        # Test entering the first special dungeon
        first_pos, first_dungeon = list(surface_special_dungeons.items())[0]
        print(f"\n🚪 Testing entry to {first_dungeon['name']} at {first_pos}...")
        
        # Move player to special dungeon entrance
        gm.player.x, gm.player.y = first_pos
        
        # Try to enter by stepping on the tile (simulate movement)
        from jedi_fugitive.game.level import Display
        target = gm.game_map[first_pos[1]][first_pos[0]]
        
        # Call the entrance handling directly
        result = gm._enter_surface_special_dungeon(first_dungeon, first_pos)
        
        if result:
            print("✅ SUCCESS: Entered special dungeon!")
            if hasattr(gm, 'current_special_dungeon'):
                current = gm.current_special_dungeon
                print(f"   Current dungeon: {current.get('template', {}).get('name', 'Unknown')}")
                print(f"   Map size: {len(gm.game_map[0])}x{len(gm.game_map)} (dungeon layout)")
                print(f"   Player position: ({gm.player.x}, {gm.player.y})")
                if 'artifact_pos' in current:
                    print(f"   Artifact at: {current['artifact_pos']}")
                if 'exit_pos' in current:
                    print(f"   Exit at: {current['exit_pos']}")
                print("   🎉 SPECIAL DUNGEON ENTRY WORKS!")
            else:
                print("❓ Entered but no current_special_dungeon set")
        else:
            print("❌ FAILED: Could not enter special dungeon")
    else:
        print("❌ ERROR: No special dungeons found on surface!")
        print("   This means the placement code didn't work or had errors.")

if __name__ == '__main__':
    main()