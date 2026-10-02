"""
A stand-in for the ``curses`` module where there is no terminal (the browser).

Nothing is drawn. Windows remember the text written to them so that modal
screens (menus, the journal, dialogs) can be captured and shown by the web
page, and ``getch()`` is answered by the bridge (see bridge.py): from a queue
of keys the player already chose, or by stopping the action with ``NeedKey``
so the page can ask for the next key.
"""
# --- constants (ncurses values) -------------------------------------------
A_NORMAL = 0
A_STANDOUT = 1 << 16
A_UNDERLINE = 1 << 17
A_REVERSE = 1 << 18
A_BLINK = 1 << 19
A_DIM = 1 << 20
A_BOLD = 1 << 21
A_COLOR = 0xFF00
COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW = 0, 1, 2, 3
COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_WHITE = 4, 5, 6, 7
KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT = 258, 259, 260, 261
KEY_HOME, KEY_BACKSPACE = 262, 263
KEY_F0 = 264
KEY_DC, KEY_IC = 330, 331
KEY_NPAGE, KEY_PPAGE = 338, 339
KEY_ENTER = 343
KEY_END = 360
KEY_RESIZE = 410
LINES, COLS = 40, 140
ACS_VLINE, ACS_HLINE = '|', '-'


def KEY_F(n):
    return KEY_F0 + n


for _n in range(1, 13):
    globals()[f'KEY_F{_n}'] = KEY_F0 + _n


class error(Exception):
    pass


class NeedKey(BaseException):
    """Raised by getch() when the player has to choose; BaseException so the
    game's many ``except Exception`` blocks do not swallow it."""


# --- the key source, installed by the bridge --------------------------------
class _Keys:
    def __init__(self):
        self.queue = []
        self.mode = 'cancel'      # 'cancel': answer ESC (non-interactive) | 'ask': raise NeedKey
        self.asked = False        # a NeedKey was raised during this action
        self.calls = 0

    def next(self):
        self.calls += 1
        if self.queue:
            return self.queue.pop(0)
        if self.mode == 'ask' and not self.asked:
            self.asked = True
            raise NeedKey()
        if self.calls > 400:
            raise NeedKey()       # a loop that ignores ESC: give up on this action
        return 27                 # unwind (ESC) if NeedKey was swallowed


keys = _Keys()
_windows = []                     # every window in creation order (for capture)


def color_pair(n):
    return (int(n) & 0xFF) << 8


def pair_number(attr):
    return (int(attr) & A_COLOR) >> 8


def init_pair(*a, **k):
    pass


def start_color():
    pass


def use_default_colors():
    pass


def get_pairs():
    return 64


def endwin():
    pass


def resizeterm(*a):
    pass


def set_app(*a, **k):
    pass


def curs_set(*a):
    pass


def noecho():
    pass


def cbreak():
    pass


def has_colors():
    return True


def getch():
    return keys.next()


class window:
    def __init__(self, h=LINES, w=COLS, y=0, x=0, kind='new'):
        self.h, self.w, self.y, self.x = int(h), int(w), int(y), int(x)
        self.kind = kind          # 'std' | 'new' | 'sub'
        self.cells = {}
        self.touched = False
        self.cur_attr = 0
        self.cy = self.cx = 0
        _windows.append(self)

    # geometry
    def getmaxyx(self):
        return (self.h, self.w)

    def getbegyx(self):
        return (self.y, self.x)

    def getyx(self):
        return (self.cy, self.cx)

    def subwin(self, *a):
        if len(a) == 4:
            h, w, y, x = a
        else:
            (y, x), h, w = a, self.h - a[0], self.w - a[1]
        return window(h, w, y, x, kind='sub')

    derwin = subwin

    def resize(self, h, w):
        self.h, self.w = int(h), int(w)

    def mvwin(self, y, x):
        self.y, self.x = int(y), int(x)

    # drawing
    def _put(self, y, x, s, attr):
        attr = int(attr) | self.cur_attr
        for i, ch in enumerate(str(s)):
            if ch == '\n':
                y += 1
                x = -i - 1
                continue
            xx = x + i
            if 0 <= y < self.h and 0 <= xx < self.w:
                self.cells[(y, xx)] = (ch, attr)
        self.touched = True

    def addstr(self, *a):
        if len(a) >= 3 and isinstance(a[0], int) and isinstance(a[1], int):
            y, x, s = a[0], a[1], a[2]
            attr = a[3] if len(a) > 3 else 0
        else:
            y, x = self.cy, self.cx
            s = a[0]
            attr = a[1] if len(a) > 1 else 0
        s = s.decode('utf-8', 'replace') if isinstance(s, bytes) else str(s)
        self._put(int(y), int(x), s, attr)
        self.cy, self.cx = int(y), int(x) + len(s)

    def addnstr(self, *a):
        if len(a) >= 4 and isinstance(a[0], int):
            y, x, s, n = a[:4]
            self.addstr(y, x, str(s)[:max(0, int(n))], *(a[4:5]))
        else:
            s, n = a[:2]
            self.addstr(str(s)[:max(0, int(n))], *(a[2:3]))

    def addch(self, *a):
        if len(a) >= 3:
            y, x, ch = a[:3]
            attr = a[3] if len(a) > 3 else 0
        else:
            y, x, ch = self.cy, self.cx, a[0]
            attr = a[1] if len(a) > 1 else 0
        ch = chr(ch) if isinstance(ch, int) else str(ch)
        self._put(int(y), int(x), ch[:1], attr)

    insstr = addstr

    def hline(self, *a):
        pass

    def vline(self, *a):
        pass

    def border(self, *a):
        for x in range(self.w):
            self.cells[(0, x)] = ('─', 0)
            self.cells[(self.h - 1, x)] = ('─', 0)
        for y in range(self.h):
            self.cells[(y, 0)] = ('│', 0)
            self.cells[(y, self.w - 1)] = ('│', 0)
        self.touched = True

    box = border

    def clear(self):
        self.cells = {}
        self.touched = True

    erase = clear

    def clrtoeol(self):
        for k in [k for k in self.cells if k[0] == self.cy and k[1] >= self.cx]:
            del self.cells[k]

    def move(self, y, x):
        self.cy, self.cx = int(y), int(x)

    # attributes
    def attron(self, a):
        self.cur_attr |= int(a)

    def attroff(self, a):
        self.cur_attr &= ~int(a)

    def attrset(self, a):
        self.cur_attr = int(a)

    def bkgd(self, *a):
        pass

    bkgdset = bkgd

    # refresh / input
    def refresh(self, *a):
        pass

    noutrefresh = refresh

    def keypad(self, *a):
        pass

    def nodelay(self, *a):
        pass

    def timeout(self, *a):
        pass

    def scrollok(self, *a):
        pass

    def idlok(self, *a):
        pass

    def leaveok(self, *a):
        pass

    def getch(self, *a):
        return keys.next()

    def getkey(self, *a):
        k = keys.next()
        return chr(k) if 0 <= k < 0x110000 else str(k)

    def get_wch(self, *a):
        return keys.next()

    def getstr(self, *a):
        return b''

    def inch(self, *a):
        return 0


