"""
Strange Attractor Point-Density Renderer
=========================================

Renders strange attractors by integrating millions of points along the
trajectory and accumulating them into a 2D density histogram. The result
looks like a long-exposure photograph of the attractor — bright where the
trajectory spends more time, dark where it rarely visits.

Each attractor is a system of ordinary differential equations. We integrate
using RK4 and project the 3D trajectory onto 2D with configurable camera angles.
"""

from __future__ import annotations
import math
import numpy as np
from PIL import Image


# =========================================================================
# Attractor definitions — each returns (dx, dy, dz) given (x, y, z)
# =========================================================================

def lorenz(state, sigma=10.0, rho=28.0, beta=8/3):
    x, y, z = state
    return np.array([
        sigma * (y - x),
        x * (rho - z) - y,
        x * y - beta * z,
    ])

def rossler(state, a=0.2, b=0.2, c=5.7):
    x, y, z = state
    return np.array([
        -y - z,
        x + a * y,
        b + z * (x - c),
    ])

def aizawa(state, a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1):
    x, y, z = state
    return np.array([
        (z - b) * x - d * y,
        d * x + (z - b) * y,
        c + a * z - z**3 / 3 - (x**2 + y**2) * (1 + e * z) + f * z * x**3,
    ])

def thomas(state, b=0.208186):
    x, y, z = state
    return np.array([
        math.sin(y) - b * x,
        math.sin(z) - b * y,
        math.sin(x) - b * z,
    ])

def halvorsen(state, a=1.89):
    x, y, z = state
    return np.array([
        -a * x - 4 * y - 4 * z - y**2,
        -a * y - 4 * z - 4 * x - z**2,
        -a * z - 4 * x - 4 * y - x**2,
    ])

def dadras(state, p=3.0, q=2.7, r=1.7, s=2.0, e=9.0):
    x, y, z = state
    return np.array([
        y - p * x + q * y * z,
        r * y - x * z + z,
        s * x * y - e * z,
    ])

def chen(state, a=35.0, b=3.0, c=28.0):
    x, y, z = state
    return np.array([
        a * (y - x),
        (c - a) * x - x * z + c * y,
        x * y - b * z,
    ])

def sprott_b(state):
    x, y, z = state
    return np.array([
        y * z,
        x - y,
        1 - x * y,
    ])

def four_wing(state, a=0.2, b=0.01, c=-0.4):
    x, y, z = state
    return np.array([
        a * x + y * z,
        b * x + c * y - x * z,
        -z - x * y,
    ])


# =========================================================================
# Integration and rendering
# =========================================================================

def rk4_step(f, state, dt):
    """Single RK4 integration step."""
    k1 = f(state)
    k2 = f(state + dt/2 * k1)
    k3 = f(state + dt/2 * k2)
    k4 = f(state + dt * k3)
    return state + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)


def integrate(f, initial, dt, n_steps, warmup=10000):
    """Integrate the system, returning all trajectory points after warmup."""
    state = np.array(initial, dtype=np.float64)

    # Warmup — let transients die out
    for _ in range(warmup):
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)

    # Collect trajectory
    trajectory = np.empty((n_steps, 3), dtype=np.float64)
    for i in range(n_steps):
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)
        trajectory[i] = state

    return trajectory


def project_2d(trajectory, angle_x=0.0, angle_z=0.0):
    """Project 3D trajectory to 2D using rotation."""
    # Rotate around X axis
    cx, sx = math.cos(angle_x), math.sin(angle_x)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])

    # Rotate around Z axis
    cz, sz = math.cos(angle_z), math.sin(angle_z)
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])

    rotated = trajectory @ (rot_x @ rot_z).T
    return rotated[:, 0], rotated[:, 1]


