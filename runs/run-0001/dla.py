"""
Diffusion-Limited Aggregation — fractal growth from random walks.

Start with a single seed particle at the center. Release random walkers
from far away. Each walker performs a random walk until it touches the
existing cluster, at which point it sticks permanently. Repeat.

The result is a fractal tree — branching, dendritic, and beautiful.
The fractal dimension is approximately 1.71 in 2D.

WHY it's fractal: screening. The outer tips of branches are more likely
to intercept incoming walkers than inner regions. So tips grow faster
than valleys, creating a positive feedback loop that amplifies any
perturbation. This is the Mullins-Sekerka instability — the same
mechanism that creates snowflake arms, lightning bolts, and river
networks.

WHY it connects to the sandpile: both are growth processes at a critical
boundary. The sandpile grows toward criticality from below (adding grains
until avalanches span all scales). DLA grows a fractal boundary that is
always critical — every point on the boundary is at the edge between
filled and empty.

Usage:
    python3 dla.py                    # Grow a DLA cluster
    python3 dla.py N                  # Grow N particles (default 3000)
    python3 dla.py N seed             # With specific random seed
"""

import sys
import os
import random
import math


# --- Braille canvas ---

DOT_BITS = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}


class BrailleCanvas:
    def __init__(self, char_width, char_height):
        self.cw = char_width
        self.ch = char_height
        self.dot_w = char_width * 2
        self.dot_h = char_height * 4
        self.grid = [[0] * char_width for _ in range(char_height)]

    def set_dot(self, x, y):
        if 0 <= x < self.dot_w and 0 <= y < self.dot_h:
            cx = x // 2
            cy = y // 4
            dx = x % 2
            dy = y % 4
            self.grid[cy][cx] |= DOT_BITS[(dx, dy)]

    def render(self):
        lines = []
        for row in self.grid:
            lines.append(''.join(chr(0x2800 + bits) for bits in row))
        return '\n'.join(lines)


# --- DLA ---

class DLACluster:
    """Diffusion-limited aggregation cluster."""

    def __init__(self, size=301):
        self.size = size
        self.center = size // 2
        self.grid = set()  # set of (x, y) occupied cells
        self.order = []    # order in which particles were added
        self.max_radius = 0

        # Seed particle
        self.grid.add((self.center, self.center))
        self.order.append((self.center, self.center))

    def _neighbors(self, x, y):
        """4-connected neighbors."""
        return [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]

    def _touches_cluster(self, x, y):
        """Check if position is adjacent to the cluster."""
        for nx, ny in self._neighbors(x, y):
            if (nx, ny) in self.grid:
                return True
        return False

    def _launch_radius(self):
        """Radius from which to launch walkers."""
        return self.max_radius + 10

    def _kill_radius(self):
        """Radius at which to kill walkers that wandered too far."""
        return self.max_radius + 50

    def grow_one(self):
        """Grow the cluster by one particle. Return the position."""
        launch_r = self._launch_radius()
        kill_r = self._kill_radius()
        cx, cy = self.center, self.center

        while True:
            # Launch from a random point on a circle
            angle = random.uniform(0, 2 * math.pi)
            x = cx + int(launch_r * math.cos(angle))
            y = cy + int(launch_r * math.sin(angle))

            # Random walk
            while True:
                # Check if we're adjacent to cluster
                if self._touches_cluster(x, y) and (x, y) not in self.grid:
                    self.grid.add((x, y))
                    self.order.append((x, y))
                    dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                    if dist > self.max_radius:
                        self.max_radius = dist
                    return (x, y)

                # Random step
                dx, dy = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
                x += dx
                y += dy

                # Check bounds
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist > kill_r:
                    break  # Kill this walker, launch a new one

                # Optimization: if far from cluster, take big steps
                if dist > launch_r + 5:
                    break  # Too far, restart

    def grow(self, n_particles, callback=None):
        """Grow n particles with optional progress callback."""
        for i in range(n_particles):
            self.grow_one()
            if callback and (i + 1) % 500 == 0:
                callback(i + 1, n_particles, self.max_radius)

    def fractal_dimension(self, n_samples=10):
        """Estimate fractal dimension using box counting."""
        if len(self.grid) < 10:
            return 0

        # Find bounding box
        xs = [p[0] for p in self.grid]
        ys = [p[1] for p in self.grid]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span = max(max_x - min_x, max_y - min_y, 1)

        # Box counting at different scales
        box_sizes = []
        box_counts = []

        for exp in range(1, 8):
            box_size = 2 ** exp
            if box_size > span:
                break

            boxes = set()
            for x, y in self.grid:
                bx = (x - min_x) // box_size
                by = (y - min_y) // box_size
                boxes.add((bx, by))

            box_sizes.append(box_size)
            box_counts.append(len(boxes))

        if len(box_sizes) < 2:
            return 0

        # Linear regression in log-log space
        log_sizes = [math.log(1.0/s) for s in box_sizes]
        log_counts = [math.log(c) for c in box_counts]

        n = len(log_sizes)
        sx = sum(log_sizes)
        sy = sum(log_counts)
        sxy = sum(x*y for x, y in zip(log_sizes, log_counts))
        sxx = sum(x*x for x in log_sizes)

        denom = n * sxx - sx * sx
        if denom == 0:
            return 0

        slope = (n * sxy - sx * sy) / denom
        return slope

    def radius_vs_mass(self):
        """Compute mass (particle count) as a function of radius."""
        cx, cy = self.center, self.center
        radii = []
        for x, y in self.grid:
            r = math.sqrt((x - cx)**2 + (y - cy)**2)
            radii.append(r)
        radii.sort()

        # Sample at logarithmic intervals
        points = []
        r_max = max(radii) if radii else 1
        for i in range(20):
            r = r_max * (i + 1) / 20
            mass = sum(1 for rad in radii if rad <= r)
            if mass > 0:
                points.append((r, mass))
        return points


