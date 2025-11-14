# Test movement into wall/tree tiles
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
    # map 10x3: player at (1,1), wall at (2,1), tree at (3,1), floor elsewhere
    gm.game_map = [[Display.FLOOR for _ in range(10)] for _ in range(3)]
    gm.game_map[1][2] = Display.WALL
    # place a tree glyph explicitly
    try:
        tree_char = getattr(Display, 'TREE', 'T')
    except Exception:
        tree_char = 'T'
    gm.game_map[1][3] = tree_char
    gm.player.x = 1; gm.player.y = 1

    print('Initial player:', gm.player.x, gm.player.y)
    # sanity checks before invoking input handler
    print('Cell at 2,1:', repr(gm.game_map[1][2]), '== Display.WALL?', gm.game_map[1][2] == Display.WALL)
    try:
        print('str equality:', str(gm.game_map[1][2]) == str(getattr(Display,'WALL','?')))
    except Exception:
        pass
    # attempt move right into wall (key 'l')
    input_handler.handle_input(gm, ord('l'))
    print('After move into wall attempt:', gm.player.x, gm.player.y)
    # attempt move right into tree (second move)
    input_handler.handle_input(gm, ord('l'))
    print('After move into tree attempt:', gm.player.x, gm.player.y)
    # print map row for context
    print('Map row:', ''.join(gm.game_map[1]))
    # print messages
    for m in getattr(gm.ui,'messages').messages:
        print('MSG:', m.get('text'))
