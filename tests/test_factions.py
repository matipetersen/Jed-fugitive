import pytest
from jedi_fugitive.game.factions import FactionManager

def test_faction_reputation_adjustment():
    fm = FactionManager()
    fm.adjust_reputation('Imperial', 30)
    assert fm.get_reputation('Imperial') == 30
    fm.adjust_reputation('Imperial', -50)
    assert fm.get_reputation('Imperial') == -20
    fm.adjust_reputation('Imperial', -100)
    assert fm.get_reputation('Imperial') == -100  # Clamped
    fm.adjust_reputation('Imperial', 300)
    assert fm.get_reputation('Imperial') == 100   # Clamped

def test_faction_init():
    fm = FactionManager()
    assert 'Imperial' in fm.factions
    assert fm.player_reputation['Rebel'] == 0
