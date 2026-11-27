"""Small geometry helpers that return cell coordinates ready for canvas.plot."""
import math

import numpy as np

from .font import ASPECT, G


def direction_glyph(dx, dy):
    """Pick '-', '|', '/' or '\\' to match a direction on screen."""
    dx = dx / ASPECT
    if abs(dy) < 0.4 * abs(dx):
        return G["-"]
    if abs(dx) < 0.4 * abs(dy):
        return G["|"]
    return G["/"] if dx * dy < 0 else G["\\"]


def line(x0, y0, x1, y1, density=1.5):
    """Points along a straight line plus the glyph that draws it."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * density) + 2
    s = np.linspace(0, 1, n)
    return x0 + s * (x1 - x0), y0 + s * (y1 - y0), direction_glyph(x1 - x0, y1 - y0)


def disc(cx, cy, ry, rx=None):
    """Cells inside an ellipse. `ry` is the radius in rows; by default the
    horizontal radius is scaled so the disc looks round. Returns x, y and
    d (0 at the centre, 1 at the edge)."""
    rx = ry * ASPECT if rx is None else rx
    xs = np.arange(math.floor(cx - rx), math.ceil(cx + rx) + 1) + 0.5
    ys = np.arange(math.floor(cy - ry), math.ceil(cy + ry) + 1) + 0.5
    X, Y = np.meshgrid(xs, ys)
    d = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
    inside = d <= 1
    return X[inside], Y[inside], d[inside]


def rotate(dx, dy, angle):
    """Rotate cell offsets by `angle` as they appear on screen."""
    u = np.asarray(dx, dtype=np.float64) / ASPECT
    v = np.asarray(dy, dtype=np.float64)
    c, s = math.cos(angle), math.sin(angle)
    return (u * c - v * s) * ASPECT, u * s + v * c


def star_outline(points=5, inner=0.42, samples=12):
    """Outline of a star with unit outer radius, top point first.
    Returns u, v (row units, multiply u by ASPECT for cells) and edge index."""
    k = np.arange(points * 2)
    ang = -math.pi / 2 + k * math.pi / points
    rad = np.where(k % 2 == 0, 1.0, inner)
    px, py = rad * np.cos(ang), rad * np.sin(ang)
    s = np.linspace(0, 1, samples, endpoint=False)[None, :]
    u = (px[:, None] * (1 - s) + np.roll(px, -1)[:, None] * s).ravel()
    v = (py[:, None] * (1 - s) + np.roll(py, -1)[:, None] * s).ravel()
    return u, v, np.repeat(k, samples)


def blob(rng, parts, size):
    """Offsets (x, y, d) of a fluffy cloud made of overlapping discs."""
    xs, ys, ds = [], [], []
    for i in range(parts):
        cx = (i - (parts - 1) / 2) * size * 1.3 + rng.uniform(-1, 1)
        cy = rng.uniform(-0.4, 0.2) * size
        x, y, d = disc(cx, cy, size * rng.uniform(0.7, 1.1))
        xs.append(x)
        ys.append(y)
        ds.append(d)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ds)
