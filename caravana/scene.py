"""Base de escenas y pila de escenas."""
from __future__ import annotations

import pygame


class Scene:
    overlay = False  # si es True se dibuja encima de la escena anterior

    def __init__(self, app):
        self.app = app

    def enter(self):
        pass

    def resume(self):
        """Se llama cuando la escena vuelve a ser la activa tras hacer pop de otra."""

    def handle(self, ev: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, screen: pygame.Surface):
        pass
