import random

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import map_features as mf


class DummyStdScr:
    def __init__(self, h=40, w=160): self._h = h; self._w = w
    def getmaxyx(self): return (self._h, self._w)
    def subwin(self, *a, **k): return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self, *a, **k): pass
    def addnstr(self, *a, **k): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self, h, w): self._h, self._w = h, w
    def mvwin(self, y, x): pass
    def move(self, y, x): pass
    def clrtoeol(self): pass
    def getch(self): return -1


def make_game(seed=1, size='small'):
    random.seed(seed)
    gm = GameManager(DummyStdScr())
    gm.initialize()
    gm.world_size = size
    gm.generate_world()
    return gm


def test_world_size_and_objectives_reachable():
    gm = make_game(seed=3, size='normal')
    w, h = mf.WORLD_SIZES['normal']
    assert (len(gm.game_map[0]), len(gm.game_map)) == (w, h)
    reach = mf._reachable_from(gm.game_map, gm.player.x, gm.player.y)
    assert len(reach) > 20000
    assert len(gm.tomb_entrances) >= 3
    for target in list(gm.tomb_entrances) + [gm.ship_pos, gm.comms_pos]:
        assert target in reach, target


def test_lore_pois_are_never_walls_or_water():
    gm = make_game(seed=5)
    for (x, y), info in gm.map_landmarks.items():
        if 'sith_lore' in info:
            assert gm.game_map[y][x] not in mf.BLOCKING


def test_no_enemy_spawns_on_top_of_the_crash_site():
    for seed in range(4):
        gm = make_game(seed=seed)
        for e in gm.enemies:
            assert abs(e.x - gm.player.x) + abs(e.y - gm.player.y) > 10


def test_final_boss_spawns_and_victory_is_reachable():
    gm = make_game(seed=2)
    gm.comms_established = True
    sx, sy = gm.ship_pos
    gm.player.x, gm.player.y = sx - 1, sy
    gm.game_map[sy][sx - 1] = '.'
    gm._try_move_player(1, 0)
    assert getattr(gm, 'final_boss_spawned', False)
    boss = gm.final_boss
    assert (boss.x, boss.y) != (gm.player.x, gm.player.y)
    gm.enemies.remove(boss)
    gm.player.x -= 1
    gm._try_move_player(1, 0)
    assert gm.victory


def test_travel_log_alias_records_entries():
    gm = make_game(seed=1)
    before = len(gm.player.travel_log)
    gm.player.add_to_travel_log("[TEST] entry")
    assert len(gm.player.travel_log) == before + 1


def test_far_enemies_stay_dormant():
    gm = make_game(seed=4)
    far = [e for e in gm.enemies if abs(e.x - gm.player.x) + abs(e.y - gm.player.y) > 60]
    assert far
    before = [(e.x, e.y) for e in far]
    for _ in range(5):
        gm._world_tick()
    assert [(e.x, e.y) for e in far] == before
