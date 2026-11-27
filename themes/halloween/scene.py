"""Halloween: a graveyard under a full moon with glowing jack-o'-lanterns,
flapping bats, floating ghosts, a dangling spider, rolling fog and
lightning. Press L for lightning."""
import math

import numpy as np

from engine import ASPECT, G, Scene, Sprite, disc, line

COLS, ROWS = 150, 105
MOON_X, MOON_Y, MOON_R = 118.0, 20.0, 11.0

BAT = (150, 110, 170)
BAT_UP = Sprite(["\\   /", " \\@/ "], {"\\": ("\\", BAT), "/": ("/", BAT), "@": ("@", BAT)})
BAT_DOWN = Sprite([" _@_ ", "/   \\"], {"\\": ("\\", BAT), "/": ("/", BAT), "@": ("@", BAT),
                                        "_": ("_", BAT)})

_GHOST_TOP = ["  ####  ", " ###### ", "##o##o##", "########", "###oo###", "########"]
_GHOST_PAL = {"#": ("#", (225, 230, 255)), "o": ("o", (30, 25, 50))}
GHOST = [Sprite(_GHOST_TOP + ["## ## ##"], _GHOST_PAL),
         Sprite(_GHOST_TOP + ["# ## ## "], _GHOST_PAL)]

TOMBSTONE = Sprite([" ### ", "#####", "##+##", "#####", "#####"],
                   {"#": ("#", (95, 95, 115)), "+": ("+", (160, 160, 180))})

SPIDER = Sprite([" \\ / ", "-(@)-", " / \\ "],
                {"\\": ("\\", (170, 160, 180)), "/": ("/", (170, 160, 180)),
                 "-": ("-", (170, 160, 180)), "(": ("(", (170, 160, 180)),
                 ")": (")", (170, 160, 180)), "@": ("@", (200, 40, 60))})


def hill(col):
    return ROWS - 14 - 5 * np.sin(col * 0.05) - 3 * np.sin(col * 0.13 + 1)


def _pumpkin(cx, cy, size):
    rx = size * ASPECT * 1.3
    x, y, d = disc(cx, cy, size, rx=rx)
    u, v = (x - cx) / rx, (y - cy) / size
    eyes = (v > -0.45) & (v < -0.08) & (np.abs(np.abs(u) - 0.38) <= (v + 0.45) * 0.75)
    nose = (v > -0.02) & (v < 0.14) & (np.abs(u) <= (v + 0.02) * 0.8 + 0.03)
    mouth = ((v >= 0.25) & (v <= 0.42 + 0.12 * (1 - (u / 0.65) ** 2)) & (np.abs(u) < 0.65)
             & ~((v < 0.33) & (np.floor((u + 0.65) * 5) % 2 == 1)))
    face = eyes | nose | mouth
    rib = (np.abs((u * 2.5) % 1 - 0.5) < 0.12) & ~face
    shade = 1 - 0.45 * d ** 2
    color = np.where(rib[:, None], [[170, 70, 10]], [[245, 125, 20]]) * shade[:, None]
    glyph = np.where(face, G["@"], np.where(rib, G["|"], G["#"]))
    sx = np.array([cx, cx + 1])
    sy = np.array([cy - size - 0.5, cy - size - 1.5])
    return dict(x=x, y=y, glyph=glyph, color=color, face=face, stem=(sx, sy),
                phase=cx * 0.37)


def _bare_tree(rng):
    xs, ys, gs = [], [], []

    def grow(x, y, a, length, depth):
        x1, y1 = x + math.cos(a) * length * ASPECT, y + math.sin(a) * length
        for off in ([-1, 0, 1] if depth == 0 else [0, 1] if depth == 1 else [0]):
            lx, ly, g = line(x + off, y, x1 + off, y1)
            xs.append(lx)
            ys.append(ly)
            gs.append(np.full(len(lx), G["#"] if depth <= 1 else g))
        if depth < 5:
            for s in (-1, 1):
                grow(x1, y1, a + s * rng.uniform(0.3, 0.8), length * rng.uniform(0.6, 0.75),
                     depth + 1)

    grow(14, float(hill(14)) + 1, -math.pi / 2 + 0.1, 16, 0)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(gs).astype(np.int16)


