"""Turn a photo into coloured ASCII cells."""
import numpy as np

from .font import CELL_H, CELL_W, G

# glyphs from light coverage to heavy coverage
RAMP = np.array([G["."], G["-"], G["+"], G["o"], G["*"], G["#"], G["@"]], dtype=np.int16)


def _read_pixels(path):
    """RGB pixels (h, w, 3). Uses Pillow when installed (JPG, PNG, ...);
    otherwise Tk, which reads PNG and GIF (a Tk window must already exist)."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((600, 600))
            return np.asarray(img, dtype=np.float32)
    except ImportError:
        import tkinter as tk
        photo = tk.PhotoImage(file=path)
        w, h = photo.width(), photo.height()
        step = max(1, max(w, h) // 300)
        xs, ys = range(0, w, step), range(0, h, step)
        return np.array([[photo.get(x, y) for x in xs] for y in ys], dtype=np.float32)


def image_to_cells(path, max_cols, max_rows, ink=None, paper=0.75):
    """Fit an image into at most max_cols x max_rows cells, keeping its shape.

    Returns (dx, dy, glyph, color): cell offsets from the top-left corner,
    a glyph per cell, and a colour per cell.

    Photo mode (ink=None): brighter cells get denser glyphs and keep their colour.
    Ink mode (ink=(r, g, b)) for drawings on light paper: cells lighter than
    `paper` are dropped, darker cells get denser glyphs drawn in the ink colour."""
    px = _read_pixels(path)
    h, w = px.shape[:2]
    scale = min(max_cols * CELL_W / w, max_rows * CELL_H / h)
    cols = max(1, int(w * scale / CELL_W))
    rows = max(1, int(h * scale / CELL_H))
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, cols + 1).astype(int)
    color = np.array([[px[ys[r]:max(ys[r + 1], ys[r] + 1), xs[c]:max(xs[c + 1], xs[c] + 1)].mean((0, 1))
                       for c in range(cols)] for r in range(rows)], dtype=np.float32)
    lum = ((color @ np.array([0.299, 0.587, 0.114], np.float32)) / 255).ravel()
    dy, dx = np.mgrid[0:rows, 0:cols]
    dx, dy = dx.ravel().astype(np.float32), dy.ravel().astype(np.float32)
    color = color.reshape(-1, 3)
    if ink is None:
        glyph = RAMP[np.clip((lum * len(RAMP)).astype(int), 0, len(RAMP) - 1)]
        return dx, dy, glyph, color
    keep = lum < paper
    darkness = (paper - lum[keep]) / paper
    glyph = RAMP[np.clip((darkness * 1.6 * len(RAMP)).astype(int), 0, len(RAMP) - 1)]
    ink_color = np.broadcast_to(np.asarray(ink, np.float32), (int(keep.sum()), 3))
    return dx[keep], dy[keep], glyph, ink_color.copy()
