import pygame
from drawing_surface import DrawingSurface
from pygame import Vector2


class Screen:
    def __init__(self, width, height):
        self.surface = DrawingSurface(
            pygame.display.set_mode((width, height), vsync=1), self, Vector2(0))
        self._previous_dirty_rects = None
        self._current_dirty_rects = []

    def resize(self, width, height):
        self.surface = DrawingSurface(
            pygame.display.set_mode((width, height), vsync=1), Vector2(0))
        self._previous_dirty_rects = None
        self._current_dirty_rects = []

    def update(self):
        """Updates screen."""

        pygame.display.update(self._previous_dirty_rects)
        pygame.display.update(self._current_dirty_rects)
        self._previous_dirty_rects = self._current_dirty_rects
        self._current_dirty_rects = []

    def add_dirty_rect(self, rect):
        """Adds a pygame.Rect to the list of dirty rects"""
        self._current_dirty_rects.append(rect)

    def get_height(self):
        return self.surface.get_height_pixels()
