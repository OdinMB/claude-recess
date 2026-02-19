"""
Random Walks — Why Drunk Men Find Their Way Home

A random walker takes steps in random directions. In 1D, left or right.
In 2D, up/down/left/right. In 3D, six possible directions. The question:
does the walker ever return to where they started?

Pólya's theorem (1921):
  1D: returns with probability 1     (certain)
  2D: returns with probability 1     (certain)
  3D: returns with probability ~0.34 (usually escapes forever)
  4D: returns with probability ~0.19
  ...
  nD: return probability → 0 as n → ∞

The boundary is at dimension 2. Below it, the walker always returns
(recurrent). Above it, the walker escapes to infinity (transient).
In exactly 2D, the walk is "critically recurrent" — it returns, but
barely. The expected return time is infinite.

This is a phase transition in dimension itself. And the fractal
dimension of a 2D random walk trajectory is exactly 2, filling the
plane with probability 1 over infinite time.

Usage:
    python3 walks.py               # Overview
    python3 walks.py fans          # Fan of 1D walks (√t envelope)
    python3 walks.py territory     # 2D walk visited-site map
    python3 walks.py polya         # Pólya's theorem: return vs dimension
    python3 walks.py passage       # First return time distribution
"""

import sys
import os
import math
import random


# ═══════════════════════════════════════════════════════════════
#  Braille canvas
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_BITS = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


