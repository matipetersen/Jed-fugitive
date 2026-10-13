"""Jugador automático: sirve para probar y equilibrar el juego sin interfaz."""
from __future__ import annotations

from . import data
from .battle import run_headless
from .model import (ArrivalSpec, BattleSpec, Contact, ContactSpec, EndSpec, ForkSpec, Game, Prompt, ShopSpec,
                    apply_offer, tribe_offers)
from .settlement import Settlement


def shop(g: Game, spec: ShopSpec, rich_ammo: int = 130):
    def buy_to(item, target_units):
        while g.stock_of(item) < target_units:
            ok, _ = g.buy(item, spec.mult)
            if not ok:
                break
    if spec.barter_tribe:
        for off in tribe_offers(g, spec.barter_tribe):
            if off["take"][0] in ("goods",) and g.sup.goods > 10 and off["give"][0] in ("food", "oxen", "medicine", "parts"):
                apply_offer(g, off)
        return
    buy_to("oxen", 7)
    buy_to("food", 30)
    buy_to("medicine", 3)
    buy_to("parts", 4)
    if g.sup.ammo < rich_ammo:
        buy_to("ammo", rich_ammo // 20)
    buy_to("food", 45)
    if g.sup.goods < 20:
        buy_to("goods", 20)


def run_contact(g: Game, cs: ContactSpec):
    c = Contact(g, cs.tribe, cs.kind, cs.prep_text)
    steps = 0
    while not c.ended and steps < 12:
        steps += 1
        a = g.tribes[cs.tribe].attitude
        if "saludo" not in c.used:
            c.used.add("saludo")
            c.do("saludo")
        elif a < 25 and g.sup.goods >= 3:
            c.do("regalo", ("goods", 2))
        elif a < 25 and g.sup.food >= 500:
            c.do("regalo", ("food", 2))
        elif g.day > g.tribes[cs.tribe].treaty_until and g.sup.goods >= 6 and a > -25:
            c.do("paso")
        elif a >= 10 and g.sup.goods >= 14 and not g.has_guide():
            c.do("guia")
        else:
            c.do("adios")
    return c.finish()


def resolve(g: Game, item, diplomacy: bool, stats: dict, seed: int):
    """Resuelve una interrupción hasta que no quede nada pendiente."""
    guard = 0
    while item is not None and guard < 20:
        guard += 1
        if isinstance(item, Prompt):
            item_next = item.options[0].action() if item.options else None
            if item.options and len(item.options) >= 3 and "profundidad" in item.title:
                item_next = item.options[2].action() if g.sup.money > 200 else item.options[1].action()
            elif item.options and item.title.startswith("¡") and len(item.options) == 3:
                item_next = item.options[1].action() if diplomacy else item.options[0].action()
            elif item.options and item.title.startswith("¡Bandoleros"):
                item_next = item.options[0].action()
            item = item_next
        elif isinstance(item, ContactSpec):
            if diplomacy:
                item = run_contact(g, item)
            else:
                item = None
        elif isinstance(item, BattleSpec):
            res = run_headless(g, item, seed + g.day)
            stats.setdefault("battles", []).append((item.foe, round(item.strength, 1), res.outcome, len(res.dead)))
            item = g.apply_battle(item, res)
        elif isinstance(item, ArrivalSpec):
            shop(g, ShopSpec(item.waypoint["name"], item.waypoint["price"], item.waypoint.get("cannon", False)))
            item = None
        elif isinstance(item, ForkSpec):
            return item
        elif isinstance(item, EndSpec):
            return item
        else:
            item = None
    return None


def play_full(seed: int = 1, profession: str = "granjero", diplomacy: bool = True, verbose: bool = False):
    g = Game.new("Jed", profession, seed)
    stats: dict = {}
    # compra inicial
    spec = ShopSpec("Independence", 1.0)
    for item, n in (("food", 36), ("ammo", 7), ("goods", 16), ("parts", 3), ("medicine", 2)):
        for _ in range(n):
            g.buy(item, 1.0)
    end = None
    guard = 0
    last_rest = -99
    while not g.over and guard < 400:
        guard += 1
        if g.pace == "normal" and g.sup.food < 150 and g.sup.money > 40:
            pass
        if g.sup.food < 300 and g.sup.ammo >= 30 and not g.starving:
            resolve(g, g.hunt_day(), diplomacy, stats, seed)
        if (sum(1 for c in g.living() if c.sick) >= 2 or g.morale < 25) and g.day - last_rest > 8 and g.sup.food > 400:
            g.rest_day(2)
            last_rest = g.day
        for i, w in enumerate(g.wagons):
            if w.hp < w.max_hp * 0.6 and g.sup.parts > 0:
                g.repair_wagon(i)
        if any(c.health < 40 for c in g.living()) and g.sup.food > 700 and g.day - last_rest > 8:
            g.rest_day(2)
            last_rest = g.day
        it = g.advance_day()
        nb = len(stats.get("battles", []))
        r = resolve(g, it, diplomacy, stats, seed)
        if len(stats.get("battles", [])) > nb and g.sup.food > 500:
            g.rest_day(3)
            last_rest = g.day
        if isinstance(r, (ForkSpec, EndSpec)):
            end = r
            break
    if isinstance(end, ForkSpec):
        site_id = "improvisado" if g.forced_winter else "walla"
        st = Settlement(g, site_id)
        for key in ("cabana", "pozo", "campos", "empalizada", "tratado", "iglesia", "establo", "puesto"):
            st.build(key)
        ch = st.simulate(seed)
        stats["chronicle"] = ch
    stats["game"] = g
    stats["end"] = end
    return stats
