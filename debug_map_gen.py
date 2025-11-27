#!/usr/bin/env python3
"""Debug map and biome generation"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.game_manager import GameManager

class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

def main():
    print("=== MAP & BIOME DIAGNOSIS ===")
    
    # Initialize game with better dummy UI
    stdscr = DummyStdscr()
    game = GameManager(stdscr)
    
    # Override UI initialization to prevent subwin errors
    from jedi_fugitive.ui.silq_ui import UI
    
    class DummyUI(UI):
        def create_layout(self, *args): pass
        def _safe_subwin(self, *args): return None
        def add_message(self, msg): print(f"MSG: {msg}")
    
    game.ui = DummyUI(stdscr)
    
    # Initialize rest of game
    game._setup_player()
    game._setup_inventory()  
    game._initialize_world()
    
    # Check map generation
    if hasattr(game, 'game_map') and game.game_map:
        print(f"Map size: {len(game.game_map[0])}x{len(game.game_map)}")
        
        # Check player position
        px, py = getattr(game.player, 'x', 0), getattr(game.player, 'y', 0)
        print(f"Player position: ({px}, {py})")
        
        # Check biomes
        if hasattr(game, 'map_biomes') and game.map_biomes:
            print(f"Biome map exists: {len(game.map_biomes[0])}x{len(game.map_biomes)}")
            
            # Count biomes
            biome_counts = {}
            for row in game.map_biomes:
                for biome in row:
                    if biome:
                        biome_counts[biome] = biome_counts.get(biome, 0) + 1
            
            print(f"Biomes found: {biome_counts}")
        else:
            print("No biome map found!")
        
        # Check tomb entrances after map features
        tomb_entrances = getattr(game, 'tomb_entrances', set())
        print(f"Tomb entrances: {len(tomb_entrances)}")
        
        if len(tomb_entrances) == 0:
            print("WARNING: No tomb entrances generated!")
            
            # Try to manually call map features
            try:
                from jedi_fugitive.game import map_features
                print("Calling place_map_features manually...")
                map_features.place_map_features(game)
                tomb_entrances = getattr(game, 'tomb_entrances', set())
                print(f"After manual call - Tomb entrances: {len(tomb_entrances)}")
            except Exception as e:
                print(f"Error calling map_features: {e}")
                import traceback
                traceback.print_exc()
                
    else:
        print("No game map found!")

if __name__ == '__main__':
    main()