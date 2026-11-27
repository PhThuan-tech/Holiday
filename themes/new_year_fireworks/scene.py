"""New Year Fireworks: rockets rise over a city skyline and burst into many
patterns (peony, rainbow, rings, heart, star, willow, palm, crossette,
glitter, spiral) plus the new year's number written in sparks."""
import colorsys
import datetime
import math

import numpy as np

from engine import ASPECT, G, Scene

COLS, ROWS = 150, 105
GRAVITY = 28.0                   # rows / s^2

PALETTE = [(255, 60, 60), (255, 150, 40), (255, 215, 70), (80, 230, 90), (60, 220, 230),
           (70, 120, 255), (180, 90, 255), (255, 100, 200), (240, 240, 255)]
FADE_GLYPHS = np.array([G["'"], G["."], G["+"], G["*"]], dtype=np.int16)   # dim -> bright

DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
}


# ------------------------------------------------------------------ particles
FIELDS = {"x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0, "life": 1.0, "max_life": 1.0,
          "drag": 1.2, "grav": 1.0, "flicker": 0.0, "trail": 0.0, "split": np.inf}


class Particles:
    """Struct-of-arrays particle store."""

    def __init__(self):
        for k in FIELDS:
            setattr(self, k, np.zeros(0, dtype=np.float32))
        self.color = np.zeros((0, 3), dtype=np.float32)

    def __len__(self):
        return len(self.x)

    def add(self, color, **values):
        n = len(np.atleast_1d(values["x"]))
        if n == 0:
            return
        values.setdefault("max_life", values["life"])
        for k, default in FIELDS.items():
            v = np.broadcast_to(np.asarray(values.get(k, default), dtype=np.float32), (n,))
            setattr(self, k, np.concatenate([getattr(self, k), v]))
        c = np.broadcast_to(np.asarray(color, dtype=np.float32), (n, 3))
        self.color = np.concatenate([self.color, c])

    def keep(self, mask):
        for k in FIELDS:
            setattr(self, k, getattr(self, k)[mask])
        self.color = self.color[mask]


# ------------------------------------------------------------------ burst patterns
# Each pattern returns a list of particle groups (dicts without x / y).

def _sphere(rng, n):
    v = rng.normal(size=(n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v[:, 0], v[:, 1]


def _ring_dirs(n, tilt, rot):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x, y = np.cos(a), np.sin(a) * tilt
    return x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)


def _group(dx, dy, speed, color, **kw):
    return dict(vx=dx * speed * ASPECT, vy=dy * speed, color=color, **kw)


def peony(rng, color):
    dx, dy = _sphere(rng, 220)
    return [_group(dx, dy, rng.uniform(24, 30), color, life=rng.uniform(1.4, 2.0, 220), drag=1.3)]


def rainbow(rng, color):
    dx, dy = _sphere(rng, 240)
    hue = (np.arctan2(dy, dx) / (2 * math.pi)) % 1
    cols = np.array([colorsys.hsv_to_rgb(h, 0.75, 1.0) for h in hue]) * 255
    return [_group(dx, dy, 27, cols, life=rng.uniform(1.5, 2.1, 240), drag=1.3)]


def ring(rng, color):
    dx, dy = _ring_dirs(100, rng.uniform(0.25, 1.0), rng.uniform(0, math.pi))
    return [_group(dx, dy, 28, color, life=1.8, drag=1.4, grav=0.6)]


def double_ring(rng, color):
    tilt, rot = rng.uniform(0.25, 1.0), rng.uniform(0, math.pi)
    other = PALETTE[rng.integers(len(PALETTE))]
    dx, dy = _ring_dirs(100, tilt, rot)
    ex, ey = _ring_dirs(70, tilt, rot)
    return [_group(dx, dy, 30, color, life=1.9, drag=1.4, grav=0.6),
            _group(ex, ey, 17, other, life=1.9, drag=1.4, grav=0.6)]


def heart(rng, color):
    t = np.linspace(0, 2 * math.pi, 130, endpoint=False)
    hx = 16 * np.sin(t) ** 3 / 17
    hy = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)) / 17
    return [_group(hx, hy, 26, (255, 80, 150), life=2.3, drag=1.6, grav=0.35)]


