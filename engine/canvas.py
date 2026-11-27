"""A grid of coloured character cells that renders to a PPM image."""
import numpy as np

from .font import BITMAP, CELL_H, CELL_W, G


class AsciiCanvas:
    def __init__(self, cols, rows, background=((6, 10, 24), (6, 10, 24))):
        self.cols, self.rows = cols, rows
        self.width, self.height = cols * CELL_W, rows * CELL_H
        self.set_background(*background)
        self.clear()

    def set_background(self, top, bottom=None):
        """Vertical gradient behind the characters. `self.bg` is (rows, cols, 3)
        and scenes may edit it directly (e.g. to paint a skyline)."""
        bottom = top if bottom is None else bottom
        k = np.linspace(0, 1, self.rows, dtype=np.float32)[:, None]
        rows = (1 - k) * np.asarray(top, np.float32) + k * np.asarray(bottom, np.float32)
        self.bg = np.repeat(rows[:, None, :], self.cols, axis=1)

    def clear(self):
        n = self.cols * self.rows
        self.glyph = np.full(n, G[" "], dtype=np.int16)
        self.color = np.zeros((n, 3), dtype=np.float32)
        self.depth = np.full(n, np.inf, dtype=np.float32)

    def plot(self, x, y, glyph, color, depth=None):
        """Draw characters at cell coordinates (x = column, y = row).

        glyph: one glyph id or an array of ids, color: (r, g, b) or (n, 3).
        With `depth`, a cell keeps only the nearest point (z-buffer).
        Without it, characters are painted over whatever is there, and count
        as background for any 3D points plotted afterwards."""
        x = np.asarray(x, dtype=np.float32).ravel()
        y = np.asarray(y, dtype=np.float32).ravel()
        n = x.size
        if n == 0:
            return
        glyph = np.broadcast_to(np.asarray(glyph, dtype=np.int16), (n,))
        color = np.broadcast_to(np.asarray(color, dtype=np.float32), (n, 3))
        xi = np.floor(x).astype(np.int64)
        yi = np.floor(y).astype(np.int64)
        idx = np.nonzero((xi >= 0) & (xi < self.cols) & (yi >= 0) & (yi < self.rows))[0]
        if idx.size == 0:
            return
        cell = yi[idx] * self.cols + xi[idx]

        if depth is None:            # flat layer: drawn on top, but later 3D points may cover it
            self.glyph[cell] = glyph[idx]
            self.color[cell] = color[idx]
            self.depth[cell] = np.inf
            return

        d = np.broadcast_to(np.asarray(depth, dtype=np.float32), (n,))[idx]
        order = np.lexsort((d, cell))            # by cell, nearest first
        cs = cell[order]
        first = np.ones(cs.size, dtype=bool)
        first[1:] = cs[1:] != cs[:-1]
        win = idx[order][first]
        cells = cs[first]
        dw = d[order][first]
        closer = dw < self.depth[cells]
        win, cells, dw = win[closer], cells[closer], dw[closer]
        self.glyph[cells] = glyph[win]
        self.color[cells] = color[win]
        self.depth[cells] = dw

    def to_ppm(self):
        r, c = self.rows, self.cols
        mask = BITMAP[self.glyph.reshape(r, c)][..., None]       # (r, c, CH, CW, 1)
        colr = self.color.reshape(r, c, 1, 1, 3)
        bg = self.bg.reshape(r, c, 1, 1, 3)
        img = np.where(mask, colr, bg + colr * 0.10)             # faint glow per cell
        img = img.transpose(0, 2, 1, 3, 4).reshape(self.height, self.width, 3)
        img = np.clip(img, 0, 255).astype(np.uint8)
        return b"P6 %d %d 255\n" % (self.width, self.height) + img.tobytes()
