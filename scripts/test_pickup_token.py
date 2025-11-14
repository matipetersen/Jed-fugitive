# Headless test for pickup token handling
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game import equipment

class DummyStdscr:
    def getmaxyx(self): return (40,140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

if __name__ == '__main__':
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    gm.game_map = [[Display.FLOOR for _ in range(10)] for _ in range(10)]
    gm.player.x = 5; gm.player.y = 5
    # place vibroblade token at player's tile
    gm.game_map[5][5] = 'v'
    gm.items_on_map = [{'x':5,'y':5,'token':'v'}]
    # pick up
    equipment.pick_up(gm)
    # print inventory
    inv = getattr(gm.player,'inventory',[]) or []
    print('Inventory after pickup:')
    for i in inv:
        print(repr(i))
    # print messages
    print('\nMessages:')
    for m in getattr(gm.ui,'messages').messages:
        print(m.get('text'))
