# Angled — Bug Reports

**Version:** v0.1.1 · **Date:** 2026-11-04 (the exact build id is in the Credits screen)
**Studio:** Shouku Games — <https://shoukugames.org/>

Thanks for helping make Angled better! Please send bug reports to
**info@shoukugames.org** with the subject `Angled bug: <short summary>`.

## Before you report

1. Check the version: open **Credits** on the title screen (or look at the window title).
   Please include the **version and build number**.
2. Look for a crash log and attach it if it exists:
   * Windows: `%APPDATA%\ShoukuGames\Angled\angled.log`
   * Linux: `~/.local/share/angled/angled.log`
3. If the bug involves scores, progress or the For Parents screen, also attach
   `save.json` from the same folder. It contains only player names, scores and play times.

## Bug report template

Copy this into your email:

```
Version / build:      v0.1.1 / 20261104.xxxxxxx
Operating system:     (e.g. Windows 11 64-bit, Ubuntu 24.04)
Installed from:       (Windows .exe / .deb package / source)
Language:             (English / 日本語)
Mode & difficulty:    (Solo / VS CPU, Easy / Normal / Hard)
Level:                (e.g. 37)

What happened:
  ...

What I expected:
  ...

Steps to reproduce:
  1.
  2.
  3.

How often:            (every time / sometimes / once)
Screenshot or video:  (attached? yes/no)
angled.log attached:  (yes/no)
```

### Severity guide

| Severity | Examples |
|---|---|
| **Critical** | Crash, game won't start, save data lost |
| **Major** | A level can't be cleared, wrong pop/no-pop decision, scoreboard not saving |
| **Minor** | Visual glitch, text overflow, translation mistake |
| **Suggestion** | Balance, ideas, new features |

## Known issues (v0.1.1)

| # | Issue | Workaround |
|---|---|---|
| 1 | Windows SmartScreen / antivirus may warn about the unsigned `.exe` (common for PyInstaller-built games). | *More info → Run anyway*, or build from source. |
| 2 | The one-file Windows `.exe` takes a few seconds to start the first time while it unpacks itself. | Wait a moment. Later starts are faster. |
| 3 | Japanese name entry depends on the operating system's IME. With some Linux IMEs the composition text appears only after you press Enter. | Type in romaji or switch IME. |
| 4 | Late levels on Hard (≈ 70+) are tuned for expert players and may take several attempts. | Try Normal or Easy. Continue restarts from the furthest level reached. |

## Fixed bugs log

| Version | Fix |
|---|---|
| v0.1.0 | First release. |
| v0.1.1 | Game could freeze (stop responding) while the guide line was shown, caused by a floating-point infinite loop when drawing the dashed line. |
| v0.1.1 | The launcher is now fixed in the centre and ← → turn the arrow. Labels re-adjust when descent moves a bubble so its number can't be struck any more, so garbage bubbles in battle no longer get unreachable angles. |
