# Headless test for inspect facing mechanic
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game import input_handler

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
    # place medkit at 6,5 (in front of player facing east)
    gm.items_on_map = [{'x':6,'y':5,'token': '+'}]
    gm.game_map[5][6] = '+'
    # ensure no enemies nearby
    gm.enemies = []
    # set facing explicitly
    gm.player.facing = (1,0)
    # call inspect
    input_handler.handle_input(gm, ord('x'))
    # print messages
    for m in getattr(gm.ui,'messages').messages:
        print(m.get('text'))
