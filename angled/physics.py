"""Hex grid geometry, shot ray-casting with wall bounces, and a shot solver.

Angle convention: degrees, measured counter-clockwise from the +x axis
(0 = right, 90 = straight up, 180 = left).  Screen y grows downward, so a
direction of `a` degrees is (cos a, -sin a).

A shot's *arrival angle* is its direction of travel at the moment it touches
a bubble.  A bubble only pops when the arrival angle matches its label.
Each wall bounce mirrors the angle (a -> 180 - a): that is the trick shot.
"""
import math

from .config import COLS, HIT_R, PIVOT_Y, R, ROW_H


# ------------------------------------------------------------------ grid
def row_len(row):
    return COLS if row % 2 == 0 else COLS - 1


def valid(row, col):
    return row >= 0 and 0 <= col < row_len(row)


def neighbors(row, col):
    if row % 2 == 0:
        cand = [(row, col - 1), (row, col + 1), (row - 1, col - 1), (row - 1, col),
                (row + 1, col - 1), (row + 1, col)]
    else:
        cand = [(row, col - 1), (row, col + 1), (row - 1, col), (row - 1, col + 1),
                (row + 1, col), (row + 1, col + 1)]
    return [c for c in cand if valid(*c)]


def connected_to_ceiling(cells):
    """Return the subset of `cells` (iterable of (row,col)) attached to row 0."""
    cells = set(cells)
    seen = set(c for c in cells if c[0] == 0)
    stack = list(seen)
    while stack:
        c = stack.pop()
        for n in neighbors(*c):
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


class Geom:
    """Field geometry in screen coordinates."""

    def __init__(self, x0):
        self.x0 = x0
        self.x1 = x0 + COLS * 2 * R
        self.wall_l = self.x0 + R
        self.wall_r = self.x1 - R
        self.pivot_y = PIVOT_Y

    def cell_pos(self, row, col, ceil_y):
        x = self.x0 + R + col * 2 * R + (R if row % 2 else 0)
        y = ceil_y + R + row * ROW_H
        return x, y

    def nearest_cell(self, x, y, ceil_y):
        row = int(round((y - ceil_y - R) / ROW_H))
        row = max(0, row)
        col = int(round((x - self.x0 - R - (R if row % 2 else 0)) / (2 * R)))
        col = max(0, min(row_len(row) - 1, col))
        return row, col


# ------------------------------------------------------------------ rays
def direction(angle_deg):
    a = math.radians(angle_deg)
    return math.cos(a), -math.sin(a)


def arrival_angle(dx, dy):
    return math.degrees(math.atan2(-dy, dx))


def step_ray(g, bubbles, ceil_y, x, y, dx, dy, length):
    """Advance a shot along (dx,dy) by at most `length`.

    bubbles: iterable of (key, cx, cy).
    Returns (nx, ny, travelled, event, key) where event is None, 'wall',
    'ceiling' or 'hit'.
    """
    tmin = length
    ev = None
    key = None
    if dx < -1e-12:
        t = (g.wall_l - x) / dx
        if t < tmin:
            tmin, ev = max(t, 0.0), "wall"
    elif dx > 1e-12:
        t = (g.wall_r - x) / dx
        if t < tmin:
            tmin, ev = max(t, 0.0), "wall"
    if dy < -1e-12:
        t = (ceil_y + R - y) / dy
        if t < tmin:
            tmin, ev = max(t, 0.0), "ceiling"
    r2 = HIT_R * HIT_R
    for k, cx, cy in bubbles:
        fx = x - cx
        fy = y - cy
        b = fx * dx + fy * dy
        if b > 0:
            continue
        c = fx * fx + fy * fy - r2
        if c < 0:
            return x, y, 0.0, "hit", k
        disc = b * b - c
        if disc < 0:
            continue
        t = -b - math.sqrt(disc)
        if t <= tmin:
            tmin, ev, key = t, "hit", k
    return x + dx * tmin, y + dy * tmin, tmin, ev, key


