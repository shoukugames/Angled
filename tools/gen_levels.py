#!/usr/bin/env python3
"""Pre-generate all 100 levels x 3 difficulties (+ battle layouts) into
assets/levels.json so the game starts instantly.  Every level is proven
solvable by angled.levels.assign_labels."""
import json, os, sys, time
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from angled.levels import GEN_VERSION, LEVELS, generate  # noqa: E402

BATTLE_LAYOUTS = 12


def job(args):
    kind, diff, i = args
    if kind == "level":
        return kind, diff, i, generate(i, diff)
    return kind, diff, i, generate(1, diff, battle=True, seed_extra=i)


def main():
    t = time.time()
    jobs = [("level", d, i) for d in ("easy", "normal", "hard") for i in range(1, LEVELS + 1)]
    jobs += [("battle", d, i) for d in ("easy", "normal", "hard") for i in range(BATTLE_LAYOUTS)]
    out = {"version": GEN_VERSION}
    with Pool() as p:
        res = p.map(job, jobs)
    for kind, diff, i, lv in res:
        key = diff if kind == "level" else "battle_" + diff
        out.setdefault(key, {})[i] = lv
    for key in list(out):
        if key != "version":
            out[key] = [out[key][k] for k in sorted(out[key])]
    path = os.path.join(ROOT, "assets", "levels.json")
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", path, "%.1fs" % (time.time() - t))


if __name__ == "__main__":
    main()
