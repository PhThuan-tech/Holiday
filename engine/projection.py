"""Perspective projection of 3D points onto the character grid."""
import math

import numpy as np

from .font import CELL_H, CELL_W


def project(points, canvas, angle=0.0, tilt=0.0, cam_dist=5.0, scale=900.0,
            center=(0.0, 0.0, 0.0), offset_rows=0.0, billboard=None):
    """Rotate `points` (n, 3) around the vertical axis by `angle`, tilt the
    camera down by `tilt`, and return (col, row, depth) arrays.

    Points flagged in `billboard` skip the spin so they always face the viewer."""
    p = np.asarray(points, dtype=np.float32) - np.asarray(center, dtype=np.float32)
    ca, sa = math.cos(angle), math.sin(angle)
    if billboard is not None:
        ca = np.where(billboard, 1.0, ca)
        sa = np.where(billboard, 0.0, sa)
    x = p[:, 0] * ca + p[:, 2] * sa
    z = -p[:, 0] * sa + p[:, 2] * ca
    y = p[:, 1]

    ct, st = math.cos(tilt), math.sin(tilt)
    y2 = y * ct + z * st
    depth = cam_dist - y * st + z * ct
    col = canvas.cols / 2 + x / depth * scale / CELL_W
    row = canvas.rows / 2 + offset_rows - y2 / depth * scale / CELL_H
    return col, row, depth
