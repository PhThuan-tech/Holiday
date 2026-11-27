"""Tiny engine for animated, coloured ASCII-art scenes."""
from .app import Scene, run
from .canvas import AsciiCanvas
from .font import ASPECT, CELL_H, CELL_W, G
from .image import image_to_cells
from .projection import project
from .shapes import blob, direction_glyph, disc, line, rotate, star_outline
from .sprites import Sprite

__all__ = ["Scene", "run", "AsciiCanvas", "G", "CELL_W", "CELL_H", "ASPECT", "project",
           "Sprite", "blob", "direction_glyph", "disc", "line", "rotate", "star_outline",
           "image_to_cells"]
