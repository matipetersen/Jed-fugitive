"""
Progressive Enemy Spawning System
Increases enemy respawn rate and difficulty as player progresses through objectives.
"""

import random
from typing import List, Dict, Any


def get_player_progress_score(game) -> int:
    """Calculate player progress score based on completed objectives."""
    score = 0
    
    # Tombs cleared (major progress)
    try:
        tombs_cleared = getattr(game.player, 'tombs_cleared', 0)
        score += tombs_cleared * 20  # 20 points per tomb
    except:
        pass
    
    # Player level progression
    try:
        player_level = getattr(game.player, 'level', 1)
        score += (player_level - 1) * 10  # 10 points per level above 1
    except:
        pass
    
    # Force abilities unlocked
    try:
        force_abilities = len(getattr(game.player, 'force_abilities', []))
        score += force_abilities * 5  # 5 points per Force ability
    except:
        pass
    
    # Equipment upgrades (crafted items)
    try:
        weapon = getattr(game.player, 'equipped_weapon', None)
        if weapon and '(' in getattr(weapon, 'name', ''):  # Upgraded weapon
            score += 15
    except:
        pass
    
    # Turn count (time pressure)
    try:
        turn_count = getattr(game, 'turn_count', 0)
        score += turn_count // 50  # 1 point per 50 turns
    except:
        pass
    
    return score


def calculate_spawn_rate(progress_score: int) -> float:
    """Calculate enemy spawn rate based on progress score."""
    # Base spawn rate: 1 enemy per 100 turns
    base_rate = 0.01
    
    # Increase rate based on progress
    if progress_score < 20:
        return base_rate  # Early game: low spawn rate
    elif progress_score < 50:
        return base_rate * 1.5  # Mid-early: moderate increase
    elif progress_score < 100:
        return base_rate * 2.0  # Mid game: double spawn rate
    elif progress_score < 150:
        return base_rate * 2.5  # Late game: high spawn rate
    else:
        return base_rate * 3.0  # End game: maximum spawn rate


def calculate_enemy_level_bonus(progress_score: int) -> int:
    """Calculate bonus levels for spawned enemies."""
    if progress_score < 30:
        return 0  # No bonus early game
    elif progress_score < 60:
        return 1  # +1 level mid-early
    elif progress_score < 100:
        return 2  # +2 levels mid game
    elif progress_score < 150:
        return 3  # +3 levels late game
    else:
        return 4  # +4 levels end game


def should_spawn_enemy(game) -> bool:
    """Determine if an enemy should spawn this turn."""
    progress_score = get_player_progress_score(game)
    spawn_rate = calculate_spawn_rate(progress_score)
    
    # Random chance based on spawn rate
    return random.random() < spawn_rate


def get_spawn_enemy_type(game, progress_score: int) -> str:
    """Choose enemy type to spawn based on progress."""
    # Enemy type probabilities based on progress
    if progress_score < 20:
        # Early game: mostly basic enemies, rare small creatures
        enemy_types = [
            ('sith_acolyte', 0.55),
            ('sith_warrior', 0.3),
            ('sith_assassin', 0.1),
            ('shadow_stalker', 0.05)  # Small chance of native creature
        ]
    elif progress_score < 60:
        # Mid-early: balanced mix with more creatures
        enemy_types = [
            ('sith_acolyte', 0.35),
            ('sith_warrior', 0.35),
            ('sith_assassin', 0.15),
            ('shadow_stalker', 0.08),
            ('dark_weaver', 0.05),
            ('void_tendril', 0.02)
        ]
    elif progress_score < 100:
        # Mid game: stronger enemies and larger creatures
        enemy_types = [
            ('sith_acolyte', 0.15),
            ('sith_warrior', 0.4),
            ('sith_assassin', 0.18),
            ('sith_lord', 0.07),
            ('shadow_stalker', 0.05),
            ('dark_weaver', 0.05),
            ('void_tendril', 0.03),
            ('bone_crusher', 0.04),
            ('frost_behemoth', 0.03)
        ]
    elif progress_score < 150:
        # Late game: elite enemies and massive creatures
        enemy_types = [
            ('sith_warrior', 0.25),
            ('sith_assassin', 0.3),
            ('sith_lord', 0.15),
            ('sith_marauder', 0.08),
            ('bone_crusher', 0.06),
            ('frost_behemoth', 0.04),
            ('crimson_leviathan', 0.05),
            ('tomb_serpent', 0.04),
            ('dark_weaver', 0.03)
        ]
    else:
        # End game: legendary creatures and elite enemies
        enemy_types = [
            ('sith_assassin', 0.2),
            ('sith_lord', 0.18),
            ('sith_marauder', 0.12),
            ('crimson_leviathan', 0.12),
            ('tomb_serpent', 0.1),
            ('stone_titan', 0.08),
            ('bone_crusher', 0.08),
            ('frost_behemoth', 0.06),
            ('void_tendril', 0.04),
            ('dark_weaver', 0.02)
        ]
    
    # Select enemy type based on probabilities
    rand = random.random()
    cumulative = 0.0
    for enemy_type, probability in enemy_types:
        cumulative += probability
        if rand <= cumulative:
            return enemy_type
    
    return 'sith_warrior'  # Fallback


