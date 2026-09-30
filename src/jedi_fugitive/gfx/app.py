"""pygame front-end: window, input, compositor and console overlay.

The app owns the pygame window. Game code draws text through the curses shim
(:mod:`jedi_fugitive.gfx.pgcurses`); every ``refresh()`` hands a window to
:meth:`GfxApp.composite`, which keeps a z-ordered stack of windows. Each frame
the app paints a background, lets the :class:`WorldRenderer` draw the map
viewport, then blits the cached window surfaces on top (rounded panels, chip
titles, modern palette).
"""
from __future__ import annotations

import builtins
import io
import os
import re
import sys
import time
import weakref
from collections import deque

import pygame

from jedi_fugitive.gfx import pgcurses, theme

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONT_DIR = os.path.join(ASSET_DIR, "fonts")
BLOCKS = {'█': 1.0, '▓': 0.7, '▒': 0.45, '░': 0.2}
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def _font_path(name):
    # PyInstaller onefile bundles data under sys._MEIPASS
    candidates = [os.path.join(FONT_DIR, name)]
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.insert(0, os.path.join(base, "jedi_fugitive", "assets", "fonts", name))
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def load_font(size, bold=False, mono=True):
    name = ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf") if mono else "DejaVuSans.ttf"
    path = _font_path(name)
    try:
        if path:
            f = pygame.font.Font(path, size)
        else:
            f = pygame.font.SysFont("dejavusansmono,menlo,consolas,couriernew,monospace", size, bold=bold)
    except Exception:
        f = pygame.font.Font(None, size + 4)
    return f


class _Tee(io.TextIOBase):
    """stdout replacement that keeps the recent printed lines for the overlay."""

    def __init__(self, real, sink):
        self.real = real
        self.sink = sink

    def write(self, s):
        try:
            if self.real is not None:
                self.real.write(s)
        except Exception:
            pass
        self.sink.append(s)
        return len(s)

    def flush(self):
        try:
            if self.real is not None:
                self.real.flush()
        except Exception:
            pass


class _Snap:
    __slots__ = ("chars", "attrs", "framed", "has_bkgd", "viewport", "w", "h", "real")

    def __init__(self, chars, attrs, framed, has_bkgd, viewport, w, h, real):
        self.chars, self.attrs, self.framed, self.has_bkgd = chars, attrs, framed, has_bkgd
        self.viewport, self.w, self.h, self.real = viewport, w, h, real


