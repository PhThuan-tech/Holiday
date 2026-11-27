"""Scene base class and the Tkinter window that animates it."""
import time
import tkinter as tk

from .canvas import AsciiCanvas
from .font import CELL_H, CELL_W


class Scene:
    """Subclass this to make a new theme."""

    title = "Holiday ASCII"
    cols, rows = 150, 105
    background = ((6, 10, 24), (6, 10, 24))     # top colour, bottom colour
    caption_color = "#ffd750"
    help_text = ""                               # extra key hints, e.g. "   M mode"

    def setup(self, canvas):
        """Called once with the canvas (paint static backgrounds here)."""
        canvas.set_background(*self.background)

    def reset(self):
        """Called at start and when R is pressed."""

    def update(self, dt, t):
        """Advance the simulation by dt seconds (t = scene time)."""

    def draw(self, canvas, t):
        """Plot this frame onto the (already cleared) canvas."""

    def caption(self, t):
        return ""

    def labels(self, t):
        """Extra text drawn on top: list of (col, row, text, colour, font size)."""
        return []

    def on_key(self, key):
        """Extra keys (lower-case keysym)."""

    def on_click(self, col, row):
        """Mouse click, in cell coordinates."""


def run(scene, fps=30):
    root = tk.Tk()                               # created first so scenes can load images
    canvas = AsciiCanvas(scene.cols, scene.rows)
    scene.setup(canvas)
    scene.reset()

    root.title(scene.title)
    root.resizable(False, False)
    view = tk.Canvas(root, width=canvas.width, height=canvas.height,
                     highlightthickness=0, bg="#000000")
    view.pack()
    image_item = view.create_image(0, 0, anchor="nw")
    caption_item = view.create_text(canvas.width // 2, canvas.height - 14, anchor="s",
                                    justify="center", fill=scene.caption_color,
                                    font=("Consolas", 22, "bold"))
    view.create_text(10, 8, anchor="nw", fill="#5a6480", font=("Consolas", 10),
                     text="SPACE pause   R restart   ESC quit" + scene.help_text)

    state = {"t": 0.0, "paused": False, "last": time.perf_counter(), "photo": None}

    def on_key(event):
        key = event.keysym.lower()
        if key == "space":
            state["paused"] = not state["paused"]
        elif key == "r":
            state["t"] = 0.0
            scene.reset()
        elif key == "escape":
            root.destroy()
        else:
            scene.on_key(key)

    def on_click(event):
        scene.on_click(event.x / CELL_W, event.y / CELL_H)

    root.bind("<Key>", on_key)
    view.bind("<Button-1>", on_click)

    def tick():
        now = time.perf_counter()
        dt = min(now - state["last"], 0.1)
        state["last"] = now
        if not state["paused"]:
            state["t"] += dt
            scene.update(dt, state["t"])

        canvas.clear()
        scene.draw(canvas, state["t"])
        photo = tk.PhotoImage(data=canvas.to_ppm())
        view.itemconfig(image_item, image=photo)
        state["photo"] = photo                       # keep a reference alive
        view.itemconfig(caption_item, text=scene.caption(state["t"]))
        view.delete("label")
        for col, row, text, color, size in scene.labels(state["t"]):
            view.create_text(col * CELL_W, row * CELL_H, text=text, fill=color, justify="center",
                             font=("Segoe UI", size, "bold"), tags="label")
        view.tag_raise(caption_item)

        elapsed_ms = (time.perf_counter() - now) * 1000
        root.after(max(1, int(1000 / fps - elapsed_ms)), tick)

    tick()
    root.mainloop()