def star(rng, color):
    k = np.arange(10)
    ang = -math.pi / 2 + rng.uniform(-0.3, 0.3) + k * math.pi / 5
    rad = np.where(k % 2 == 0, 1.0, 0.42)
    px, py = rad * np.cos(ang), rad * np.sin(ang)
    s = np.linspace(0, 1, 14, endpoint=False)[None, :]
    xs = (px[:, None] * (1 - s) + np.roll(px, -1)[:, None] * s).ravel()
    ys = (py[:, None] * (1 - s) + np.roll(py, -1)[:, None] * s).ravel()
    return [_group(xs, ys, 28, (255, 215, 70), life=2.2, drag=1.6, grav=0.35)]


def willow(rng, color):
    dx, dy = _sphere(rng, 150)
    return [_group(dx, dy, 22, (255, 185, 80), life=rng.uniform(3.0, 3.8, 150),
                   drag=1.8, grav=0.7, trail=1)]


def palm(rng, color):
    arms = 7
    a = rng.uniform(0, 2 * math.pi) + np.repeat(np.arange(arms) * 2 * math.pi / arms, 10)
    s = np.tile(np.linspace(0.35, 1.0, 10), arms)
    return [_group(np.cos(a) * s, np.sin(a) * s, 32, color, life=2.0, drag=1.4, grav=0.8, trail=1)]


def crossette(rng, color):
    a = np.linspace(0, 2 * math.pi, 12, endpoint=False) + rng.uniform(0, 1)
    return [_group(np.cos(a), np.sin(a), 24, color, life=1.6, drag=1.0, trail=1, split=0.7)]


def glitter(rng, color):
    dx, dy = _sphere(rng, 260)
    return [_group(dx, dy, 25, (235, 235, 255), life=rng.uniform(1.6, 2.4, 260),
                   drag=1.3, flicker=1)]


def spiral(rng, color):
    arms, n = 3, 45
    s = np.tile(np.linspace(0.2, 1.0, n), arms)
    arm = np.repeat(np.arange(arms), n)
    a = rng.uniform(0, 2 * math.pi) + arm * 2 * math.pi / arms + s * 2.6
    first = int(rng.integers(len(PALETTE)))
    cols = np.array([PALETTE[(first + 3 * i) % len(PALETTE)] for i in arm], dtype=np.float32)
    return [_group(np.cos(a) * s, np.sin(a) * s, 30, cols, life=2.0, drag=1.4, grav=0.5)]


def year_text(rng, text):
    """Sparks that fly out and settle into the digits of `text`."""
    pts = [(i * 4 + c, r) for i, ch in enumerate(text)
           for r, line in enumerate(DIGITS[ch]) for c, v in enumerate(line) if v == "#"]
    pts = np.repeat(np.array(pts, dtype=np.float32), 2, axis=0)
    width = len(text) * 4 - 1
    ox = (pts[:, 0] - (width - 1) / 2) * 3.0 + rng.uniform(-0.6, 0.6, len(pts))
    oy = (pts[:, 1] - 2) * 2.6 + rng.uniform(-0.5, 0.5, len(pts))
    drag = 2.5                     # final offset = v / drag
    return [dict(vx=ox * drag, vy=oy * drag, color=(255, 215, 90), life=3.6,
                 drag=drag, grav=0.05)]


PATTERNS = {peony: 3, rainbow: 2, ring: 2, double_ring: 2, heart: 1.5, star: 1.5,
            willow: 2, palm: 2, crossette: 1.5, glitter: 1.5, spiral: 1.5}
_PATTERN_LIST = list(PATTERNS)
_PATTERN_P = np.array(list(PATTERNS.values())) / sum(PATTERNS.values())


# ------------------------------------------------------------------ scene
def _target_year():
    now = datetime.datetime.now()
    return now.year if (now.month == 1 and now.day <= 7) else now.year + 1