class GfxApp:
    TITLE = "Jedi Fugitive: Echoes of the Fallen"

    def __init__(self, size=None, fullscreen=False, font_size=None):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        # only video + fonts: the game has no audio and mixer init spams errors on headless boxes
        pygame.display.init()
        pygame.font.init()
        pygame.key.set_repeat(170, 55)
        try:
            desktop = pygame.display.get_desktop_sizes()[0]
        except Exception:
            desktop = (1600, 1000)
        if size is None:
            size = (max(1024, min(1680, int(desktop[0] * 0.86))), max(700, min(1020, int(desktop[1] * 0.86))))
        self.fullscreen = fullscreen
        self.windowed_size = size
        flags = pygame.RESIZABLE
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption(self.TITLE)
        self._set_icon()

        self.font_size = font_size or self._auto_font_size(self.screen.get_size())
        self._load_fonts()

        self.cols = max(40, self.screen.get_width() // self.cw)
        self.rows = max(20, self.screen.get_height() // self.ch)
        self.stdscr = pgcurses.Window(self, self.rows, self.cols, 0, 0)
        pgcurses.set_app(self)

        self.stack = []                  # weakrefs in z-order (bottom first)
        self.keys = deque()
        self.clock = pygame.time.Clock()
        self.last_frame = 0.0
        self.frame_dt = 1 / 60.0
        self.fps = 60.0
        self.world = None
        self.game = None
        self.on_resize = None
        self.on_hotkey = None
        self.quit_requested = False
        self.interrupt_getch = False
        self.show_fps = False
        self._glyphs = {}
        self._bg_cache = None
        self._flash_until = 0.0
        self._printed = []
        self._console_installed = False

    # ------------------------------------------------------------------ setup
    def _auto_font_size(self, px):
        # aim for at least ~128x40 cells so the existing panel layout fits
        for size in range(18, 10, -1):
            f = load_font(size)
            cw, ch = f.size("M")[0], f.get_linesize()
            if px[0] // cw >= 128 and px[1] // ch >= 40:
                return size
        return 11

    def _load_fonts(self):
        self.font = load_font(self.font_size)
        self.font_bold = load_font(self.font_size, bold=True)
        self.font_fallback = load_font(self.font_size, mono=False)
        self.cw = self.font.size("M")[0]
        self.ch = self.font.get_linesize()
        self._glyphs = {}
        self.ui_font_small = load_font(max(10, self.font_size - 3), bold=True)
        self.ui_font = load_font(self.font_size, bold=True)
        self.ui_font_big = load_font(self.font_size + 10, bold=True)

    def _set_icon(self):
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(icon, (20, 24, 40), (16, 16), 15)
            pygame.draw.line(icon, (90, 200, 255), (9, 23), (23, 9), 4)
            pygame.draw.line(icon, (230, 250, 255), (9, 23), (23, 9), 2)
            pygame.display.set_icon(icon)
        except Exception:
            pass

    def attach_game(self, game):
        from jedi_fugitive.gfx.world import WorldRenderer
        self.game = game
        self.world = WorldRenderer(self, game)

    # ------------------------------------------------------ console capture
    def install_console_capture(self):
        """Route print()/input() (splash, story, death screens) into the window."""
        if self._console_installed:
            return
        self._console_installed = True
        self._real_stdout = sys.stdout
        self._real_input = builtins.input
        sys.stdout = _Tee(self._real_stdout, self._printed)
        builtins.input = self.console_input

    def uninstall_console_capture(self):
        if not self._console_installed:
            return
        sys.stdout = self._real_stdout
        builtins.input = self._real_input
        self._console_installed = False

    def console_lines(self):
        text = ANSI_ESCAPE.sub("", "".join(self._printed))
        lines = text.split("\n")
        # keep only the most recent screen-worth of output
        return [ln.rstrip() for ln in lines[-400:]]

    def console_input(self, prompt=""):
        """Blocking input() replacement rendered as a full-screen overlay."""
        lines = self.console_lines()
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and not lines[-1].strip():
            lines.pop()
        prompt = ANSI_ESCAPE.sub("", str(prompt)).strip("\n")
        typed = ""
        scroll = None
        while True:
            for ev in self._events():
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self._printed.clear()
                        return typed
                    if ev.key == pygame.K_ESCAPE:
                        self._printed.clear()
                        return "q"
                    if ev.key == pygame.K_BACKSPACE:
                        typed = typed[:-1]
                    elif ev.key in (pygame.K_UP, pygame.K_PAGEUP):
                        scroll = (scroll if scroll is not None else 10 ** 6) - (1 if ev.key == pygame.K_UP else 15)
                    elif ev.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                        scroll = (scroll if scroll is not None else 10 ** 6) + (1 if ev.key == pygame.K_DOWN else 15)
                    elif ev.unicode and ev.unicode.isprintable():
                        typed += ev.unicode
                elif ev.type == pygame.MOUSEWHEEL:
                    scroll = (scroll if scroll is not None else 10 ** 6) - ev.y * 3
            scroll = self._draw_console(lines, prompt, typed, scroll)
            pygame.display.flip()
            self.clock.tick(30)

    def _draw_console(self, lines, prompt, typed, scroll):
        W, H = self.screen.get_size()
        self._draw_background()
        pad = 28
        # choose a font size that fits all lines if possible
        size = self.font_size
        font = self.font
        while size > 10:
            font = load_font(size)
            if (len(lines) + 3) * font.get_linesize() <= H - 2 * pad and \
                    max((font.size(l)[0] for l in lines), default=0) <= W - 2 * pad - 20:
                break
            size -= 1
            font = load_font(size)
        lh = font.get_linesize()
        visible = max(1, (H - 2 * pad) // lh - 3)
        max_scroll = max(0, len(lines) - visible)
        if scroll is None:
            scroll = 0
        scroll = max(0, min(max_scroll, scroll))
        block_w = min(W - 2 * pad, max((font.size(l)[0] for l in lines), default=400) + 48)
        block_h = min(H - 2 * pad, (min(visible, len(lines)) + 3) * lh + 32)
        bx = (W - block_w) // 2
        by = (H - block_h) // 2
        panel = pygame.Surface((block_w, block_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, theme.DIALOG_BG, panel.get_rect(), border_radius=14)
        pygame.draw.rect(panel, theme.PANEL_BORDER, panel.get_rect(), 1, border_radius=14)
        self.screen.blit(panel, (bx, by))
        y = by + 16
        for ln in lines[scroll:scroll + visible]:
            col = theme.DEFAULT_FG
            s = ln.strip()
            if s.startswith(("╔", "║", "╚", "═", "=")):
                col = theme.ANSI[6]
            elif s.isupper() and len(s) > 3:
                col = theme.ANSI[3]
            elif s.startswith(("[DEATH]", "GAME OVER")):
                col = theme.ANSI[1]
            self.screen.blit(font.render(ln, True, col), (bx + 24, y))
            y += lh
        if max_scroll > 0:
            hint = f"{scroll + 1}-{min(len(lines), scroll + visible)} / {len(lines)}  (↑/↓ scroll)"
            self.screen.blit(self.ui_font_small.render(hint, True, theme.PANEL_BORDER), (bx + 24, by + block_h - 2 * lh - 8))
        pulse = 0.6 + 0.4 * abs(((time.time() * 1.2) % 2) - 1)
        p = (prompt or "Press Enter to continue") + (" " + typed if typed else "") + ("▌" if int(time.time() * 2) % 2 else " ")
        self.screen.blit(font.render(p, True, theme.scale(theme.ANSI[6], pulse)), (bx + 24, by + block_h - lh - 12))
        return scroll

    # ------------------------------------------------------------ loading
    def run_loading(self, work, title="GENERATING WORLD"):
        """Run ``work`` in a thread while an animated loading screen keeps the window alive."""
        import threading
        result = {}

        def _target():
            try:
                work()
            except BaseException as e:  # re-raised on the main thread
                result['error'] = e

        th = threading.Thread(target=_target, name="worldgen", daemon=True)
        th.start()
        start = time.perf_counter()
        while th.is_alive():
            self._events()
            self._draw_loading(title, time.perf_counter() - start)
            pygame.display.flip()
            self.clock.tick(30)
        self._printed.clear()
        if 'error' in result:
            raise result['error']

    def _draw_loading(self, title, elapsed):
        self._draw_background()
        W, H = self.screen.get_size()
        cx, cy = W // 2, H // 2 - 20
        # spinning lightsaber
        ang = elapsed * 3.0
        L = 90
        import math
        x0, y0 = cx - math.cos(ang) * L / 2, cy - math.sin(ang) * L / 2
        x1, y1 = cx + math.cos(ang) * L / 2, cy + math.sin(ang) * L / 2
        glow = pygame.Surface((W, H))
        glow.fill((0, 0, 0))
        for w, k in ((22, 0.18), (14, 0.35), (8, 0.6)):
            pygame.draw.line(glow, theme.scale(theme.ANSI[6], k), (x0, y0), (x1, y1), w)
        self.screen.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.line(self.screen, (235, 250, 255), (x0, y0), (x1, y1), 4)
        t = self.ui_font_big.render(title, True, theme.DEFAULT_FG)
        self.screen.blit(t, (cx - t.get_width() // 2, cy + 80))
        lines = [ln.strip() for ln in self.console_lines() if ln.strip()]
        msg = lines[-1] if lines else "..."
        m = self.ui_font_small.render(msg[:140], True, theme.ANSI[3])
        self.screen.blit(m, (cx - m.get_width() // 2, cy + 80 + t.get_height() + 12))
        e = self.ui_font_small.render(f"{elapsed:4.1f}s", True, theme.PANEL_BORDER)
        self.screen.blit(e, (cx - e.get_width() // 2, cy + 80 + t.get_height() + 40))

    # ------------------------------------------------------------- events
    def _events(self):
        out = []
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.quit_requested = True
                raise SystemExit(0)
            if ev.type == pygame.VIDEORESIZE and not self.fullscreen:
                self._handle_resize((ev.w, ev.h))
                continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                self.toggle_fullscreen()
                continue
            out.append(ev)
        return out

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self._handle_resize(self.screen.get_size())

    def _handle_resize(self, size):
        if not self.fullscreen:
            try:
                self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            except Exception:
                pass
        self._bg_cache = None
        self.cols = max(40, self.screen.get_width() // self.cw)
        self.rows = max(20, self.screen.get_height() // self.ch)
        self.stdscr.resize(self.rows, self.cols)
        pgcurses.LINES, pgcurses.COLS = self.rows, self.cols
        if self.on_resize:
            try:
                self.on_resize()
            except Exception:
                pass

    KEYMAP = {
        pygame.K_UP: pgcurses.KEY_UP, pygame.K_DOWN: pgcurses.KEY_DOWN,
        pygame.K_LEFT: pgcurses.KEY_LEFT, pygame.K_RIGHT: pgcurses.KEY_RIGHT,
        pygame.K_RETURN: 10, pygame.K_KP_ENTER: 10, pygame.K_ESCAPE: 27,
        pygame.K_BACKSPACE: pgcurses.KEY_BACKSPACE, pygame.K_TAB: 9,
        pygame.K_HOME: pgcurses.KEY_HOME, pygame.K_END: pgcurses.KEY_END,
        pygame.K_PAGEUP: pgcurses.KEY_PPAGE, pygame.K_PAGEDOWN: pgcurses.KEY_NPAGE,
        pygame.K_DELETE: pgcurses.KEY_DC, pygame.K_INSERT: pgcurses.KEY_IC,
        # numpad: 8/2/4/6 are arrows, diagonals keep their digits (the game maps 7/9/1/3)
        pygame.K_KP8: pgcurses.KEY_UP, pygame.K_KP2: pgcurses.KEY_DOWN,
        pygame.K_KP4: pgcurses.KEY_LEFT, pygame.K_KP6: pgcurses.KEY_RIGHT,
        pygame.K_KP7: ord('7'), pygame.K_KP9: ord('9'), pygame.K_KP1: ord('1'),
        pygame.K_KP3: ord('3'), pygame.K_KP5: ord('5'),
    }

    def pump(self):
        """Process window events and queue key presses as curses key codes."""
        for ev in self._events():
            if ev.type == pygame.KEYDOWN:
                if pygame.K_F1 <= ev.key <= pygame.K_F12:
                    code = pgcurses.KEY_F(ev.key - pygame.K_F1 + 1)
                    if self.on_hotkey and self.on_hotkey(code):
                        continue
                    self.keys.append(code)
                    continue
                code = self.KEYMAP.get(ev.key)
                if code is None and ev.unicode:
                    o = ord(ev.unicode[0])
                    if o >= 32 or 1 <= o <= 26:
                        code = o
                if code is not None:
                    self.keys.append(code)
            elif ev.type == pygame.MOUSEWHEEL and self.world is not None:
                self.world.zoom(ev.y)
        # keep the queue short so held keys never build up a backlog
        while len(self.keys) > 4:
            self.keys.popleft()

    def poll_key(self):
        return self.keys.popleft() if self.keys else -1

    def push_key(self, code):
        self.keys.append(code)

    def flush_input(self):
        self.keys.clear()

    def getch(self, timeout_ms=-1):
        """curses.getch(): blocking (-1), non-blocking (0) or with a timeout."""
        self._printed.clear()
        deadline = None if timeout_ms is None or timeout_ms < 0 else time.perf_counter() + timeout_ms / 1000.0
        while True:
            self.pump()
            if self.keys:
                return self.keys.popleft()
            if self.interrupt_getch:
                self.interrupt_getch = False
                return -1
            if deadline is not None and time.perf_counter() >= deadline:
                self.render_frame_if_due()
                return -1
            self.render_frame()
            self.clock.tick(60)

    def sleep(self, seconds):
        end = time.perf_counter() + max(0.0, seconds)
        while time.perf_counter() < end:
            self.pump()
            self.render_frame()
            self.clock.tick(60)

    def flash(self):
        self._flash_until = time.perf_counter() + 0.12

    # ------------------------------------------------------------ compositor
    def composite(self, win):
        # curses semantics: what is on screen is what was last refreshed, so
        # snapshot the window now and only re-render its surface on change.
        sig = win.signature()
        if sig != win._sig:
            win._sig = sig
            win._snap = ([r[:] for r in win.chars], [r[:] for r in win.attrs],
                         win.framed, win.has_bkgd, win.viewport, win.w, win.h)
            win._surface = None
        rect = (win.x, win.y, win.w, win.h)
        alive = []
        for ref in self.stack:
            w = ref()
            if w is None or w is win:
                continue
            # a window fully covered by the one being refreshed is gone (curses overwrites it)
            if w.x >= rect[0] and w.y >= rect[1] and w.x + w.w <= rect[0] + rect[2] and w.y + w.h <= rect[1] + rect[3]:
                continue
            alive.append(ref)
        alive.append(weakref.ref(win))
        self.stack = alive

    def windows(self):
        out = []
        for ref in self.stack:
            w = ref()
            if w is not None:
                out.append(w)
        return out

    def _colors(self, attr, win_bg):
        pair = pgcurses.pair_number(attr)
        fg_i, bg_i = pgcurses.get_pairs().get(pair, (-1, -1))
        fg = theme.ANSI.get(fg_i, theme.DEFAULT_FG) if fg_i >= 0 else theme.DEFAULT_FG
        bg = None
        if bg_i >= 0:
            # solid ANSI backgrounds are harsh on a dark UI: use deep tinted versions
            base = theme.ANSI.get(bg_i, (40, 40, 60))
            bg = theme.mix(theme.BG_TOP, base, 0.45 if bg_i != 7 else 0.3)
            if fg_i == 0:
                fg = (240, 244, 255)
        bold = bool(attr & (pgcurses.A_BOLD | pgcurses.A_BLINK | pgcurses.A_STANDOUT))
        if attr & pgcurses.A_REVERSE:
            bg, fg = theme.scale(fg, 0.85), (12, 14, 24)
        if bold:
            fg = theme.mix(fg, (255, 255, 255), 0.12)
        if attr & pgcurses.A_DIM:
            fg = theme.mix(fg, win_bg[:3], 0.5)
        return fg, bg, bold, bool(attr & pgcurses.A_UNDERLINE)

    def glyph(self, ch, fg, bold):
        key = (ch, fg, bold)
        surf = self._glyphs.get(key)
        if surf is None:
            font = self.font_bold if bold else self.font
            try:
                m = font.metrics(ch)
                if not m or m[0] is None:
                    font = self.font_fallback
            except Exception:
                font = self.font_fallback
            try:
                surf = font.render(ch, True, fg)
            except Exception:
                surf = self.font.render("?", True, fg)
            if len(self._glyphs) > 6000:
                self._glyphs.clear()
            self._glyphs[key] = surf
        return surf

    def _window_surface(self, win):
        key = (self.cw, self.ch)
        if win._surface is not None and win._surface_key == key:
            return win._surface
        snap = getattr(win, "_snap", None)
        if snap is None:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        chars, attrs, framed, has_bkgd, viewport, ww, wh = snap
        win = _Snap(chars, attrs, framed, has_bkgd, viewport, ww, wh, win)
        cw, ch = self.cw, self.ch
        W, H = win.w * cw, win.h * ch
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        if win.has_bkgd:
            win_bg = theme.DIALOG_BG
        elif win.framed:
            win_bg = theme.PANEL_BG
        else:
            win_bg = (0, 0, 0, 0)
        radius = theme.PANEL_RADIUS
        if win.has_bkgd or win.framed:
            pygame.draw.rect(surf, win_bg, surf.get_rect(), border_radius=radius)
            if win.viewport and win.w > 2 and win.h > 2:
                surf.fill((0, 0, 0, 0), pygame.Rect(cw, ch, (win.w - 2) * cw, (win.h - 2) * ch))
        if win.framed or win.has_bkgd:
            border = theme.DIALOG_BORDER if win.has_bkgd else theme.PANEL_BORDER
            fr = pygame.Rect(cw // 2, ch // 2, W - cw, H - ch)
            pygame.draw.rect(surf, border, fr, 1, border_radius=max(4, radius - 3))
            if win.has_bkgd:
                glow = pygame.Rect(cw // 2 + 1, ch // 2 + 1, W - cw - 2, 2)
                pygame.draw.rect(surf, theme.scale(border, 0.6), glow, border_radius=2)
        # title chips on border rows
        if win.framed:
            for row in (0, win.h - 1):
                x = 0
                cells = win.chars[row]
                while x < win.w:
                    if cells[x] != pgcurses.BORDER_CELL:
                        start = x
                        while x < win.w and cells[x] != pgcurses.BORDER_CELL:
                            x += 1
                        if ''.join(cells[start:x]).strip():
                            chip = pygame.Rect(start * cw - 2, row * ch + 1, (x - start) * cw + 4, ch - 2)
                            pygame.draw.rect(surf, theme.TITLE_BG, chip, border_radius=ch // 2)
                    else:
                        x += 1
        for y in range(win.h):
            row_c = win.chars[y]
            row_a = win.attrs[y]
            py = y * ch
            for x in range(win.w):
                c = row_c[x]
                a = row_a[x]
                if c == pgcurses.BORDER_CELL:
                    continue
                if c == ' ' and a == 0:
                    continue
                fg, bg, bold, underline = self._colors(a, win_bg if len(win_bg) == 4 else (0, 0, 0, 0))
                px = x * cw
                if bg is not None:
                    surf.fill(bg, (px, py, cw, ch))
                block = BLOCKS.get(c)
                if block is not None:
                    # text-mode bars (█░) become clean continuous bar segments
                    bh = max(4, ch // 2)
                    surf.fill(theme.mix((20, 22, 34), fg, block), (px, py + (ch - bh) // 2, cw, bh))
                elif c != ' ':
                    g = self.glyph(c, fg, bold)
                    gx = px + (cw - g.get_width()) // 2 if g.get_width() > cw else px
                    surf.blit(g, (gx, py))
                if underline:
                    pygame.draw.line(surf, fg, (px, py + ch - 2), (px + cw - 1, py + ch - 2))
        win.real._surface = surf
        win.real._surface_key = key
        return surf

    def viewport_rect(self, win):
        return pygame.Rect((win.x + 1) * self.cw, (win.y + 1) * self.ch,
                           max(1, win.w - 2) * self.cw, max(1, win.h - 2) * self.ch)

    # --------------------------------------------------------------- frame
    def _draw_background(self):
        size = self.screen.get_size()
        if self._bg_cache is None or self._bg_cache.get_size() != size:
            bg = pygame.Surface(size)
            W, H = size
            for y in range(H):
                t = y / max(1, H - 1)
                pygame.draw.line(bg, theme.mix(theme.BG_TOP, theme.BG_BOTTOM, t), (0, y), (W, y))
            import random
            rnd = random.Random(7)
            for _ in range(W * H // 5000):
                x, y = rnd.randrange(W), rnd.randrange(H)
                v = rnd.randrange(40, 120)
                bg.set_at((x, y), (v, v, min(255, v + 30)))
            self._bg_cache = bg
        self.screen.blit(self._bg_cache, (0, 0))

    def render_frame_if_due(self):
        if time.perf_counter() - self.last_frame >= 1 / 60.0:
            self.render_frame()

    def render_frame(self):
        now = time.perf_counter()
        dt = min(0.1, now - self.last_frame) if self.last_frame else 1 / 60.0
        self.last_frame = now
        self.frame_dt = dt
        if dt > 0:
            self.fps = self.fps * 0.95 + (1.0 / dt) * 0.05
        self._draw_background()
        wins = self.windows()
        if self.world is not None:
            for w in wins:
                if w.viewport:
                    try:
                        self.world.render(self.screen, self.viewport_rect(w), dt)
                    except Exception as e:  # never let a render bug kill the game
                        self._render_error(e)
                    break
        for w in wins:
            try:
                self.screen.blit(self._window_surface(w), (w.x * self.cw, w.y * self.ch))
            except Exception:
                pass
        if now < self._flash_until:
            s = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            s.fill((255, 255, 255, 40))
            self.screen.blit(s, (0, 0))
        pygame.display.flip()

    def _render_error(self, e):
        try:
            if not getattr(self, "_render_error_logged", False):
                self._render_error_logged = True
                import traceback
                traceback.print_exc(file=sys.stderr)
        except Exception:
            pass

    def save_screenshot(self, path):
        pygame.image.save(self.screen, path)

    def shutdown(self):
        self.uninstall_console_capture()
        try:
            pygame.quit()
        except Exception:
            pass
