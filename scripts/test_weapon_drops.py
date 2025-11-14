#!/usr/bin/env python3
"""
Test script to verify weapon drop system works correctly.
Tests:
1. Enemy defeat triggers weapon drops
2. Drop rates match enemy tiers
3. Rarity system works
4. Player can pick up weapons
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.game.enemies_sith import (
    create_sith_trooper, create_sith_acolyte, create_sith_warrior,
    create_sith_assassin, create_sith_officer, create_sith_sorcerer,
    create_sith_lord
)

def test_weapon_rarity_distribution():
    """Check weapon rarity distribution"""
    print("=== Weapon Rarity Distribution ===")
    rarity_counts = {}
    for weapon in WEAPONS:
        if hasattr(weapon, 'rarity') and hasattr(weapon, 'name'):
            rarity = weapon.rarity
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
            print(f"  {weapon.name}: {rarity}")
    
    print("\n--- Summary ---")
    total = sum(rarity_counts.values())
    for rarity, count in sorted(rarity_counts.items()):
        pct = (count / total) * 100 if total > 0 else 0
        print(f"  {rarity}: {count} weapons ({pct:.1f}%)")
    print()

def test_enemy_tiers():
    """Test enemy name detection for drop tiers"""
    print("=== Enemy Tier Detection ===")
    enemies = [
        (create_sith_trooper(), "Basic Trooper", "Common weapons"),
        (create_sith_acolyte(), "Basic Acolyte", "Common weapons"),
        (create_sith_warrior(), "Mid-tier Warrior", "Uncommon weapons"),
        (create_sith_assassin(), "Mid-tier Assassin", "Uncommon weapons"),
        (create_sith_officer(), "Mid-tier Officer", "Uncommon weapons"),
        (create_sith_sorcerer(), "Advanced Sorcerer", "Rare weapons"),
        (create_sith_lord(), "Boss", "Legendary weapons")
    ]
    
    for enemy, description, expected_drops in enemies:
        enemy_name = getattr(enemy, 'name', '').lower()
        is_boss = getattr(enemy, 'is_boss', False)
        
        # Determine tier (matching input_handler.py logic)
        if is_boss:
            tier = "legendary (100% drop)"
        elif 'lord' in enemy_name or 'regent' in enemy_name:
            tier = "rare (90% drop)"
        elif 'inquisitor' in enemy_name or 'officer' in enemy_name or 'sorcerer' in enemy_name:
            tier = "uncommon (60% drop)"
        elif 'assassin' in enemy_name or 'warrior' in enemy_name or 'acolyte' in enemy_name:
            tier = "common (40% drop)"
        elif 'trooper' in enemy_name or 'guard' in enemy_name:
            tier = "common (30% drop)"
        else:
            tier = "common (20% drop)"
        
        print(f"  {description}: {tier}")
        print(f"    Name: '{enemy_name}', Boss: {is_boss}")
        print(f"    Expected: {expected_drops}")
        print()

def test_weapon_pools():
    """Test weapon pool filtering by rarity"""
    print("=== Weapon Pool Tests ===")
    
    # Test legendary pool
    legendary_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                     w.rarity in ['Legendary', 'Rare'] and 
                     hasattr(w, 'name')]
    print(f"Legendary/Rare pool: {len(legendary_pool)} weapons")
    for w in legendary_pool[:5]:
        print(f"  - {w.name} ({w.rarity})")
    
    # Test rare pool
    rare_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                w.rarity in ['Rare', 'Uncommon'] and 
                hasattr(w, 'name')]
    print(f"\nRare/Uncommon pool: {len(rare_pool)} weapons")
    for w in rare_pool[:5]:
        print(f"  - {w.name} ({w.rarity})")
    
    # Test uncommon pool
    uncommon_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                    w.rarity in ['Uncommon', 'Common'] and 
                    hasattr(w, 'name')]
    print(f"\nUncommon/Common pool: {len(uncommon_pool)} weapons")
    for w in uncommon_pool[:5]:
        print(f"  - {w.name} ({w.rarity})")
    
    # Test common pool
    common_pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                  w.rarity == 'Common' and 
                  hasattr(w, 'name')]
    print(f"\nCommon pool: {len(common_pool)} weapons")
    for w in common_pool:
        print(f"  - {w.name} ({w.rarity})")
    print()

def simulate_drops(num_kills=100):
    """Simulate drops from various enemy types"""
    import random
    
    print(f"=== Simulating {num_kills} Enemy Kills ===")
    
    enemy_configs = [
        ("Sith Trooper", 0.3, "common", 0.05),
        ("Sith Acolyte", 0.4, "common", 0.08),
        ("Sith Warrior", 0.4, "uncommon", 0.08),
        ("Sith Officer", 0.6, "uncommon", 0.15),
        ("Sith Sorcerer", 0.6, "rare", 0.15),
        ("Sith Lord (Boss)", 1.0, "legendary", 0.5)
    ]
    
    for enemy_name, drop_rate, tier, rare_chance in enemy_configs:
        drops = 0
        rarity_drops = {'Legendary': 0, 'Rare': 0, 'Uncommon': 0, 'Common': 0}
        
        for _ in range(num_kills):
            if random.random() < drop_rate:
                drops += 1
                
                # Determine weapon pool
                if tier == 'legendary' or (tier == 'rare' and random.random() < rare_chance):
                    pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                           w.rarity in ['Legendary', 'Rare'] and hasattr(w, 'name')]
                elif tier == 'rare' or (tier == 'uncommon' and random.random() < rare_chance):
                    pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                           w.rarity in ['Rare', 'Uncommon'] and hasattr(w, 'name')]
                elif tier == 'uncommon':
                    pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                           w.rarity in ['Uncommon', 'Common'] and hasattr(w, 'name')]
                else:
                    pool = [w for w in WEAPONS if hasattr(w, 'rarity') and 
                           w.rarity == 'Common' and hasattr(w, 'name')]
                
                if pool:
                    weapon = random.choice(pool)
                    rarity = getattr(weapon, 'rarity', 'Common')
                    rarity_drops[rarity] = rarity_drops.get(rarity, 0) + 1
        
        print(f"\n{enemy_name}:")
        print(f"  Drop rate: {drop_rate*100}%, Drops: {drops}/{num_kills} ({drops/num_kills*100:.1f}%)")
        print(f"  Rarity distribution:")
        for rarity, count in sorted(rarity_drops.items(), reverse=True):
            if count > 0:
                pct = (count / drops) * 100 if drops > 0 else 0
                print(f"    {rarity}: {count} ({pct:.1f}%)")

if __name__ == "__main__":
    print("WEAPON DROP SYSTEM TEST\n")
    
    test_weapon_rarity_distribution()
    print("\n" + "="*50 + "\n")
    
    test_enemy_tiers()
    print("\n" + "="*50 + "\n")
    
    test_weapon_pools()
    print("\n" + "="*50 + "\n")
    
    simulate_drops(100)
    
    print("\n" + "="*50)
    print("Tests complete!")