class NewYearFireworks(Scene):
    title = "New Year Fireworks"
    cols, rows = COLS, ROWS
    caption_color = "#ffe08a"
    help_text = "   F finale   CLICK launch a rocket"

    def __init__(self):
        self.year = _target_year()

    def setup(self, canvas):
        rng = np.random.default_rng(31)
        canvas.set_background((2, 3, 12), (26, 18, 52))
        building = np.zeros((ROWS, COLS), dtype=bool)
        win_x, win_y = [], []
        x = 0
        while x < COLS:
            w, h = int(rng.integers(5, 13)), int(rng.integers(6, 24))
            top = ROWS - h
            shade = rng.uniform(8, 16)
            building[top:, x:x + w] = True
            canvas.bg[top:, x:x + w] = (shade, shade, shade + 10)
            for r in range(top + 1, ROWS - 1, 2):
                for c in range(x + 1, min(x + w - 1, COLS), 2):
                    win_x.append(c)
                    win_y.append(r)
            x += w + int(rng.integers(0, 2))
        self.building = building
        self.base_bg = canvas.bg.copy()
        self.win_x = np.array(win_x, dtype=np.float32)
        self.win_y = np.array(win_y, dtype=np.float32)
        self.win_lit = rng.random(len(win_x)) < 0.35

        n = 140
        sx, sy = rng.uniform(0, COLS, n), rng.uniform(0, ROWS - 30, n)
        sky = ~building[sy.astype(int), sx.astype(int)]
        self.star_x, self.star_y = sx[sky], sy[sky]
        self.star_ph = rng.uniform(0, 2 * math.pi, len(self.star_x))

    def reset(self):
        self.rng = np.random.default_rng()
        self.parts = Particles()
        self.rockets = []
        self.queue = []                         # (time, target, pattern)
        self.t = 0.0
        self.next_launch = 0.5
        self.next_year = 4.0
        self.next_finale = 25.0
        self.flash = 0.0
        self.flash_color = np.zeros(3, dtype=np.float32)

    # ---- launching
    def launch(self, target=None, pattern=None):
        rng = self.rng
        tx, ty = target or (rng.uniform(15, COLS - 15), rng.uniform(10, 45))
        x0 = float(np.clip(tx + rng.uniform(-25, 25), 5, COLS - 5))
        y0 = ROWS - 1
        vy = -math.sqrt(2 * GRAVITY * max(y0 - ty, 5))
        vx = (tx - x0) / (-vy / GRAVITY)
        if pattern is None:
            pattern = _PATTERN_LIST[rng.choice(len(_PATTERN_LIST), p=_PATTERN_P)]
        color = np.array(PALETTE[rng.integers(len(PALETTE))], dtype=np.float32)
        self.rockets.append(dict(x=x0, y=y0, vx=vx, vy=vy, pattern=pattern, color=color))

    def finale(self):
        for i in range(14):
            self.queue.append((self.t + i * 0.15, None, None))

    def explode(self, r):
        if r["pattern"] == "year":
            groups = year_text(self.rng, str(self.year))
        else:
            groups = r["pattern"](self.rng, r["color"])
        for grp in groups:
            n = len(grp["vx"])
            color = grp.pop("color")
            self.parts.add(color, x=np.full(n, r["x"]), y=np.full(n, r["y"]), **grp)
        self.flash = min(1.0, self.flash + 0.6)
        self.flash_color = r["color"]

    # ---- simulation
    def update(self, dt, t):
        self.t = t
        rng = self.rng
        if t >= self.next_launch:
            self.launch()
            self.next_launch = t + rng.uniform(0.35, 1.0)
        if t >= self.next_year:
            self.launch(target=(COLS / 2, 30), pattern="year")
            self.next_year = t + 15
        if t >= self.next_finale:
            self.finale()
            self.next_finale = t + 30
        due = [q for q in self.queue if q[0] <= t]
        self.queue = [q for q in self.queue if q[0] > t]
        for _, target, pattern in due:
            self.launch(target, pattern)

        alive = []
        for r in self.rockets:
            r["vy"] += GRAVITY * dt
            r["x"] += r["vx"] * dt
            r["y"] += r["vy"] * dt
            self.parts.add((255, 170, 80), x=[r["x"]], y=[r["y"]], vx=rng.uniform(-3, 3, 1),
                           vy=2.0, life=0.4, drag=2.0, grav=0.2)
            if r["vy"] >= -1:
                self.explode(r)
            else:
                alive.append(r)
        self.rockets = alive

        p = self.parts
        if len(p):
            k = np.exp(-p.drag * dt)
            p.vx *= k
            p.vy *= k
            p.vy += GRAVITY * p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt

            split = (p.max_life - p.life) >= p.split
            sx, sy, sc = p.x[split], p.y[split], p.color[split]
            tr = (p.trail > 0) & (p.life > 0)
            tx, ty, tc = p.x[tr], p.y[tr], p.color[tr] * 0.55
            p.keep((p.life > 0) & ~split & (p.y < ROWS + 2))

            if len(sx):                         # crossette: each spark splits in 4
                a = np.tile(np.arange(4) * math.pi / 2 + math.pi / 4, len(sx))
                p.add(np.repeat(sc, 4, axis=0), x=np.repeat(sx, 4), y=np.repeat(sy, 4),
                      vx=np.cos(a) * 12 * ASPECT, vy=np.sin(a) * 12,
                      life=0.9, drag=1.5, flicker=1)
            if len(tx):                         # embers left behind by trailing sparks
                p.add(tc, x=tx, y=ty, life=0.45, drag=3.0, grav=0.15)

        self.flash *= math.exp(-dt * 5)
        flip = rng.random(len(self.win_lit)) < 0.05 * dt
        self.win_lit ^= flip

    # ---- drawing
    def draw(self, canvas, t):
        glow = (self.flash * 0.15) * self.flash_color
        canvas.bg = self.base_bg + glow * (~self.building)[..., None]

        tw = 0.5 + 0.5 * np.sin(t * 2 + self.star_ph)
        canvas.plot(self.star_x, self.star_y, np.where(tw > 0.85, G["+"], G["."]),
                    np.outer(0.3 + 0.7 * tw, (200, 210, 255)))

        p = self.parts
        if len(p):
            f = np.clip(p.life / p.max_life, 0, 1)
            glyph = FADE_GLYPHS[np.searchsorted([0.1, 0.25, 0.5], f)]
            bright = 0.3 + 0.7 * f
            sparkle = np.where(self.rng.random(len(p)) < 0.55, 1.15, 0.25)
            bright = np.where(p.flicker > 0, bright * sparkle, bright)
            visible = ~self._behind_buildings(p.x, p.y)
            canvas.plot(p.x[visible], p.y[visible], glyph[visible],
                        p.color[visible] * bright[visible, None])

        if self.rockets:
            rx = np.array([r["x"] for r in self.rockets])
            ry = np.array([r["y"] for r in self.rockets])
            vis = ~self._behind_buildings(rx, ry)
            canvas.plot(rx[vis], ry[vis], G["*"], (255, 230, 180))

        lit = self.win_lit
        canvas.plot(self.win_x[lit], self.win_y[lit], G["="], (220, 170, 80))

    def _behind_buildings(self, x, y):
        xi = np.clip(x.astype(int), 0, COLS - 1)
        yi = np.clip(y.astype(int), 0, ROWS - 1)
        return self.building[yi, xi] & (y >= 0) & (y < ROWS)

    def caption(self, t):
        now = datetime.datetime.now()
        if now.year == self.year:
            return f"HAPPY NEW YEAR {self.year}!"
        left = datetime.datetime(self.year, 1, 1) - now
        h, rem = divmod(left.seconds, 3600)
        m, s = divmod(rem, 60)
        return f"HAPPY NEW YEAR {self.year}!\n{left.days}d {h:02d}:{m:02d}:{s:02d} to go"

    def on_key(self, key):
        if key == "f":
            self.finale()

    def on_click(self, col, row):
        if row < ROWS - 28:
            self.launch(target=(col, row))


SCENE = NewYearFireworks
