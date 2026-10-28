# -*- coding: utf-8 -*-
"""
maze.py — класс Maze: матрица лабиринта, список стен, освещение и движение
динамических стен.

Матрица self.matrix — это двумерный список чисел (типы блоков из constants.py).
Параллельно хранится список объектов Wall: по матрице удобно проверять
свободные клетки, а по объектам — рисовать и считать освещение.
"""

import pygame

from constants import (
    CHAR_TO_TILE, DYNAMIC_WALL_INTERVAL_MS, GRID_COLUMNS, LEVEL_LAYOUT,
    LIGHT_HALF_ANGLE_DEG, LIGHT_RADIUS, TILE_DYNAMIC, TILE_EMPTY,
    TILE_FINISH, TILE_SIZE, TILE_START, TILE_WALL,
)
from flashlight import is_in_light_cone
from wall import Wall


class Maze:
    """Лабиринт с обычными и динамическими стенами."""

    def __init__(self, now):
        self.matrix = []            # матрица чисел (типы блоков)
        self.walls = []             # все стены в виде объектов Wall
        self.start_cell = (1, 1)    # (столбец, строка) старта
        self.finish_cell = (1, 1)   # (столбец, строка) финиша
        self.shift_count = 0        # сколько раз динамические стены сдвинулись
        self._build(now)

    # ------------------------------------------------------------------
    # Построение лабиринта из текстовой карты
    # ------------------------------------------------------------------
    def _build(self, now):
        """Превращает строки LEVEL_LAYOUT в матрицу чисел и объекты Wall."""
        for row, line in enumerate(LEVEL_LAYOUT):
            matrix_row = []
            for col, char in enumerate(line):
                tile = CHAR_TO_TILE[char]
                matrix_row.append(tile)

                if tile == TILE_WALL:
                    self.walls.append(Wall(col, row, dynamic=False))
                elif tile == TILE_DYNAMIC:
                    wall = Wall(col, row, dynamic=True)
                    wall.last_move_time = now   # отсчёт до первого сдвига
                    self.walls.append(wall)
                elif tile == TILE_START:
                    self.start_cell = (col, row)
                elif tile == TILE_FINISH:
                    self.finish_cell = (col, row)
            self.matrix.append(matrix_row)

    # ------------------------------------------------------------------
    # Геометрия
    # ------------------------------------------------------------------
    @property
    def start_pixel(self):
        """Центр стартовой клетки в пикселях."""
        col, row = self.start_cell
        return (col * TILE_SIZE + TILE_SIZE // 2, row * TILE_SIZE + TILE_SIZE // 2)

    @property
    def finish_rect(self):
        """Прямоугольник финиша в пикселях."""
        col, row = self.finish_cell
        return pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def collides(self, rect):
        """True, если прямоугольник пересекается хотя бы с одной стеной."""
        return any(wall.rect.colliderect(rect) for wall in self.walls)

    # ------------------------------------------------------------------
    # Освещение
    # ------------------------------------------------------------------
    def update_lighting(self, origin, facing_angle):
        """Для каждой стены вычисляет, попала ли она в конус света (lit)."""
        for wall in self.walls:
            wall.lit = is_in_light_cone(origin, facing_angle, wall.center,
                                        LIGHT_RADIUS, LIGHT_HALF_ANGLE_DEG)

    # ------------------------------------------------------------------
    # Движение динамических стен
    # ------------------------------------------------------------------
    def update_dynamic_walls(self, now, player_rect):
        """Сдвигает неосвещённые динамические стены на 1 клетку по таймеру.

        Правила:
          * стена двигается, только если lit == False;
          * сдвиг происходит раз в DYNAMIC_WALL_INTERVAL_MS миллисекунд;
          * стена идёт влево/вправо; если впереди препятствие — разворачивается;
          * на клетку, где стоит игрок, стена не заходит.
        """
        for wall in self.walls:
            if not wall.dynamic or wall.lit:
                continue
            if now - wall.last_move_time < DYNAMIC_WALL_INTERVAL_MS:
                continue

            wall.last_move_time = now
            new_col = wall.col + wall.direction

            if self._can_move_to(new_col, wall.row, player_rect):
                # Обновляем матрицу: старую клетку освобождаем, новую занимаем.
                self.matrix[wall.row][wall.col] = TILE_EMPTY
                wall.col = new_col
                self.matrix[wall.row][wall.col] = TILE_DYNAMIC
                self.shift_count += 1
            else:
                wall.direction *= -1    # упёрлись — идём в другую сторону

    def _can_move_to(self, col, row, player_rect):
        """Можно ли динамической стене занять клетку (col, row)."""
        if not 0 <= col < GRID_COLUMNS:
            return False
        if self.matrix[row][col] != TILE_EMPTY:    # занято стеной, стартом или финишем
            return False
        tile_rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        return not tile_rect.colliderect(player_rect)
