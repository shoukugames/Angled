"""Single-player game: 100 levels, 99-second timer, fireworks after level 99."""
import math

import pygame

from . import ui
from .config import (CELEBRATE_AFTER, CYAN, FIELD_W, GREEN, GREY, GUIDE_LEVELS, LEVEL_TIME, LEVELS,
                     ORANGE, PINK, RED, SCREEN_H, SCREEN_W, WHITE, YELLOW)
from .effects import Fireworks
from .field import Field
from .i18n import T
from .levels import get_level, level_params

FIELD_X = (SCREEN_W - FIELD_W) // 2


class GameScene:
    def __init__(self, app, start_level=1):
        self.app = app
        self.diff = app.difficulty
        self.name = app.player
        self.start_level = max(1, min(LEVELS, start_level))
        self.level = self.start_level
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.levels_cleared = 0
        self.field = Field(FIELD_X, app.audio, app.fonts)
        self.state = "ready"
        self.state_t = 0.0
        self.timer = float(LEVEL_TIME)
        self.last_tick = 99
        self.play_time = 0.0
        self.t = 0.0
        self.message = None   # (text, sub, colour, time_left)
        self.pause_index = 0
        self.prev_state = None
        self.fail_reason = None
        self.bonus = (0, 0)
        self.fw = None
        self.recorded = False
        self.mouse_slide = False
        self.load_level()

    # ------------------------------------------------------------ level flow
    def load_level(self):
        p = level_params(self.level, self.diff)
        self.field.base_speed = p["speed"]
        self.field.tol = p["tol"]
        self.field.label_pool = p["labels"]
        self.field.load(get_level(self.level, self.diff))
        self.timer = float(LEVEL_TIME)
        self.last_tick = 99
        self.state = "ready"
        self.state_t = 0.0
        self.message = None
        self.app.store.note_level(self.name, self.diff, self.level)

    @property
    def guide(self):
        return self.level <= GUIDE_LEVELS

    def enter(self):
        self.app.audio.play_music("main")

    def leave(self):
        pygame.key.stop_text_input()

    def on_quit(self):
        self.record("quit")

    def record(self, result):
        if self.recorded:
            return
        self.recorded = True
        self.app.store.add_session(
            name=self.name, mode="single", difficulty=self.diff, start_level=self.start_level,
            end_level=self.level, result=result, score=int(self.score), duration=int(self.play_time),
            pops=self.field.pops, misses=self.field.misses, levels_cleared=self.levels_cleared,
            best_combo=self.best_combo)

    def finish(self):
        """Leave after game over / all clear: name entry if top-10, else title."""
        from .scenes_menu import NameEntryScene, TitleScene
        if self.app.store.score_rank(self.score):
            self.app.switch(NameEntryScene(self.app, self.score, self.level, self.diff))
        else:
            self.app.switch(TitleScene(self.app))

    # ------------------------------------------------------------ input
    def handle(self, e):
        f = self.field
        if self.state == "paused":
            self.handle_pause(e)
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE and self.state in ("ending", "over") and self.state_t > 2.0:
                self.advance_from_overlay()
                return
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                if self.state in ("ready", "play"):
                    self.prev_state = self.state
                    self.state = "paused"
                    self.pause_index = 0
                    f.move_dir = f.rot_dir = 0
                    self.app.audio.sfx("select")
                return
            if self.state in ("celebrate", "ending", "over"):
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.state_t > 2.0:
                    self.advance_from_overlay()
                return
            if self.state != "play":
                return
            if e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                d = 1 if e.key in (pygame.K_UP, pygame.K_w) else -1
                step = 5 if (e.mod & pygame.KMOD_SHIFT) else 1
                f.nudge_angle(d * step)
                f.rot_dir, f.rot_step, f.rot_timer = d, step, 0.28
            elif e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                f.fire()
        elif e.type == pygame.KEYUP:
            if e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                keys = pygame.key.get_pressed()
                if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
                    f.rot_dir = 0
        elif e.type == pygame.MOUSEMOTION and self.state == "play":
            if self.mouse_slide:
                f.launch_x = f.clamp_x(e.pos[0])
            else:
                f.aim_at(*e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if self.state in ("celebrate", "ending", "over") and e.button == 1 and self.state_t > 2.0:
                self.advance_from_overlay()
            elif self.state == "play":
                if e.button == 1:
                    f.fire()
                elif e.button == 3:
                    self.mouse_slide = True
                    f.launch_x = f.clamp_x(e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 3:
            self.mouse_slide = False
        elif e.type == pygame.MOUSEWHEEL and self.state == "play":
            f.slide(-e.y * 10 if e.flipped else e.y * 10)

    def handle_pause(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = self.prev_state
            elif e.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self.pause_index = 1 - self.pause_index
                self.app.audio.sfx("move")
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.pause_choose()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(getattr(self, "_pause_rects", [])):
                if r.collidepoint(e.pos):
                    self.pause_index = i
                    self.pause_choose()

    def pause_choose(self):
        self.app.audio.sfx("select")
        if self.pause_index == 0:
            self.state = self.prev_state
        else:
            self.record("quit")
            from .scenes_menu import TitleScene
            self.app.switch(TitleScene(self.app))

    def advance_from_overlay(self):
        self.app.audio.sfx("select")
        if self.state == "celebrate":
            self.fw = None
            self.level += 1
            self.load_level()
            self.app.audio.play_music("main")
        elif self.state == "ending":
            self.record("allclear")
            self.finish()
        elif self.state == "over":
            self.finish()

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        if self.state == "paused":
            return
        self.state_t += dt
        f = self.field
        if self.state in ("ready", "play", "clear"):
            self.play_time += dt
        if self.state == "play":
            keys = pygame.key.get_pressed()
            f.move_dir = (1 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0) - \
                         (1 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else 0)
        else:
            f.move_dir = 0
            f.rot_dir = 0

        if self.state == "ready":
            f.update(dt, descend=False)
            if self.state_t >= 2.0:
                self.state = "play"
                self.state_t = 0.0
                self.app.audio.sfx("go")
        elif self.state == "play":
            self.timer = max(0.0, self.timer - dt)
            sec = int(math.ceil(self.timer))
            if sec <= 10 and sec != self.last_tick and sec > 0:
                self.app.audio.sfx("tick")
            self.last_tick = sec
            for ev in f.update(dt):
                self.on_event(ev)
            if self.state == "play":
                if f.cleared():
                    self.level_clear()
                elif self.timer <= 0:
                    self.game_over("time")
            danger = f.danger > 0.72 or self.timer < 15
            if self.state == "play":
                self.app.audio.play_music("danger" if danger else "main")
        elif self.state == "clear":
            f.update(dt, descend=False)
            if self.state_t >= 3.0:
                if self.level == CELEBRATE_AFTER:
                    self.state = "celebrate"
                    self.state_t = 0.0
                    self.fw = Fireworks(SCREEN_W, SCREEN_H, self.app.audio)
                    self.fw.rate = 0.25
                    self.app.audio.play_music("fanfare")
                elif self.level >= LEVELS:
                    self.state = "ending"
                    self.state_t = 0.0
                    self.record("allclear")
                    self.fw = Fireworks(SCREEN_W, SCREEN_H, self.app.audio)
                    self.fw.rate = 0.18
                    self.app.audio.play_music("fanfare")
                else:
                    self.level += 1
                    self.load_level()
        elif self.state in ("celebrate", "ending"):
            self.fw.update(dt)
            if self.state_t > 7.5 and self.app.audio.current == "fanfare":
                self.app.audio.play_music("main")
        elif self.state == "over":
            f.update(dt, descend=False)
        if self.message:
            self.message[3] -= dt
            if self.message[3] <= 0:
                self.message = None

    def on_event(self, ev):
        f = self.field
        kind = ev[0]
        if kind == "pop":
            _, cell, label, (x, y), bounces, dropped = ev
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            mult = min(5, self.combo)
            pts = 100 * mult + 50 * bounces
            self.score += pts
            f.fx.text(x, y - 10, "+%d" % pts, 22, YELLOW, 0.9)
            if bounces:
                f.fx.text(x, y - 40, T("bank", n=bounces), 22, CYAN, 1.1)
            elif self.combo >= 3:
                f.fx.text(x, y - 40, T("great") if self.combo >= 5 else T("nice"), 22, PINK, 0.9)
            if dropped:
                dp = 150 * len(dropped) * mult
                self.score += dp
                cx = sum(d[2][0] for d in dropped) / len(dropped)
                cy = sum(d[2][1] for d in dropped) / len(dropped)
                f.fx.text(cx, cy, T("drop", n=dp), 24, GREEN, 1.2)
        elif kind == "wrong":
            _, cell, label, arr, (x, y) = ev
            self.combo = 0
            self.message = [T("wrong"), T("wrong_detail", a=label, b=arr), RED, 2.0]
        elif kind == "fizzle":
            self.combo = 0
        elif kind == "dead":
            self.game_over("floor")

    def level_clear(self):
        self.state = "clear"
        self.state_t = 0.0
        tb = int(math.ceil(self.timer)) * 50
        lb = self.level * 100
        self.bonus = (tb, lb)
        self.score += tb + lb
        self.levels_cleared += 1
        self.app.audio.sfx("clear")
        self.app.audio.play_music("main")
        self.app.store.note_level(self.name, self.diff, min(LEVELS, self.level + 1))
        for i in range(5):
            self.field.fx.burst(FIELD_X + 40 + i * 90, 300, ui.label_color(i * 40), 30, 300, 1.0, 5)

    def game_over(self, reason):
        self.state = "over"
        self.state_t = 0.0
        self.fail_reason = reason
        self.field.dead = True
        self.app.audio.play_music(None)
        self.app.audio.sfx("gameover")
        for c in list(self.field.grid):
            x, y = self.field.pos(c)
            self.field.fx.burst(x, y, (120, 120, 140), 4, 120, 0.8, 3)
        self.record(reason)

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        fo = self.app.fonts
        surf.blit(ui.background(), (0, 0))
        f = self.field
        f.draw(surf, show_guide=self.guide and self.state == "play")
        self.draw_left(surf, fo)
        self.draw_right(surf, fo)
        cx = FIELD_X + FIELD_W // 2
        if self.message:
            a = min(1.0, self.message[3] / 0.4) * 255
            fo.draw(surf, self.message[0], 34, (cx, 420), self.message[2], "center", outline=(0, 0, 0), ow=3,
                    alpha=a)
            fo.draw(surf, self.message[1], 20, (cx, 458), WHITE, "center", outline=(0, 0, 0), alpha=a)
        if self.state == "ready":
            ui.dim(surf, 90)
            if self.level == LEVELS:
                fo.draw(surf, T("final_level"), 46, (cx, 250), PINK, "center", outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("ready", n=self.level), 60, (cx, 320), YELLOW, "center", outline=(0, 0, 0), ow=4)
            fo.draw(surf, T("ready2") if self.state_t < 1.4 else T("go"), 40, (cx, 390), WHITE, "center",
                    outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("guide_on") if self.guide else T("guide_off"), 20, (cx, 450),
                    GREEN if self.guide else ORANGE, "center", outline=(0, 0, 0))
        elif self.state == "clear":
            fo.draw(surf, T("clear"), 54, (cx, 300), YELLOW, "center", outline=(0, 0, 0), ow=4)
            if self.state_t > 0.6:
                fo.draw(surf, T("time_bonus", n=self.bonus[0]), 26, (cx, 370), CYAN, "center", outline=(0, 0, 0))
            if self.state_t > 1.1:
                fo.draw(surf, T("level_bonus", n=self.bonus[1]), 26, (cx, 408), GREEN, "center", outline=(0, 0, 0))
            if self.level == GUIDE_LEVELS and self.state_t > 1.6:
                fo.draw(surf, T("guide_off"), 20, (cx, 460), ORANGE, "center", outline=(0, 0, 0))
        elif self.state == "over":
            ui.dim(surf, min(170, int(self.state_t * 200)))
            fo.draw(surf, T("time_up") if self.fail_reason == "time" else T("floor_hit"),
                    30 if self.fail_reason != "time" else 48, (SCREEN_W // 2, 260), ORANGE, "center",
                    outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("game_over"), 72, (SCREEN_W // 2, 340), RED, "center", outline=(0, 0, 0), ow=4)
            fo.draw(surf, T("final_score", s=self.score, l=self.level), 30, (SCREEN_W // 2, 420), WHITE,
                    "center", outline=(0, 0, 0))
            if self.state_t > 2.0:
                fo.draw(surf, T("press_key"), 22, (SCREEN_W // 2, 480), GREY, "center", outline=(0, 0, 0))
        elif self.state in ("celebrate", "ending"):
            self.draw_celebration(surf, fo)
        if self.state == "paused":
            self.draw_pause(surf, fo)

    def draw_celebration(self, surf, fo):
        ui.dim(surf, 190)
        self.fw.draw(surf, fo)
        t = self.state_t
        sc = min(1.0, t / 0.6)
        pulse = 1 + 0.06 * math.sin(t * 5)
        hue_col = ui.label_color(int((t * 60) % 180))
        if self.state == "celebrate":
            fo.draw(surf, T("congrats"), int(84 * sc * pulse) + 1, (SCREEN_W // 2, 230), hue_col, "center",
                    outline=(40, 0, 60), ow=5)
            fo.draw(surf, T("congrats_99"), 40, (SCREEN_W // 2, 340), YELLOW, "center", outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("final_score", s=self.score, l=self.level), 28, (SCREEN_W // 2, 400), WHITE,
                    "center", outline=(0, 0, 0))
            if t > 2.0:
                fo.draw(surf, T("congrats_more"), 24, (SCREEN_W // 2, 470), CYAN, "center", outline=(0, 0, 0))
                fo.draw(surf, T("press_key"), 22, (SCREEN_W // 2, 520), GREY, "center", outline=(0, 0, 0))
        else:
            fo.draw(surf, T("congrats"), int(84 * sc * pulse) + 1, (SCREEN_W // 2, 210), hue_col, "center",
                    outline=(40, 0, 60), ow=5)
            fo.draw(surf, T("all_clear"), 44, (SCREEN_W // 2, 320), YELLOW, "center", outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("all_clear2"), 32, (SCREEN_W // 2, 380), PINK, "center", outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("final_score", s=self.score, l=self.level), 28, (SCREEN_W // 2, 440), WHITE,
                    "center", outline=(0, 0, 0))
            if t > 2.0:
                fo.draw(surf, T("press_key"), 22, (SCREEN_W // 2, 510), GREY, "center", outline=(0, 0, 0))

    def draw_pause(self, surf, fo):
        ui.dim(surf, 160)
        fo.draw(surf, T("paused"), 60, (SCREEN_W // 2, 260), YELLOW, "center", outline=(0, 0, 0), ow=4)
        self._pause_rects = []
        for i, key in enumerate(("resume", "to_title")):
            r = pygame.Rect(0, 0, 380, 50)
            r.center = (SCREEN_W // 2, 360 + i * 64)
            self._pause_rects.append(r)
            sel = i == self.pause_index
            ui.panel(surf, r, (40, 50, 120) if sel else (20, 24, 56), YELLOW if sel else (80, 100, 200), 220, 10)
            fo.draw(surf, T(key), 26, r.center, YELLOW if sel else WHITE, "center")

    def draw_left(self, surf, fo):
        x, w = 28, FIELD_X - 60
        ui.panel(surf, (x, 40, w, 640))
        cx = x + w // 2
        fo.draw(surf, T("level"), 18, (cx, 70), GREY, "center")
        fo.draw(surf, "%d / %d" % (self.level, LEVELS), 40, (cx, 108), YELLOW, "center", outline=(0, 0, 0))
        fo.draw(surf, T("score"), 18, (cx, 160), GREY, "center")
        fo.draw(surf, "%d" % self.score, 36, (cx, 196), WHITE, "center", outline=(0, 0, 0))
        fo.draw(surf, T("hiscore"), 16, (cx, 244), GREY, "center")
        fo.draw(surf, "%d" % max(self.score, self.app.store.hiscore()), 24, (cx, 272), CYAN, "center")
        fo.draw(surf, T("difficulty"), 16, (cx, 316), GREY, "center")
        dcol = {"easy": GREEN, "normal": CYAN, "hard": RED}[self.diff]
        fo.draw(surf, T(self.diff), 24, (cx, 344), dcol, "center")
        fo.draw(surf, T("combo"), 16, (cx, 388), GREY, "center")
        fo.draw(surf, "x%d" % min(5, max(1, self.combo)), 30, (cx, 420), PINK if self.combo >= 2 else WHITE,
                "center", outline=(0, 0, 0))
        # rules reminder with a small diagram
        y = 480
        for k in ("rule_1", "rule_2"):
            fo.draw(surf, T(k), 17, (cx, y), WHITE, "center")
            y += 24
        y += 10
        for k in ("rule_3", "rule_4"):
            fo.draw(surf, T(k), 15, (cx, y), (190, 200, 240), "center")
            y += 21
        # tiny bank-shot diagram
        bx, by = cx, 650
        pygame.draw.line(surf, (110, 130, 210), (bx + 60, by - 46), (bx + 60, by + 10), 3)
        pygame.draw.line(surf, CYAN, (bx - 40, by), (bx + 60, by - 26), 2)
        pygame.draw.line(surf, ORANGE, (bx + 60, by - 26), (bx - 20, by - 46), 2)
        fo.draw(surf, "60°", 13, (bx - 40, by - 12), CYAN, "center")
        fo.draw(surf, "120°", 13, (bx - 28, by - 54), ORANGE, "center")

    def draw_right(self, surf, fo):
        x = FIELD_X + FIELD_W + 32
        w = SCREEN_W - x - 28
        ui.panel(surf, (x, 40, w, 640))
        cx = x + w // 2
        fo.draw(surf, T("time"), 18, (cx, 70), GREY, "center")
        sec = int(math.ceil(self.timer))
        col = WHITE
        size = 72
        if sec <= 10:
            pulse = 0.5 + 0.5 * math.sin(self.t * 12)
            col = (255, int(80 + 100 * pulse), int(80 + 60 * pulse))
            size = int(72 + 8 * pulse)
        elif sec <= 30:
            col = ORANGE
        fo.draw(surf, "%02d" % sec, size, (cx, 130), col, "center", outline=(0, 0, 0), ow=3)
        # time bar
        bar = pygame.Rect(x + 24, 180, w - 48, 12)
        pygame.draw.rect(surf, (40, 44, 80), bar, border_radius=6)
        fill = bar.copy()
        fill.w = int(bar.w * self.timer / LEVEL_TIME)
        pygame.draw.rect(surf, col, fill, border_radius=6)
        # angle readout
        fo.draw(surf, T("angle"), 18, (cx, 228), GREY, "center")
        fo.draw(surf, "%d°" % self.field.angle, 56, (cx, 276), YELLOW, "center", outline=(0, 0, 0), ow=3)
        fo.draw(surf, T("guide_on") if self.guide else T("guide_off"), 14, (cx, 324),
                GREEN if self.guide else ORANGE, "center")
        # danger meter
        p = self.field.danger
        bar = pygame.Rect(x + 24, 346, w - 48, 10)
        pygame.draw.rect(surf, (40, 44, 80), bar, border_radius=5)
        fill = bar.copy()
        fill.w = int(bar.w * p)
        pygame.draw.rect(surf, RED if p > 0.7 else ORANGE if p > 0.45 else GREEN, fill, border_radius=5)
        y = 392
        fo.draw(surf, T("ctl_title"), 17, (cx, y), CYAN, "center")
        for k in ("ctl_1", "ctl_2", "ctl_3", "ctl_4", "ctl_5", "ctl_6"):
            y += 30
            fo.draw(surf, T(k), 15, (cx, y), (200, 205, 235), "center")
        fo.draw(surf, self.name, 18, (cx, 640), WHITE, "center")
