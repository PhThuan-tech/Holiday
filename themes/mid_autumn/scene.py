"""Mid-Autumn Festival: a giant full moon with the banyan tree, clouds
drifting past, sky lanterns rising, rotating five-pointed star lanterns
and mooncakes on the table."""
import math

import numpy as np

from engine import ASPECT, G, Scene, Sprite, blob, disc, rotate, star_outline

COLS, ROWS = 150, 105
MOON_X, MOON_Y, MOON_R = 75.0, 34.0, 21.0

_TREE = (105, 70, 35)
BANYAN = Sprite(r"""
    #####
  #########
 ###########
#############
 ###########
   # ### #
     ###   @
     ###  /|\
    #####  /\
""", {"#": ("#", _TREE), "@": ("@", _TREE), "/": ("/", _TREE), "|": ("|", _TREE),
      "\\": ("\\", _TREE)})

_LANTERN = {"#": ("#", (255, 140, 40)), "*": ("*", (255, 235, 140))}
SKY_LANTERNS = [
    Sprite(["@"], {"@": ("@", (255, 150, 50))}),
    Sprite(["###", " * "], _LANTERN),
    Sprite(["#####", "#####", " ### ", "  *  "], _LANTERN),
]


class MidAutumn(Scene):
    title = "Mid-Autumn Festival"
    cols, rows = COLS, ROWS
    background = ((4, 8, 30), (22, 22, 62))
    caption_color = "#ffcf5a"

    def setup(self, canvas):
        rng = np.random.default_rng(15)
        canvas.set_background(*self.background)
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        dist = np.hypot((X - MOON_X) / ASPECT, Y - MOON_Y)
        canvas.bg += (np.exp(-((dist - MOON_R) / 12).clip(0) ** 2) * 40)[..., None] * np.array([1.0, 0.8, 0.45])

        mx, my, d = disc(MOON_X, MOON_Y, MOON_R)
        tex = np.sin(mx * 0.31) * np.sin(my * 0.43) + np.sin(mx * 0.11 + my * 0.17)
        mare = tex > 0.7
        shade = (1 - 0.25 * d ** 2) * (0.92 + 0.08 * tex) * np.where(mare, 0.82, 1.0)
        self.moon = (mx, my, np.where(mare, G["o"], G["#"]), np.outer(shade, (255, 226, 140)))

        sx, sy = rng.uniform(0, COLS, 110), rng.uniform(0, ROWS - 25, 110)
        ok = np.hypot((sx - MOON_X) / ASPECT, sy - MOON_Y) > MOON_R + 3
        self.stars = (sx[ok], sy[ok], rng.uniform(0, 6.3, ok.sum()))

        self.clouds = []
        for i in range(4):
            bx, by, bd = blob(rng, int(rng.integers(3, 5)), rng.uniform(2.5, 4))
            self.clouds.append(dict(dx=bx, dy=by, d=bd, x=rng.uniform(-20, COLS),
                                    y=rng.uniform(12, 55), v=rng.uniform(1.5, 3.5)))

        self.cakes = []
        for cx, cy, r in ((58, ROWS - 9, 3.2), (75, ROWS - 10, 4.2), (92, ROWS - 9, 3.2)):
            x, y, dd = disc(cx, cy, r)
            glyph = np.where(dd > 0.78, G["*"], np.where(dd < 0.35, G["@"], G["#"]))
            color = np.where((dd > 0.78)[:, None], [[230, 160, 65]],
                             np.where((dd < 0.35)[:, None], [[185, 115, 40]], [[210, 140, 55]]))
            self.cakes.append((x, y, glyph, color * (1 - 0.15 * dd)[:, None]))

        self.star_lanterns = [dict(x=20, y=72, r=8, spin=0.6, ph=0.0),
                              dict(x=130, y=70, r=9, spin=-0.5, ph=2.0),
                              dict(x=108, y=86, r=5.5, spin=0.8, ph=4.0)]
        self.star_u, self.star_v, self.star_edge = star_outline(samples=14)

    def reset(self):
        rng = self.rng = np.random.default_rng()
        n = 24
        self.lan_x = rng.uniform(5, COLS - 5, n)
        self.lan_y = rng.uniform(0, ROWS, n)
        self.lan_size = rng.choice([0, 0, 1, 1, 2], n)
        self.lan_ph = rng.uniform(0, 6.3, n)

    def update(self, dt, t):
        speed = np.array([1.2, 2.2, 3.4])[self.lan_size]
        self.lan_y -= speed * dt
        self.lan_x += np.sin(t * 0.6 + self.lan_ph) * 1.5 * dt
        gone = self.lan_y < -5
        self.lan_y[gone] = ROWS + 4
        self.lan_x[gone] = self.rng.uniform(5, COLS - 5, gone.sum())
        for c in self.clouds:
            c["x"] += c["v"] * dt
            if c["x"] > COLS + 25:
                c["x"] = -25

    def _draw_lanterns(self, canvas, t, sizes):
        for i in np.nonzero(np.isin(self.lan_size, sizes))[0]:
            glow = 0.75 + 0.25 * math.sin(t * 7 + self.lan_ph[i])
            SKY_LANTERNS[self.lan_size[i]].draw(canvas, self.lan_x[i], self.lan_y[i], glow)

    def draw(self, canvas, t):
        sx, sy, sph = self.stars
        tw = 0.5 + 0.5 * np.sin(t * 2 + sph)
        canvas.plot(sx, sy, np.where(tw > 0.9, G["+"], G["."]), np.outer(0.3 + 0.6 * tw, (220, 220, 255)))
        canvas.plot(*self.moon)
        BANYAN.draw(canvas, MOON_X - 9, MOON_Y + 9)

        self._draw_lanterns(canvas, t, [0])
        for c in self.clouds:
            canvas.plot(c["x"] + c["dx"], c["y"] + c["dy"], np.where(c["d"] > 0.6, G["~"], G["-"]),
                        np.outer(1 - 0.4 * c["d"], (150, 160, 200)))
        self._draw_lanterns(canvas, t, [1, 2])

        for s in self.star_lanterns:
            ang = t * s["spin"] + s["ph"]
            stick = np.arange(s["y"] + s["r"] * 0.4, ROWS)
            canvas.plot(np.full(len(stick), float(s["x"])), stick, G["|"], (130, 90, 50))
            spokes = np.linspace(0.15, 0.9, 6)[None, :]
            k = np.arange(10)
            vang = -math.pi / 2 + k * math.pi / 5
            vrad = np.where(k % 2 == 0, 1.0, 0.42)
            fu = (np.cos(vang) * vrad)[:, None] * spokes
            fv = (np.sin(vang) * vrad)[:, None] * spokes
            fx, fy = rotate(fu.ravel() * s["r"] * ASPECT, fv.ravel() * s["r"], ang)
            canvas.plot(s["x"] + fx, s["y"] + fy, G["+"], (150, 80, 30))
            ex, ey = rotate(self.star_u * s["r"] * ASPECT, self.star_v * s["r"], ang)
            color = np.where((self.star_edge % 2 == 0)[:, None], [[255, 60, 50]], [[255, 210, 60]])
            canvas.plot(s["x"] + ex, s["y"] + ey, G["*"], color)
            for vi in (4, 6):                                 # tassels on the lower points
                tx, ty = rotate(math.cos(vang[vi]) * s["r"] * ASPECT, math.sin(vang[vi]) * s["r"], ang)
                canvas.plot(np.full(3, s["x"] + tx), s["y"] + ty + np.arange(1, 4), G["|"], (255, 90, 60))
            flame = 0.8 + 0.2 * math.sin(t * 11 + s["ph"])
            canvas.plot([s["x"]], [s["y"]], G["@"], np.array([255, 225, 120]) * flame)

        canvas.plot(np.arange(42, 109, dtype=np.float32), np.full(67, ROWS - 5.0), G["="], (140, 85, 45))
        for cake in self.cakes:
            canvas.plot(*cake)

    def caption(self, t):
        return "Happy Mid-Autumn Festival\nTết Trung Thu vui vẻ" if t > 2 else ""


SCENE = MidAutumn
