import pytest
from jedi_fugitive.game.pursuit import PursuitSystem
from jedi_fugitive.game.level import Display

class DummyPlayer:
    def __init__(self):
        self.turn_count = 0
        self.x = self.y = 5


class _Msgs:
    def add(self, *a, **k):
        pass


class _UI:
    messages = _Msgs()


class DummyGame:
    def __init__(self):
        self.player = DummyPlayer()
        self.game_map = [[Display.FLOOR] * 60 for _ in range(60)]
        self.player.x = self.player.y = 30
        self.enemies = []
        self.ui = _UI()


def test_detection_increases_on_force_and_combat():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.update_detection('force')
    assert ps.detection_level == 20
    ps.update_detection('combat')
    # a melee swing is +3 Heat (it was +10: ten swings summoned the Predator)
    assert ps.detection_level == 23

def test_detection_decreases_on_stealth_and_disguise():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 50
    ps.update_detection('stealth')
    assert ps.detection_level == 40
    ps.update_detection('combat', disguise_bonus=10)
    assert ps.detection_level == 33  # 3 up, 10 down

def test_predator_spawns_at_threshold():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 100
    game = DummyGame()
    assert ps.check_predator_spawn(game) is True
    assert ps.sith_predator_active is True
    pred = game.enemies[-1]
    # dispatched out of sight, never on top of the player
    assert abs(pred.x - game.player.x) + abs(pred.y - game.player.y) >= 12
    assert ps.check_predator_spawn(game) is False

def test_detection_decay():
    p = DummyPlayer()
    ps = PursuitSystem(p)
    ps.detection_level = 5
    ps.decay_detection()
    assert ps.detection_level == 4
