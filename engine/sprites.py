"""Sprites: little pictures written as ASCII art."""
import numpy as np

from .font import G

_MIRROR = {"/": "\\", "\\": "/", "(": ")", ")": "(", "<": ">", ">": "<"}


class Sprite:
    """Build a sprite from ASCII art.

    `palette` maps a character used in the art to (glyph, colour). A character
    missing from the palette is drawn as itself in white; spaces are see-through.

        bat = Sprite(["\\\\   /", " \\\\@/ "], {"@": ("@", (120, 80, 140))})
        bat.draw(canvas, x, y)
    """

    def __init__(self, art, palette=None):
        palette = palette or {}
        lines = art.strip("\n").split("\n") if isinstance(art, str) else list(art)
        h, w = len(lines), max(len(line) for line in lines)
        dx, dy, glyph, mirror, color = [], [], [], [], []
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == " ":
                    continue
                name, col = palette.get(ch, (ch, (255, 255, 255)))
                dx.append(c - (w - 1) / 2)
                dy.append(r - (h - 1) / 2)
                glyph.append(G[name])
                mirror.append(G[_MIRROR.get(name, name)])
                color.append(col)
        self.dx = np.array(dx, dtype=np.float32)
        self.dy = np.array(dy, dtype=np.float32)
        self.glyph = np.array(glyph, dtype=np.int16)
        self.mirror_glyph = np.array(mirror, dtype=np.int16)
        self.color = np.array(color, dtype=np.float32).reshape(-1, 3)
        self.width, self.height = w, h

    def draw(self, canvas, x, y, brightness=1.0, flip=False):
        dx = -self.dx if flip else self.dx
        glyph = self.mirror_glyph if flip else self.glyph
        canvas.plot(x + dx, y + self.dy, glyph, self.color * brightness)
