#!/usr/bin/env python3
"""
Full Playtest Simulation - Test complete game flow from start to victory.
Tests: Combat, loot caches, merchants, Sith Keep, and final boss.
"""

import sys
import os
import random

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def simulate_full_playthrough():
    """Simulate a complete playthrough from start to Sith Keep victory"""
    
    print("=" * 80)
    print("JEDI FUGITIVE - FULL PLAYTEST SIMULATION")
    print("=" * 80)
    print()
    
    # Import game components
    from jedi_fugitive.game.player import Player
    from jedi_fugitive.game import enemies_sith as sith
    from jedi_fugitive.items.weapons import WEAPONS
    from jedi_fugitive.items.armor import ARMORS
    from jedi_fugitive.game.combat import player_attack, enemy_attack
    
    print("Phase 1: Character Creation & Early Game")
    print("-" * 80)
    
    # Create player
    player = Player(x=100, y=100)
    print(f"✓ Player created: Level {player.level}")
    print(f"  HP: {player.hp}/{player.max_hp}")
    print(f"  Attack: {player.attack}, Defense: {player.defense}")
    print(f"  Force Points: {player.force_points}")
    print()
    
    # Early combat simulation
    print("Phase 2: Early Combat (Levels 1-3)")
    print("-" * 80)
    
    kills = 0
    for i in range(5):
        enemy = sith.create_sith_acolyte(level=1, x=105, y=105)
        print(f"\nEncounter {i+1}: {enemy.name} (HP: {enemy.hp}, ATK: {enemy.attack})")
        
        rounds = 0
        while enemy.hp > 0 and player.hp > 0 and rounds < 20:
            # Player attacks
            old_hp = enemy.hp
            player_attack(player, enemy)
            if enemy.hp < old_hp:
                dmg = old_hp - enemy.hp
                print(f"  Round {rounds+1}: Player hits for {dmg} damage ({enemy.hp} HP left)")
            else:
                print(f"  Round {rounds+1}: Player misses")
            
            if enemy.hp <= 0:
                kills += 1
                xp = enemy.xp_value
                old_level = player.level
                player.gain_xp(xp)
                print(f"  ✓ Victory! Gained {xp} XP")
                if player.level > old_level:
                    print(f"  ★ LEVEL UP! Now level {player.level}")
                break
            
            # Enemy attacks
            old_php = player.hp
            enemy_attack(enemy, player)
            if player.hp < old_php:
                dmg = old_php - player.hp
                print(f"  Round {rounds+1}: {enemy.name} hits for {dmg} damage ({player.hp} HP left)")
            
            rounds += 1
        
        if player.hp <= 0:
            print("\n✗ GAME OVER - Player died in early game!")
            return False
    
    print(f"\n✓ Early game complete: {kills} enemies defeated, Level {player.level}")
    print()
    
    # Find and equip better gear
    print("Phase 3: Loot Cache Discovery (Levels 3-5)")
    print("-" * 80)
    
    # Simulate finding loot cache
    print("\nSimulating loot cache discovery...")
    
    # Clear guards first
    for i in range(3):
        guard = sith.create_sith_trooper(level=player.level, x=110, y=110)
        print(f"  Cache Guard {i+1}: {guard.name} (HP: {guard.hp})")
        
            # Quick combat
            combat_rounds = 0
            while guard.hp > 0 and player.hp > 0 and combat_rounds < 15:
                player_attack(player, guard)
                
                if guard.hp <= 0:
                    player.gain_xp(guard.xp_value)
                    print(f"    ✓ Defeated! Gained {guard.xp_value} XP")
                    break
                
                enemy_attack(guard, player)
                
                combat_rounds += 1        if player.hp <= 0:
            print("\n✗ GAME OVER - Died fighting cache guards!")
            return False
    
    # Loot the cache
    print("\n  Opening loot cache...")
    cache_weapons = [w for w in WEAPONS if w['damage'] >= 8 and w['damage'] <= 12]
    cache_armor = [a for a in ARMORS if a['defense'] >= 4 and a['defense'] <= 7]
    
    if cache_weapons:
        weapon = random.choice(cache_weapons)
        print(f"  ★ Found: {weapon['name']} ({weapon['damage']} damage)")
        player.equipped_weapon = weapon
        player.attack = 5 + weapon['damage']
    
    if cache_armor:
        armor = random.choice(cache_armor)
        print(f"  ★ Found: {armor['name']} ({armor['defense']} defense)")
        player.equipped_armor = armor
        player.defense = 3 + armor['defense']
    
    print(f"\n✓ New stats: ATK {player.attack}, DEF {player.defense}")
    print()
    
    # Merchant encounter
    print("Phase 4: Merchant Trading (Levels 5-7)")
    print("-" * 80)
    
    # Give player some gold
    player.gold = 200
    print(f"\nPlayer has {player.gold} gold")
    
    # Simulate buying from merchant
    print("\nVisiting Mandalorian Arms Dealer...")
    
    # Buy a better weapon
    advanced_weapons = [w for w in WEAPONS if w['damage'] >= 12 and w['damage'] <= 18]
    if advanced_weapons:
        weapon = random.choice(advanced_weapons)
        cost = int(weapon['value'] * 1.3)  # Markup
        if player.gold >= cost:
            print(f"  Buying: {weapon['name']} ({weapon['damage']} damage) for {cost} gold")
            player.gold -= cost
            player.equipped_weapon = weapon
            player.attack = 5 + weapon['damage']
            print(f"  ★ Purchased! Gold remaining: {player.gold}")
    
    # Sell old gear
    old_gold = player.gold
    player.gold += 50  # Simulate selling old items
    print(f"  Sold old equipment for 50 gold (total: {player.gold})")
    
    print()
    
    # Mid-game leveling
    print("Phase 5: Mid-Game Progression (Levels 7-10)")
    print("-" * 80)
    
    print("\nFighting progressively stronger enemies...")
    
    enemy_types = [
        ("Sith Warrior", sith.create_sith_warrior),
        ("Sith Assassin", sith.create_sith_assassin),
        ("Sith Sorcerer", sith.create_sith_sorcerer),
        ("Sith Officer", sith.create_sith_officer),
    ]
    
    for enemy_name, enemy_func in enemy_types:
        for i in range(3):
            enemy = enemy_func(level=player.level, x=120, y=120)
            
            # Quick combat simulation
            rounds = 0
            while enemy.hp > 0 and player.hp > 0 and rounds < 25:
                # Player attacks
                if calculate_hit(player.attack, enemy.defense, player.evasion):
                    dmg = calculate_damage(player.attack, enemy.defense)
                    enemy.hp -= dmg
                
                if enemy.hp <= 0:
                    old_level = player.level
                    player.gain_xp(enemy.xp_value)
                    if player.level > old_level:
                        # Level up healing
                        player.hp = min(player.max_hp, player.hp + 20)
                    break
                
                # Enemy attacks
                if calculate_hit(enemy.attack, player.defense, getattr(enemy, 'evasion', 0)):
                    dmg = calculate_damage(enemy.attack, player.defense)
                    player.hp -= dmg
                
                rounds += 1
            
            if player.hp <= 0:
                print(f"\n✗ GAME OVER - Died fighting {enemy_name}!")
                return False
            
            # Heal up between fights
            player.hp = min(player.max_hp, player.hp + 10)
    
    print(f"✓ Mid-game complete: Level {player.level}")
    print(f"  HP: {player.hp}/{player.max_hp}")
    print(f"  ATK: {player.attack}, DEF: {player.defense}")
    print()
    
    # Prepare for Sith Keep
    print("Phase 6: Sith Keep Preparation (Level 10+)")
    print("-" * 80)
    
    # Get best gear
    print("\nAcquiring end-game equipment...")
    
    best_weapons = sorted(WEAPONS, key=lambda w: w['damage'], reverse=True)[:5]
    best_weapon = best_weapons[0]
    print(f"  ★ Equipped: {best_weapon['name']} ({best_weapon['damage']} damage)")
    player.equipped_weapon = best_weapon
    player.attack = 5 + best_weapon['damage'] + (player.level - 1)
    
    best_armors = sorted(ARMORS, key=lambda a: a['defense'], reverse=True)[:5]
    best_armor = best_armors[0]
    print(f"  ★ Equipped: {best_armor['name']} ({best_armor['defense']} defense)")
    player.equipped_armor = best_armor
    player.defense = 3 + best_armor['defense'] + (player.level - 1) // 2
    
    # Full heal
    player.hp = player.max_hp
    player.force_points = 10
    
    print(f"\n✓ Ready for Sith Keep!")
    print(f"  Level: {player.level}")
    print(f"  HP: {player.hp}/{player.max_hp}")
    print(f"  ATK: {player.attack}, DEF: {player.defense}")
    print(f"  Force: {player.force_points}")
    print()
    
    # Sith Keep - Elite Guards
    print("Phase 7: Sith Keep - Elite Guards")
    print("-" * 80)
    
    print("\nFighting elite guards in the keep...")
    
    for i in range(6):
        guard_level = player.level + random.randint(2, 4)
        guard = sith.create_sith_warrior(level=guard_level, x=150, y=150)
        
        print(f"\n  Elite Guard {i+1}: {guard.name} Level {guard.level} (HP: {guard.hp})")
        
        rounds = 0
        while guard.hp > 0 and player.hp > 0 and rounds < 30:
            # Player attacks (with force abilities)
            hit = calculate_hit(player.attack, guard.defense, player.evasion)
            if hit:
                dmg = calculate_damage(player.attack, guard.defense)
                # Bonus from force abilities
                if player.force_points > 0 and rounds % 3 == 0:
                    dmg = int(dmg * 1.3)  # Force-enhanced strike
                    player.force_points -= 1
                    print(f"    Round {rounds+1}: Force-enhanced strike! {dmg} damage")
                else:
                    print(f"    Round {rounds+1}: Hit for {dmg} damage")
                guard.hp -= dmg
            
            if guard.hp <= 0:
                player.gain_xp(guard.xp_value)
                print(f"    ✓ Guard defeated!")
                break
            
            # Guard attacks
            if calculate_hit(guard.attack, player.defense, 0):
                dmg = calculate_damage(guard.attack, player.defense)
                player.hp -= dmg
                print(f"    Round {rounds+1}: Guard hits for {dmg} damage ({player.hp} HP left)")
            
            rounds += 1
        
        if player.hp <= 0:
            print("\n✗ GAME OVER - Died fighting elite guards!")
            return False
        
        # Recover some HP between guards
        player.hp = min(player.max_hp, player.hp + 15)
        
        # Recover some Force
        if i % 2 == 0:
            player.force_points = min(10, player.force_points + 2)
    
    print(f"\n✓ All guards defeated!")
    print(f"  HP: {player.hp}/{player.max_hp}")
    print(f"  Force: {player.force_points}")
    print()
    
    # Final Boss - Sith Inquisitor
    print("Phase 8: FINAL BOSS - Sith Inquisitor")
    print("-" * 80)
    
    boss_level = player.level + 5
    boss = sith.create_sith_inquisitor(level=boss_level, x=160, y=160)
    
    print(f"\n  ★ BOSS: {boss.name} Level {boss.level}")
    print(f"  HP: {boss.hp}/{boss.max_hp}")
    print(f"  ATK: {boss.attack}, DEF: {boss.defense}")
    print(f"  Boss has Force Lightning, Heal, and Force Drain abilities")
    print()
    
    # Full heal before boss
    player.hp = player.max_hp
    player.force_points = 10
    
    print("  Beginning epic battle...")
    
    rounds = 0
    boss_phase = 1
    force_drained = 0
    
    while boss.hp > 0 and player.hp > 0 and rounds < 100:
        rounds += 1
        
        # Check boss phase transitions
        boss_hp_percent = boss.hp / boss.max_hp
        if boss_hp_percent < 0.5 and boss_phase == 1:
            boss_phase = 2
            print(f"\n  ★★ BOSS PHASE 2: Inquisitor becomes more aggressive!")
        
        # Player turn
        player_hit = calculate_hit(player.attack, boss.defense, player.evasion)
        if player_hit:
            dmg = calculate_damage(player.attack, boss.defense)
            
            # Use force abilities strategically
            if player.force_points >= 2 and rounds % 4 == 0:
                # Force Lightning
                dmg = int(dmg * 1.5)
                player.force_points -= 2
                print(f"  Round {rounds}: Player uses Force Lightning! {dmg} damage")
            else:
                print(f"  Round {rounds}: Player hits for {dmg} damage")
            
            boss.hp -= dmg
            print(f"    Boss HP: {boss.hp}/{boss.max_hp} ({int(boss_hp_percent*100)}%)")
        else:
            print(f"  Round {rounds}: Player misses!")
        
        if boss.hp <= 0:
            break
        
        # Boss turn
        boss_action = random.choice(['attack', 'lightning', 'drain', 'heal'])
        
        if boss_action == 'lightning' and rounds % 3 == 0:
            # Force Lightning
            dmg = 20 + boss.level * 2
            player.hp -= dmg
            print(f"  Round {rounds}: Boss uses Force Lightning! {dmg} damage to player")
        
        elif boss_action == 'drain' and rounds % 4 == 0:
            # Force Drain
            if player.force_points > 0:
                drained = min(2, player.force_points)
                player.force_points -= drained
                boss.force_points = getattr(boss, 'force_points', 0) + drained
                force_drained += drained
                print(f"  Round {rounds}: Boss drains {drained} Force points!")
        
        elif boss_action == 'heal' and boss_hp_percent < 0.4 and boss.force_points > 0:
            # Force Heal
            heal = 15 + boss.level * 2
            boss.hp = min(boss.max_hp, boss.hp + heal)
            boss.force_points -= 1
            print(f"  Round {rounds}: Boss heals for {heal} HP!")
        
        else:
            # Normal attack
            boss_hit = calculate_hit(boss.attack, player.defense, 0)
            if boss_hit:
                dmg = calculate_damage(boss.attack, player.defense)
                if boss_phase == 2:
                    dmg = int(dmg * 1.2)  # Phase 2 bonus
                player.hp -= dmg
                print(f"  Round {rounds}: Boss attacks for {dmg} damage")
        
        print(f"    Player HP: {player.hp}/{player.max_hp}")
        
        # Player healing (limited)
        if player.hp < player.max_hp * 0.3 and player.force_points >= 1 and rounds % 5 == 0:
            heal = 15
            player.hp = min(player.max_hp, player.hp + heal)
            player.force_points -= 1
            print(f"    Player uses Force Heal! +{heal} HP")
        
        # Check defeat
        if player.hp <= 0:
            print("\n✗ DEFEATED BY SITH INQUISITOR!")
            return False
    
    if boss.hp <= 0:
        print(f"\n★★★ VICTORY! Sith Inquisitor defeated in {rounds} rounds! ★★★")
        print()
        
        # Legendary weapon reward
        print("Phase 9: Victory & Rewards")
        print("-" * 80)
        
        legendary_weapons = sorted(WEAPONS, key=lambda w: w['damage'], reverse=True)[:3]
        legendary = legendary_weapons[0]
        
        print(f"\n  ★★★ LEGENDARY WEAPON OBTAINED ★★★")
        print(f"  {legendary['name']}")
        print(f"  Damage: {legendary['damage']}")
        print(f"  Type: {legendary['type']}")
        print()
        
        print(f"  Final Stats:")
        print(f"  - Level: {player.level}")
        print(f"  - HP: {player.hp}/{player.max_hp}")
        print(f"  - Total XP: {player.xp}")
        print(f"  - Rounds vs Boss: {rounds}")
        print(f"  - Force Drained: {force_drained}")
        
        return True
    else:
        print(f"\n✗ TIMEOUT - Battle took too long ({rounds} rounds)")
        return False

