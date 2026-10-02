"""Terminal front-end (curses).  All game rules live in the engine; this file
only maps keys to engine calls and paints :mod:`outbreak.ui.render` views."""
from __future__ import annotations

import curses
import textwrap
from typing import Callable, List, Optional, Sequence, Tuple

from outbreak.content import BRANCHES, PERKS, RECIPES
from outbreak.content.perks import BRANCH_NAMES
from outbreak.engine import cipher, combat, encounters, inventory_ops, services
from outbreak.engine import save as savemod
from outbreak.engine.game import Game
from outbreak.engine.model import Human
from outbreak.ui import render
from outbreak.util import DIRS8, cheb

SIDEBAR_W = 34
LOG_LINES = 6
MIN_W, MIN_H = 80, 24

MOVE_KEYS = {
    curses.KEY_UP: (0, -1), curses.KEY_DOWN: (0, 1), curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0),
    ord("k"): (0, -1), ord("j"): (0, 1), ord("h"): (-1, 0), ord("l"): (1, 0),
    ord("y"): (-1, -1), ord("u"): (1, -1), ord("b"): (-1, 1), ord("n"): (1, 1),
    ord("8"): (0, -1), ord("2"): (0, 1), ord("4"): (-1, 0), ord("6"): (1, 0),
    ord("7"): (-1, -1), ord("9"): (1, -1), ord("1"): (-1, 1), ord("3"): (1, 1),
    curses.KEY_HOME: (-1, -1), curses.KEY_PPAGE: (1, -1), curses.KEY_END: (-1, 1), curses.KEY_NPAGE: (1, 1),
}
ESC = 27
ENTER = (10, 13, curses.KEY_ENTER)

HELP = """\
MOVE        arrows / hjkl / yubn / numpad     WAIT   .  or  5      REST   r
FIGHT       walk into an enemy                FIRE   f (cycle targets with f, fire with Enter)
THROW       t (pick an item, then a spot)     AMPUTATE   x  (only right after a limb bite)
INTERACT    e (crates, bench, people, beds)   PICK UP   g
INVENTORY   i   CRAFT   c   DOCUMENTS   d   SKILLS   p   PLACES   m
SNEAK       s   RUN   R   LIGHT   L   SMEAR WITH GORE   v
SAVE & QUIT Q            HELP  ?

Noise draws the dead. Guns are loud; sneaking and blades are quiet.
Head shots drop most dead. Bite on an arm or leg? Cut it off (x) fast, with a blade.
Documents are written in a cipher: read them, study them, learn words.
Components are in locked vaults at the bottom of certain buildings.
"""


class Colors:
    def __init__(self):
        self.pairs = {}
        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            return
        table = {"white": curses.COLOR_WHITE, "red": curses.COLOR_RED, "green": curses.COLOR_GREEN,
                 "yellow": curses.COLOR_YELLOW, "blue": curses.COLOR_BLUE, "magenta": curses.COLOR_MAGENTA,
                 "cyan": curses.COLOR_CYAN, "grey": curses.COLOR_WHITE}
        for i, (name, col) in enumerate(table.items(), start=1):
            try:
                curses.init_pair(i, col, -1)
                self.pairs[name] = curses.color_pair(i)
            except curses.error:
                pass

    def attr(self, name: str, bold: bool = False) -> int:
        a = self.pairs.get(name, 0)
        if name == "grey":
            a |= curses.A_DIM
        if bold:
            a |= curses.A_BOLD
        return a


