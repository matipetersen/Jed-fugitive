# Headless test: verify ROCK blocks movement and LOS
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
    # generate world so we have a surface map large enough for tests
    try:
        gm.generate_world()
    except Exception:
        pass

    # ensure player is placed centrally for test (some worlds start player at 0,0)
    mh = len(gm.game_map); mw = len(gm.game_map[0]) if mh else 0
    if mw and mh:
        gm.player.x = mw // 2
        gm.player.y = mh // 2
    px = int(getattr(gm.player, 'x', 1))
    py = int(getattr(gm.player, 'y', 1))
    print(f'Player at: {(px,py)}')

    # ensure map bounds
    mh = len(gm.game_map); mw = len(gm.game_map[0]) if mh else 0
    if px + 2 >= mw:
        print('Map too small to run rock tests; need >2 tiles to the right of player')
        raise SystemExit(2)

    # Place a rock at px+1
    try:
        gm.game_map[py][px+1] = getattr(Display, 'ROCK', 'r')
        print(f'Placed ROCK at {(px+1, py)}')
    except Exception as e:
        print('ERROR placing rock:', e)
        raise

    # Attempt to move into rock
    moved = gm._try_move_player(1, 0)
    if moved:
        print('FAIL: player moved into ROCK tile (movement should be blocked)')
        raise SystemExit(3)
    else:
        print('PASS: movement into ROCK is blocked')

    # Place a visible target two tiles away
    try:
        gm.game_map[py][px+2] = getattr(Display, 'SHIP', 'S')
        print(f'Placed visible target at {(px+2, py)}')
    except Exception as e:
        print('ERROR placing target:', e); raise

    # Recompute visibility
    vis = gm.compute_visibility()
    if (px+2, py) in vis:
        print('FAIL: target behind ROCK is visible (ROCK should block LOS)')
        # as a debugging aid, print some nearby tiles
        for ox in range(px, px+3):
            print(f'tile {(ox,py)}: {gm.game_map[py][ox]!r}')
        raise SystemExit(4)
    else:
        print('PASS: ROCK blocks LOS to tile behind it')

    # Now remove rock and ensure LOS opens
    try:
        gm.game_map[py][px+1] = getattr(Display, 'FLOOR', '.')
        print('Removed ROCK (set floor) at tile in front')
    except Exception:
        pass
    vis2 = gm.compute_visibility()
    if (px+2, py) in vis2:
        print('PASS: after removing ROCK target is visible')
    else:
        print('FAIL: after removing ROCK target still not visible')
        raise SystemExit(5)

    print('\nAll rock/LOS tests completed successfully.')
