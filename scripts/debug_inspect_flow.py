# Debug inspect flow outside of handler
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display

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
    gm.player.facing = (1,0)
    gm.items_on_map = [{'x':6,'y':5,'token': '+'}]
    gm.enemies = []
    print('player facing', gm.player.facing)
    fdx, fdy = getattr(gm.player, 'facing', (1,0))
    px = getattr(gm.player, 'x', 0); py = getattr(gm.player, 'y', 0)
    fx = px + int(fdx); fy = py + int(fdy)
    print('facing tile', fx, fy)
    mh = len(gm.game_map); mw = len(gm.game_map[0]) if mh else 0
    print('map size', mw, mh)
    print('in bounds?', 0 <= fx < mw and 0 <= fy < mh)
    print('items_on_map', gm.items_on_map)
    found_item = None
    for it in gm.items_on_map:
        print('checking item', it)
        if it.get('x') == fx and it.get('y') == fy:
            found_item = it; break
    print('found_item', found_item)
    # try calling game.add_message
    try:
        gm.add_message('test message from debug')
    except Exception as e:
        print('add_message failed', e)
    print('messages buffer', getattr(gm.ui,'messages').messages)
