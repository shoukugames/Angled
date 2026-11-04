"""Persistent settings, top-10 scoreboard, progress and parent statistics."""
import datetime as _dt
import json
import os

from .config import data_dir

DEFAULT = {
    "settings": {"lang": "en", "bgm": True, "difficulty": "normal", "name": "PLAYER"},
    "scores": [],
    "progress": {},
    "sessions": [],
}
MAX_SESSIONS = 1000


def now_iso():
    return _dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")


class Storage:
    def __init__(self, path=None):
        self.path = path or os.path.join(data_dir(), "save.json")
        self.data = json.loads(json.dumps(DEFAULT))
        self.load()

    # ------------------------------------------------------------ io
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k, v in DEFAULT.items():
                if k not in d or not isinstance(d[k], type(v)):
                    d[k] = json.loads(json.dumps(v))
            for k, v in DEFAULT["settings"].items():
                d["settings"].setdefault(k, v)
            self.data = d
        except FileNotFoundError:
            pass
        except Exception:
            # corrupt file: keep a backup and start fresh
            try:
                os.replace(self.path, self.path + ".bad")
            except Exception:
                pass

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        except Exception:
            pass

    # ------------------------------------------------------------ settings
    @property
    def settings(self):
        return self.data["settings"]

    def set(self, key, value):
        self.data["settings"][key] = value
        self.save()

    # ------------------------------------------------------------ scores
    @property
    def scores(self):
        return self.data["scores"]

    def score_rank(self, score):
        """1-based rank this score would get, or None if it does not make the top 10."""
        if score <= 0:
            return None
        lst = sorted(self.scores, key=lambda e: -e["score"])
        for i, e in enumerate(lst):
            if score > e["score"]:
                return i + 1
        return len(lst) + 1 if len(lst) < 10 else None

    def add_score(self, name, score, level, difficulty):
        entry = {"name": name, "score": int(score), "level": int(level),
                 "difficulty": difficulty, "date": now_iso()[:10]}
        lst = self.scores + [entry]
        lst.sort(key=lambda e: -e["score"])
        self.data["scores"] = lst[:10]
        self.save()
        try:
            return self.data["scores"].index(entry)
        except ValueError:
            return None

    def hiscore(self):
        return max([e["score"] for e in self.scores] or [0])

    # ------------------------------------------------------------ progress
    def best_level(self, name, difficulty):
        return int(self.data["progress"].get(name, {}).get(difficulty, 1))

    def note_level(self, name, difficulty, level):
        p = self.data["progress"].setdefault(name, {})
        if level > p.get(difficulty, 1):
            p[difficulty] = int(level)
            self.save()

    # ------------------------------------------------------------ sessions
    def add_session(self, **rec):
        rec.setdefault("date", now_iso())
        self.data["sessions"].append(rec)
        self.data["sessions"] = self.data["sessions"][-MAX_SESSIONS:]
        self.save()

    def sessions(self, name=None):
        s = self.data["sessions"]
        if name:
            s = [x for x in s if x.get("name") == name]
        return s

    def player_names(self):
        names = []
        for x in self.data["sessions"]:
            n = x.get("name")
            if n and n not in names:
                names.append(n)
        return names

    def reset_stats(self):
        self.data["sessions"] = []
        self.data["progress"] = {}
        self.data["scores"] = []
        self.save()
