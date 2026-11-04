"""Title screen, high-score name entry, credits and the For Parents screen."""
import datetime as _dt
import math
import random

import pygame

from . import i18n, ui
from .config import (APP_NAME, AUTHORS, BUILD, BUILD_DATE, CYAN, DIFFICULTIES, EMAIL, GREEN, GREY,
                     ORANGE, RED, SCREEN_H, SCREEN_W, STUDIO, URL, VERSION, WHITE, YELLOW)
from .effects import Fireworks
from .i18n import T

DIGIT_KEYS = {getattr(pygame, "K_%d" % i): str(i) for i in range(10)}
DIGIT_KEYS.update({getattr(pygame, "K_KP%d" % i): str(i) for i in range(10)})


def version_line():
    return "v%s   %s %s   %s %s" % (VERSION, T("build"), BUILD, T("build_date"), BUILD_DATE)


class TextInput:
    """Single-line text field with IME (Japanese input) support."""

    def __init__(self, text="", maxlen=12):
        self.text = text
        self.comp = ""
        self.maxlen = maxlen
        self.active = False

    def start(self, rect=None):
        self.active = True
        self.comp = ""
        pygame.key.start_text_input()
        if rect is not None:
            try:
                pygame.key.set_text_input_rect(pygame.Rect(rect))
            except Exception:
                pass

    def stop(self):
        self.active = False
        self.comp = ""
        pygame.key.stop_text_input()

    def handle(self, e):
        if e.type == pygame.TEXTINPUT:
            for ch in e.text:
                if ch.isprintable() and len(self.text) < self.maxlen:
                    self.text += ch
            self.comp = ""
        elif e.type == pygame.TEXTEDITING:
            self.comp = e.text
        elif e.type == pygame.KEYDOWN:
            if self.comp:
                return None
            if e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "done"
            elif e.key == pygame.K_ESCAPE:
                return "cancel"
        return None

    def display(self, t):
        cursor = "|" if int(t * 2) % 2 == 0 else " "
        return self.text + (("[" + self.comp + "]") if self.comp else "") + cursor


class FloatingBubbles:
    def __init__(self, n=18):
        self.items = []
        for _ in range(n):
            self.items.append(self._new(random.uniform(0, SCREEN_H)))

    @staticmethod
    def _new(y=None):
        return [random.uniform(0, SCREEN_W), y if y is not None else SCREEN_H + 30,
                random.uniform(18, 45), random.choice(range(15, 166, 15)), random.uniform(0, 6)]

    def update(self, dt):
        for b in self.items:
            b[1] -= b[2] * dt
            b[4] += dt
        self.items = [b for b in self.items if b[1] > -40] + \
            [self._new() for b in self.items if b[1] <= -40]

    def draw(self, surf, fonts):
        for b in self.items:
            ui.draw_bubble(surf, b[3], b[0] + math.sin(b[4]) * 10, b[1], fonts, 0.8, alpha=90)


