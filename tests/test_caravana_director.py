import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from caravana import story
from caravana.battle import Battle
from caravana.director import Director
from caravana.model import Game


def make(seed=1, prof="granjero", diff="normal"):
    g = Game.new("T", prof, seed, diff)
    g.sup.food, g.sup.ammo = 2000, 150
    return g


def test_tension_rises_with_hunger_losses_and_falls_when_calm():
    g = make()
    for _ in range(20):
        g.director.update(g)
    calm = g.director.tension
    g.sup.food, g.sup.ammo = 30, 5
    for c in g.living():
        c.health = 40
    g.stats["lost"] += 2
    g.director.last_battle_day = g.day
    for _ in range(20):
        g.director.update(g)
    assert g.director.tension > calm + 0.35
    assert g.director.raid_mult(g) < 1.0


def test_calm_player_gets_more_pressure():
    g = make()
    g.day = 40
    g.director.last_battle_day = 0
    for _ in range(30):
        g.director.update(g)
    assert g.director.tension < 0.2
    assert g.director.raid_mult(g) > 1.2
    assert g.director.strength_mult(g) > 1.0


def test_grace_period_after_defeat():
    g = make()
    g.director.last_defeat_day = g.day
    assert g.director.raid_mult(g) <= 0.6


def test_difficulty_changes_mercy():
    easy, hard = make(diff="facil"), make(diff="dificil")
    for g in (easy, hard):
        g.director.tension = 0.8
        g.director.last_defeat_day = -99
    assert easy.director.raid_mult(easy) < hard.director.raid_mult(hard)


def test_disabled_director_is_neutral():
    g = make()
    g.director.enabled = False
    g.director.tension = 0.9
    assert g.director.raid_mult(g) == 1.0 and g.director.strength_mult(g) == 1.0
    assert g.director.allow_story(g)


def test_story_postponed_but_never_forever():
    g = make()
    g.mile = 200
    g.director.tension = 0.95
    calls = 0
    for _ in range(14):
        g.director.tension = 0.95
        if story.check(g) is not None:
            break
        calls += 1
    assert 1 <= calls <= 12
    assert any("pospuesto" in t for _, t in g.director.log)


def test_reweight_favors_relief_when_stressed():
    g = make()

    def _ev_bison():
        pass

    def _ev_wheel():
        pass
    table = [(_ev_bison, 3), (_ev_wheel, 3)]
    g.director.tension = 0.9
    hi = dict((f.__name__, w) for f, w in g.director.reweight(g, table))
    g.director.tension = 0.0
    lo = dict((f.__name__, w) for f, w in g.director.reweight(g, table))
    assert hi["_ev_bison"] > lo["_ev_bison"] and hi["_ev_wheel"] < lo["_ev_wheel"]


def test_wave_pulled_forward_when_previous_dead_and_delayed_when_overwhelmed():
    g = make(2, "soldado")
    spec = g.compose_battle("cheyenne", 22)
    assert len(spec.waves) >= 2
    b = Battle(g, spec, seed=3)
    b.start_fight()
    b.auto_assign()
    for _ in range(600):
        b.update(0.1)
        if b.done:
            break
    assert b.done

    # presión alta -> retrasa
    g2 = make(3)
    spec2 = g2.compose_battle("cheyenne", 26)
    b2 = Battle(g2, spec2, seed=1)
    b2.start_fight()
    for w in b2.wagons[:5]:
        w.destroyed = True
    for c in b2.colonists[:8]:
        c.ref.health = 10
    first_due = b2.pending[1][0] if len(b2.pending) > 1 else b2.pending[0][0]
    b2.fight_time = first_due + 0.1
    assert g2.director.wave_decision(b2, first_due) == "wait"
    assert b2.wave_shift == 7.0


def test_old_saves_get_a_director():
    g = make()
    st = g.__dict__.copy()
    del st["director"]
    g2 = Game.__new__(Game)
    g2.__setstate__(st)
    assert isinstance(g2.director, Director)
    g3 = pickle.loads(pickle.dumps(g))
    assert g3.director.tension == g.director.tension