class UI:
    def __init__(self, stdscr, game: Game):
        self.s = stdscr
        self.g = game
        self.colors = Colors()
        curses.curs_set(0)
        self.s.keypad(True)
        self.quit = False

    # ------------------------------------------------------------ drawing helpers
    def put(self, y: int, x: int, text: str, color: str = "white", bold: bool = False) -> None:
        h, w = self.s.getmaxyx()
        if y < 0 or y >= h or x >= w:
            return
        try:
            self.s.addstr(y, x, text[: max(0, w - x - (1 if y == h - 1 else 0))], self.colors.attr(color, bold))
        except curses.error:
            pass

    def size(self) -> Tuple[int, int]:
        return self.s.getmaxyx()

    def too_small(self) -> bool:
        h, w = self.size()
        return h < MIN_H or w < MIN_W

    def draw(self, cursor=None, status: str = "") -> None:
        self.s.erase()
        h, w = self.size()
        if self.too_small():
            self.put(0, 0, f"Terminal too small ({w}x{h}); need {MIN_W}x{MIN_H}.", "red")
            self.s.refresh()
            return
        map_w, map_h = w - SIDEBAR_W - 1, h - LOG_LINES - 1
        view = render.build_view(self.g, map_w, map_h, LOG_LINES, w - 2, cursor)
        for y, row in enumerate(view.map_rows):
            for x, (ch, color, bold) in enumerate(row):
                if ch != " ":
                    self.put(y, x, ch, color, bold)
        for y in range(map_h):
            self.put(y, map_w, "|", "grey")
        for i, (text, color) in enumerate(view.side[:map_h]):
            self.put(i, map_w + 2, text[:SIDEBAR_W - 2], color)
        self.put(map_h, 0, "-" * (w - 1), "grey")
        for i, (text, color) in enumerate(view.log):
            self.put(map_h + 1 + i, 1, text, color)
        if status:
            self.put(h - 1, 0, status[:w - 1], "yellow", True)
        self.s.refresh()

    def wait_key(self) -> int:
        return self.s.getch()

    # ------------------------------------------------------------ generic widgets
    def pick(self, title: str, rows: Sequence[Tuple[str, str]], footer: str = "Enter: choose   Esc: back",
             start: int = 0, disabled: Optional[Sequence[bool]] = None, on_key: Optional[Callable] = None) -> Optional[int]:
        """A scrolling list.  Returns the chosen index or None.  ``on_key(key, index)`` may handle extra keys and
        return True to redraw / False to ignore / 'close' to leave."""
        idx = min(max(0, start), max(0, len(rows) - 1))
        top = 0
        while True:
            self.s.erase()
            h, w = self.size()
            self.put(0, 1, title, "yellow", True)
            view_h = h - 4
            if idx < top:
                top = idx
            if idx >= top + view_h:
                top = idx - view_h + 1
            for i in range(view_h):
                j = top + i
                if j >= len(rows):
                    break
                text, color = rows[j]
                dim = bool(disabled and disabled[j])
                prefix = "> " if j == idx else "  "
                self.put(2 + i, 1, (prefix + text)[:w - 2], "grey" if dim else color, j == idx)
            if not rows:
                self.put(2, 2, "(nothing)", "grey")
            self.put(h - 1, 1, footer[:w - 2], "grey")
            self.s.refresh()
            key = self.wait_key()
            if key in (ESC, ord("q")):
                return None
            if key in (curses.KEY_UP, ord("k")) and rows:
                idx = (idx - 1) % len(rows)
            elif key in (curses.KEY_DOWN, ord("j")) and rows:
                idx = (idx + 1) % len(rows)
            elif key in ENTER and rows:
                if not (disabled and disabled[idx]):
                    return idx
            elif on_key is not None and rows:
                r = on_key(key, idx)
                if r == "close":
                    return None

    def text_screen(self, title: str, text: str, footer: str = "Any key") -> int:
        self.s.erase()
        h, w = self.size()
        self.put(0, 1, title, "yellow", True)
        y = 2
        for para in text.split("\n"):
            lines = textwrap.wrap(para, w - 4) or [""]
            for line in lines:
                if y >= h - 2:
                    break
                self.put(y, 2, line)
                y += 1
        self.put(h - 1, 1, footer, "grey")
        self.s.refresh()
        return self.wait_key()

    def message(self, text: str) -> None:
        self.text_screen("", text)

    # ------------------------------------------------------------ main loop
    def run(self) -> None:
        g = self.g
        while not self.quit:
            if g.over:
                self.ending_screen()
                return
            if g.pending_event:
                self.event_screen()
                continue
            self.draw()
            key = self.wait_key()
            if key == curses.KEY_RESIZE:
                continue
            self.handle(key)
        self.autosave()

    def autosave(self) -> None:
        if not self.g.over:
            try:
                savemod.save(self.g)
            except OSError:
                pass

    def handle(self, key: int) -> None:
        g = self.g
        if key in MOVE_KEYS:
            g.move(*MOVE_KEYS[key])
        elif key in (ord("."), ord("5"), curses.KEY_B2):
            g.wait(1)
        elif key == ord("r"):
            g.rest()
        elif key == ord("g"):
            g.pickup()
        elif key == ord("e"):
            self.interact()
        elif key == ord("i"):
            self.inventory_screen()
        elif key == ord("c"):
            self.craft_screen()
        elif key == ord("d"):
            self.documents_screen()
        elif key == ord("p"):
            self.perks_screen()
        elif key == ord("m"):
            self.places_screen()
        elif key == ord("f"):
            self.fire_mode()
        elif key == ord("t"):
            self.throw_mode()
        elif key in (ord("x"), ord("X")):
            g.amputate()
        elif key == ord("s"):
            g.toggle_sneak()
        elif key == ord("R"):
            g.toggle_sprint()
        elif key == ord("L"):
            g.toggle_light()
        elif key == ord("v"):
            g.smear()
        elif key == ord("?"):
            self.text_screen("Help", HELP)
        elif key == ord("Q"):
            self.quit = True

    # ------------------------------------------------------------ interaction
    def interact(self) -> None:
        g = self.g
        what = g.interact()
        if what == "npc":
            self.npc_screen(g.adjacent_npc())
        elif what == "bed":
            self.draw(status="Sleeping...")
            g.sleep()

    def npc_screen(self, npc: Human) -> None:
        g = self.g
        reason = services.refuses(g)
        if reason:
            self.message(f"{npc.name}: {reason}")
            return
        if npc.role == "trader":
            self.trade_screen()
        elif npc.role == "healer":
            r = self.pick(f"{npc.name} - heal for {services.HEAL_COST} {g.era.coin}?",
                          [("Patch me up", "white"), ("Never mind", "grey")])
            if r == 0:
                self.message(services.heal(g))
        elif npc.role == "scholar":
            rows = [(f"Teach me the {g.era.cipher_name.lower()} ({services.TEACH_COST} {g.era.coin}, "
                     f"{services.TEACH_WORDS} words)", "white"),
                    (f"Buy a lead on a building ({services.LEAD_COST} {g.era.coin})", "white"),
                    ("Never mind", "grey")]
            r = self.pick(f"{npc.name}", rows)
            if r == 0:
                self.message(services.teach(g))
            elif r == 1:
                self.message(services.buy_lead(g))

    def trade_screen(self) -> None:
        g = self.g
        while True:
            rows = [("BUY", "yellow")] + [(f"{g.item_def(i).name:<24} {price:>3} {g.era.coin}", "white")
                                         for i, price in services.stock(g)]
            rows.append(("SELL", "yellow"))
            sells = [(i, it) for i, it in enumerate(g.player.inventory) if g.item_def(it.id).kind != "component"
                     and services.sell_price(g, it) > 0]
            rows += [(f"{g.item_def(it.id).name} x{it.qty:<3} {services.sell_price(g, it):>3} {g.era.coin}", "white")
                     for _, it in sells]
            stock = services.stock(g)
            dis = [True] + [False] * len(stock) + [True] + [False] * len(sells)
            r = self.pick(f"Trader   you have {g.player.coins} {g.era.coin}", rows, disabled=dis)
            if r is None:
                return
            if 1 <= r <= len(stock):
                self.message(services.buy(g, stock[r - 1][0]))
            elif r > len(stock) + 1:
                self.message(services.sell(g, sells[r - len(stock) - 2][0]))

    # ------------------------------------------------------------ inventory
    def inventory_screen(self) -> None:
        g, p = self.g, self.g.player
        pos = 0
        while True:
            rows: List[Tuple[str, str]] = []
            for slot, item in (("Hand", p.weapon), ("Wear", p.armor), ("Light", p.light)):
                rows.append((f"[{slot}] " + self._item_text(item), "cyan"))
            for it in p.inventory:
                rows.append((self._item_text(it), "white"))
            n_eq = 3

            def on_key(key, idx, rows=rows):
                if key == ord("d") and idx >= n_eq:
                    g.drop(idx - n_eq)
                    return "close"
                if key == ord("u") and idx < n_eq:
                    g.unequip(("weapon", "armor", "light")[idx])
                    return "close"
                return False

            r = self.pick(f"Inventory  ({len(p.inventory)}/{26} slots)   Enter: use/equip   d: drop   u: unequip",
                          rows, start=pos, on_key=on_key)
            if r is None:
                return
            pos = r
            if r >= n_eq:
                it = p.inventory[r - n_eq]
                d = g.item_def(it.id)
                if d.kind == "throw":
                    self.message("Use 't' on the map to throw it.")
                else:
                    g.use(r - n_eq)
                    self.draw()

    def _item_text(self, item) -> str:
        if item is None:
            return "(empty)"
        d = self.g.item_def(item.id)
        s = d.name
        if item.qty > 1:
            s += f" x{item.qty}"
        if d.durability and item.dur is not None:
            s += f"  ({item.dur}/{d.durability})"
        if d.kind == "weapon":
            s += f"  {d.style} {d.dmg[0]}-{d.dmg[1]}" + (f" reach {d.reach}" if d.reach > 1 else "")
        elif d.kind == "armor":
            s += f"  def {d.defense}, bite guard {int(d.bite_guard * 100)}%"
        return s

    def craft_screen(self) -> None:
        g = self.g
        pos = 0
        while True:
            rows, dis, ids = [], [], []
            for r in RECIPES:
                out = inventory_ops.recipe_output(g, r)
                if out is None:
                    continue
                ok, why = inventory_ops.recipe_status(g, r)
                need = ", ".join(f"{q}x {g.item_def(i).name.lower()}" for i, q in r.inputs)
                rows.append((f"{g.item_def(out).name:<22} {need}" + ("" if ok else f"   ({why})"), "white" if ok else "grey"))
                dis.append(not ok)
                ids.append(r.id)
            idx = self.pick(f"Craft   fluency {int(g.know.fluency * 100)}% in the {g.era.cipher_name.lower()}",
                            rows, start=pos, disabled=dis)
            if idx is None:
                return
            pos = idx
            g.craft(ids[idx])

    # ------------------------------------------------------------ documents and skills
    def documents_screen(self) -> None:
        g, p = self.g, self.g.player
        while True:
            rows = []
            for doc_id in p.documents:
                doc = g.docs[doc_id]
                frac = int(cipher.decoded_fraction(doc, g.know) * 100)
                state = "decoded" if cipher.is_decoded(doc, g.know) else f"{frac}% readable"
                rows.append((f"{doc.title:<18} {state}", "green" if frac >= 60 else "white"))
            r = self.pick(f"Documents   fluency {int(g.know.fluency * 100)}% "
                          f"({len(g.know.known)}/{len(g.know.vocab)} words)", rows,
                          footer="Enter: read   s: study (takes time)   Esc: back",
                          on_key=lambda k, i: self._doc_key(k, i))
            if r is None:
                return
            text, learned = g.read_document(p.documents[r])
            self.text_screen(g.docs[p.documents[r]].title, text, "Any key")

    def _doc_key(self, key: int, idx: int):
        if key == ord("s"):
            doc_id = self.g.player.documents[idx]
            text, _ = self.g.study_document(doc_id)
            self.text_screen("You study the page", text)
            return True
        return False

    def perks_screen(self) -> None:
        g, p = self.g, self.g.player
        while True:
            rows, ids = [], []
            for branch in BRANCHES:
                rows.append((BRANCH_NAMES[branch].upper(), "yellow"))
                ids.append(None)
                for perk in PERKS.values():
                    if perk.branch == branch:
                        rank = p.perks.get(perk.id, 0)
                        rows.append((f"  {perk.name:<16} {rank}/{perk.max_rank}  {perk.desc}", "green" if rank else "white"))
                        ids.append(perk.id)
            style_line = "  ".join(f"{s}:{p.style_rank(s)}" for s in ("blunt", "blade", "polearm", "bow", "firearm", "energy")
                                   if p.style_xp.get(s))
            r = self.pick(f"Skills  ({p.perk_points} points)   weapon mastery: {style_line or 'none yet'}",
                          rows, disabled=[i is None for i in ids])
            if r is None:
                return
            if ids[r] and not g.learn_perk(ids[r]):
                self.message("You cannot learn that (no points, or already at maximum).")

    def places_screen(self) -> None:
        rows = render.places(self.g)
        self.pick("Known places", rows, footer="Esc: back")

    # ------------------------------------------------------------ events and ending
    def event_screen(self) -> None:
        g = self.g
        ev = g.pending_event
        d = ev.definition
        rows = [(c.label.format(**encounters.context(g)), "white") for c in d.choices]
        dis = [not encounters.can_afford(g, c) for c in d.choices]
        self.s.erase()
        h, w = self.size()
        self.put(0, 1, d.title, "yellow", True)
        y = 2
        for line in textwrap.wrap(ev.text, w - 4):
            self.put(y, 2, line)
            y += 1
        y += 1
        idx = 0
        while True:
            for i, (text, color) in enumerate(rows):
                self.put(y + i, 2, ("> " if i == idx else "  ") + text, "grey" if dis[i] else color, i == idx)
            self.s.refresh()
            key = self.wait_key()
            if key in (curses.KEY_UP, ord("k")):
                idx = (idx - 1) % len(rows)
            elif key in (curses.KEY_DOWN, ord("j")):
                idx = (idx + 1) % len(rows)
            elif key in ENTER and not dis[idx]:
                result = g.resolve_event(idx)
                self.message(result)
                return

    def ending_screen(self) -> None:
        g, e = self.g, self.g.over
        lines = [e.text, ""] + e.summary + ["", f"Score: {e.score}"]
        self.text_screen(("VICTORY - " if e.victory else "") + e.title, "\n".join(lines), "Any key to leave")
        if self.g.cfg.permadeath or e.victory:
            savemod.delete()

    # ------------------------------------------------------------ aiming
    def fire_mode(self) -> None:
        g = self.g
        w = combat.weapon_def(g)
        if not w.is_ranged:
            g.msg("You have no ranged weapon equipped.", "warn")
            return
        targets = [a for a in g.visible_hostiles() if cheb(a.pos, g.player.pos) <= w.reach]
        targets.sort(key=lambda a: cheb(a.pos, g.player.pos))
        if not targets:
            g.msg("Nothing in range.", "warn")
            return
        i = 0
        while True:
            t = targets[i]
            self.draw(cursor=t.pos, status=f"Target: {t.name}  (f/Tab: next, Enter: fire, Esc: cancel)")
            key = self.wait_key()
            if key in (ord("f"), 9, curses.KEY_RIGHT, curses.KEY_DOWN):
                i = (i + 1) % len(targets)
            elif key in (curses.KEY_LEFT, curses.KEY_UP):
                i = (i - 1) % len(targets)
            elif key in ENTER:
                g.fire(t)
                return
            elif key == ESC:
                return

    def throw_mode(self) -> None:
        g, p = self.g, self.g.player
        throwables = [(i, it) for i, it in enumerate(p.inventory) if g.item_def(it.id).kind == "throw"]
        if not throwables:
            g.msg("You have nothing to throw.", "warn")
            return
        rows = [(f"{g.item_def(it.id).name} x{it.qty}", "white") for _, it in throwables]
        r = self.pick("Throw what?", rows)
        if r is None:
            return
        item_id = throwables[r][1].id
        cx, cy = p.x, p.y
        while True:
            self.draw(cursor=(cx, cy), status="Aim: arrows move, Enter throws, Esc cancels")
            key = self.wait_key()
            if key in MOVE_KEYS:
                dx, dy = MOVE_KEYS[key]
                nx, ny = cx + dx, cy + dy
                if cheb((nx, ny), p.pos) <= 8:
                    cx, cy = nx, ny
            elif key in ENTER:
                g.throw(item_id, (cx, cy))
                return
            elif key == ESC:
                return


def run_game(game: Game) -> None:
    def main(stdscr):
        UI(stdscr, game).run()

    curses.wrapper(main)
