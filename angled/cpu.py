"""CPU opponent for VS battle."""
import random

from .config import DIFF
from .physics import connected_to_ceiling, solve


class CPU:
    def __init__(self, field, diff):
        self.f = field
        d = DIFF[diff]
        self.think = d["cpu_think"]
        self.err = d["cpu_err"]
        self.move_speed = d["cpu_move"]
        self.rot_speed = {"easy": 70, "normal": 120, "hard": 200}[diff]
        self.state = "think"
        self.timer = self.think * 1.2
        self.tx = field.launch_x
        self.ta = 90
        self.cur_angle = float(field.angle)

    def update(self, dt):
        f = self.f
        if f.dead:
            return
        if self.state == "think":
            self.timer -= dt
            if self.timer <= 0 and f.shot is None and f.grid:
                self.plan()
        elif self.state == "move":
            dx = self.tx - f.launch_x
            step = self.move_speed * dt
            f.launch_x = f.clamp_x(f.launch_x + max(-step, min(step, dx)))
            da = self.ta - self.cur_angle
            rs = self.rot_speed * dt
            self.cur_angle += max(-rs, min(rs, da))
            f.set_angle(self.cur_angle)
            if abs(self.tx - f.launch_x) < 0.6 and f.angle == self.ta:
                f.launch_x = f.clamp_x(self.tx)
                self.state = "aim"
                self.timer = random.uniform(0.1, 0.35)
        elif self.state == "aim":
            self.timer -= dt
            if self.timer <= 0:
                f.fire()
                self.state = "think"
                self.timer = self.think * random.uniform(0.7, 1.3)

    def plan(self):
        f = self.f
        bub = f.bubble_list()
        cells = list(f.grid.keys())
        scored = []
        for c in cells:
            rest = set(cells)
            rest.discard(c)
            drop = len(rest) - len(connected_to_ceiling(rest))
            scored.append((drop * 3 + c[0] + random.random() * 2.5, c))
        scored.sort(reverse=True)
        target = None
        for _, c in scored[:16]:
            x, y = f.pos(c)
            sol = solve(f.g, bub, f.ceil_y, c, x, y, f.grid[c].label, robust=False)
            if sol:
                target = sol
                break
        if target is None:
            self.tx = f.clamp_x(f.launch_x + random.uniform(-120, 120))
            self.ta = random.randint(40, 140)
        else:
            self.tx, self.ta = target[0], int(target[1])
            if random.random() < self.err:  # human-like mistake
                self.ta = int(max(10, min(170, self.ta + random.choice([-1, 1]) * random.randint(3, 12))))
        self.cur_angle = float(f.angle)
        self.state = "move"
