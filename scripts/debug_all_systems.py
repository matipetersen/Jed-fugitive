#!/usr/bin/env python3
"""
Comprehensive system debugger for Jedi Fugitive.
Tests all major systems and reports errors.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 80)
    print("TESTING MODULE IMPORTS")
    print("=" * 80)
    print()
    
    modules = [
        'jedi_fugitive.game.game_manager',
        'jedi_fugitive.game.player',
        'jedi_fugitive.game.enemy',
        'jedi_fugitive.game.enemies_sith',
        'jedi_fugitive.game.map_features',
        'jedi_fugitive.game.level',
        'jedi_fugitive.game.sith_keep',
        'jedi_fugitive.game.combat',
        'jedi_fugitive.game.force_abilities',
        'jedi_fugitive.items.weapons',
        'jedi_fugitive.items.armor',
        'jedi_fugitive.items.consumables',
        'jedi_fugitive.items.tokens',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed.append((module, e))
    
    print()
    if failed:
        print(f"✗ {len(failed)} modules failed to import")
        for mod, err in failed:
            print(f"  - {mod}: {err}")
        return False
    else:
        print(f"✓ All {len(modules)} modules imported successfully")
        return True


def test_player_creation():
    """Test player creation."""
    print("\n" + "=" * 80)
    print("TESTING PLAYER CREATION")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.game.player import Player
        player = Player(10, 10)
        
        # Check critical attributes
        checks = [
            ('hp', player.hp),
            ('max_hp', player.max_hp),
            ('force_points', player.force_points),
            ('level', player.level),
            ('stress', player.stress),
            ('inventory', player.inventory),
        ]
        
        for attr, value in checks:
            print(f"  {attr}: {value}")
        
        print()
        print("✓ Player created successfully")
        return True
    except Exception as e:
        print(f"✗ Player creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enemy_creation():
    """Test enemy creation."""
    print("\n" + "=" * 80)
    print("TESTING ENEMY CREATION")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.game import enemies_sith as sith
        
        enemies = [
            ('Sith Trooper', lambda: sith.create_sith_trooper(1, 0, 0)),
            ('Sith Acolyte', lambda: sith.create_sith_acolyte(1, 0, 0)),
            ('Sith Warrior', lambda: sith.create_sith_warrior(5, 0, 0)),
            ('Sith Inquisitor', lambda: sith.create_sith_inquisitor(10, 0, 0)),
        ]
        
        for name, creator in enemies:
            try:
                enemy = creator()
                print(f"  ✓ {name}: HP={enemy.hp}, ATK={enemy.attack}, DEF={enemy.defense}")
            except Exception as e:
                print(f"  ✗ {name} creation failed: {e}")
                return False
        
        print()
        print("✓ All enemies created successfully")
        return True
    except Exception as e:
        print(f"✗ Enemy creation system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_level_generation():
    """Test dungeon level generation."""
    print("\n" + "=" * 80)
    print("TESTING DUNGEON GENERATION")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.game.level import generate_dungeon_level
        
        for depth in [1, 2, 3]:
            try:
                level_map, rooms = generate_dungeon_level(depth)
                print(f"  ✓ Level {depth}: {len(level_map)}x{len(level_map[0])} map, {len(rooms)} rooms")
            except Exception as e:
                print(f"  ✗ Level {depth} generation failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        print()
        print("✓ Dungeon generation successful")
        return True
    except Exception as e:
        print(f"✗ Dungeon generation system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_items():
    """Test item definitions."""
    print("\n" + "=" * 80)
    print("TESTING ITEMS")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.items.weapons import WEAPONS
        from jedi_fugitive.items.armor import ARMORS
        from jedi_fugitive.items.consumables import ITEM_DEFS
        
        print(f"  Weapons: {len(WEAPONS)} defined")
        print(f"  Armor: {len(ARMORS)} defined")
        print(f"  Consumables: {len(ITEM_DEFS)} defined")
        
        # Test a few weapons
        if WEAPONS:
            print(f"  Sample weapon: {WEAPONS[0].name} (dmg: {WEAPONS[0].base_damage})")
        
        # Test a few armors
        if ARMORS:
            print(f"  Sample armor: {ARMORS[0].name} (def: {ARMORS[0].defense})")
        
        print()
        print("✓ Items loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Items system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_force_abilities():
    """Test Force abilities."""
    print("\n" + "=" * 80)
    print("TESTING FORCE ABILITIES")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.game.force_abilities import FORCE_ABILITIES
        
        if not FORCE_ABILITIES:
            print("  ⚠ No Force abilities found")
            return True
        
        print(f"  Force abilities: {len(FORCE_ABILITIES)} defined")
        
        for ability in FORCE_ABILITIES[:5]:  # Show first 5
            name = getattr(ability, 'name', 'Unknown')
            cost = getattr(ability, 'cost', 0)
            print(f"    - {name} (cost: {cost} FP)")
        
        print()
        print("✓ Force abilities loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Force abilities system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sith_keep():
    """Test Sith Keep generation."""
    print("\n" + "=" * 80)
    print("TESTING SITH KEEP GENERATION")
    print("=" * 80)
    print()
    
    try:
        from jedi_fugitive.game.sith_keep import generate_sith_keep_layout
        
        layout, entrance, chambers, boss_chamber = generate_sith_keep_layout()
        
        print(f"  Keep size: {len(layout)}x{len(layout[0])}")
        print(f"  Entrance: {entrance}")
        print(f"  Chambers: {len(chambers)}")
        print(f"  Boss chamber: {boss_chamber}")
        
        print()
        print("✓ Sith Keep generation successful")
        return True
    except Exception as e:
        print(f"✗ Sith Keep generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all system tests."""
    print("\n" + "=" * 80)
    print("JEDI FUGITIVE - COMPREHENSIVE SYSTEM DEBUGGER")
    print("=" * 80)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Player Creation", test_player_creation),
        ("Enemy Creation", test_enemy_creation),
        ("Dungeon Generation", test_level_generation),
        ("Items", test_items),
        ("Force Abilities", test_force_abilities),
        ("Sith Keep", test_sith_keep),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL SYSTEMS OPERATIONAL")
        return 0
    else:
        print(f"\n✗ {total - passed} SYSTEMS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
