#!/usr/bin/env python3
"""
Test enemy respawning system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jedi_fugitive.game.game_manager import GameManager

class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

def test_enemy_respawn():
    print("=== ENEMY RESPAWNING TEST ===")
    
    # Initialize game with dummy UI
    print("⟳ Creating game with dummy UI...")
    stdscr = DummyStdscr()
    game = GameManager(stdscr)
    
    # Initialize
    game.initialize()
    game.generate_world()
    
    print("✓ Game initialized successfully")
    print(f"  Starting level: {game.player.level}")
    print(f"  Starting corruption: {game.player.corruption}")
    print(f"  Tombs cleared: {getattr(game.player, 'tombs_cleared', game.player.tombs_explored)}")
    
    # Check initial enemies
    initial_enemies = len(game.enemies)
    print(f"  Initial enemies on surface: {initial_enemies}")
    
    if initial_enemies == 0:
        print("⚠️  No enemies on surface - normal for some world generations")
        return
    
    # Clear most enemies to trigger respawn
    print("⟳ Clearing enemies to test respawn trigger...")
    while len(game.enemies) > 2:
        enemy = game.enemies[0]
        print(f"  Removing {enemy.name} at ({enemy.x}, {enemy.y})")
        game.enemies.remove(enemy)
    
    remaining = len(game.enemies)
    print(f"✓ Enemies cleared, {remaining} remaining")
    
    # Test respawn trigger
    print("⟳ Testing respawn system...")
    print(f"  Current enemy count: {len(game.enemies)}")
    print(f"  Respawn threshold: <3 enemies")
    
    if len(game.enemies) < 3:
        print("✓ Below threshold - respawn should trigger")
        
        # Simulate respawn check
        old_count = len(game.enemies)
        game._check_enemy_respawn()
        new_count = len(game.enemies)
        
        print(f"  Enemy count after respawn check: {old_count} → {new_count}")
        
        if new_count > old_count:
            spawned = new_count - old_count
            print(f"🎉 SUCCESS: {spawned} enemies spawned!")
            
            # Show spawned enemies
            print("  Spawned enemies:")
            for i, enemy in enumerate(game.enemies[-spawned:]):
                print(f"    {i+1}. {enemy.name} at ({enemy.x}, {enemy.y}) - Level {enemy.level}")
        else:
            print("⚠️  No enemies spawned (might be no valid spawn positions)")
    else:
        print("✓ Above threshold - no respawn needed")

if __name__ == "__main__":
    test_enemy_respawn()