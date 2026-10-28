# -*- coding: utf-8 -*-
"""
game.py — класс Game: окно, игровой цикл, состояния и отрисовка.

Игровой цикл на каждом кадре делает три вещи:
  1) обрабатывает события (закрытие окна, нажатия клавиш);
  2) обновляет состояние (движение игрока, освещение, сдвиг стен);
  3) рисует кадр.

Состояния игры: MENU (стартовый экран), PLAY (игра), WIN (финиш).
"""

import pygame

from constants import (
    COLORS, FPS, LIGHT_HALF_ANGLE_DEG, LIGHT_POLYGON_STEPS, LIGHT_RADIUS,
    STATE_MENU, STATE_PLAY, STATE_WIN, TILE_SIZE, TITLE,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from flashlight import cone_polygon, is_in_light_cone
from maze import Maze
from player import Player


class Game:
    """Главный класс игры."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Шрифт Arial есть в Windows и поддерживает русский язык.
        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.big_font = pygame.font.SysFont("arial", 56, bold=True)

        # Прозрачный слой для конуса света и полоса под HUD создаются один раз.
        self.light_layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.hud_layer = pygame.Surface((WINDOW_WIDTH, 30), pygame.SRCALPHA)
        self.hud_layer.fill(COLORS["hud_bg"])

        self.state = STATE_MENU
        self.maze = None
        self.player = None
        self.start_time = 0     # момент начала забега (мс)
        self.final_time = 0.0   # итоговое время в секундах
        self.final_shifts = 0   # сколько раз сдвинулись стены за забег

    # ------------------------------------------------------------------
    # Запуск новой игры
    # ------------------------------------------------------------------
    def new_game(self):
        """Создаёт лабиринт и игрока, запускает таймер и переходит в PLAY."""
        now = pygame.time.get_ticks()
        self.maze = Maze(now)
        self.player = Player(*self.maze.start_pixel)
        self.start_time = now
        self.state = STATE_PLAY

    # ------------------------------------------------------------------
    # Главный цикл
    # ------------------------------------------------------------------
    def run(self):
        """Игровой цикл: события -> обновление -> отрисовка."""
        running = True
        while running:
            running = self._handle_events()
            now = pygame.time.get_ticks()
            if self.state == STATE_PLAY:
                self._update(now)
            self._draw(now)
            pygame.display.flip()
            self.clock.tick(FPS)        # не больше FPS кадров в секунду
        pygame.quit()

    # ------------------------------------------------------------------
    # События
    # ------------------------------------------------------------------
    def _handle_events(self):
        """Обрабатывает события. Возвращает False, если нужно выйти."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue

            if self.state == STATE_MENU:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.new_game()
                elif event.key == pygame.K_ESCAPE:
                    return False
            elif self.state == STATE_PLAY:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
            elif self.state == STATE_WIN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
        return True

    # ------------------------------------------------------------------
    # Обновление состояния
    # ------------------------------------------------------------------
    def _update(self, now):
        """Один шаг игры: движение, освещение, сдвиг стен, проверка финиша."""
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.maze)

        # Сначала узнаём, какие стены освещены, потом двигаем остальные.
        self.maze.update_lighting(self.player.center, self.player.facing)
        self.maze.update_dynamic_walls(now, self.player.rect)

        # Игрок дошёл до финиша?
        if self.player.rect.colliderect(self.maze.finish_rect):
            self.final_time = (now - self.start_time) / 1000
            self.final_shifts = self.maze.shift_count
            self.state = STATE_WIN

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------
    def _draw(self, now):
        """Рисует кадр в зависимости от состояния игры."""
        self.screen.fill(COLORS["bg"])
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_PLAY:
            self._draw_play(now)
        elif self.state == STATE_WIN:
            self._draw_win()

    def _draw_text(self, text, font, color, center_y, center_x=WINDOW_WIDTH // 2):
        """Вспомогательная функция: рисует строку по центру."""
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(center_x, center_y))
        self.screen.blit(surface, rect)

    def _draw_menu(self):
        """Стартовый экран с названием и правилами."""
        self._draw_text("СВЕТОВОЙ ЛАБИРИНТ", self.big_font, COLORS["title"], 120)
        lines = [
            "Лабиринт погружён во тьму. Видно только то, что освещает фонарик.",
            "Фонарик светит в ту сторону, куда вы идёте.",
            "Стены, на которые не падает свет, сдвигаются сами.",
            "Найдите зелёный финиш в правом нижнем углу.",
        ]
        for i, line in enumerate(lines):
            self._draw_text(line, self.font, COLORS["text"], 220 + i * 34)
        self._draw_text("WASD — движение     Esc — меню / выход",
                        self.small_font, COLORS["text_dim"], 400)
        self._draw_text("Нажмите Enter, чтобы начать", self.font, COLORS["title"], 480)

    def _draw_play(self, now):
        """Игровой экран: финиш, конус света, освещённые стены, игрок, HUD."""
        # Финиш: слабо светится в темноте, ярко — в луче фонарика.
        finish = self.maze.finish_rect
        in_light = is_in_light_cone(self.player.center, self.player.facing,
                                    finish.center, LIGHT_RADIUS, LIGHT_HALF_ANGLE_DEG)
        finish_color = COLORS["finish_lit"] if in_light else COLORS["finish_dim"]
        pygame.draw.rect(self.screen, finish_color, finish)

        # Конус света — полупрозрачный многоугольник.
        self.light_layer.fill((0, 0, 0, 0))
        points = cone_polygon(self.player.center, self.player.facing, LIGHT_RADIUS,
                              LIGHT_HALF_ANGLE_DEG, LIGHT_POLYGON_STEPS)
        pygame.draw.polygon(self.light_layer, COLORS["light_cone"], points)
        self.screen.blit(self.light_layer, (0, 0))

        # Стены: каждая рисуется, только если lit == True.
        for wall in self.maze.walls:
            wall.draw(self.screen)

        self.player.draw(self.screen)
        self._draw_hud(now)

    def _draw_hud(self, now):
        """Верхняя полоса: время забега и число сдвигов стен."""
        elapsed = (now - self.start_time) / 1000
        self.screen.blit(self.hud_layer, (0, 0))
        text = f"Время: {elapsed:5.1f} с     Сдвигов стен: {self.maze.shift_count}"
        self.screen.blit(self.small_font.render(text, True, COLORS["text"]), (12, 5))
        hint = self.small_font.render("WASD — движение, Esc — меню", True, COLORS["text_dim"])
        self.screen.blit(hint, (WINDOW_WIDTH - hint.get_width() - 12, 5))

    def _draw_win(self):
        """Экран завершения: результат и подсказки."""
        self._draw_text("ВЫ НАШЛИ ВЫХОД!", self.big_font, COLORS["finish_lit"], 170)
        self._draw_text(f"Время: {self.final_time:.1f} с", self.font, COLORS["text"], 270)
        self._draw_text(f"Стены сдвигались: {self.final_shifts} раз",
                        self.font, COLORS["text"], 310)
        self._draw_text("Enter — сыграть ещё раз     Esc — в меню",
                        self.font, COLORS["title"], 430)
