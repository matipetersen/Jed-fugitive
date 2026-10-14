import os
import sys

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
pygame = pytest.importorskip("pygame")

from caravana import ui  # noqa: E402
from caravana.app import App  # noqa: E402
from caravana.battle_view import BattleScene  # noqa: E402
from caravana.model import Game  # noqa: E402
from caravana.scenes_defense import DefenseScene  # noqa: E402
from caravana.scenes_menu import SetupScene, TitleScene  # noqa: E402
from caravana.scenes_trade import ShopScene  # noqa: E402
from caravana.scenes_travel import JournalScene, TravelScene  # noqa: E402
from caravana.model import ShopSpec  # noqa: E402


def touch_ev(kind, pos, **kw):
    ev = pygame.event.Event(kind, pos=pos, button=1, touch=True, **kw)
    return ev


def tap(app, pos):
    app.step(1 / 30, [touch_ev(pygame.MOUSEBUTTONDOWN, pos)])
    app.step(1 / 30, [touch_ev(pygame.MOUSEBUTTONUP, pos)])


@pytest.fixture(autouse=True)
def reset_touch():
    ui.TOUCH = False
    yield
    ui.TOUCH = False


def make_app(tmp_path, monkeypatch):
    monkeypatch.setattr("caravana.app.SAVE_PATH", tmp_path / "s.pkl")
    monkeypatch.setattr("caravana.app.SCORES_PATH", tmp_path / "sc.json")
    app = App(headless=True)
    app.game = Game.new("T", "soldado", 3)
    app.game.sup.ammo = 80
    return app


def test_touch_detected_and_finger_events_ignored(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    app.replace(TitleScene(app))
    app.step(1 / 30, [pygame.event.Event(pygame.FINGERDOWN, x=0.5, y=0.5, touch_id=1, finger_id=1, pressure=1.0)])
    assert ui.TOUCH is True
    ui.TOUCH = False
    tap(app, (5, 5))
    assert ui.TOUCH is True


def test_battle_tap_assign_and_unassign(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    g = app.game
    spec = g.compose_battle("pawnee", 8)
    sc = BattleScene(app, g, spec, lambda r: None)
    app.replace(sc)
    tap(app, (700, 600))  # primer toque activa el modo táctil
    assert ui.TOUCH and sc._touch
    rows = sc._roster_rows()
    bc, rect = rows[3]
    bc.ref.post = None
    tap(app, rect.center)
    assert sc.selected is bc
    # toque en la plaza de tirador 0
    sx, sy = sc.cam(*sc.battle.post_pos(0, "ayuda"))
    tap(app, (int(sx) + 10, int(sy) + 8))  # tolerancia táctil
    assert bc.ref.post == (0, "ayuda")
    # seleccionar de nuevo y quitar con el botón
    tap(app, rect.center)
    assert sc.selected is bc
    app.step(1 / 30, [])
    assert sc.unassign_btn.enabled
    tap(app, sc.unassign_btn.rect.center)
    assert bc.ref.post is None and sc.selected is None


def test_battle_roster_drag_scrolls_without_selecting(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    g = app.game
    for i in range(8):  # más colonos que filas visibles
        g._make("adulto", f"Extra {i}")
    sc = BattleScene(app, g, g.compose_battle("pawnee", 6), lambda r: None)
    app.replace(sc)
    ui.TOUCH = True
    sc._build_buttons()
    start = (100, 200)
    app.step(1 / 30, [touch_ev(pygame.MOUSEBUTTONDOWN, start)])
    for k in range(1, 6):
        app.step(1 / 30, [pygame.event.Event(pygame.MOUSEMOTION, pos=(100, 200 - k * 20), rel=(0, -20), buttons=(1, 0, 0), touch=True)])
    app.step(1 / 30, [touch_ev(pygame.MOUSEBUTTONUP, (100, 100))])
    assert sc.roster_scroll > 0
    assert sc.selected is None


def test_defense_unassign_button(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    app.replace(TravelScene(app))
    sc = DefenseScene(app)
    app.push(sc)
    c = next(c for c in app.game.living() if c.post)
    sc.sel_col = c
    tap(app, sc.unassign.rect.center)
    assert c.post is None


def test_shop_bulk_toggle_and_journal_buttons(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    app.replace(ShopScene(app, ShopSpec("Fort", 1.0)))
    sc = app.top
    f0 = app.game.sup.food
    app.game.sup.money = 500
    tap(app, sc.bulk_btn.rect.center)
    assert sc.bulk
    sc._buy("food")
    assert app.game.sup.food == f0 + 250
    app.game.journal += [(i, f'nota {i}') for i in range(40)]
    app.replace(TravelScene(app))
    j = JournalScene(app)
    app.push(j)
    tap(app, j.down.rect.center)
    assert j.scroll > 0


def test_setup_textinput_and_random_name(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    sc = SetupScene(app)
    app.replace(sc)
    tap(app, (300, 140))  # foco en el campo
    assert sc.focus
    sc.name = ""
    app.step(1 / 30, [pygame.event.Event(pygame.TEXTINPUT, text="Ñu")])
    assert sc.name == "Ñu"
    tap(app, sc.rnd.rect.center)
    assert sc.name in SetupScene.NAMES
