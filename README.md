# Angled — v0.1.0

**Pop each bubble at the angle written inside it!** / **かくどを あわせて ポン！**

Angled is a physics bubble-popping game about angles and trick shots, inspired by
classic bubble shooters. Every bubble shows an angle like `60°`. Your shot has to
be travelling at that exact angle when it touches the bubble, or the bubble won't pop.
Bounce off the walls for trick shots: a bank shot mirrors the angle, so a shot
fired at 60° arrives at 120° after one bounce.

| | |
|---|---|
| **Version** | v0.1.0 |
| **Build** | `20261104.fe2da27` (shown in the Credits screen and the window title) |
| **Build date** | 2026-11-04 |
| **Created by** | Shawn Rapaz and Claude Code |
| **Studio** | Shouku Games — <https://shoukugames.org/> — info@shoukugames.org |
| **License** | GPL v3 (see `LICENSE`) |

---

## Download / install

| Platform | File | How to run |
|---|---|---|
| Windows 10/11 (64-bit) | `dist/Angled-v0.1.0-win64.exe` | Double-click it. It's a single portable file with no installer. Windows SmartScreen may warn about an unsigned app: choose *More info → Run anyway*. |
| Debian / Ubuntu / Mint (amd64) | `dist/angled_0.1.0_amd64.deb` | `sudo apt install ./angled_0.1.0_amd64.deb`, then start **Angled** from the menu, or run `angled`. Remove with `sudo apt remove angled`. |
| From source (any OS) | this folder | `pip install pygame` then `python3 run.py` |

---

## How to play

1. Read the angle inside a bubble, for example **75°**.
2. Turn the launcher to that angle. The big number next to the arrow shows your current angle.
3. Slide the launcher left/right until the shot lines up with the bubble, then fire.
4. If the direction of travel matches the bubble's number when it touches → **POP!**
   If not → *clank!*: the bubble stays and the ceiling drops a little as a penalty.

**Trick shots:** angles are measured like a protractor (0° = right, 90° = straight up,
180° = left). Each wall bounce flips the angle: `angle → 180° − angle`. Steep
bubbles high up often need a bank shot.

**Pressure:** the ceiling keeps pushing the bubbles down, and it gets **faster and
faster** the closer they get to the floor (the music switches to a panic theme too).
If a bubble crosses the red line by the launcher, it's game over. Each level also has a
**99-second countdown**. Left-over seconds become a time bonus.

**Guide line:** on levels 1–10 a dotted line predicts where the shot will go and
what angle it will arrive at (green = it will pop). From level 11 on, you're on your own.

**Drops:** bubbles that are no longer connected to the ceiling fall off for bonus points.

### Controls

| Action | Keyboard | Mouse |
|---|---|---|
| Slide launcher | ← → or A D | mouse wheel, or hold right button and drag |
| Change angle | ↑ ↓ or W S (hold to speed up) | point the mouse where you want to aim |
| Change angle by 5° | Shift + ↑ ↓ | — |
| Shoot | Space or Enter | left click |
| Pause | Esc or P | — |
| Fullscreen | F11 | — |

### Scoring

| Event | Points |
|---|---|
| Pop | 100 × combo (combo grows with each pop in a row, up to ×5) |
| Bank shot | +50 per wall bounce |
| Dropped bubble | 150 × combo each |
| Level clear | seconds left × 50 + level × 100 |

A wrong angle or a shot that hits the ceiling resets the combo.

---

## Title screen

| Item | What it does |
|---|---|
| **Start Game** | Level 1 on the selected difficulty |
| **Continue (Level N)** | Restart from the furthest level this player has reached on this difficulty |
| **VS CPU Battle** | Split-screen battle (see below) |
| **Difficulty** | Easy / Normal / Hard (← →) |
| **Name** | Press Enter and type (Japanese IME input works). Used for the scoreboard and the parent statistics. |
| **Language** | English ⇄ 日本語 |
| **BGM** | Background music on/off. Sound effects stay on. |
| **For Parents** | Progress screen (see below) |
| **Credits** | Authors, URL, email, version, build and date |
| **TOP 10** | The scoreboard is always shown on the right. A new top-10 score asks for a name. |

## Levels & difficulty

There are 100 levels. Each level gets progressively harder in several ways:

* **More bubbles and more rows** (2 rows at level 1, up to 6).
* **Faster descent** (the base speed rises every level, on top of the speed-up near the floor).
* **Finer angles:** labels start in steps of 15° (60°, 75°, 90°…), then 10°, 5°, 2° and finally any whole degree.
* **Wider angle range:** shallow angles (like 20° or 160°) need bank shots and appear later.
* **No guide line** after level 10.

