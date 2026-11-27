"""Easter: three painted 3D eggs (stripes, polka dots, zigzag + hearts)
spinning in a woven basket on a sunny spring day, with a hopping bunny,
fluttering butterflies, flowers and grass swaying in the wind."""
import math

import numpy as np

from engine import ASPECT, G, Scene, Sprite, blob, direction_glyph, disc, project

COLS, ROWS = 150, 105
CX = 75
BASKET_TOP = 80
EGG_X = (-1.35, 0.0, 1.35)

BUNNY = Sprite("""
 #   #
 #   #
 #####
##o#o##
###v###
 #####
#######
 ## ##
""", {"#": ("#", (250, 250, 250)), "o": ("@", (60, 40, 60)), "v": ("v", (255, 120, 160))})


def ground_row(col):
    return ROWS - 18 - 2 * np.sin(col * 0.05)


def build_egg(rng, style, n=5000):
    y = rng.uniform(-1, 1, n)
    th = rng.uniform(0, 2 * math.pi, n)
    r = 0.45 * np.sqrt(1 - y ** 2) * (1 - 0.12 * y)
    pos = np.stack([r * np.cos(th), y * 0.6, r * np.sin(th)], 1)
    glyph = np.full(n, G["#"], dtype=np.int16)
    if style == "stripes":
        palette = np.array([(255, 130, 180), (255, 225, 90), (90, 210, 230), (180, 130, 255)])
        band = np.floor((y + 0.08 * np.sin(th * 8) + 1) * 3.5).astype(int)
        color = palette[band % 4].astype(np.float32)
        edge = ((y + 0.08 * np.sin(th * 8) + 1) * 3.5) % 1 < 0.12
        glyph[edge] = G["="]
    elif style == "dots":
        color = np.tile(np.array([[120, 220, 190]], np.float32), (n, 1))
        dist = np.full(n, 9.0)
        for i, yc in enumerate((-0.6, -0.2, 0.2, 0.6)):
            for k in range(6):
                thc = k * math.pi / 3 + (i % 2) * math.pi / 6
                dth = (th - thc + math.pi) % (2 * math.pi) - math.pi
                dist = np.minimum(dist, np.hypot((y - yc) * 0.6, dth * 0.45 * math.sqrt(1 - yc ** 2)))
        dot = dist < 0.09
        color[dot] = (255, 120, 170)
        glyph[dot] = G["@"]
    else:
        zig = 0.12 * np.abs(((th * 6 / math.pi) % 2) - 1)
        upper, lower = y > 0.15 + zig, y < -0.25 + zig
        color = np.where(upper[:, None], [[190, 140, 255]],
                         np.where(lower[:, None], [[255, 220, 80]], [[255, 110, 150]])).astype(np.float32)
        glyph[~upper & ~lower] = G["♥"]
    return pos.astype(np.float32), color, glyph


