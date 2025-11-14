"""
Quick integration guide for diverse enemies into the main game.

This file shows how to integrate the new diverse enemy system into game_manager.py
"""

# Example 1: Replace existing enemy spawning with diverse enemies
# --------------------------------------------------------------
# OLD CODE (in game_manager.py):
"""
from jedi_fugitive.game.enemy import Enemy
enemy = Enemy("Sith Trooper", 20, 10, 5, 10, None, xp_value=25, level=depth)
"""

# NEW CODE:
"""
from jedi_fugitive.game.diverse_enemies import create_random_enemy, create_mixed_group

# Option A: Spawn random diverse enemy
enemy = create_random_enemy(level=depth)

# Option B: Spawn specific enemy type
from jedi_fugitive.game.diverse_enemies import create_sith_sniper
enemy = create_sith_sniper(level=depth)

# Option C: Spawn balanced mixed group
enemies = create_mixed_group(count=3, level=depth)
"""


# Example 2: Weighted enemy spawning based on depth
# -------------------------------------------------
"""
from jedi_fugitive.game.diverse_enemies import ENEMY_TYPES
import random

def spawn_enemies_for_depth(depth, count=3):
    '''Spawn enemies appropriate for current depth with weighted selection.'''
    
    # Weight different enemy types based on depth
    if depth <= 3:
        # Early game: Scouts and Troopers
        weights = {
            'scout': 0.4,
            'trooper': 0.4,
            'brawler': 0.2,
        }
    elif depth <= 6:
        # Mid game: More variety
        weights = {
            'sniper': 0.2,
            'trooper': 0.3,
            'assassin': 0.2,
            'brawler': 0.2,
            'scout': 0.1,
        }
    else:
        # Late game: All types including elite enemies
        weights = {
            'sniper': 0.15,
            'brawler': 0.15,
            'assassin': 0.15,
            'trooper': 0.15,
            'scout': 0.1,
            'guardian': 0.15,
            'acolyte': 0.15,
        }
    
    enemies = []
    enemy_types = list(weights.keys())
    type_weights = list(weights.values())
    
    for _ in range(count):
        enemy_type = random.choices(enemy_types, weights=type_weights)[0]
        enemy = ENEMY_TYPES[enemy_type](level=depth)
        enemies.append(enemy)
    
    return enemies
"""


# Example 3: Boss encounter with diverse minions
# ----------------------------------------------
"""
def spawn_boss_encounter(depth):
    '''Create a boss fight with tactical minions.'''
    from jedi_fugitive.game.diverse_enemies import (
        create_sith_guardian,
        create_sith_sniper,
        create_sith_assassin,
        create_dark_acolyte
    )
    
    # Boss is a powerful Acolyte
    boss = create_dark_acolyte(level=depth + 3)
    boss.hp *= 2  # Double HP for boss
    boss.name = "Sith Lord"
    boss.is_boss = True
    boss.symbol = '@'
    
    # Tactical support squad
    minions = [
        create_sith_guardian(level=depth),  # Tank to protect boss
        create_sith_sniper(level=depth),    # Ranged support
        create_sith_assassin(level=depth),  # Flanker to harass
    ]
    
    return boss, minions
"""


# Example 4: Replace spawn in a specific function
# -----------------------------------------------
# Find in game_manager.py, look for enemy spawning code like:
"""
# OLD:
enemy = Enemy("Sith Trooper", 20, 10, 5, 10, None, xp_value=25, level=depth)
enemy.x = x
enemy.y = y
self.enemies.append(enemy)

# REPLACE WITH:
from jedi_fugitive.game.diverse_enemies import create_random_enemy
enemy = create_random_enemy(level=depth)
enemy.x = x
enemy.y = y
self.enemies.append(enemy)
"""


# Example 5: Strategic enemy placement
# ------------------------------------
"""
def place_tactical_squad(game, center_x, center_y, depth):
    '''Place a tactically diverse squad around a position.'''
    from jedi_fugitive.game.diverse_enemies import (
        create_sith_sniper,
        create_sith_brawler,
        create_sith_trooper
    )
    
    # Sniper in the back
    sniper = create_sith_sniper(level=depth)
    sniper.x = center_x
    sniper.y = center_y - 3  # Behind the group
    game.enemies.append(sniper)
    
    # Brawler in front
    brawler = create_sith_brawler(level=depth)
    brawler.x = center_x
    brawler.y = center_y + 2  # Front line
    game.enemies.append(brawler)
    
    # Troopers on flanks
    for offset in [-2, 2]:
        trooper = create_sith_trooper(level=depth)
        trooper.x = center_x + offset
        trooper.y = center_y
        game.enemies.append(trooper)
"""


# Example 6: Testing in headless mode
# -----------------------------------
"""
# In scripts/headless_smoke.py or similar:
from jedi_fugitive.game.diverse_enemies import create_mixed_group

# Replace enemy spawning:
game.enemies = create_mixed_group(count=5, level=3)
for i, enemy in enumerate(game.enemies):
    enemy.x = game.player.x + (i % 3) * 2
    enemy.y = game.player.y + (i // 3) * 2
"""


# Integration Checklist
# --------------------
"""
□ 1. Import diverse_enemies module in game_manager.py
□ 2. Replace Enemy() calls with create_*_enemy() calls
□ 3. Test coordinated charging with 3+ enemies
□ 4. Verify gun targeting works (Press 'F' with ranged weapon equipped)
□ 5. Test grenade throwing (Press 't')
□ 6. Check travel log entries use alignment-based narrative
□ 7. Run test_diverse_enemies.py to verify all systems
□ 8. Play test with diverse enemy compositions
"""


if __name__ == "__main__":
    print("=" * 60)
    print("DIVERSE ENEMIES INTEGRATION GUIDE")
    print("=" * 60)
    print()
    print("This file contains examples of how to integrate the new")
    print("diverse enemy system into your game.")
    print()
    print("Key changes:")
    print("  1. Import from jedi_fugitive.game.diverse_enemies")
    print("  2. Use factory functions instead of Enemy() constructor")
    print("  3. Enemies have enemy_behavior attribute set automatically")
    print()
    print("Quick start:")
    print("  from jedi_fugitive.game.diverse_enemies import create_random_enemy")
    print("  enemy = create_random_enemy(level=5)")
    print()
    print("See examples above for more advanced usage patterns.")
    print("=" * 60)
