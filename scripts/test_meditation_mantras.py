#!/usr/bin/env python3
"""
Test meditation mantras at different corruption levels.
Demonstrates how mantras change from Jedi Code to Sith Code as player becomes corrupted.
"""
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

from jedi_fugitive.game.game_manager import GameManager

class DummyStdScr:
    def __init__(self, h=24, w=80):
        self._h = h
        self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self):
        pass
    def erase(self):
        pass
    def border(self):
        pass
    def addstr(self, *args, **kwargs):
        pass
    def addnstr(self, *args, **kwargs):
        pass
    def refresh(self):
        pass
    def noutrefresh(self):
        pass
    def resize(self, h, w):
        self._h = h
        self._w = w
    def getch(self):
        return -1

def test_meditation_mantras():
    """Test meditation mantras at different corruption levels"""
    print("Testing Meditation Mantras by Alignment")
    print("=" * 70)
    
    corruption_levels = [
        (0, "Pure Light Side (Jedi)"),
        (10, "Strong Light Side"),
        (30, "Light-leaning"),
        (50, "Balanced (Gray Jedi)"),
        (65, "Dark-leaning"),
        (85, "Strong Dark Side"),
        (100, "Pure Dark Side (Sith)")
    ]
    
    for corruption, description in corruption_levels:
        print(f"\n{description} (Corruption: {corruption})")
        print("-" * 70)
        
        # Create game manager
        dummy_screen = DummyStdScr(h=40, w=120)
        gm = GameManager(dummy_screen)
        gm.initialize()
        
        # Set player corruption level
        gm.player.dark_corruption = corruption
        
        # Clear player position and remove enemies for safe meditation
        gm.player.x = 10
        gm.player.y = 10
        gm.enemies = []
        
        # Capture mantras from 3 meditation sessions
        mantras = []
        for i in range(3):
            # Clear messages
            if hasattr(gm.ui, 'messages'):
                gm.ui.messages.messages = []
            
            # Meditate
            gm.meditate()
            
            # Extract mantra from messages
            if hasattr(gm.ui, 'messages') and gm.ui.messages.messages:
                for msg in gm.ui.messages.messages:
                    # Messages can be dicts or strings
                    msg_text = msg.get('text', '') if isinstance(msg, dict) else str(msg)
                    if msg_text.startswith('"') and msg_text.endswith('"'):
                        mantras.append(msg_text)
                        break
        
        # Display the mantras
        for i, mantra in enumerate(mantras, 1):
            print(f"  Mantra {i}: {mantra}")
    
    print("\n" + "=" * 70)
    print("✓ Meditation mantra test complete!")
    print("\nNote: Mantras change dynamically based on player's alignment:")
    print("  - Pure Light (0-20): Jedi Code and light side philosophy")
    print("  - Light-leaning (21-40): Jedi teachings with pragmatism")
    print("  - Balanced (41-59): Gray Jedi, embracing both sides")
    print("  - Dark-leaning (60-79): Passion and power-focused")
    print("  - Pure Dark (80-100): Sith Code and dark side philosophy")

if __name__ == "__main__":
    try:
        test_meditation_mantras()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
