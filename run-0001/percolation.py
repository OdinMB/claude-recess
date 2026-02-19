"""
Percolation — The Geometry of Connectivity

Drop sites randomly on a lattice. Each site is "open" with probability p.
Two adjacent open sites are connected. As p increases from 0 to 1, something
remarkable happens: at a critical probability p_c, a giant connected cluster
suddenly appears that spans the entire lattice.

Below p_c: only small, isolated clusters. No path from top to bottom.
Above p_c: one giant cluster connects everything. A path always exists.
AT p_c: fractal clusters of all sizes. Power-law distribution. No
characteristic scale. The critical point is the boundary between
disconnection and connection — and it's where all the complexity lives.

For site percolation on a square lattice: p_c ≈ 0.592746

This connects to the spatial Prisoner's Dilemma directly: whether cooperators
can form a spanning cluster determines whether cooperation survives. The
percolation threshold IS the critical temptation parameter. Below it,
cooperator clusters percolate and cooperation is sustainable. Above it,
cooperation fragments and collapses.

And the percolation transition is sharp — not gradual. There's no "halfway
connected." The system goes from disconnected to connected at a single point.
Like a phase transition in physics. Like cooperation collapsing in the
spatial PD.

Usage:
  python3 percolation.py             # Full demo
  python3 percolation.py critical    # Visualize at p_c
  python3 percolation.py sweep       # Sweep p, measure spanning probability
  python3 percolation.py clusters    # Cluster size distribution at p_c
"""

import random
import sys
import time
import math
from collections import deque


# ═══════════════════════════════════════════════════════════════
#  Union-Find for efficient cluster detection
# ═══════════════════════════════════════════════════════════════

