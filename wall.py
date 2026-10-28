# -*- coding: utf-8 -*-
"""
wall.py — класс Wall, один блок стены лабиринта.

У стены есть позиция в матрице (col, row), признак dynamic (двигается ли она)
и признак lit (освещена ли она фонариком в данный момент).
"""

import random

import pygame

from constants import COLORS, TILE_SIZE


class Wall:
    """Блок стены. Может быть статичным или динамическим."""

    def __init__(self, col, row, dynamic=False):
        self.col = col              # номер столбца в матрице
        self.row = row              # номер строки в матрице
        self.dynamic = dynamic      # True — стена двигается, пока её не видно
        self.lit = False            # True — стена сейчас в луче фонарика
        self.direction = random.choice((-1, 1))  # куда сдвигается: -1 влево, +1 вправо
        self.last_move_time = 0     # когда стена двигалась в последний раз (мс)

    @property
    def rect(self):
        """Прямоугольник стены в пикселях (нужен для столкновений и рисования)."""
        return pygame.Rect(self.col * TILE_SIZE, self.row * TILE_SIZE,
                           TILE_SIZE, TILE_SIZE)

    @property
    def center(self):
        """Центр стены в пикселях — точка, которую проверяет фонарик."""
        return (self.col * TILE_SIZE + TILE_SIZE / 2,
                self.row * TILE_SIZE + TILE_SIZE / 2)

    def draw(self, surface):
        """Рисует стену, только если на неё падает свет."""
        if not self.lit:
            return
        color = COLORS["wall_dynamic"] if self.dynamic else COLORS["wall_static"]
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLORS["wall_border"], self.rect, 2)