class BrailleCanvas:
    def __init__(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.dw, self.dh = cw * 2, ch * 4
        self.grid = [[0] * cw for _ in range(ch)]

    def set(self, dx, dy):
        if 0 <= dx < self.dw and 0 <= dy < self.dh:
            self.grid[dy // 4][dx // 2] |= BRAILLE_BITS[(dx % 2, dy % 4)]

    def plot(self, x, y, xr, yr):
        dx = int((x - xr[0]) / (xr[1] - xr[0] + 1e-15) * (self.dw - 1))
        dy = int((1 - (y - yr[0]) / (yr[1] - yr[0] + 1e-15)) * (self.dh - 1))
        self.set(dx, dy)

    def render(self):
        return ["".join(chr(BRAILLE_BASE + c) for c in row) for row in self.grid]


class DensityCanvas:
    """Accumulate point density and render with color."""
    def __init__(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.dw, self.dh = cw * 2, ch * 4
        self.density = [[0] * self.dw for _ in range(self.dh)]

    def add(self, dx, dy):
        if 0 <= dx < self.dw and 0 <= dy < self.dh:
            self.density[dy][dx] += 1

    def add_point(self, x, y, xr, yr):
        dx = int((x - xr[0]) / (xr[1] - xr[0] + 1e-15) * (self.dw - 1))
        dy = int((1 - (y - yr[0]) / (yr[1] - yr[0] + 1e-15)) * (self.dh - 1))
        self.add(dx, dy)

    def render_binary(self):
        """Render as braille: any visited dot is set."""
        grid = [[0] * self.cw for _ in range(self.ch)]
        for dy in range(self.dh):
            for dx in range(self.dw):
                if self.density[dy][dx] > 0:
                    cy, cx = dy // 4, dx // 2
                    grid[cy][cx] |= BRAILLE_BITS[(dx % 2, dy % 4)]
        return ["".join(chr(BRAILLE_BASE + c) for c in row) for row in grid]

    def render_color(self):
        """Render with ANSI color based on visit density."""
        # Color palette: dark → bright
        colors = [0, 232, 233, 234, 235, 237, 239, 241, 243, 245,
                  24, 25, 26, 27, 33, 39, 45, 51, 50, 49,
                  48, 47, 46, 82, 118, 154, 190, 226, 220,
                  214, 208, 202, 196, 231]

        max_d = 0
        for row in self.density:
            for v in row:
                if v > max_d:
                    max_d = v

        if max_d == 0:
            return self.render_binary()

        log_max = math.log(max_d + 1)

        lines = []
        for cy in range(self.ch):
            chars = []
            for cx in range(self.cw):
                bits = 0
                max_cell_d = 0
                for bx in range(2):
                    for by in range(4):
                        dx = cx * 2 + bx
                        dy = cy * 4 + by
                        d = self.density[dy][dx]
                        if d > 0:
                            bits |= BRAILLE_BITS[(bx, by)]
                            if d > max_cell_d:
                                max_cell_d = d
                if max_cell_d > 0:
                    level = math.log(max_cell_d + 1) / log_max
                    ci = int(level * (len(colors) - 1))
                    ci = max(0, min(len(colors) - 1, ci))
                    chars.append(f"\033[38;5;{colors[ci]}m{chr(BRAILLE_BASE + bits)}\033[0m")
                else:
                    chars.append(chr(BRAILLE_BASE))
            lines.append("".join(chars))
        return lines


# ═══════════════════════════════════════════════════════════════
#  Terminal size
# ═══════════════════════════════════════════════════════════════

def get_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# ═══════════════════════════════════════════════════════════════
#  Random walk generators
# ═══════════════════════════════════════════════════════════════

def walk_1d(steps):
    """1D random walk. Returns list of positions."""
    pos = 0
    path = [0]
    for _ in range(steps):
        pos += random.choice([-1, 1])
        path.append(pos)
    return path


def walk_2d(steps):
    """2D random walk. Returns list of (x, y)."""
    x, y = 0, 0
    path = [(0, 0)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for _ in range(steps):
        dx, dy = random.choice(directions)
        x += dx
        y += dy
        path.append((x, y))
    return path


def walk_nd(steps, dim):
    """nD random walk. Returns True if walker returns to origin."""
    pos = [0] * dim
    for _ in range(steps):
        axis = random.randint(0, dim - 1)
        pos[axis] += random.choice([-1, 1])
        if all(p == 0 for p in pos):
            return True
    return False


# ═══════════════════════════════════════════════════════════════
#  Fan of 1D walks
# ═══════════════════════════════════════════════════════════════

def fans_mode():
    """Show multiple 1D random walks — the √t envelope."""
    cols, rows = get_size()
    cw = cols - 8
    ch = max(10, rows // 2 - 4)

    n_walks = 50
    n_steps = 2000

    print(f"  {n_walks} independent 1D random walks ({n_steps:,} steps each)")
    print(f"  Horizontal: time   Vertical: position")
    print()

    canvas = BrailleCanvas(cw, ch)

    max_displacement = 0
    walks = []
    for _ in range(n_walks):
        path = walk_1d(n_steps)
        walks.append(path)
        m = max(abs(p) for p in path)
        if m > max_displacement:
            max_displacement = m

    y_range = (-max_displacement, max_displacement)

    for path in walks:
        for t, pos in enumerate(path):
            canvas.plot(t, pos, (0, n_steps), y_range)

    # Also plot the theoretical √t envelope
    for t in range(1, n_steps + 1):
        envelope = 2.0 * math.sqrt(t)
        canvas.plot(t, envelope, (0, n_steps), y_range)
        canvas.plot(t, -envelope, (0, n_steps), y_range)

    lines = canvas.render()
    for i, line in enumerate(lines):
        if i == 0:
            yl = f"+{max_displacement}"
        elif i == len(lines) - 1:
            yl = f"-{max_displacement}"
        elif i == len(lines) // 2:
            yl = "   0"
        else:
            yl = "    "
        print(f"  {yl:>5s} │{line}")

    print(f"  {'':>5s} └{'─' * cw}")
    print(f"  {'':>5s}  0{' ' * (cw - 10)}{n_steps:,} steps")
    print()

    # Statistics
    final_positions = [w[-1] for w in walks]
    rms = math.sqrt(sum(p**2 for p in final_positions) / len(final_positions))
    returns = sum(1 for w in walks if any(w[t] == 0 for t in range(1, len(w))))

    print(f"  RMS displacement at t={n_steps}: {rms:.1f}")
    print(f"  Theoretical (√t):               {math.sqrt(n_steps):.1f}")
    print(f"  Walks that returned to origin:   {returns}/{n_walks}")
    print(f"  Theoretical return probability:  1.0 (always returns, eventually)")
    print()
    print(f"  The envelope curves are ±2√t. Most walks stay within this.")
    print(f"  The walk spreads as √t, not t. It goes nowhere fast.")
    print(f"  And yet it ALWAYS returns — Pólya's theorem guarantees it.")


# ═══════════════════════════════════════════════════════════════
#  2D walk territory
# ═══════════════════════════════════════════════════════════════

def territory_mode():
    """Show the territory covered by a 2D random walk."""
    cols, rows = get_size()
    cw = min(cols - 6, 80)
    ch = max(10, rows // 2 - 4)

    n_steps = 50000

    print(f"  2D random walk: {n_steps:,} steps")
    print(f"  Color = visit density (blue=once → red=many times)")
    print()

    path = walk_2d(n_steps)

    # Compute bounds
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # Make square aspect ratio
    x_range = x_max - x_min
    y_range = y_max - y_min
    max_range = max(x_range, y_range)
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    x_min = cx - max_range / 2 - 1
    x_max = cx + max_range / 2 + 1
    y_min = cy - max_range / 2 - 1
    y_max = cy + max_range / 2 + 1

    canvas = DensityCanvas(cw, ch)

    for x, y in path:
        canvas.add_point(x, y, (x_min, x_max), (y_min, y_max))

    for line in canvas.render_color():
        print(f"    {line}")

    print()

    # Compute territory statistics
    visited = set(path)
    n_visited = len(visited)
    total_cells = int(x_range * y_range) if x_range > 0 and y_range > 0 else 1
    max_dist = max(math.sqrt(x**2 + y**2) for x, y in path)

    # Count returns to origin
    returns = sum(1 for x, y in path if x == 0 and y == 0)

    print(f"  Distinct sites visited: {n_visited:,}")
    print(f"  Maximum distance from origin: {max_dist:.1f}")
    print(f"  Expected max distance (√n): {math.sqrt(n_steps):.1f}")
    print(f"  Returns to origin: {returns}")
    print()
    print(f"  In 2D, the walk is recurrent: it returns to every")
    print(f"  visited site infinitely many times. But the expected")
    print(f"  return time is infinite — it takes a long time to")
    print(f"  wander back.")
    print()
    print(f"  The territory boundary is fractal. The walk visits")
    print(f"  ~n/log(n) distinct sites out of n steps — it revisits")
    print(f"  most sites, but still covers new ground slowly.")


# ═══════════════════════════════════════════════════════════════
#  Pólya's theorem demonstration
# ═══════════════════════════════════════════════════════════════

def polya_mode():
    """Monte Carlo demonstration of Pólya's recurrence theorem."""
    cols, rows = get_size()
    cw = min(cols - 8, 70)
    ch = max(8, rows // 3 - 2)

    n_trials = 1000
    max_steps = 5000

    print(f"  Pólya's Recurrence Theorem")
    print(f"  Does a random walker return to the origin?")
    print(f"  ({n_trials} trials, up to {max_steps:,} steps each)")
    print()

    # Test dimensions 1 through 6
    dims = [1, 2, 3, 4, 5, 6]
    return_probs = []

    for dim in dims:
        returns = 0
        for _ in range(n_trials):
            if walk_nd(max_steps, dim):
                returns += 1
        prob = returns / n_trials
        return_probs.append(prob)

        # Theoretical values
        if dim == 1:
            theory = "1.000"
        elif dim == 2:
            theory = "1.000"
        elif dim == 3:
            theory = "0.340"
        elif dim == 4:
            theory = "0.193"
        elif dim == 5:
            theory = "0.135"
        elif dim == 6:
            theory = "0.105"
        else:
            theory = "?"

        bar_len = int(prob * 50)
        bar = '█' * bar_len + '░' * (50 - bar_len)
        print(f"    {dim}D:  {prob:.3f}  (theory ≈ {theory})  {bar}")

    print()

    # Plot return probability vs step count for each dimension
    print(f"  Return probability vs number of steps allowed:")
    print()

    canvas = BrailleCanvas(cw, ch)
    checkpoints = [50, 100, 200, 500, 1000, 2000, 5000]

    for dim in [1, 2, 3]:
        for max_s in checkpoints:
            returns = sum(1 for _ in range(200) if walk_nd(max_s, dim))
            prob = returns / 200
            canvas.plot(math.log10(max_s), prob, (math.log10(50), math.log10(5000)), (0, 1))

    lines = canvas.render()
    for i, line in enumerate(lines):
        if i == 0:
            yl = " 1.0"
        elif i == len(lines) - 1:
            yl = " 0.0"
        else:
            yl = "    "
        print(f"  {yl} │{line}")

    print(f"       └{'─' * cw}")
    print(f"        50{' ' * (cw - 8)}5000 steps")
    print()
    print(f"  In 1D and 2D, the return probability → 1 as steps → ∞.")
    print(f"  In 3D, it plateaus at ~0.34. The walker escapes forever.")
    print()

    print(f"  ─────────────────────────────────────────────────────")
    print(f"  Why dimension 2?")
    print()
    print(f"  A random walk visits ~n^(d/2) distinct sites in d dimensions.")
    print(f"  The total volume within distance √n is ~(√n)^d = n^(d/2).")
    print(f"  In d ≤ 2: visits grow slower than volume → revisits → recurrent")
    print(f"  In d > 2: visits grow slower than volume → escapes → transient")
    print(f"  At d = 2: they grow at the same rate → critical, barely recurrent")
    print(f"  The boundary between returning and escaping is exactly d = 2.")


# ═══════════════════════════════════════════════════════════════
#  First passage time distribution
# ═══════════════════════════════════════════════════════════════

def passage_mode():
    """Distribution of first return times in 1D and 2D."""
    n_trials = 10000
    max_steps = 50000

    print(f"  First Return Time Distribution ({n_trials:,} trials)")
    print(f"  How long until the walker returns to the origin?")
    print()

    for dim, label in [(1, "1D"), (2, "2D")]:
        return_times = []

        for _ in range(n_trials):
            if dim == 1:
                pos = 0
                for t in range(1, max_steps + 1):
                    pos += random.choice([-1, 1])
                    if pos == 0:
                        return_times.append(t)
                        break
            else:
                x, y = 0, 0
                dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                for t in range(1, max_steps + 1):
                    dx, dy = random.choice(dirs)
                    x += dx
                    y += dy
                    if x == 0 and y == 0:
                        return_times.append(t)
                        break

        returned = len(return_times)
        print(f"  {label}: {returned}/{n_trials} returned within {max_steps:,} steps")

        if return_times:
            avg = sum(return_times) / len(return_times)
            median_idx = len(return_times) // 2
            sorted_times = sorted(return_times)
            median = sorted_times[median_idx]
            max_time = max(return_times)

            print(f"    Mean return time: {avg:.1f}")
            print(f"    Median: {median}")
            print(f"    Max: {max_time:,}")
            print()

            # Histogram (log-scale bins)
            n_bins = 25
            log_min = 0
            log_max = math.log10(max_time + 1)
            bins = [0] * n_bins

            for t in return_times:
                b = int((math.log10(t + 1) - log_min) / (log_max - log_min + 1e-15) * n_bins)
                b = min(b, n_bins - 1)
                bins[b] += 1

            max_count = max(bins)
            for i in range(n_bins):
                t_lo = int(10 ** (log_min + (log_max - log_min) * i / n_bins))
                t_hi = int(10 ** (log_min + (log_max - log_min) * (i + 1) / n_bins))
                bar = '█' * int(40 * bins[i] / max_count) if max_count > 0 else ''
                if bins[i] > 0:
                    print(f"    {t_lo:>6,}-{t_hi:<6,}: {bins[i]:>5d} {bar}")

            print()

    print(f"  The return time distribution has a heavy tail.")
    print(f"  In 1D: P(return at step 2n) ~ 1/(n√n) — power law!")
    print(f"  The expected return time in 1D is infinite.")
    print(f"  In 2D: even heavier tail. Returns are certain but slow.")
    print(f"  Most walks return quickly, but some wander for ages.")


# ═══════════════════════════════════════════════════════════════
#  Overview
# ═══════════════════════════════════════════════════════════════

def overview_mode():
    """Show random walks across dimensions."""
    cols, rows = get_size()
    cw = cols - 8
    ch = max(8, (rows - 25) // 3)

    print(f"  A random walker takes one step in a random direction.")
    print(f"  Does it ever return home?")
    print()

    # 1D walk
    print(f"  \033[1m1D: always returns\033[0m")
    canvas = BrailleCanvas(cw, ch)
    n_steps = 1000
    for _ in range(20):
        path = walk_1d(n_steps)
        m = max(abs(p) for p in path)
        for t, pos in enumerate(path):
            canvas.plot(t, pos, (0, n_steps), (-80, 80))

    for line in canvas.render():
        print(f"    {line}")
    print()

    # 2D walk
    print(f"  \033[1m2D: always returns (but barely)\033[0m")
    canvas2 = BrailleCanvas(min(cw, 60), ch)
    path2 = walk_2d(10000)
    xs = [p[0] for p in path2]
    ys = [p[1] for p in path2]
    r = max(max(abs(x) for x in xs), max(abs(y) for y in ys)) + 1
    for x, y in path2:
        canvas2.plot(x, y, (-r, r), (-r, r))

    for line in canvas2.render():
        print(f"    {line}")
    print()

    # Pólya's theorem summary
    print(f"  \033[1m3D and beyond: escapes forever\033[0m")
    print()

    # Quick Monte Carlo
    for dim in [1, 2, 3, 4]:
        returns = sum(1 for _ in range(500) if walk_nd(3000, dim))
        prob = returns / 500
        bar = '█' * int(prob * 40) + '░' * int((1 - prob) * 40)
        labels = {1: "1D", 2: "2D", 3: "3D", 4: "4D"}
        print(f"    {labels[dim]}: return prob ≈ {prob:.2f}  {bar}")

    print()
    print(f"  In 1D and 2D, the drunk man always finds his way home.")
    print(f"  In 3D, he wanders off into infinity with probability ~66%.")
    print(f"  The boundary is sharp: dimension 2 is the critical dimension.")
    print()
    print(f"  This is a phase transition — not in temperature or density,")
    print(f"  but in the dimension of space itself.")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "overview"

    # Set seed for reproducibility if desired
    if "--seed" in args:
        idx = args.index("--seed")
        if idx + 1 < len(args):
            random.seed(int(args[idx + 1]))

    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  RANDOM WALKS\033[0m")
    print("  \033[1m  Pólya's Recurrence Theorem\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()

    if mode == "overview":
        overview_mode()
    elif mode == "fans":
        fans_mode()
    elif mode == "territory":
        territory_mode()
    elif mode == "polya":
        polya_mode()
    elif mode == "passage":
        passage_mode()
    else:
        print(f"  Unknown mode: {mode}")
        print(f"  Modes: overview, fans, territory, polya, passage")
        return

    print()


if __name__ == "__main__":
    main()
