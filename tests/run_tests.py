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
    gm.crash_inflate = 2
    gm.generate_world()
    return gm


def run():
    print('Running quick tests...')
    gm = setup_game()
    p = gm.player
    p.inventory = []
    gm.turn_count = 0
    x,y = p.x, p.y
    gm.game_map[y][x] = 'v'
    gm.items_on_map.append({'x': x, 'y': y, 'token': 'v', 'name': 'Vibroblade'})
    equipment.pick_up(gm)
    assert len(p.inventory) == 1, 'pickup did not add to inventory'
    assert gm.turn_count == 1, 'turn_count not incremented on pickup'
    equipment.equip_item(gm)
    assert getattr(p, 'equipped_weapon', None) is not None, 'equip did not set equipped_weapon'
    assert gm.turn_count == 2, 'turn_count not incremented on equip'
    # test unequip with full inventory
    p.inventory = ['i'] * int(getattr(gm, 'max_inventory', 9) or 9)
    p.equipped_weapon = {'name': 'Test Blade'}
    returned = p.unequip_weapon()
    assert returned is not None, 'unequip returned None'
    assert len(p.inventory) == int(getattr(gm, 'max_inventory', 9) or 9), 'inventory size changed unexpectedly'
    # try pickup when full
    p.inventory = ['i'] * int(getattr(gm, 'max_inventory', 9) or 9)
    gm.turn_count = 0
    gm.game_map[y][x] = 'b'
    gm.items_on_map.append({'x': x, 'y': y, 'token': 'b', 'name': 'Blaster'})
    equipment.pick_up(gm)
    assert len(p.inventory) == int(getattr(gm, 'max_inventory', 9) or 9), 'pickup allowed when full'
    assert gm.turn_count == 0, 'turn_count changed when pickup should have failed'
    print('All quick tests passed.')

if __name__ == '__main__':
    run()
