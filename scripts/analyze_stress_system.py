#!/usr/bin/env python3
"""
Test script to analyze stress system progression and effects.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def analyze_stress_sources():
    """Analyze all stress sources and their rates"""
    print("=== STRESS SOURCES ANALYSIS ===\n")
    
    sources = {
        "Being Hunted": {"amount": 5, "frequency": "per turn", "duration": "multiple turns"},
        "Combat Turn": {"amount": 2, "frequency": "per turn in combat", "duration": "ongoing"},
        "Low HP (<25%)": {"amount": 5, "frequency": "per turn", "duration": "while low HP"},
        "Surrounded (3+ enemies)": {"amount": 20, "frequency": "once when triggered", "duration": "one-time"},
        "Dark Area": {"amount": 10, "frequency": "once when entering", "duration": "one-time"},
    }
    
    print("Per-Turn Stress Sources:")
    for source, info in sources.items():
        print(f"  {source}: +{info['amount']} stress ({info['frequency']})")
    
    print("\n--- Typical Combat Scenario ---")
    print("Turn 1: Enter combat (+2 stress from combat_turn)")
    print("Turn 2-5: Each turn in combat (+2 stress/turn = +8 total)")
    print("Turn 6: HP drops below 25% (+5 stress)")
    print("Turn 7-10: Low HP + combat (+7 stress/turn = +28 total)")
    print("Total after 10 turns: 2 + 8 + 5 + 28 = 43 stress")
    print()

def analyze_stress_mitigation():
    """Analyze stress reduction mechanisms"""
    print("=== STRESS MITIGATION ===\n")
    
    print("Per-Level Resilience:")
    print("  Formula: reduction = 3% per level (level - 1)")
    for level in [1, 3, 5, 7, 10]:
        reduction = 0.03 * (level - 1)
        print(f"  Level {level}: {reduction*100:.0f}% stress reduction")
    print()
    
    print("Equipment Mitigation:")
    equipment = {
        "Cloth Robes": 0.30,
        "Scout Vest": 0.10,
        "Kyber Crystal/Focus Weapon": 0.15,
    }
    for item, reduction in equipment.items():
        print(f"  {item}: {reduction*100:.0f}% stress reduction")
    
    print("\n  Maximum mitigation: 60% (capped)")
    print("  Example: Level 5 + Cloth Robes + Kyber Focus")
    level_reduction = 0.03 * (5 - 1)
    equipment_reduction = 0.30 + 0.15
    total = min(0.60, level_reduction + equipment_reduction)
    print(f"    = {level_reduction*100:.0f}% + {equipment_reduction*100:.0f}% = {total*100:.0f}%")
    print()

def analyze_stress_effects():
    """Analyze effects of stress levels"""
    print("=== STRESS EFFECTS ===\n")
    
    stress_tiers = [
        (0, 30, 1, "10% accuracy penalty"),
        (31, 60, 2, "15% accuracy penalty"),
        (61, 85, 3, "25% accuracy penalty"),
        (86, 100, 4, "40% accuracy penalty"),
    ]
    
    print("Stress Tiers:")
    for low, high, tier, effect in stress_tiers:
        print(f"  Tier {tier} ({low}-{high} stress): {effect}")
    
    print("\nAccuracy Example (base 80 accuracy):")
    base_acc = 80
    for low, high, tier, _ in stress_tiers:
        penalties = [0.10, 0.15, 0.25, 0.40]
        penalty = penalties[tier-1]
        # With no resilience
        effective = int(base_acc * (1.0 - penalty))
        print(f"  {low}-{high} stress: {effective} accuracy (-{penalty*100:.0f}%)")
    
    print("\nWith Level 5 Resilience (12% reduction):")
    for low, high, tier, _ in stress_tiers:
        penalties = [0.10, 0.15, 0.25, 0.40]
        penalty = penalties[tier-1]
        # With level 5 resilience
        resilience = 1.0 - (0.03 * 4)  # level 5 = 4 levels of reduction
        effective = int(base_acc * (1.0 - penalty * resilience))
        print(f"  {low}-{high} stress: {effective} accuracy (-{penalty*resilience*100:.1f}%)")
    print()

def simulate_combat_stress():
    """Simulate stress accumulation in combat"""
    print("=== COMBAT STRESS SIMULATION ===\n")
    
    scenarios = [
        {
            "name": "Basic Combat (Level 1, no equipment)",
            "level": 1,
            "equipment_mitigation": 0.0,
            "turns": 15,
            "combat": True,
            "low_hp_turn": 10,
        },
        {
            "name": "Mid-Level Combat (Level 5, Cloth Robes)",
            "level": 5,
            "equipment_mitigation": 0.30,
            "turns": 15,
            "combat": True,
            "low_hp_turn": 10,
        },
        {
            "name": "High-Level Combat (Level 10, Full Gear)",
            "level": 10,
            "equipment_mitigation": 0.45,  # Robes + Focus
            "turns": 15,
            "combat": True,
            "low_hp_turn": 10,
        },
    ]
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        stress = 0
        level = scenario['level']
        equip_mit = scenario['equipment_mitigation']
        level_reduction = 0.03 * (level - 1)
        total_mitigation = min(0.60, level_reduction + equip_mit)
        
        for turn in range(1, scenario['turns'] + 1):
            turn_stress = 0
            
            # Combat stress
            if scenario['combat']:
                raw = 2
                mitigated = int(raw * (1.0 - total_mitigation))
                turn_stress += mitigated
            
            # Low HP stress
            if turn >= scenario['low_hp_turn']:
                raw = 5
                mitigated = int(raw * (1.0 - total_mitigation))
                turn_stress += mitigated
            
            stress += turn_stress
            
            if turn % 5 == 0:
                print(f"  Turn {turn}: {stress} stress (+{turn_stress}/turn)")
        
        print(f"  Final stress: {stress}")
        
        # Determine tier
        if stress <= 30:
            tier = 1
        elif stress <= 60:
            tier = 2
        elif stress <= 85:
            tier = 3
        else:
            tier = 4
        print(f"  Stress tier: {tier} ({['Low', 'Medium', 'High', 'Critical'][tier-1]})")
        print()

def analyze_stress_recovery():
    """Analyze stress recovery options"""
    print("=== STRESS RECOVERY ===\n")
    
    recovery_options = [
        ("Level Up", -10, "Automatic on level up"),
        ("New Force Ability", -5, "Per ability gained"),
        ("Meditation (Force Ability)", -5, "Costs 1 Force Point"),
        ("Consumable: Calming Tea", -25, "Item use"),
        ("Consumable: Water Canteen", -15, "Item use"),
        ("Consumable: Jedi Focus", -40, "Item use"),
        ("Consumable: Emergency Ration", -10, "Item use"),
        ("Force Ability Use", -5, "Some abilities reduce stress"),
    ]
    
    print("Recovery Methods:")
    for method, amount, note in recovery_options:
        print(f"  {method}: {amount} stress ({note})")
    print()
    
    print("Example Recovery Sequence:")
    print("  Starting stress: 80 (Critical tier)")
    stress = 80
    print(f"  1. Use Jedi Meditation Focus: {stress} → {stress-40} stress")
    stress -= 40
    print(f"  2. Use Calming Tea: {stress} → {stress-25} stress")
    stress -= 25
    print(f"  3. Level up: {stress} → {stress-10} stress")
    stress -= 10
    print(f"  Final stress: {stress} (Tier 1 - recovered!)")
    print()

def calculate_turns_to_critical():
    """Calculate how many turns to reach critical stress"""
    print("=== TURNS TO CRITICAL STRESS (85+) ===\n")
    
    scenarios = [
        ("Level 1, no gear, combat only", 1, 0.0, 2),
        ("Level 1, no gear, combat + low HP", 1, 0.0, 7),
        ("Level 5, Cloth Robes, combat only", 5, 0.30, 2),
        ("Level 5, Cloth Robes, combat + low HP", 5, 0.30, 7),
        ("Level 10, Full gear, combat only", 10, 0.45, 2),
        ("Level 10, Full gear, combat + low HP", 10, 0.45, 7),
    ]
    
    for name, level, equip_mit, stress_per_turn in scenarios:
        level_reduction = 0.03 * (level - 1)
        total_mitigation = min(0.60, level_reduction + equip_mit)
        mitigated_stress = int(stress_per_turn * (1.0 - total_mitigation))
        
        if mitigated_stress == 0:
            turns = "N/A (no stress gain)"
        else:
            turns = 85 // mitigated_stress
        
        print(f"{name}:")
        print(f"  Mitigation: {total_mitigation*100:.0f}%")
        print(f"  Stress/turn: {mitigated_stress} (from {stress_per_turn})")
        print(f"  Turns to critical: {turns}")
        print()

if __name__ == "__main__":
    print("STRESS SYSTEM ANALYSIS\n")
    print("="*60 + "\n")
    
    analyze_stress_sources()
    print("="*60 + "\n")
    
    analyze_stress_mitigation()
    print("="*60 + "\n")
    
    analyze_stress_effects()
    print("="*60 + "\n")
    
    simulate_combat_stress()
    print("="*60 + "\n")
    
    analyze_stress_recovery()
    print("="*60 + "\n")
    
    calculate_turns_to_critical()
    
    print("="*60)
    print("Analysis complete!")