def find_spawn_location(game) -> tuple:
    """Find a suitable spawn location away from player."""
    player_x = getattr(game.player, 'x', 0)
    player_y = getattr(game.player, 'y', 0)
    
    mh = len(game.game_map)
    mw = len(game.game_map[0]) if mh else 0
    floor_ch = getattr(game.level.Display, 'FLOOR', '.')
    
    # Try to find a spawn location 15+ tiles away from player
    for attempt in range(100):
        x = random.randint(0, mw - 1)
        y = random.randint(0, mh - 1)
        
        # Must be on floor tile
        if game.game_map[y][x] != floor_ch:
            continue
            
        # Must be far enough from player
        distance = abs(x - player_x) + abs(y - player_y)
        if distance < 15:
            continue
            
        # Check no other enemies too close
        too_close = False
        for enemy in game.enemies:
            ex = getattr(enemy, 'x', -999)
            ey = getattr(enemy, 'y', -999)
            if abs(x - ex) + abs(y - ey) < 3:
                too_close = True
                break
        
        if not too_close:
            return (x, y)
    
    # Fallback: spawn anywhere that's floor
    for attempt in range(50):
        x = random.randint(0, mw - 1)
        y = random.randint(0, mh - 1)
        if game.game_map[y][x] == floor_ch:
            return (x, y)
    
    return None


def spawn_progressive_enemy(game) -> bool:
    """Spawn an enemy based on current progress level."""
    try:
        from jedi_fugitive.game import enemies_sith as sith
        
        # Calculate progress and spawn parameters
        progress_score = get_player_progress_score(game)
        level_bonus = calculate_enemy_level_bonus(progress_score)
        enemy_type = get_spawn_enemy_type(game, progress_score)
        
        # Find spawn location
        spawn_pos = find_spawn_location(game)
        if not spawn_pos:
            return False  # Couldn't find suitable location
        
        x, y = spawn_pos
        
        # Calculate enemy level
        player_level = getattr(game.player, 'level', 1)
        enemy_level = max(1, player_level - 1 + level_bonus + random.randint(-1, 2))
        
        # Check if player can sense the disturbance
        player_x = getattr(game.player, 'x', 0)
        player_y = getattr(game.player, 'y', 0)
        distance_to_player = abs(x - player_x) + abs(y - player_y)
        
        # Force disturbance detection (closer spawns are more noticeable)
        if distance_to_player <= 8:  # Within sensing range
            from jedi_fugitive.game.atmosphere import get_force_disturbance
            disturbance_msg = get_force_disturbance()
            try:
                game.ui.messages.add(f"#6#[FORCE SENSE]#0# {disturbance_msg}")
                game.ui.messages.add("#6#[FORCE SENSE]#0# Press 'c' to use Force Sense and reveal the threat...")
            except Exception:
                pass
        
        # Create enemy based on type
        if enemy_type == 'sith_acolyte':
            enemy = sith.create_sith_acolyte(level=enemy_level, x=x, y=y)
        elif enemy_type == 'sith_warrior':
            enemy = sith.create_sith_warrior(level=enemy_level, x=x, y=y)
        elif enemy_type == 'sith_assassin':
            enemy = sith.create_sith_assassin(level=enemy_level, x=x, y=y)
        elif enemy_type == 'sith_lord':
            enemy = sith.create_sith_lord(level=enemy_level, x=x, y=y)
        elif enemy_type == 'sith_marauder':
            enemy = sith.create_sith_marauder(level=enemy_level, x=x, y=y)
        # Massive Creatures
        elif enemy_type == 'crimson_leviathan':
            enemy = sith.create_crimson_leviathan(level=enemy_level, x=x, y=y)
        elif enemy_type == 'bone_crusher':
            enemy = sith.create_bone_crusher(level=enemy_level, x=x, y=y)
        elif enemy_type == 'void_tendril':
            enemy = sith.create_void_tendril(level=enemy_level, x=x, y=y)
        elif enemy_type == 'shadow_stalker':
            enemy = sith.create_shadow_stalker(level=enemy_level, x=x, y=y)
        elif enemy_type == 'stone_titan':
            enemy = sith.create_stone_titan(level=enemy_level, x=x, y=y)
        elif enemy_type == 'tomb_serpent':
            enemy = sith.create_tomb_serpent(level=enemy_level, x=x, y=y)
        elif enemy_type == 'dark_weaver':
            enemy = sith.create_dark_weaver(level=enemy_level, x=x, y=y)
        elif enemy_type == 'frost_behemoth':
            enemy = sith.create_frost_behemoth(level=enemy_level, x=x, y=y)
        else:
            enemy = sith.create_sith_warrior(level=enemy_level, x=x, y=y)
        
        # Mark as progressive spawn
        enemy.name += " (Reinforcement)"
        
        # Add basic patrol around spawn point
        patrol_points = []
        for _ in range(3):
            px = x + random.randint(-3, 3)
            py = y + random.randint(-3, 3)
            patrol_points.append((px, py))
        enemy.patrol_points = patrol_points
        enemy._patrol_index = 0
        
        # Add to game
        game.enemies.append(enemy)
        
        # Optional: notify player
        try:
            if progress_score > 40:  # Only notify after early game
                game.ui.messages.add(f"#2#[THREAT]#0# {enemy.name} arrives to hunt you!")
        except:
            pass
        
        return True
        
    except Exception as e:
        # Fail silently - don't break game
        return False


def process_progressive_spawning(game):
    """Main function to handle progressive enemy spawning each turn."""
    try:
        # Only spawn if not too many enemies already
        current_enemies = len(getattr(game, 'enemies', []))
        max_enemies = 60  # Reasonable limit
        
        if current_enemies >= max_enemies:
            return False
        
        # Check if should spawn
        if should_spawn_enemy(game):
            return spawn_progressive_enemy(game)
        
        return False
        
    except Exception:
        return False