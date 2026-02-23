"""
Velocity-Colored Strange Attractors
=====================================

Instead of pure density, we color each point by the speed of the
trajectory at that location. This reveals the dynamics — where the
system moves fast (transitions between lobes) vs. slow (near the
unstable fixed points).

We accumulate both density and average velocity per pixel, then
map velocity to hue and density to brightness.
"""

from __future__ import annotations
import math
import numpy as np
from PIL import Image


def rk4_step(f, state, dt):
    k1 = f(state)
    k2 = f(state + dt/2 * k1)
    k3 = f(state + dt/2 * k2)
    k4 = f(state + dt * k3)
    return state + (dt / 6) * (k1 + 2*k2 + 2*k3 + k4)


def integrate_with_velocity(f, initial, dt, n_steps, warmup=20000):
    """Integrate and return trajectory + velocity magnitude at each point."""
    state = np.array(initial, dtype=np.float64)
    for _ in range(warmup):
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)

    trajectory = np.empty((n_steps, 3), dtype=np.float64)
    velocities = np.empty(n_steps, dtype=np.float64)

    for i in range(n_steps):
        deriv = f(state)
        velocities[i] = np.sqrt(np.sum(deriv**2))
        state = rk4_step(f, state, dt)
        if np.any(np.isnan(state)) or np.any(np.abs(state) > 1e10):
            state = np.array(initial, dtype=np.float64)
        trajectory[i] = state

    return trajectory, velocities


def project_2d(trajectory, angle_x=0.0, angle_z=0.0):
    cx, sx = math.cos(angle_x), math.sin(angle_x)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    cz, sz = math.cos(angle_z), math.sin(angle_z)
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    rotated = trajectory @ (rot_x @ rot_z).T
    return rotated[:, 0], rotated[:, 1]


def render_velocity_colored(xs, ys, velocities, width=2000, height=2000,
                            gamma=0.35, hue_shift=0.0) -> Image.Image:
    """
    Render with velocity mapped to hue.
    Slow = cool (blue/purple), Fast = warm (yellow/red).
    Density maps to brightness.
    """
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

    # Accumulate density and velocity sum
    density = np.zeros((height, width), dtype=np.float64)
    vel_sum = np.zeros((height, width), dtype=np.float64)

    np.add.at(density, (y_bins, x_bins), 1)
    np.add.at(vel_sum, (y_bins, x_bins), velocities)

    # Average velocity per pixel
    mask = density > 0
    avg_vel = np.zeros_like(density)
    avg_vel[mask] = vel_sum[mask] / density[mask]

    # Normalize velocity to [0, 1]
    vel_min = avg_vel[mask].min() if mask.any() else 0
    vel_max = avg_vel[mask].max() if mask.any() else 1
    if vel_max > vel_min:
        avg_vel[mask] = (avg_vel[mask] - vel_min) / (vel_max - vel_min)

    # Normalize density
    max_density = density.max()
    if max_density > 0:
        density = density / max_density
    brightness = np.power(density, gamma)
    brightness = np.clip(brightness, 0, 1)

    # Map velocity to hue: slow=blue(0.65), fast=red(0.0)
    # Using a perceptually pleasing warm-to-cool gradient
    hue = (1.0 - avg_vel) * 0.65 + hue_shift  # blue to red
    hue = hue % 1.0

    # HSV to RGB conversion (vectorized)
    h6 = hue * 6.0
    sector = h6.astype(int) % 6
    frac = h6 - h6.astype(int)

    sat = np.where(mask, 0.85, 0.0)
    val = brightness

    p = val * (1 - sat)
    q = val * (1 - sat * frac)
    t = val * (1 - sat * (1 - frac))

    r = np.zeros_like(val)
    g = np.zeros_like(val)
    b = np.zeros_like(val)

    s0 = sector == 0
    r[s0] = val[s0]; g[s0] = t[s0]; b[s0] = p[s0]
    s1 = sector == 1
    r[s1] = q[s1]; g[s1] = val[s1]; b[s1] = p[s1]
    s2 = sector == 2
    r[s2] = p[s2]; g[s2] = val[s2]; b[s2] = t[s2]
    s3 = sector == 3
    r[s3] = p[s3]; g[s3] = q[s3]; b[s3] = val[s3]
    s4 = sector == 4
    r[s4] = t[s4]; g[s4] = p[s4]; b[s4] = val[s4]
    s5 = sector == 5
    r[s5] = val[s5]; g[s5] = p[s5]; b[s5] = q[s5]

    r_img = (np.clip(r, 0, 1) * 255).astype(np.uint8)
    g_img = (np.clip(g, 0, 1) * 255).astype(np.uint8)
    b_img = (np.clip(b, 0, 1) * 255).astype(np.uint8)

    img_array = np.stack([r_img, g_img, b_img], axis=-1)
    return Image.fromarray(img_array, "RGB")


