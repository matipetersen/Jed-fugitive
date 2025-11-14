# Headless test for consumable pickup and use
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
    gm.player.hp = 5
    gm.player.max_hp = 20
    # place a small medkit '+' at player
    gm.game_map[5][5] = '+'
    gm.items_on_map = [{'x':5,'y':5,'token':'+'}]
    print('Before use: HP=', gm.player.hp)
    equipment.pick_up(gm)
    print('Inventory after pickup:', gm.player.inventory)
    used = equipment.use_item(gm)
    print('use_item returned:', used)
    print('After use: HP=', gm.player.hp)
    # test stress reduction med
    gm.player.stress = 50
    gm.game_map[5][5] = 'M'
    gm.items_on_map = [{'x':5,'y':5,'token':'M'}]
    equipment.pick_up(gm)
    print('Inventory before stress use:', gm.player.inventory)
    used2 = equipment.use_item(gm)
    print('use_item returned:', used2)
    print('After use: Stress=', gm.player.stress)
