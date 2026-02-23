"""
Refined renders for the attractors that need more love:
- Halvorsen: needs better initial conditions and more points
- Thomas: needs far more integration time (it's a slow system)
- Also: a few bonus attractors and alternate views of the best ones
"""

from __future__ import annotations
import math
import numpy as np
from PIL import Image


DELTAS_3D = {}  # not needed, just reusing render infrastructure


def rk4_step(f, state, dt):
    k1 = f(state)
    k2 = f(state + dt/2 * k1)
    k3 = f(state + dt/2 * k2)
    k4 = f(state + dt * k3)
    return state + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)


def integrate(f, initial, dt, n_steps, warmup=20000):
    state = np.array(initial, dtype=np.float64)
    for _ in range(warmup):
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)
    trajectory = np.empty((n_steps, 3), dtype=np.float64)
    for i in range(n_steps):
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)
        trajectory[i] = state
    return trajectory


def project_2d(trajectory, angle_x=0.0, angle_z=0.0):
    cx, sx = math.cos(angle_x), math.sin(angle_x)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    cz, sz = math.cos(angle_z), math.sin(angle_z)
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    rotated = trajectory @ (rot_x @ rot_z).T
    return rotated[:, 0], rotated[:, 1]


def render_density(xs, ys, width=2000, height=2000,
                   color_scheme="white_on_black",
                   gamma=0.35, brightness=1.0) -> Image.Image:
    margin = 0.05
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    x_range = x_max - x_min
    y_range = y_max - y_min
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

    x_bins = np.clip(((xs - x_min) / (x_max - x_min) * width).astype(int), 0, width - 1)
    y_bins = np.clip(((ys - y_min) / (y_max - y_min) * height).astype(int), 0, height - 1)
    density = np.zeros((height, width), dtype=np.float64)
    np.add.at(density, (y_bins, x_bins), 1)

    max_val = density.max()
    if max_val > 0:
        density = density / max_val
    density = np.power(density, gamma) * brightness
    density = np.clip(density, 0, 1)

    if color_scheme == "white_on_black":
        r = (density * 255).astype(np.uint8)
        g = (density * 250).astype(np.uint8)
        b = (density * 245).astype(np.uint8)
    elif color_scheme == "ember":
        r = np.clip(density * 3, 0, 1)
        g = np.clip(density * 3 - 1, 0, 1)
        b = np.clip(density * 3 - 2, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "ice":
        r = np.clip(density * 3 - 2, 0, 1)
        g = np.clip(density * 2 - 0.5, 0, 1)
        b = np.clip(density * 1.5, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "aurora":
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
    elif color_scheme == "violet":
        t = density
        r = np.clip(t * 0.7 + t**2 * 0.3, 0, 1)
        g = np.clip(t * 0.2, 0, 1)
        b = np.clip(t * 1.0, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    elif color_scheme == "mint":
        t = density
        r = np.clip(t * 0.3, 0, 1)
        g = np.clip(t * 1.1, 0, 1)
        b = np.clip(t * 0.6 + t**2 * 0.3, 0, 1)
        r = (r * 255).astype(np.uint8)
        g = (g * 255).astype(np.uint8)
        b = (b * 255).astype(np.uint8)
    else:
        r = g = b = (density * 255).astype(np.uint8)

    img_array = np.stack([r, g, b], axis=-1)
    return Image.fromarray(img_array, "RGB")


# =========================================================================
# Attractor definitions
# =========================================================================

def thomas(state, b=0.208186):
    x, y, z = state
    return np.array([math.sin(y) - b*x, math.sin(z) - b*y, math.sin(x) - b*z])

def halvorsen(state, a=1.89):
    x, y, z = state
    return np.array([
        -a*x - 4*y - 4*z - y**2,
        -a*y - 4*z - 4*x - z**2,
        -a*z - 4*x - 4*y - x**2,
    ])

def lorenz(state, sigma=10.0, rho=28.0, beta=8/3):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])

def sprott_linz_f(state, a=0.5):
    """Sprott-Linz F — a particularly elegant minimal attractor."""
    x, y, z = state
    return np.array([y + z, -x + a*y, x**2 - z])

def nose_hoover(state, a=1.5):
    """Nosé-Hoover thermostat — from molecular dynamics."""
    x, y, z = state
    return np.array([y, -x + y*z, a - y**2])

def bouali(state, a=0.3, s=1.0):
    """Bouali attractor."""
    x, y, z = state
    return np.array([
        x * (4 - y) + a * z,
        -y * (1 - x**2),
        -x * (1.5 - s * z) - 0.05 * z,
    ])

def three_scroll(state, a=32.48, b=45.84, c=1.18, d=0.13, e=0.57, f=14.7):
    """Three-Scroll Unified Chaotic System (TSUCS)."""
    x, y, z = state
    return np.array([
        a * (y - x) + d * x * z,
        b * x - x * z + f * y,
        c * z + x * y - e * x**2,
    ])


def run(name, func, initial, dt, steps, angle_x, angle_z, color, gamma=0.3, res=1800):
    print(f"\n  {name}...")
    print(f"    Integrating {steps:,} steps...", end=" ", flush=True)
    traj = integrate(func, initial, dt, steps)
    print("done")
    print(f"    Projecting & rendering...", end=" ", flush=True)
    xs, ys = project_2d(traj, angle_x, angle_z)
    img = render_density(xs, ys, res, res, color_scheme=color, gamma=gamma)
    filename = f"attractor_{name}.png"
    img.save(filename)
    print(f"done -> {filename}")


if __name__ == "__main__":
    print("Rendering refined attractors...")

    # Thomas — needs WAY more integration time (slow dynamics)
    run("thomas_v2", thomas, [1.0, 0.0, 0.0],
        dt=0.04, steps=10_000_000,
        angle_x=0.55, angle_z=0.35,
        color="gold", gamma=0.25)

    # Thomas — different angle showing threefold symmetry
    run("thomas_symmetric", thomas, [1.0, 0.0, 0.0],
        dt=0.04, steps=10_000_000,
        angle_x=math.atan(1/math.sqrt(2)), angle_z=math.pi/4,
        color="violet", gamma=0.25)

    # Halvorsen — fixed with better initial conditions and more points
    run("halvorsen_v2", halvorsen, [-5.0, 0.0, 0.0],
        dt=0.002, steps=8_000_000,
        angle_x=0.6, angle_z=0.7,
        color="mint", gamma=0.28)

    # Nosé-Hoover — from statistical mechanics
    run("nose_hoover", nose_hoover, [0.1, 0.0, 0.0],
        dt=0.02, steps=8_000_000,
        angle_x=0.0, angle_z=0.0,
        color="aurora", gamma=0.28)

    # Sprott-Linz F
    run("sprott_f", sprott_linz_f, [0.1, 0.1, 0.1],
        dt=0.01, steps=8_000_000,
        angle_x=0.4, angle_z=0.2,
        color="ember", gamma=0.28)

    # Bouali
    run("bouali", bouali, [1.0, 0.1, 0.1],
        dt=0.008, steps=6_000_000,
        angle_x=0.3, angle_z=0.1,
        color="ice", gamma=0.3)

    # Lorenz in a different, more dramatic view angle
    run("lorenz_dramatic", lorenz, [1.0, 1.0, 1.0],
        dt=0.002, steps=8_000_000,
        angle_x=1.2, angle_z=0.4,
        color="ember", gamma=0.28)

    print("\n\nAll refined renders complete.")
