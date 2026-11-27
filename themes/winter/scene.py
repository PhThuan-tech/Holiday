"""Winter Wonderland: a waving snowman, a log cabin with chimney smoke,
snowy pines, an aurora rippling across the sky, big rotating
six-armed snowflakes and three layers of falling snow."""
import math

import numpy as np

from engine import ASPECT, G, Scene, disc, line, rotate

COLS, ROWS = 150, 105
AURORA_ROWS = 48


def ground_row(col):
    return ROWS - 15 - 3 * np.sin(col * 0.045 + 0.5) - 2 * np.sin(col * 0.11)


def _flake_pattern():
    """Unit snowflake: six arms, each with two pairs of side branches."""
    u, v, tip = [0.0], [0.0], [True]
    for k in range(6):
        a = k * math.pi / 3 - math.pi / 2
        r = np.linspace(0.12, 1.0, 10)
        u += list(r * math.cos(a))
        v += list(r * math.sin(a))
        tip += list(r > 0.9)
        for r0, length in ((0.42, 0.32), (0.7, 0.22)):
            for s in (-1, 1):
                b = a + s * math.pi / 3
                rr = np.linspace(0, length, 5)[1:]
                u += list(r0 * math.cos(a) + rr * math.cos(b))
                v += list(r0 * math.sin(a) + rr * math.sin(b))
                tip += [False, False, False, True]
    return np.array(u), np.array(v), np.where(np.array(tip), G["*"], G["+"]).astype(np.int16)


