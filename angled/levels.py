"""Level parameters and the (solvability-checked) level generator.

Every level is generated from a fixed seed, so levels are identical on every
machine.  The generator assigns an angle label to each bubble and then proves
the level can be cleared: it repeatedly finds a bubble that a real shot (same
physics as the game, integer launcher angles, launcher may slide) can hit at
exactly its labelled angle, removes it (plus anything that would fall), and
repeats.  Because removing bubbles can only open up shots - never block them -
any order the player chooses also stays solvable.

Results are cached in assets/levels.json (built by tools/gen_levels.py).
"""
import json
import math
import random

from .config import DIFF, FIELD_TOP, LEVELS, MAX_ANGLE, MIN_ANGLE, resource_path
from .physics import Geom, connected_to_ceiling, neighbors, row_len, solve

GEN_VERSION = 6
_cache = None


# ------------------------------------------------------------------ params
def label_step(level, diff):
    tiers = {
        "easy": [(20, 15), (50, 10), (100, 5)],
        "normal": [(10, 15), (25, 10), (50, 5), (75, 2), (100, 1)],
        "hard": [(10, 10), (30, 5), (60, 2), (100, 1)],
    }[diff]
    for upto, step in tiers:
        if level <= upto:
            return step
    return 1


def level_params(level, diff):
    d = DIFF[diff]
    rows = min(6, 2 + (level - 1) // 20)
    n = int(round((6 + (level - 1) * 0.27) * d["count"]))
    n = max(4, min(n, 60))
    if diff == "easy":
        amin = max(25, 60 - (level - 1) * 0.6)
    elif diff == "hard":
        amin = max(12, 45 - (level - 1) * 0.8)
    else:
        amin = max(15, 60 - (level - 1) * 0.9)
    amin = max(MIN_ANGLE + 2, amin)
    amax = 180 - amin
    step = label_step(level, diff)
    labels = [a for a in range(int(math.ceil(amin / step) * step), int(amax) + 1, step)
              if MIN_ANGLE + 2 <= a <= MAX_ANGLE - 2]
    if not labels:
        labels = [90]
    speed = (0.9 + 0.015 * (level - 1)) * d["speed"]
    return {"rows": rows, "count": n, "labels": labels, "step": step,
            "speed": speed, "tol": d["tol"]}


def battle_params(diff):
    p = level_params({"easy": 8, "normal": 25, "hard": 45}[diff], diff)
    p["rows"] = 4
    p["count"] = {"easy": 16, "normal": 22, "hard": 28}[diff]
    p["speed"] = {"easy": 2.0, "normal": 2.8, "hard": 3.6}[diff]
    return p


# ------------------------------------------------------------------ shapes
def _all_cells(rows):
    return {(r, c) for r in range(rows) for c in range(row_len(r))}


def gen_shape(rng, rows, n):
    kind = rng.choice(["block", "pyramid", "vee", "chandelier", "random", "columns", "zigzag", "chandelier"])
    cells = set()
    if kind == "block":
        cells = _all_cells(rows)
    elif kind == "pyramid":  # wide at the top, narrow at the bottom
        for r in range(rows):
            cut = r // 2
            cells |= {(r, c) for c in range(cut, row_len(r) - cut)}
    elif kind == "vee":  # narrow at the top, wide at the bottom (hangs from the middle)
        for r in range(rows):
            half = 1 + r
            mid = row_len(r) / 2.0
            cells |= {(r, c) for c in range(row_len(r)) if abs(c + 0.5 - mid) <= half}
    elif kind == "chandelier":  # a few anchors with clusters hanging below
        k = rng.randint(2, 4)
        anchors = rng.sample(range(row_len(0)), k)
        per = max(2, n // k)
        for a in anchors:
            cl = {(0, a)}
            frontier = [(0, a)]
            while len(cl) < per and frontier:
                c = rng.choice(frontier)
                opts = [x for x in neighbors(*c) if x[0] >= c[0] and x[0] < rows and x not in cl]
                if not opts:
                    frontier.remove(c)
                    continue
                nb = rng.choice(opts)
                cl.add(nb)
                frontier.append(nb)
            cells |= cl
    elif kind == "columns":
        for r in range(rows):
            cells |= {(r, c) for c in range(row_len(r)) if (c // 2) % 2 == 0 or r == 0}
    elif kind == "zigzag":
        for r in range(rows):
            shift = (r // 2) % 2
            cells |= {(r, c) for c in range(row_len(r)) if (c + shift) % 3 != 2 or r == 0}
    else:
        cells = {c for c in _all_cells(rows) if rng.random() < 0.75}
    cells = connected_to_ceiling(cells)

    guard = 0
    while len(cells) > n and guard < 500:
        guard += 1
        lst = sorted(cells, key=lambda c: (-c[0], rng.random()))
        pick = lst[min(len(lst) - 1, int(rng.random() ** 2 * len(lst) * 0.6))]
        cells.discard(pick)
        cells = connected_to_ceiling(cells)
    guard = 0
    while len(cells) < n and guard < 2000:
        guard += 1
        cand = set()
        for c in cells:
            for nb in neighbors(*c):
                if nb not in cells and nb[0] < rows:
                    cand.add(nb)
        cand |= {(0, c) for c in range(row_len(0)) if (0, c) not in cells}
        if not cand:
            break
        cells.add(rng.choice(sorted(cand)))
    return cells, kind


# ------------------------------------------------------------------ labels + proof
def assign_labels(rng, cells, labels, x0=100.0):
    """Give every cell a label so that the level is provably solvable."""
    g = Geom(x0)
    ceil_y = FIELD_TOP
    lab = {c: rng.choice(labels) for c in cells}
    remaining = set(cells)
    known = set()  # cells proven hittable in some superset state (stay hittable)

    def hittable(c, label):
        bub = [(k, *g.cell_pos(k[0], k[1], ceil_y)) for k in remaining]
        x, y = g.cell_pos(c[0], c[1], ceil_y)
        return solve(g, bub, ceil_y, c, x, y, label, strict=True) is not None

    while remaining:
        ready = [c for c in remaining if c in known]
        pick = None
        if ready:
            pick = rng.choice(ready)
        else:
            order = sorted(remaining, key=lambda c: (-c[0], rng.random()))
            for c in order:
                if hittable(c, lab[c]):
                    known.add(c)
                    pick = c
                    break
            if pick is None:
                # relabel an exposed bubble with an angle that works
                for c in order[:12]:
                    tries = labels[:]
                    rng.shuffle(tries)
                    for L in tries:
                        if hittable(c, L):
                            lab[c] = L
                            known.add(c)
                            pick = c
                            break
                    if pick:
                        break
            if pick is None:  # practically never: drop the lowest bubble
                pick = order[0]
                del lab[pick]
        remaining.discard(pick)
        remaining = connected_to_ceiling(remaining)
    # remove any bubble that lost its label
    return {c: lab[c] for c in cells if c in lab}


def generate(level, diff, battle=False, seed_extra=0):
    p = battle_params(diff) if battle else level_params(level, diff)
    seed = (level * 7919 + {"easy": 11, "normal": 23, "hard": 37}[diff] * 104729
            + (555 if battle else 0) + seed_extra * 31337)
    rng = random.Random(seed)
    cells, _kind = gen_shape(rng, p["rows"], p["count"])
    lab = assign_labels(rng, cells, p["labels"])
    lab = {c: v for c, v in lab.items() if c in connected_to_ceiling(lab.keys())}
    return [[r, c, v] for (r, c), v in sorted(lab.items())]


# ------------------------------------------------------------------ cache
def _load_cache():
    global _cache
    if _cache is None:
        try:
            with open(resource_path("assets", "levels.json"), "r", encoding="utf-8") as f:
                d = json.load(f)
            _cache = d if d.get("version") == GEN_VERSION else {}
        except Exception:
            _cache = {}
    return _cache


def get_level(level, diff):
    c = _load_cache().get(diff)
    if c and len(c) >= level:
        return c[level - 1]
    return generate(level, diff)


def get_battle(diff, index):
    c = _load_cache().get("battle_" + diff)
    if c:
        return c[index % len(c)]
    return generate(1, diff, battle=True, seed_extra=index)


__all__ = ["level_params", "battle_params", "get_level", "get_battle", "generate", "LEVELS"]
