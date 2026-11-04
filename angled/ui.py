"""Shared drawing helpers: background, bubbles, panels, launcher, menus."""
import colorsys
import math
import random

import pygame

from .config import BG_BOTTOM, BG_TOP, R, SCREEN_H, SCREEN_W, WHITE

_bubble_cache = {}
_bg_cache = {}


def label_color(label):
    hue = (max(0, min(180, label)) / 180.0) * 0.82
    r, g, b = colorsys.hsv_to_rgb(hue, 0.72, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def bubble_surface(label, fonts, radius=R, ghost=False):
    key = (label, radius, ghost)
    s = _bubble_cache.get(key)
    if s is not None:
        return s
    col = label_color(label) if label is not None else (235, 240, 255)
    d = radius * 2 + 4
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    steps = radius
    for i in range(steps, 0, -1):
        t = i / steps
        shade = 0.55 + 0.45 * (1 - t) ** 0.7
        cc = tuple(min(255, int(v * shade + (255 - v) * (1 - t) ** 3 * 0.35)) for v in col)
        pygame.draw.circle(s, cc, (c, c), i)
    pygame.draw.circle(s, tuple(int(v * 0.45) for v in col), (c, c), radius, 2)
    hl = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 120),
                        (c - radius * 0.62, c - radius * 0.78, radius * 0.75, radius * 0.45))
    s.blit(hl, (0, 0))
    if label is not None:
        txt = "%d°" % label
        size = 16 if len(txt) <= 3 else 14
        if radius < R:
            size = max(9, int(size * radius / R))
        fonts.draw(s, txt, size, (c + 1, c + 1), WHITE, "center", outline=(20, 20, 40), ow=2)
    if ghost:
        s.set_alpha(110)
    _bubble_cache[key] = s
    return s


def draw_bubble(surf, label, x, y, fonts, scale=1.0, alpha=None):
    b = bubble_surface(label, fonts)
    if scale != 1.0:
        w = max(2, int(b.get_width() * scale))
        b = pygame.transform.smoothscale(b, (w, w))
    if alpha is not None:
        b = b.copy()
        b.set_alpha(int(alpha))
    surf.blit(b, b.get_rect(center=(int(x), int(y))))


def background(w=SCREEN_W, h=SCREEN_H, top=BG_TOP, bottom=BG_BOTTOM):
    key = (w, h, top, bottom)
    s = _bg_cache.get(key)
    if s is None:
        s = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(s, col, (0, y), (w, y))
        rnd = random.Random(7)
        for _ in range(90):  # faint stars / bubbles
            x, y = rnd.randrange(w), rnd.randrange(h)
            r = rnd.choice([1, 1, 1, 2])
            pygame.draw.circle(s, (120, 140, 220), (x, y), r)
        for _ in range(14):
            x, y = rnd.randrange(w), rnd.randrange(h)
            r = rnd.randint(14, 40)
            pygame.draw.circle(s, (60, 70, 150), (x, y), r, 1)
        _bg_cache[key] = s
    return s


def panel(surf, rect, color=(16, 20, 50), border=(90, 110, 210), alpha=215, radius=14, width=2):
    rect = pygame.Rect(rect)
    p = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(p, (*color, alpha), p.get_rect(), border_radius=radius)
    surf.blit(p, rect.topleft)
    if border:
        pygame.draw.rect(surf, border, rect, width, border_radius=radius)


def dim(surf, alpha=150):
    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 10, alpha))
    surf.blit(s, (0, 0))


