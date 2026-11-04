# Changelog

## v0.1.2 — 2026-11-04

* Space is now the only fire key during play. ↑ / W and Enter no longer shoot (left click still does).
  The in-game control hints and README are updated.

## v0.1.1 — 2026-11-04

* **Fixed launcher:** the launcher stays in the centre of the floor. ← → / A D turn the arrow
  (hold to turn faster, Shift for 5° steps, mouse wheel for 1°).
* **Strike-angle rule:** a bubble's number is now the spot on its edge the shot must touch
  (0° right edge, 90° bottom, 180° left edge), within ±5° on Easy, ±3° on Normal and ±2° on Hard.
  Off-centre hits and wall bank shots reach every spot.
* The number of wall bounces a label may need grows with the level (Easy up to 3, Normal 4, Hard 5).
* When the descending ceiling moves a bubble so its number can't be struck any more, the number
  updates and the bubble flashes. If nothing can be popped, the lowest open bubble gets a strikeable number.
* The guide line (levels 1–10) marks the exact strike spot and its angle. New rules diagram in the side panel.
* All 300 levels and the battle layouts regenerated and re-proven for the new rules. Easy has 75% of the bubbles (was 85%).
* Fixed: the game could freeze while the guide line was shown (infinite loop drawing the dashed line).
* Fixed: battle garbage bubbles could get unreachable angles.

## v0.1.0 — 2026-11-04 (build 20261104)

First release by Shouku Games (created by Shawn Rapaz and Claude Code).

* Angle-matching bubble popping: a shot must arrive at the bubble's written angle.
  Wall bank shots mirror the angle.
* 100 progressively harder levels, each proven solvable. 99-second countdown per level.
* The ceiling descends faster and faster as the bubbles near the floor. A panic music theme plays when danger is high or time is short.
* Guide line on levels 1–10.
* Easy / Normal / Hard difficulty.
* VS CPU split-screen battle: popped bubbles move to the opponent's side.
* Top 10 scoreboard on the title screen, with name entry for new records.
* English / Japanese language toggle, BGM on/off toggle.
* For Parents screen behind a parental gate: play time, levels reached and failed, scores, accuracy.
* Fireworks + congratulations after level 99, and an all-clear ending after level 100.
* Real recorded bubble pops (CC0). Synthesized upbeat music.
* Windows `.exe` and Debian/Ubuntu `.deb` builds.
