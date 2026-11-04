"""Split-screen battle against the CPU.

Every bubble you pop (or drop) disappears from your field and flies over to
the opponent's field, so good play makes the other side harder.
"""
import math

import pygame

from . import ui
from .config import CYAN, FIELD_W, GREY, LEVEL_TIME, ORANGE, PINK, RED, SCREEN_W, WHITE, YELLOW
from .cpu import CPU
from .effects import Fireworks
from .field import Field
from .i18n import T
from .levels import battle_params, get_battle

LEFT_X = 92
RIGHT_X = SCREEN_W - 92 - FIELD_W
MAX_SEND = 10


class BattleScene:
    def __init__(self, app, round_index=0, wins=(0, 0)):
        self.app = app
        self.diff = app.difficulty
        self.name = app.player
        self.round = round_index
        self.wins = list(wins)
        p = battle_params(self.diff)
        layout = get_battle(self.diff, round_index)
        self.me = Field(LEFT_X, app.audio, app.fonts, p["speed"], p["tol"], p["labels"])
        self.cpu_f = Field(RIGHT_X, app.audio, app.fonts, p["speed"], p["tol"], p["labels"])
        for fld in (self.me, self.cpu_f):
            fld.label_step = p["step"]
            fld.max_bounces = p["bounces"]
            fld.load(layout)
        self.cpu_f.label_timer = 0.1   # stagger the two fields' label checks
        self.cpu = CPU(self.cpu_f, self.diff)
        self.timer = float(LEVEL_TIME)
        self.last_tick = 99
        self.state = "ready"
        self.state_t = 0.0
        self.t = 0.0
        self.play_time = 0.0
        self.result = None
        self.recorded = False
        self.message = None
        self.paused = False
        self.fw = None
        self.sent = [0, 0]

    def enter(self):
        self.app.audio.play_music("main")

    def on_quit(self):
        self.record("bquit")

    def record(self, result):
        if self.recorded:
            return
        self.recorded = True
        self.app.store.add_session(
            name=self.name, mode="battle", difficulty=self.diff, start_level=0, end_level=0,
            result=result, score=self.me.pops * 100, duration=int(self.play_time),
            pops=self.me.pops, misses=self.me.misses, levels_cleared=0)

    # ------------------------------------------------------------ input
    def handle(self, e):
        f = self.me
        if e.type == pygame.KEYDOWN:
            if self.state == "over":
                if self.state_t > 1.0:
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        self.app.audio.sfx("select")
                        self.app.switch(BattleScene(self.app, self.round + 1, self.wins))
                    elif e.key == pygame.K_ESCAPE:
                        self.to_title()
                return
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = not self.paused
                f.rot_dir = 0
                self.app.audio.sfx("select")
                return
            if self.paused:
                if e.key in (pygame.K_q, pygame.K_BACKSPACE):
                    self.record("bquit")
                    self.to_title()
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.paused = False
                return
            if self.state != "play":
                return
            if f.rotate_key_down(e):
                pass
            elif e.key == pygame.K_SPACE:   # Space is the only fire key
                f.fire()
        elif e.type == pygame.KEYUP:
            f.rotate_key_up(e)
        elif self.paused:
            return
        elif e.type == pygame.MOUSEMOTION and self.state == "play":
            f.aim_at(*e.pos)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "play" and e.button == 1:
                f.fire()
            elif self.state == "over" and e.button == 1 and self.state_t > 1.0:
                self.app.switch(BattleScene(self.app, self.round + 1, self.wins))
        elif e.type == pygame.MOUSEWHEEL and self.state == "play":
            f.wheel(e)

    def to_title(self):
        from .scenes_menu import TitleScene
        self.app.audio.sfx("select")
        self.app.switch(TitleScene(self.app))

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        if self.paused:
            return
        self.state_t += dt
        if self.state in ("ready", "play"):
            self.play_time += dt
        if self.state == "ready":
            self.me.update(dt, descend=False)
            self.cpu_f.update(dt, descend=False)
            if self.state_t > 2.0:
                self.state = "play"
                self.state_t = 0
                self.app.audio.sfx("go")
            return
        if self.state == "play":
            self.timer = max(0.0, self.timer - dt)
            sec = int(math.ceil(self.timer))
            if sec <= 10 and sec != self.last_tick and sec > 0:
                self.app.audio.sfx("tick")
            self.last_tick = sec
            self.cpu.update(dt)
            for ev in self.me.update(dt):
                self.on_event(ev, self.me, self.cpu_f, 0)
            for ev in self.cpu_f.update(dt):
                self.on_event(ev, self.cpu_f, self.me, 1)
            self.check_end()
            danger = self.me.danger > 0.72 or self.timer < 15
            if self.state == "play":
                self.app.audio.play_music("danger" if danger else "main")
        else:
            self.me.rot_dir = 0
            self.me.update(dt, descend=False)
            self.cpu_f.update(dt, descend=False)
            if self.fw:
                self.fw.update(dt)
        if self.message:
            self.message[2] -= dt
            if self.message[2] <= 0:
                self.message = None

    def on_event(self, ev, src, dst, who):
        if ev[0] == "pop":
            _, cell, label, pos, bounces, dropped = ev
            pts = [pos] + [d[2] for d in dropped]
            n = min(MAX_SEND, len(pts))
            dst.receive(n, pts, delay=0.15)
            self.sent[who] += n
            self.app.audio.sfx("whoosh", 0.5)
            if bounces:
                src.fx.text(pos[0], pos[1] - 30, T("bank", n=bounces), 20, CYAN, 1.0)
            src.fx.text(pos[0], pos[1], "→ %d" % n if who == 0 else "← %d" % n, 22, PINK, 0.9)
        elif ev[0] == "wrong" and who == 0:
            _, cell, label, arr, pos = ev
            self.message = [T("wrong"), T("wrong_detail", a=label, b=arr), 1.8]

    def check_end(self):
        me, cpu = self.me, self.cpu_f
        res = None
        if me.dead and cpu.dead:
            res = "draw"
        elif me.dead:
            res = "lose"
        elif cpu.dead:
            res = "win"
        elif me.cleared():
            res = "win"
        elif cpu.cleared():
            res = "lose"
        elif self.timer <= 0:
            a, b = len(me.grid) + len(me.incoming), len(cpu.grid) + len(cpu.incoming)
            res = "win" if a < b else "lose" if a > b else "draw"
        if res:
            self.state = "over"
            self.state_t = 0.0
            self.result = res
            me.dead = cpu.dead = True
            if res == "win":
                self.wins[0] += 1
                self.app.audio.sfx("clear")
                self.fw = Fireworks(SCREEN_W, 720, self.app.audio)
                self.fw.rate = 0.5
                self.app.audio.play_music("main")
            elif res == "lose":
                self.wins[1] += 1
                self.app.audio.sfx("gameover")
                self.app.audio.play_music(None)
            else:
                self.app.audio.play_music("main")
            self.record(res)

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        fo = self.app.fonts
        surf.blit(ui.background(), (0, 0))
        show_guide = self.diff == "easy" and self.state == "play"
        self.me.draw(surf, show_guide=show_guide, color=YELLOW, title="%s : %s" % (T("you"), self.name))
        self.cpu_f.draw(surf, show_guide=False, color=(255, 120, 160), title=T("cpu"))
        # centre column
        cx = SCREEN_W // 2
        ui.panel(surf, (cx - 92, 40, 184, 640))
        fo.draw(surf, T("time"), 16, (cx, 66), GREY, "center")
        sec = int(math.ceil(self.timer))
        col = (255, 90, 90) if sec <= 10 else ORANGE if sec <= 30 else WHITE
        fo.draw(surf, "%02d" % sec, 60, (cx, 116), col, "center", outline=(0, 0, 0), ow=3)
        fo.draw(surf, T("wins", a=self.wins[0], b=self.wins[1]), 16, (cx, 176), YELLOW, "center")
        fo.draw(surf, T("you"), 16, (cx, 220), YELLOW, "center")
        fo.draw(surf, T("bubbles_left", n=len(self.me.grid)), 15, (cx, 244), WHITE, "center")
        fo.draw(surf, T("cpu"), 16, (cx, 286), (255, 120, 160), "center")
        fo.draw(surf, T("bubbles_left", n=len(self.cpu_f.grid)), 15, (cx, 310), WHITE, "center")
        fo.draw(surf, T(self.diff), 18, (cx, 356), CYAN, "center")
        fo.draw(surf, T("angle"), 15, (cx, 400), GREY, "center")
        fo.draw(surf, "%d°" % self.me.angle, 40, (cx, 436), YELLOW, "center", outline=(0, 0, 0))
        y = 488
        for line in T("battle_rule").replace("!", "!\n").replace("！", "！\n").split("\n"):
            if line.strip():
                for chunk in _wrap(line, 14 if any(ord(c) > 0x3000 for c in line) else 18):
                    fo.draw(surf, chunk, 14, (cx, y), (200, 205, 235), "center")
                    y += 20
        for k in ("ctl_1", "ctl_2", "ctl_4"):
            y += 6
            for chunk in _wrap(T(k), 22):
                fo.draw(surf, chunk, 12, (cx, y), GREY, "center")
                y += 17
        if self.message:
            a = min(1.0, self.message[2] / 0.4) * 255
            mx = LEFT_X + FIELD_W // 2
            fo.draw(surf, self.message[0], 30, (mx, 420), RED, "center", outline=(0, 0, 0), ow=3, alpha=a)
            fo.draw(surf, self.message[1], 17, (mx, 454), WHITE, "center", outline=(0, 0, 0), alpha=a)
        if self.state == "ready":
            ui.dim(surf, 90)
            fo.draw(surf, T("menu_battle"), 54, (cx, 290), YELLOW, "center", outline=(0, 0, 0), ow=4)
            fo.draw(surf, T("ready2") if self.state_t < 1.4 else T("go"), 40, (cx, 360), WHITE, "center",
                    outline=(0, 0, 0), ow=3)
            fo.draw(surf, T("battle_rule"), 22, (cx, 420), CYAN, "center", outline=(0, 0, 0))
        elif self.state == "over":
            ui.dim(surf, 140)
            if self.fw:
                self.fw.draw(surf, fo)
            txt = {"win": T("you_win"), "lose": T("cpu_wins"), "draw": T("draw")}[self.result]
            col = {"win": YELLOW, "lose": RED, "draw": WHITE}[self.result]
            fo.draw(surf, txt, 76, (cx, 300), col, "center", outline=(0, 0, 0), ow=4)
            fo.draw(surf, T("wins", a=self.wins[0], b=self.wins[1]), 28, (cx, 380), WHITE, "center",
                    outline=(0, 0, 0))
            if self.state_t > 1.0:
                fo.draw(surf, T("battle_end"), 22, (cx, 450), GREY, "center", outline=(0, 0, 0))
        if self.paused:
            ui.dim(surf, 160)
            fo.draw(surf, T("paused"), 60, (cx, 300), YELLOW, "center", outline=(0, 0, 0), ow=4)
            fo.draw(surf, "ENTER: " + T("resume") + "     Q: " + T("to_title"), 24, (cx, 380), WHITE, "center",
                    outline=(0, 0, 0))


def _wrap(text, width):
    if len(text) <= width:
        return [text]
    words = text.split(" ")
    if len(words) == 1:
        return [text[i:i + width] for i in range(0, len(text), width)]
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines
