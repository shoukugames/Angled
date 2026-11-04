#!/usr/bin/env python3
"""Render assets/icon.png and assets/icon.ico (multi-size, PNG-encoded ICO)."""
import io, math, os, struct, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
from angled.assets import Fonts  # noqa: E402


def render(size):
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    pygame.draw.rect(s, (26, 30, 90), (8, 8, 240, 240), border_radius=48)
    pygame.draw.rect(s, (110, 140, 255), (8, 8, 240, 240), 6, border_radius=48)
    # bubble
    c, r = (150, 104), 70
    for i in range(r, 0, -1):
        t = i / r
        col = (int(90 + 140 * (1 - t)), int(200 + 50 * (1 - t)), 255)
        pygame.draw.circle(s, col, c, i)
    pygame.draw.circle(s, (30, 60, 140), c, r, 4)
    pygame.draw.ellipse(s, (255, 255, 255, 150), (c[0] - 45, c[1] - 55, 50, 28))
    Fonts().draw(s, "45°", 50, (c[0] + 3, c[1] + 4), (255, 255, 255), "center", outline=(20, 30, 80), ow=3)
    # launcher + arrow at 45 degrees
    o = (62, 206)
    a = math.radians(45)
    tip = (o[0] + math.cos(a) * 70, o[1] - math.sin(a) * 70)
    pygame.draw.line(s, (255, 221, 64), o, tip, 14)
    px, py = -(-math.sin(a)), math.cos(a)
    ux, uy = math.cos(a), -math.sin(a)
    pygame.draw.polygon(s, (255, 221, 64), [(tip[0] + ux * 26, tip[1] + uy * 26),
                                             (tip[0] + px * 18, tip[1] + py * 18),
                                             (tip[0] - px * 18, tip[1] - py * 18)])
    pygame.draw.circle(s, (255, 255, 255), o, 20)
    pygame.draw.arc(s, (255, 221, 64), (o[0] - 50, o[1] - 50, 100, 100), 0, a, 5)
    return pygame.transform.smoothscale(s, (size, size)) if size != 256 else s


def main():
    out_png = os.path.join(ROOT, "assets", "icon.png")
    pygame.image.save(render(256), out_png)
    sizes = [256, 64, 48, 32, 16]
    blobs = []
    for sz in sizes:
        tmp = os.path.join(ROOT, "assets", "_ico_%d.png" % sz)
        pygame.image.save(render(sz), tmp)
        with open(tmp, "rb") as f:
            blobs.append(f.read())
        os.remove(tmp)
    hdr = struct.pack("<HHH", 0, 1, len(sizes))
    off = 6 + 16 * len(sizes)
    dirs = b""
    for sz, b in zip(sizes, blobs):
        dirs += struct.pack("<BBBBHHII", sz % 256, sz % 256, 0, 0, 1, 32, len(b), off)
        off += len(b)
    with open(os.path.join(ROOT, "assets", "icon.ico"), "wb") as f:
        f.write(hdr + dirs + b"".join(blobs))
    print("wrote assets/icon.png and assets/icon.ico")


if __name__ == "__main__":
    main()
