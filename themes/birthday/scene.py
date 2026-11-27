"""Birthday: a two-tier cake with flickering candles, balloons, bunting and
spinning confetti. Press B to blow out (or relight) the candles.

    python run.py birthday            # generic greeting
    python run.py birthday Alice 25   # "Happy 25th Birthday, Alice!"
"""
import math

import numpy as np

from engine import ASPECT, G, Scene, disc

COLS, ROWS = 150, 105
CX = 75
CANDLES = [CX - 14, CX - 7, CX, CX + 7, CX + 14]
FLAME_ROW = 56
PALETTE = np.array([(255, 90, 90), (255, 180, 60), (255, 230, 90), (90, 220, 120),
                    (80, 190, 255), (170, 120, 255), (255, 120, 200)], dtype=np.float32)
CONFETTI_GLYPHS = np.array([G["-"], G["/"], G["|"], G["\\"]], dtype=np.int16)   # spinning


def ordinal(n):
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _build_cake():
    xs, ys, gs, cs = [], [], [], []

    def put(x, y, g, c):
        xs.append(x)
        ys.append(y)
        gs.append(G[g])
        cs.append(c)

    tiers = [(30, 80, 96, (140, 80, 50), "♥", (255, 120, 160), 88, 6),
             (20, 66, 80, (245, 150, 185), "@", (255, 255, 255), 73, 4)]
    for half, top, bottom, body, deco, deco_c, deco_row, step in tiers:
        for col in range(CX - half, CX + half + 1):
            drip = 1 + int(2.5 * abs(math.sin(col * 0.9)))
            for row in range(top, bottom):
                if row == top:
                    put(col, row, "~", (255, 245, 240))
                elif row <= top + drip:
                    put(col, row, "|", (255, 235, 240))
                elif row == deco_row and (col - CX) % step == 0:
                    put(col, row, deco, deco_c)
                else:
                    put(col, row, "#", body)
    for col in range(CX - 36, CX + 37):
        put(col, 96, "=", (200, 200, 215))
    for i, col in enumerate(CANDLES):
        for row in range(FLAME_ROW + 2, 66):
            put(col, row, "#", (255, 255, 255) if row % 2 else tuple(PALETTE[i % len(PALETTE)]))
    return (np.array(xs, np.float32), np.array(ys, np.float32),
            np.array(gs, np.int16), np.array(cs, np.float32))


