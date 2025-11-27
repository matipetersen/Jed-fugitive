#!/usr/bin/env python3
"""
Simulate a complete gameplay scenario with narrative choices.
This shows how the system works from the player's perspective.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game import narrative_events

class SimulatedPlayer:
    """Simulated player for testing."""
    def __init__(self):
        self.corruption = 50
        self.name = "Test Jedi"

class SimulatedGame:
    """Simulated game state for testing."""
    def __init__(self):
        self.player = SimulatedPlayer()
        self.pending_narrative_choice = None
        self.turn_count = 100

def simulate_distress_signal_encounter(game):
    """Simulate encountering and resolving a distress signal."""
    print("=" * 70)
    print("TURN 150: You detect a distress signal...")
    print("=" * 70)
    
    # Trigger event
    signal = narrative_events.get_random_distress_signal()
    formatted, choice_mapping = narrative_events.format_distress_signal(signal)
    
    # Display to player
    print()
    for line in formatted:
        print(line)
    
    # Store pending choice (what game manager does)
    game.pending_narrative_choice = (signal, choice_mapping, 'distress')
    
    print("\n" + "-" * 70)
    print("(Player presses '2')")
    print("-" * 70)
    
    # Process player input
    choice_num = 2
    if choice_num in choice_mapping:
        choice_key = choice_mapping[choice_num]
        outcome, corruption, reward = narrative_events.process_narrative_choice(
            signal, choice_key, game.player
        )
        
        # Display outcome (what input handler does)
        print("\n" + "─" * 60)
        print(outcome)
        
        # Apply corruption
        old_corruption = game.player.corruption
        game.player.corruption = max(0, min(100, game.player.corruption + corruption))
        
        if corruption > 0:
            print(f"[Dark Side influence: +{corruption}]")
        elif corruption < 0:
            print(f"[Light Side influence: {corruption}]")
        
        # Show reward
        if reward:
            print(f"[Gained: {reward.replace('_', ' ').title()}]")
        
        print("─" * 60)
        print(f"\nCorruption: {old_corruption} → {game.player.corruption}")
        
        # Clear pending choice
        game.pending_narrative_choice = None
    
    print()

def simulate_environmental_discovery(game):
    """Simulate discovering an environmental event."""
    print("=" * 70)
    print("TURN 180: You discover something unusual...")
    print("=" * 70)
    
    # Trigger event
    event = narrative_events.get_environmental_event()
    formatted, choice_mapping = narrative_events.format_environmental_event(event)
    
    # Display to player
    print()
    for line in formatted:
        print(line)
    
    if choice_mapping:
        # Store pending choice
        game.pending_narrative_choice = (event, choice_mapping, 'environmental')
        
        print("\n" + "-" * 70)
        print("(Player presses '1')")
        print("-" * 70)
        
        # Process player input
        choice_num = 1
        if choice_num in choice_mapping:
            choice_key = choice_mapping[choice_num]
            outcome, corruption, reward = narrative_events.process_narrative_choice(
                event, choice_key, game.player
            )
            
            # Display outcome
            print("\n" + "─" * 60)
            if outcome:
                print(outcome)
            else:
                print("You make your choice.")
            
            # Apply corruption
            old_corruption = game.player.corruption
            game.player.corruption = max(0, min(100, game.player.corruption + corruption))
            
            if corruption > 0:
                print(f"[Dark Side influence: +{corruption}]")
            elif corruption < 0:
                print(f"[Light Side influence: {corruption}]")
            
            # Show reward
            if reward:
                print(f"[Gained: {reward.replace('_', ' ').title()}]")
            
            print("─" * 60)
            print(f"\nCorruption: {old_corruption} → {game.player.corruption}")
            
            # Clear pending choice
            game.pending_narrative_choice = None
    else:
        print("\n(No choices for this event)")
    
    print()

def demonstrate_choice_variation():
    """Show how same event appears differently."""
    print("=" * 70)
    print("DEMONSTRATION: Same event, different presentations")
    print("=" * 70)
    
    signal = narrative_events.DISTRESS_SIGNALS[0]
    
    for attempt in range(3):
        print(f"\n--- Presentation {attempt + 1} ---")
        formatted, choice_mapping = narrative_events.format_distress_signal(signal)
        
        # Show just the choices with their actual keys
        in_choices = False
        for line in formatted:
            if "What will you do?" in line:
                in_choices = True
                continue
            if in_choices and line.startswith(('1.', '2.', '3.')):
                num = int(line[0])
                key = choice_mapping[num]
                alignment = "LIGHT" if "light" in key else "DARK" if "dark" in key else "NEUTRAL"
                print(f"  {line} [{alignment}]")

def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  NARRATIVE CHOICE SYSTEM - GAMEPLAY SIMULATION".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    game = SimulatedGame()
    
    print(f"Starting corruption: {game.player.corruption}")
    print()
    
    # Simulate encounters
    simulate_distress_signal_encounter(game)
    simulate_environmental_discovery(game)
    
    # Show variation
    print()
    demonstrate_choice_variation()
    
    print("\n" + "=" * 70)
    print("✅ Gameplay simulation complete!")
    print(f"Final corruption: {game.player.corruption}")
    print("=" * 70)
    print("\nKEY IMPROVEMENTS:")
    print("  ✓ No alignment labels - player must judge actions themselves")
    print("  ✓ Random choice order - no positional bias")
    print("  ✓ Choices actually work - pressing 1/2/3 does something")
    print("  ✓ Clear feedback - outcomes, corruption changes, rewards shown")
    print("=" * 70)

if __name__ == '__main__':
    main()
