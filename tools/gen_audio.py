#!/usr/bin/env python3
"""Generate the background music and synthesized sound effects for Angled.

The bubble *pop* sounds are NOT generated here: they are real recordings
(assets/sounds/pop1..6.wav, cut from BigSoundBank #0462 "Bubble wrap:
Breakouts" by Joseph Sardin, CC0).

Run:  python3 tools/gen_audio.py
Requires numpy (build-time only; the game itself does not need numpy).
"""
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(ROOT, "assets", "music")
SOUNDS = os.path.join(ROOT, "assets", "sounds")
SR = 32000
rng = np.random.default_rng(1234)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


NOTE_IDX = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
            "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def note(name):
    """'C5' -> midi 72, 'F#4' -> 66"""
    p, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + NOTE_IDX[p]


def osc(kind, f, n, duty=0.5, phase0=0.0):
    t = np.arange(n) / SR
    ph = (f * t + phase0) % 1.0
    if kind == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if kind == "tri":
        return 4.0 * np.abs(ph - 0.5) - 1.0
    if kind == "saw":
        return 2.0 * ph - 1.0
    return np.sin(2 * np.pi * ph)


def env(n, a=0.004, d=0.06, s=0.55, r=0.04):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na, endpoint=False) if na else e[:na]
    nd = min(nd, n - na)
    if nd > 0:
        e[na:na + nd] = np.linspace(1, s, nd)
    nr = min(nr, n)
    if nr > 0:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, k=4):
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def write_wav(path, x, sr=SR, peak=0.89):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) or 1.0
    x = x / m * peak
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print("wrote", os.path.relpath(path, ROOT), "%.2fs" % (len(x) / sr))


class Track:
    def __init__(self, seconds):
        self.buf = np.zeros(int(seconds * SR) + SR)

    def add(self, start, sig):
        i = int(start * SR)
        if i >= len(self.buf):
            return
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += sig[: j - i]

    def tone(self, start, dur, midi, kind="square", vol=0.2, duty=0.5,
             a=0.004, d=0.06, s=0.55, r=0.03, vib=0.0):
        n = int(dur * SR)
        if n <= 0:
            return
        f = hz(midi)
        if vib:
            t = np.arange(n) / SR
            fm = f * (1 + vib * np.sin(2 * np.pi * 6 * t) * np.clip(t / 0.15, 0, 1))
            ph = np.cumsum(fm) / SR
            p = ph % 1.0
            if kind == "square":
                sig = np.where(p < duty, 1.0, -1.0)
            elif kind == "saw":
                sig = 2 * p - 1
            else:
                sig = np.sin(2 * np.pi * p)
        else:
            sig = osc(kind, f, n, duty)
        self.add(start, sig * env(n, a, d, s, r) * vol)

    def kick(self, start, vol=0.9):
        n = int(0.16 * SR)
        t = np.arange(n) / SR
        f = 45 + 110 * np.exp(-t * 35)
        ph = np.cumsum(f) / SR
        sig = np.sin(2 * np.pi * ph) * np.exp(-t * 18)
        self.add(start, sig * vol)

    def snare(self, start, vol=0.45):
        n = int(0.15 * SR)
        t = np.arange(n) / SR
        noise = rng.uniform(-1, 1, n)
        noise = noise - lowpass(noise, 3) * 0.6
        sig = noise * np.exp(-t * 22) + 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30)
        self.add(start, sig * vol)

    def hat(self, start, vol=0.13, open_=False):
        n = int((0.12 if open_ else 0.035) * SR)
        t = np.arange(n) / SR
        noise = rng.uniform(-1, 1, n)
        noise = np.diff(noise, prepend=0)
        sig = noise * np.exp(-t * (25 if open_ else 110))
        self.add(start, sig * vol)

    def crash(self, start, vol=0.3, dur=1.6):
        n = int(dur * SR)
        t = np.arange(n) / SR
        noise = np.diff(rng.uniform(-1, 1, n), prepend=0)
        self.add(start, noise * np.exp(-t * 2.6) * vol)


# chord tables (bass-register triads)
CH = {
    "C": [48, 52, 55], "G": [43, 47, 50], "Am": [45, 48, 52], "F": [41, 45, 48],
    "D": [50, 54, 57], "E": [40, 44, 47], "Dm": [50, 53, 57], "Em": [40, 43, 47],
}


def parse_bar(s):
    """'E5 G5 - . A5' -> list of tokens (one per slot)"""
    return s.split()


