#!/usr/bin/env python3
"""Test script to demonstrate alignment-based narrative in the travel log."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.player import Player

def test_narrative_system():
    """Demonstrate how narrative changes based on player alignment."""
    
    print("=== ALIGNMENT-BASED NARRATIVE SYSTEM TEST ===\n")
    
    # Create a player
    player = Player(0, 0)
    
    # Scenario 1: Light Side Player (low corruption)
    print("1. LIGHT SIDE JEDI (Corruption: 0%)")
    print("-" * 50)
    player.dark_corruption = 0
    
    combat = player.narrative_text(
        light_version="Defended myself against the enemy, seeking only to survive.",
        dark_version="Obliterated the enemy without mercy or hesitation.",
        balanced_version="Slew the enemy in battle."
    )
    print(f"Combat: {combat}")
    
    artifact = player.narrative_text(
        light_version="Cleansed the artifact, its corruption dissolved by the Force.",
        dark_version="Destroyed the artifact, though it felt like wasted power.",
        balanced_version="Destroyed the artifact, resisting the darkness."
    )
    print(f"Artifact: {artifact}")
    
    ability = player.narrative_text(
        light_version="Achieved harmony with the Force, gaining insight into Force Heal.",
        dark_version="Learned Force Heal, though it feels weak compared to dark powers.",
        balanced_version="Gained light power: Force Heal"
    )
    print(f"Ability: {ability}\n")
    
    # Scenario 2: Balanced Player (moderate corruption)
    print("2. BALANCED FORCE USER (Corruption: 45%)")
    print("-" * 50)
    player.dark_corruption = 45
    
    combat = player.narrative_text(
        light_version="Defended myself against the enemy, seeking only to survive.",
        dark_version="Obliterated the enemy without mercy or hesitation.",
        balanced_version="Slew the enemy in battle."
    )
    print(f"Combat: {combat}")
    
    artifact = player.narrative_text(
        light_version="Absorbed the artifact with reluctance, feeling its dark power seep in.",
        dark_version="Devoured the essence of the artifact, reveling in its dark power!",
        balanced_version="Absorbed the artifact, embracing the dark side."
    )
    print(f"Artifact: {artifact}")
    
    stairs = player.narrative_text(
        light_version="Descended deeper, seeking to understand this dark place.",
        dark_version="Plunged deeper into darkness, hungry for more power.",
        balanced_version="Descended to the next level."
    )
    print(f"Stairs: {stairs}\n")
    
    # Scenario 3: Dark Side Player (high corruption)
    print("3. DARK SIDE SITH (Corruption: 85%)")
    print("-" * 50)
    player.dark_corruption = 85
    
    combat = player.narrative_text(
        light_version="Defeated the fearsome enemy, bringing justice to the galaxy.",
        dark_version="Crushed the enemy utterly, proving your superior power!",
        balanced_version="Defeated the fearsome enemy in mortal combat!"
    )
    print(f"Combat: {combat}")
    
    artifact = player.narrative_text(
        light_version="Absorbed the artifact with reluctance, feeling its dark power seep in.",
        dark_version="Devoured the essence of the artifact, reveling in its dark power!",
        balanced_version="Absorbed the artifact, embracing the dark side."
    )
    print(f"Artifact: {artifact}")
    
    ability = player.narrative_text(
        light_version="Reluctantly learned Force Lightning, fearing its corrupting influence.",
        dark_version="Mastered Force Lightning, feeling the intoxicating power of the dark side!",
        balanced_version="Gained dark power: Force Lightning"
    )
    print(f"Ability: {ability}")
    
    tomb = player.narrative_text(
        light_version="Entered the Sith tomb with caution, feeling the weight of its evil.",
        dark_version="Stormed into the Sith tomb, eager to claim its forbidden secrets!",
        balanced_version="Entered a Sith tomb, the darkness palpable."
    )
    print(f"Tomb: {tomb}\n")
    
    # Show the alignment detection
    print("=== ALIGNMENT DETECTION ===")
    print("-" * 50)
    for corruption in [0, 20, 30, 45, 60, 75, 100]:
        player.dark_corruption = corruption
        alignment = player.get_alignment()
        color = {
            'light': '🔵 Light Side',
            'balanced': '⚪ Balanced',
            'dark': '🔴 Dark Side'
        }[alignment]
        print(f"Corruption {corruption:3d}% -> {color}")

if __name__ == "__main__":
    test_narrative_system()