# --- Rendering ---

def render_cluster(cluster, char_width, char_height):
    """Render DLA cluster into braille."""
    canvas = BrailleCanvas(char_width, char_height)

    if not cluster.grid:
        return canvas.render()

    # Find bounding box
    xs = [p[0] for p in cluster.grid]
    ys = [p[1] for p in cluster.grid]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Add some padding
    pad = 2
    min_x -= pad
    max_x += pad
    min_y -= pad
    max_y += pad

    span_x = max_x - min_x
    span_y = max_y - min_y

    # Map cluster coordinates to canvas coordinates
    for x, y in cluster.grid:
        px = int((x - min_x) / span_x * (canvas.dot_w - 1))
        py = int((y - min_y) / span_y * (canvas.dot_h - 1))
        canvas.set_dot(px, py)

    return canvas.render()


def render_growth_rings(cluster, char_width, char_height, n_rings=5):
    """Render cluster colored by growth order using density."""
    canvas = BrailleCanvas(char_width, char_height)

    if not cluster.order:
        return canvas.render()

    xs = [p[0] for p in cluster.grid]
    ys = [p[1] for p in cluster.grid]
    min_x, max_x = min(xs) - 2, max(xs) + 2
    min_y, max_y = min(ys) - 2, max(ys) + 2
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    # Show only every nth particle to reveal the growth pattern
    step = max(1, len(cluster.order) // (n_rings * 200))
    for i, (x, y) in enumerate(cluster.order):
        if i % step < step // n_rings:  # Show sparse rings
            px = int((x - min_x) / span_x * (canvas.dot_w - 1))
            py = int((y - min_y) / span_y * (canvas.dot_h - 1))
            canvas.set_dot(px, py)

    return canvas.render()


# --- Main ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


def main():
    n_particles = 3000
    seed = None

    args = sys.argv[1:]
    if len(args) >= 1:
        try:
            n_particles = int(args[0])
        except ValueError:
            pass
    if len(args) >= 2:
        try:
            seed = int(args[1])
        except ValueError:
            pass

    if seed is not None:
        random.seed(seed)

    cols, rows = get_terminal_size()
    cw = cols - 4
    ch = max(15, rows - 10)

    print(f"  Diffusion-Limited Aggregation — fractal growth from random walks")
    print(f"  Growing {n_particles} particles...")
    print()

    # Choose grid size based on expected radius
    grid_size = max(201, int(n_particles ** 0.6) * 3)
    cluster = DLACluster(size=grid_size)

    def progress(i, total, max_r):
        pct = 100 * i / total
        print(f"    {i:>5d}/{total} particles  |  radius: {max_r:.0f}  |  {pct:.0f}%")

    cluster.grow(n_particles, callback=progress)

    print()
    print(f"  Cluster ({len(cluster.grid)} particles, max radius {cluster.max_radius:.0f}):")
    print()
    print(render_cluster(cluster, cw, ch))
    print()

    # Fractal dimension
    fd = cluster.fractal_dimension()
    if fd > 0:
        print(f"  Fractal dimension (box counting): {fd:.2f}")
        print(f"    (theoretical DLA in 2D: ≈ 1.71)")
        print()

    # Mass-radius relationship
    points = cluster.radius_vs_mass()
    if len(points) > 2:
        # Fit log(M) vs log(R)
        lr = [math.log(r) for r, m in points if r > 0]
        lm = [math.log(m) for r, m in points if r > 0]
        if len(lr) >= 2:
            n = len(lr)
            sx = sum(lr)
            sy = sum(lm)
            sxy = sum(x*y for x, y in zip(lr, lm))
            sxx = sum(x*x for x in lr)
            denom = n * sxx - sx * sx
            if denom != 0:
                slope = (n * sxy - sx * sy) / denom
                print(f"  Mass-radius exponent: M(R) ~ R^{slope:.2f}")
                print(f"    (should equal fractal dimension ≈ 1.71)")
                print()

    # What makes it interesting
    print(f"  The branching structure emerges from screening: outer tips")
    print(f"  intercept random walkers before they reach inner regions.")
    print(f"  Small perturbations get amplified — the Mullins-Sekerka")
    print(f"  instability. The same mechanism creates snowflakes,")
    print(f"  lightning bolts, and river networks.")


if __name__ == "__main__":
    main()
