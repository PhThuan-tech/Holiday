"""Render a scene straight to an animated GIF, without opening a window.
Needs Pillow (pip install pillow)."""
import os
import tkinter as tk

from .canvas import AsciiCanvas
from .font import CELL_H, CELL_W

_FONTS = {"caption": ["consolab.ttf", "DejaVuSansMono-Bold.ttf"],
          "label": ["segoeuib.ttf", "DejaVuSans-Bold.ttf"]}
_FONT_DIR = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")


def _font(kind, px):
    from PIL import ImageFont
    for name in _FONTS[kind]:
        for path in (name, os.path.join(_FONT_DIR, name)):
            try:
                return ImageFont.truetype(path, px)
            except OSError:
                pass
    return ImageFont.load_default(px)


def _text(draw, x, y, text, font, fill, bottom=False):
    """Centred (multi-line) text at x; centred on y, or ending at y if bottom."""
    left, top, right, low = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    w, h = right - left, low - top
    ty = y - h - top if bottom else y - h / 2 - top
    draw.multiline_text((x - w / 2 - left, ty), text, font=font, fill=fill, align="center")


def record(scene, path, seconds=6.0, start=0.0, fps=15, scale=0.5):
    """Simulate `scene` up to `start`, then save `seconds` of animation to `path`."""
    from PIL import Image, ImageDraw

    root = tk.Tk()                     # some scenes load images through Tk
    root.withdraw()
    try:
        canvas = AsciiCanvas(scene.cols, scene.rows)
        scene.setup(canvas)
        scene.reset()
        t, sim_dt = 0.0, 1 / 30
        while t < start:
            t += sim_dt
            scene.update(sim_dt, t)

        substeps = max(1, round((1 / fps) / sim_dt))
        caption_font = _font("caption", 29)
        label_fonts = {}
        size = (round(canvas.width * scale), round(canvas.height * scale))
        frames = []
        for _ in range(int(seconds * fps)):
            for _ in range(substeps):
                t += 1 / fps / substeps
                scene.update(1 / fps / substeps, t)
            canvas.clear()
            scene.draw(canvas, t)
            raw = canvas.to_ppm().split(b"\n", 1)[1]
            img = Image.frombytes("RGB", (canvas.width, canvas.height), raw)
            draw = ImageDraw.Draw(img)
            for col, row, text, color, pt in scene.labels(t):
                font = label_fonts.setdefault(pt, _font("label", round(pt * 4 / 3)))
                _text(draw, col * CELL_W, row * CELL_H, text, font, color)
            caption = scene.caption(t)
            if caption:
                _text(draw, canvas.width / 2, canvas.height - 14, caption, caption_font,
                      scene.caption_color, bottom=True)
            if scale != 1:
                img = img.resize(size, Image.LANCZOS)
            frames.append(img.quantize(colors=128))

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       duration=round(1000 / fps), loop=0, optimize=True)
    finally:
        root.destroy()
    return os.path.getsize(path)
