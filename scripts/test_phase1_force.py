#!/usr/bin/env python3
"""Test Phase 1 Force system implementation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player
from jedi_fugitive.game.force_abilities import (
    ForceProtect, ForceMeditation, ForceChoke, ForceDrain, ForceFear
)

def test_force_energy_regeneration():
    """Test Force energy regeneration."""
    print("\n=== Testing Force Energy Regeneration ===")
    player = Player(x=0, y=0)
    
    # Check initial state
    print(f"Initial Force Energy: {player.force_energy}/{player.max_force_energy}")
    assert player.force_energy == 100, "Should start with 100 Force"
    
    # Use some Force
    player.force_energy = 50
    print(f"After spending Force: {player.force_energy}/{player.max_force_energy}")
    
    # Regenerate (peaceful)
    player.regenerate_force(in_combat=False)
    print(f"After peaceful regen (+20): {player.force_energy}/{player.max_force_energy}")
    assert player.force_energy == 70, f"Expected 70, got {player.force_energy}"
    
    # Regenerate (combat)
    player.regenerate_force(in_combat=True)
    print(f"After combat regen (+5): {player.force_energy}/{player.max_force_energy}")
    assert player.force_energy == 75, f"Expected 75, got {player.force_energy}"
    
    # Don't exceed max
    player.force_energy = 95
    player.regenerate_force(in_combat=False)
    print(f"After regen at 95: {player.force_energy}/{player.max_force_energy}")
    assert player.force_energy == 100, "Should cap at max_force_energy"
    
    print("✓ Force regeneration working correctly")

def test_alignment_mastery():
    """Test alignment mastery calculation."""
    print("\n=== Testing Alignment Mastery ===")
    player = Player(x=0, y=0)
    
    # Pure Light (0-20)
    player.dark_corruption = 0
    mastery = player.get_alignment_mastery()
    print(f"Corruption 0 (Pure Light): Mastery {mastery}")
    assert mastery == 3, f"Expected mastery 3, got {mastery}"
    
    player.dark_corruption = 15
    mastery = player.get_alignment_mastery()
    print(f"Corruption 15 (Pure Light): Mastery {mastery}")
    assert mastery == 3, f"Expected mastery 3, got {mastery}"
    
    # Light (21-40)
    player.dark_corruption = 30
    mastery = player.get_alignment_mastery()
    print(f"Corruption 30 (Light): Mastery {mastery}")
    assert mastery == 2, f"Expected mastery 2, got {mastery}"
    
    # Balanced (41-59)
    player.dark_corruption = 50
    mastery = player.get_alignment_mastery()
    print(f"Corruption 50 (Balanced): Mastery {mastery}")
    assert mastery == 1, f"Expected mastery 1, got {mastery}"
    
    # Dark (60-79)
    player.dark_corruption = 70
    mastery = player.get_alignment_mastery()
    print(f"Corruption 70 (Dark): Mastery {mastery}")
    assert mastery == 2, f"Expected mastery 2, got {mastery}"
    
    # Pure Dark (80-100)
    player.dark_corruption = 90
    mastery = player.get_alignment_mastery()
    print(f"Corruption 90 (Pure Dark): Mastery {mastery}")
    assert mastery == 3, f"Expected mastery 3, got {mastery}"
    
    print("✓ Alignment mastery calculation working correctly")

def test_ability_cost_scaling():
    """Test ability cost multipliers."""
    print("\n=== Testing Ability Cost Scaling ===")
    
    # Pure Light player using Light ability
    player = Player(x=0, y=0)
    player.dark_corruption = 10
    
    ability = ForceProtect()
    base_cost = ability.base_cost
    actual_cost = ability.get_actual_cost(player)
    multiplier = player.get_ability_cost_multiplier('light')
    
    print(f"Pure Light (10) using Light ability (Protect):")
    print(f"  Base cost: {base_cost}, Multiplier: {multiplier:.2f}, Actual: {actual_cost}")
    assert multiplier < 1.0, "Should get cost reduction for aligned ability"
    
    # Pure Light player using Dark ability
    dark_multiplier = player.get_ability_cost_multiplier('dark')
    print(f"Pure Light (10) using Dark ability:")
    print(f"  Multiplier: {dark_multiplier:.2f}")
    assert dark_multiplier == 2.0, "Should pay double for opposing alignment"
    
    # Pure Dark player using Dark ability
    player.dark_corruption = 90
    dark_cost_mult = player.get_ability_cost_multiplier('dark')
    print(f"Pure Dark (90) using Dark ability:")
    print(f"  Multiplier: {dark_cost_mult:.2f}")
    assert dark_cost_mult < 1.0, "Should get cost reduction"
    
    print("✓ Ability cost scaling working correctly")

def test_ability_power_scaling():
    """Test ability power multipliers."""
    print("\n=== Testing Ability Power Scaling ===")
    
    # Pure Light player
    player = Player(x=0, y=0)
    player.dark_corruption = 5
    
    light_power = player.get_ability_power_scale('light')
    dark_power = player.get_ability_power_scale('dark')
    
    print(f"Pure Light (5) power scales:")
    print(f"  Light abilities: {light_power:.2f}x")
    print(f"  Dark abilities: {dark_power:.2f}x")
    
    assert light_power > 1.0, "Should get power bonus for aligned abilities"
    assert dark_power == 0.5, "Should get power penalty for opposing abilities"
    
    # Balanced player
    player.dark_corruption = 50
    light_power = player.get_ability_power_scale('light')
    dark_power = player.get_ability_power_scale('dark')
    
    print(f"Balanced (50) power scales:")
    print(f"  Light abilities: {light_power:.2f}x")
    print(f"  Dark abilities: {dark_power:.2f}x")
    
    assert light_power == 1.0, "Balanced should have neutral power"
    assert dark_power == 1.0, "Balanced should have neutral power"
    
    print("✓ Ability power scaling working correctly")

def test_new_abilities_exist():
    """Test that new abilities are defined."""
    print("\n=== Testing New Abilities ===")
    
    abilities = [
        ('ForceProtect', ForceProtect, 'light'),
        ('ForceMeditation', ForceMeditation, 'light'),
        ('ForceChoke', ForceChoke, 'dark'),
        ('ForceDrain', ForceDrain, 'dark'),
        ('ForceFear', ForceFear, 'dark'),
    ]
    
    for name, cls, alignment in abilities:
        ability = cls()
        print(f"  {name}: cost={ability.base_cost}, alignment={ability.alignment}, target={ability.target_type}")
        assert ability.alignment == alignment, f"{name} should be {alignment}"
        assert hasattr(ability, 'get_actual_cost'), f"{name} missing get_actual_cost"
        assert hasattr(ability, 'get_power_scale'), f"{name} missing get_power_scale"
    
    print("✓ All new abilities defined correctly")

def test_force_meditation():
    """Test Meditation ability (free Force restore)."""
    print("\n=== Testing Force Meditation ===")
    
    player = Player(x=0, y=0)
    player.force_energy = 30  # Low Force
    player.stress = 50
    
    ability = ForceMeditation()
    
    class MockMessages:
        def add(self, msg):
            print(f"  Message: {msg}")
    
    messages = MockMessages()
    
    # Should restore Force and reduce stress
    result = ability.use(player, player, None, messages=messages)
    
    print(f"After meditation: Force={player.force_energy}, Stress={player.stress}")
    assert result, "Meditation should succeed"
    assert player.force_energy > 30, "Should restore Force"
    assert player.stress < 50, "Should reduce stress"
    
    print("✓ Meditation working correctly")

if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 1 FORCE SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        test_force_energy_regeneration()
        test_alignment_mastery()
        test_ability_cost_scaling()
        test_ability_power_scaling()
        test_new_abilities_exist()
        test_force_meditation()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - PHASE 1 WORKING!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
