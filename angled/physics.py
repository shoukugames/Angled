"""Hex grid geometry, shot ray-casting with wall bounces, and a shot solver.

Angle convention: degrees, measured counter-clockwise from the +x axis
(0 = right, 90 = straight up, 180 = left).  Screen y grows downward, so a
direction of `a` degrees is (cos a, -sin a).

A bubble's label is its *strike angle*: the spot on the bubble's edge where
the shot touches it, measured from the bubble's centre like a protractor
drawn around the bubble (right edge 0, bottom 90, left edge 180).  A shot
fired at `a` that hits a bubble dead centre strikes it at 180 - a; hitting it
off-centre or after a wall bounce strikes it elsewhere - that is the trick shot.
The launcher is fixed at the centre of the floor and fires at whole degrees.
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
        self.px = (self.x0 + self.x1) / 2.0   # the launcher is fixed at the centre

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
    __slots__ = ("path", "key", "arrival", "bounces", "end", "event", "contact")

    def __init__(self):
        self.path = []
        self.key = None
        self.contact = None
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
            for k, cx, cy in bubbles:
                if k == key:
                    res.contact = contact_angle(x, y, cx, cy)
                    break
        break
    res.arrival = arrival_angle(dx, dy)
    res.end = (x, y)
    return res


def contact_angle(sx, sy, cx, cy):
    """Strike angle: where the shot (centre sx,sy) touches the bubble (centre
    cx,cy), measured from the bubble's centre.  0 = right edge, 90 = bottom,
    180 = left edge (shots come from below, so this is the lower half)."""
    return math.degrees(math.atan2(sy - cy, sx - cx))


def _fold(g, x):
    """Map an x coordinate in unfolded (mirrored-walls) space back into the well."""
    w = g.wall_r - g.wall_l
    u = (x - g.wall_l) % (2 * w)
    return g.wall_l + (u if u <= w else 2 * w - u)


def alone_contacts(g, cx, cy, ceil_y, lo=8, hi=172, max_bounces=14):
    """Every way the fixed launcher can strike a lone bubble at (cx, cy).

    Fast and analytic: wall bounces become straight lines through mirror
    images of the bubble.  Returns [(launch_angle, strike_angle, bounces)]."""
    w = g.wall_r - g.wall_l
    px, py = g.px, g.pivot_y
    images = []
    for k in range(-8, 9):   # enough mirror images for max_bounces=14
        images.append(cx + 2 * k * w)
        images.append(2 * g.wall_l - cx + 2 * k * w)
    cand = {}
    dy = py - cy
    if dy <= 0:
        return []
    for xi in images:
        dx = xi - px
        dist = math.hypot(dx, dy)
        if dist <= HIT_R:
            continue
        th = math.degrees(math.atan2(dy, dx))
        half = math.degrees(math.asin(min(1.0, HIT_R / dist))) + 0.5
        for a in range(max(lo, int(math.ceil(th - half))), min(hi, int(math.floor(th + half))) + 1):
            cand.setdefault(a, []).append(xi)   # only these images can be hit at angle a
    out = []
    r2 = HIT_R * HIT_R
    top = ceil_y + R
    for a in sorted(cand):
        ux, uy = direction(a)
        best = None
        for xi in cand[a]:
            fx, fy = px - xi, py - cy
            b = fx * ux + fy * uy
            if b >= 0:
                continue
            c = fx * fx + fy * fy - r2
            disc = b * b - c
            if disc < 0:
                continue
            t = -b - math.sqrt(disc)
            if t > 0 and (best is None or t < best):
                best = t
        if best is None:
            continue
        hx, hy = px + ux * best, py + uy * best
        if hy < top:          # would reach the ceiling first
            continue
        bounces = int(abs(math.floor((hx - g.wall_l) / w)))
        if bounces > max_bounces:
            continue
        out.append((a, contact_angle(_fold(g, hx), hy, cx, cy), bounces))
    return out


def _find(bubbles, key):
    for k, cx, cy in bubbles:
        if k == key:
            return cx, cy
    return None


def label_launch(g, bubbles, ceil_y, key, label, tol, lo=8, hi=172, max_bounces=14):
    """Launcher angle that strikes bubble `key` within `tol` degrees of
    `label`, with every other bubble in the way taken into account.
    Returns the best launch angle or None."""
    bubbles = list(bubbles)
    pos = _find(bubbles, key)
    if pos is None:
        return None
    lim = tol + 0.5
    opts = [(abs(ca - label), a) for a, ca, _b in alone_contacts(g, pos[0], pos[1], ceil_y, lo, hi, max_bounces)
            if abs(ca - label) <= lim]
    opts.sort()
    if len(bubbles) == 1:
        return opts[0][1] if opts else None
    for _err, a in opts:
        res = cast(g, bubbles, ceil_y, g.px, g.pivot_y, a)
        if res.key == key and abs(res.contact - label) <= lim:
            return a
    return None


def lone_ok(g, cx, cy, ceil_y, label, tol, lo=8, hi=172, max_bounces=14):
    """Could `label` be struck on a lone bubble at (cx, cy)?"""
    lim = tol + 0.5
    return any(abs(ca - label) <= lim for _a, ca, _b in alone_contacts(g, cx, cy, ceil_y, lo, hi, max_bounces))


def label_choices(contacts, tol, lo_label, hi_label):
    """Whole-degree labels that the given strike angles can satisfy."""
    out = set()
    t = int(math.floor(tol + 0.5))
    for ca in contacts:
        for L in range(int(math.ceil(ca - t - 0.5)), int(math.floor(ca + t + 0.5)) + 1):
            if lo_label <= L <= hi_label and abs(ca - L) <= tol + 0.5:
                out.add(L)
    return out
