"""CPU opponent for VS battle."""
import random

from .config import DIFF
from .physics import connected_to_ceiling


class CPU:
    def __init__(self, field, diff):
        self.f = field
        d = DIFF[diff]
        self.think = d["cpu_think"]
        self.err = d["cpu_err"]
        self.rot_speed = {"easy": 70, "normal": 120, "hard": 200}[diff]
        self.state = "think"
        self.timer = self.think * 1.2
        self.ta = 90
        self.target = None
        self.blunder = False
        self.cur_angle = float(field.angle)

    def update(self, dt):
        f = self.f
        if f.dead:
            return
        if self.state == "think":
            self.timer -= dt
            if self.timer <= 0 and f.shot is None and f.grid:
                self.plan()
        elif self.state == "move":   # the launcher is fixed: only turn the arrow
            da = self.ta - self.cur_angle
            rs = self.rot_speed * dt
            self.cur_angle += max(-rs, min(rs, da))
            f.set_angle(self.cur_angle)
            if f.angle == self.ta:
                self.state = "aim"
                self.timer = random.uniform(0.1, 0.35)
        elif self.state == "aim":
            self.timer -= dt
            if self.timer <= 0:
                # the bubbles kept moving while we turned: re-aim if the shot no longer works
                if self.target is not None and not self.blunder and f.shot is None:
                    a = f.launch_for(self.target)
                    if a is None:
                        self.state = "think"
                        self.timer = 0.05
                        return
                    if a != f.angle:
                        self.ta = a
                        self.state = "move"
                        return
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
        self.target = None
        self.blunder = False
        for _, c in scored:
            a = f.launch_for(c, bub)
            if a is not None:
                self.target, self.ta = c, a
                break
        if self.target is None:
            self.ta = random.randint(40, 140)
        elif random.random() < self.err:  # human-like mistake
            self.blunder = True
            self.ta = int(max(10, min(170, self.ta + random.choice([-1, 1]) * random.randint(3, 12))))
        self.cur_angle = float(f.angle)
        self.state = "move"
