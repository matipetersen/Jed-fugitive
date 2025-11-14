from jedi_fugitive.game.game_manager import GameManager
from jedi_fugitive.game.level import Display
from jedi_fugitive.game import equipment, input_handler

class DummyStdscr:
    def getmaxyx(self): return (40,140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

# Setup game
gm = GameManager(DummyStdscr())
gm.initialize()
# Create a simple map so compute_visibility etc. won't crash
gm.game_map = [[Display.FLOOR for _ in range(10)] for _ in range(5)]
# Show base stats
print('Before equip:')
for ln in gm.player.get_stats_display():
    print(ln)

# Craft a dict-backed weapon and armor
weapon = {'token': 'v', 'name': 'Vibroblade', 'attack': 3}
armor = {'token': 's', 'name': 'Energy Shield', 'defense': 2, 'max_hp': 5}

# Place them in inventory
gm.player.inventory = [weapon, armor]

# Equip weapon (call equip_item; with single-item selection logic it will auto-choose if single, but we have 2 -> inventory_chooser will attempt to read getch, which returns -1 -> returns None, so equip_item will fallback to inv[0] if len==1. To avoid chooser, call equipment._apply_equipment_effects directly.)
# Apply weapon effects
equipment._apply_equipment_effects(gm, weapon, 'weapon')
# Apply armor effects
equipment._apply_equipment_effects(gm, armor, 'armor')

print('\nAfter equip:')
for ln in gm.player.get_stats_display():
    print(ln)

# Also print equipped items
print('\nEquipped:')
print('Weapon:', getattr(gm.player, 'equipped_weapon', None))
print('Armor:', getattr(gm.player, 'equipped_armor', None))
