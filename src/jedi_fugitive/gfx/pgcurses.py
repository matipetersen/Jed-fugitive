"""A small curses-compatible API implemented on top of pygame.

The game was written against curses (≈70 ``addstr`` calls, a handful of
``getch``/``newwin``/``border`` calls). Instead of rewriting every panel, this
module is installed as ``sys.modules['curses']`` when the graphical front-end
starts, so the existing UI code keeps working unchanged while
:class:`jedi_fugitive.gfx.app.GfxApp` composites the windows with a modern look
and renders the map panel as real graphics.

Only the subset of curses used by the project is implemented, with the same
semantics where it matters (attribute bit layout, key codes, ``curses.error``
on out-of-bounds writes, ``subwin`` using absolute coordinates).
"""
from __future__ import annotations

IS_PYGAME_SHIM = True

# --- attributes (same bit layout as ncurses) ---------------------------------
A_NORMAL = 0
A_ATTRIBUTES = 0xFFFFFF00
A_COLOR = 0x0000FF00
A_CHARTEXT = 0x000000FF
A_STANDOUT = 1 << 16
A_UNDERLINE = 1 << 17
A_REVERSE = 1 << 18
A_BLINK = 1 << 19
A_DIM = 1 << 20
A_BOLD = 1 << 21
A_ALTCHARSET = 1 << 22
A_INVIS = 1 << 23
A_PROTECT = 1 << 24
A_ITALIC = 1 << 31

COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW = 0, 1, 2, 3
COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_WHITE = 4, 5, 6, 7
COLORS = 256
COLOR_PAIRS = 256

# --- key codes (ncurses values) ----------------------------------------------
KEY_MIN = 257
KEY_BREAK = 257
KEY_DOWN = 258
KEY_UP = 259
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_HOME = 262
KEY_BACKSPACE = 263
KEY_F0 = 264
for _i in range(1, 13):
    globals()[f"KEY_F{_i}"] = KEY_F0 + _i
KEY_DC = 330
KEY_IC = 331
KEY_NPAGE = 338
KEY_PPAGE = 339
KEY_ENTER = 343
KEY_BTAB = 353
KEY_END = 360
KEY_RESIZE = 410
KEY_MOUSE = 409
KEY_MAX = 511

# line drawing characters
ACS_VLINE = '│'
ACS_HLINE = '─'
ACS_ULCORNER = '┌'
ACS_URCORNER = '┐'
ACS_LLCORNER = '└'
ACS_LRCORNER = '┘'
ACS_LTEE = '├'
ACS_RTEE = '┤'
ACS_TTEE = '┬'
ACS_BTEE = '┴'
ACS_PLUS = '┼'
ACS_BLOCK = '█'
ACS_BULLET = '·'
ACS_DIAMOND = '◆'
ACS_CKBOARD = '▒'

# Cell value written by border(): drawn as a vector frame instead of glyphs.
BORDER_CELL = '\x01'

LINES = 0
COLS = 0

_app = None



def _strip_emoji(s):
    if all(ord(c) < 0x2600 for c in s):
        return s
    out = []
    for c in s:
        o = ord(c)
        if o > 0xFFFF or o in (0xFE0F, 0x200D):
            continue  # astral-plane emoji, variation selector, zero-width joiner
        out.append(c)
    return ''.join(out)

class error(Exception):
    pass


def KEY_F(n):
    return KEY_F0 + n


def set_app(app):
    global _app, LINES, COLS
    _app = app
    try:
        LINES, COLS = app.rows, app.cols
    except Exception:
        pass


def get_app():
    return _app


def color_pair(n):
    return (int(n) & 0xFF) << 8


def pair_number(attr):
    return (int(attr) & A_COLOR) >> 8


