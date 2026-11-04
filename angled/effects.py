"""Particles, floating text and fireworks."""
import colorsys
import math
import random

import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max", "color", "size", "g", "drag", "trail")

    def __init__(self, x, y, vx, vy, life, color, size=3, g=300.0, drag=0.0, trail=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max = life
        self.color = color
        self.size = size
        self.g = g
        self.drag = drag
        self.trail = trail


class Effects:
    def __init__(self):
        self.parts = []
        self.texts = []   # [x, y, text, size, color, life, max, vy]
        self.rings = []   # [x, y, r, max_r, life, max, color]

    def burst(self, x, y, color, n=16, speed=220, life=0.6, size=4, g=380):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(speed * 0.35, speed)
            c = tuple(min(255, max(0, int(v + random.randint(-30, 30)))) for v in color)
            self.parts.append(Particle(x, y, math.cos(a) * s, math.sin(a) * s,
                                       random.uniform(life * 0.6, life), c, random.uniform(2, size), g))

    def ring(self, x, y, color, max_r=40, life=0.35):
        self.rings.append([x, y, 4, max_r, life, life, color])

    def text(self, x, y, s, size=26, color=(255, 255, 255), life=1.0, vy=-50):
        self.texts.append([x, y, s, size, color, life, life, vy])

    def clear(self):
        self.parts.clear()
        self.texts.clear()
        self.rings.clear()

    def update(self, dt):
        alive = []
        for p in self.parts:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.g * dt
            if p.drag:
                k = max(0.0, 1 - p.drag * dt)
                p.vx *= k
                p.vy *= k
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.parts = alive
        for t in self.texts:
            t[5] -= dt
            t[1] += t[7] * dt
        self.texts = [t for t in self.texts if t[5] > 0]
        for r in self.rings:
            r[4] -= dt
            r[2] = r[3] * (1 - r[4] / r[5])
        self.rings = [r for r in self.rings if r[4] > 0]

    def draw(self, surf, fonts):
        for r in self.rings:
            a = r[4] / r[5]
            if r[2] > 2:
                col = tuple(int(c * a + 255 * (1 - a) * 0.2) for c in r[6])
                pygame.draw.circle(surf, col, (int(r[0]), int(r[1])), int(r[2]), max(1, int(4 * a)))
        for p in self.parts:
            a = p.life / p.max
            size = max(1, int(p.size * (0.4 + 0.6 * a)))
            col = tuple(int(c * (0.35 + 0.65 * a)) for c in p.color)
            if p.trail:
                pygame.draw.line(surf, col, (int(p.x), int(p.y)),
                                 (int(p.x - p.vx * 0.03), int(p.y - p.vy * 0.03)), max(1, size - 1))
            pygame.draw.circle(surf, col, (int(p.x), int(p.y)), size)
        for t in self.texts:
            a = min(1.0, t[5] / (t[6] * 0.5)) * 255
            fonts.draw(surf, t[2], t[3], (int(t[0]), int(t[1])), t[4], "center",
                       outline=(0, 0, 0), alpha=a)


class Fireworks:
    """Rockets that rise, explode into coloured sparks, and crackle."""

    def __init__(self, w, h, audio=None):
        self.w, self.h = w, h
        self.audio = audio
        self.rockets = []  # [x, y, vx, vy, fuse, color]
        self.fx = Effects()
        self.timer = 0.0
        self.rate = 0.35

    def launch(self, x=None):
        x = x if x is not None else random.uniform(self.w * 0.12, self.w * 0.88)
        hue = random.random()
        col = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.75, 1.0))
        self.rockets.append([x, self.h + 10, random.uniform(-40, 40), random.uniform(-760, -560),
                             random.uniform(0.9, 1.4), col])
        if self.audio:
            self.audio.sfx("fw_launch", 0.35)

    def explode(self, x, y, col):
        kind = random.choice(["sphere", "ring", "double", "willow"])
        n = random.randint(70, 120)
        for i in range(n):
            a = math.tau * i / n + random.uniform(-0.05, 0.05)
            if kind == "ring":
                s = 260
            elif kind == "willow":
                s = random.uniform(80, 220)
            else:
                s = random.uniform(60, 300)
            c = col
            if kind == "double" and i % 2:
                c = (255, 255, 255)
            p = Particle(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(1.0, 2.0),
                         c, random.uniform(2, 4), g=120 if kind != "willow" else 60, drag=1.2, trail=True)
            self.fx.parts.append(p)
        self.fx.ring(x, y, col, 90, 0.4)
        if self.audio:
            self.audio.sfx("fw_boom", 0.7)

    def update(self, dt, auto=True):
        if auto:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = random.uniform(self.rate * 0.4, self.rate * 1.6)
                self.launch()
        for r in self.rockets:
            r[0] += r[2] * dt
            r[1] += r[3] * dt
            r[3] += 260 * dt
            r[4] -= dt
            if random.random() < 0.8:
                self.fx.parts.append(Particle(r[0], r[1], random.uniform(-20, 20), random.uniform(20, 60),
                                              0.35, (255, 200, 120), 2, g=50))
        for r in [r for r in self.rockets if r[4] <= 0 or r[3] > -60]:
            self.explode(r[0], r[1], r[5])
        self.rockets = [r for r in self.rockets if r[4] > 0 and r[3] <= -60]
        self.fx.update(dt)

    def draw(self, surf, fonts):
        for r in self.rockets:
            pygame.draw.circle(surf, (255, 240, 200), (int(r[0]), int(r[1])), 3)
        self.fx.draw(surf, fonts)