def draw_logo(surf, fonts, t, y=78):
    word = APP_NAME.upper()
    size = 92
    widths = [fonts.width(ch, size) for ch in word]
    total = sum(widths) + 6 * (len(word) - 1)
    x = SCREEN_W // 2 - total // 2
    for i, ch in enumerate(word):
        col = ui.label_color(int((i / max(1, len(word) - 1)) * 160) + 10)
        bob = math.sin(t * 3 + i * 0.6) * 6
        fonts.draw(surf, ch, size, (x, y + bob), col, "midleft", outline=(10, 10, 40), ow=4)
        x += widths[i] + 6
    fonts.draw(surf, T("title_sub"), 26, (SCREEN_W // 2, y + 64), WHITE, "center", outline=(0, 0, 0))


# ======================================================================
class TitleScene:
    def __init__(self, app, highlight=None):
        self.app = app
        self.t = 0.0
        self.highlight = highlight
        self.bubbles = FloatingBubbles()
        self.name_input = None
        items = [
            {"id": "start", "label": lambda: T("menu_start")},
            {"id": "continue", "label": lambda: T("menu_continue", n=self.best()),
             "show": lambda: self.best() > 1},
            {"id": "battle", "label": lambda: T("menu_battle")},
            {"id": "difficulty", "label": lambda: "%s:  ◀ %s ▶" % (T("menu_difficulty"), T(app.difficulty))},
            {"id": "name", "label": self._name_label},
            {"id": "lang", "label": lambda: "%s:  ◀ %s ▶" % (T("menu_lang"), T("lang_name"))},
            {"id": "bgm", "label": lambda: "%s:  %s" % (T("menu_bgm"), T("on") if app.audio.bgm_on else T("off"))},
            {"id": "parents", "label": lambda: T("menu_parents")},
            {"id": "credits", "label": lambda: T("menu_credits")},
            {"id": "quit", "label": lambda: T("menu_quit")},
        ]
        self.menu = ui.Menu(items, 96, 212, spacing=44, size=25, width=540)

    def best(self):
        return min(100, self.app.store.best_level(self.app.player, self.app.difficulty))

    def _name_label(self):
        if self.name_input and self.name_input.active:
            return "%s:  %s" % (T("menu_name"), self.name_input.display(self.t))
        return "%s:  %s" % (T("menu_name"), self.app.player)

    def enter(self):
        self.app.audio.play_music("main")

    # ------------------------------------------------------------ input
    def activate(self, item, direction=0):
        app = self.app
        iid = item["id"]
        if iid == "start":
            app.audio.sfx("select")
            from .scene_game import GameScene
            app.switch(GameScene(app, 1))
        elif iid == "continue":
            app.audio.sfx("select")
            from .scene_game import GameScene
            app.switch(GameScene(app, self.best()))
        elif iid == "battle":
            app.audio.sfx("select")
            from .scene_battle import BattleScene
            app.switch(BattleScene(app))
        elif iid == "difficulty":
            i = DIFFICULTIES.index(app.difficulty)
            i = (i + (direction or 1)) % len(DIFFICULTIES)
            app.store.set("difficulty", DIFFICULTIES[i])
            app.audio.sfx("move")
        elif iid == "name":
            if direction == 0:
                self.name_input = TextInput(app.player, 12)
                r = self.menu.rects[self.menu.index] if self.menu.rects else None
                self.name_input.start(r)
                app.audio.sfx("select")
        elif iid == "lang":
            i18n.set_lang("ja" if i18n.get_lang() == "en" else "en")
            app.store.set("lang", i18n.get_lang())
            app.audio.sfx("move")
        elif iid == "bgm":
            app.audio.set_bgm(not app.audio.bgm_on)
            app.store.set("bgm", app.audio.bgm_on)
            app.audio.sfx("move")
        elif iid == "parents":
            app.audio.sfx("select")
            app.switch(ParentsScene(app))
        elif iid == "credits":
            app.audio.sfx("select")
            app.switch(CreditsScene(app))
        elif iid == "quit":
            app.quit()

    def handle(self, e):
        if self.name_input and self.name_input.active:
            r = self.name_input.handle(e)
            if r == "done":
                name = self.name_input.text.strip()
                if name:
                    self.app.store.set("name", name)
                self.name_input.stop()
                self.app.audio.sfx("select")
            elif r == "cancel":
                self.name_input.stop()
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.menu.move(-1)
                self.app.audio.sfx("move")
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.menu.move(1)
                self.app.audio.sfx("move")
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                it = self.menu.current()
                if it and it["id"] in ("difficulty", "lang", "bgm"):
                    self.activate(it, -1 if e.key in (pygame.K_LEFT, pygame.K_a) else 1)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                it = self.menu.current()
                if it:
                    self.activate(it)
            elif e.key == pygame.K_ESCAPE:
                pass
        elif e.type == pygame.MOUSEMOTION:
            i = self.menu.hit(e.pos)
            if i is not None and i != self.menu.index:
                self.menu.index = i
                self.app.audio.sfx("move")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            i = self.menu.hit(e.pos)
            if i is not None:
                self.menu.index = i
                self.activate(self.menu.current())

    def update(self, dt):
        self.t += dt
        self.bubbles.update(dt)

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        f = self.app.fonts
        surf.blit(ui.background(), (0, 0))
        self.bubbles.draw(surf, f)
        draw_logo(surf, f, self.t)
        ui.panel(surf, (60, 186, 600, 452), (14, 18, 48), (80, 100, 200), 190)
        self.menu.draw(surf, f, self.t)
        if self.name_input and self.name_input.active:
            f.draw(surf, T("name_edit_hint"), 18, (360, 646), YELLOW, "center", outline=(0, 0, 0))
        self.draw_scores(surf, f)
        f.draw(surf, T("title_hint"), 17, (SCREEN_W // 2, 676), GREY, "center")
        f.draw(surf, version_line(), 15, (SCREEN_W - 12, SCREEN_H - 8), (150, 160, 210), "bottomright")
        f.draw(surf, "© 2026 " + STUDIO, 15, (12, SCREEN_H - 8), (150, 160, 210), "bottomleft")

    def draw_scores(self, surf, f):
        rect = pygame.Rect(690, 186, 530, 452)
        ui.panel(surf, rect, (14, 18, 48), (255, 200, 80), 200)
        f.draw(surf, "★ " + T("top10") + " ★", 28, (rect.centerx, rect.y + 30), YELLOW, "center",
               outline=(0, 0, 0))
        scores = self.app.store.scores
        if not scores:
            f.draw(surf, T("no_scores"), 20, (rect.centerx, rect.centery), GREY, "center")
            return
        for i, e in enumerate(scores[:10]):
            y = rect.y + 76 + i * 37
            hl = self.highlight == i and int(self.t * 4) % 2 == 0
            col = YELLOW if i == 0 else (CYAN if i < 3 else WHITE)
            if hl:
                pygame.draw.rect(surf, (90, 70, 20), (rect.x + 12, y - 16, rect.w - 24, 32), border_radius=8)
            f.draw(surf, "%2d." % (i + 1), 20, (rect.x + 24, y), col, "midleft")
            f.draw(surf, str(e.get("name", "?"))[:12], 20, (rect.x + 78, y), col, "midleft")
            f.draw(surf, "%d" % e.get("score", 0), 20, (rect.x + 360, y), col, "midright")
            f.draw(surf, "%s%d" % (T("lv"), e.get("level", 1)), 17, (rect.x + 375, y), GREY, "midleft")
            d = e.get("difficulty", "normal")
            dcol = {"easy": GREEN, "normal": CYAN, "hard": RED}.get(d, WHITE)
            f.draw(surf, T(d), 15, (rect.right - 20, y), dcol, "midright")


# ======================================================================
class NameEntryScene:
    def __init__(self, app, score, level, difficulty):
        self.app = app
        self.score, self.level, self.diff = score, level, difficulty
        self.rank = app.store.score_rank(score) or 10
        self.input = TextInput(app.player, 12)
        self.t = 0.0
        self.fw = Fireworks(SCREEN_W, SCREEN_H, None)
        self.fw.rate = 0.7

    def enter(self):
        self.input.start((440, 380, 400, 60))
        self.app.audio.play_music("main")

    def leave(self):
        self.input.stop()

    def on_quit(self):
        name = self.input.text.strip() or self.app.player
        self.app.store.add_score(name, self.score, self.level, self.diff)

    def handle(self, e):
        r = self.input.handle(e)
        if r == "done":
            name = self.input.text.strip() or self.app.player
            self.app.store.set("name", name)
            idx = self.app.store.add_score(name, self.score, self.level, self.diff)
            self.app.audio.sfx("select")
            self.app.switch(TitleScene(self.app, highlight=idx))
        elif r == "cancel":
            idx = self.app.store.add_score(self.app.player, self.score, self.level, self.diff)
            self.app.switch(TitleScene(self.app, highlight=idx))

    def update(self, dt):
        self.t += dt
        self.fw.update(dt)

    def draw(self, surf):
        f = self.app.fonts
        surf.blit(ui.background(), (0, 0))
        self.fw.draw(surf, f)
        pulse = 1 + 0.05 * math.sin(self.t * 6)
        f.draw(surf, T("new_record"), int(64 * pulse), (SCREEN_W // 2, 150), YELLOW, "center",
               outline=(80, 20, 0), ow=4)
        f.draw(surf, T("rank_n", n=self.rank), 40, (SCREEN_W // 2, 232), CYAN, "center", outline=(0, 0, 0))
        f.draw(surf, T("final_score", s=self.score, l=self.level), 28, (SCREEN_W // 2, 292), WHITE, "center",
               outline=(0, 0, 0))
        box = pygame.Rect(0, 0, 460, 70)
        box.center = (SCREEN_W // 2, 400)
        ui.panel(surf, box, (20, 24, 60), YELLOW, 230)
        f.draw(surf, self.input.display(self.t), 36, box.center, WHITE, "center")
        f.draw(surf, T("enter_name"), 22, (SCREEN_W // 2, 480), GREY, "center", outline=(0, 0, 0))


# ======================================================================
class CreditsScene:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.bubbles = FloatingBubbles(14)

    def handle(self, e):
        if (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE,
                                                  pygame.K_BACKSPACE)) or \
                (e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3)):
            self.app.audio.sfx("select")
            self.app.switch(TitleScene(self.app))

    def update(self, dt):
        self.t += dt
        self.bubbles.update(dt)

    def draw(self, surf):
        f = self.app.fonts
        surf.blit(ui.background(), (0, 0))
        self.bubbles.draw(surf, f)
        draw_logo(surf, f, self.t, 70)
        ui.panel(surf, (190, 170, 900, 490), (14, 18, 48), (90, 110, 220), 215)
        cx = SCREEN_W // 2
        f.draw(surf, T("credits"), 34, (cx, 205), YELLOW, "center", outline=(0, 0, 0))
        rows = [
            (T("created_by"), AUTHORS, WHITE),
            (T("studio"), STUDIO, WHITE),
            ("URL", URL, CYAN),
            ("Email", EMAIL, CYAN),
            (T("version"), "v" + VERSION, GREEN),
            (T("build"), BUILD, GREEN),
            (T("build_date"), BUILD_DATE, GREEN),
        ]
        y = 258
        for k, v, col in rows:
            f.draw(surf, k, 22, (cx - 20, y), GREY, "midright")
            f.draw(surf, v, 24, (cx + 10, y), col, "midleft", outline=(0, 0, 0))
            y += 40
        y += 8
        f.draw(surf, T("third_party"), 18, (cx, y), ORANGE, "center")
        for line in (T("tp_pop"), T("tp_font"), T("tp_pygame")):
            y += 26
            f.draw(surf, line, 16, (cx, y), (200, 205, 230), "center")
        f.draw(surf, T("back"), 18, (cx, 690), GREY, "center")


# ======================================================================
def fmt_hm(sec):
    sec = int(sec)
    h, m = sec // 3600, (sec % 3600) // 60
    if h == 0:
        return T("ms", m=m, s=sec % 60)
    return T("hm", h=h, m=m)


def result_text(s):
    r = s.get("result")
    n = s.get("end_level", 1)
    return {
        "time": T("res_time", n=n), "floor": T("res_floor", n=n), "quit": T("res_quit", n=n),
        "allclear": T("res_allclear"), "win": T("res_win"), "lose": T("res_lose"),
        "draw": T("res_draw"), "bquit": T("res_bquit"),
    }.get(r, str(r))


class ParentsScene:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.unlocked = False
        self.a, self.b = random.randint(6, 9), random.randint(3, 9)
        self.answer = ""
        self.msg = ""
        self.player_idx = 0
        self.scroll = 0
        self.confirm_reset = 0.0
        names = app.store.player_names()
        self.players = [None] + names
        if app.player in names:
            self.player_idx = self.players.index(app.player)

    def back(self):
        self.app.audio.sfx("select")
        self.app.switch(TitleScene(self.app))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            self.back()
            return
        if e.type != pygame.KEYDOWN:
            if e.type == pygame.MOUSEWHEEL and self.unlocked:
                self.scroll = max(0, self.scroll - e.y)
            return
        if not self.unlocked:
            if e.key == pygame.K_ESCAPE:
                self.back()
            elif e.key in DIGIT_KEYS and len(self.answer) < 3:
                self.answer += DIGIT_KEYS[e.key]
            elif e.key == pygame.K_BACKSPACE:
                self.answer = self.answer[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.answer == str(self.a * self.b):
                    self.unlocked = True
                    self.app.audio.sfx("select")
                else:
                    self.msg = T("gate_wrong")
                    self.answer = ""
                    self.a, self.b = random.randint(6, 9), random.randint(3, 9)
                    self.app.audio.sfx("wrong")
            return
        if e.key == pygame.K_ESCAPE:
            self.back()
        elif e.key in (pygame.K_LEFT, pygame.K_a):
            self.player_idx = (self.player_idx - 1) % len(self.players)
            self.scroll = 0
            self.app.audio.sfx("move")
        elif e.key in (pygame.K_RIGHT, pygame.K_d):
            self.player_idx = (self.player_idx + 1) % len(self.players)
            self.scroll = 0
            self.app.audio.sfx("move")
        elif e.key in (pygame.K_UP, pygame.K_w):
            self.scroll = max(0, self.scroll - 1)
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            self.scroll += 1
        elif e.key == pygame.K_DELETE:
            if self.confirm_reset > 0:
                self.app.store.reset_stats()
                self.players = [None]
                self.player_idx = 0
                self.confirm_reset = 0
                self.msg = T("reset_done")
                self.app.audio.sfx("wrong")
            else:
                self.confirm_reset = 4.0
                self.msg = T("reset_confirm")

    def update(self, dt):
        self.t += dt
        if self.confirm_reset > 0:
            self.confirm_reset -= dt
            if self.confirm_reset <= 0 and self.msg == T("reset_confirm"):
                self.msg = ""

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        f = self.app.fonts
        surf.blit(ui.background(top=(18, 26, 40), bottom=(12, 30, 54)), (0, 0))
        f.draw(surf, T("parents"), 34, (SCREEN_W // 2, 36), YELLOW, "center", outline=(0, 0, 0))
        if not self.unlocked:
            self.draw_gate(surf, f)
        else:
            self.draw_stats(surf, f)

    def draw_gate(self, surf, f):
        box = pygame.Rect(0, 0, 700, 300)
        box.center = (SCREEN_W // 2, SCREEN_H // 2)
        ui.panel(surf, box, (20, 26, 50), (120, 150, 230), 230)
        f.draw(surf, T("gate_q"), 22, (box.centerx, box.y + 60), WHITE, "center")
        f.draw(surf, "%d × %d = %s" % (self.a, self.b, self.answer + ("_" if int(self.t * 2) % 2 == 0 else " ")),
               48, (box.centerx, box.centery + 10), YELLOW, "center")
        if self.msg:
            f.draw(surf, self.msg, 20, (box.centerx, box.bottom - 50), RED, "center")
        f.draw(surf, T("back"), 16, (SCREEN_W // 2, SCREEN_H - 24), GREY, "center")

    def draw_stats(self, surf, f):
        store = self.app.store
        name = self.players[self.player_idx] if self.player_idx < len(self.players) else None
        sess = store.sessions(name)
        single = [s for s in sess if s.get("mode") == "single"]
        label = name if name else T("all_players")
        f.draw(surf, "◀  %s: %s  ▶" % (T("player"), label), 24, (SCREEN_W // 2, 78), CYAN, "center",
               outline=(0, 0, 0))

        today = _dt.date.today()
        week_start = today - _dt.timedelta(days=6)

        def sdate(s):
            try:
                return _dt.date.fromisoformat(s.get("date", "")[:10])
            except Exception:
                return None

        total = sum(s.get("duration", 0) for s in sess)
        t_today = sum(s.get("duration", 0) for s in sess if sdate(s) == today)
        t_week = sum(s.get("duration", 0) for s in sess if sdate(s) and sdate(s) >= week_start)
        pops = sum(s.get("pops", 0) for s in sess)
        misses = sum(s.get("misses", 0) for s in sess)
        acc = "%d%%" % round(100 * pops / (pops + misses)) if pops + misses else "-"
        best_score = max([s.get("score", 0) for s in single] or [0])
        best_level = max([s.get("end_level", 0) for s in single] or [0])
        cards = [(T("total_time"), fmt_hm(total)), (T("today"), fmt_hm(t_today)), (T("week"), fmt_hm(t_week)),
                 (T("games"), str(len(sess))), (T("best_score"), str(best_score)),
                 (T("best_level"), str(best_level) if best_level else "-"), (T("accuracy"), acc)]
        cw = (SCREEN_W - 60 - 6 * 10) // 7
        for i, (k, v) in enumerate(cards):
            r = pygame.Rect(30 + i * (cw + 10), 104, cw, 78)
            ui.panel(surf, r, (22, 30, 60), (80, 110, 190), 230, 10)
            f.draw(surf, k, 14, (r.centerx, r.y + 18), GREY, "center")
            f.draw(surf, v, 24, (r.centerx, r.y + 50), WHITE, "center")

        # ---- chart: level reached per game
        cr = pygame.Rect(30, 196, 790, 232)
        ui.panel(surf, cr, (18, 24, 48), (70, 90, 160), 230, 10)
        f.draw(surf, T("chart_title"), 16, (cr.x + 14, cr.y + 14), WHITE, "topleft")
        last = single[-30:]
        plot = pygame.Rect(cr.x + 46, cr.y + 44, cr.w - 66, cr.h - 74)
        top = max([10] + [s.get("end_level", 1) for s in last])
        top = int(math.ceil(top / 10.0) * 10)
        for k in range(0, 6):
            v = top * k / 5
            y = plot.bottom - plot.h * k / 5
            pygame.draw.line(surf, (45, 55, 95), (plot.x, y), (plot.right, y), 1)
            f.draw(surf, "%d" % v, 12, (plot.x - 6, y), GREY, "midright")
        if last:
            bw = plot.w / 30.0
            for i, s in enumerate(last):
                lv = s.get("end_level", 1)
                h = max(2, plot.h * lv / top)
                col = {"time": RED, "floor": ORANGE, "quit": GREY, "allclear": YELLOW}.get(s.get("result"), CYAN)
                pygame.draw.rect(surf, col, (plot.x + i * bw + 2, plot.bottom - h, bw - 4, h), border_radius=3)
            lx = plot.x
            for col, key in ((RED, "leg_time"), (ORANGE, "leg_floor"), (GREY, "leg_quit"), (YELLOW, "leg_clear")):
                pygame.draw.rect(surf, col, (lx, cr.bottom - 20, 12, 12))
                rr = f.draw(surf, T(key), 12, (lx + 16, cr.bottom - 14), GREY, "midleft")
                lx = rr.right + 18
        else:
            f.draw(surf, T("none_yet"), 18, plot.center, GREY, "center")

        # ---- most failed levels
        fr = pygame.Rect(836, 196, 414, 232)
        ui.panel(surf, fr, (18, 24, 48), (70, 90, 160), 230, 10)
        f.draw(surf, T("failed_levels"), 16, (fr.x + 14, fr.y + 14), WHITE, "topleft")
        fails = {}
        for s in single:
            if s.get("result") in ("time", "floor"):
                fails[s.get("end_level", 1)] = fails.get(s.get("end_level", 1), 0) + 1
        top_fails = sorted(fails.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        if top_fails:
            mx = max(v for _, v in top_fails)
            for i, (lv, cnt) in enumerate(top_fails):
                y = fr.y + 54 + i * 28
                f.draw(surf, "%s %d" % (T("lv"), lv), 16, (fr.x + 20, y), WHITE, "midleft")
                w = int((fr.w - 150) * cnt / mx)
                pygame.draw.rect(surf, RED, (fr.x + 90, y - 8, w, 16), border_radius=4)
                f.draw(surf, "×%d" % cnt, 15, (fr.x + 96 + w, y), GREY, "midleft")
        else:
            f.draw(surf, "-", 20, fr.center, GREY, "center")

        # ---- recent games table
        tr = pygame.Rect(30, 442, SCREEN_W - 60, 236)
        ui.panel(surf, tr, (18, 24, 48), (70, 90, 160), 230, 10)
        f.draw(surf, T("recent"), 16, (tr.x + 14, tr.y + 12), WHITE, "topleft")
        cols = [(T("h_date"), 18), (T("player"), 190), (T("h_mode"), 330), (T("h_diff"), 430),
                (T("h_result"), 540), (T("h_score"), 900), (T("h_time"), 1030)]
        for h, x in cols:
            f.draw(surf, h, 14, (tr.x + x, tr.y + 42), GREY, "midleft")
        rows = list(reversed(sess))
        per = 6
        self.scroll = min(self.scroll, max(0, len(rows) - per))
        for i, s in enumerate(rows[self.scroll:self.scroll + per]):
            y = tr.y + 70 + i * 26
            vals = [s.get("date", "")[:16], str(s.get("name", ""))[:12],
                    T("mode_battle") if s.get("mode") == "battle" else T("mode_single"),
                    T(s.get("difficulty", "normal")), result_text(s), str(s.get("score", 0)),
                    fmt_hm(s.get("duration", 0))]
            for (h, x), v in zip(cols, vals):
                col = WHITE
                if h == T("h_result"):
                    col = RED if s.get("result") in ("time", "floor", "lose") else \
                        YELLOW if s.get("result") in ("allclear", "win") else (200, 205, 230)
                f.draw(surf, v, 15, (tr.x + x, y), col, "midleft")
        if not rows:
            f.draw(surf, T("none_yet"), 18, (tr.centerx, tr.centery + 10), GREY, "center")
        elif len(rows) > per:
            f.draw(surf, "%d-%d / %d" % (self.scroll + 1, min(len(rows), self.scroll + per), len(rows)), 13,
                   (tr.right - 14, tr.y + 14), GREY, "topright")
        if self.msg:
            f.draw(surf, self.msg, 18, (SCREEN_W // 2, SCREEN_H - 34), RED, "center", outline=(0, 0, 0))
        f.draw(surf, T("parents_hint"), 14, (SCREEN_W // 2, SCREEN_H - 12), GREY, "center")
