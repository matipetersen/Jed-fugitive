#!/usr/bin/env python3
"""
Test script to show the REVISED stress system balance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def show_revised_stress_sources():
    """Show revised stress sources"""
    print("=== REVISED STRESS SOURCES ===\n")
    
    print("Per-Turn Stress (REDUCED):")
    print("  Being Hunted: +3 stress (every 2nd turn, was +5 every turn)")
    print("  Combat Turn: +1-3 stress (every 3rd turn based on nearby enemies, was +2 every turn)")
    print("  Low HP (<25%): +3 stress (every 4th turn, was +5 every turn)")
    print("  Critical HP (<10%): +4 stress (every 3rd turn, NEW)")
    print("  Surrounded (3+ enemies): +15 stress (once, was +20)")
    print("  Dark Area: +10 stress (once, unchanged)")
    print()
    
    print("NEW: Passive Recovery:")
    print("  Safe (no enemies within 8 tiles): -1 stress every 5 turns")
    print()
    
    print("NEW: Combat Victory Relief:")
    print("  Defeat enemy: -2 stress")
    print("  Defeat tough enemy (level 3+): -4 stress")
    print("  Defeat boss: -8 stress")
    print()

def simulate_revised_combat():
    """Simulate combat with new system"""
    print("=== REVISED COMBAT SIMULATION ===\n")
    
    scenarios = [
        {
            "name": "Level 1, No Equipment (15 turn fight, 3 kills)",
            "level": 1,
            "equipment_mitigation": 0.0,
            "turns": 15,
            "kills": [5, 10, 15],  # Turn numbers when enemies die
        },
        {
            "name": "Level 5, Cloth Robes (15 turn fight, 3 kills)",
            "level": 5,
            "equipment_mitigation": 0.30,
            "turns": 15,
            "kills": [5, 10, 15],
        },
        {
            "name": "Level 10, Full Gear (15 turn fight, 3 kills)",
            "level": 10,
            "equipment_mitigation": 0.45,
            "turns": 15,
            "kills": [5, 10, 15],
        },
    ]
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        stress = 0
        level = scenario['level']
        equip_mit = scenario['equipment_mitigation']
        level_reduction = 0.03 * (level - 1)
        total_mitigation = min(0.60, level_reduction + equip_mit)
        
        enemy_count = 2  # Start with 2 enemies nearby
        low_hp_turn = 10  # Go low HP at turn 10
        
        for turn in range(1, scenario['turns'] + 1):
            turn_stress = 0
            
            # Combat stress - every 3rd turn, scaled by enemies
            if turn % 3 == 0 and enemy_count > 0:
                raw = min(3, max(1, enemy_count // 2))
                mitigated = int(raw * (1.0 - total_mitigation))
                turn_stress += mitigated
            
            # Low HP stress - every 4th turn after turn 10
            if turn >= low_hp_turn and turn % 4 == 0:
                raw = 3
                mitigated = int(raw * (1.0 - total_mitigation))
                turn_stress += mitigated
            
            # Apply stress
            stress += turn_stress
            
            # Check for kills
            if turn in scenario['kills']:
                stress = max(0, stress - 2)  # Victory relief
                enemy_count -= 1
                turn_stress -= 2  # Show the reduction
            
            if turn % 5 == 0:
                print(f"  Turn {turn}: {stress} stress ({turn_stress:+d} this turn, {enemy_count} enemies left)")
        
        # Determine tier
        if stress <= 30:
            tier = "Low"
        elif stress <= 60:
            tier = "Medium"
        elif stress <= 85:
            tier = "High"
        else:
            tier = "CRITICAL"
        
        print(f"  Final: {stress} stress ({tier} tier)")
        print()

def show_improvements():
    """Show improvements over old system"""
    print("=== KEY IMPROVEMENTS ===\n")
    
    print("1. SLOWER STRESS ACCUMULATION")
    print("   Old: +2 every turn in combat = +30 stress in 15 turns")
    print("   New: +1-3 every 3rd turn = +5-15 stress in 15 turns")
    print("   Result: 50-75% less combat stress")
    print()
    
    print("2. LOW HP LESS PUNISHING")
    print("   Old: +5 every turn when low HP = +25 stress in 5 turns")
    print("   New: +3 every 4th turn when low HP = +3-6 stress in 5 turns")
    print("   Result: 75% less low HP stress")
    print()
    
    print("3. VICTORY PROVIDES RELIEF")
    print("   Old: No stress reduction for kills")
    print("   New: -2 stress per kill, -4 for tough enemies, -8 for bosses")
    print("   Result: Combat has positive payoff")
    print()
    
    print("4. PASSIVE RECOVERY WHEN SAFE")
    print("   Old: Stress only reduced by items/abilities")
    print("   New: -1 stress every 5 turns when safe (>8 tiles from enemies)")
    print("   Result: Exploration naturally reduces stress")
    print()
    
    print("5. BETTER ABILITY RECOVERY")
    print("   Old: Force abilities reduce -5 stress")
    print("   New: Force abilities reduce -10 stress")
    print("   Result: More meaningful stress management tool")
    print()
    
    print("6. IMPROVED LEVEL UP")
    print("   Old: Complete stress reset on level up")
    print("   New: -30 stress on level up (with feedback message)")
    print("   Result: Meaningful but not trivializing")
    print()

def compare_old_vs_new():
    """Direct comparison of old vs new stress rates"""
    print("=== OLD vs NEW SYSTEM COMPARISON ===\n")
    
    print("Level 1 Player, 10 Turns Combat, No Equipment:")
    print()
    
    # Old system
    old_stress = 0
    old_stress += 2 * 10  # Combat every turn
    print(f"OLD SYSTEM: {old_stress} stress")
    print("  - Combat: +2/turn × 10 = +20")
    print("  - Total: 20 stress (Tier 1)")
    print()
    
    # New system
    new_stress = 0
    new_stress += 1 * (10 // 3)  # Combat every 3rd turn
    new_stress -= 2 * 2  # 2 kills
    print(f"NEW SYSTEM: {max(0, new_stress)} stress")
    print("  - Combat: +1/3rd turn × 3 = +3")
    print("  - Victory: -2 × 2 kills = -4")
    print(f"  - Total: {max(0, new_stress)} stress (Tier 1, much better!)")
    print()
    
    print("Level 1 Player, 15 Turns Combat + Low HP:")
    print()
    
    # Old system
    old_stress = 0
    old_stress += 2 * 15  # Combat every turn
    old_stress += 5 * 6   # Low HP for 6 turns
    print(f"OLD SYSTEM: {old_stress} stress")
    print("  - Combat: +2/turn × 15 = +30")
    print("  - Low HP: +5/turn × 6 = +30")
    print("  - Total: 60 stress (Tier 2 - Medium)")
    print()
    
    # New system
    new_stress = 0
    new_stress += 1 * (15 // 3)  # Combat every 3rd turn
    new_stress += 3 * (6 // 4)   # Low HP every 4th turn
    new_stress -= 2 * 2  # 2 kills
    print(f"NEW SYSTEM: {max(0, new_stress)} stress")
    print("  - Combat: +1/3rd turn × 5 = +5")
    print("  - Low HP: +3/4th turn × 1 = +3")
    print("  - Victory: -2 × 2 kills = -4")
    print(f"  - Total: {max(0, new_stress)} stress (Tier 1 - much more manageable!)")
    print()

if __name__ == "__main__":
    print("REVISED STRESS SYSTEM\n")
    print("="*60 + "\n")
    
    show_revised_stress_sources()
    print("="*60 + "\n")
    
    simulate_revised_combat()
    print("="*60 + "\n")
    
    show_improvements()
    print("="*60 + "\n")
    
    compare_old_vs_new()
    
    print("="*60)
    print("\nRevised system is much more balanced!")
    print("- Stress rises 50-75% slower")
    print("- Victory provides relief")
    print("- Safe exploration gradually reduces stress")
    print("- Force abilities more effective for stress management")
