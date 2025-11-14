
import curses
from typing import Tuple, Optional

def init_colors():
    """Initialize a small set of color pairs used by the UI."""
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_WHITE, -1)
        curses.init_pair(5, curses.COLOR_BLUE, -1)
        curses.init_pair(14, curses.COLOR_WHITE, curses.COLOR_BLUE)
    except curses.error:
        # ignore if terminal doesn't support colors
        pass

def centered_window(height: int, width: int, stdscr) -> Optional[curses.window]:
    """Return a centered curses window (or None on error)."""
    try:
        th, tw = stdscr.getmaxyx()
        y = max(0, (th - height)//2)
        x = max(0, (tw - width)//2)
        win = curses.newwin(height, width, y, x)
        win.keypad(True)
        return win
    except curses.error:
        return None