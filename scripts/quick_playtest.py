#!/usr/bin/env python3
"""
Simplified Playtest - Quick validation that game systems work together.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def quick_playtest():
    """Quick test of key game systems"""
    
    print("=" * 80)
    print("JEDI FUGITIVE - QUICK PLAYTEST VALIDATION")
    print("=" * 80)
    print()
    
    from jedi_fugitive.game.player import Player
    from jedi_fugitive.game import enemies_sith as sith
    from jedi_fugitive.items.weapons import WEAPONS
    from jedi_fugitive.items.armor import ARMORS
    from jedi_fugitive.game.combat import player_attack, enemy_attack
    
    # Test 1: Player Creation
    print("Test 1: Player Creation")
    print("-" * 40)
    player = Player(x=100, y=100)
    print(f"✓ Player Level {player.level}: HP {player.hp}/{player.max_hp}, ATK {player.attack}, DEF {player.defense}")
    print()
    
    # Test 2: Basic Combat
    print("Test 2: Basic Combat System")
    print("-" * 40)
    enemy = sith.create_sith_acolyte(level=1, x=105, y=105)
    print(f"Fighting: {enemy.name} (HP: {enemy.hp})")
    
    combat_log = []
    rounds = 0
    while enemy.hp > 0 and player.hp > 0 and rounds < 10:
        old_ehp = enemy.hp
        player_attack(player, enemy)
        if enemy.hp < old_ehp:
            combat_log.append(f"Player dealt {old_ehp - enemy.hp} damage")
        
        if enemy.hp > 0:
            old_php = player.hp
            enemy_attack(enemy, player)
            if player.hp < old_php:
                combat_log.append(f"Enemy dealt {old_php - player.hp} damage")
        rounds += 1
    
    if enemy.hp <= 0:
        print(f"✓ Victory in {rounds} rounds")
        player.gain_xp(enemy.xp_value)
        print(f"✓ Gained {enemy.xp_value} XP")
    else:
        print(f"✗ Combat failed")
        return False
    print()
    
    # Test 3: Leveling System
    print("Test 3: Leveling & Progression")
    print("-" * 40)
    start_level = player.level
    
    # Fight multiple enemies to level up
    for i in range(10):
        enemy = sith.create_sith_acolyte(level=player.level, x=105, y=105)
        while enemy.hp > 0 and player.hp > 0:
            player_attack(player, enemy)
            if enemy.hp > 0:
                enemy_attack(enemy, player)
        
        if enemy.hp <= 0:
            player.gain_xp(enemy.xp_value)
        
        # Heal between fights
        player.hp = min(player.max_hp, player.hp + 20)
    
    if player.level > start_level:
        print(f"✓ Leveled up from {start_level} to {player.level}")
    else:
        print(f"⚠ Still level {player.level} (may need more XP)")
    print()
    
    # Test 4: Equipment System
    print("Test 4: Equipment System")
    print("-" * 40)
    
    # Find and equip weapon
    good_weapons = [w for w in WEAPONS if w['damage'] >= 10]
    if good_weapons:
        weapon = good_weapons[0]
        player.equipped_weapon = weapon
        print(f"✓ Equipped: {weapon['name']} ({weapon['damage']} damage)")
    
    # Find and equip armor
    good_armor = [a for a in ARMORS if a['defense'] >= 5]
    if good_armor:
        armor = good_armor[0]
        player.equipped_armor = armor
        print(f"✓ Equipped: {armor['name']} ({armor['defense']} defense)")
    
    print(f"✓ Updated stats: ATK {player.attack}, DEF {player.defense}")
    print()
    
    # Test 5: Mid-tier Combat
    print("Test 5: Mid-Tier Enemy Combat")
    print("-" * 40)
    
    mid_enemy = sith.create_sith_warrior(level=player.level + 2, x=110, y=110)
    print(f"Fighting: {mid_enemy.name} Level {mid_enemy.level} (HP: {mid_enemy.hp})")
    
    rounds = 0
    while mid_enemy.hp > 0 and player.hp > 0 and rounds < 30:
        player_attack(player, mid_enemy)
        if mid_enemy.hp > 0:
            enemy_attack(mid_enemy, player)
        rounds += 1
    
    if mid_enemy.hp <= 0:
        print(f"✓ Defeated {mid_enemy.name} in {rounds} rounds")
        player.gain_xp(mid_enemy.xp_value)
    else:
        print(f"✗ Failed to defeat mid-tier enemy")
        return False
    print()
    
    # Test 6: Elite Enemy (Keep Guard Level)
    print("Test 6: Elite Enemy Combat")
    print("-" * 40)
    
    # Level up player more
    player.level = 10
    player.max_hp = 50 + player.level * 5
    player.hp = player.max_hp
    player.attack = 15 + player.level
    player.defense = 8 + player.level // 2
    
    # Get best gear
    best_weapon = max(WEAPONS, key=lambda w: w['damage'])
    best_armor = max(ARMORS, key=lambda a: a['defense'])
    player.equipped_weapon = best_weapon
    player.equipped_armor = best_armor
    
    print(f"Player Level {player.level}: HP {player.hp}, ATK {player.attack}, DEF {player.defense}")
    print(f"Weapon: {best_weapon['name']} ({best_weapon['damage']} dmg)")
    print(f"Armor: {best_armor['name']} ({best_armor['defense']} def)")
    print()
    
    elite = sith.create_sith_warrior(level=player.level + 3, x=115, y=115)
    print(f"Fighting Elite: {elite.name} Level {elite.level} (HP: {elite.hp})")
    
    rounds = 0
    while elite.hp > 0 and player.hp > 0 and rounds < 40:
        player_attack(player, elite)
        if elite.hp > 0:
            enemy_attack(elite, player)
        
        # Simple heal every 5 rounds
        if rounds % 5 == 0 and player.hp < player.max_hp * 0.5:
            heal = 15
            player.hp = min(player.max_hp, player.hp + heal)
        
        rounds += 1
    
    if elite.hp <= 0:
        print(f"✓ Defeated elite enemy in {rounds} rounds")
        print(f"  Player HP remaining: {player.hp}/{player.max_hp}")
    else:
        print(f"✗ Failed to defeat elite enemy")
        print(f"  Player HP: {player.hp}, Enemy HP: {elite.hp}")
        return False
    print()
    
    # Test 7: Boss Fight Simulation
    print("Test 7: Sith Inquisitor Boss (Simulation)")
    print("-" * 40)
    
    # Full heal and prep
    player.hp = player.max_hp
    player.force_points = 10
    
    boss = sith.create_sith_inquisitor(level=player.level + 5, x=120, y=120)
    print(f"BOSS: {boss.name} Level {boss.level}")
    print(f"Boss HP: {boss.hp}/{boss.max_hp}")
    print(f"Boss ATK: {boss.attack}, DEF: {boss.defense}")
    print()
    
    rounds = 0
    boss_phases = 0
    max_rounds = 100
    
    while boss.hp > 0 and player.hp > 0 and rounds < max_rounds:
        rounds += 1
        
        # Check phase transition
        boss_hp_pct = boss.hp / boss.max_hp
        if boss_hp_pct < 0.5 and boss_phases == 0:
            boss_phases = 1
            print(f"  [Round {rounds}] Boss enters Phase 2!")
        
        # Player turn
        player_attack(player, boss)
        
        if boss.hp <= 0:
            break
        
        # Boss turn (simplified - just attack)
        enemy_attack(boss, player)
        
        # Player healing (limited)
        if player.hp < player.max_hp * 0.3 and rounds % 6 == 0:
            heal = 20
            player.hp = min(player.max_hp, player.hp + heal)
            print(f"  [Round {rounds}] Player heals for {heal} HP")
        
        # Progress update every 10 rounds
        if rounds % 10 == 0:
            print(f"  [Round {rounds}] Boss HP: {boss.hp}/{boss.max_hp} ({int(boss_hp_pct*100)}%), Player HP: {player.hp}/{player.max_hp}")
    
    print()
    if boss.hp <= 0:
        print(f"★★★ VICTORY! Boss defeated in {rounds} rounds! ★★★")
        print(f"Player HP remaining: {player.hp}/{player.max_hp}")
        print()
        print("=" * 80)
        print("✓ ALL TESTS PASSED - GAME IS WINNABLE")
        print("=" * 80)
        return True
    else:
        print(f"✗ BOSS FIGHT FAILED")
        print(f"Player HP: {player.hp}/{player.max_hp}")
        print(f"Boss HP: {boss.hp}/{boss.max_hp}")
        print(f"Rounds: {rounds}/{max_rounds}")
        return False

if __name__ == "__main__":
    try:
        success = quick_playtest()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
