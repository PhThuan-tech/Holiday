"""Lunar New Year: a peach-blossom branch grows and blooms, petals drift
down, red lanterns sway and lucky red envelopes fall.
Press M to switch between peach (pink) and apricot (yellow) blossoms."""
import datetime
import math

import numpy as np

from engine import ASPECT, G, Scene

COLS, ROWS = 150, 105
ZODIAC = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
          "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

BLOSSOMS = {   # petal colour, bud colour, centre colour
    "peach": ((255, 130, 175), (190, 60, 110), (255, 225, 120)),
    "apricot": ((255, 205, 40), (170, 140, 30), (235, 120, 20)),
}
BARK = np.array([110, 62, 35], dtype=np.float32)


def _direction_glyph(dx, dy):
    if abs(dy) < 0.4 * abs(dx):
        return G["-"]
    if abs(dx) < 0.4 * abs(dy):
        return G["|"]
    return G["/"] if dx * dy < 0 else G["\\"]


def _lantern_template():
    dx, dy, glyph, color = [], [], [], []

    def put(x, y, g, c):
        dx.append(x)
        dy.append(y)
        glyph.append(G[g])
        color.append(c)

    for y in range(-5, 6):
        if abs(y) == 5:                                   # gold caps
            for x in range(-3, 4):
                put(x, y, "=", (255, 200, 70))
            continue
        hw = int(round(4.6 * math.sqrt(1 - (y / 6) ** 2) * ASPECT))
        for x in range(-hw, hw + 1):
            fall = 1 - 0.5 * (abs(x) / max(hw, 1)) ** 2   # rounder look
            if x != 0 and x % 3 == 0:
                put(x, y, "|", (200 * fall, 90 * fall, 30 * fall))
            else:
                put(x, y, "#", (235 * fall, 45 * fall, 35 * fall))
    put(0, 0, "@", (255, 215, 80))                        # gold emblem
    for y in range(6, 10):                                # tassel
        put(0, y, "|", (255, 190, 60))
    put(-1, 9, "|", (255, 190, 60))
    put(1, 9, "|", (255, 190, 60))
    return (np.array(dx, np.float32), np.array(dy, np.float32),
            np.array(glyph, np.int16), np.array(color, np.float32))


def _envelope_template():
    dx, dy, glyph, color = [], [], [], []
    for y in range(-3, 4):
        for x in range(-2, 3):
            dx.append(x)
            dy.append(y)
            if y == -3:
                glyph.append(G["="])
                color.append((255, 200, 70))
            elif (x, y) == (0, 0):
                glyph.append(G["@"])
                color.append((255, 215, 80))
            else:
                glyph.append(G["#"])
                color.append((205, 25, 30))
    return (np.array(dx, np.float32), np.array(dy, np.float32),
            np.array(glyph, np.int16), np.array(color, np.float32))


