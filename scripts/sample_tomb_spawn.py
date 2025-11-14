# Sample tomb spawn distribution
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
    success = gm.enter_tomb()
    if not success:
        print('enter_tomb failed')
        exit(1)
    # count enemy types per floor
    counts = {}
    for idx, floor_en in enumerate(getattr(gm, 'tomb_enemies', [])):
        for e in floor_en:
            name = getattr(e, 'name', None) or getattr(e, '__class__', type(e)).__name__
            counts[name] = counts.get(name, 0) + 1
    print('Enemy distribution across tomb (sample):')
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{k}: {v}")
    # also show first floor sample
    if gm.tomb_enemies:
        print('\nFirst floor sample:')
        for e in gm.tomb_enemies[0][:10]:
            print('-', getattr(e,'name',str(e)))
