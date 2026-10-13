"""Aplicación principal: ventana, bucle y pila de escenas."""
from __future__ import annotations

import json
import os
import pickle
import sys
from pathlib import Path

import pygame

from . import sfx, ui
from .model import Game
from .scene import Scene

SAVE_PATH = Path(os.environ.get("CARAVANA_SAVE", Path.home() / ".caravana_save.pkl"))
SCORES_PATH = Path(os.environ.get("CARAVANA_SCORES", Path.home() / ".caravana_scores.json"))


class App:
    def __init__(self, headless: bool = False):
        pygame.init()
        pygame.display.set_caption("LA CARAVANA — Hacia el Oeste")
        flags = pygame.SCALED | pygame.RESIZABLE if not headless else 0
        try:
            self.screen = pygame.display.set_mode((ui.W, ui.H), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode((ui.W, ui.H))
        self.clock = pygame.time.Clock()
        self.scenes: list[Scene] = []
        self.game: Game | None = None
        self.travel = None
        self.running = True
        self.fps = 60
        sfx.init()

    # ------------------------------------------------------------ pila de escenas
    def push(self, scene: Scene):
        self.scenes.append(scene)
        scene.enter()

    def pop(self):
        if self.scenes:
            self.scenes.pop()
        if self.scenes:
            self.scenes[-1].resume()

    def replace(self, scene: Scene):
        self.scenes = []
        self.push(scene)

    @property
    def top(self) -> Scene | None:
        return self.scenes[-1] if self.scenes else None

    # ------------------------------------------------------------ interrupciones del juego
    def handle_interrupt(self, it):
        if self.travel is not None:
            self.travel.handle_interrupt(it)

    # ------------------------------------------------------------ guardado
    def save_exists(self) -> bool:
        return SAVE_PATH.exists()

    def autosave(self):
        if self.game is None or self.game.over:
            return
        try:
            with open(SAVE_PATH, "wb") as f:
                pickle.dump(self.game, f)
        except Exception:
            pass

    def load_save(self) -> Game | None:
        try:
            with open(SAVE_PATH, "rb") as f:
                g = pickle.load(f)
            return g if isinstance(g, Game) else None
        except Exception:
            return None

    def clear_save(self):
        try:
            SAVE_PATH.unlink()
        except Exception:
            pass

    def add_score(self, name: str, score: int, rank: str):
        try:
            data = []
            if SCORES_PATH.exists():
                data = json.loads(SCORES_PATH.read_text())
            data.append(dict(name=name, score=score, rank=rank))
            data = sorted(data, key=lambda d: -d["score"])[:10]
            SCORES_PATH.write_text(json.dumps(data))
        except Exception:
            pass

    def scores(self) -> list:
        try:
            return json.loads(SCORES_PATH.read_text())
        except Exception:
            return []

    # ------------------------------------------------------------ bucle
    def draw(self):
        # se dibuja desde la última escena opaca
        start = 0
        for i in range(len(self.scenes) - 1, -1, -1):
            if not self.scenes[i].overlay:
                start = i
                break
        for sc in self.scenes[start:]:
            sc.draw(self.screen)

    def step(self, dt: float, events=None):
        for ev in (events if events is not None else pygame.event.get()):
            if ev.type == pygame.QUIT:
                self.running = False
            elif self.scenes:
                self.scenes[-1].handle(ev)
        if self.scenes:
            self.scenes[-1].update(dt)
        self.draw()

    def run(self):
        from .scenes_menu import TitleScene
        self.replace(TitleScene(self))
        while self.running:
            dt = min(0.05, self.clock.tick(self.fps) / 1000.0)
            self.step(dt)
            pygame.display.flip()
        pygame.quit()


def main():
    App().run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
