"""Simulate killing an enemy via perform_player_attack and verify XP/leveling messages."""
import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
src = proj_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.enemy import Enemy
from jedi_fugitive.game.input_handler import perform_player_attack

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
    # ensure messages buffer exists
    try:
        g.ui.messages = g.ui.messages
    except Exception:
        pass
    # create a weak enemy next to player
    e = Enemy('Test Minion', 1, 1, 0, 0, None, 250, g.player.x+1, g.player.y)
    e.xp_value = 250
    e.hp = 1
    g.enemies.append(e)
    print('Player before: level, xp, force:', g.player.level, g.player.xp, g.player.force_points)
    # simulate attack
    perform_player_attack(g, e)
    print('Player after: level, xp, force:', g.player.level, g.player.xp, g.player.force_points)
    # show messages
    try:
        msgs = getattr(g.ui.messages, 'messages', [])
        print('Recent messages:', msgs[-6:])
    except Exception:
        pass

if __name__ == '__main__':
    run()
