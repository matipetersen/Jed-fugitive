# Verify tomb persistence and unequip behavior (headless)
from copy import deepcopy
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

    # Enter tomb and check tomb_levels exists
    ok = gm.enter_tomb()
    if not ok:
        print('ERROR: enter_tomb returned False')
        raise SystemExit(2)
    floors = len(getattr(gm, 'tomb_levels', []))
    print(f'Generated tomb with {floors} floors')
    if floors < 1:
        print('ERROR: no floors generated')
        raise SystemExit(3)

    # snapshot the stringified floors for comparison
    def map_to_str(m):
        return '\n'.join(''.join(str(c) for c in row) for row in m)

    snapshots = [map_to_str(floor) for floor in gm.tomb_levels]

    # Walk down to deepest floor, then up to surface, then back down, checking equality
    initial_floor = gm.tomb_floor
    print(f'Initial floor index: {initial_floor}')

    # Descend until bottom
    while gm.tomb_floor < len(gm.tomb_levels) - 1:
        moved = gm.change_floor(1)
        if not moved:
            print('ERROR: failed to go down')
            raise SystemExit(4)
    print(f'Reached floor {gm.tomb_floor} (deepest)')

    # Ascend back to top floor (0)
    while gm.tomb_floor > 0:
        moved = gm.change_floor(-1)
        if not moved:
            print('ERROR: failed to go up')
            raise SystemExit(5)
    print(f'Returned to floor {gm.tomb_floor} (top)')

    # Now validate that each in-memory level equals the original snapshot
    mismatches = 0
    for idx, level in enumerate(gm.tomb_levels):
        s = map_to_str(level)
        if s != snapshots[idx]:
            print(f'MISMATCH on floor {idx}: snapshot differs from current stored level')
            mismatches += 1
    if mismatches == 0:
        print('PASS: tomb_levels are persistent and unchanged across floor changes')
    else:
        print(f'FAIL: {mismatches} floor(s) mismatched')

    # Also check that current game_map equals tomb_levels[tomb_floor]
    cur_str = map_to_str(gm.game_map)
    if cur_str == map_to_str(gm.tomb_levels[gm.tomb_floor]):
        print('PASS: game_map matches tomb_levels[tomb_floor] after floor changes')
    else:
        print('FAIL: game_map does NOT match the expected tomb level')

    # --- Unequip behavior tests ---
    print('\nTesting unequip behavior...')
    # ensure clean inventory
    gm.player.inventory = []
    gm.player.max_inventory = 2

    # Case 1: add equipped weapon and unequip into empty inventory
    weapon = {'name': 'Test Saber'}
    gm.player.equipped_weapon = weapon
    returned = gm.player.unequip_weapon()
    if returned is None:
        print('FAIL: unequip returned None when equipped')
        raise SystemExit(6)
    if any((getattr(x,'name', None) if not isinstance(x, dict) else x.get('name')) == 'Test Saber' for x in gm.player.inventory):
        print('PASS: unequipped item returned to inventory')
    else:
        print('FAIL: unequipped item NOT found in inventory')

    # Case 2: inventory full triggers ejection to ground
    gm.player.inventory = [{'name':'Old Item'}]
    gm.player.max_inventory = 1
    gm.player.equipped_weapon = {'name':'Second Saber'}
    returned2 = gm.player.unequip_weapon()
    if returned2 is None:
        print('FAIL: unequip returned None on full-inventory case')
        raise SystemExit(7)
    # ensure items_on_map contains a dropped item with name 'Old Item'
    dropped = any((it.get('name') == 'Old Item') for it in getattr(gm, 'items_on_map', []))
    if dropped:
        print('PASS: full inventory caused ejection of oldest item to ground')
    else:
        print('FAIL: expected ejected item to appear on game.items_on_map')

    print('\nAll tests completed.')
