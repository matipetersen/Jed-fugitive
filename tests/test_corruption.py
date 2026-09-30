import pytest
from jedi_fugitive.game.corruption import CorruptionSystem

class DummyAbility:
    def __init__(self, name, alignment, base_cost=10):
        self.name = name
        self.alignment = alignment
        self.base_cost = base_cost
        self.unlocked = True

class DummyPlayer:
    def __init__(self):
        self.dark_corruption = 0
        self.force_abilities = {
            'light': DummyAbility('Heal', 'light'),
            'dark': DummyAbility('Lightning', 'dark')
        }


def test_corruption_increases_and_thresholds():
    p = DummyPlayer()
    cs = CorruptionSystem(p)
    cs.adjust_corruption(25)
    assert p.dark_corruption == 25
    cs.adjust_corruption(30)
    assert p.dark_corruption == 55
    cs.adjust_corruption(30)
    assert p.dark_corruption == 85


def test_light_side_locked_at_high_corruption():
    p = DummyPlayer()
    cs = CorruptionSystem(p)
    cs.adjust_corruption(85)
    assert p.force_abilities['light'].unlocked is False
    assert p.force_abilities['dark'].base_cost == 5  # Strengthened
