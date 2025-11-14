import pytest
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game import equipment

class DummyStdScr:
    def __init__(self,h=40,w=160): self._h=h; self._w=w
    def getmaxyx(self): return (self._h,self._w)
    def subwin(self,*a,**k): return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self,*a,**k): pass
    def addnstr(self,*a,**k): pass
    def refresh(self): pass
    def noutrefresh(self): pass
    def resize(self,h,w): self._h, self._w = h, w
    def mvwin(self,y,x): pass
    def move(self,y,x): pass
    def clrtoeol(self): pass
    def getch(self): return -1

def setup_game():
    ui = DummyStdScr()
    gm = GameManager(ui)
    gm.initialize()
    gm.crash_inflate = 4
    gm.generate_world()
    return gm

def test_pickup_and_equip_increments_turn_count():
    gm = setup_game()
    p = gm.player
    # clear inventory and ensure turn_count starts at 0
    p.inventory = []
    gm.turn_count = 0
    # place a vibroblade at player's location
    token = 'v'
    x, y = p.x, p.y
    gm.game_map[y][x] = token
    gm.items_on_map.append({'x': x, 'y': y, 'token': token, 'name': 'Vibroblade'})
    # pick up
    equipment.pick_up(gm)
    assert len(p.inventory) == 1
    assert gm.turn_count == 1
    # equip
    equipment.equip_item(gm)
    assert getattr(p, 'equipped_weapon', None) is not None
    assert gm.turn_count == 2

def test_unequip_returns_to_inventory_or_drops_when_full():
    gm = setup_game()
    p = gm.player
    # prepare inventory at capacity
    p.inventory = ['x'] * int(getattr(gm, 'max_inventory', 9) or 9)
    # equip an item
    p.equipped_weapon = {'name': 'Test Blade'}
    # unequip
    returned = p.unequip_weapon()
    # returned should be the unequipped item
    assert returned is not None
    # inventory should still be at capacity (we eject oldest and add new)
    assert len(p.inventory) == int(getattr(gm, 'max_inventory', 9) or 9)

def test_cant_pickup_when_inventory_full():
    gm = setup_game()
    p = gm.player
    p.inventory = ['i'] * int(getattr(gm, 'max_inventory', 9) or 9)
    gm.turn_count = 0
    # place item at player
    token = 'b'
    x,y = p.x, p.y
    gm.game_map[y][x] = token
    gm.items_on_map.append({'x': x, 'y': y, 'token': token, 'name': 'Blaster'})
    equipment.pick_up(gm)
    # inventory should not grow
    assert len(p.inventory) == int(getattr(gm, 'max_inventory', 9) or 9)
    # turn count unchanged
    assert gm.turn_count == 0
