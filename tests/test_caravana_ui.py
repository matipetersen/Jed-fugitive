import os
import sys

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(__file__))
pygame = pytest.importorskip("pygame")

from uidriver import Driver  # noqa: E402


@pytest.mark.parametrize("seed,prof", [(1, "comerciante"), (2, "granjero"), (3, "medico")])
def test_ui_playthrough_reaches_an_ending(seed, prof, tmp_path, monkeypatch):
    monkeypatch.setattr("caravana.app.SAVE_PATH", tmp_path / "save.pkl")
    monkeypatch.setattr("caravana.app.SCORES_PATH", tmp_path / "scores.json")
    d = Driver(seed, prof).run(max_steps=8000)
    assert "CHRONICLE_RESULT" in d.seen or "ENDSCENE" in d.seen, d.seen
