import pytest
from jedi_fugitive.game.factions import FactionManager

def test_faction_reputation_adjustment():
    fm = FactionManager()
    fm.player_reputation['Sith Empire'] = 0
    fm.adjust_reputation('Sith Empire', 30)
    assert fm.get_reputation('Sith Empire') == 30
    fm.adjust_reputation('Sith Empire', -50)
    assert fm.get_reputation('Sith Empire') == -20
    fm.adjust_reputation('Sith Empire', -100)
    assert fm.get_reputation('Sith Empire') == -100  # Clamped
    fm.adjust_reputation('Sith Empire', 300)
    assert fm.get_reputation('Sith Empire') == 100   # Clamped

def test_faction_init():
    fm = FactionManager()
    assert 'Sith Empire' in fm.factions
    assert 'Republic' in fm.player_reputation
