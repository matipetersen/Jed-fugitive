#!/usr/bin/env python3
"""
Demonstration of the enhanced AI system with diverse enemies and coordinated tactics.

This script showcases:
1. Diverse enemy types with unique behaviors
2. Coordinated charging when 3+ enemies are present
3. Gun targeting system using the unified targeting interface
4. Tactical variety in combat scenarios
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from jedi_fugitive.game.diverse_enemies import (
    create_sith_sniper,
    create_sith_brawler,
    create_sith_assassin,
    create_sith_trooper,
    create_sith_scout,
    create_sith_guardian,
    create_dark_acolyte,
    create_mixed_group
)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def demo_enemy_showcase():
    """Show off all the diverse enemy types."""
    print_header("DIVERSE ENEMY TYPES")
    
    enemies = [
        create_sith_sniper(5),
        create_sith_brawler(5),
        create_sith_assassin(5),
        create_sith_trooper(5),
        create_sith_scout(5),
        create_sith_guardian(5),
        create_dark_acolyte(5)
    ]
    
    print("The galaxy is filled with various Sith forces, each with unique")
    print("combat styles and tactical approaches:\n")
    
    for enemy in enemies:
        print(f"┌─ {enemy.name} ({enemy.symbol}) ─────────────")
        print(f"│  {enemy.description}")
        print(f"│  HP: {enemy.hp}  ATK: {enemy.attack}  DEF: {enemy.defense}  EVA: {enemy.evasion}%")
        print(f"│  Behavior: {getattr(enemy, 'enemy_behavior', 'standard')}")
        print(f"└─────────────────────────────────────────\n")


def demo_tactical_scenarios():
    """Demonstrate different combat scenarios."""
    print_header("TACTICAL COMBAT SCENARIOS")
    
    print("SCENARIO 1: THE AMBUSH (3+ Enemies = Coordinated Charge)")
    print("-" * 60)
    print("You enter a chamber and encounter:")
    group1 = create_mixed_group(4, level=5)
    for i, enemy in enumerate(group1, 1):
        behavior = getattr(enemy, 'enemy_behavior', 'standard')
        print(f"  {i}. {enemy.name} [{behavior.upper()}]")
    print("\nWith 3+ enemies present, they coordinate a UNIFIED ASSAULT!")
    print("Even the sniper abandons his position to join the charge!")
    print("Tactical diversity gives way to overwhelming numbers.\n")
    
    print("\nSCENARIO 2: THE DUEL (1-2 Enemies = Individual Tactics)")
    print("-" * 60)
    print("You face a single opponent:")
    sniper = create_sith_sniper(6)
    print(f"  {sniper.name} [{getattr(sniper, 'enemy_behavior', 'standard').upper()}]")
    print("\nThe sniper maintains distance, retreating when you approach.")
    print("Each shot is calculated. No reckless charges here.\n")
    
    print("\nSCENARIO 3: MIXED TACTICS (Various Enemy Behaviors)")
    print("-" * 60)
    print("A diverse squad with complementary roles:")
    print("  • SNIPER: Stays back, forces you to close distance")
    print("  • BRAWLER: Charges directly, soaks damage")
    print("  • FLANKER: Circles around, attacks from sides")
    print("  • RANGED: Maintains optimal distance for sustained fire")
    print("  • GUARDIAN: Tanks hits while others deal damage")
    print("\nEach enemy plays their role until numbers trigger coordinated charge!")


def demo_gun_targeting():
    """Explain the gun targeting system."""
    print_header("GUN TARGETING SYSTEM")
    
    print("The targeting system now works for ALL ranged attacks:")
    print()
    print("  FORCE ABILITIES (f):")
    print("    • Press 'f' to enter Force targeting mode")
    print("    • Range depends on ability")
    print("    • Select target with arrow keys, confirm with Enter")
    print()
    print("  GRENADES (t):")
    print("    • Press 't' to throw thermal detonator")
    print("    • Fixed 3-tile range")
    print("    • Area of effect damage on impact")
    print()
    print("  GUNS (F):")
    print("    • Press 'F' to enter gun targeting mode")
    print("    • Range depends on equipped weapon")
    print("    • Accuracy vs enemy evasion determines hit")
    print("    • Damage reduced by enemy defense")
    print()
    print("All three systems use the SAME intuitive targeting interface!")
    print("Move reticle with arrow keys, confirm with Enter, cancel with Esc.")


def demo_ai_intelligence():
    """Explain the AI decision-making."""
    print_header("ENEMY AI INTELLIGENCE")
    
    print("Enemy behavior adapts dynamically based on combat conditions:")
    print()
    print("INDIVIDUAL TACTICS (< 3 enemies nearby):")
    print("  • SNIPER: Maintains 5+ tile distance, retreats if approached")
    print("  • AGGRESSIVE: Always charges directly, ignores tactics")
    print("  • FLANKER: Uses ai_find_flanking_position() for perpendicular attacks")
    print("  • RANGED: Uses ai_maintain_range() to stay at preferred distance")
    print("  • STANDARD: Balanced approach, adapts to situation")
    print()
    print("COORDINATED ASSAULT (3+ enemies within 8 tiles):")
    print("  • ALL enemies charge directly at player")
    print("  • Overwhelming numbers override individual tactics")
    print("  • Message: 'The enemies coordinate a unified assault!'")
    print("  • Exception: Enemies with < 25% HP still retreat")
    print()
    print("SURVIVAL INSTINCT:")
    print("  • Enemies below 30% HP retreat regardless of tactics")
    print("  • Bosses never retreat")
    print("  • ai_should_retreat() overrides other behaviors")


def demo_gameplay_tips():
    """Provide strategic tips for players."""
    print_header("STRATEGIC GAMEPLAY TIPS")
    
    print("DEALING WITH DIVERSE ENEMIES:")
    print()
    print("  vs SNIPERS:")
    print("    • Close distance quickly using Force powers")
    print("    • Use cover to approach safely")
    print("    • High evasion enemies - use accurate weapons")
    print()
    print("  vs BRAWLERS:")
    print("    • Keep distance, use ranged attacks")
    print("    • Throw grenades before they close in")
    print("    • High HP - prepare for prolonged fight")
    print()
    print("  vs FLANKERS:")
    print("    • Watch your sides and back")
    print("    • Use Force Push to create space")
    print("    • Very high evasion - patience is key")
    print()
    print("  vs COORDINATED CHARGES (3+ enemies):")
    print("    • Thin their numbers quickly with grenades")
    print("    • Focus fire to drop below 3 enemies")
    print("    • Once < 3 remain, tactics return")
    print("    • Use Force abilities for crowd control")


def main():
    """Run the complete demonstration."""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  JEDI FUGITIVE: ENHANCED AI & COMBAT DEMONSTRATION  ".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    demo_enemy_showcase()
    input("\n[Press Enter to continue...]")
    
    demo_tactical_scenarios()
    input("\n[Press Enter to continue...]")
    
    demo_gun_targeting()
    input("\n[Press Enter to continue...]")
    
    demo_ai_intelligence()
    input("\n[Press Enter to continue...]")
    
    demo_gameplay_tips()
    
    print_header("SUMMARY")
    print("✓ 7 diverse enemy types with unique stats and behaviors")
    print("✓ 5 AI behavior patterns (sniper, aggressive, flanker, ranged, standard)")
    print("✓ Coordinated charging when 3+ enemies present")
    print("✓ Unified targeting system for Force, grenades, and guns")
    print("✓ Dynamic tactics that adapt to combat conditions")
    print("✓ Survival instincts (retreat at low HP)")
    print()
    print("The galaxy has never been more dangerous... or tactical!")
    print("\n" + "█" * 60 + "\n")


if __name__ == "__main__":
    main()
