import os
import pickle
import sys

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from caravana import cutscenes, origin, story  # noqa: E402
from caravana.model import CutsceneSpec, Game, Prompt  # noqa: E402
from caravana.settlement import Settlement  # noqa: E402


def make(seed=1, prof="granjero"):
    return Game.new("T", prof, seed)


# ------------------------------------------------------------------ origen
@pytest.mark.parametrize("motive", list(origin.MOTIVES))
def test_every_origin_applies(motive):
    g = make()
    m0 = g.sup.money
    origin.apply_origin(g, motive, "granja")
    assert g.flags["motive"] == motive and g.flags["promise"] == origin.MOTIVES[motive]["promise"]
    if motive == "deudas":
        assert g.sup.money == m0 + 180
    if motive == "oro":
        assert g.sup.goods >= 6 and g.sup.money == m0 + 60
    if motive == "fe":
        assert g.sup.medicine >= 2 and g.tribes["lakota"].attitude > -10 + 2


def test_purpose_affects_site_and_scoring():
    g = make(2)
    origin.apply_origin(g, "tierra", "fortaleza")
    g.sup.parts, g.sup.goods, g.sup.food, g.sup.ammo = 12, 20, 900, 60
    st = Settlement(g, "columbia")
    assert st.site["defense"] == data_defense("columbia") + 2
    assert st.build("empalizada")[0]
    ch = st.simulate(1)
    assert any(lbl == "Propósito cumplido" for lbl, _ in ch.breakdown)


def data_defense(site):
    from caravana import data
    return data.SITES[site]["defense"]


# ------------------------------------------------------------------ reclutamiento
def test_candidates_are_deterministic_and_varied():
    a = [c["tpl"]["id"] for c in origin.make_candidates(make(5))]
    b = [c["tpl"]["id"] for c in origin.make_candidates(make(5))]
    c = [c["tpl"]["id"] for c in origin.make_candidates(make(6))]
    assert a == b and len(set(a)) == 6 and a != c


def test_hire_persuade_and_limits():
    g = make(3)
    origin.apply_origin(g, "oro", "comercio")
    r = origin.Recruitment(g)
    assert r.approaches >= 4
    n0 = len(g.living())
    i = next(i for i, c in enumerate(r.cands) if c["tpl"]["fee"] > 0)
    money = g.sup.money
    ok, msg = r.hire(i)
    assert ok and len(g.living()) >= n0 + 1 and g.sup.money == money - r.cands[i]["tpl"]["fee"]
    new = g.by_role(r.cands[i]["tpl"]["id"])
    assert new is not None and new.loyalty <= 45 and new.trait
    # no se puede reclutar dos veces
    assert not r.hire(i)[0]
    # límite de sitio
    for _ in range(30):
        g._make("adulto", "Relleno")
    j = next(j for j, c in enumerate(r.cands) if c["state"] == "libre")
    assert not r.persuade(j)[0]


def test_persuasion_uses_motive_affinity():
    g = make(4)
    r = origin.Recruitment(g)
    i = next(i for i, c in enumerate(r.cands) if "faith" in c["tpl"]["likes"])
    p0 = r.persuade_chance(i)
    origin.apply_origin(g, "fe", "comunidad")
    assert r.persuade_chance(i) > p0


def test_mercenary_deserts_when_disloyal():
    g = make(7)
    origin.join(g, next(t for t in origin.CANDIDATES if t["id"] == "mercenario"), 10)
    g.sup.food = 5000
    gone = False
    for _ in range(400):
        g._desertions()
        if g.member("mercenario") is None:
            gone = True
            break
    assert gone