| Difficulty | Descent speed | Angle tolerance | Bubbles | Angle steps |
|---|---|---|---|---|
| Easy | 70% | ±2° | 85% | 15° → 10° → 5° |
| Normal | 100% | ±1° | 100% | 15° → 10° → 5° → 2° → 1° |
| Hard | 125% | exact | 110% | 10° → 5° → 2° → 1° |

Every level is generated from a fixed seed and **proven solvable** by the build tools
using the game's own physics. The proof requires solutions that still work if you're
a couple of pixels off, and it holds whatever order you pop the bubbles in.

Clearing **level 99** triggers a big **CONGRATULATIONS** fireworks show with a fanfare,
then the **final level 100**. Clearing level 100 shows the all-clear fireworks ending.

## VS CPU battle

Both players start with the same bubbles. **Every bubble you pop or drop disappears
from your side and flies over to the opponent's side** (up to 10 per shot), so a
good shot makes the other side harder. You win if you clear your field, if the CPU's
bubbles reach its floor, or if you have fewer bubbles when the 99-second timer ends.
The CPU's speed and accuracy depend on the difficulty. The guide line is shown in battle
only on Easy.

## For Parents

Open **For Parents** from the title screen and answer the multiplication question
(a simple parental gate). The screen shows, per player or for all players:

* total play time, play time today and in the last 7 days
* games played, best score, highest level reached, shot accuracy
* a chart of the level reached in each of the last 30 games, coloured by how it ended
  (time up, bubbles reached the floor, quit, all clear)
* the levels the child fails most often
* a table of recent games: date, player, mode, difficulty, **which level they failed and why**, score and time spent

Use ← → to switch players, ↑ ↓ to scroll, and press **Delete twice** to erase all play data.

### Where data is stored

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\ShoukuGames\Angled\` |
| Linux | `~/.local/share/angled/` (or `$XDG_DATA_HOME/angled/`) |

`save.json` holds settings, the top 10, progress and play history. `angled.log`
records crashes (attach it to bug reports). Nothing is sent over the network.

---

## Building from source

Requirements: Python 3.11+, `pygame` 2.6, `pyinstaller` 6.x. You also need `numpy`, but only for the asset tools.

```bash
python3 run.py                    # play from source
python3 tools/gen_audio.py        # regenerate music + synthesized sound effects
python3 tools/gen_icon.py         # regenerate assets/icon.png / icon.ico
python3 tools/gen_levels.py       # regenerate + re-prove all levels (assets/levels.json)
./build_linux.sh                  # -> dist/angled_0.1.0_amd64.deb
./build_windows.sh                # -> dist/Angled-v0.1.0-win64.exe (via Wine)
```

`build_windows.bat` builds the .exe natively on Windows.

**One-time Wine setup for `build_windows.sh`** (Windows Python in `C:\py311`):

```bash
curl -L -o py.nupkg https://www.nuget.org/api/v2/package/python/3.11.9
python3 -m zipfile -e py.nupkg py && mkdir -p ~/.wine/drive_c/py311 && cp -r py/tools/* ~/.wine/drive_c/py311/
printf 'C:\\py311\\python.exe -m ensurepip\r\nC:\\py311\\python.exe -m pip install pygame==2.6.1 pyinstaller\r\n' > ~/.wine/drive_c/setup.bat
wine cmd /c 'C:\setup.bat' </dev/null
```

Every build stamps `angled/build_info.py` with the build id (`YYYYMMDD.<git sha>`)
and date, and embeds the version in the Windows file properties.

### Project layout

```
angled/          game package
  main.py        window, main loop, crash log
  config.py      constants, version, paths
  physics.py     hex grid, ray casting with wall bounces, shot solver
  levels.py      level parameters + solvable level generator
  field.py       one playfield (grid, descent, launcher, shots, garbage)
  scene_game.py  single player (levels, timer, celebration)
  scene_battle.py VS CPU battle
  scenes_menu.py title/top 10/name entry, credits, For Parents
  cpu.py         CPU opponent
  effects.py     particles and fireworks
  i18n.py        English / Japanese text
assets/          fonts, music, sounds, icon, levels.json
tools/           asset generators and build helpers
```

## Credits

* **Created by:** Shawn Rapaz and Claude Code
* **Studio:** Shouku Games — <https://shoukugames.org/> — info@shoukugames.org
* **Version:** v0.1.0 (build 20261104.fe2da27, 2026-11-04)
* **Pop sounds:** real bubble-wrap pops recorded by Joseph Sardin, [BigSoundBank](https://bigsoundbank.com/) #0462, CC0
* **Music & other sound effects:** synthesized for this game (`tools/gen_audio.py`)
* **Fonts:** DejaVu Sans Bold (Bitstream Vera / DejaVu license), Droid Sans Fallback (Apache 2.0)
* **Engine:** [pygame](https://www.pygame.org/) (LGPL)
