"""Vietnam National Day (2/9): the Ho Chi Minh Mausoleum under a bright
sun, the red flag with the yellow star waving on its roof, white doves,
and a framed portrait of President Ho Chi Minh made from a photo.

The portrait comes from an image file you provide:
    themes/national_day/assets/portrait.png   (or .jpg / .jpeg / .gif)
or a path on the command line:
    python run.py national-day path/to/photo.jpg
PNG and GIF work out of the box; JPG needs `pip install pillow`.
"""
import datetime
import math
import os

import numpy as np

from engine import ASPECT, CELL_H, CELL_W, G, Scene, Sprite, direction_glyph, disc, image_to_cells

COLS, ROWS = 150, 105
CX = 75                                   # mausoleum centre column
GROUND = 96
SUN_X, SUN_Y = 128.0, 15.0
FLAG_W, FLAG_H = 30, 15                   # 3:2 on screen (cells are 6x8 px)
POLE_TOP = 26
PORTRAIT_BOX = (5, 4, 47, 44)             # col, row, max width, max height (cells)
ASSETS = os.path.join(os.path.dirname(__file__), "assets")

WHITE = (250, 250, 250)
DOVE_UP = Sprite(["\\   /", " \\o/ "], {"\\": ("\\", WHITE), "/": ("/", WHITE), "o": ("o", WHITE)})
DOVE_DOWN = Sprite([" _o_ ", "/   \\"], {"\\": ("\\", WHITE), "/": ("/", WHITE), "o": ("o", WHITE),
                                        "_": ("_", WHITE)})


def _in_star(px, py, cx, cy, r, inner=0.382):
    """Even-odd test: are points (px, py) inside a 5-pointed star?"""
    k = np.arange(10)
    ang = -math.pi / 2 + k * math.pi / 5
    rad = np.where(k % 2 == 0, r, r * inner)
    vx, vy = cx + rad * np.cos(ang), cy + rad * np.sin(ang)
    inside = np.zeros(px.shape, dtype=bool)
    for i in range(10):
        x1, y1, x2, y2 = vx[i], vy[i], vx[(i + 1) % 10], vy[(i + 1) % 10]
        crosses = (y1 > py) != (y2 > py)
        inside ^= crosses & (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-9) + x1)
    return inside


