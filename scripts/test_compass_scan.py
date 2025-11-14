#!/usr/bin/env python3
"""Headless test: verify compass/scan returns a direction and distance to nearest tomb."""
from jedi_fugitive.game.game_manager import GameManager

class DummyStdscr:
    def getmaxyx(self): return (40,140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

def find_last_scan_message(gm):
    try:
        msgs = getattr(gm.ui, 'messages', None)
        if msgs is None:
            return None
        lines = []
        # UIMessageBuffer exposes .messages in render paths; fall back to get_lines
        if hasattr(msgs, 'messages'):
            lines = list(getattr(msgs, 'messages') or [])
        elif hasattr(msgs, 'get_lines'):
            lines = list(msgs.get_lines() or [])
        else:
            return None
        for ln in reversed(lines):
            try:
                s = ln if isinstance(ln, str) else (ln.get('text') if isinstance(ln, dict) else str(ln))
            except Exception:
                s = str(ln)
            if 'tomb' in s.lower() or 'you sense' in s.lower() or 'scan' in s.lower():
                return s
        return None
    except Exception:
        return None

if __name__ == '__main__':
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    try:
        gm.generate_world()
    except Exception:
        pass

    mh = len(gm.game_map); mw = len(gm.game_map[0]) if mh else 0
    if mw and mh:
        gm.player.x = mw // 2
        gm.player.y = mh // 2
    px = int(getattr(gm.player, 'x', 1)); py = int(getattr(gm.player, 'y', 1))
    print(f'Player at: {(px,py)}')

    # ensure we have a tomb entrance; generate_world should create them but be defensive
    if not getattr(gm, 'tomb_entrances', None):
        tx = min(mw-2, px + 8) if mw else px + 8
        ty = py
        try:
            gm.tomb_entrances.add((tx, ty))
            print(f'No tombs detected; injected tomb at {(tx,ty)}')
        except Exception:
            pass

    # perform scan
    ok = gm.perform_scan()
    if not ok:
        print('FAIL: perform_scan returned False')
        raise SystemExit(2)

    # find message
    msg = find_last_scan_message(gm)
    if not msg:
        print('FAIL: no scan message found in UI messages')
        raise SystemExit(3)
    print('Scan message:', msg)
    # basic validation: message should contain a number (distance) and a direction (N/S/E/W)
    import re
    if re.search(r"\d+", msg) and re.search(r"\b(N|S|E|W|NE|NW|SE|SW)\b", msg):
        print('PASS: scan produced direction and distance')
    else:
        print('FAIL: scan message missing distance/direction')
        raise SystemExit(4)

    print('\nCompass/scan test completed.')
