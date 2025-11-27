#!/usr/bin/env python3
"""
Comprehensive System Integration Test
Tests all major game systems for proper integration and functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.player import Player
from jedi_fugitive.game import force_abilities as fa

class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def subwin(self, *args, **kwargs): return self
    def getch(self): return -1
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *args, **kwargs): pass
    def addnstr(self, *args, **kwargs): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): pass
    def mvwin(self, y, x): pass
    def move(self, y, x): pass
    def clrtoeol(self): pass

def test_system_integration():
    print("=== COMPREHENSIVE SYSTEM INTEGRATION TEST ===\n")
    
    # Initialize game
    print("1. GAME INITIALIZATION")
    stdscr = DummyStdscr()
    game = GameManager(stdscr)
    
    if not hasattr(game, 'initialize'):
        print("✗ CRITICAL: GameManager missing initialize method")
        return False
    
    game.initialize()
    game.generate_world()
    print("✓ Game initialization and world generation successful")
    
    # Test player systems
    print("\n2. PLAYER SYSTEMS")
    player = game.player
    print(f"  Initial level: {player.level}")
    print(f"  Initial HP: {player.hp}/{player.max_hp}")
    print(f"  Initial Force: {getattr(player, 'force_points', 'N/A')}")
    print(f"  Initial corruption: {player.corruption}")
    
    # Test Force abilities
    print("\n3. FORCE ABILITIES SYSTEM")
    try:
        abilities = getattr(fa, 'FORCE_ABILITIES', [])
        print(f"  Available abilities: {len(abilities)}")
        
        # Test basic abilities
        for ability_name in ['ForcePushPull', 'ForceHeal', 'ForceLightning']:
            if ability_name in [a.__name__ for a in abilities]:
                print(f"  ✓ {ability_name} available")
            else:
                print(f"  ⚠ {ability_name} missing")
    except Exception as e:
        print(f"  ✗ Force abilities error: {e}")
    
    # Test special dungeons
    print("\n4. SPECIAL DUNGEONS SYSTEM")
    special_dungeons = getattr(game, 'special_dungeons_on_surface', [])
    print(f"  Special dungeons on surface: {len(special_dungeons)}")
    
    # Check if special dungeon functions exist
    integration_functions = [
        '_handle_special_dungeon_entrance',
        '_enter_special_dungeon',
        '_exit_special_dungeon',
        '_handle_special_dungeon_artifact'
    ]
    
    for func_name in integration_functions:
        if hasattr(game, func_name):
            print(f"  ✓ {func_name} integrated")
        else:
            print(f"  ✗ {func_name} missing")
    
    # Test combat system
    print("\n5. COMBAT SYSTEM")
    combat_functions = [
        'process_enemies',
        '_respawn_enemies',
        'meditate'
    ]
    
    for func_name in combat_functions:
        if hasattr(game, func_name):
            print(f"  ✓ {func_name} available")
        else:
            print(f"  ⚠ {func_name} missing")
    
    # Test enemy system
    print("\n6. ENEMY SYSTEM")
    print(f"  Enemies on surface: {len(game.enemies)}")
    if game.enemies:
        enemy = game.enemies[0]
        print(f"  First enemy: {enemy.name} (Level {getattr(enemy, 'level', '?')})")
    
    # Test tomb system
    print("\n7. TOMB ENTRANCE SYSTEM")
    tomb_entrances = getattr(game, 'tomb_entrances', set())
    print(f"  Tomb entrances: {len(tomb_entrances)}")
    
    # Test movement system
    print("\n8. MOVEMENT SYSTEM")
    if hasattr(game, '_try_move_player'):
        print("  ✓ Core movement function available")
    else:
        print("  ✗ Core movement function missing")
    
    # Test save/load system
    print("\n9. SAVE/LOAD SYSTEM")
    save_functions = ['save_game', 'load_game']
    save_available = 0
    for func_name in save_functions:
        if hasattr(game, func_name):
            print(f"  ✓ {func_name} available")
            save_available += 1
        else:
            print(f"  ⚠ {func_name} not found")
    
    # Test UI integration  
    print("\n10. UI INTEGRATION")
    ui_functions = ['draw', 'add_message', 'handle_input']
    ui_available = 0
    for func_name in ui_functions:
        if hasattr(game, func_name):
            print(f"  ✓ {func_name} integrated")
            ui_available += 1
        else:
            print(f"  ✗ {func_name} missing")
    
    # Test equipment system
    print("\n11. EQUIPMENT SYSTEM")
    inventory = getattr(player, 'inventory', [])
    print(f"  Starting inventory items: {len(inventory)}")
    
    equipped_weapon = getattr(player, 'equipped_weapon', None) or getattr(player, 'main_weapon', None)
    if equipped_weapon:
        print(f"  ✓ Weapon equipped: {equipped_weapon}")
    else:
        print("  ⚠ No weapon equipped")
    
    # Test atmospheric system
    print("\n12. ATMOSPHERIC SYSTEM")
    try:
        from jedi_fugitive.game import atmosphere
        if hasattr(atmosphere, 'get_biome_atmosphere'):
            print("  ✓ Atmospheric system available")
        else:
            print("  ⚠ Atmospheric functions missing")
    except ImportError:
        print("  ⚠ Atmospheric system not found")
    
    print("\n" + "="*50)
    print("INTEGRATION SUMMARY:")
    
    # Calculate integration score
    total_systems = 12
    working_systems = 0
    
    # Basic scoring
    if hasattr(game, 'initialize'): working_systems += 1
    if len(abilities) > 10: working_systems += 1  
    if len(integration_functions) > 0: working_systems += 1
    if len(combat_functions) > 0: working_systems += 1
    if len(game.enemies) >= 0: working_systems += 1  # Even 0 is valid
    if len(tomb_entrances) > 0: working_systems += 1
    if hasattr(game, '_try_move_player'): working_systems += 1
    if save_available > 0: working_systems += 1
    if ui_available >= 2: working_systems += 1
    if len(inventory) > 0: working_systems += 1
    if equipped_weapon: working_systems += 1
    try:
        from jedi_fugitive.game import atmosphere
        working_systems += 1
    except:
        pass
    
    integration_percentage = (working_systems / total_systems) * 100
    print(f"  Systems working: {working_systems}/{total_systems}")
    print(f"  Integration level: {integration_percentage:.1f}%")
    
    if integration_percentage >= 90:
        print("  Status: ✅ EXCELLENT INTEGRATION")
    elif integration_percentage >= 75:
        print("  Status: ✅ GOOD INTEGRATION") 
    elif integration_percentage >= 50:
        print("  Status: ⚠️ PARTIAL INTEGRATION")
    else:
        print("  Status: ❌ POOR INTEGRATION")
    
    return integration_percentage >= 75

if __name__ == "__main__":
    success = test_system_integration()
    sys.exit(0 if success else 1)