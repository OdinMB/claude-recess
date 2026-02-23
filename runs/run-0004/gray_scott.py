"""
Gray-Scott Reaction-Diffusion System
=====================================
Two virtual chemicals U and V interact:
  U + 2V → 3V   (V "eats" U and replicates)
  V → P          (V decays to an inert product)

The PDEs:
  ∂u/∂t = Du·∇²u - u·v² + F·(1-u)
  ∂v/∂t = Dv·∇²v + u·v² - (F+k)·v

Different (F, k) parameters produce dramatically different patterns:
  - Spots, stripes, spirals, moving waves, solitons
"""

import numpy as np
import time
import sys
import os

# --- Parameter Presets ---
PRESETS = {
    "coral":    dict(F=0.0545, k=0.062,  Du=0.2097, Dv=0.105,  name="Coral Growth"),
    "spots":    dict(F=0.035,  k=0.065,  Du=0.2097, Dv=0.105,  name="Spots"),
    "stripes":  dict(F=0.060,  k=0.0630, Du=0.2097, Dv=0.105,  name="Stripes"),
    "mitosis":  dict(F=0.0367, k=0.0649, Du=0.2097, Dv=0.105,  name="Mitosis (dividing spots)"),
    "maze":     dict(F=0.029,  k=0.057,  Du=0.2097, Dv=0.105,  name="Maze"),
    "waves":    dict(F=0.014,  k=0.054,  Du=0.2097, Dv=0.105,  name="Waves"),
}

def laplacian(Z):
    """2D discrete Laplacian with wraparound (toroidal boundary)."""
    return (
        np.roll(Z,  1, axis=0) +
        np.roll(Z, -1, axis=0) +
        np.roll(Z,  1, axis=1) +
        np.roll(Z, -1, axis=1) -
        4 * Z
    )

def step(U, V, Du, Dv, F, k, dt=1.0):
    """Advance one time step using Euler integration."""
    uvv = U * V * V
    dU = Du * laplacian(U) - uvv + F * (1 - U)
    dV = Dv * laplacian(V) + uvv - (F + k) * V
    U += dt * dU
    V += dt * dV
    np.clip(U, 0, 1, out=U)
    np.clip(V, 0, 1, out=V)
    return U, V

def init_grid(rows, cols, seed_count=5, rng=None):
    """Initialize with uniform U=1, V=0, plus random V-seeds."""
    if rng is None:
        rng = np.random.default_rng()
    U = np.ones((rows, cols), dtype=np.float64)
    V = np.zeros((rows, cols), dtype=np.float64)
    for _ in range(seed_count):
        r = rng.integers(10, rows - 10)
        c = rng.integers(10, cols - 10)
        sz = rng.integers(2, 5)
        U[r-sz:r+sz, c-sz:c+sz] = 0.5 + rng.random((2*sz, 2*sz)) * 0.1
        V[r-sz:r+sz, c-sz:c+sz] = 0.25 + rng.random((2*sz, 2*sz)) * 0.1
    return U, V

PALETTE = " ·:;+=xX$&#"

def render_ascii(V, width, height):
    """Map V concentration to ASCII characters."""
    lines = []
    rows, cols = V.shape
    for ry in range(height):
        row = []
        r = int(ry * rows / height)
        for rx in range(width):
            c = int(rx * cols / width)
            v = V[r, c]
            idx = int(v * (len(PALETTE) - 1))
            idx = max(0, min(idx, len(PALETTE) - 1))
            row.append(PALETTE[idx])
        lines.append("".join(row))
    return "\n".join(lines)

def run(preset_name="coral", grid_size=128, display_steps=50,
        total_steps=2000, seed=42):

    p = PRESETS[preset_name]
    print(f"\n  Gray-Scott Reaction-Diffusion: {p['name']}")
    print(f"  F={p['F']}, k={p['k']}, grid={grid_size}×{grid_size}")
    print(f"  Running {total_steps} steps, displaying every {display_steps}...\n")
    time.sleep(1)

    # Terminal size
    term_cols = min(os.get_terminal_size().columns - 4, grid_size)
    term_rows = min(os.get_terminal_size().lines - 6, grid_size // 2)

    rng = np.random.default_rng(seed)
    U, V = init_grid(grid_size, grid_size, seed_count=8, rng=rng)

    start = time.time()
    for step_n in range(1, total_steps + 1):
        U, V = step(U, V, p["Du"], p["Dv"], p["F"], p["k"])

        if step_n % display_steps == 0:
            frame = render_ascii(V, term_cols, term_rows)
            elapsed = time.time() - start
            # Move cursor to top of frame area
            sys.stdout.write(f"\033[{term_rows + 2}A")
            sys.stdout.write(f"  Step {step_n:5d}/{total_steps}  |  "
                           f"V̄={V.mean():.4f}  |  {elapsed:.1f}s elapsed\n")
            sys.stdout.write(frame + "\n\n")
            sys.stdout.flush()

    print(f"\n  Done. Final V̄={V.mean():.4f}, max(V)={V.max():.4f}")
    return U, V

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gray-Scott reaction-diffusion visualizer")
    parser.add_argument("preset", nargs="?", default="coral",
                        choices=list(PRESETS.keys()),
                        help="Pattern preset (default: coral)")
    parser.add_argument("--size", type=int, default=128, help="Grid size (default: 128)")
    parser.add_argument("--steps", type=int, default=3000, help="Total steps (default: 3000)")
    parser.add_argument("--every", type=int, default=50, help="Display every N steps (default: 50)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--list", action="store_true", help="List all presets")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable presets:")
        for k, v in PRESETS.items():
            print(f"  {k:12s}  F={v['F']:.4f}, k={v['k']:.4f}  —  {v['name']}")
        print()
    else:
        run(args.preset, args.size, args.every, args.steps, args.seed)