def _mausoleum():
    xs, ys, gs, cs = [], [], [], []

    def rect(c0, c1, r0, r1, glyph, color):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                xs.append(c)
                ys.append(r)
                gs.append(G[glyph] if isinstance(glyph, str) else glyph(c, r))
                cs.append(color(c, r) if callable(color) else color)

    granite = (175, 172, 165)
    # three-step red granite platform
    for i, (half, r0, r1) in enumerate(((40, 93, 95), (37, 91, 92), (34, 89, 90))):
        rect(CX - half, CX + half, r0, r1, "=", (150 - i * 8, 55, 48))
    rect(CX - 32, CX + 32, 84, 88, "#", (125, 60, 52))                     # podium
    rect(CX - 30, CX + 30, 66, 83, "#", (55, 55, 62))                      # shaded wall behind columns
    rect(CX - 3, CX + 3, 72, 83, "#", (25, 25, 30))                        # entrance
    for c in np.linspace(CX - 29, CX + 27, 8).astype(int):                 # square columns
        rect(c, c + 2, 66, 83, "#",
             lambda cc, rr, c=c: tuple(np.array(granite) * (1.05 if cc == c else 0.9 if cc == c + 2 else 1.0)))
    rect(CX - 34, CX + 34, 58, 65, "#", (190, 188, 180))                   # frieze (inscription)
    rect(CX - 34, CX + 34, 57, 57, "=", (150, 148, 140))
    rect(CX - 31, CX + 31, 54, 56, "=", (200, 198, 190))                   # stepped roof
    rect(CX - 26, CX + 26, 52, 53, "=", (185, 183, 175))
    for c in range(CX - 28, CX + 29, 4):                                   # flowers along the base
        xs.append(c)
        ys.append(88)
        gs.append(G["@"])
        cs.append((230, 40, 40) if (c // 4) % 2 else (255, 210, 50))
    return (np.array(xs, np.float32), np.array(ys, np.float32),
            np.array(gs, np.int16), np.array(cs, np.float32))


def _find_portrait(path):
    if path:
        return path if os.path.isfile(path) else None
    for ext in ("png", "jpg", "jpeg", "gif"):
        p = os.path.join(ASSETS, f"portrait.{ext}")
        if os.path.isfile(p):
            return p
    return None


class NationalDay(Scene):
    title = "Vietnam National Day"
    cols, rows = COLS, ROWS
    background = ((70, 135, 220), (255, 214, 160))
    caption_color = "#c8102e"

    def __init__(self, portrait=""):
        self.portrait_path = _find_portrait(portrait)
        self.portrait = None
        self.portrait_error = ""
        self.building = _mausoleum()

        j, i = np.mgrid[0:FLAG_H, 0:FLAG_W]
        self.flag_i, self.flag_j = i.ravel().astype(np.float32), j.ravel().astype(np.float32)
        px, py = (self.flag_i + 0.5) * CELL_W, (self.flag_j + 0.5) * CELL_H
        w_px, h_px = FLAG_W * CELL_W, FLAG_H * CELL_H
        self.flag_star = _in_star(px, py, w_px / 2, h_px / 2, w_px / 5)

    def setup(self, canvas):
        rng = np.random.default_rng(29)
        canvas.set_background(*self.background)
        Y, X = np.mgrid[0:ROWS, 0:COLS]
        dist = np.hypot((X - SUN_X) / ASPECT, Y - SUN_Y)
        canvas.bg += (np.exp(-(dist / 26) ** 2) * 90)[..., None] * np.array([1.0, 0.85, 0.5])
        canvas.bg[Y >= GROUND] = (70, 150, 70)
        c0, r0, w, h = PORTRAIT_BOX
        panel = (25, 18, 14)

        gx = rng.uniform(0, COLS, 400)
        self.lawn = (gx, rng.uniform(GROUND, ROWS, 400), G["."], (60, 125, 55))
        self.trees = []
        for cx, r in ((16, 7), (30, 5), (122, 6), (138, 8)):
            x, y, d = disc(cx, GROUND - r + 1, r)
            self.trees.append((x, y, np.where(d < 0.7, G["#"], G["@"]), np.outer(1 - 0.35 * d, (40, 120, 50))))

        if self.portrait_path:
            try:
                # A drawing on light paper -> ink on a cream panel; a photo -> colours on a dark panel.
                dx, dy, g, c = image_to_cells(self.portrait_path, w, h, ink=(30, 22, 20))
                full_w, full_h = image_to_cells(self.portrait_path, w, h)[0:2]
                cols, rows = full_w.max() + 1, full_h.max() + 1
                if len(dx) < 0.6 * cols * rows:
                    panel = (246, 236, 214)
                else:
                    dx, dy, g, c = image_to_cells(self.portrait_path, w, h)
                    c = np.clip(c * 1.15 + 10, 0, 255)
                ox, oy = c0 + (w - cols) / 2, r0 + (h - rows) / 2
                self.portrait = (dx + ox, dy + oy, g, c)
            except Exception as exc:                     # unreadable file: show a hint instead
                self.portrait_error = f"Could not read image: {exc}"
        canvas.bg[r0 - 1:r0 + h + 1, c0 - 2:c0 + w + 2] = panel
        canvas.bg = np.clip(canvas.bg, 0, 255)

    def reset(self):
        rng = self.rng = np.random.default_rng()
        self.doves = [dict(x=rng.uniform(0, COLS), y=rng.uniform(8, 40), v=rng.uniform(7, 12),
                           ph=rng.uniform(0, 6.3)) for _ in range(6)]

    def update(self, dt, t):
        for d in self.doves:
            d["x"] -= d["v"] * dt
            if d["x"] < -6:
                d["x"], d["y"] = COLS + 6, self.rng.uniform(8, 40)

    def draw(self, canvas, t):
        x, y, d = disc(SUN_X, SUN_Y, 7)
        pulse = 0.92 + 0.08 * math.sin(t * 2)
        canvas.plot(x, y, np.where(d < 0.55, G["@"], G["#"]), np.outer((1.05 - 0.15 * d) * pulse, (255, 230, 120)))
        for k in range(16):
            a = k * math.pi / 8 + t * 0.15
            r = np.linspace(9, 13 + 2.5 * math.sin(t * 2.5 + k * 1.3), 6)
            canvas.plot(SUN_X + np.cos(a) * r * ASPECT, SUN_Y + np.sin(a) * r,
                        direction_glyph(math.cos(a) * ASPECT, math.sin(a)), (255, 200, 60))

        for dv in self.doves:
            up = math.sin(t * 10 + dv["ph"]) > 0
            (DOVE_UP if up else DOVE_DOWN).draw(canvas, dv["x"], dv["y"] + 2 * math.sin(t + dv["ph"]))

        canvas.plot(*self.lawn)
        for tree in self.trees:
            canvas.plot(*tree)
        canvas.plot(*self.building)

        pole = np.arange(POLE_TOP - 1, 52, dtype=np.float32)
        canvas.plot(np.full(len(pole), float(CX)), pole, G["|"], (210, 210, 215))
        canvas.plot([CX], [POLE_TOP - 2], G["o"], (255, 215, 80))
        u = self.flag_i / FLAG_W
        phase = u * 2 * math.pi * 1.3 - t * 4
        wave = np.sin(phase) * 1.3 * u
        shade = 0.78 + 0.22 * np.cos(phase)
        color = np.where(self.flag_star[:, None], [[255, 225, 0]], [[218, 37, 29]]) * shade[:, None]
        canvas.plot(CX + 1 + self.flag_i, POLE_TOP + self.flag_j + wave,
                    np.where(self.flag_star, G["@"], G["#"]), color)

        c0, r0, w, h = PORTRAIT_BOX
        gold = (225, 180, 60)
        canvas.plot(np.arange(c0 - 2, c0 + w + 2), np.full(w + 4, r0 - 1.0), G["="], gold)
        canvas.plot(np.arange(c0 - 2, c0 + w + 2), np.full(w + 4, r0 + h + 0.0), G["="], gold)
        canvas.plot(np.full(h, c0 - 2.0), np.arange(r0, r0 + h), G["|"], gold)
        canvas.plot(np.full(h, c0 + w + 1.0), np.arange(r0, r0 + h), G["|"], gold)
        if self.portrait is not None:
            canvas.plot(*self.portrait)

    def labels(self, t):
        c0, r0, w, h = PORTRAIT_BOX
        out = [(CX + 0.5, 61.5, "CHỦ TỊCH HỒ CHÍ MINH", "#b3121f", 14),
               (c0 + w / 2, r0 + h + 2.2, "Chủ tịch Hồ Chí Minh (1890 – 1969)", "#7a1010", 11)]
        if self.portrait is None:
            hint = self.portrait_error or "Put a portrait photo at\nthemes/national_day/assets/portrait.png"
            out.append((c0 + w / 2, r0 + h / 2, hint, "#e8d9a0", 10))
        return out

    def caption(self, t):
        if t < 1.5:
            return ""
        today = datetime.date.today()
        year = today.year if (today.month, today.day) <= (9, 2) else today.year + 1
        return (f"Mừng Quốc khánh 2/9 – {year - 1945} năm (1945 – {year})\n"
                "Độc lập – Tự do – Hạnh phúc")


SCENE = NationalDay