class Halloween(Scene):
    title = "Halloween"
    cols, rows = COLS, ROWS
    background = ((14, 4, 26), (4, 10, 8))
    caption_color = "#ff8c1a"
    help_text = "   L lightning"

    def setup(self, canvas):
        rng = np.random.default_rng(13)
        canvas.set_background(*self.background)
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        dist = np.hypot((X - MOON_X) / ASPECT, Y - MOON_Y)
        canvas.bg += (np.exp(-(dist / 20) ** 2) * 45)[..., None] * np.array([1.0, 0.9, 0.6])
        canvas.bg[Y >= hill(X)] = (6, 12, 8)
        self.base_bg = canvas.bg.copy()

        mx, my, d = disc(MOON_X, MOON_Y, MOON_R)
        crater = np.zeros(len(mx), dtype=bool)
        for _ in range(7):
            ccx = MOON_X + rng.uniform(-0.6, 0.6) * MOON_R * ASPECT
            ccy = MOON_Y + rng.uniform(-0.6, 0.6) * MOON_R
            cr = rng.uniform(1.2, 3.0)
            crater |= np.hypot((mx - ccx) / ASPECT, my - ccy) < cr
        self.moon = (mx, my, np.where(crater, G["o"], G["#"]),
                     np.outer((1 - 0.3 * d ** 2) * np.where(crater, 0.75, 1.0), (250, 235, 170)))

        sx, sy = rng.uniform(0, COLS, 120), rng.uniform(0, ROWS - 30, 120)
        ok = (sy < hill(sx) - 3) & (np.hypot((sx - MOON_X) / ASPECT, sy - MOON_Y) > MOON_R + 2)
        self.stars = (sx[ok], sy[ok], rng.uniform(0, 6.3, ok.sum()))

        self.tree = _bare_tree(rng)
        self.tombs = [(c, float(hill(c)) - 2) for c in (30, 58, 84, 112, 138)]
        self.pumpkins = [_pumpkin(c, float(hill(c)) - s + 1, s) for c, s in ((45, 6), (70, 5), (98, 7))]

    def reset(self):
        rng = self.rng = np.random.default_rng()
        self.bats = [dict(x=rng.uniform(0, COLS), y=rng.uniform(8, 50), vx=rng.choice([-1, 1]) * rng.uniform(8, 16),
                          ph=rng.uniform(0, 6.3), rate=rng.uniform(9, 14)) for _ in range(9)]
        self.ghosts = [dict(x=rng.uniform(10, COLS - 10), y=rng.uniform(40, 70), vx=rng.uniform(-5, 5),
                            ph=rng.uniform(0, 6.3)) for _ in range(3)]
        n = 260
        self.fog = [rng.uniform(0, COLS, n), rng.uniform(ROWS - 20, ROWS, n),
                    rng.uniform(1, 4, n), rng.uniform(0, 6.3, n)]
        self.flash = 0.0
        self.bolt = None
        self.next_bolt = rng.uniform(4, 8)
        self.t = 0.0

    def strike(self):
        rng = self.rng
        x, y, segs = rng.uniform(25, 105), 0.0, []
        bottom = rng.uniform(45, 70)
        while y < bottom:
            nx, ny = x + rng.uniform(-5, 5), y + rng.uniform(3, 7)
            segs.append((x, y, nx, ny))
            if rng.random() < 0.25:
                segs.append((nx, ny, nx + rng.uniform(-9, 9), ny + rng.uniform(4, 9)))
            x, y = nx, ny
        parts = [line(*s) for s in segs]
        self.bolt = (np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts]),
                     np.concatenate([np.full(len(p[0]), p[2]) for p in parts]).astype(np.int16))
        self.flash = 1.0

    def update(self, dt, t):
        self.t = t
        for b in self.bats:
            b["x"] = (b["x"] + b["vx"] * dt + 10) % (COLS + 20) - 10
        for g in self.ghosts:
            g["x"] += (g["vx"] + 4 * math.sin(t * 0.5 + g["ph"])) * dt
            if not 5 < g["x"] < COLS - 5:
                g["vx"] = -g["vx"]
                g["x"] = min(max(g["x"], 5), COLS - 5)
        fx, fy, fv, fph = self.fog
        fx += fv * dt
        fx %= COLS
        if t >= self.next_bolt:
            self.strike()
            self.next_bolt = t + self.rng.uniform(6, 14)
        self.flash *= math.exp(-dt * 7)

    def draw(self, canvas, t):
        canvas.bg = self.base_bg + self.flash * np.array([70, 70, 100], np.float32)

        sx, sy, sph = self.stars
        tw = 0.5 + 0.5 * np.sin(t * 2 + sph)
        canvas.plot(sx, sy, G["."], np.outer(0.3 + 0.6 * tw, (200, 200, 255)))
        canvas.plot(*self.moon)
        canvas.plot(*self.tree, (40, 32, 48))

        for x, y in self.tombs:
            TOMBSTONE.draw(canvas, x, y)
        for p in self.pumpkins:
            flicker = 0.75 + 0.25 * math.sin(t * 9 + p["phase"]) * math.sin(t * 5.3 + p["phase"] * 2)
            color = np.where(p["face"][:, None], np.array([255, 215, 70]) * flicker, p["color"])
            canvas.plot(p["x"], p["y"], p["glyph"], color)
            canvas.plot(*p["stem"], np.array([G["|"], G["/"]]), (70, 140, 50))

        for g in self.ghosts:
            alpha = 0.45 + 0.35 * math.sin(t * 1.3 + g["ph"])
            frame = GHOST[int(t * 4 + g["ph"]) % 2]
            frame.draw(canvas, g["x"], g["y"] + 3 * math.sin(t * 1.7 + g["ph"]), alpha, flip=g["vx"] < 0)

        for b in self.bats:
            up = math.sin(t * b["rate"] + b["ph"]) > 0
            (BAT_UP if up else BAT_DOWN).draw(canvas, b["x"], b["y"] + 4 * math.sin(t * 1.3 + b["ph"]))

        length = 26 + 14 * math.sin(t * 0.6)
        thread = np.arange(0, length, dtype=np.float32)
        canvas.plot(np.full(len(thread), 141.0), thread, G["|"], (110, 110, 125))
        SPIDER.draw(canvas, 141, length + 1)

        if self.bolt is not None and self.flash > 0.25:
            canvas.plot(*self.bolt, np.array([230, 230, 255]) * self.flash)

        fx, fy, fv, fph = self.fog
        canvas.plot(fx, fy, G["~"], np.outer(0.2 + 0.15 * np.sin(t * 0.7 + fph), (150, 160, 170)))

    def caption(self, t):
        return "Happy Halloween!" if t > 1.5 else ""

    def on_key(self, key):
        if key == "l":
            self.strike()


SCENE = Halloween
