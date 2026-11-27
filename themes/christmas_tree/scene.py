"""Christmas Tree: a rotating 3D tree with garland, blinking baubles,
a golden star, gifts and falling snow."""
import math

import numpy as np

from engine import Scene, G, project

SPIN_SPEED = 0.5                 # rad / second
TILT = 0.25                      # camera looks slightly down
CAM_DIST = 5.0
SCALE = 880.0

TREE_BASE = 0.35                 # height where the foliage starts
TREE_H = 2.3                     # foliage height
TREE_R = 1.1                     # radius at the bottom
TIERS = 5                        # number of foliage layers

SNOW_COLOR = (235, 240, 255)


def tree_radius(h):
    """Foliage radius at relative height h (0 = bottom, 1 = top), in tiers."""
    band = (h * TIERS) % 1.0
    return TREE_R * (1 - h) * (0.45 + 0.55 * (1 - band)) + 0.03


def build_tree(seed=2026):
    """Return the point cloud: positions, colours, glyphs, appear time,
    kind (0 normal, 1 blinking, 2 star) and blink phase."""
    rng = np.random.default_rng(seed)
    pos, col, glyph, appear, kind, phase = [], [], [], [], [], []

    def add(p, c, g, t, k=0, ph=0.0):
        n = len(p)
        pos.append(np.asarray(p, dtype=np.float32))
        col.append(np.broadcast_to(np.asarray(c, dtype=np.float32), (n, 3)))
        glyph.append(np.broadcast_to(np.asarray(g, dtype=np.int16), (n,)))
        appear.append(np.broadcast_to(np.asarray(t, dtype=np.float32), (n,)))
        kind.append(np.full(n, k, dtype=np.int8))
        phase.append(np.broadcast_to(np.asarray(ph, dtype=np.float32), (n,)))

    # Snowy ground
    n = 7000
    r = 1.7 * np.sqrt(rng.random(n))
    a = rng.random(n) * 2 * math.pi
    p = np.stack([r * np.cos(a), rng.random(n) * 0.02, r * np.sin(a)], 1)
    c = np.repeat(rng.uniform(190, 245, (n, 1)), 3, 1) * [0.95, 0.97, 1.0]
    add(p, c, np.where(rng.random(n) < 0.85, G["."], G["*"]), 0.0)

    # Trunk
    n = 700
    a = rng.random(n) * 2 * math.pi
    y = rng.random(n) * (TREE_BASE + 0.05)
    add(np.stack([0.16 * np.cos(a), y, 0.16 * np.sin(a)], 1), (115, 72, 40), G["#"], 0.4)

    # Foliage (mostly on the surface, some inside)
    n = 12000
    h = 1 - np.sqrt(rng.random(n))
    a = rng.random(n) * 2 * math.pi
    frac = np.where(rng.random(n) < 0.8, 1 - rng.random(n) * 0.08, rng.random(n))
    r = tree_radius(h) * frac
    y = TREE_BASE + h * TREE_H - 0.1 * frac ** 2
    c = np.stack([rng.uniform(10, 45, n), rng.uniform(110, 220, n), rng.uniform(20, 60, n)], 1)
    g = rng.choice([G["*"], G["+"], G["x"], G["#"]], n)
    add(np.stack([r * np.cos(a), y, r * np.sin(a)], 1), c, g, 0.8 + h * 2.5)

    # Spiral garland, red / gold, twinkling
    n = 2500
    t = np.linspace(0, 1, n)
    h = 0.03 + t * 0.93
    a = t * 5.5 * 2 * math.pi
    r = tree_radius(h) * 1.04
    p = np.stack([r * np.cos(a), TREE_BASE + h * TREE_H - 0.1, r * np.sin(a)], 1)
    c = np.where(((t * 60).astype(int) % 2 == 0)[:, None], [[230, 30, 40]], [[255, 200, 60]])
    add(p, c, G["="], 3.4 + t * 1.5, k=1, ph=t * 20)

    # Baubles (blinking)
    palette = [(235, 40, 50), (255, 205, 60), (60, 120, 255),
               (255, 110, 200), (255, 140, 30), (170, 80, 255)]
    for i in range(28):
        hb = rng.uniform(0.05, 0.85)
        ab = rng.random() * 2 * math.pi
        rb = tree_radius(hb) * 1.03
        center = np.array([rb * math.cos(ab), TREE_BASE + hb * TREE_H - 0.1, rb * math.sin(ab)])
        d = rng.normal(size=(120, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        add(center + d * 0.055, palette[i % len(palette)], G["@"] if i % 2 else G["o"],
            5.0 + i * 0.06, k=1, ph=rng.random() * 2 * math.pi)

    # Five-pointed star (always faces the viewer)
    n = 900
    a = rng.random(n) * 2 * math.pi
    seg = 2 * math.pi / 5
    tip = np.abs(((a - math.pi / 2) % seg) / seg * 2 - 1)    # 1 at a point, 0 between
    u = np.sqrt(rng.random(n)) * (0.08 + 0.12 * tip)
    top = TREE_BASE + TREE_H + 0.12
    add(np.stack([u * np.cos(a), top + u * np.sin(a), np.zeros(n)], 1),
        (255, 215, 80), G["*"], 6.6, k=2)

    # Gift boxes with ribbons
    box_colors = [(170, 60, 220), (40, 180, 90), (220, 40, 50), (50, 110, 240), (255, 140, 30)]
    for i, bc in enumerate(box_colors):
        ang = i * 2 * math.pi / len(box_colors) + 0.4
        w, hgt = rng.uniform(0.22, 0.32), rng.uniform(0.18, 0.28)
        cx, cz = 1.1 * math.cos(ang), 1.1 * math.sin(ang)
        n = 900
        q = rng.uniform(-1, 1, (n, 3))
        q[np.arange(n), rng.integers(0, 3, n)] = np.where(rng.random(n) < 0.5, -1, 1)
        ribbon = (np.abs(q[:, 0]) < 0.18) | (np.abs(q[:, 2]) < 0.18)
        p = np.stack([cx + q[:, 0] * w / 2, (q[:, 1] + 1) * hgt / 2, cz + q[:, 2] * w / 2], 1)
        add(p, np.where(ribbon[:, None], [[255, 225, 120]], [bc]),
            np.where(ribbon, G["+"], G["#"]), 7.0 + i * 0.15)

    return tuple(np.concatenate(v) for v in (pos, col, glyph, appear, kind, phase))


class ChristmasTree(Scene):
    title = "Christmas Tree"
    caption_color = "#ffd750"

    def __init__(self):
        (self.pos, self.col, self.glyph, self.appear,
         self.kind, self.phase) = build_tree()
        self.billboard = self.kind == 2

    def reset(self):
        rng = np.random.default_rng(7)
        n = 260
        self.snow_x = rng.uniform(0, self.cols, n)
        self.snow_y = rng.uniform(0, self.rows, n)
        self.snow_v = rng.uniform(4, 12, n)
        self.snow_ph = rng.uniform(0, 2 * math.pi, n)
        self.snow_g = np.where(rng.random(n) < 0.7, G["."], G["*"])

    def update(self, dt, t):
        self.snow_y += self.snow_v * dt
        self.snow_x += np.sin(t * 1.5 + self.snow_ph) * 3 * dt
        self.snow_y[self.snow_y >= self.rows] -= self.rows
        self.snow_x %= self.cols

    def draw(self, canvas, t):
        vis = self.appear <= t                       # tree builds up over time
        col, row, depth = project(self.pos[vis], canvas, angle=t * SPIN_SPEED, tilt=TILT,
                                  cam_dist=CAM_DIST, scale=SCALE, center=(0, 1.35, 0),
                                  offset_rows=-4, billboard=self.billboard[vis])
        kind = self.kind[vis]
        shade = np.clip(1.25 - (depth - CAM_DIST) * 0.35, 0.45, 1.1)
        blink = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 4 + self.phase[vis]))
        shade = np.where(kind == 1, shade * blink, shade)
        shade = np.where(kind == 2, 0.85 + 0.15 * math.sin(t * 3), shade)
        canvas.plot(col, row, self.glyph[vis], self.col[vis] * shade[:, None], depth)
        canvas.plot(self.snow_x, self.snow_y, self.snow_g, SNOW_COLOR)

    def caption(self, t):
        return "Merry Christmas!" if t > 7.8 else ""


SCENE = ChristmasTree