class Winter(Scene):
    title = "Winter Wonderland"
    cols, rows = COLS, ROWS
    background = ((2, 6, 22), (22, 32, 64))
    caption_color = "#bfe6ff"

    def setup(self, canvas):
        rng = np.random.default_rng(21)
        canvas.set_background(*self.background)
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        canvas.bg[Y >= ground_row(X)] = (55, 65, 92)
        self.base_bg = canvas.bg.copy()
        self.aurora_X, self.aurora_Y = X[:AURORA_ROWS], Y[:AURORA_ROWS]

        gx = rng.uniform(0, COLS, 600)
        gy = rng.uniform(ground_row(gx) + 1, ROWS)
        self.ground_snow = (gx, gy, G["."], np.outer(rng.uniform(0.4, 0.9, 600), (220, 230, 250)))

        sx, sy = rng.uniform(0, COLS, 130), rng.uniform(0, ROWS - 30, 130)
        self.stars = (sx, sy, rng.uniform(0, 6.3, 130))

        self.static = self._build_static(rng)
        self.chimney = (128.0, float(int(ground_row(122)) + 1 - 20))
        self.flake = _flake_pattern()

    def _build_static(self, rng):
        xs, ys, gs, cs = [], [], [], []

        def put(x, y, g, c):
            xs.append(float(x))
            ys.append(float(y))
            gs.append(G[g])
            cs.append(c)

        for col, height, width in ((8, 26, 6.5), (24, 18, 5), (92, 14, 4), (145, 22, 5.5)):
            base = int(ground_row(col)) + 1
            for r in range(2):
                put(col, base - r, "|", (100, 65, 40))
            for r in range(height):
                p = r / height
                lp = (p * 3) % 1
                hw = max(0.5, width * (0.25 + 0.75 * p) * (0.55 + 0.45 * lp))
                for x in np.arange(round(col - hw), round(col + hw) + 1):
                    if lp < 0.12:
                        put(x, base - 2 - height + r, "*", (225, 235, 250))
                    else:
                        put(x, base - 2 - height + r, "#", tuple(np.array([25, 85, 50]) * rng.uniform(0.75, 1.1)))

        cx, base = 122, int(ground_row(122)) + 1          # log cabin
        wall_top = base - 10
        for r in range(wall_top, base + 1):
            for x in range(cx - 11, cx + 12):
                put(x, r, "=", (110, 70, 42))
        for wx in (cx - 7, cx + 4):                      # glowing windows
            for r in range(wall_top + 3, wall_top + 6):
                for x in range(wx, wx + 4):
                    put(x, r, "+" if (r == wall_top + 4 and x == wx + 1) else "#", (255, 195, 85))
        for r in range(base - 6, base + 1):              # door
            for x in range(cx - 1, cx + 2):
                put(x, r, "|", (70, 40, 25))
        put(cx + 1, base - 3, ".", (255, 210, 90))
        for x in range(cx + 5, cx + 8):                  # chimney
            for r in range(wall_top - 9, wall_top - 3):
                put(x, r, "*" if r == wall_top - 9 else "#", (230, 235, 250) if r == wall_top - 9 else (115, 105, 105))
        for k in range(8):                               # roof
            r = wall_top - 1 - k
            hw = 13 - k * 1.6
            for x in np.arange(round(cx - hw), round(cx + hw) + 1):
                edge = abs(x - cx) >= hw - 1
                if k == 7 or edge:
                    put(x, r, "*", (230, 235, 250))
                else:
                    put(x, r, "#", (120, 40, 35))
        return (np.array(xs, np.float32), np.array(ys, np.float32),
                np.array(gs, np.int16), np.array(cs, np.float32))

    def reset(self):
        rng = self.rng = np.random.default_rng()
        layers = [(160, 3, 0.35, G["."]), (90, 6, 0.65, G["."]), (45, 10, 1.0, G["*"])]
        self.snow = []
        for n, speed, bright, glyph in layers:
            self.snow.append(dict(x=rng.uniform(0, COLS, n), y=rng.uniform(0, ROWS, n),
                                  v=rng.uniform(0.7, 1.3, n) * speed, ph=rng.uniform(0, 6.3, n),
                                  bright=bright, glyph=glyph))
        self.flakes = [dict(x=rng.uniform(10, COLS - 10), y=rng.uniform(-10, ROWS), r=rng.uniform(6, 11),
                            spin=rng.choice([-1, 1]) * rng.uniform(0.2, 0.5), v=rng.uniform(0.8, 2.0),
                            ph=rng.uniform(0, 6.3)) for _ in range(6)]
        self.smoke = np.zeros((0, 3))                    # x, y, age
        self.smoke_acc = 0.0

    def update(self, dt, t):
        for layer in self.snow:
            layer["y"] += layer["v"] * dt
            layer["x"] += np.sin(t + layer["ph"]) * 2 * dt
            wrap = layer["y"] > ROWS
            layer["y"][wrap] -= ROWS + 2
            layer["x"] %= COLS
        for f in self.flakes:
            f["y"] += f["v"] * dt
            if f["y"] > ROWS + 10:
                f["y"], f["x"] = -10, self.rng.uniform(10, COLS - 10)
        self.smoke_acc += dt * 5
        while self.smoke_acc >= 1:
            self.smoke_acc -= 1
            self.smoke = np.vstack([self.smoke, [*self.chimney, 0.0]])
        if len(self.smoke):
            self.smoke[:, 0] += (3 + np.sin(t + self.smoke[:, 1])) * dt
            self.smoke[:, 1] -= 3 * dt
            self.smoke[:, 2] += dt
            self.smoke = self.smoke[self.smoke[:, 2] < 4]

    def draw(self, canvas, t):
        X, Y = self.aurora_X, self.aurora_Y
        center = 14 + 5 * np.sin(X * 0.045 + t * 0.35) + 3 * np.sin(X * 0.11 - t * 0.6)
        green = np.exp(-((Y - center) / 5) ** 2) * (0.55 + 0.45 * np.sin(X * 0.07 + t * 0.8))
        purple = np.exp(-((Y - center - 9) / 4) ** 2) * (0.5 + 0.5 * np.sin(X * 0.05 - t * 0.5)) * 0.6
        bg = self.base_bg.copy()
        bg[:AURORA_ROWS] += green[..., None] * np.array([25, 150, 95]) + purple[..., None] * np.array([100, 35, 140])
        canvas.bg = bg

        sx, sy, sph = self.stars
        tw = 0.5 + 0.5 * np.sin(t * 2 + sph)
        canvas.plot(sx, sy, G["."], np.outer(0.25 + 0.5 * tw, (220, 230, 255)))
        canvas.plot(*self.ground_snow)
        canvas.plot(*self.static)

        if len(self.smoke):
            age = self.smoke[:, 2]
            glyph = np.where(age < 1.2, G["o"], np.where(age < 2.6, G["~"], G["."]))
            canvas.plot(self.smoke[:, 0], self.smoke[:, 1], glyph, np.outer(1 - age / 4, (160, 160, 175)))

        self._draw_snowman(canvas, t)

        u, v, glyph = self.flake
        for f in self.flakes:
            fx, fy = rotate(u * f["r"] * ASPECT, v * f["r"], t * f["spin"] + f["ph"])
            canvas.plot(f["x"] + fx + 3 * math.sin(t * 0.5 + f["ph"]), f["y"] + fy, glyph,
                        np.array([200, 230, 255]) * (0.4 + 0.6 * f["r"] / 11))
        for layer in self.snow:
            canvas.plot(layer["x"], layer["y"], layer["glyph"], np.array([235, 240, 255]) * layer["bright"])

    def _draw_snowman(self, canvas, t):
        cx = 55.0
        g = float(ground_row(cx)) + 1
        balls = [(g - 7, 7.0), (g - 18, 5.0), (g - 25.8, 3.6)]
        for cy, r in balls:
            x, y, d = disc(cx, cy, r)
            light = 1 - 0.35 * d + 0.12 * (-(x - cx) / (r * ASPECT) - (y - cy) / r)
            canvas.plot(x, y, np.where(d < 0.75, G["o"], G["@"]), np.outer(light, (235, 240, 255)))
        hy, my = balls[2][0], balls[1][0]
        dark = (30, 30, 40)
        canvas.plot([cx - 1.6, cx + 1.6], [hy - 1, hy - 1], G["@"], dark)            # eyes
        canvas.plot([cx + 0.5, cx + 1.5], [hy + 0.2, hy + 0.2], np.array([G["-"], G[">"]]), (255, 140, 30))
        mouth = np.arange(-2, 3)
        canvas.plot(cx + mouth, hy + 1.7 + 0.12 * mouth ** 2, G["."], dark)
        canvas.plot(np.full(3, cx), my + np.array([-2.5, 0, 2.5]), G["@"], dark)      # buttons

        top = hy - 3.6
        canvas.plot(np.arange(cx - 5, cx + 6), np.full(11, top - 0.5), G["="], (75, 75, 90))   # hat
        for r in range(1, 5):
            canvas.plot(np.arange(cx - 3, cx + 4), np.full(7, top - 0.5 - r),
                        G["="] if r == 1 else G["#"], (200, 40, 40) if r == 1 else (65, 65, 80))
        neck = hy + 3.4                                                         # scarf
        canvas.plot(np.arange(cx - 5, cx + 6), np.full(11, neck), G["="], (210, 40, 50))
        k = np.arange(1, 5)
        canvas.plot(cx + 3 + np.sin(t * 2.5) * 0.25 * k, neck + k, G["|"], (210, 40, 50))

        lx, ly, lg = line(cx - 6, my - 1, cx - 16, my - 7)                       # arms
        canvas.plot(lx, ly, lg, (120, 80, 45))
        a = -0.6 + 0.35 * math.sin(t * 3)
        ex, ey = cx + 6 + math.cos(a) * 9 * ASPECT, my - 1 + math.sin(a) * 9
        rx, ry, rg = line(cx + 6, my - 1, ex, ey)
        canvas.plot(rx, ry, rg, (120, 80, 45))
        canvas.plot([ex + 1, ex], [ey - 1, ey - 1.5], np.array([G["/"], G["|"]]), (120, 80, 45))

    def caption(self, t):
        return "Let it snow!\nHappy Holidays" if t > 2 else ""


SCENE = Winter
