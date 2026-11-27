"""Valentine Heart: a puffy 3D heart that spins and beats, with little
hearts floating up and sparkles twinkling around it."""
import math

import numpy as np

from engine import G, Scene, project

CAM_DIST = 5.0
SPIN_SPEED = 0.8
BEAT_PERIOD = 1.0                 # seconds per heartbeat


def heartbeat(t):
    """Two quick pulses per period, like a real heartbeat (0..1)."""
    ph = t % BEAT_PERIOD
    return math.exp(-((ph - 0.05) / 0.06) ** 2) + 0.6 * math.exp(-((ph - 0.3) / 0.07) ** 2)


def build_heart(seed=14, n=9000):
    rng = np.random.default_rng(seed)
    t = rng.uniform(0, 2 * math.pi, n)
    hx = 16 * np.sin(t) ** 3 / 17
    hy = (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)) / 17
    s = np.sqrt(rng.random(n))                       # spread evenly over the area
    thick = 0.5 * (0.6 + 0.4 * np.hypot(hx, hy))
    z = np.where(rng.random(n) < 0.5, -1, 1) * np.sqrt(1 - s ** 2) * thick
    pos = np.stack([s * hx, s * hy, z], 1).astype(np.float32)
    color = np.stack([rng.uniform(210, 255, n), rng.uniform(20, 60, n),
                      rng.uniform(50, 95, n)], 1).astype(np.float32)
    glyph = rng.choice([G["@"], G["#"], G["*"], G["o"], G["♥"]], n,
                       p=[0.3, 0.25, 0.2, 0.15, 0.1]).astype(np.int16)
    return pos, color, glyph


class ValentineHeart(Scene):
    title = "Valentine Heart"
    background = ((32, 4, 22), (8, 2, 10))
    caption_color = "#ff7ab0"

    def __init__(self):
        self.pos, self.color, self.glyph = build_heart()
        rng = np.random.default_rng(3)
        n = 50
        self.spark_x = rng.uniform(30, self.cols - 30, n)
        self.spark_y = rng.uniform(10, self.rows - 25, n)
        self.spark_ph = rng.uniform(0, 2 * math.pi, n)

    def reset(self):
        rng = self.rng = np.random.default_rng()
        n = 70
        self.fx = rng.uniform(0, self.cols, n)
        self.fy = rng.uniform(0, self.rows, n)
        self.fv = rng.uniform(3, 8, n)
        self.fph = rng.uniform(0, 2 * math.pi, n)
        self.fc = rng.choice(np.array([(255, 120, 170), (255, 70, 110), (255, 170, 210),
                                       (230, 60, 160)], np.float32), n)

    def update(self, dt, t):
        self.fy -= self.fv * dt
        self.fx += np.sin(t + self.fph) * 3 * dt
        gone = self.fy < -2
        self.fy[gone] = self.rows + 2
        self.fx[gone] = self.rng.uniform(0, self.cols, gone.sum())

    def draw(self, canvas, t):
        tw = np.sin(t * 3 + self.spark_ph)
        on = tw > 0.2
        canvas.plot(self.spark_x[on], self.spark_y[on], np.where(tw[on] > 0.8, G["+"], G["."]),
                    np.outer(tw[on], (255, 210, 235)))

        fade = np.clip(self.fy / self.rows * 1.6, 0.15, 1.0)
        canvas.plot(self.fx, self.fy, G["♥"], self.fc * fade[:, None])

        beat = heartbeat(t)
        col, row, depth = project(self.pos * (1 + 0.08 * beat), canvas, angle=t * SPIN_SPEED,
                                  tilt=0.1, cam_dist=CAM_DIST, scale=1300,
                                  center=(0, -0.1, 0), offset_rows=-6)
        shade = np.clip(1.3 - (depth - CAM_DIST) * 0.8, 0.35, 1.2) * (1 + 0.25 * beat)
        canvas.plot(col, row, self.glyph, self.color * shade[:, None], depth)

    def caption(self, t):
        return "Happy Valentine's Day" if t > 1.5 else ""


SCENE = ValentineHeart
