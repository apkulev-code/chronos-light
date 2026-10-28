# -*- coding: utf-8 -*-
"""
player.py — класс Player: персонаж с фонариком.

Игрок двигается по WASD. Направление взгляда (facing) — это направление
последнего движения: именно туда светит фонарик.
"""

import math

import pygame

from constants import COLORS, PLAYER_SIZE, PLAYER_SPEED


class Player:
    """Игрок: позиция, угол взгляда, движение с проверкой столкновений."""

    def __init__(self, x, y):
        self.x = float(x)                      # центр по X (дробное число для плавности)
        self.y = float(y)                      # центр по Y
        self.facing = 0.0                      # угол взгляда в радианах (0 — вправо)
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = (round(self.x), round(self.y))

    @property
    def center(self):
        """Центр игрока — точка, из которой светит фонарик."""
        return (self.x, self.y)

    def update(self, keys, maze):
        """Читает клавиши WASD, обновляет взгляд и двигает игрока."""
        dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        if dx == 0 and dy == 0:
            return                              # игрок стоит, взгляд не меняется

        # Взгляд поворачивается в сторону движения.
        self.facing = math.atan2(dy, dx)

        # Нормируем вектор, чтобы по диагонали игрок не двигался быстрее.
        length = math.hypot(dx, dy)
        vx = dx / length * PLAYER_SPEED
        vy = dy / length * PLAYER_SPEED

        # Двигаем по осям отдельно: так игрок скользит вдоль стены, а не залипает.
        self._move_axis(vx, 0, maze)
        self._move_axis(0, vy, maze)

    def _move_axis(self, vx, vy, maze):
        """Сдвигает игрока на (vx, vy); если упёрся в стену — отменяет шаг."""
        old_x, old_y = self.x, self.y
        self.x += vx
        self.y += vy
        self.rect.center = (round(self.x), round(self.y))
        if maze.collides(self.rect):
            self.x, self.y = old_x, old_y
            self.rect.center = (round(self.x), round(self.y))

    def draw(self, surface):
        """Рисует игрока кругом."""
        pygame.draw.circle(surface, COLORS["player"], self.rect.center, PLAYER_SIZE // 2)