def run_multiple_simulations(count=5):
    """Run multiple playthroughs to test consistency"""
    
    print("=" * 80)
    print(f"RUNNING {count} FULL PLAYTEST SIMULATIONS")
    print("=" * 80)
    print()
    
    wins = 0
    losses = 0
    
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"SIMULATION {i+1}/{count}")
        print(f"{'='*80}\n")
        
        try:
            success = simulate_full_playthrough()
            if success:
                wins += 1
                print(f"\n✓ Simulation {i+1}: VICTORY")
            else:
                losses += 1
                print(f"\n✗ Simulation {i+1}: DEFEAT")
        except Exception as e:
            losses += 1
            print(f"\n✗ Simulation {i+1}: ERROR - {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Final results
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"\nTotal Simulations: {count}")
    print(f"Victories: {wins} ({wins/count*100:.1f}%)")
    print(f"Defeats: {losses} ({losses/count*100:.1f}%)")
    print()
    
    if wins > 0:
        print("✓ GAME IS WINNABLE")
        if wins / count >= 0.5:
            print("✓ Win rate is balanced (50%+)")
        else:
            print("⚠ Win rate is low - game may be too difficult")
    else:
        print("✗ GAME IS UNWINNABLE - No victories in any simulation")
    
    print()
    return wins > 0

if __name__ == "__main__":
    import sys
    
    # Run simulations
    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
        success = run_multiple_simulations(count)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ SIMULATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