class Window:
    """A character-cell window. Rendering is done by the app compositor."""

    def __init__(self, app, nlines, ncols, begin_y, begin_x):
        self.app = app
        self.h = max(1, int(nlines))
        self.w = max(1, int(ncols))
        self.y = int(begin_y)
        self.x = int(begin_x)
        self.cy = 0
        self.cx = 0
        self.bkgd_attr = 0
        self.has_bkgd = False
        self.framed = False
        self.viewport = False     # interior replaced by the world renderer
        self.cur_attr = 0
        self._nodelay = False
        self._timeout = -1
        self._alloc()
        self._sig = None
        self._snap = None
        self._surface = None
        self._surface_key = None

    # --- internal helpers -------------------------------------------------
    def _alloc(self):
        self.chars = [[' '] * self.w for _ in range(self.h)]
        self.attrs = [[0] * self.w for _ in range(self.h)]

    def signature(self):
        return (self.h, self.w, self.framed, self.has_bkgd, self.bkgd_attr, self.viewport,
                tuple(''.join(r) for r in self.chars), tuple(tuple(r) for r in self.attrs))

    def _put(self, y, x, s, attr):
        """Write text with curses wrap semantics; raise error past window end."""
        if not (0 <= y < self.h) or not (0 <= x < self.w):
            raise error("addstr() returned ERR")
        overflow = False
        for ch in s:
            if ch == '\n':
                # curses clears to end of line and moves to the next one
                for cx in range(x, self.w):
                    self.chars[y][cx] = ' '
                    self.attrs[y][cx] = attr
                y += 1
                x = 0
                if y >= self.h:
                    overflow = True
                    break
                continue
            if ch == '\t':
                ch = ' '
            if y >= self.h:
                overflow = True
                break
            self.chars[y][x] = ch
            self.attrs[y][x] = attr
            x += 1
            if x >= self.w:
                x = 0
                y += 1
        self.cy = min(y, self.h - 1)
        self.cx = x
        if overflow or y >= self.h:
            # curses reports ERR when the cursor cannot advance past the end
            raise error("addstr() returned ERR")

    @staticmethod
    def _parse(args, need_str=True):
        if len(args) == 1:
            return None, None, args[0], 0
        if len(args) == 2:
            return None, None, args[0], args[1]
        if len(args) == 3:
            return args[0], args[1], args[2], 0
        if len(args) >= 4:
            return args[0], args[1], args[2], args[3]
        raise error("bad arguments")

    # --- output ---------------------------------------------------------------
    def addstr(self, *args):
        y, x, s, attr = self._parse(args)
        if y is None:
            y, x = self.cy, self.cx
        attr = int(attr) | self.cur_attr
        s = s.decode('utf-8', 'replace') if isinstance(s, bytes) else str(s)
        # the bundled monospace font has no colour emoji (they draw as tofu boxes)
        s = _strip_emoji(s)
        self._put(int(y), int(x), s, attr)

    def addnstr(self, *args):
        if len(args) in (2, 3):
            s, n = args[0], args[1]
            attr = args[2] if len(args) == 3 else 0
            self.addstr(str(s)[:max(0, int(n))], attr)
        else:
            y, x, s, n = args[0], args[1], args[2], args[3]
            attr = args[4] if len(args) > 4 else 0
            self.addstr(y, x, str(s)[:max(0, int(n))], attr)

    def addch(self, *args):
        if len(args) in (1, 2):
            ch = args[0]
            attr = args[1] if len(args) == 2 else 0
            y, x = self.cy, self.cx
        else:
            y, x, ch = args[0], args[1], args[2]
            attr = args[3] if len(args) > 3 else 0
        if isinstance(ch, int):
            attr = attr | (ch & ~A_CHARTEXT & 0xFFFFFF00)
            ch = chr(ch & 0xFF) if ch < 256 else chr(ch)
        try:
            self._put(int(y), int(x), str(ch)[:1] or ' ', int(attr) | self.cur_attr)
        except error:
            # curses writes the bottom-right character but still reports ERR
            if not (int(y) == self.h - 1 and int(x) == self.w - 1):
                raise

    insstr = addstr

    def hline(self, *args):
        if len(args) == 2:
            y, x, ch, n = self.cy, self.cx, args[0], args[1]
        else:
            y, x, ch, n = args[0], args[1], args[2], args[3]
        ch = chr(ch) if isinstance(ch, int) else str(ch)[:1]
        for i in range(int(n)):
            if 0 <= y < self.h and 0 <= x + i < self.w:
                self.chars[y][x + i] = ch
                self.attrs[y][x + i] = self.cur_attr

    def vline(self, *args):
        if len(args) == 2:
            y, x, ch, n = self.cy, self.cx, args[0], args[1]
        else:
            y, x, ch, n = args[0], args[1], args[2], args[3]
        ch = chr(ch) if isinstance(ch, int) else str(ch)[:1]
        for i in range(int(n)):
            if 0 <= y + i < self.h and 0 <= x < self.w:
                self.chars[y + i][x] = ch
                self.attrs[y + i][x] = self.cur_attr

    def border(self, *args):
        self.framed = True
        for x in range(self.w):
            self.chars[0][x] = BORDER_CELL
            self.chars[self.h - 1][x] = BORDER_CELL
            self.attrs[0][x] = 0
            self.attrs[self.h - 1][x] = 0
        for y in range(self.h):
            self.chars[y][0] = BORDER_CELL
            self.chars[y][self.w - 1] = BORDER_CELL
            self.attrs[y][0] = 0
            self.attrs[y][self.w - 1] = 0

    def box(self, *args):
        self.border()

    def bkgd(self, ch=' ', attr=0):
        if isinstance(ch, int) and attr == 0:
            attr = ch & 0xFFFFFF00
        self.has_bkgd = True
        self.bkgd_attr = int(attr)

    bkgdset = bkgd

    def erase(self):
        self._alloc()
        self.framed = False
        self.cy = self.cx = 0

    clear = erase

    def clrtoeol(self):
        for x in range(self.cx, self.w):
            self.chars[self.cy][x] = ' '
            self.attrs[self.cy][x] = 0

    def clrtobot(self):
        self.clrtoeol()
        for y in range(self.cy + 1, self.h):
            self.chars[y] = [' '] * self.w
            self.attrs[y] = [0] * self.w

    def move(self, y, x):
        if not (0 <= y < self.h and 0 <= x < self.w):
            raise error("wmove() returned ERR")
        self.cy, self.cx = int(y), int(x)

    def attron(self, attr):
        self.cur_attr |= int(attr)

    def attroff(self, attr):
        self.cur_attr &= ~int(attr)

    def attrset(self, attr):
        self.cur_attr = int(attr)

    # --- geometry ---------------------------------------------------------------
    def getmaxyx(self):
        return (self.h, self.w)

    def getbegyx(self):
        return (self.y, self.x)

    def getyx(self):
        return (self.cy, self.cx)

    def subwin(self, *args):
        if len(args) == 2:
            nlines, ncols = self.h - args[0] + self.y, self.w - args[1] + self.x
            by, bx = args
        else:
            nlines, ncols, by, bx = args
        if nlines <= 0 or ncols <= 0:
            raise error("subwin() returned NULL")
        return Window(self.app, nlines, ncols, by, bx)

    def derwin(self, *args):
        if len(args) == 2:
            return self.subwin(self.y + args[0], self.x + args[1])
        nlines, ncols, by, bx = args
        return Window(self.app, nlines, ncols, self.y + by, self.x + bx)

    def resize(self, nlines, ncols):
        nlines, ncols = max(1, int(nlines)), max(1, int(ncols))
        old_c, old_a = self.chars, self.attrs
        self.h, self.w = nlines, ncols
        self._alloc()
        for y in range(min(len(old_c), self.h)):
            for x in range(min(len(old_c[y]), self.w)):
                self.chars[y][x] = old_c[y][x]
                self.attrs[y][x] = old_a[y][x]
        self._surface = None

    def mvwin(self, y, x):
        self.y, self.x = int(y), int(x)

    # --- refresh / input -----------------------------------------------------------
    def refresh(self, *args):
        if self.app is not None:
            self.app.composite(self)

    noutrefresh = refresh

    def touchwin(self):
        pass

    def redrawwin(self):
        pass

    def keypad(self, flag):
        pass

    def nodelay(self, flag):
        self._nodelay = bool(flag)

    def timeout(self, ms):
        self._timeout = int(ms)

    def scrollok(self, flag):
        pass

    def idlok(self, flag):
        pass

    def leaveok(self, flag):
        pass

    def clearok(self, flag):
        pass

    def immedok(self, flag):
        pass

    def getch(self, *args):
        if self.app is None:
            return -1
        if self._nodelay:
            return self.app.getch(timeout_ms=0)
        return self.app.getch(timeout_ms=self._timeout)

    def getkey(self, *args):
        k = self.getch()
        if k == -1:
            raise error("no input")
        return chr(k) if k < 256 else str(k)

    def get_wch(self, *args):
        k = self.getch()
        if k == -1:
            raise error("no input")
        return chr(k) if k < 256 else k

    def inch(self, y=None, x=None):
        if y is None:
            y, x = self.cy, self.cx
        return ord(self.chars[y][x][0]) | self.attrs[y][x]