# Attractor definitions
def lorenz(state, sigma=10.0, rho=28.0, beta=8/3):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])

def rossler(state, a=0.2, b=0.2, c=5.7):
    x, y, z = state
    return np.array([-y - z, x + a*y, b + z*(x - c)])

def aizawa(state, a=0.95, b=0.7, c=0.6, d=3.5, e=0.25, f=0.1):
    x, y, z = state
    return np.array([
        (z - b)*x - d*y,
        d*x + (z - b)*y,
        c + a*z - z**3/3 - (x**2 + y**2)*(1 + e*z) + f*z*x**3,
    ])

def chen(state, a=35.0, b=3.0, c=28.0):
    x, y, z = state
    return np.array([a*(y-x), (c-a)*x - x*z + c*y, x*y - b*z])

def nose_hoover(state, a=1.5):
    x, y, z = state
    return np.array([y, -x + y*z, a - y**2])

def dadras(state, p=3.0, q=2.7, r=1.7, s=2.0, e=9.0):
    x, y, z = state
    return np.array([y - p*x + q*y*z, r*y - x*z + z, s*x*y - e*z])


CONFIGS = [
    ("lorenz_velocity", lorenz, [1.0, 1.0, 1.0], 0.002, 8_000_000, 0.3, 0.0, 0.28, 0.0),
    ("lorenz_velocity_top", lorenz, [1.0, 1.0, 1.0], 0.002, 8_000_000, math.pi/2, 0.0, 0.28, 0.0),
    ("rossler_velocity", rossler, [1.0, 1.0, 0.0], 0.005, 6_000_000, 0.5, 0.2, 0.30, 0.0),
    ("aizawa_velocity", aizawa, [0.1, 0.0, 0.0], 0.005, 6_000_000, 0.4, 0.8, 0.30, 0.15),
    ("chen_velocity", chen, [-0.1, 0.5, -0.6], 0.001, 8_000_000, 0.35, 0.1, 0.28, 0.0),
    ("nose_hoover_velocity", nose_hoover, [0.1, 0.0, 0.0], 0.02, 10_000_000, 0.0, 0.0, 0.25, 0.0),
    ("dadras_velocity", dadras, [1.0, 1.0, 1.0], 0.003, 6_000_000, 0.3, 0.5, 0.28, 0.0),
]


def main():
    res = 1800

    for name, func, init, dt, steps, ax, az, gamma, hue_shift in CONFIGS:
        print(f"\n  {name}...")
        print(f"    Integrating {steps:,} steps...", end=" ", flush=True)
        traj, vels = integrate_with_velocity(func, init, dt, steps)
        print("done")

        print(f"    Projecting & rendering...", end=" ", flush=True)
        xs, ys = project_2d(traj, ax, az)
        img = render_velocity_colored(xs, ys, vels, res, res,
                                      gamma=gamma, hue_shift=hue_shift)
        filename = f"attractor_{name}.png"
        img.save(filename)
        print(f"done -> {filename}")

    print("\n\nAll velocity-colored renders complete.")


if __name__ == "__main__":
    main()
