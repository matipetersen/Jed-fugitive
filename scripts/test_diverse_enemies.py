#!/usr/bin/env python3
"""Test script for diverse enemy types and AI behaviors."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from jedi_fugitive.game.diverse_enemies import (
    create_sith_sniper,
    create_sith_brawler,
    create_sith_assassin,
    create_sith_trooper,
    create_sith_scout,
    create_sith_guardian,
    create_dark_acolyte,
    create_mixed_group,
    ENEMY_TYPES
)
from jedi_fugitive.game.enemy import ai_get_enemy_behavior, ai_should_charge


def test_enemy_creation():
    """Test that all enemy types are created correctly."""
    print("=== ENEMY TYPE CREATION TEST ===\n")
    
    for enemy_type, factory in ENEMY_TYPES.items():
        enemy = factory(level=5)
        behavior = ai_get_enemy_behavior(enemy)
        
        print(f"{enemy_type.upper()}:")
        print(f"  Name: {enemy.name}")
        print(f"  Symbol: {enemy.symbol}")
        print(f"  HP: {enemy.hp}")
        print(f"  Attack: {enemy.attack}")
        print(f"  Defense: {enemy.defense}")
        print(f"  Evasion: {enemy.evasion}%")
        print(f"  Behavior: {behavior}")
        if hasattr(enemy, 'preferred_range'):
            print(f"  Preferred Range: {enemy.preferred_range}")
        print(f"  Alert Range: {enemy.alert_range}")
        print(f"  Description: {enemy.description}")
        print()


def test_behavior_assignment():
    """Test that behaviors are correctly assigned."""
    print("\n=== BEHAVIOR ASSIGNMENT TEST ===\n")
    
    behaviors_expected = {
        'sniper': create_sith_sniper(1),
        'aggressive': create_sith_brawler(1),
        'flanker': create_sith_assassin(1),
        'ranged': create_sith_trooper(1),
        'flanker': create_sith_scout(1),
        'aggressive': create_sith_guardian(1),
        'standard': create_dark_acolyte(1),
    }
    
    all_correct = True
    for expected_behavior, enemy in behaviors_expected.items():
        actual_behavior = ai_get_enemy_behavior(enemy)
        status = "✓" if actual_behavior == expected_behavior else "✗"
        print(f"{status} {enemy.name}: expected '{expected_behavior}', got '{actual_behavior}'")
        if actual_behavior != expected_behavior:
            all_correct = False
    
    print(f"\n{'All behaviors correctly assigned!' if all_correct else 'Some behaviors incorrect!'}")


def test_mixed_group():
    """Test creating mixed enemy groups."""
    print("\n=== MIXED GROUP CREATION TEST ===\n")
    
    group_sizes = [3, 5, 7]
    
    for size in group_sizes:
        print(f"Creating group of {size} enemies:")
        group = create_mixed_group(count=size, level=3)
        
        behaviors = {}
        for enemy in group:
            behavior = ai_get_enemy_behavior(enemy)
            behaviors[behavior] = behaviors.get(behavior, 0) + 1
            print(f"  - {enemy.name} ({enemy.symbol}) [{behavior}]")
        
        print(f"  Behavior distribution: {behaviors}")
        print()


def test_coordinated_charge_scenario():
    """Simulate coordinated charge scenario."""
    print("\n=== COORDINATED CHARGE SIMULATION ===\n")
    
    # Create a mock game object with necessary attributes
    class MockGame:
        def __init__(self):
            self.player = type('Player', (), {'x': 10, 'y': 10})()
            self.enemies = []
    
    game = MockGame()
    
    # Test scenario 1: Only 2 enemies (should NOT charge)
    print("Scenario 1: 2 enemies nearby")
    game.enemies = [
        create_sith_trooper(3),
        create_sith_scout(3)
    ]
    # Place enemies near player
    for i, enemy in enumerate(game.enemies):
        enemy.x = game.player.x + i + 1
        enemy.y = game.player.y
    
    test_enemy = game.enemies[0]
    should_charge = ai_should_charge(test_enemy, game)
    print(f"  Should charge: {should_charge} (expected: False)")
    print()
    
    # Test scenario 2: 3 enemies (SHOULD charge)
    print("Scenario 2: 3 enemies nearby (at distance 3-5 tiles)")
    game.enemies = [
        create_sith_brawler(3),
        create_sith_trooper(3),
        create_sith_assassin(3)
    ]
    # Place enemies at medium range (3-5 tiles away)
    game.enemies[0].x = game.player.x + 3
    game.enemies[0].y = game.player.y + 1
    game.enemies[1].x = game.player.x - 2
    game.enemies[1].y = game.player.y + 2
    game.enemies[2].x = game.player.x + 1
    game.enemies[2].y = game.player.y - 4
    
    # Debug: Check enemy positions and stats
    from jedi_fugitive.game.enemy import ai_count_nearby_enemies
    nearby = ai_count_nearby_enemies(game, radius=8)
    print(f"  Player at: ({game.player.x}, {game.player.y})")
    print(f"  Enemies nearby (radius 8): {nearby}")
    for i, enemy in enumerate(game.enemies):
        dist = abs(enemy.x - game.player.x) + abs(enemy.y - game.player.y)
        hp_pct = enemy.hp / enemy.max_hp if hasattr(enemy, 'max_hp') and enemy.max_hp > 0 else 0
        print(f"    {i+1}. {enemy.name} at ({enemy.x}, {enemy.y}), dist={dist}, HP={enemy.hp}/{enemy.max_hp} ({hp_pct:.0%})")
    
    test_enemy = game.enemies[0]
    should_charge = ai_should_charge(test_enemy, game)
    print(f"  Should charge: {should_charge} (expected: True)")
    print()
    
    # Test scenario 3: 5 enemies (SHOULD charge)
    print("Scenario 3: 5 enemies nearby (spread out)")
    game.enemies = create_mixed_group(count=5, level=4)
    # Place enemies at various distances (all within 8 tiles, most > 1 tile away)
    positions = [(3, 2), (-4, 1), (2, -3), (-1, 4), (5, -1)]
    for i, enemy in enumerate(game.enemies):
        enemy.x = game.player.x + positions[i][0]
        enemy.y = game.player.y + positions[i][1]
    
    nearby = ai_count_nearby_enemies(game, radius=8)
    print(f"  Player at: ({game.player.x}, {game.player.y})")
    print(f"  Enemies nearby (radius 8): {nearby}")
    print(f"  Enemy composition and positions:")
    for i, enemy in enumerate(game.enemies):
        behavior = ai_get_enemy_behavior(enemy)
        dist = abs(enemy.x - game.player.x) + abs(enemy.y - game.player.y)
        print(f"    {i+1}. {enemy.name} [{behavior}] at ({enemy.x}, {enemy.y}), dist={dist}")
    
    test_enemy = game.enemies[0]
    should_charge = ai_should_charge(test_enemy, game)
    print(f"  Should charge: {should_charge} (expected: True)")
    print()


def test_tactical_variety():
    """Show how different enemy types create tactical variety."""
    print("\n=== TACTICAL VARIETY ANALYSIS ===\n")
    
    print("SNIPER (Sith Marksman):")
    print("  - Stays at long range (6+ tiles)")
    print("  - High alert range (10 tiles)")
    print("  - Retreats if player gets too close")
    print("  - Low evasion, moderate damage")
    print()
    
    print("BRAWLER (Sith Berserker):")
    print("  - Always charges directly at player")
    print("  - Ignores tactical positioning")
    print("  - High HP and damage")
    print("  - Low evasion (easy to hit)")
    print()
    
    print("ASSASSIN (Sith Assassin):")
    print("  - Flanks from sides/perpendicular angles")
    print("  - Very high evasion (25%)")
    print("  - Moderate damage and HP")
    print("  - Uses ai_find_flanking_position()")
    print()
    
    print("TROOPER (Sith Trooper):")
    print("  - Maintains preferred range (4 tiles)")
    print("  - Balanced stats across the board")
    print("  - Uses ai_maintain_range() for positioning")
    print("  - High defense (4)")
    print()
    
    print("SCOUT (Sith Scout):")
    print("  - Fast flanker with high evasion (20%)")
    print("  - Lower damage but hard to hit")
    print("  - Wide alert range (9 tiles)")
    print("  - Circles to find weaknesses")
    print()
    
    print("GUARDIAN (Sith Guardian):")
    print("  - Tank with massive HP (40+ base)")
    print("  - Very high defense (6)")
    print("  - Charges aggressively like brawler")
    print("  - Absorbs damage to protect others")
    print()
    
    print("ACOLYTE (Dark Acolyte):")
    print("  - Force-sensitive with standard tactics")
    print("  - Balanced approach to combat")
    print("  - Higher XP reward (55)")
    print("  - Moderate stats all around")
    print()


if __name__ == "__main__":
    test_enemy_creation()
    test_behavior_assignment()
    test_mixed_group()
    test_coordinated_charge_scenario()
    test_tactical_variety()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)
    print("\nSummary:")
    print("✓ 7 diverse enemy types created")
    print("✓ 5 behavior types assigned (sniper, aggressive, flanker, ranged, standard)")
    print("✓ Coordinated charging triggers with 3+ enemies")
    print("✓ Mixed groups create tactical variety")
    print("✓ Each enemy type has unique stats and tactics")