def test_recruit_chapters_run():
    g = make(8)
    origin.join(g, next(t for t in origin.CANDIDATES if t["id"] == "mercenario"), 40)
    origin.join(g, next(t for t in origin.CANDIDATES if t["id"] == "medico"), 40)
    g.sup.money, g.sup.medicine, g.mile = 100, 5, 1600
    for key in ("cobb_paga", "finch_cayuse"):
        ch = next(c for c in story.CHAPTERS if c[0] == key)
        assert ch[1](g)
        for i in range(len(ch[2](g).options)):
            g2 = pickle.loads(pickle.dumps(g))
            res = ch[2](g2).options[i].action()
            while isinstance(res, Prompt):
                res = res.options[0].action()


# ------------------------------------------------------------------ cutscenes
def test_all_cutscenes_build_with_valid_backdrops():
    from caravana.cutscene_art import _build
    g = make(9)
    origin.apply_origin(g, "fe", "comunidad")
    origin.join(g, next(t for t in origin.CANDIDATES if t["id"] == "mercenario"), 40)
    origin.join(g, next(t for t in origin.CANDIDATES if t["id"] == "medico"), 40)
    seen = set()
    for key in cutscenes.SCENES:
        cs = cutscenes.build(key, g)
        assert isinstance(cs, CutsceneSpec) and len(cs.beats) >= 3, key
        for b in cs.beats:
            assert b.text and b.mood in ("neutral", "alegre", "risa", "triste", "enojado", "miedo", "serio")
            for r in b.cast:
                assert g.member(r) is not None
            seen.add(b.bg)
    for bg in seen:
        assert _build(bg).get_size()[1] == 720


def test_cutscene_prologue_depends_on_motive():
    g = make(10)
    origin.apply_origin(g, "deudas", "granja")
    txt = " ".join(b.text for b in cutscenes.build("prologue", g).beats)
    assert "alguaciles" in txt
    g2 = make(10)
    origin.apply_origin(g2, "tierra", "granja")
    assert "320 acres" in " ".join(b.text for b in cutscenes.build("prologue", g2).beats)


def test_story_check_returns_cutscene_then_prompt():
    g = make(11)
    g.mile = 150
    g.flags["cutscenes"] = True
    it = story.check(g, scenes=True)
    assert isinstance(it, CutsceneSpec)
    p = it.then()
    assert isinstance(p, Prompt) and p.title.startswith("Samuel")
    g2 = make(11)
    g2.mile = 150
    g2.flags["cutscenes"] = False
    assert isinstance(story.check(g2, scenes=True), Prompt)


def test_cutscene_scene_plays_through_and_calls_then(tmp_path, monkeypatch):
    import pygame
    from caravana.app import App
    from caravana.scenes_cutscene import CutsceneScene
    from caravana.scenes_travel import TravelScene
    monkeypatch.setattr("caravana.app.SAVE_PATH", tmp_path / "s.pkl")
    monkeypatch.setattr("caravana.app.SCORES_PATH", tmp_path / "sc.json")
    app = App(headless=True)
    g = app.game = make(12)
    origin.apply_origin(g, "tierra", "granja")
    app.replace(TravelScene(app))
    got = []
    cs = cutscenes.build("samuel_noche", g)
    cs.then = lambda: got.append(1)
    app.push(CutsceneScene(app, cs))
    sc = app.top
    for _ in range(80):
        app.step(1 / 30, [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(600, 300), button=1)])
        if app.top is not sc:
            break
    assert got == [1] and isinstance(app.top, TravelScene)
    # saltar
    cs2 = cutscenes.build("eli_roca", g)
    cs2.then = lambda: got.append(2)
    app.push(CutsceneScene(app, cs2))
    app.top.finish()
    assert got == [1, 2]


def test_portraits_render_all_roles_and_moods():
    import pygame
    from caravana import art
    pygame.init()
    s = pygame.Surface((400, 500))
    for role in list(art.PORTRAIT_STYLES) + ["lider", "x"]:
        for mood in ("neutral", "alegre", "risa", "triste", "enojado", "miedo"):
            art.draw_portrait(s, 200, 480, 400, role, "adulto", 3, mood, speaking=True, t=0.4)
    art.draw_portrait(s, 200, 480, 400, "lider", back=True)