window = Window


# --- module level API ------------------------------------------------------------
def initscr():
    if _app is None:
        raise error("graphical app not initialised")
    return _app.stdscr


def wrapper(func, *args, **kwargs):
    stdscr = initscr()
    return func(stdscr, *args, **kwargs)


def newwin(nlines, ncols, begin_y=0, begin_x=0):
    if nlines <= 0 or ncols <= 0:
        raise error("newwin() returned NULL")
    return Window(_app, nlines, ncols, begin_y, begin_x)


_pairs = {0: (-1, -1)}


def init_pair(n, fg, bg):
    _pairs[int(n)] = (int(fg), int(bg))


def pair_content(n):
    return _pairs.get(int(n), (-1, -1))


def get_pairs():
    return _pairs


def start_color():
    pass


def use_default_colors():
    pass


def has_colors():
    return True


def can_change_color():
    return False


def init_color(*args):
    pass


def endwin():
    pass


def isendwin():
    return False


def resizeterm(*args):
    pass


def resize_term(*args):
    pass


def is_term_resized(*args):
    return False


def update_lines_cols():
    pass


def curs_set(v):
    return 0


def noecho():
    pass


def echo():
    pass


def cbreak():
    pass


def nocbreak():
    pass


def raw():
    pass


def noraw():
    pass


def beep():
    pass


def flash():
    if _app is not None:
        _app.flash()


def doupdate():
    pass


def napms(ms):
    if _app is not None:
        _app.sleep(ms / 1000.0)
    return 0


def mousemask(*args):
    return (0, 0)


def flushinp():
    if _app is not None:
        _app.flush_input()


def ungetch(ch):
    if _app is not None:
        _app.push_key(ch if isinstance(ch, int) else ord(ch))


def keyname(k):
    try:
        return chr(k).encode()
    except Exception:
        return b'?'


def baudrate():
    return 38400


def setupterm(*args, **kwargs):
    pass
