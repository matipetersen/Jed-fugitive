#!/usr/bin/env python3
"""
Test complete equipment flow: enemy drops → pickup → equip → stats application
Verifies both old token system (v, b, s, L) and new equipment drops (E).
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.items.weapons import WEAPONS
from jedi_fugitive.items.armor import ARMORS
from jedi_fugitive.items.consumables import ITEM_DEFS


def test_equipment_drops():
    """Test enemy equipment drops can be picked up and equipped."""
    print("=" * 60)
    print("Testing Equipment Drop Flow")
    print("=" * 60)
    
    # Create minimal game state for testing
    from jedi_fugitive.game.player import Player
    
    class MockUI:
        class Messages:
            def add(self, msg):
                print(f"      [UI] {msg}")
        def __init__(self):
            self.messages = self.Messages()
    
    class MockGame:
        def __init__(self):
            self.player = Player(5, 5)
            self.player.inventory = []
            self.player.attack = 10
            self.player.defense = 5
            self.player.evasion = 0
            self.player.hp = 100
            self.player.max_hp = 100
            self.player._base_stats = {
                "attack": 10,
                "defense": 5,
                "evasion": 0,
                "max_hp": 100
            }
            self.player.equipped_weapon = None
            self.player.equipped_armor = None
            
            # Create map
            self.game_map = [['.' for _ in range(20)] for _ in range(20)]
            self.equipment_drops = {}
            self.items_on_map = []
            self.ui = MockUI()
    
    game = MockGame()
    
    # Save player's initial stats
    print(f"\n1. Initial Player Stats:")
    print(f"   Attack: {game.player.attack}")
    print(f"   Defense: {game.player.defense}")
    print(f"   HP: {game.player.hp}/{game.player.max_hp}")
    print(f"   Inventory: {len(game.player.inventory)} items")
    
    initial_attack = game.player.attack
    initial_defense = game.player.defense
    
    # Test 1: Drop a weapon from WEAPONS list
    print(f"\n2. Testing Weapon Drop (from WEAPONS list):")
    test_weapon = None
    for weapon in WEAPONS:
        if getattr(weapon, 'rarity', '') == 'Rare' and getattr(weapon, 'base_damage', 0) > 0:
            test_weapon = weapon
            break
    
    if test_weapon:
        print(f"   Weapon: {test_weapon.name}")
        print(f"   Base Damage (attack bonus): +{test_weapon.base_damage}")
        
        # Simulate enemy drop at player position
        px, py = game.player.x, game.player.y
        game.game_map[py][px] = 'E'
        
        if not hasattr(game, 'equipment_drops'):
            game.equipment_drops = {}
        
        game.equipment_drops[(px, py)] = {
            'type': 'weapon',
            'item': test_weapon,
            'name': test_weapon.name,
            'rarity': test_weapon.rarity
        }
        
        print(f"   ✓ Placed 'E' token at ({px}, {py})")
        print(f"   ✓ Added to equipment_drops dict")
        
        # Test pickup
        from jedi_fugitive.game.equipment import pick_up
        pick_up(game)
        
        print(f"   ✓ Picked up weapon")
        print(f"   Inventory size: {len(game.player.inventory)}")
        
        if len(game.player.inventory) > 0:
            picked_item = game.player.inventory[-1]
            print(f"   Item in inventory: {picked_item}")
            
            # Test equip
            from jedi_fugitive.game.equipment import equip_item
            equip_item(game)
            
            print(f"   ✓ Equipped weapon")
            print(f"   New Attack: {game.player.attack} (expected: {initial_attack + test_weapon.base_damage})")
            
            if game.player.attack == initial_attack + test_weapon.base_damage:
                print(f"   ✅ Weapon attack bonus applied correctly!")
            else:
                print(f"   ❌ Attack bonus mismatch!")
                print(f"      Expected: {initial_attack + test_weapon.base_damage}")
                print(f"      Got: {game.player.attack}")
        else:
            print(f"   ❌ Weapon not added to inventory!")
    
    # Test 2: Drop armor from ARMORS list
    print(f"\n3. Testing Armor Drop (from ARMORS list):")
    test_armor = None
    for armor in ARMORS:
        if getattr(armor, 'defense', 0) > 0 or (isinstance(armor, dict) and armor.get('defense', 0) > 0):
            test_armor = armor
            break
    
    if test_armor:
        armor_name = getattr(test_armor, 'name', test_armor.get('name', 'Unknown') if isinstance(test_armor, dict) else 'Unknown')
        armor_defense = getattr(test_armor, 'defense', test_armor.get('defense', 0) if isinstance(test_armor, dict) else 0)
        armor_hp = getattr(test_armor, 'hp_bonus', test_armor.get('hp_bonus', 0) if isinstance(test_armor, dict) else 0)
        print(f"   Armor: {armor_name}")
        print(f"   Defense: +{armor_defense}")
        print(f"   HP Bonus: +{armor_hp}")
        
        # Reset player position and drop armor
        px, py = game.player.x, game.player.y
        game.game_map[py][px] = 'E'
        
        armor_name = getattr(test_armor, 'name', test_armor.get('name', 'Unknown') if isinstance(test_armor, dict) else 'Unknown')
        armor_rarity = getattr(test_armor, 'rarity', test_armor.get('rarity', 'Common') if isinstance(test_armor, dict) else 'Common')
        
        game.equipment_drops[(px, py)] = {
            'type': 'armor',
            'item': test_armor,
            'name': armor_name,
            'rarity': armor_rarity
        }
        
        print(f"   ✓ Placed 'E' token at ({px}, {py})")
        
        # Test pickup
        from jedi_fugitive.game.equipment import pick_up
        pick_up(game)
        
        print(f"   ✓ Picked up armor")
        print(f"   Inventory size: {len(game.player.inventory)}")
        
        if len(game.player.inventory) > 0:
            # Find armor in inventory (might not be last item)
            armor_item = None
            armor_name = getattr(test_armor, 'name', test_armor.get('name', 'Unknown') if isinstance(test_armor, dict) else 'Unknown')
            for item in game.player.inventory:
                item_name = getattr(item, 'name', item.get('name', '') if isinstance(item, dict) else '')
                if item_name == armor_name:
                    armor_item = item
                    break
            
            if armor_item:
                item_display = getattr(armor_item, 'name', armor_item.get('name', 'Unknown') if isinstance(armor_item, dict) else 'Unknown')
                print(f"   Item in inventory: {item_display}")
                
                # Manually set chosen item and equip
                game.player.inventory = [armor_item]  # Simplify for test
                from jedi_fugitive.game.equipment import equip_item
                equip_item(game)
                
                print(f"   ✓ Equipped armor")
                print(f"   New Defense: {game.player.defense}")
                print(f"   New Max HP: {game.player.max_hp}")
            else:
                print(f"   ❌ Armor not found in inventory!")
        else:
            print(f"   ❌ Armor not added to inventory!")
    
    # Test 3: Test old token system (v, b, s, L)
    print(f"\n4. Testing Old Token System:")
    print(f"   Testing 'v' (Vibroblade) token...")
    
    # Create new game for token test
    game2 = MockGame()
    initial_attack2 = game2.player.attack
    
    px, py = game2.player.x, game2.player.y
    game2.game_map[py][px] = 'v'
    
    from jedi_fugitive.game.equipment import pick_up, equip_item
    pick_up(game2)
    
    print(f"   ✓ Picked up 'v' token")
    print(f"   Inventory: {game2.player.inventory}")
    
    if len(game2.player.inventory) > 0:
        equip_item(game2)
        print(f"   ✓ Equipped Vibroblade")
        print(f"   Attack before: {initial_attack2}")
        print(f"   Attack after: {game2.player.attack}")
        
        if game2.player.attack > initial_attack2:
            print(f"   ✅ Token system working correctly!")
        else:
            print(f"   ❌ Token did not apply attack bonus!")
    
    print("\n" + "=" * 60)
    print("Equipment Flow Test Complete")
    print("=" * 60)


def test_weapon_objects_directly():
    """Test that weapon objects from WEAPONS list have correct attributes."""
    print("\n" + "=" * 60)
    print("Testing Weapon Objects Structure")
    print("=" * 60)
    
    print(f"\nTotal weapons: {len(WEAPONS)}")
    
    melee_count = 0
    ranged_count = 0
    
    print(f"\nSample weapons with attack bonuses:")
    for i, weapon in enumerate(WEAPONS[:10]):  # First 10 weapons
        rarity = getattr(weapon, 'rarity', 'Unknown')
        base_damage = getattr(weapon, 'base_damage', 0)
        name = getattr(weapon, 'name', 'Unknown')
        
        if 'Blaster' in name or 'Rifle' in name or 'Bowcaster' in name:
            ranged_count += 1
            weapon_type = "RANGED"
        else:
            melee_count += 1
            weapon_type = "MELEE"
        
        print(f"   {i+1}. {name} ({rarity}, {weapon_type})")
        print(f"      base_damage: +{base_damage}")
    
    print(f"\nWeapon distribution:")
    for weapon in WEAPONS:
        name = getattr(weapon, 'name', '')
        if 'Blaster' in name or 'Rifle' in name or 'Bowcaster' in name:
            ranged_count += 1
        else:
            melee_count += 1
    
    total = melee_count + ranged_count
    melee_pct = (melee_count / total * 100) if total > 0 else 0
    ranged_pct = (ranged_count / total * 100) if total > 0 else 0
    
    print(f"   Melee: {melee_count} ({melee_pct:.1f}%)")
    print(f"   Ranged: {ranged_count} ({ranged_pct:.1f}%)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        test_weapon_objects_directly()
        test_equipment_drops()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