class UnionFind:
    """Weighted quick-union with path compression."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def cluster_size(self, x):
        return self.size[self.find(x)]


# ═══════════════════════════════════════════════════════════════
#  Percolation model
# ═══════════════════════════════════════════════════════════════

def make_lattice(w, h, p):
    """Generate random lattice. Each site open with probability p."""
    return [[random.random() < p for _ in range(w)] for _ in range(h)]


def find_clusters(grid, w, h):
    """Find all connected clusters using union-find. Returns (uf, labels).
    labels[y][x] = cluster label for open sites, -1 for closed sites."""
    uf = UnionFind(w * h)
    labels = [[-1] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            if not grid[y][x]:
                continue
            idx = y * w + x
            labels[y][x] = idx
            # Connect to open neighbors (left and up only — symmetry handles rest)
            if x > 0 and grid[y][x - 1]:
                uf.union(idx, y * w + (x - 1))
            if y > 0 and grid[y - 1][x]:
                uf.union(idx, (y - 1) * w + x)

    return uf, labels


def spanning_cluster(grid, w, h, uf):
    """Check if any cluster spans from top to bottom."""
    top_roots = set()
    for x in range(w):
        if grid[0][x]:
            top_roots.add(uf.find(0 * w + x))

    for x in range(w):
        if grid[h - 1][x]:
            if uf.find((h - 1) * w + x) in top_roots:
                return True
    return False


def spanning_roots(grid, w, h, uf):
    """Return set of root IDs for clusters that span top to bottom."""
    top_roots = set()
    for x in range(w):
        if grid[0][x]:
            top_roots.add(uf.find(0 * w + x))

    bot_roots = set()
    for x in range(w):
        if grid[h - 1][x]:
            bot_roots.add(uf.find((h - 1) * w + x))

    return top_roots & bot_roots


def cluster_size_distribution(uf, grid, w, h):
    """Return dict mapping cluster_size -> count."""
    roots = {}
    for y in range(h):
        for x in range(w):
            if grid[y][x]:
                r = uf.find(y * w + x)
                roots[r] = uf.cluster_size(r)

    dist = {}
    seen = set()
    for r, s in roots.items():
        if r not in seen:
            seen.add(r)
            dist[s] = dist.get(s, 0) + 1
    return dist


# ═══════════════════════════════════════════════════════════════
#  Rendering
# ═══════════════════════════════════════════════════════════════

# Color palette for clusters (256-color)
CLUSTER_COLORS = [
    33, 160, 40, 178, 129, 202, 51, 196, 82, 214,
    27, 167, 34, 172, 93, 208, 45, 190, 76, 220,
]
SPANNING_COLOR = 226  # Bright yellow for spanning cluster
CLOSED_COLOR = 236    # Dark gray for closed sites


def render_grid(grid, w, h, uf, span_roots, p, title=""):
    """Render the lattice with colored clusters using half-blocks."""
    buf = []
    buf.append("\033[H")
    buf.append(f"  \033[1m{title}\033[0m" if title else "")
    buf.append(f"  p = {p:.4f}  │  {w}×{h} lattice  │  "
               f"{'SPANNING' if span_roots else 'no spanning cluster'}")
    buf.append("")

    # Assign colors to cluster roots
    root_color = {}
    color_idx = 0
    for y in range(h):
        for x in range(w):
            if grid[y][x]:
                r = uf.find(y * w + x)
                if r not in root_color:
                    if r in span_roots:
                        root_color[r] = SPANNING_COLOR
                    else:
                        root_color[r] = CLUSTER_COLORS[color_idx % len(CLUSTER_COLORS)]
                        color_idx += 1

    def cell_color(y, x):
        if not grid[y][x]:
            return CLOSED_COLOR
        return root_color.get(uf.find(y * w + x), 250)

    for ry in range(0, h - 1, 2):
        parts = ["  "]
        for x in range(min(w, 120)):
            fg = cell_color(ry, x)
            bg = cell_color(ry + 1, x)
            parts.append(f"\033[38;5;{fg};48;5;{bg}m▀")
        parts.append("\033[0m")
        buf.append("".join(parts))

    if h % 2 == 1:
        parts = ["  "]
        for x in range(min(w, 120)):
            fg = cell_color(h - 1, x)
            parts.append(f"\033[38;5;{fg}m▀")
        parts.append("\033[0m")
        buf.append("".join(parts))

    sys.stdout.write("\n".join(buf) + "\n")
    sys.stdout.flush()


# ═══════════════════════════════════════════════════════════════
#  Braille plotting
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_MAP = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


def braille_plot(points, char_w, char_h, x_range, y_range):
    """Render scatter/line plot using braille."""
    dot_w = char_w * 2
    dot_h = char_h * 4
    canvas = [[0] * char_w for _ in range(char_h)]

    x_min, x_max = x_range
    y_min, y_max = y_range
    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1

    for px, py in points:
        dx = int((px - x_min) / x_span * (dot_w - 1))
        dy = int((1.0 - (py - y_min) / y_span) * (dot_h - 1))
        if 0 <= dx < dot_w and 0 <= dy < dot_h:
            cx, cy = dx // 2, dy // 4
            bx, by = dx % 2, dy % 4
            canvas[cy][cx] |= BRAILLE_MAP[(bx, by)]

    return ["".join(chr(BRAILLE_BASE + cell) for cell in row) for row in canvas]


def braille_line_plot(data, char_w, char_h, x_range, y_range):
    """Plot data as a connected line using braille, filling between points."""
    points = []
    for i in range(len(data) - 1):
        x0, y0 = data[i]
        x1, y1 = data[i + 1]
        # Interpolate
        n_steps = max(2, int(abs(x1 - x0) / ((x_range[1] - x_range[0]) / (char_w * 2)) * 2))
        for j in range(n_steps + 1):
            t = j / n_steps
            points.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    if data:
        points.append(data[-1])
    return braille_plot(points, char_w, char_h, x_range, y_range)


# ═══════════════════════════════════════════════════════════════
#  Demonstrations
# ═══════════════════════════════════════════════════════════════

def demo_critical(w=100, h=80):
    """Visualize lattice at the critical point."""
    p_c = 0.592746
    print("\033[2J\033[H")
    print(f"  \033[1m── AT THE CRITICAL POINT ──\033[0m  p = {p_c}")
    print(f"  Site percolation on a {w}×{h} square lattice")
    print()
    print("  At p_c ≈ 0.5927, clusters of all sizes coexist.")
    print("  The spanning cluster (yellow) is fractal — full of holes,")
    print("  with a jagged, self-similar boundary.")
    print()
    time.sleep(1.5)
    print("\033[2J")

    # Generate until we get a spanning cluster (usually happens at p_c)
    for attempt in range(20):
        grid = make_lattice(w, h, p_c)
        uf, labels = find_clusters(grid, w, h)
        sr = spanning_roots(grid, w, h, uf)
        if sr:
            render_grid(grid, w, h, uf, sr, p_c, "Percolation at p_c")
            # Stats
            largest = max(uf.cluster_size(r) for r in sr)
            open_sites = sum(sum(row) for row in grid)
            print(f"\n  Open sites: {open_sites}/{w * h} ({100 * open_sites / (w * h):.1f}%)")
            print(f"  Spanning cluster size: {largest} ({100 * largest / open_sites:.1f}% of open sites)")
            break
    else:
        print("  (No spanning cluster found in 20 attempts — try again)")

    time.sleep(1)


def demo_transition(w=100, h=80):
    """Animate the percolation transition by sweeping p."""
    print("\033[2J\033[H")
    print(f"  \033[1m── PERCOLATION TRANSITION ──\033[0m")
    print(f"  Sweeping p from 0.3 to 0.8. Watch for the spanning cluster (yellow).")
    print()
    time.sleep(1.5)
    print("\033[2J")

    random.seed(42)
    # Pre-generate random values for each site
    site_vals = [[random.random() for _ in range(w)] for _ in range(h)]

    for p_i in range(30, 81, 2):
        p = p_i / 100.0
        grid = [[site_vals[y][x] < p for x in range(w)] for y in range(h)]
        uf, labels = find_clusters(grid, w, h)
        sr = spanning_roots(grid, w, h, uf)
        render_grid(grid, w, h, uf, sr, p, "Percolation Transition")

        if sr:
            largest = max(uf.cluster_size(r) for r in sr)
            print(f"  \033[1;33mSPANNING\033[0m — largest cluster: {largest} sites")
        else:
            print(f"  No spanning cluster")

        time.sleep(0.15)

    time.sleep(1)


def demo_sweep(w=60, h=60, n_trials=50, n_points=80):
    """Sweep p and measure spanning probability."""
    print("\033[2J\033[H")
    print(f"  \033[1m── SPANNING PROBABILITY vs p ──\033[0m")
    print(f"  For each p, running {n_trials} trials on a {w}×{h} lattice.")
    print(f"  Measuring fraction of trials where a spanning cluster exists.")
    print()

    p_min, p_max = 0.35, 0.85
    data = []

    for i in range(n_points):
        p = p_min + (p_max - p_min) * i / (n_points - 1)
        spans = 0
        for trial in range(n_trials):
            grid = make_lattice(w, h, p)
            uf, _ = find_clusters(grid, w, h)
            if spanning_cluster(grid, w, h, uf):
                spans += 1
        frac = spans / n_trials
        data.append((p, frac))

        filled = int(60 * (i + 1) / n_points)
        bar = "█" * filled + "░" * (60 - filled)
        sys.stdout.write(f"\r  [{bar}] p={p:.3f} spans={frac*100:5.1f}%")
        sys.stdout.flush()

    print("\n")

    # Plot
    pw, ph = 70, 18
    lines = braille_line_plot(data, pw, ph, (p_min, p_max), (0.0, 1.0))

    for i, line in enumerate(lines):
        if i == 0:
            label = "100%"
        elif i == ph // 4:
            label = " 75%"
        elif i == ph // 2:
            label = " 50%"
        elif i == 3 * ph // 4:
            label = " 25%"
        elif i == ph - 1:
            label = "  0%"
        else:
            label = "    "
        print(f"  {label} │{line}")

    print(f"       └{'─' * pw}")
    print(f"        {p_min:.2f}" + " " * (pw - 8) + f"{p_max:.2f}")
    print(f"        {'occupation probability p →':^{pw}}")
    print()

    # Find p_c estimate (where spanning probability crosses 50%)
    for j in range(len(data) - 1):
        if data[j][1] < 0.5 <= data[j + 1][1]:
            # Linear interpolation
            p0, f0 = data[j]
            p1, f1 = data[j + 1]
            p_c_est = p0 + (0.5 - f0) / (f1 - f0) * (p1 - p0)
            print(f"  Estimated p_c ≈ {p_c_est:.4f}  (true value: 0.592746...)")
            break

    print()
    print("  The transition sharpens as lattice size → ∞.")
    print("  In the thermodynamic limit, the spanning probability is a")
    print("  step function: 0 for p < p_c, 1 for p > p_c.")
    print("  This is a second-order phase transition.")
    print()
    time.sleep(1)
    return data


def demo_cluster_sizes(w=100, h=100, n_trials=20):
    """Measure cluster size distribution at p_c."""
    print("\033[2J\033[H")
    print(f"  \033[1m── CLUSTER SIZE DISTRIBUTION AT p_c ──\033[0m")
    print(f"  Generating {n_trials} lattices at p_c ≈ 0.5927")
    print(f"  Cluster sizes should follow a power law: n(s) ~ s^(-τ)")
    print(f"  with τ ≈ 187/91 ≈ 2.055 for 2D percolation")
    print()

    p_c = 0.592746
    all_sizes = {}

    for trial in range(n_trials):
        grid = make_lattice(w, h, p_c)
        uf, _ = find_clusters(grid, w, h)

        # Exclude spanning cluster from distribution
        sr = spanning_roots(grid, w, h, uf)
        dist = cluster_size_distribution(uf, grid, w, h)
        for size, count in dist.items():
            all_sizes[size] = all_sizes.get(size, 0) + count

        sys.stdout.write(f"\r  Trial {trial + 1}/{n_trials}")
        sys.stdout.flush()

    print("\n")

    # Log-log plot
    sizes = sorted(all_sizes.keys())
    if not sizes:
        print("  No clusters found.")
        return

    log_points = []
    for s in sizes:
        if s > 0 and all_sizes[s] > 0:
            log_points.append((math.log10(s), math.log10(all_sizes[s])))

    if len(log_points) < 2:
        print("  Not enough data for log-log plot.")
        return

    x_min = min(p[0] for p in log_points)
    x_max = max(p[0] for p in log_points)
    y_min = min(p[1] for p in log_points)
    y_max = max(p[1] for p in log_points)

    pw, ph = 70, 16
    lines = braille_plot(log_points, pw, ph, (x_min, x_max), (y_min, y_max))

    print("  log₁₀(count)")
    for i, line in enumerate(lines):
        if i == 0:
            label = f"{y_max:.1f}"
        elif i == ph - 1:
            label = f"{y_min:.1f}"
        else:
            label = "    "
        print(f"  {label:>4s} │{line}")

    print(f"       └{'─' * pw}")
    print(f"       {x_min:.1f}" + " " * (pw - 8) + f"{x_max:.1f}")
    print(f"        {'log₁₀(cluster size) →':^{pw}}")
    print()

    # Estimate power law exponent via linear regression on log-log data
    if len(log_points) >= 3:
        # Use middle portion to avoid finite-size effects
        mid = log_points[1:-1] if len(log_points) > 4 else log_points
        n = len(mid)
        sx = sum(p[0] for p in mid)
        sy = sum(p[1] for p in mid)
        sxx = sum(p[0] ** 2 for p in mid)
        sxy = sum(p[0] * p[1] for p in mid)
        denom = n * sxx - sx * sx
        if abs(denom) > 1e-10:
            slope = (n * sxy - sx * sy) / denom
            print(f"  Estimated power law exponent: τ ≈ {-slope:.3f}")
            print(f"  Theoretical value: τ = 187/91 ≈ 2.055")

    print()
    print("  A straight line on a log-log plot means a power law.")
    print("  Power laws mean no characteristic scale — clusters of all")
    print("  sizes exist, just like avalanches in the sandpile model.")
    print("  This is the hallmark of criticality.")
    print()
    time.sleep(1)


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "full"

    if mode == "full":
        print("\033[2J\033[H")
        print()
        print("  ═══════════════════════════════════════════════════")
        print("  \033[1m  PERCOLATION\033[0m")
        print("  \033[1m  The Geometry of Connectivity\033[0m")
        print("  ═══════════════════════════════════════════════════")
        print()
        print("  Open each site on a grid with probability p.")
        print("  Adjacent open sites are connected.")
        print("  Does a connected path exist from top to bottom?")
        print()
        print("  Below p_c ≈ 0.593: isolated islands. No connection.")
        print("  Above p_c: a giant cluster spans the whole system.")
        print("  The transition is sharp — a phase transition.")
        print()
        time.sleep(2.5)

        demo_transition()
        demo_critical()
        demo_sweep()
        demo_cluster_sizes()

        print("  ═══════════════════════════════════════════════════")
        print()
        print("  Percolation is the geometry of the boundary theme.")
        print()
        print("  The percolation threshold p_c is a phase transition:")
        print("  below it, the system is fragmented; above it, connected.")
        print("  AT p_c, the largest cluster is fractal — full of holes")
        print("  at every scale, with a boundary that's infinitely jagged.")
        print()
        print("  Cluster sizes at p_c follow a power law, just like")
        print("  avalanches in the sandpile. Same signature of criticality.")
        print("  Same universality class. Same reason: the system is at")
        print("  the boundary between two qualitatively different states.")
        print()
        print("  And the connection to the Prisoner's Dilemma is direct:")
        print("  whether cooperators can survive depends on whether their")
        print("  clusters percolate. The temptation parameter b maps to")
        print("  the occupation probability p. The collapse of cooperation")
        print("  IS a percolation transition.")
        print()

    elif mode == "critical":
        demo_critical()

    elif mode == "sweep":
        demo_sweep()

    elif mode == "clusters":
        demo_cluster_sizes()

    elif mode == "transition":
        demo_transition()

    else:
        print(f"Unknown mode: {mode}")
        print("Modes: critical, sweep, clusters, transition")


if __name__ == "__main__":
    main()
