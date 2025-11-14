#!/usr/bin/env python3
"""
Test the death screen with mock data to verify it displays correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.player import Player

# Create a minimal dummy stdscr
class DummyStdScr:
    def __init__(self, h=24, w=80):
        self._h = h
        self._w = w
    def getmaxyx(self):
        return (self._h, self._w)
    def subwin(self, h, w, y, x):
        return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *args, **kwargs): pass
    def addnstr(self, *args, **kwargs): pass
    def refresh(self): pass
    def noutrefresh(self): pass

# Create game manager
dummy = DummyStdScr()
gm = GameManager(dummy)

# Set up mock death data
gm.death = True
gm.death_cause = 'Sith Inquisitor'
gm.death_biome = 'Sith Tomb'
gm.death_pos = (15, 23)
gm.turns = 127
gm.term_w = 80

# Create a mock player with stats
gm.player = Player(x=15, y=23)
gm.player.level = 3
gm.player.kills_count = 12
gm.player.artifacts_consumed = 2
gm.player.dark_corruption = 45
gm.player.gold_collected = 150  # Test with some gold
gm.player.travel_log = [
    {'text': 'Descended deeper into the tomb', 'turn': 120},
    {'text': 'Defeated Sith Trooper in battle', 'turn': 122},
    {'text': 'Found Vibroblade (+5 attack)', 'turn': 123},
    {'text': 'Learned Sith lore: The Rule of Two', 'turn': 125},
    {'text': 'Faced Sith Inquisitor - a deadly opponent', 'turn': 127},
]

print("\n" + "="*80)
print("TESTING DEATH SCREEN WITH GOLD")
print("="*80 + "\n")

# Call the death screen function
gm.show_death_stats()
