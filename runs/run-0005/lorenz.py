"""
Lorenz Attractor - ASCII terminal visualization

The Lorenz attractor: three coupled differential equations that produce
deterministic chaos. A butterfly shape that never quite repeats itself.

    dx/dt = σ(y - x)
    dy/dt = x(ρ - z) - y
    dz/dt = xy - βz

Standard parameters: σ=10, ρ=28, β=8/3
"""

import math
import time
import sys
import os


def lorenz_step(x, y, z, dt=0.01, sigma=10.0, rho=28.0, beta=8/3):
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return x + dx * dt, y + dy * dt, z + dz * dt


def generate_trajectory(steps=50000, skip=1000):
    """Generate points on the attractor, skipping transient behavior."""
    x, y, z = 0.1, 0.0, 0.0
    # Skip transient
    for _ in range(skip):
        x, y, z = lorenz_step(x, y, z)

    points = []
    for _ in range(steps):
        x, y, z = lorenz_step(x, y, z)
        points.append((x, y, z))
    return points


def project_to_2d(points, width=80, height=40):
    """Project 3D points to 2D using x-z plane (the butterfly view)."""
    xs = [p[0] for p in points]
    zs = [p[2] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)

    margin = 2
    def scale_x(v):
        return int((v - min_x) / (max_x - min_x) * (width - 1 - 2*margin)) + margin
    def scale_z(v):
        return int((v - min_z) / (max_z - min_z) * (height - 1 - 2*margin)) + margin

    return [(scale_x(p[0]), scale_z(p[2])) for p in points]


def render(points_2d, width=80, height=40):
    """Render with density-based characters for depth."""
    # Count how many times each cell is visited
    grid = [[0] * width for _ in range(height)]
    for px, py in points_2d:
        if 0 <= px < width and 0 <= py < height:
            grid[py][px] += 1

    # Map density to characters
    chars = ' ·:;+=xX$#@'
    max_density = max(max(row) for row in grid)

    lines = []
    for row in grid:
        line = ''
        for cell in row:
            if cell == 0:
                line += ' '
            else:
                idx = min(len(chars) - 1, int(cell / max_density * (len(chars) - 1)) + 1)
                line += chars[idx]
        lines.append(line)
    return lines


def main():
    try:
        width = min(80, os.get_terminal_size().columns)
        height = min(40, os.get_terminal_size().lines - 6)
    except OSError:
        width, height = 80, 40

    print("Lorenz Attractor  [σ=10, ρ=28, β=8/3]")
    print("Deterministic chaos: the butterfly that never repeats...")
    print()

    points = generate_trajectory(steps=80000)
    projected = project_to_2d(points, width=width, height=height)
    lines = render(projected, width=width, height=height)

    for line in lines:
        print(line)

    print()
    print(f"  {len(points):,} points computed, projected onto x-z plane")
    print(f"  Initial condition: (0.1, 0.0, 0.0)")


if __name__ == '__main__':
    main()