class LunarNewYear(Scene):
    title = "Lunar New Year"
    cols, rows = COLS, ROWS
    background = ((28, 5, 12), (70, 14, 20))
    caption_color = "#ffd24a"
    help_text = "   M peach / apricot"

    def __init__(self):
        self.mode = "peach"
        rng = np.random.default_rng(88)
        self.segments, self.tips = [], []
        self._grow(rng, 4.0, ROWS - 2.0, -0.95, 24.0, 0, 0.2)
        self._build_branch()
        self._build_blossoms(rng)
        self.lantern = _lantern_template()
        self.envelope = _envelope_template()
        self.lanterns = [dict(col=98, length=18, phase=0.0, amp=0.10),
                         dict(col=118, length=28, phase=1.7, amp=0.08),
                         dict(col=138, length=14, phase=3.1, amp=0.12)]

    # ---- branch generation
    def _grow(self, rng, x, y, angle, length, depth, t0):
        x1 = x + math.cos(angle) * length * ASPECT
        y1 = y + math.sin(angle) * length
        t1 = t0 + 0.25 + length * 0.05
        self.segments.append((x, y, x1, y1, depth, t0, t1))
        if depth >= 5 or length < 3.0:
            self.tips.append((x1, y1, t1))
            return
        children = 2 if depth < 1 else int(rng.choice([2, 2, 3]))
        for i in range(children):
            sign = 1 if i % 2 == 0 else -1
            spread = rng.uniform(0.35, 0.75) * sign if i < 2 else rng.uniform(-0.15, 0.15)
            new_angle = float(np.clip(angle + spread, -2.9, 0.3))
            self._grow(rng, x1, y1, new_angle, length * rng.uniform(0.62, 0.8), depth + 1, t1)

    def _build_branch(self):
        xs, ys, gs, ts = [], [], [], []
        for x0, y0, x1, y1, depth, t0, t1 in self.segments:
            dx, dy = x1 - x0, y1 - y0
            steps = int(max(abs(dx), abs(dy)) * 1.5) + 2
            s = np.linspace(0, 1, steps)
            thick = [-1, 0, 1] if depth == 0 else [0, 1] if depth == 1 else [0]
            glyph = G["#"] if depth <= 1 else _direction_glyph(dx, dy)
            for off in thick:
                xs.append(x0 + s * dx + off)
                ys.append(y0 + s * dy)
                gs.append(np.full(steps, glyph))
                ts.append(t0 + s * (t1 - t0))
        self.branch_x = np.concatenate(xs)
        self.branch_y = np.concatenate(ys)
        self.branch_g = np.concatenate(gs).astype(np.int16)
        self.branch_t = np.concatenate(ts)

    def _build_blossoms(self, rng):
        cx, cy, bt, size = [], [], [], []
        for x, y, t in self.tips:
            cx.append(x)
            cy.append(y)
            bt.append(t + rng.uniform(0.3, 1.5))
            size.append(1.15)
        for x0, y0, x1, y1, depth, t0, t1 in self.segments:
            if depth < 3 or rng.random() < 0.4:
                continue
            for s in rng.uniform(0.3, 1.0, 1):
                cx.append(x0 + s * (x1 - x0))
                cy.append(y0 + s * (y1 - y0))
                bt.append(t0 + s * (t1 - t0) + rng.uniform(0.3, 1.5))
                size.append(1.0)
        n = len(cx)
        self.bl_x = np.array(cx, np.float32)
        self.bl_y = np.array(cy, np.float32)
        self.bl_t = np.array(bt, np.float32)
        self.bl_size = np.array(size, np.float32)
        self.bl_rot = rng.uniform(0, 2 * math.pi, n).astype(np.float32)
        self.bl_tint = rng.uniform(0.85, 1.1, n).astype(np.float32)

    # ---- simulation
    def reset(self):
        self.rng = np.random.default_rng()
        self.petal_x = np.zeros(0)
        self.petal_y = np.zeros(0)
        self.petal_v = np.zeros(0)
        self.petal_ph = np.zeros(0)
        self.env = []
        self.next_env = 3.0

    def _bloom(self, t):
        return np.clip((t - self.bl_t) / 1.4, 0, 1)

    def update(self, dt, t):
        rng = self.rng
        full = np.nonzero(self._bloom(t) >= 1)[0]
        k = rng.poisson(10 * dt) if len(full) else 0
        if k:
            pick = rng.choice(full, k)
            self.petal_x = np.concatenate([self.petal_x, self.bl_x[pick]])
            self.petal_y = np.concatenate([self.petal_y, self.bl_y[pick]])
            self.petal_v = np.concatenate([self.petal_v, rng.uniform(3, 7, k)])
            self.petal_ph = np.concatenate([self.petal_ph, rng.uniform(0, 2 * math.pi, k)])
        self.petal_y += self.petal_v * dt
        self.petal_x += (np.sin(t * 2 + self.petal_ph) * 4 + 2) * dt
        keep = self.petal_y < ROWS + 1
        self.petal_x, self.petal_y = self.petal_x[keep], self.petal_y[keep]
        self.petal_v, self.petal_ph = self.petal_v[keep], self.petal_ph[keep]

        if t >= self.next_env:
            self.env.append(dict(x=rng.uniform(60, COLS - 6), y=-5.0,
                                 v=rng.uniform(5, 8), ph=rng.uniform(0, 6.3)))
            self.next_env = t + rng.uniform(1.0, 2.5)
        for e in self.env:
            e["y"] += e["v"] * dt
            e["x"] += math.sin(t * 1.5 + e["ph"]) * 5 * dt
        self.env = [e for e in self.env if e["y"] < ROWS + 6]

    # ---- drawing
    def draw(self, canvas, t):
        petal_c, bud_c, center_c = (np.array(c, np.float32) for c in BLOSSOMS[self.mode])

        grown = self.branch_t <= t
        canvas.plot(self.branch_x[grown], self.branch_y[grown], self.branch_g[grown], BARK)

        b = self._bloom(t)
        started = t >= self.bl_t
        opened = b >= 0.35
        if opened.any():
            ob = (b[opened] - 0.35) / 0.65
            r = (0.7 + 0.7 * ob) * self.bl_size[opened]
            ang = self.bl_rot[opened][:, None] + np.arange(5) * 2 * math.pi / 5
            px = self.bl_x[opened][:, None] + np.cos(ang) * (r * ASPECT)[:, None]
            py = self.bl_y[opened][:, None] + np.sin(ang) * r[:, None]
            stage = np.where(ob < 0.4, G["."], np.where(ob < 0.8, G["o"], G["@"]))
            color = np.outer(self.bl_tint[opened] * (0.6 + 0.4 * ob), petal_c)
            canvas.plot(px, py, np.repeat(stage, 5), np.repeat(color, 5, axis=0))
        if started.any():
            is_bud = ~opened[started]
            canvas.plot(self.bl_x[started], self.bl_y[started],
                        np.where(is_bud, G["o"], G["@"]),
                        np.where(is_bud[:, None], bud_c, center_c))

        if len(self.petal_x):
            spin = np.sin(t * 5 + self.petal_ph) > 0
            canvas.plot(self.petal_x, self.petal_y, np.where(spin, G["*"], G["o"]),
                        petal_c * 0.9)

        ldx, ldy, lg, lc = self.lantern
        for lan in self.lanterns:
            th = lan["amp"] * math.sin(t * 1.2 + lan["phase"])
            rope = np.arange(0, lan["length"] - 5, dtype=np.float32)
            canvas.plot(lan["col"] + math.sin(th) * rope * ASPECT, rope * math.cos(th),
                        G["|"], (200, 160, 60))
            d = lan["length"] + ldy
            glow = 0.9 + 0.1 * math.sin(t * 6 + lan["phase"])
            canvas.plot(lan["col"] + ldx + math.sin(th) * d * ASPECT, d * math.cos(th),
                        lg, lc * glow)

        edx, edy, eg, ec = self.envelope
        for e in self.env:
            canvas.plot(e["x"] + edx, e["y"] + edy, eg, ec)

    def caption(self, t):
        if t < 4:
            return ""
        now = datetime.date.today()
        year = now.year + 1 if now.month >= 3 else now.year
        animal = ZODIAC[(year - 4) % 12]
        return f"Happy Lunar New Year {year}\nYear of the {animal}  ·  Chúc Mừng Năm Mới"

    def on_key(self, key):
        if key == "m":
            self.mode = "apricot" if self.mode == "peach" else "peach"


SCENE = LunarNewYear
