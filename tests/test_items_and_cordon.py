import io
import contextlib
import math
import random

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import equipment
from jedi_fugitive.items import registry
from jedi_fugitive.items.tokens import TOKEN_MAP


class DummyStdScr:
    def __init__(self, h=40, w=160): self._h = h; self._w = w; self.keys = []
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
    def getch(self): return self.keys.pop(0) if self.keys else 27


def make_game(seed=1, cordon=True):
    random.seed(seed)
    gm = GameManager(DummyStdScr())
    gm.cordon_enabled = cordon
    gm.initialize()
    gm.world_size = 'small'
    with contextlib.redirect_stdout(io.StringIO()):
        gm.generate_world()
    return gm


WORLD_GLYPHS = set('#~rTCSDo*=x<>') | set('MOAdWYHIVFUPQGNBJRL')


def test_item_glyphs_never_collide_with_world_glyphs():
    assert not (set(TOKEN_MAP) - {'Q'}) & WORLD_GLYPHS


def test_every_item_can_be_picked_up_and_used_or_equipped():
    gm = make_game(seed=2, cordon=False)
    p = gm.player
    for tk, info in TOKEN_MAP.items():
        p.inventory = []
        x, y = p.x, p.y
        gm.items_on_map = [{'x': x, 'y': y, 'token': tk, 'name': info['name'], 'type': info.get('type'),
                            'effect': info.get('effect')}]
        equipment.pick_up(gm)
        assert len(p.inventory) == 1, tk
        item = p.inventory[0]
        if info.get('type') in ('weapon', 'armor'):
            assert not isinstance(item, dict), f"{tk} should materialize into a real object"
            gm.stdscr.keys = [ord('m')]
            equipment.equip_item(gm)
        else:
            gm.stdscr.keys = [ord('1')]
            equipment.use_item(gm)   # must not raise / print tracebacks
    assert "Item use failed." not in [m['text'] for m in gm.ui.messages.messages]


def test_consumable_is_consumed_and_heals():
    gm = make_game(seed=3, cordon=False)
    p = gm.player
    p.hp, p.max_hp = 2, 20
    p.inventory = [registry.materialize(TOKEN_MAP['+'])]
    assert equipment.use_item(gm) is True
    assert p.hp == 12 and p.inventory == []


def test_replaced_weapon_returns_to_inventory():
    gm = make_game(seed=4, cordon=False)
    p = gm.player
    p.inventory = [registry.materialize(TOKEN_MAP['v']), registry.materialize(TOKEN_MAP['/'])]
    p.equipped_weapon = None
    # the chooser is a popup menu: pick entry 0 (Vibroblade), then the only equippable left
    gm.ui.popup_dialogue = lambda items, **kw: 0
    equipment.equip_item(gm)
    gm.stdscr.keys = [ord('m')]  # replace the main-hand weapon
    equipment.equip_item(gm)
    assert p.equipped_weapon.name == 'Single Lightsaber'
    assert [registry.item_name(i) for i in p.inventory] == ['Vibroblade']


def test_drop_and_pickup_keeps_the_same_object():
    gm = make_game(seed=5, cordon=False)
    p = gm.player
    saber = registry.materialize(TOKEN_MAP['/'])
    p.inventory = [saber]
    equipment.drop_item(gm)
    assert p.inventory == []
    equipment.pick_up(gm)
    assert p.inventory and p.inventory[0] is saber


def test_cordon_lands_in_a_ring_and_closes_on_a_player_who_waits():
    gm = make_game(seed=6)
    c = gm.cordon
    assert c.active and len(c.units) >= 8
    cx, cy = c.center
    for u in c.units:
        assert abs(math.hypot(u.x - cx, u.y - cy) - c.radius0) <= 7
    r0 = c.radius
    for _ in range(65):
        gm._world_tick()
        if not gm.running:
            break
    assert c.radius < r0
    nearest = min(abs(u.x - gm.player.x) + abs(u.y - gm.player.y) for u in c.units if u.hp > 0)
    assert nearest <= 6 or not gm.running


def test_leaving_the_ring_ends_the_cordon():
    gm = make_game(seed=7)
    c = gm.cordon
    gm.player.x = int(c.center[0] + c.escape_radius + 2)
    gm.player.y = c.center[1]
    gm._world_tick()
    assert not c.active and c.escaped
    assert all(not getattr(u, 'cordon', False) for u in c.units)