def render_lead(tr, bars, t0, bar_len, kind="square", vol=0.22, duty=0.5,
                octave=0, vib=0.004):
    for bi, bar in enumerate(bars):
        toks = parse_bar(bar)
        slot = bar_len / len(toks)
        i = 0
        while i < len(toks):
            tk = toks[i]
            if tk in ("-", "."):
                i += 1
                continue
            j = i + 1
            while j < len(toks) and toks[j] == "-":
                j += 1
            dur = slot * (j - i)
            tr.tone(t0 + bi * bar_len + i * slot, dur * 0.92, note(tk) + octave,
                    kind, vol, duty, d=0.08, s=0.6, vib=vib)
            i = j


# --------------------------------------------------------------------------
# MAIN THEME: upbeat, major key, 150 BPM, with "panic" alarm runs
# --------------------------------------------------------------------------
def gen_main():
    bpm = 150
    beat = 60.0 / bpm
    bar = beat * 4
    chords = ["C", "G", "Am", "F", "C", "G", "F", "G",
              "Am", "F", "C", "G", "Am", "F", "D", "G"]
    lead = [
        "E5 G5 C6 G5 A5 G5 E5 G5",
        "D5 - G5 - B5 A5 G5 D5",
        "C5 E5 A5 - G5 E5 C5 E5",
        "F5 - A5 - C6 - A5 G5",
        "E5 G5 C6 G5 E6 D6 C6 G5",
        "B5 - D6 - B5 A5 G5 -",
        "A5 G5 F5 A5 C6 - A5 -",
        "G5 - . G5 A5 B5 C6 D6",
        "E6 - C6 - A5 - C6 E6",
        "D6 C6 A5 F5 A5 C6 F6 -",
        "E6 D6 C6 G5 E5 G5 C6 E6",
        "D6 - B5 G5 D6 - G6 -",
        "E6 E6 . E6 D6 C6 B5 A5",
        "C6 C6 . C6 A5 G5 F5 A5",
        "F#5 A5 D6 F#6 A6 F#6 D6 A5",
        "G5 G#5 A5 A#5 B5 C6 C#6 D6 D#6 E6 F6 F#6 G6 - - .",  # panic run
    ]
    total = bar * len(chords)
    tr = Track(total)
    for bi, ch in enumerate(chords):
        t = bi * bar
        tones = CH[ch]
        root = tones[0] - 12
        # octave-bounce bass (8ths)
        for k in range(8):
            m = root + (12 if k % 2 else 0)
            tr.tone(t + k * beat / 2, beat / 2 * 0.85, m, "tri", 0.42, d=0.05, s=0.8)
        # 16th-note arpeggio pad, quiet
        arp = [tones[0] + 24, tones[1] + 24, tones[2] + 24, tones[1] + 24]
        for k in range(16):
            tr.tone(t + k * beat / 4, beat / 4 * 0.7, arp[k % 4], "square", 0.045,
                    duty=0.25, d=0.03, s=0.3)
        # drums: four on the floor + backbeat + hats
        for k in range(4):
            tr.kick(t + k * beat)
            tr.hat(t + k * beat + beat / 2, 0.14, open_=(k == 3))
        tr.snare(t + beat)
        tr.snare(t + 3 * beat)
        if bi >= 8:  # second half: 16th hats for urgency
            for k in range(16):
                if k % 2:
                    tr.hat(t + k * beat / 4, 0.07)
        # panic alarm blips in bars 13-16
        if bi >= 12:
            for k in range(16):
                if k % 2 == 1:
                    tr.tone(t + k * beat / 4, beat / 4 * 0.45,
                            95 if (k // 2) % 2 == 0 else 96, "square", 0.035,
                            duty=0.5, d=0.01, s=0.5, r=0.01)
        if bi == len(chords) - 1:  # snare roll into loop point
            for k in range(8, 16):
                tr.snare(t + k * beat / 4, 0.18 + 0.03 * (k - 8))
    render_lead(tr, lead, 0.0, bar, "square", 0.2, duty=0.5)
    render_lead(tr, lead, 0.006, bar, "square", 0.07, duty=0.125, octave=-12)  # chorus layer
    write_wav(os.path.join(MUSIC, "bgm_main.wav"), tr.buf[: int(total * SR)])


# --------------------------------------------------------------------------
# DANGER THEME: minor key, 176 BPM, siren lead -> used when time/space runs out
# --------------------------------------------------------------------------
def gen_danger():
    bpm = 176
    beat = 60.0 / bpm
    bar = beat * 4
    chords = ["Am", "F", "G", "E", "Am", "F", "G", "E"]
    lead = [
        "A5 E5 A5 B5 C6 B5 A5 E5",
        "F5 A5 C6 A5 F5 A5 C6 D6",
        "D6 B5 G5 B5 D6 B5 G5 B5",
        "E6 - D6 - C6 - B5 G#5",
        "A5 C6 E6 C6 A6 - G#6 -",
        "A6 F6 C6 F6 A6 - F6 -",
        "G6 D6 B5 D6 G6 - F6 -",
        "E6 D#6 E6 D#6 E6 D#6 E6 D#6 E6 F6 E6 D#6 E6 G#6 B6 E6",
    ]
    total = bar * len(chords)
    tr = Track(total)
    for bi, ch in enumerate(chords):
        t = bi * bar
        tones = CH[ch]
        root = tones[0] - 12
        for k in range(16):  # driving 16th bass
            m = root + (12 if k % 4 == 2 else 0)
            tr.tone(t + k * beat / 4, beat / 4 * 0.8, m, "square", 0.16, duty=0.25,
                    d=0.03, s=0.7)
            tr.tone(t + k * beat / 4, beat / 4 * 0.8, root - 12, "tri", 0.25, d=0.02, s=0.8)
        for k in range(4):
            tr.kick(t + k * beat, 0.95)
            tr.hat(t + k * beat + beat / 2, 0.15, open_=True)
        for k in range(16):
            tr.hat(t + k * beat / 4, 0.06)
        tr.snare(t + beat, 0.5)
        tr.snare(t + 3 * beat, 0.5)
        tr.snare(t + 3.5 * beat, 0.3)
        # alarm pulses every beat: high fifth stabs
        for k in range(4):
            tr.tone(t + k * beat + beat * 0.75, beat * 0.2, tones[2] + 36, "square",
                    0.03, duty=0.5, d=0.01, s=0.6, r=0.01)
    render_lead(tr, lead, 0.0, bar, "square", 0.2, duty=0.5, vib=0.006)
    render_lead(tr, lead, 0.008, bar, "saw", 0.06, octave=-12)
    write_wav(os.path.join(MUSIC, "bgm_danger.wav"), tr.buf[: int(total * SR)])


# --------------------------------------------------------------------------
# FANFARE (99-level celebration)
# --------------------------------------------------------------------------
def gen_fanfare():
    bpm = 120
    beat = 60.0 / bpm
    trip = beat / 3
    tr = Track(7.0)
    seq = [("G4", 0, 1), ("G4", 1, 1), ("G4", 2, 1), ("C5", 3, 3), ("E5", 6, 3),
           ("G5", 9, 6), ("E5", 15, 2), ("G5", 17, 1), ("C6", 18, 12)]
    for nm, st, ln in seq:
        tr.tone(st * trip, ln * trip * 0.95, note(nm), "saw", 0.22, a=0.01, d=0.1,
                s=0.75, r=0.08, vib=0.006 if ln >= 6 else 0.0)
        tr.tone(st * trip, ln * trip * 0.95, note(nm) - 12, "square", 0.08, duty=0.3,
                a=0.01, s=0.7)
    for i, m in enumerate([48, 52, 55, 60]):  # final held chord
        tr.tone(18 * trip, 12 * trip, m, "saw", 0.08, a=0.05, s=0.8, r=0.5)
    for k in range(18):  # drum roll
        tr.snare(k * trip / 2 + 4.5 * trip, 0.12 + 0.012 * k)
    tr.kick(18 * trip, 1.0)
    tr.crash(18 * trip, 0.35, 3.0)
    write_wav(os.path.join(MUSIC, "fanfare.wav"), tr.buf[: int(7.0 * SR)])


# --------------------------------------------------------------------------
# SFX
# --------------------------------------------------------------------------
def sweep(f0, f1, dur, kind="square", duty=0.5, curve=1.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    f = f0 + (f1 - f0) * t ** curve
    ph = np.cumsum(f) / SR % 1.0
    if kind == "square":
        return np.where(ph < duty, 1.0, -1.0)
    if kind == "tri":
        return 4 * np.abs(ph - 0.5) - 1
    return np.sin(2 * np.pi * ph)


def gen_sfx():
    n = lambda d: int(d * SR)  # noqa: E731

    # shoot: soft "pew" + air
    s = sweep(500, 1400, 0.11, "tri") * np.exp(-np.linspace(0, 5, n(0.11)))
    air = rng.uniform(-1, 1, n(0.11)) * np.exp(-np.linspace(0, 8, n(0.11))) * 0.3
    write_wav(os.path.join(SOUNDS, "shoot.wav"), s + lowpass(air, 3), peak=0.6)

    # wall bounce: short wooden tick
    t = np.arange(n(0.05)) / SR
    s = np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 90) + 0.4 * np.sin(2 * np.pi * 900 * t) * np.exp(-t * 60)
    write_wav(os.path.join(SOUNDS, "bounce.wav"), s, peak=0.5)

    # wrong angle: metallic clank + low "bonk"
    t = np.arange(n(0.5)) / SR
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, a, k in
            [(523, 1.0, 9), (1371, 0.6, 12), (2211, 0.4, 16), (3020, 0.25, 22)])
    s += 0.8 * sweep(220, 110, 0.5, "square", 0.5)[: len(t)] * np.exp(-t * 14)
    write_wav(os.path.join(SOUNDS, "wrong.wav"), s, peak=0.7)

    # drop: falling bloop
    s = sweep(900, 180, 0.35, "sine", curve=0.6) * env(n(0.35), 0.005, 0.1, 0.7, 0.1)
    write_wav(os.path.join(SOUNDS, "drop.wav"), s, peak=0.6)

    # fizzle (shot reached ceiling without hitting anything)
    t = np.arange(n(0.25)) / SR
    s = lowpass(rng.uniform(-1, 1, len(t)), 6) * np.exp(-t * 12)
    write_wav(os.path.join(SOUNDS, "fizzle.wav"), s, peak=0.4)

    # menu move / select
    t = np.arange(n(0.06)) / SR
    write_wav(os.path.join(SOUNDS, "move.wav"),
              osc("square", 880, len(t), 0.25) * np.exp(-t * 50), peak=0.35)
    tr = Track(0.25)
    tr.tone(0.0, 0.07, 76, "square", 0.5, duty=0.25)
    tr.tone(0.07, 0.12, 83, "square", 0.5, duty=0.25)
    write_wav(os.path.join(SOUNDS, "select.wav"), tr.buf[: n(0.22)], peak=0.4)

    # countdown tick (last 10 s)
    t = np.arange(n(0.09)) / SR
    write_wav(os.path.join(SOUNDS, "tick.wav"),
              osc("square", 1320, len(t), 0.5) * env(len(t), 0.002, 0.02, 0.6, 0.02), peak=0.35)

    # ready / go
    tr = Track(0.6)
    tr.tone(0.0, 0.45, 84, "square", 0.5, duty=0.5, s=0.7, r=0.15)
    tr.tone(0.0, 0.45, 79, "square", 0.3, duty=0.25, s=0.7, r=0.15)
    write_wav(os.path.join(SOUNDS, "go.wav"), tr.buf[: n(0.55)], peak=0.45)

    # level clear jingle
    tr = Track(1.4)
    for i, m in enumerate([72, 76, 79, 84, 88]):
        tr.tone(i * 0.07, 0.12, m, "square", 0.4, duty=0.25)
    for m in [72, 76, 79, 84]:
        tr.tone(0.38, 0.8, m, "square", 0.18, duty=0.5, s=0.7, r=0.3, vib=0.006)
    write_wav(os.path.join(SOUNDS, "clear.wav"), tr.buf[: n(1.3)], peak=0.6)

    # game over
    tr = Track(2.0)
    for i, m in enumerate([67, 66, 65, 64]):
        tr.tone(i * 0.28, 0.26, m, "square", 0.4, duty=0.5, s=0.7)
    tr.tone(1.12, 0.8, 48, "tri", 0.6, s=0.8, r=0.4, vib=0.01)
    tr.tone(1.12, 0.8, 60, "square", 0.2, duty=0.25, s=0.8, r=0.4, vib=0.01)
    write_wav(os.path.join(SOUNDS, "gameover.wav"), tr.buf[: n(1.95)], peak=0.6)

    # battle: garbage whoosh
    noise = rng.uniform(-1, 1, n(0.4))
    e = np.sin(np.linspace(0, np.pi, n(0.4))) ** 2
    s = lowpass(noise, 5) * e + 0.3 * sweep(300, 900, 0.4, "sine") * e
    write_wav(os.path.join(SOUNDS, "whoosh.wav"), s, peak=0.5)

    # fireworks: launch whistle + boom with crackle
    s = sweep(600, 2200, 0.7, "sine", curve=1.3) * np.linspace(0.2, 1, n(0.7)) * np.linspace(1, 0.3, n(0.7))
    s += lowpass(rng.uniform(-1, 1, n(0.7)), 4) * 0.15
    write_wav(os.path.join(SOUNDS, "fw_launch.wav"), s, peak=0.35)
    t = np.arange(n(1.6)) / SR
    boom = lowpass(rng.uniform(-1, 1, len(t)), 18) * np.exp(-t * 4) * 3
    boom += np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 10)) * t) * np.exp(-t * 6)
    crackle = np.zeros(len(t))
    for _ in range(70):
        i = int(rng.uniform(0.15, 1.5) * SR)
        L = int(0.006 * SR)
        if i + L < len(t):
            crackle[i:i + L] += rng.uniform(-1, 1, L) * rng.uniform(0.2, 0.7)
    write_wav(os.path.join(SOUNDS, "fw_boom.wav"), boom + crackle, peak=0.7)


if __name__ == "__main__":
    os.makedirs(MUSIC, exist_ok=True)
    os.makedirs(SOUNDS, exist_ok=True)
    gen_main()
    gen_danger()
    gen_fanfare()
    gen_sfx()
