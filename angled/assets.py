"""Fonts (mixed Latin/Japanese rendering), sounds and music."""
import random

import pygame

from .config import resource_path

LATIN_FONT = resource_path("assets", "fonts", "DejaVuSans-Bold.ttf")
JP_FONT = resource_path("assets", "fonts", "DroidSansFallbackFull.ttf")


def _is_jp(ch):
    o = ord(ch)
    return (0x3000 <= o <= 0x9FFF) or (0xFF00 <= o <= 0xFFEF) or (0xF900 <= o <= 0xFAFF) \
        or (0x3400 <= o <= 0x4DBF)


class Fonts:
    def __init__(self):
        self._latin = {}
        self._jp = {}
        self._cache = {}

    def _font(self, size, jp):
        table = self._jp if jp else self._latin
        f = table.get(size)
        if f is None:
            try:
                f = pygame.font.Font(JP_FONT if jp else LATIN_FONT, int(size * (1.12 if jp else 1.0)))
            except Exception:
                f = pygame.font.Font(None, size)
            table[size] = f
        return f

    def _plain(self, s, size, color):
        runs = []
        for ch in s:
            jp = _is_jp(ch)
            if runs and runs[-1][0] == jp:
                runs[-1][1].append(ch)
            else:
                runs.append((jp, [ch]))
        parts = []
        asc = 0
        desc = 0
        for jp, chars in runs:
            f = self._font(size, jp)
            surf = f.render("".join(chars), True, color)
            a = f.get_ascent()
            parts.append((surf, a))
            asc = max(asc, a)
            desc = max(desc, surf.get_height() - a)
        w = sum(p[0].get_width() for p in parts) or 1
        h = max(1, asc + desc)
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 0
        for surf, a in parts:
            out.blit(surf, (x, asc - a))
            x += surf.get_width()
        return out

    def render(self, s, size, color=(255, 255, 255), outline=None, ow=2):
        key = (s, size, color, outline, ow)
        surf = self._cache.get(key)
        if surf is not None:
            return surf
        base = self._plain(s, size, color)
        if outline:
            o = self._plain(s, size, outline)
            out = pygame.Surface((base.get_width() + ow * 2, base.get_height() + ow * 2), pygame.SRCALPHA)
            for dx in range(-ow, ow + 1):
                for dy in range(-ow, ow + 1):
                    if dx * dx + dy * dy <= ow * ow + 1:
                        out.blit(o, (dx + ow, dy + ow))
            out.blit(base, (ow, ow))
            base = out
        if len(self._cache) > 1500:
            self._cache.clear()
        self._cache[key] = base
        return base

    def draw(self, target, s, size, pos, color=(255, 255, 255), anchor="topleft",
             outline=None, ow=2, alpha=None):
        surf = self.render(s, size, color, outline, ow)
        if alpha is not None and alpha < 255:
            surf = surf.copy()
            surf.set_alpha(max(0, int(alpha)))
        rect = surf.get_rect(**{anchor: pos})
        target.blit(surf, rect)
        return rect

    def width(self, s, size):
        return self.render(s, size).get_width()


class Audio:
    MUSIC = {"main": "bgm_main.wav", "danger": "bgm_danger.wav", "fanfare": "fanfare.wav"}
    SFX = ["shoot", "bounce", "wrong", "drop", "fizzle", "move", "select", "tick", "go",
           "clear", "gameover", "whoosh", "fw_launch", "fw_boom"]

    def __init__(self):
        self.ok = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.pops = []
        self.music = {}
        self.bgm_on = True
        self.current = None
        self.channels = {}
        if not self.ok:
            return
        pygame.mixer.set_num_channels(24)
        pygame.mixer.set_reserved(3)
        self.channels = {"main": pygame.mixer.Channel(0), "danger": pygame.mixer.Channel(1),
                         "fanfare": pygame.mixer.Channel(2)}
        for name in self.SFX:
            self.sounds[name] = self._load(resource_path("assets", "sounds", name + ".wav"))
        for i in range(1, 7):
            snd = self._load(resource_path("assets", "sounds", "pop%d.wav" % i))
            if snd:
                self.pops.append(snd)
        for k, fn in self.MUSIC.items():
            self.music[k] = self._load(resource_path("assets", "music", fn))
        vols = {"shoot": 0.45, "bounce": 0.5, "move": 0.5, "tick": 0.6, "whoosh": 0.6,
                "fw_launch": 0.5, "fw_boom": 0.8}
        for k, v in vols.items():
            if self.sounds.get(k):
                self.sounds[k].set_volume(v)
        for k, snd in self.music.items():
            if snd:
                snd.set_volume(0.55)

    @staticmethod
    def _load(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None

    def sfx(self, name, volume=None):
        if not self.ok:
            return
        snd = self.sounds.get(name)
        if snd:
            ch = snd.play()
            if ch and volume is not None:
                ch.set_volume(volume)

    def pop(self, volume=1.0):
        if self.ok and self.pops:
            ch = random.choice(self.pops).play()
            if ch:
                ch.set_volume(volume)

    def play_music(self, name, fade_ms=600):
        """Switch background track ('main', 'danger', 'fanfare' or None)."""
        if not self.ok:
            self.current = name
            return
        if name == self.current and (not self.bgm_on or self.channels[name].get_busy()):
            return
        for k, ch in self.channels.items():
            if k != name:
                ch.fadeout(fade_ms)
        self.current = name
        if name and self.bgm_on and self.music.get(name):
            loops = 0 if name == "fanfare" else -1
            self.channels[name].play(self.music[name], loops=loops, fade_ms=fade_ms if loops else 0)

    def set_bgm(self, on):
        self.bgm_on = on
        if not self.ok:
            return
        if not on:
            for ch in self.channels.values():
                ch.stop()
        else:
            cur, self.current = self.current, None
            self.play_music(cur or "main")
