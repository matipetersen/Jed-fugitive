# Headless test for push/pull ability
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game.player import Player
from jedi_fugitive.game.enemy import Enemy
from jedi_fugitive.game import abilities, force_abilities

# create a minimal fake stdscr
class DummyStdscr:
    def getmaxyx(self):
        return (40, 140)
    def getch(self):
        return -1
    def clear(self):
        pass
    def refresh(self):
        pass

if __name__ == '__main__':
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    # small map 10x10 floor
    gm.game_map = [[Display.FLOOR for _ in range(10)] for _ in range(10)]
    # place player at 5,5
    gm.player.x = 5; gm.player.y = 5
    gm.player.force_points = 5
    # create enemy at 6,5
    e = Enemy('Test Dummy', 10, 1, 0, 1, None, 10, 6, 5, level=1)
    gm.enemies = [e]
    # construct wrapper for push
    base = force_abilities.ForcePushPull()
    class Wrapper:
        def __init__(self, base, mode):
            self._base = base; self.mode = mode; self.name = f"{mode} - {getattr(base,'name',str(base))}"
        def use(self, *args, **kwargs):
            # delegate and accept either coords or actor
            try:
                return self._base.use(*args, **kwargs)
            except TypeError:
                try:
                    return self._base.use(*args, **kwargs)
                except Exception:
                    return False
    w = Wrapper(base, 'push')

    # simulate using push on tile (6,5)
    from jedi_fugitive.game.abilities import use_force_ability
    print('Before:', e.x, e.y, 'FP:', gm.player.force_points)
    used = use_force_ability(gm, w, 6, 5)
    print('Used returned:', used)
    print('After:', e.x, e.y, 'FP:', gm.player.force_points)
    # try pull back
    gm.player.force_points = 5
    w2 = Wrapper(base, 'pull')
    used2 = use_force_ability(gm, w2, 6, 5)
    print('Pull used returned:', used2)
    print('After pull:', e.x, e.y, 'FP:', gm.player.force_points)
