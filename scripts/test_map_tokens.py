# Headless test to show items_on_map entries produced by generate_world
from jedi_fugitive.game.game_manager import GameManager

class DummyStdscr:
    def getmaxyx(self): return (40,140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

if __name__ == '__main__':
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    gm.generate_world()
    print('Placed items_on_map (first 10):')
    for it in (getattr(gm,'items_on_map',[]) or [])[:10]:
        print(it)
    print('\nMap sample (10x10 top-left):')
    for y in range(10):
        print(''.join(str(c) for c in gm.game_map[y][:40]))
