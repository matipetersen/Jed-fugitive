"""Quick leveling test.

Run with: PYTHONPATH=src python3 scripts/test_leveling.py
"""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from jedi_fugitive.game.game_manager import GameManager

class Dummy:
    def getmaxyx(self): return (24,80)
    def subwin(self,*a,**k): return self
    def clear(self): pass
    def erase(self): pass
    def border(self): pass
    def addstr(self,*a,**k): pass
    def refresh(self): pass
    def getch(self): return -1


def run():
    g = GameManager(Dummy())
    g.initialize()
    p = g.player
    print("Initial level, xp:", p.level, p.xp, "to next:", p.xp_to_next_level(p.level))
    # give enough XP to level multiple times
    gained = 0
    for amt in [50, 100, 300, 500]:
        print(f"Giving {amt} XP...")
        leveled = p.gain_xp(amt)
        gained += amt
        print("After: level, xp:", p.level, p.xp, "leveled?", leveled)
    print("Final state:", p.level, p.xp)

if __name__ == '__main__':
    run()