Window = window


def newwin(h, w, y=0, x=0):
    return window(h, w, y, x, kind='new')


def initscr():
    return window(LINES, COLS, 0, 0, kind='std')


def wrapper(fn, *a, **k):
    return fn(initscr(), *a, **k)


doupdate = endwin
napms = endwin


def reset_capture():
    """Forget what modal windows showed (call at the start of each action)."""
    for w in list(_windows):
        if w.kind != 'sub':
            w.touched = False
    # drop windows nobody will draw again
    _windows[:] = [w for w in _windows if w.kind in ('std', 'sub')]
    for w in _windows:
        if w.kind == 'std':
            w.cells = {}


def capture(rows=LINES, cols=COLS):
    """The modal screen drawn during this action: stdscr and popups, composed.

    Returns (lines, attrs): attrs holds one entry per line, a list of
    [start, end, color_pair, reverse] runs for the non-default cells.
    """
    grid = [[' '] * cols for _ in range(rows)]
    attr = [[0] * cols for _ in range(rows)]
    drawn = False
    for w in _windows:
        if w.kind == 'sub' or not w.touched or not w.cells:
            continue
        drawn = True
        if w.kind == 'new':  # popups cover what is behind them
            for yy in range(w.h):
                for xx in range(w.w):
                    Y, X = w.y + yy, w.x + xx
                    if 0 <= Y < rows and 0 <= X < cols:
                        grid[Y][X] = ' '
                        attr[Y][X] = 0
        for (yy, xx), (ch, a) in w.cells.items():
            Y, X = w.y + yy, w.x + xx
            if 0 <= Y < rows and 0 <= X < cols:
                grid[Y][X] = ch
                attr[Y][X] = a
    if not drawn:
        return None
    lines = [''.join(r).rstrip() for r in grid]
    # compact: drop blank rows (and rows that are only a frame) beyond one in a row,
    # then the common left margin
    frame = set(' │|║─═')
    keep, prev_blank = [], True
    for i, ln in enumerate(lines):
        blank = all(ch in frame for ch in ln) and not set(ln) & set('─═')
        if blank and prev_blank:
            continue
        keep.append(i)
        prev_blank = blank
    lines = [lines[i] for i in keep]
    attr = [attr[i] for i in keep]
    while lines and all(ch in frame for ch in lines[-1]) and not set(lines[-1]) & set('─═'):
        lines.pop()
        attr.pop()
    if not lines:
        return None
    margin = min((len(ln) - len(ln.lstrip(' ')) for ln in lines if ln.strip()), default=0)
    lines = [ln[margin:] for ln in lines]
    attr = [r[margin:] for r in attr]
    runs = []
    for r in attr[:len(lines)]:
        line_runs = []
        start = None
        cur = None
        for i, a in enumerate(r + [0]):
            key = (pair_number(a), bool(a & (A_REVERSE | A_STANDOUT))) if a else None
            if key != cur:
                if cur is not None:
                    line_runs.append([start, i, cur[0], cur[1]])
                start, cur = i, key
        runs.append(line_runs)
    return lines, runs
