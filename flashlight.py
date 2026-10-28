# -*- coding: utf-8 -*-
"""
flashlight.py — математика «фонарика»: попадает ли точка в конус света.

Конус задаётся тремя величинами:
  * origin — точка, откуда светим (центр игрока);
  * facing — угол взгляда в радианах (куда повёрнут игрок);
  * radius и half_angle_deg — дальность луча и половина угла обзора.

Блок считается освещённым, если одновременно:
  1) расстояние от игрока до блока не больше радиуса R;
  2) угол между вектором взгляда и вектором «игрок -> блок» меньше 30°.
"""

import math


def normalize_angle(angle):
    """Приводит угол в радианах к диапазону [-pi, pi).

    Нужно, чтобы правильно считать разницу углов около границы
    (например, между 350° и 10° разница 20°, а не 340°).
    """
    return (angle + math.pi) % (2 * math.pi) - math.pi


def is_in_light_cone(origin, facing, target, radius, half_angle_deg):
    """Возвращает True, если точка target попадает в конус света."""
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]

    # Шаг 1. Расстояние по теореме Пифагора. Слишком далёкие блоки не светятся.
    distance = math.hypot(dx, dy)
    if distance > radius:
        return False

    # Шаг 2. Угол направления на блок. Ось Y в Pygame направлена вниз,
    # но atan2(dy, dx) используется и для взгляда, и для блока, поэтому
    # углы согласованы между собой.
    angle_to_target = math.atan2(dy, dx)

    # Шаг 3. Разница между взглядом игрока и направлением на блок.
    difference = abs(normalize_angle(angle_to_target - facing))

    # Шаг 4. Блок виден, если разница меньше половины угла обзора.
    return difference <= math.radians(half_angle_deg)


def cone_polygon(origin, facing, radius, half_angle_deg, steps=24):
    """Список вершин многоугольника, которым рисуется конус света.

    Первая вершина — игрок, остальные лежат на дуге радиуса radius
    в секторе facing ± half_angle_deg.
    """
    half = math.radians(half_angle_deg)
    points = [origin]
    for i in range(steps + 1):
        angle = facing - half + (2 * half) * i / steps
        points.append((
            origin[0] + math.cos(angle) * radius,
            origin[1] + math.sin(angle) * radius,
        ))
    return points