class Birthday(Scene):
    title = "Happy Birthday"
    cols, rows = COLS, ROWS
    background = ((40, 16, 60), (12, 6, 24))
    caption_color = "#ffd1f0"
    help_text = "   B blow out / relight candles   C confetti"

    def __init__(self, name="", age=""):
        self.name = name.strip()
        self.age = int(age) if str(age).isdigit() else None
        self.cake = _build_cake()
        bx, by, bd = disc(0, 0, 3.2)
        self.balloon_shape = (bx, by, bd)

    def setup(self, canvas):
        canvas.set_background(*self.background)
        self.base_bg = canvas.bg.copy()
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        glow = sum(np.exp(-(((X - c) / ASPECT) ** 2 + (Y - FLAME_ROW) ** 2) / 40) for c in CANDLES)
        self.glow = glow[..., None] * np.array([255, 170, 60], np.float32) * 0.3

    def reset(self):
        rng = self.rng = np.random.default_rng()
        self.t = 0.0
        self.lit = True
        self.auto = True
        self.next_toggle = 8.0
        self.conf = {k: np.zeros(0) for k in ("x", "y", "vx", "vy", "ph", "rate")}
        self.conf_c = np.zeros((0, 3), np.float32)
        self._spawn_confetti(120, rng.uniform(0, COLS, 120), rng.uniform(0, ROWS, 120), 0, rng.uniform(2, 5, 120))
        self.smoke = np.zeros((0, 4))                  # x, y, age, phase
        self.smoke_until = 0.0
        n = 8
        self.bal_x = rng.uniform(5, COLS - 5, n)
        self.bal_y = rng.uniform(10, ROWS + 40, n)
        self.bal_v = rng.uniform(2.5, 4.5, n)
        self.bal_c = PALETTE[rng.integers(0, len(PALETTE), n)]
        self.bal_ph = rng.uniform(0, 6.3, n)

    def _spawn_confetti(self, n, x, y, vx, vy):
        rng = self.rng
        new = dict(x=np.broadcast_to(x, (n,)), y=np.broadcast_to(y, (n,)),
                   vx=np.broadcast_to(vx, (n,)), vy=np.broadcast_to(vy, (n,)),
                   ph=rng.uniform(0, 4, n), rate=rng.uniform(4, 10, n))
        for k in self.conf:
            self.conf[k] = np.concatenate([self.conf[k], new[k]])
        self.conf_c = np.concatenate([self.conf_c, PALETTE[rng.integers(0, len(PALETTE), n)]])

    def burst(self):
        rng = self.rng
        n = 350
        self._spawn_confetti(n, CX + rng.uniform(-15, 15, n), FLAME_ROW, rng.normal(0, 14, n) * ASPECT,
                             -rng.uniform(15, 40, n))

    def blow(self):
        if self.lit:
            self.lit = False
            self.smoke_until = self.t + 1.5
            self.burst()
        else:
            self.lit = True

    def update(self, dt, t):
        self.t = t
        rng = self.rng
        if self.auto and t >= self.next_toggle:
            self.blow()
            self.next_toggle = t + (10 if not self.lit else 8)

        k = rng.poisson(25 * dt)
        if k:
            self._spawn_confetti(k, rng.uniform(0, COLS, k), -1.0, 0.0, rng.uniform(2, 5, k))
        c = self.conf
        c["vy"] = np.minimum(c["vy"] + 12 * dt, 7)
        c["vx"] *= math.exp(-dt * 1.5)
        c["x"] += (c["vx"] + np.sin(t * 2 + c["ph"]) * 3) * dt
        c["y"] += c["vy"] * dt
        keep = c["y"] < ROWS + 1
        for key in c:
            c[key] = c[key][keep]
        self.conf_c = self.conf_c[keep]

        if t < self.smoke_until:
            puffs = np.column_stack([np.array(CANDLES) + rng.uniform(-0.5, 0.5, len(CANDLES)),
                                     np.full(len(CANDLES), FLAME_ROW + 1.0), np.zeros(len(CANDLES)),
                                     rng.uniform(0, 6.3, len(CANDLES))])
            self.smoke = np.concatenate([self.smoke, puffs])
        if len(self.smoke):
            self.smoke[:, 1] -= 4 * dt
            self.smoke[:, 0] += np.sin(t * 3 + self.smoke[:, 3]) * 2 * dt
            self.smoke[:, 2] += dt
            self.smoke = self.smoke[self.smoke[:, 2] < 2.0]

        self.bal_y -= self.bal_v * dt
        gone = self.bal_y < -15
        self.bal_y[gone] = ROWS + 10
        self.bal_x[gone] = rng.uniform(5, COLS - 5, gone.sum())

    def draw(self, canvas, t):
        flicker = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 7.7)
        canvas.bg = self.base_bg + (self.glow * flicker if self.lit else 0)

        self._draw_bunting(canvas, t)

        bx, by, bd = self.balloon_shape
        for i in range(len(self.bal_x)):
            x, y = self.bal_x[i] + 2 * math.sin(t * 0.8 + self.bal_ph[i]), self.bal_y[i]
            string_off = np.sin(t * 2 + self.bal_ph[i] + np.arange(8) * 0.6) * 0.8
            glyph = np.where(np.abs(np.diff(string_off, prepend=0)) < 0.25, G["|"],
                             np.where(np.diff(string_off, prepend=0) > 0, G["\\"], G["/"]))
            canvas.plot(x + string_off, y + 4.5 + np.arange(8), glyph, (200, 200, 215))
            canvas.plot(x + bx, y + by, G["#"], np.outer(1 - 0.35 * bd, self.bal_c[i]))
            canvas.plot([x - 1.5], [y - 1.5], G["@"], self.bal_c[i] * 0.4 + 150)
            canvas.plot([x], [y + 3.6], G["v"], self.bal_c[i])

        canvas.plot(*self.cake)
        if self.lit:
            for i, col in enumerate(CANDLES):
                sway = 0.6 * math.sin(t * 9 + i * 1.7)
                canvas.plot([col + sway], [FLAME_ROW], G["^"], np.array([255, 150, 40]) * flicker)
                canvas.plot([col], [FLAME_ROW + 1], G["@"], np.array([255, 235, 160]) * flicker)
        if len(self.smoke):
            fade = 1 - self.smoke[:, 2] / 2.0
            canvas.plot(self.smoke[:, 0], self.smoke[:, 1], np.where(self.smoke[:, 2] < 0.6, G["o"], G["~"]),
                        np.outer(fade, (170, 170, 185)))

        c = self.conf
        glyph = CONFETTI_GLYPHS[(t * c["rate"] + c["ph"]).astype(int) % 4]
        canvas.plot(c["x"], c["y"], glyph, self.conf_c)

    def _draw_bunting(self, canvas, t):
        x = np.arange(0, COLS, 0.5)
        y = 3 + 7 * (1 - ((x - CX) / CX) ** 2)
        slope = np.gradient(y, x)
        glyph = np.where(np.abs(slope) < 0.12, G["-"], np.where(slope > 0, G["\\"], G["/"]))
        canvas.plot(x, y, glyph, (220, 220, 230))
        for i, ax in enumerate(np.linspace(6, COLS - 6, 14)):
            ay = 3 + 7 * (1 - ((ax - CX) / CX) ** 2) + 1
            wave = math.sin(t * 2 + i)
            for k, hw in enumerate((3, 2, 1, 0)):
                cols = np.arange(-hw, hw + 1) + ax + wave * k * 0.3
                canvas.plot(cols, np.full(len(cols), ay + k), G["#"], PALETTE[i % len(PALETTE)])

    def caption(self, t):
        if t < 1:
            return ""
        who = f", {self.name}" if self.name else ""
        if self.lit:
            return f"Make a wish{who}!"
        age = f"{ordinal(self.age)} " if self.age else ""
        return f"Happy {age}Birthday{who}!"

    def on_key(self, key):
        if key == "b":
            self.auto = False
            self.blow()
        elif key == "c":
            self.burst()


SCENE = Birthday
