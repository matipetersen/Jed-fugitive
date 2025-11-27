#!/usr/bin/env python3
"""
Integration test - verify narrative choices work in-game.
Creates a test scenario and simulates player making choices.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game import narrative_events

def demo_distress_signal():
    """Demo a distress signal with randomized choices."""
    print("=" * 60)
    print("DISTRESS SIGNAL DEMO")
    print("=" * 60)
    
    signal = narrative_events.get_random_distress_signal()
    formatted, choice_mapping = narrative_events.format_distress_signal(signal)
    
    # Display to player
    for line in formatted:
        print(line)
    
    print("\n" + "=" * 60)
    print("CHOICE MAPPING (internal):")
    for num, choice_key in sorted(choice_mapping.items()):
        print(f"  {num} -> {choice_key}")
    
    # Simulate player choosing option 2
    print("\n" + "=" * 60)
    print("PLAYER CHOOSES OPTION 2")
    print("=" * 60)
    
    class MockPlayer:
        def __init__(self):
            self.corruption = 50
    
    player = MockPlayer()
    choice_key = choice_mapping[2]
    outcome, corruption, reward = narrative_events.process_narrative_choice(
        signal, choice_key, player
    )
    
    print("\nOutcome:")
    print(outcome)
    print(f"\nCorruption change: {corruption:+d}")
    print(f"Reward: {reward}")
    print(f"New corruption: {player.corruption + corruption}")

def demo_environmental_event():
    """Demo an environmental event with randomized choices."""
    print("\n\n" + "=" * 60)
    print("ENVIRONMENTAL EVENT DEMO")
    print("=" * 60)
    
    event = narrative_events.get_environmental_event()
    formatted, choice_mapping = narrative_events.format_environmental_event(event)
    
    # Display to player
    for line in formatted:
        print(line)
    
    if choice_mapping:
        print("\n" + "=" * 60)
        print("CHOICE MAPPING (internal):")
        for num, choice_key in sorted(choice_mapping.items()):
            print(f"  {num} -> {choice_key}")
        
        # Simulate player choosing option 1
        print("\n" + "=" * 60)
        print("PLAYER CHOOSES OPTION 1")
        print("=" * 60)
        
        class MockPlayer:
            def __init__(self):
                self.corruption = 50
        
        player = MockPlayer()
        choice_key = choice_mapping[1]
        outcome, corruption, reward = narrative_events.process_narrative_choice(
            event, choice_key, player
        )
        
        print("\nOutcome:")
        print(outcome if outcome else "(None - text choice only)")
        print(f"\nCorruption change: {corruption:+d}")
        print(f"Reward: {reward}")
    else:
        print("\n(This event has no choices)")

def demo_multiple_randomizations():
    """Show that same event displays in different orders."""
    print("\n\n" + "=" * 60)
    print("RANDOMIZATION DEMO - Same event, 3 different displays")
    print("=" * 60)
    
    signal = narrative_events.DISTRESS_SIGNALS[0]
    
    for i in range(3):
        print(f"\n--- Attempt {i+1} ---")
        formatted, choice_mapping = narrative_events.format_distress_signal(signal)
        
        # Show just the choices
        for line in formatted:
            if line.startswith(('1.', '2.', '3.')):
                choice_num = int(line[0])
                choice_key = choice_mapping[choice_num]
                print(f"{line}  [{choice_key}]")

if __name__ == '__main__':
    demo_distress_signal()
    demo_environmental_event()
    demo_multiple_randomizations()
    
    print("\n\n" + "=" * 60)
    print("✅ Integration demo complete!")
    print("=" * 60)