class Easter(Scene):
    title = "Easter"
    cols, rows = COLS, ROWS
    background = ((95, 160, 230), (205, 232, 250))
    caption_color = "#6a2c91"

    def setup(self, canvas):
        rng = np.random.default_rng(4)
        canvas.set_background(*self.background)
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        canvas.bg[Y >= ROWS - 30 - 6 * np.sin(X * 0.03 + 1)] = (120, 190, 110)
        canvas.bg[Y >= ground_row(X)] = (80, 160, 70)
        self.base_bg = canvas.bg

        self.eggs = [build_egg(rng, s) for s in ("stripes", "dots", "zigzag")]
        self.clouds = []
        for _ in range(4):
            bx, by, bd = blob(rng, int(rng.integers(3, 5)), rng.uniform(2.5, 3.5))
            self.clouds.append(dict(dx=bx, dy=by, d=bd, x=rng.uniform(0, COLS), y=rng.uniform(6, 30),
                                    v=rng.uniform(1, 2.5)))

        n = 300                                            # grass blades
        self.grass_c = rng.uniform(0, COLS, n)
        self.grass_base = ground_row(self.grass_c) + rng.uniform(1, 17, n)
        self.grass_h = rng.integers(2, 5, n)
        self.grass_col = np.stack([rng.uniform(40, 90, n), rng.uniform(150, 220, n), rng.uniform(40, 80, n)], 1)

        self.flowers = []
        for _ in range(16):
            x = rng.choice([rng.uniform(2, 24), rng.uniform(126, 148)])
            self.flowers.append(dict(x=x, y=float(ground_row(x)) + rng.uniform(2, 12),
                                     kind=rng.choice(["daisy", "tulip"]),
                                     color=[(240, 60, 80), (255, 120, 200), (170, 90, 230), (255, 160, 40)][rng.integers(4)]))

        self.basket = self._build_basket()
        self.butterflies = []
        for i in range(5):
            c = [(255, 140, 40), (90, 170, 255), (255, 100, 190), (250, 220, 60), (170, 110, 255)][i]
            pal = {"@": ("@", c), "o": ("o", c), "(": ("(", c), ")": (")", c), "|": ("|", (60, 40, 30))}
            self.butterflies.append(dict(open=Sprite(["@|@", "o|o"], pal), closed=Sprite(["(|)", " | "], pal),
                                         x0=rng.uniform(25, 125), y0=rng.uniform(25, 55),
                                         ph=rng.uniform(0, 6.3), k=rng.uniform(0.6, 1.2)))

    def _build_basket(self):
        xs, ys, gs, cs = [], [], [], []
        for r in range(0, 15):
            hw = 48 - r * 1.3
            for x in range(int(CX - hw), int(CX + hw) + 1):
                xs.append(x)
                ys.append(BASKET_TOP + r)
                if r == 0:
                    gs.append(G["="])
                    cs.append((205, 150, 80))
                elif (x + r) % 2 == 0:
                    gs.append(G["x"])
                    cs.append((175, 120, 60))
                else:
                    gs.append(G["#"])
                    cs.append((140, 90, 45))
        front = (np.array(xs, np.float32), np.array(ys, np.float32), np.array(gs, np.int16), np.array(cs, np.float32))
        th = np.linspace(math.pi, 2 * math.pi, 220)
        hx, hy = CX + 47 * np.cos(th), BASKET_TOP + 40 * np.sin(th)
        hg = np.array([direction_glyph(-math.sin(a) * 47, math.cos(a) * 40) for a in th], np.int16)
        handle = (np.concatenate([hx, hx + 1]), np.concatenate([hy, hy]), np.concatenate([hg, hg]))
        return front, handle

    def update(self, dt, t):
        for c in self.clouds:
            c["x"] += c["v"] * dt
            if c["x"] > COLS + 20:
                c["x"] = -20

    def draw(self, canvas, t):
        x, y, d = disc(18, 14, 6)                                         # sun
        canvas.plot(x, y, np.where(d < 0.6, G["@"], G["#"]), np.outer(1 - 0.2 * d, (255, 215, 60)))
        for k in range(12):
            a = k * math.pi / 6 + t * 0.2
            r = np.linspace(8, 11 + 1.5 * math.sin(t * 2 + k), 5)
            canvas.plot(18 + np.cos(a) * r * ASPECT, 14 + np.sin(a) * r,
                        direction_glyph(math.cos(a) * ASPECT, math.sin(a)), (255, 195, 40))
        for c in self.clouds:
            canvas.plot(c["x"] + c["dx"], c["y"] + c["dy"], np.where(c["d"] < 0.7, G["@"], G["o"]), (255, 255, 255))

        sway = np.sin(t * 1.6 + self.grass_c * 0.12) * 0.6
        hmax = int(self.grass_h.max())
        for k in range(hmax):
            m = self.grass_h > k
            glyph = np.where(k == 0, G["|"], np.where(sway[m] > 0.25, G["/"], np.where(sway[m] < -0.25, G["\\"], G["|"])))
            canvas.plot(self.grass_c[m] + sway[m] * k * 0.6, self.grass_base[m] - k, glyph, self.grass_col[m])
        for f in self.flowers:
            s = math.sin(t * 1.6 + f["x"] * 0.12) * 0.6
            canvas.plot(np.full(3, f["x"]) + np.arange(3)[::-1] * s * 0.3, f["y"] - np.arange(3), G["|"], (60, 150, 60))
            hx, hy = f["x"] + s, f["y"] - 3
            if f["kind"] == "daisy":
                canvas.plot(hx + np.array([-1.3, 1.3, 0, 0]), hy + np.array([0, 0, -1, 1]), G["o"], (255, 255, 255))
                canvas.plot([hx], [hy], G["@"], (255, 210, 40))
            else:
                canvas.plot(hx + np.array([-1, 0, 1]), np.full(3, hy), np.array([G["("], G["@"], G[")"]]), f["color"])

        front, handle = self.basket
        canvas.plot(*handle, (160, 105, 55))

        pts, cols, glyphs, shade = [], [], [], []
        for i, (pos, color, glyph) in enumerate(self.eggs):
            a = t * (0.9 + 0.35 * i) + i
            ca, sa = math.cos(a), math.sin(a)
            x = pos[:, 0] * ca + pos[:, 2] * sa
            z = -pos[:, 0] * sa + pos[:, 2] * ca
            yy = pos[:, 1] + 0.06 * math.sin(t * 2 + i * 2)
            pts.append(np.stack([x + EGG_X[i], yy, z], 1))
            shade.append(np.clip(1.1 - z * 0.9, 0.45, 1.15))
            cols.append(color)
            glyphs.append(glyph)
        col, row, depth = project(np.concatenate(pts), canvas, tilt=0.12, scale=900, offset_rows=19.5)
        canvas.plot(col, row, np.concatenate(glyphs), np.concatenate(cols) * np.concatenate(shade)[:, None], depth)
        canvas.plot(*front)

        hop, phase = divmod(t, 1.1)
        p = min(phase / 0.6, 1.0)
        bx = (20 + 14 * (hop + p)) % (COLS + 20) - 10
        by = ROWS - 7 - (7 * math.sin(math.pi * p) if phase < 0.6 else 0)
        BUNNY.draw(canvas, bx, by)

        for b in self.butterflies:
            x = b["x0"] + 25 * math.sin(t * 0.4 * b["k"] + b["ph"])
            y = b["y0"] + 8 * math.sin(t * 0.7 * b["k"] + b["ph"] * 2)
            sprite = b["open"] if int(t * 8 + b["ph"]) % 2 else b["closed"]
            sprite.draw(canvas, x, y)

    def caption(self, t):
        return "Happy Easter!" if t > 1.5 else ""


SCENE = Easter
