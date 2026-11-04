"""Global constants, paths and version information."""
import math
import os
import sys

APP_NAME = "Angled"
APP_ID = "angled"
VERSION = "0.1.2"
try:  # written by the build scripts
    from .build_info import BUILD, BUILD_DATE  # type: ignore
except Exception:  # running from source without a build
    BUILD, BUILD_DATE = "dev", "2026-11-04"

STUDIO = "Shouku Games"
AUTHORS = "Shawn Rapaz and Claude Code"
URL = "https://shoukugames.org/"
EMAIL = "info@shoukugames.org"

# ---------------------------------------------------------------- display
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# ---------------------------------------------------------------- playfield
R = 22                      # bubble radius
COLS = 10                   # bubbles in an even row (odd rows have COLS-1)
ROW_H = R * math.sqrt(3)    # vertical distance between rows
FIELD_W = COLS * 2 * R      # 440
FIELD_TOP = 70              # y of the ceiling at the start of a level
PIVOT_Y = 662               # launcher pivot (where shots start)
DEADLINE_Y = PIVOT_Y - 2 * R - 8   # bubbles touching this line = game over
FLOOR_Y = 700
HIT_R = 2 * R * 0.84        # collision distance shot<->bubble (a bit forgiving)
SHOT_SPEED = 1150.0         # px / second
MIN_ANGLE, MAX_ANGLE = 8, 172
LEVELS = 100
CELEBRATE_AFTER = 99        # big fireworks after clearing this level
GUIDE_LEVELS = 10           # prediction line shown on levels 1..10
LEVEL_TIME = 99             # seconds per level

DIFFICULTIES = ("easy", "normal", "hard")

# per difficulty tuning
DIFF = {
    "easy":   {"speed": 0.70, "tol": 5, "count": 0.75, "cpu_think": 2.4, "cpu_err": 0.30, "cpu_move": 260},
    "normal": {"speed": 1.00, "tol": 3, "count": 1.00, "cpu_think": 1.5, "cpu_err": 0.13, "cpu_move": 420},
    "hard":   {"speed": 1.25, "tol": 2, "count": 1.10, "cpu_think": 0.85, "cpu_err": 0.05, "cpu_move": 650},
}

# ---------------------------------------------------------------- colours
BG_TOP = (26, 18, 64)
BG_BOTTOM = (8, 40, 92)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 221, 64)
RED = (255, 72, 88)
GREEN = (80, 230, 120)
CYAN = (90, 220, 255)
PINK = (255, 120, 200)
ORANGE = (255, 160, 60)
GREY = (150, 160, 190)
PANEL = (20, 24, 56)


# ---------------------------------------------------------------- paths
def resource_path(*parts):
    """Locate bundled assets both from source and from a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir():
    """Per-user writable folder for settings, scores and parent statistics."""
    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(root, "ShoukuGames", APP_NAME)
    elif sys.platform == "darwin":
        path = os.path.expanduser("~/Library/Application Support/" + APP_NAME)
    else:
        root = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = os.path.join(root, APP_ID)
    os.makedirs(path, exist_ok=True)
    return path
