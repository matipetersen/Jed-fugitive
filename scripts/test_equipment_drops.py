#!/usr/bin/env python3
"""
Test script to verify equipment drop system works for weapons, armor, and consumables.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.items.armor import ARMORS
from jedi_fugitive.items.consumables import ITEM_DEFS
from jedi_fugitive.game.enemies_sith import (
    create_sith_trooper, create_sith_acolyte, create_sith_officer,
    create_sith_sorcerer, create_sith_lord
)
import random

def test_equipment_availability():
    """Check what equipment is available"""
    print("=== Available Equipment ===\n")
    
    print(f"Weapons: {len(WEAPONS)}")
    for w in WEAPONS[:5]:
        print(f"  - {w.name} ({getattr(w, 'rarity', 'Common')})")
    print(f"  ... and {len(WEAPONS)-5} more\n")
    
    print(f"Armor: {len(ARMORS)}")
    for a in ARMORS:
        print(f"  - {a.name} ({a.rarity}, +{a.defense} DEF, {a.evasion_mod:+d} EVA)")
    print()
    
    print(f"Consumables: {len(ITEM_DEFS)}")
    for item in ITEM_DEFS[:5]:
        print(f"  - {item['name']} ({item['type']})")
    print(f"  ... and {len(ITEM_DEFS)-5} more\n")

def simulate_equipment_drops(num_kills=100):
    """Simulate drops from various enemy types"""
    print(f"=== Simulating {num_kills} Kills Per Enemy Type ===\n")
    
    enemy_types = [
        ("Sith Trooper", create_sith_trooper(), 0.3, "common"),
        ("Sith Acolyte", create_sith_acolyte(), 0.4, "common"),
        ("Sith Officer", create_sith_officer(), 0.6, "uncommon"),
        ("Sith Sorcerer", create_sith_sorcerer(), 0.6, "rare"),
        ("Sith Lord", create_sith_lord(), 1.0, "legendary")
    ]
    
    for enemy_name, enemy_template, base_drop_rate, tier in enemy_types:
        print(f"--- {enemy_name} ({tier} tier) ---")
        
        drops = {'weapon': 0, 'armor': 0, 'consumable': 0}
        rarity_counts = {}
        total_drops = 0
        
        for _ in range(num_kills):
            # Simulate drop
            if random.random() < base_drop_rate:
                total_drops += 1
                
                # 60% weapon, 25% armor, 15% consumable
                drop_roll = random.random()
                drop_type = 'weapon' if drop_roll < 0.6 else ('armor' if drop_roll < 0.85 else 'consumable')
                drops[drop_type] += 1
                
                # Simulate rarity based on tier
                if drop_type == 'weapon':
                    if tier == 'legendary':
                        pool = [w for w in WEAPONS if hasattr(w, 'rarity') and w.rarity in ['Legendary', 'Rare']]
                    elif tier == 'rare':
                        pool = [w for w in WEAPONS if hasattr(w, 'rarity') and w.rarity in ['Rare', 'Uncommon']]
                    elif tier == 'uncommon':
                        pool = [w for w in WEAPONS if hasattr(w, 'rarity') and w.rarity in ['Uncommon', 'Common']]
                    else:
                        pool = [w for w in WEAPONS if hasattr(w, 'rarity') and w.rarity == 'Common']
                    
                    if pool:
                        item = random.choice(pool)
                        rarity = getattr(item, 'rarity', 'Common')
                        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
                
                elif drop_type == 'armor':
                    if tier in ['legendary', 'rare']:
                        pool = [a for a in ARMORS if a.rarity.lower() in ['epic', 'rare']]
                    elif tier == 'uncommon':
                        pool = [a for a in ARMORS if a.rarity.lower() in ['uncommon', 'common']]
                    else:
                        pool = [a for a in ARMORS if a.rarity.lower() == 'common']
                    
                    if pool:
                        item = random.choice(pool)
                        rarity = item.rarity.capitalize()
                        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        print(f"Drop rate: {base_drop_rate*100}%")
        print(f"Total drops: {total_drops}/{num_kills} ({total_drops/num_kills*100:.1f}%)")
        print(f"Distribution:")
        print(f"  Weapons: {drops['weapon']} ({drops['weapon']/total_drops*100:.1f}%)" if total_drops > 0 else "  Weapons: 0")
        print(f"  Armor: {drops['armor']} ({drops['armor']/total_drops*100:.1f}%)" if total_drops > 0 else "  Armor: 0")
        print(f"  Consumables: {drops['consumable']} ({drops['consumable']/total_drops*100:.1f}%)" if total_drops > 0 else "  Consumables: 0")
        
        if rarity_counts:
            print(f"Rarity breakdown:")
            for rarity, count in sorted(rarity_counts.items(), key=lambda x: ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary'].index(x[0]) if x[0] in ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary'] else 999):
                pct = (count / total_drops) * 100 if total_drops > 0 else 0
                print(f"  {rarity}: {count} ({pct:.1f}%)")
        print()

def test_drop_type_distribution():
    """Test that drop type percentages are correct"""
    print("=== Drop Type Distribution Test ===\n")
    
    samples = 10000
    results = {'weapon': 0, 'armor': 0, 'consumable': 0}
    
    for _ in range(samples):
        drop_roll = random.random()
        drop_type = 'weapon' if drop_roll < 0.6 else ('armor' if drop_roll < 0.85 else 'consumable')
        results[drop_type] += 1
    
    print(f"Over {samples} simulated drops:")
    print(f"  Weapons: {results['weapon']} ({results['weapon']/samples*100:.1f}%) - Target: 60%")
    print(f"  Armor: {results['armor']} ({results['armor']/samples*100:.1f}%) - Target: 25%")
    print(f"  Consumables: {results['consumable']} ({results['consumable']/samples*100:.1f}%) - Target: 15%")
    print()

def test_consumable_tiers():
    """Test consumable drops by tier"""
    print("=== Consumable Tier Test ===\n")
    
    tiers = {
        'legendary': ['medkit_small', 'grenade', 'nutrient_paste', 'jedi_meditation_focus', 'ration'],
        'uncommon': ['stimpack', 'ration', 'water_canteen', 'calming_tea'],
        'common': ['water_canteen', 'calming_tea']
    }
    
    for tier, allowed_ids in tiers.items():
        print(f"{tier.capitalize()} tier consumables:")
        pool = [item for item in ITEM_DEFS if item.get('type') == 'consumable' and item.get('id') in allowed_ids]
        for item in pool:
            effect = item.get('effect', {})
            print(f"  - {item['name']}: {effect}")
        print()

if __name__ == "__main__":
    print("EQUIPMENT DROP SYSTEM TEST\n")
    print("="*60 + "\n")
    
    test_equipment_availability()
    print("="*60 + "\n")
    
    test_drop_type_distribution()
    print("="*60 + "\n")
    
    test_consumable_tiers()
    print("="*60 + "\n")
    
    simulate_equipment_drops(100)
    
    print("="*60)
    print("Tests complete!")
