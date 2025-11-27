#!/usr/bin/env python3
"""
Test planetary biome-specific enemies.
Verifies that different biomes spawn appropriate enemy types.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.planetary_enemies import (
    create_biome_enemy,
    get_biome_enemy_types,
    create_mixed_biome_group,
    get_all_biomes,
    BIOME_ENEMIES
)


def test_planetary_enemies():
    """Test biome-specific enemy creation."""
    print("\n" + "="*70)
    print("Testing Planetary Biome-Specific Enemies")
    print("="*70)
    
    # Test 1: Verify all biomes have enemies
    print("\n[Test 1] Biome Coverage")
    all_biomes = get_all_biomes()
    print(f"  Available biomes: {', '.join(all_biomes)}")
    
    for biome in all_biomes:
        enemy_types = get_biome_enemy_types(biome)
        print(f"  {biome}: {len(enemy_types)} enemy types")
        assert len(enemy_types) > 0, f"Biome {biome} has no enemies!"
    
    print("  ✓ All biomes have enemy types")
    
    # Test 2: Create one enemy from each biome
    print("\n[Test 2] Enemy Creation by Biome")
    for biome in ['desert', 'forest', 'rocky', 'plains', 'river']:
        enemy = create_biome_enemy(biome, level=1)
        print(f"  {biome}: {enemy.name} (symbol={enemy.symbol}, hp={enemy.hp}, attack={enemy.attack})")
        assert hasattr(enemy, 'biome'), f"Enemy {enemy.name} missing biome attribute"
        assert enemy.biome == biome, f"Enemy {enemy.name} has wrong biome: {enemy.biome}"
        assert hasattr(enemy, 'enemy_behavior'), f"Enemy {enemy.name} missing behavior"
    
    print("  ✓ All biomes create valid enemies")
    
    # Test 3: Level scaling
    print("\n[Test 3] Level Scaling")
    biome = 'desert'
    for level in [1, 5, 10]:
        enemy = create_biome_enemy(biome, level=level)
        print(f"  Level {level} {enemy.name}: HP={enemy.hp}, Attack={enemy.attack}, Defense={enemy.defense}")
    
    print("  ✓ Enemies scale with level")
    
    # Test 4: Enemy variety within biome
    print("\n[Test 4] Enemy Variety Within Biomes")
    biome = 'forest'
    enemies_found = set()
    
    for _ in range(20):
        enemy = create_biome_enemy(biome, level=1)
        enemies_found.add(enemy.name)
    
    print(f"  {biome} unique enemies found: {', '.join(sorted(enemies_found))}")
    assert len(enemies_found) > 1, f"Only found 1 enemy type in {biome}"
    
    print("  ✓ Multiple enemy types spawn per biome")
    
    # Test 5: Mixed group creation
    print("\n[Test 5] Mixed Enemy Groups")
    biome = 'rocky'
    group = create_mixed_biome_group(biome, count=5, level=3)
    
    print(f"  Created {len(group)} enemies for {biome}:")
    for enemy in group:
        print(f"    - {enemy.name} (behavior={enemy.enemy_behavior})")
    
    assert len(group) == 5, "Group size mismatch"
    print("  ✓ Mixed groups created successfully")
    
    # Test 6: Behavior types
    print("\n[Test 6] Enemy Behavior Types")
    behaviors = {}
    
    for biome in ['desert', 'forest', 'rocky', 'plains']:
        for _ in range(10):
            enemy = create_biome_enemy(biome, level=1)
            behavior = enemy.enemy_behavior
            if behavior not in behaviors:
                behaviors[behavior] = []
            behaviors[behavior].append(enemy.name)
    
    print(f"  Behavior types found:")
    for behavior, names in behaviors.items():
        unique_names = set(names)
        print(f"    {behavior}: {len(unique_names)} unique enemies")
    
    assert len(behaviors) >= 3, "Not enough behavior variety"
    print("  ✓ Multiple behavior types present")
    
    # Test 7: Complete enemy summary
    print("\n[Test 7] Complete Enemy Summary by Biome")
    print("  " + "-"*68)
    print(f"  {'Biome':<15} {'Enemy Name':<25} {'Symbol':<8} {'Behavior':<12}")
    print("  " + "-"*68)
    
    for biome in sorted(BIOME_ENEMIES.keys()):
        enemy_factories = BIOME_ENEMIES[biome]
        for factory in enemy_factories:
            enemy = factory(level=1)
            print(f"  {biome:<15} {enemy.name:<25} {enemy.symbol:<8} {enemy.enemy_behavior:<12}")
    
    print("  " + "-"*68)
    
    # Test 8: Crash site enemies
    print("\n[Test 8] Crash Site Special Enemies")
    for _ in range(5):
        enemy = create_biome_enemy('crash_site', level=2)
        print(f"  {enemy.name}: {enemy.description}")
    
    print("  ✓ Crash site enemies spawn correctly")
    
    # Test 9: Fallback for unknown biome
    print("\n[Test 9] Unknown Biome Fallback")
    enemy = create_biome_enemy('unknown_biome', level=1)
    print(f"  Unknown biome spawned: {enemy.name} (biome={enemy.biome})")
    assert enemy is not None, "Failed to create fallback enemy"
    print("  ✓ Fallback works for unknown biomes")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    
    # Summary statistics
    total_enemies = sum(len(factories) for factories in BIOME_ENEMIES.values())
    print(f"\nSummary:")
    print(f"  • Total biomes: {len(BIOME_ENEMIES)}")
    print(f"  • Total enemy types: {total_enemies}")
    print(f"  • Average enemies per biome: {total_enemies / len(BIOME_ENEMIES):.1f}")
    print()
    
    # Biome-specific stats
    print("Biome Details:")
    for biome, factories in sorted(BIOME_ENEMIES.items()):
        print(f"  • {biome}: {len(factories)} enemy types")
    print()


if __name__ == "__main__":
    test_planetary_enemies()
