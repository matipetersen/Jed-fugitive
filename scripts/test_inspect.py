# Headless test for inspect command
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game.enemy import Enemy
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
    # place enemy at 6,5
    e = Enemy('Test Dummy', 10, 1, 0, 1, None)
    e.x = 6; e.y = 5; e.level = 1; e.max_hp = 10; e.hp = 10
    gm.enemies = [e]
    # place medkit at 4,5
    gm.items_on_map = [{'x':4,'y':5,'token': '+'}]
    gm.game_map[5][4] = '+'
    # call input handler for 'x' (inspect)
    input_handler.handle_input(gm, ord('x'))
    # print messages
    for m in getattr(gm.ui,'messages').messages:
        print(m.get('text'))
