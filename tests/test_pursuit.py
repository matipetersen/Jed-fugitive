import pytest
from jedi_fugitive.game.pursuit import PursuitSystem

class DummyPlayer:
    def __init__(self):
        self.turn_count = 0


def test_detection_increases_on_force_and_combat():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.update_detection('force')
    assert ps.detection_level == 20
    ps.update_detection('combat')
    assert ps.detection_level == 30

def test_detection_decreases_on_stealth_and_disguise():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 50
    ps.update_detection('stealth')
    assert ps.detection_level == 40
    ps.update_detection('combat', disguise_bonus=10)
    assert ps.detection_level == 40  # 10 up, 10 down

def test_predator_spawns_at_threshold():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 70
    assert ps.check_predator_spawn() is True
    assert ps.sith_predator_active is True
    assert ps.check_predator_spawn() is False

def test_detection_decay():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 5
    ps.decay_detection()
    assert ps.detection_level == 4
