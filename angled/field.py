"""One playfield: bubble grid, descending ceiling, launcher and shot."""
import math
import random

import pygame

from . import ui
from .config import (DEADLINE_Y, FIELD_TOP, FIELD_W, FLOOR_Y, MAX_ANGLE, MIN_ANGLE, PIVOT_Y, R,
                     ROW_H, SHOT_SPEED)
from .effects import Effects
from .physics import Geom, arrival_angle, cast, connected_to_ceiling, direction, neighbors, \
    row_len, step_ray

MOVE_SPEED = 330.0
PENALTY_PUSH = 9.0


class Bubble:
    __slots__ = ("label", "wobble", "spawn")

    def __init__(self, label, spawn=0.0):
        self.label = label
        self.wobble = 0.0
        self.spawn = spawn


class Shot:
    __slots__ = ("x", "y", "dx", "dy", "bounces", "trail", "launch_angle")

    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.dx, self.dy = direction(angle)
        self.bounces = 0
        self.trail = []
        self.launch_angle = angle


class Field:
    def __init__(self, x0, audio, fonts, speed=1.5, tol=1, label_pool=None):
        self.g = Geom(x0)
        self.x0 = x0
        self.audio = audio
        self.fonts = fonts
        self.base_speed = speed
        self.tol = tol
        self.label_pool = label_pool or [45, 60, 75, 90, 105, 120, 135]
        self.grid = {}
        self.ceil_y = float(FIELD_TOP)
        self.launch_x = x0 + FIELD_W / 2.0
        self.angle = 90
        self.shot = None
        self.reload = 0.0
        self.fx = Effects()
        self.falling = []    # [x, y, vx, vy, label]
        self.incoming = []   # dicts for battle garbage in flight
        self.dead = False
        self.time = 0.0
        self.shake = 0.0
        # held controls
        self.move_dir = 0
        self.rot_dir = 0
        self.rot_step = 1
        self.rot_timer = 0.0
        self.rot_held = 0.0
        # stats
        self.pops = 0
        self.misses = 0
        self.shots = 0
        self.banks = 0
        self.danger = 0.0

    # ------------------------------------------------------------ setup
    def load(self, cells):
        self.grid = {(r, c): Bubble(v) for r, c, v in cells}
        self.ceil_y = float(FIELD_TOP)
        self.shot = None
        self.falling.clear()
        self.incoming.clear()
        self.fx.clear()
        self.dead = False
        self.launch_x = self.x0 + FIELD_W / 2.0
        self.angle = 90

    # ------------------------------------------------------------ queries
    def pos(self, cell):
        return self.g.cell_pos(cell[0], cell[1], self.ceil_y)

    def bubble_list(self):
        return [(c, *self.pos(c)) for c in self.grid]

    def lowest_y(self):
        if not self.grid:
            return self.ceil_y
        r = max(c[0] for c in self.grid)
        return self.ceil_y + R + r * ROW_H + R

    def progress(self):
        """0 = lowest bubble at the top, 1 = touching the deadline."""
        return max(0.0, min(1.0, (self.lowest_y() - FIELD_TOP) / (DEADLINE_Y - FIELD_TOP)))

    def cleared(self):
        return not self.grid and not self.incoming and not self.falling

    def busy(self):
        return self.shot is not None

    # ------------------------------------------------------------ controls
    def clamp_x(self, x):
        return min(max(x, self.g.wall_l + 0.5), self.g.wall_r - 0.5)

    def set_angle(self, a):
        self.angle = int(max(MIN_ANGLE, min(MAX_ANGLE, round(a))))

    def nudge_angle(self, d):
        self.set_angle(self.angle + d)

    def aim_at(self, mx, my):
        if my >= PIVOT_Y - 4:
            my = PIVOT_Y - 4
        a = math.degrees(math.atan2(PIVOT_Y - my, mx - self.launch_x))
        self.set_angle(a)

    def slide(self, dx):
        self.launch_x = self.clamp_x(self.launch_x + dx)

    def fire(self):
        if self.shot is not None or self.reload > 0 or self.dead:
            return False
        self.shot = Shot(self.launch_x, PIVOT_Y, self.angle)
        self.shots += 1
        self.audio.sfx("shoot")
        return True

    # ------------------------------------------------------------ update
    def update(self, dt, descend=True):
        """Advance the field.  Returns a list of event tuples."""
        events = []
        self.time += dt
        self.fx.update(dt)
        self.shake = max(0.0, self.shake - dt)
        if self.reload > 0:
            self.reload -= dt
        # held controls
        if self.move_dir:
            self.slide(self.move_dir * MOVE_SPEED * dt)
        if self.rot_dir:
            self.rot_timer -= dt
            self.rot_held += dt
            if self.rot_timer <= 0:
                self.nudge_angle(self.rot_dir * self.rot_step)
                fast = self.rot_held > 0.8
                self.rot_timer = (0.022 if fast else 0.05) if self.rot_step == 1 else 0.11
        else:
            self.rot_held = 0.0
        for b in self.grid.values():
            if b.wobble > 0:
                b.wobble = max(0.0, b.wobble - dt)
            if b.spawn > 0:
                b.spawn = max(0.0, b.spawn - dt)
        # descent: faster and faster as the bubbles approach the floor
        p = self.progress()
        self.danger = p
        if descend and self.grid and not self.dead:
            delta = self.base_speed * (1.0 + 2.0 * p * p) * dt
            self.ceil_y += delta
            if self.shot is not None:
                # the shot rides along with the grid so the guide line's
                # prediction is exactly what happens
                self.shot.y += delta
        # falling (dropped) bubbles
        for f in self.falling:
            f[3] += 1500 * dt
            f[0] += f[2] * dt
            f[1] += f[3] * dt
        self.falling = [f for f in self.falling if f[1] < FLOOR_Y + 40]
        # garbage arriving (battle)
        self._update_incoming(dt, events)
        # shot
        if self.shot is not None:
            self._update_shot(dt, events)
        if not self.dead and self.grid and self.lowest_y() >= DEADLINE_Y:
            self.dead = True
            events.append(("dead",))
        return events

    def _update_shot(self, dt, events):
        s = self.shot
        remaining = SHOT_SPEED * dt
        bub = self.bubble_list()
        guard = 0
        while remaining > 0 and guard < 20:
            guard += 1
            nx, ny, t, ev, key = step_ray(self.g, bub, self.ceil_y, s.x, s.y, s.dx, s.dy, remaining)
            s.x, s.y = nx, ny
            remaining -= t
            if ev == "wall":
                s.dx = -s.dx
                s.bounces += 1
                self.audio.sfx("bounce")
                self.fx.burst(s.x, s.y, (200, 220, 255), 5, 120, 0.25, 2, 0)
                continue
            if ev == "ceiling":
                self.audio.sfx("fizzle")
                self.fx.burst(s.x, s.y, (180, 180, 200), 10, 140, 0.4, 3, 200)
                self.fx.text(s.x, s.y + 30, "MISS", 18, (200, 200, 220), 0.7)
                events.append(("fizzle",))
                self.shot = None
                self.reload = 0.12
                return
            if ev == "hit":
                self._resolve_hit(key, events)
                return
        s.trail.append((s.x, s.y))
        if len(s.trail) > 10:
            s.trail.pop(0)

    def _resolve_hit(self, key, events):
        s = self.shot
        self.shot = None
        self.reload = 0.12
        arr = arrival_angle(s.dx, s.dy)
        b = self.grid.get(key)
        if b is None:
            return
        bx, by = self.pos(key)
        if abs(arr - b.label) <= self.tol + 0.05:
            # POP!
            del self.grid[key]
            self.pops += 1
            if s.bounces:
                self.banks += 1
            self.audio.pop()
            col = ui.label_color(b.label)
            self.fx.burst(bx, by, col, 22, 260, 0.7, 5)
            self.fx.burst(bx, by, (255, 255, 255), 8, 160, 0.4, 3)
            self.fx.ring(bx, by, col, 46, 0.3)
            dropped = self._drop_floating()
            events.append(("pop", key, b.label, (bx, by), s.bounces, dropped))
        else:
            b.wobble = 0.45
            self.misses += 1
            self.shake = 0.25
            self.audio.sfx("wrong")
            self.fx.burst(s.x, s.y, (170, 170, 190), 14, 200, 0.5, 3)
            self.ceil_y += PENALTY_PUSH
            events.append(("wrong", key, b.label, round(arr), (bx, by)))

    def _drop_floating(self):
        keep = connected_to_ceiling(self.grid.keys())
        gone = [c for c in self.grid if c not in keep]
        out = []
        for c in gone:
            x, y = self.pos(c)
            b = self.grid.pop(c)
            self.falling.append([x, y, random.uniform(-90, 90), random.uniform(-260, -80), b.label])
            out.append((c, b.label, (x, y)))
        if out:
            self.audio.sfx("drop")
        return out

    # ------------------------------------------------------------ battle garbage
    def _free_slots(self, reserved):
        occupied = set(self.grid) | reserved
        cand = set()
        for c in self.grid:
            for n in neighbors(*c):
                if n not in occupied:
                    cand.add(n)
        cand |= {(0, c) for c in range(row_len(0)) if (0, c) not in occupied}
        return sorted(cand)

    def receive(self, count, src_points, delay=0.0):
        """Queue `count` garbage bubbles flying in from src_points (screen coords)."""
        reserved = {g["cell"] for g in self.incoming}
        for i in range(count):
            slots = self._free_slots(reserved)
            if not slots:
                break
            maxrow = max(s[0] for s in slots)
            low = [s for s in slots if s[0] >= maxrow - 1]
            cell = random.choice(low)
            reserved.add(cell)
            sx, sy = src_points[i % len(src_points)] if src_points else (self.x0, 0)
            self.incoming.append({"cell": cell, "label": random.choice(self.label_pool),
                                  "sx": sx, "sy": sy, "t": -delay - i * 0.06, "dur": 0.7})

    def _update_incoming(self, dt, events):
        arrived = []
        for gb in self.incoming:
            gb["t"] += dt
            if gb["t"] >= gb["dur"]:
                arrived.append(gb)
        for gb in arrived:
            self.incoming.remove(gb)
            cell = gb["cell"]
            if cell in self.grid or not (cell[0] == 0 or any(n in self.grid for n in neighbors(*cell))):
                slots = self._free_slots({g["cell"] for g in self.incoming})
                if not slots:
                    continue
                cell = max(slots, key=lambda c: (c[0], random.random()))
            self.grid[cell] = Bubble(gb["label"], spawn=0.25)
            x, y = self.pos(cell)
            self.fx.ring(x, y, (255, 120, 120), 36, 0.3)
            events.append(("garbage_in", cell))

    # ------------------------------------------------------------ drawing
    def draw(self, surf, show_guide=False, color=(255, 230, 90), active=True, title=None):
        ox = int(math.sin(self.time * 60) * 4 * (self.shake / 0.25)) if self.shake else 0
        x0, x1 = self.g.x0 + ox, self.g.x1 + ox
        top = FIELD_TOP - 30
        # well
        ui.panel(surf, (x0 - 8, top, FIELD_W + 16, FLOOR_Y - top + 6), (10, 12, 36), (80, 100, 200), 205, 10)
        # danger glow
        p = self.danger
        if p > 0.7 and self.grid:
            pulse = 0.5 + 0.5 * math.sin(self.time * (8 + 10 * p))
            glow = pygame.Surface((FIELD_W, 90), pygame.SRCALPHA)
            for i in range(90):
                a = int((1 - i / 90) * 120 * pulse * (p - 0.7) / 0.3)
                pygame.draw.line(glow, (255, 40, 60, a), (0, 89 - i), (FIELD_W, 89 - i))
            surf.blit(glow, (x0, DEADLINE_Y - 80))
        # pressing ceiling
        ch = int(self.ceil_y) - top
        if ch > 0:
            pygame.draw.rect(surf, (70, 80, 130), (x0, top, FIELD_W, ch))
            for yy in range(top + 8, int(self.ceil_y) - 2, 14):
                pygame.draw.line(surf, (95, 105, 160), (x0, yy), (x1, yy), 2)
            pygame.draw.rect(surf, (170, 185, 240), (x0, int(self.ceil_y) - 5, FIELD_W, 5))
        # deadline
        ui.dashed_polyline(surf, [(x0, DEADLINE_Y), (x1, DEADLINE_Y)], (255, 80, 90), 12, 8, 2)
        # bubbles
        for c, b in self.grid.items():
            x, y = self.pos(c)
            if b.wobble:
                x += math.sin(b.wobble * 60) * 4
            sc = 1.0 - b.spawn * 2.4 if b.spawn else 1.0
            ui.draw_bubble(surf, b.label, x + ox, y, self.fonts, max(0.2, sc))
        for f in self.falling:
            ui.draw_bubble(surf, f[4], f[0] + ox, f[1], self.fonts)
        for gb in self.incoming:
            t = max(0.0, gb["t"]) / gb["dur"]
            tx, ty = self.pos(gb["cell"])
            x = gb["sx"] + (tx - gb["sx"]) * t
            y = gb["sy"] + (ty - gb["sy"]) * t - math.sin(t * math.pi) * 120
            if gb["t"] >= 0:
                ui.draw_bubble(surf, gb["label"], x, y, self.fonts, 0.7 + 0.3 * t)
        # guide line
        if show_guide and self.shot is None and not self.dead and active:
            self.draw_guide(surf)
        # rail + launcher
        pygame.draw.line(surf, (90, 100, 170), (x0 + 10, PIVOT_Y + 24), (x1 - 10, PIVOT_Y + 24), 4)
        ui.draw_launcher(surf, self.fonts, self.launch_x + ox, PIVOT_Y, self.angle, color,
                         loaded=self.shot is None and active)
        # shot
        if self.shot is not None:
            s = self.shot
            for i, (tx, ty) in enumerate(s.trail):
                a = (i + 1) / (len(s.trail) + 1)
                pygame.draw.circle(surf, (int(120 * a), int(170 * a), int(255 * a)), (int(tx), int(ty)),
                                   int(4 + 7 * a))
            pygame.draw.circle(surf, (255, 255, 255), (int(s.x), int(s.y)), 12)
            pygame.draw.circle(surf, (160, 210, 255), (int(s.x), int(s.y)), 12, 3)
        self.fx.draw(surf, self.fonts)
        if title:
            self.fonts.draw(surf, title, 22, ((x0 + x1) // 2, top - 16), color, "center", outline=(0, 0, 0))

    def draw_guide(self, surf):
        res = cast(self.g, self.bubble_list(), self.ceil_y, self.launch_x, PIVOT_Y, self.angle)
        if len(res.path) < 2:
            return
        ok = False
        if res.event == "hit" and res.key in self.grid:
            ok = abs(res.arrival - self.grid[res.key].label) <= self.tol + 0.05
        col = (120, 255, 150) if ok else (255, 240, 160) if res.event != "hit" else (255, 120, 120)
        ui.dashed_polyline(surf, res.path, col, 10, 7, 3)
        ex, ey = res.end
        if res.event == "hit":
            pygame.draw.circle(surf, col, (int(ex), int(ey)), R, 2)
            tag = "%d°" % round(res.arrival)
            self.fonts.draw(surf, tag, 18, (ex, ey + R + 12), col, "center", outline=(0, 0, 0))
            if ok:
                bx, by = self.pos(res.key)
                pygame.draw.circle(surf, (120, 255, 150), (int(bx), int(by)), R + 4, 3)
