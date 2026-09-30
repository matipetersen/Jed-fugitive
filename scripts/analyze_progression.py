#!/usr/bin/env python3
"""
Level Progression Analysis and Rebalancing Tool
Analyzes current system and proposes improvements.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def analyze_current_system():
    """Analyze the current level progression system."""
    print("═" * 80)
    print("CURRENT LEVEL PROGRESSION SYSTEM ANALYSIS")
    print("═" * 80)
    
    print("\n" + "─" * 80)
    print("XP REQUIREMENTS")
    print("─" * 80)
    
    # Calculate XP curve: base 100, grows ~1.25^level
    levels_data = []
    total_xp = 0
    for level in range(1, 21):
        xp_needed = int(100 * (1.25 ** (level - 1)))
        total_xp += xp_needed
        levels_data.append((level, xp_needed, total_xp))
    
    print(f"{'Level':<8} {'XP Needed':<12} {'Total XP':<12} {'Notes'}")
    print("-" * 80)
    for level, xp_needed, total in levels_data[:15]:
        note = ""
        if level == 1:
            note = "Starting level"
        elif level == 5:
            note = "Mid-game"
        elif level == 10:
            note = "Late-game"
        elif level == 15:
            note = "Endgame"
        print(f"{level:<8} {xp_needed:<12} {total:<12} {note}")
    
    print("\n" + "─" * 80)
    print("STAT GAINS PER LEVEL")
    print("─" * 80)
    
    stat_gains = {
        "Max HP": "+5 per level (automatic)",
        "Attack": "+1 per level (automatic)",
        "Defense": "+1 per level (automatic)",
        "Evasion": "+1 per level (automatic)",
        "Force Points": "+1 per level (automatic)",
        "Stress Reduction": "-30 stress per level",
    }
    
    for stat, gain in stat_gains.items():
        print(f"  {stat:<20} {gain}")
    
    print("\n" + "─" * 80)
    print("LEVEL-UP CHOICES")
    print("─" * 80)
    
    choices = [
        "+5 Max HP",
        "+1 Attack",
        "+1 Evasion",
        "+2 Force Points",
        "Melee Mastery (+2 dmg with melee)",
        "Ranged Mastery (+2 dmg with ranged)",
        "Shield Mastery (+2 def with shields)",
        "Dual Wield Mastery (+1 dmg per weapon)",
        "Learn Force Ability",
    ]
    
    print("\nPlayer chooses ONE reward per level:")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    print("\n" + "─" * 80)
    print("CURRENT ISSUES")
    print("─" * 80)
    
    issues = [
        "• Too many automatic stat gains make choices less impactful",
        "• No fighting stance/form system (missed Star Wars lore opportunity)",
        "• Masteries are flat bonuses with no progression",
        "• Force abilities not tied to character development arc",
        "• No sense of specialization or build diversity",
        "• Stats scale linearly - becomes predictable",
        "• No milestone abilities or signature techniques",
    ]
    
    for issue in issues:
        print(f"  {issue}")


def propose_new_system():
    """Propose improved progression system."""
    print("\n\n" + "═" * 80)
    print("PROPOSED NEW PROGRESSION SYSTEM")
    print("═" * 80)
    
    print("\n" + "─" * 80)
    print("CORE PRINCIPLES")
    print("─" * 80)
    
    principles = [
        "1. CHOICES MATTER: Fewer automatic gains, more meaningful choices",
        "2. SPECIALIZATION: Forms and masteries create unique builds",
        "3. STAR WARS LORE: Canonical lightsaber forms are central",
        "4. PROGRESSION ARCS: Light/Dark path affects available options",
        "5. MILESTONE REWARDS: Special unlocks at key levels (5, 10, 15)",
    ]
    
    for principle in principles:
        print(f"  {principle}")
    
    print("\n" + "─" * 80)
    print("NEW LEVEL-UP STRUCTURE")
    print("─" * 80)
    
    print("\nAUTOMATIC GAINS (Reduced):")
    print("  • Max HP: +3 per level (was +5)")
    print("  • Attack: +1 per level")
    print("  • Defense: +1 per level") 
    print("  • Force Points: +1 every 2 levels (was every level)")
    print("  • Stress: -20 per level (was -30)")
    
    print("\nLEVEL-UP CHOICE (Pick ONE):")
    print("  1. +10 Max HP (significant health boost)")
    print("  2. +2 Attack (offensive focus)")
    print("  3. +2 Defense (defensive focus)")
    print("  4. +3 Evasion (mobility focus)")
    print("  5. +3 Force Points (Force user focus)")
    print("  6. Learn Lightsaber Form (combat style)")
    print("  7. Improve Mastery (weapon specialization)")
    print("  8. Learn Force Ability (new power)")
    
    print("\n" + "─" * 80)
    print("LIGHTSABER FORMS SYSTEM")
    print("─" * 80)
    
    print("\nForm I: Shii-Cho (Level 1 - Starting Form)")
    print("  • Foundation form all Jedi learn")
    print("  • +1 Attack, +1 Defense")
    print("  • Wide sweeping strikes")
    
    print("\nForm II: Makashi (Level 3+)")
    print("  • Elegant dueling form")
    print("  • +3 Attack, +1 Defense, +10% Crit")
    print("  • Bonus vs single opponents")
    
    print("\nForm III: Soresu (Level 4+)")
    print("  • Ultimate defense (Obi-Wan)")
    print("  • +4 Defense, +3 Evasion, -1 Attack")
    print("  • Deflects blaster fire")
    
    print("\nForm IV: Ataru (Level 5+)")
    print("  • Acrobatic aggression (Ataru Form)")
    print("  • +3 Attack, +4 Evasion, -10% Force cost")
    print("  • Multiple rapid strikes")
    
    print("\nForm V: Shien/Djem So (Level 6+)")
    print("  • Power attacks (Djem So Form)")
    print("  • +4 Attack, +2 Defense, +5% Crit")
    print("  • Counter-attacks after blocks")
    
    print("\nForm VI: Niman (Level 7+)")
    print("  • Force integration")
    print("  • +2 Attack, +2 Defense, +1 Evasion, -20% Force cost")
    print("  • Mix Force powers with combat")
    
    print("\nForm VII: Juyo/Vaapad (Level 10+)")
    print("  • Ferocious unpredictability (Mace Windu)")
    print("  • +5 Attack, +2 Evasion, +15% Crit")
    print("  • Feeds on dark side energy")
    print("  • RISK: Can lead to dark side corruption")
    
    print("\nJar'Kai (Level 5+, requires Shii-Cho + Ataru)")
    print("  • Dual-wielding mastery (Ahsoka)")
    print("  • +2 Attack, +1 Defense, +2 Evasion (when dual-wielding)")
    print("  • Extra attack per turn")
    
    print("\nSaberstaff Mastery (Level 6+, requires Shii-Cho + Ataru)")
    print("  • Double-bladed technique (Juyo/Vaapad Form)")
    print("  • +3 Attack, +2 Defense, +1 Evasion (with saberstaff)")
    print("  • Spinning attacks hit multiple enemies")
    
    print("\n" + "─" * 80)
    print("MASTERY SYSTEM (REWORKED)")
    print("─" * 80)
    
    print("\nEach mastery has 3 ranks:")
    
    print("\nMelee Mastery:")
    print("  Rank 1 (Level 2+): +1 damage with melee weapons")
    print("  Rank 2 (Level 6+): +2 damage, ignore 2 enemy defense")
    print("  Rank 3 (Level 12+): +3 damage, 10% lifesteal on melee hits")
    
    print("\nRanged Mastery:")
    print("  Rank 1 (Level 2+): +1 damage with ranged weapons")
    print("  Rank 2 (Level 6+): +2 damage, +1 range")
    print("  Rank 3 (Level 12+): +3 damage, ignore cover penalties")
    
    print("\nShield Mastery:")
    print("  Rank 1 (Level 3+): +2 defense with shields")
    print("  Rank 2 (Level 7+): +3 defense, block melee attacks")
    print("  Rank 3 (Level 13+): +4 defense, reflect projectiles")
    
    print("\nForce Mastery:")
    print("  Rank 1 (Level 3+): -10% Force ability costs")
    print("  Rank 2 (Level 8+): -20% costs, Force regen +1/turn")
    print("  Rank 3 (Level 14+): -30% costs, can use 2 abilities/turn")
    
    print("\n" + "─" * 80)
    print("MILESTONE REWARDS")
    print("─" * 80)
    
    milestones = [
        ("Level 5", "Choose specialization path", "Unlock advanced forms OR master ability"),
        ("Level 10", "Signature technique", "Create custom ability based on your path"),
        ("Level 15", "Master achievement", "Gain title and unique ultimate ability"),
        ("Level 20", "Legendary status", "Transcend normal Force limits"),
    ]
    
    print()
    for level, name, reward in milestones:
        print(f"{level:<12} {name:<25} {reward}")


def compare_builds():
    """Show example character builds."""
    print("\n\n" + "═" * 80)
    print("EXAMPLE CHARACTER BUILDS")
    print("═" * 80)
    
    builds = [
        {
            "name": "Jedi Guardian (Tank)",
            "form": "Form III: Soresu",
            "masteries": ["Shield Mastery Rank 3", "Melee Mastery Rank 2"],
            "stats": "High HP, High Defense, Moderate Attack",
            "abilities": ["Force Protect", "Force Heal", "Force Push"],
            "playstyle": "Defensive wall, outlasts enemies, protects allies"
        },
        {
            "name": "Jedi Sentinel (Balanced)",
            "form": "Form VI: Niman",
            "masteries": ["Force Mastery Rank 3", "Melee Mastery Rank 2"],
            "stats": "Balanced, High Force Points",
            "abilities": ["Force Speed", "Force Stun", "Force Sight"],
            "playstyle": "Mix combat and Force powers, adaptable to any situation"
        },
        {
            "name": "Sith Marauder (DPS)",
            "form": "Form VII: Juyo/Vaapad",
            "masteries": ["Melee Mastery Rank 3", "Dual Wield"],
            "stats": "High Attack, High Crit, Moderate HP",
            "abilities": ["Force Rage", "Force Lightning", "Force Choke"],
            "playstyle": "Relentless aggression, high damage, risks corruption"
        },
        {
            "name": "Jedi Consular (Force Focus)",
            "form": "Form VI: Niman",
            "masteries": ["Force Mastery Rank 3", "Ranged Mastery Rank 2"],
            "stats": "Moderate HP, High Force Points, High Evasion",
            "abilities": ["Force Storm", "Force Meditation", "Force Heal"],
            "playstyle": "Pure Force user, minimal lightsaber combat"
        },
        {
            "name": "Shadow Jedi (Stealth)",
            "form": "Form IV: Ataru",
            "masteries": ["Dual Wield", "Melee Mastery Rank 2"],
            "stats": "High Evasion, High Attack, Moderate HP",
            "abilities": ["Force Phantom", "Force Speed", "Force Blink"],
            "playstyle": "Mobile striker, in and out, never gets hit"
        },
    ]
    
    for i, build in enumerate(builds, 1):
        print(f"\n{i}. {build['name'].upper()}")
        print(f"   Form: {build['form']}")
        print(f"   Masteries: {', '.join(build['masteries'])}")
        print(f"   Stats: {build['stats']}")
        print(f"   Abilities: {', '.join(build['abilities'])}")
        print(f"   Playstyle: {build['playstyle']}")


def main():
    analyze_current_system()
    propose_new_system()
    compare_builds()
    
    print("\n\n" + "═" * 80)
    print("IMPLEMENTATION RECOMMENDATIONS")
    print("═" * 80)
    
    recommendations = [
        "1. Implement lightsaber_forms.py as new combat stance system",
        "2. Reduce automatic stat gains on level up",
        "3. Add form selection to level-up menu",
        "4. Implement ranked mastery system (3 ranks each)",
        "5. Add milestone rewards at levels 5, 10, 15, 20",
        "6. Integrate form bonuses into combat calculations",
        "7. Add stance-switching command (e.g., 'X' key)",
        "8. Create visual indicators for active form",
        "9. Add form descriptions to help screen",
        "10. Balance Force ability costs with form reductions",
    ]
    
    print()
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n" + "═" * 80)
    print("✅ Analysis complete! Ready to implement improvements.")
    print("═" * 80)
    print()

if __name__ == '__main__':
    main()