class CastResult:
    __slots__ = ("path", "key", "arrival", "bounces", "end", "event")

    def __init__(self):
        self.path = []
        self.key = None
        self.arrival = None
        self.bounces = 0
        self.end = None
        self.event = None


def cast(g, bubbles, ceil_y, x, y, angle_deg, max_bounces=14, max_len=6000.0):
    """Simulate a whole shot instantly.  Used for the guide line, the CPU and
    the level generator."""
    bubbles = list(bubbles)
    dx, dy = direction(angle_deg)
    res = CastResult()
    res.path.append((x, y))
    remaining = max_len
    while remaining > 0:
        x, y, t, ev, key = step_ray(g, bubbles, ceil_y, x, y, dx, dy, remaining)
        remaining -= t
        res.path.append((x, y))
        if ev == "wall":
            dx = -dx
            res.bounces += 1
            if res.bounces > max_bounces:
                res.event = "limit"
                break
            continue
        res.event = ev or "limit"
        if ev == "hit":
            res.key = key
        break
    res.arrival = arrival_angle(dx, dy)
    res.end = (x, y)
    return res


def backtrace(g, x, y, dx, dy, target_y):
    """Trace from (x,y) along (dx,dy) (moving downward) reflecting off the
    walls until reaching target_y.  Returns (x, reflections) or None."""
    if dy <= 1e-9:
        return None
    n = 0
    while n < 60:
        ty = (target_y - y) / dy
        if dx < -1e-12:
            tw = (g.wall_l - x) / dx
        elif dx > 1e-12:
            tw = (g.wall_r - x) / dx
        else:
            tw = float("inf")
        if ty <= tw:
            return x + dx * ty, n
        x += dx * tw
        y += dy * tw
        dx = -dx
        n += 1
    return None


OFFSETS = (0.0, 0.35, -0.35, 0.65, -0.65, 0.85, -0.85)


def _works(g, bubbles, ceil_y, key, lx, ang, label):
    res = cast(g, bubbles, ceil_y, lx, g.pivot_y, ang)
    return res.key == key and abs(res.arrival - label) < 0.25


def solve(g, bubbles, ceil_y, key, cx, cy, label, offsets=OFFSETS, robust=True, strict=False):
    """Find a launcher x and integer launcher angle so that a shot reaches
    bubble `key` (centre cx,cy) first, travelling at exactly `label` degrees.

    robust: prefer solutions that still work when the launcher is off by a
    couple of pixels and the bubbles have moved a little (human margin).
    strict: only accept robust solutions.
    Returns (launch_x, launcher_angle, bounces) or None."""
    bubbles = list(bubbles)
    tdx, tdy = direction(label)
    nx, ny = -tdy, tdx
    fallback = None
    for s in offsets:
        qx = cx + nx * s * HIT_R
        qy = cy + ny * s * HIT_R
        if not (g.wall_l - 0.01 <= qx <= g.wall_r + 0.01):
            continue
        qx = min(max(qx, g.wall_l), g.wall_r)
        bt = backtrace(g, qx, qy, -tdx, -tdy, g.pivot_y)
        if bt is None:
            continue
        lx, nref = bt
        ang = label if nref % 2 == 0 else 180 - label
        if not (8 <= ang <= 172):
            continue
        lx = min(max(lx, g.wall_l + 0.5), g.wall_r - 0.5)
        res = cast(g, bubbles, ceil_y, lx, g.pivot_y, ang)
        if res.key != key or abs(res.arrival - label) >= 0.25:
            continue
        sol = (lx, ang, res.bounces)
        if not robust:
            return sol
        ok = True
        for dx, dc in ((-2.0, 0.0), (2.0, 0.0), (0.0, -4.0), (0.0, 4.0)):
            x2 = min(max(lx + dx, g.wall_l + 0.5), g.wall_r - 0.5)
            if not _works(g, bubbles, ceil_y + dc, key, x2, ang, label):
                ok = False
                break
        if ok:
            return sol
        if fallback is None:
            fallback = sol
    return None if strict else fallback