def render_density(xs, ys, width=2000, height=2000,
                   color_scheme="white_on_black",
                   gamma=0.35, brightness=1.0) -> Image.Image:
    """
    Render a point-density image.

    Accumulates points into a 2D histogram, applies gamma correction
    for dynamic range, and maps to a color scheme.
    """
    # Compute bounds with a small margin
    margin = 0.05
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    x_range = x_max - x_min
    y_range = y_max - y_min

    # Make aspect ratio square by expanding the smaller axis
    if x_range > y_range:
        diff = x_range - y_range
        y_min -= diff / 2
        y_max += diff / 2
        y_range = x_range
    else:
        diff = y_range - x_range
        x_min -= diff / 2
        x_max += diff / 2
        x_range = y_range

    x_min -= x_range * margin
    x_max += x_range * margin
    y_min -= y_range * margin
    y_max += y_range * margin

    # Bin points into histogram
    x_bins = np.clip(((xs - x_min) / (x_max - x_min) * width).astype(int), 0, width - 1)
    y_bins = np.clip(((ys - y_min) / (y_max - y_min) * height).astype(int), 0, height - 1)

    density = np.zeros((height, width), dtype=np.float64)
    np.add.at(density, (y_bins, x_bins), 1)

    # Normalize and apply gamma
    max_val = density.max()
    if max_val > 0:
        density = density / max_val
    density = np.power(density, gamma) * brightness
    density = np.clip(density, 0, 1)

    # Apply color scheme
    if color_scheme == "white_on_black":
        r = (density * 255).astype(np.uint8)
        g = (density * 250).astype(np.uint8)
        b = (density * 245).astype(np.uint8)
    elif color_scheme == "ember":
        # Black -> dark red -> orange -> yellow -> white
        r = np.clip(density * 3, 0, 1)
        g = np.clip(density * 3 - 1, 0, 1)
        b = np.clip(density * 3 - 2, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "ice":
        # Black -> dark blue -> cyan -> white
        r = np.clip(density * 3 - 2, 0, 1)
        g = np.clip(density * 2 - 0.5, 0, 1)
        b = np.clip(density * 1.5, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "aurora":
        # Black -> deep purple -> green -> cyan -> white
        t = density
        r = np.clip(0.5 * t + 0.5 * t**3, 0, 1)
        g = np.clip(t**0.7 * 0.8, 0, 1)
        b = np.clip(0.3 + 0.7 * t**0.5, 0, 1) * np.clip(t * 5, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "gold":
        t = density
        r = np.clip(t * 1.2, 0, 1)
        g = np.clip(t * 0.85, 0, 1)
        b = np.clip(t * 0.3, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "ocean":
        t = density
        r = np.clip(t * 0.2 + t**3 * 0.8, 0, 1)
        g = np.clip(t * 0.7, 0, 1)
        b = np.clip(0.15 + t * 0.85, 0, 1) * np.clip(t * 4, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    else:
        r = g = b = (density * 255).astype(np.uint8)

    # Compose into image
    img_array = np.stack([r, g, b], axis=-1)
    return Image.fromarray(img_array, "RGB")


# =========================================================================
# Attractor configurations
# =========================================================================

ATTRACTORS = [
    {
        "name": "lorenz",
        "title": "Lorenz Attractor",
        "func": lorenz,
        "initial": [1.0, 1.0, 1.0],
        "dt": 0.002,
        "steps": 5_000_000,
        "angle_x": 0.3,
        "angle_z": 0.0,
        "color": "ember",
        "gamma": 0.3,
    },
    {
        "name": "lorenz_top",
        "title": "Lorenz — Top View",
        "func": lorenz,
        "initial": [1.0, 1.0, 1.0],
        "dt": 0.002,
        "steps": 5_000_000,
        "angle_x": math.pi/2,
        "angle_z": 0.0,
        "color": "white_on_black",
        "gamma": 0.3,
    },
    {
        "name": "rossler",
        "title": "Rössler Attractor",
        "func": rossler,
        "initial": [1.0, 1.0, 0.0],
        "dt": 0.005,
        "steps": 4_000_000,
        "angle_x": 0.5,
        "angle_z": 0.2,
        "color": "aurora",
        "gamma": 0.32,
    },
    {
        "name": "aizawa",
        "title": "Aizawa Attractor",
        "func": aizawa,
        "initial": [0.1, 0.0, 0.0],
        "dt": 0.005,
        "steps": 4_000_000,
        "angle_x": 0.4,
        "angle_z": 0.8,
        "color": "ice",
        "gamma": 0.32,
    },
    {
        "name": "thomas",
        "title": "Thomas Attractor",
        "func": thomas,
        "initial": [1.0, 0.0, 0.0],
        "dt": 0.05,
        "steps": 5_000_000,
        "angle_x": 0.6,
        "angle_z": 0.3,
        "color": "gold",
        "gamma": 0.28,
    },
    {
        "name": "halvorsen",
        "title": "Halvorsen Attractor",
        "func": halvorsen,
        "initial": [-1.48, -1.51, 2.04],
        "dt": 0.003,
        "steps": 5_000_000,
        "angle_x": 0.55,
        "angle_z": 0.75,
        "color": "ocean",
        "gamma": 0.3,
    },
    {
        "name": "dadras",
        "title": "Dadras Attractor",
        "func": dadras,
        "initial": [1.0, 1.0, 1.0],
        "dt": 0.003,
        "steps": 4_000_000,
        "angle_x": 0.3,
        "angle_z": 0.5,
        "color": "aurora",
        "gamma": 0.3,
    },
    {
        "name": "chen",
        "title": "Chen Attractor",
        "func": chen,
        "initial": [-0.1, 0.5, -0.6],
        "dt": 0.001,
        "steps": 5_000_000,
        "angle_x": 0.35,
        "angle_z": 0.1,
        "color": "ember",
        "gamma": 0.3,
    },
]


def main():
    resolution = 1800

    for cfg in ATTRACTORS:
        name = cfg["name"]
        print(f"\n{'='*60}")
        print(f"  {cfg['title']}")
        print(f"  dt={cfg['dt']}, steps={cfg['steps']:,}")
        print(f"{'='*60}")

        print("  Integrating...", end=" ", flush=True)
        traj = integrate(cfg["func"], cfg["initial"], cfg["dt"], cfg["steps"])
        print(f"done ({traj.shape[0]:,} points)")

        print("  Projecting...", end=" ", flush=True)
        xs, ys = project_2d(traj, cfg.get("angle_x", 0), cfg.get("angle_z", 0))
        print("done")

        print("  Rendering...", end=" ", flush=True)
        img = render_density(xs, ys, resolution, resolution,
                             color_scheme=cfg["color"],
                             gamma=cfg.get("gamma", 0.35))
        filename = f"attractor_{name}.png"
        img.save(filename)
        print(f"done -> {filename} ({img.width}x{img.height})")

    print(f"\n\nAll {len(ATTRACTORS)} attractors rendered.")


if __name__ == "__main__":
    main()