def draw_launcher(surf, fonts, x, y, angle, color=(255, 230, 90), show_scale=True, loaded=True,
                  label_size=26):
    """Arrow launcher with a protractor scale."""
    if show_scale:
        rad = 64
        arc_rect = pygame.Rect(0, 0, rad * 2, rad * 2)
        arc_rect.center = (int(x), int(y))
        pygame.draw.arc(surf, (90, 110, 190), arc_rect, 0, math.pi, 2)
        for a in range(0, 181, 15):
            ca, sa = math.cos(math.radians(a)), -math.sin(math.radians(a))
            ln = 9 if a % 45 == 0 else 5
            pygame.draw.line(surf, (110, 130, 210), (x + ca * rad, y + sa * rad),
                             (x + ca * (rad - ln), y + sa * (rad - ln)), 2 if a % 45 == 0 else 1)
            if a % 45 == 0:
                fonts.draw(surf, str(a), 11, (x + ca * (rad + 12), y + sa * (rad + 10)),
                           (140, 160, 230), "center")
    # base
    pygame.draw.circle(surf, (60, 70, 130), (int(x), int(y)), 20)
    pygame.draw.circle(surf, (150, 170, 240), (int(x), int(y)), 20, 2)
    ca, sa = math.cos(math.radians(angle)), -math.sin(math.radians(angle))
    tip = (x + ca * 58, y + sa * 58)
    pygame.draw.line(surf, color, (x, y), tip, 6)
    px, py = -sa, ca
    head = [(tip[0] + ca * 14, tip[1] + sa * 14), (tip[0] + px * 9, tip[1] + py * 9),
            (tip[0] - px * 9, tip[1] - py * 9)]
    pygame.draw.polygon(surf, color, head)
    if loaded:
        pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)), 12)
        pygame.draw.circle(surf, (190, 220, 255), (int(x), int(y)), 12, 2)
    # angle readout
    fonts.draw(surf, "%d°" % round(angle), label_size, (x, y + 36), color, "center", outline=(0, 0, 0))


def dashed_polyline(surf, pts, color, dash=10, gap=7, width=3):
    carry = 0.0
    on = True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg < 1e-6:
            continue
        ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
        pos = 0.0
        while pos < seg:
            length = (dash if on else gap) - carry
            end = min(seg, pos + length)
            if on:
                pygame.draw.line(surf, color, (x0 + ux * pos, y0 + uy * pos),
                                 (x0 + ux * end, y0 + uy * end), width)
            used = end - pos
            if used < length:
                carry += used
            else:
                carry = 0.0
                on = not on
            pos = end


class Menu:
    """Simple vertical menu with keyboard + mouse support."""

    def __init__(self, items, x, y, spacing=44, size=28, anchor="midleft", width=460):
        self.items = items  # list of dicts: {id, label(fn), enabled(fn)}
        self.x, self.y = x, y
        self.spacing = spacing
        self.size = size
        self.anchor = anchor
        self.width = width
        self.index = 0
        self.rects = []

    def visible(self):
        return [it for it in self.items if it.get("show", lambda: True)()]

    def current(self):
        vis = self.visible()
        self.index = max(0, min(self.index, len(vis) - 1))
        return vis[self.index] if vis else None

    def move(self, d):
        vis = self.visible()
        if vis:
            self.index = (self.index + d) % len(vis)

    def hit(self, pos):
        for i, r in enumerate(self.rects):
            if r.collidepoint(pos):
                return i
        return None

    def draw(self, surf, fonts, t):
        self.rects = []
        vis = self.visible()
        for i, it in enumerate(vis):
            y = self.y + i * self.spacing
            sel = i == self.index
            rect = pygame.Rect(0, 0, self.width, self.spacing - 6)
            if self.anchor == "midleft":
                rect.midleft = (self.x - 16, y)
            else:
                rect.center = (self.x, y)
            self.rects.append(rect)
            if sel:
                pulse = 0.5 + 0.5 * math.sin(t * 6)
                panel(surf, rect, (40, 50, 120), (255, 220, 90), 200, 10, 2)
                col = (255, int(220 + 35 * pulse), 90)
            else:
                col = (225, 230, 255)
            label = it["label"]()
            if self.anchor == "midleft":
                fonts.draw(surf, label, self.size, (self.x, y), col, "midleft", outline=(0, 0, 0))
            else:
                fonts.draw(surf, label, self.size, (self.x, y), col, "center", outline=(0, 0, 0))
