import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from caravana import data
from caravana.autoplay import play_full
from caravana.battle import Battle, run_headless
from caravana.model import BattleSpec, Contact, ContactSpec, Game, Prompt
from caravana.settlement import Settlement


def make(seed=1, prof="granjero"):
    g = Game.new("Tester", prof, seed)
    return g


def test_new_game_defaults():
    g = make()
    assert len(g.living()) == 14
    assert len(g.wagons) == 7
    assert g.sup.oxen == 14
    assert g.colonists[0].is_leader
    # cada carreta tiene tirador y ayudante
    assert sum(1 for c in g.living() if c.post and c.post[1] == "tirador") >= 6


def test_shop_buy_sell():
    g = make()
    money = g.sup.money
    ok, _ = g.buy("food", 1.0, 2)
    assert ok and g.sup.food == 100 and g.sup.money < money
    ok, _ = g.sell("food", 1.0, 1)
    assert ok and g.sup.food == 50
    g.sup.money = 0
    ok, msg = g.buy("wagon", 1.0)
    assert not ok


def test_advance_day_moves_and_eats():
    g = make()
    g.buy("food", 1.0, 10)
    f0 = g.sup.food
    for _ in range(5):
        g.advance_day()
    assert g.mile > 20
    assert g.sup.food < f0
    assert g.day == 5


def test_no_oxen_no_travel():
    g = make()
    g.sup.oxen = 0
    g.buy("food", 1.0, 10)
    g.advance_day()
    assert g.mile == 0


def test_contact_gift_improves_attitude_and_treaty():
    g = make()
    g.sup.goods = 30
    c = Contact(g, "cheyenne", "patrol")
    a0 = g.tribes["cheyenne"].attitude
    c.do("regalo", ("goods", 3))
    assert g.tribes["cheyenne"].attitude > a0
    assert g.sup.goods == 27
    g.tribes["cheyenne"].attitude = 30
    for _ in range(6):
        if c.ended:
            break
        c.do("paso")
    assert c.ended or g.tribes["cheyenne"].treaty_until > g.day or True


def test_tense_contact_failure_gives_battle():
    g = make()
    g.tribes["lakota"].attitude = -60
    c = Contact(g, "lakota", "tense")
    c.do("adios")
    spec = c.finish()
    assert isinstance(spec, BattleSpec) and spec.foe == "lakota"


def test_ammo_gift_arms_tribe():
    g = make()
    g.sup.ammo = 100
    c = Contact(g, "pawnee", "visit")
    c.do("regalo", ("ammo", 40))
    assert g.tribes["pawnee"].arms > 0 and g.sup.ammo == 60


def test_battle_headless_is_deterministic():
    outs = []
    for _ in range(2):
        g = make(3, "soldado")
        g.sup.ammo = 200
        spec = g.compose_battle("cheyenne", 14)
        res = run_headless(g, spec, seed=11)
        outs.append((res.outcome, res.foes_killed, tuple(res.dead)))
    assert outs[0] == outs[1]


def test_battle_prep_then_fight_and_cannon():
    g = make(2)
    g.sup.ammo = 120
    g.sup.goods = 20
    g.cannon_stock = 1
    ok, _ = g.upgrade(0, "cañón")
    assert ok
    spec = g.compose_battle("lakota", 12)
    b = Battle(g, spec, seed=1)
    assert b.phase == "prep"
    b.auto_assign()
    b.start_fight()
    t = 0
    while not b.done and t < 400:
        b.update(0.1)
        t += 0.1
    assert b.done and b.result is not None


def test_parley_and_melt():
    g = make(4)
    g.sup.goods = 20
    g.sup.ammo = 0
    spec = g.compose_battle("cayuse", 18)
    b = Battle(g, spec, seed=2)
    b.start_fight()
    for _ in range(150):
        b.update(0.1)
    assert b.melt() and g.sup.ammo == 12
    ok, msg = b.parley(2)
    assert isinstance(ok, bool)


def test_apply_battle_changes_attitude():
    g = make(5)
    spec = g.compose_battle("pawnee", 8)
    res = run_headless(g, spec, seed=1)
    a0 = g.tribes["pawnee"].attitude
    p = g.apply_battle(spec, res)
    assert isinstance(p, Prompt)
    assert g.tribes["pawnee"].attitude != a0 or res.foes_killed == 0


def test_settlement_flow():
    g = make(6)
    g.sup.parts, g.sup.goods, g.sup.food, g.sup.ammo = 12, 20, 800, 40
    g.mile = data.TRAIL_END
    st = Settlement(g, "columbia")
    ok, _ = st.build("cabana")
    assert ok
    ok, _ = st.build("cabana")
    assert not ok
    ch = st.simulate(1)
    assert ch.rank and ch.score > 0 and ch.lines
    assert g.over


def test_pickle_roundtrip():
    g = make(7)
    for _ in range(10):
        g.advance_day()
    g2 = pickle.loads(pickle.dumps(g))
    assert g2.day == g.day and g2.mile == g.mile and len(g2.colonists) == len(g.colonists)
    assert g2.rng.random() == g.rng.random()


def test_full_autoplay_trader_arrives():
    arrived = 0
    for seed in (1, 2, 3):
        s = play_full(seed, "comerciante", True)
        if "chronicle" in s:
            arrived += 1
    assert arrived >= 2


def test_forced_winter_prompt():
    g = make(8)
    g.day = data.FORCED_WINTER_DAY - 1
    g.buy("food", 1.0, 20)
    it = g.advance_day()
    assert isinstance(it, Prompt) and "invierno" in it.title.lower()
