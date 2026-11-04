"""Application entry point and main loop."""
import os
import sys
import traceback

import pygame

from . import i18n
from .assets import Audio, Fonts
from .config import APP_NAME, FPS, SCREEN_H, SCREEN_W, VERSION, data_dir, resource_path
from .storage import Storage


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
        except Exception:
            pass
        pygame.display.set_caption("%s v%s" % (APP_NAME, VERSION))
        try:
            pygame.display.set_icon(pygame.image.load(resource_path("assets", "icon.png")))
        except Exception:
            pass
        flags = pygame.SCALED | pygame.RESIZABLE
        try:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags, vsync=1)
        except Exception:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.key.stop_text_input()
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.audio = Audio()
        self.store = Storage()
        s = self.store.settings
        i18n.set_lang(s.get("lang", "en"))
        self.audio.bgm_on = bool(s.get("bgm", True))
        self.running = True
        self.t = 0.0
        self.scene = None
        from .scenes_menu import TitleScene
        self.switch(TitleScene(self))

    # ------------------------------------------------------------ helpers
    @property
    def difficulty(self):
        d = self.store.settings.get("difficulty", "normal")
        return d if d in ("easy", "normal", "hard") else "normal"

    @property
    def player(self):
        return self.store.settings.get("name") or "PLAYER"

    def switch(self, scene):
        old = self.scene
        if old is not None and hasattr(old, "leave"):
            old.leave()
        self.scene = scene
        if hasattr(scene, "enter"):
            scene.enter()

    def quit(self):
        if self.scene is not None and hasattr(self.scene, "on_quit"):
            try:
                self.scene.on_quit()
            except Exception:
                pass
        self.running = False

    # ------------------------------------------------------------ loop
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.t += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                    break
                if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    continue
                self.scene.handle(e)
            if not self.running:
                break
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


def main():
    log_path = None
    try:
        log_path = os.path.join(data_dir(), "angled.log")
    except Exception:
        pass
    try:
        App().run()
    except Exception:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    import datetime
                    f.write("\n=== %s  v%s ===\n%s" % (datetime.datetime.now(), VERSION, msg))
            except Exception:
                pass
        raise


if __name__ == "__main__":
    main()
