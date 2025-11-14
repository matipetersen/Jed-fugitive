# Headless test for equip/pickup flow
from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game.player import Player
from jedi_fugitive.game.enemy import Enemy
from jedi_fugitive.game import equipment

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
    # place a token weapon 'v' (vibroblade) on map at player pos
    gm.game_map[5][5] = 'v'
    gm.items_on_map = [{'x':5,'y':5,'token':'v'}]

    print('Before equip: attack=', gm.player.attack, 'defense=', gm.player.defense, 'max_hp=', gm.player.max_hp)
    # simulate pick up
    equipment.pick_up(gm)
    print('Inventory after pickup:', gm.player.inventory)
    # equip
    equipment.equip_item(gm)
    print('After equip: attack=', gm.player.attack, 'defense=', gm.player.defense, 'max_hp=', gm.player.max_hp)
    # unequip weapon to test removal
    try:
        gm.player.equipped_weapon and gm.player.unequip_weapon()
    except Exception:
        pass
    equipment._remove_equipment_effects(gm, 'weapon')
    print('After remove: attack=', gm.player.attack, 'defense=', gm.player.defense, 'max_hp=', gm.player.max_hp)
