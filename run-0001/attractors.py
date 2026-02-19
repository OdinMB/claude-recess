"""
Strange Attractor Gallery — Chaos as Art

Four equations. Millions of iterations. Intricate structures emerge from
simple rules, traced out point by point, the orbit never repeating but
always bound to an invisible shape in phase space.

The attractor is a mathematical object that exists only as a limit: no
finite portion of the orbit defines it, but the longer you iterate, the
more clearly the shape emerges. It's the ghost of infinity.

Attractors rendered here:
  Clifford:  x' = sin(a·y) + c·cos(a·x),  y' = sin(b·x) + d·cos(b·y)
  De Jong:   x' = sin(a·y) - cos(b·x),      y' = sin(c·x) - cos(d·y)
  Hénon:     x' = 1 - a·x² + y,             y' = b·x
  Ikeda:     t = 0.4 - 6/(1+x²+y²),        x' = 1 + u(x·cos(t) - y·sin(t))
                                              y' = u(x·sin(t) + y·cos(t))

Usage:
  python3 attractors.py               # Full gallery
  python3 attractors.py clifford      # Clifford attractor variants
  python3 attractors.py dejong        # De Jong attractor variants
  python3 attractors.py sweep         # Parameter sweep animation
"""

import math
import sys
import time


# ═══════════════════════════════════════════════════════════════
#  Density canvas with braille rendering
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_DOTS = [
    (0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (0, 3, 0x40),
    (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (1, 3, 0x80),
]


class DensityCanvas:
    """Accumulates point density and renders using braille with color."""

    def __init__(self, char_w, char_h):
        self.char_w = char_w
        self.char_h = char_h
        self.dot_w = char_w * 2
        self.dot_h = char_h * 4
        self.density = [[0] * self.dot_w for _ in range(self.dot_h)]
        self.total_points = 0

    def add(self, x, y, x_range, y_range):
        """Add a point in data coordinates."""
        x_min, x_max = x_range
        y_min, y_max = y_range
        dx = int((x - x_min) / (x_max - x_min + 1e-15) * (self.dot_w - 1))
        dy = int((1 - (y - y_min) / (y_max - y_min + 1e-15)) * (self.dot_h - 1))
        if 0 <= dx < self.dot_w and 0 <= dy < self.dot_h:
            self.density[dy][dx] += 1
            self.total_points += 1

    def render_plain(self):
        """Render using braille, all visited dots lit."""
        lines = []
        for cy in range(self.char_h):
            row = []
            for cx in range(self.char_w):
                code = 0
                for bx, by, bit in BRAILLE_DOTS:
                    px = cx * 2 + bx
                    py = cy * 4 + by
                    if px < self.dot_w and py < self.dot_h:
                        if self.density[py][px] > 0:
                            code |= bit
                row.append(chr(BRAILLE_BASE + code))
            lines.append("".join(row))
        return lines

    def render_color(self):
        """Render with ANSI 256-color based on cell density."""
        # Compute log density per character cell
        cell_density = []
        for cy in range(self.char_h):
            row = []
            for cx in range(self.char_w):
                total = 0
                code = 0
                for bx, by, bit in BRAILLE_DOTS:
                    px = cx * 2 + bx
                    py = cy * 4 + by
                    if px < self.dot_w and py < self.dot_h:
                        d = self.density[py][px]
                        if d > 0:
                            code |= bit
                            total += d
                row.append((code, total))
            cell_density.append(row)

        # Find max for normalization
        max_d = max(max(d for _, d in row) for row in cell_density) or 1

        # Color palette: dark → bright
        # Blue → Cyan → Green → Yellow → Red → White
        palette = [
            17, 18, 19, 20, 21,      # dark blues
            25, 26, 27, 32, 33,      # blues
            38, 39, 44, 45, 50,      # cyans
            51, 49, 48, 47, 46,      # cyan → green
            82, 118, 154, 190, 226,  # green → yellow
            220, 214, 208, 202, 196, # yellow → red
            197, 198, 199, 255,      # red → white
        ]

        lines = []
        for cy in range(self.char_h):
            parts = []
            for cx in range(self.char_w):
                code, total = cell_density[cy][cx]
                if code == 0:
                    parts.append(" ")
                else:
                    # Log scale for better contrast
                    norm = math.log1p(total) / math.log1p(max_d)
                    idx = min(len(palette) - 1, int(norm * len(palette)))
                    color = palette[idx]
                    parts.append(f"\033[38;5;{color}m{chr(BRAILLE_BASE + code)}\033[0m")
            lines.append("".join(parts))
        return lines


# ═══════════════════════════════════════════════════════════════
#  Attractor functions
# ═══════════════════════════════════════════════════════════════

def clifford(a, b, c, d, n=2_000_000, warmup=100):
    """Clifford attractor: x' = sin(ay) + c·cos(ax), y' = sin(bx) + d·cos(by)"""
    x, y = 0.1, 0.1
    sin, cos = math.sin, math.cos
    for _ in range(warmup):
        x, y = sin(a * y) + c * cos(a * x), sin(b * x) + d * cos(b * y)
    points = []
    for _ in range(n):
        x, y = sin(a * y) + c * cos(a * x), sin(b * x) + d * cos(b * y)
        points.append((x, y))
    return points


def dejong(a, b, c, d, n=2_000_000, warmup=100):
    """De Jong attractor: x' = sin(ay) - cos(bx), y' = sin(cx) - cos(dy)"""
    x, y = 0.1, 0.1
    sin, cos = math.sin, math.cos
    for _ in range(warmup):
        x, y = sin(a * y) - cos(b * x), sin(c * x) - cos(d * y)
    points = []
    for _ in range(n):
        x, y = sin(a * y) - cos(b * x), sin(c * x) - cos(d * y)
        points.append((x, y))
    return points


def henon(a=1.4, b=0.3, n=500_000, warmup=100):
    """Hénon map: x' = 1 - ax² + y, y' = bx"""
    x, y = 0.1, 0.1
    points = []
    for _ in range(warmup):
        x, y = 1 - a * x * x + y, b * x
    for _ in range(n):
        x, y = 1 - a * x * x + y, b * x
        if abs(x) > 10 or abs(y) > 10:
            break
        points.append((x, y))
    return points


def ikeda(u=0.918, n=1_000_000, warmup=100):
    """Ikeda map: chaotic dynamics of a ring cavity laser."""
    x, y = 0.1, 0.1
    sin, cos = math.sin, math.cos
    for _ in range(warmup):
        t = 0.4 - 6.0 / (1.0 + x * x + y * y)
        x, y = 1 + u * (x * cos(t) - y * sin(t)), u * (x * sin(t) + y * cos(t))
    points = []
    for _ in range(n):
        t = 0.4 - 6.0 / (1.0 + x * x + y * y)
        x, y = 1 + u * (x * cos(t) - y * sin(t)), u * (x * sin(t) + y * cos(t))
        points.append((x, y))
    return points


def compute_bounds(points, margin=0.05):
    """Compute axis ranges with margin."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    dx = (x_max - x_min) * margin
    dy = (y_max - y_min) * margin
    # Make square aspect ratio
    rx = x_max - x_min + 2 * dx
    ry = y_max - y_min + 2 * dy
    if rx > ry:
        dy += (rx - ry) / 2
    else:
        dx += (ry - rx) / 2
    return (x_min - dx, x_max + dx), (y_min - dy, y_max + dy)


def render_attractor(points, char_w=120, char_h=40, color=True):
    """Render an attractor to the terminal."""
    x_range, y_range = compute_bounds(points)
    canvas = DensityCanvas(char_w, char_h)

    for x, y in points:
        canvas.add(x, y, x_range, y_range)

    if color:
        return canvas.render_color()
    else:
        return canvas.render_plain()


# ═══════════════════════════════════════════════════════════════
#  Gallery
# ═══════════════════════════════════════════════════════════════

# Beautiful parameter sets discovered by exploration
CLIFFORD_PARAMS = [
    (-1.4, 1.6, 1.0, 0.7, "Butterfly"),
    (1.7, 1.7, 0.6, 1.2, "Swirl"),
    (-1.7, 1.3, -0.1, -1.2, "Tendrils"),
    (1.5, -1.8, 1.6, 0.9, "Windmill"),
]

DEJONG_PARAMS = [
    (-2.0, -2.0, -1.2, 2.0, "Petals"),
    (1.4, -2.3, 2.4, -2.1, "Wings"),
    (-2.7, -0.09, -0.86, -2.2, "Feathers"),
    (0.97, -1.9, 1.38, -1.5, "Ribbons"),
]


def show_attractor(title, points, char_w=120, char_h=35):
    """Display one attractor with title."""
    lines = render_attractor(points, char_w, char_h)
    print(f"  \033[1m{title}\033[0m")
    print()
    for line in lines:
        print(f"  {line}")
    print()


def demo_clifford():
    """Show Clifford attractor variants."""
    print("\033[2J\033[H")
    print("  ═══════════════════════════════════════════════════")
    print("  \033[1m  CLIFFORD ATTRACTOR\033[0m")
    print("  \033[1m  x' = sin(a·y) + c·cos(a·x)\033[0m")
    print("  \033[1m  y' = sin(b·x) + d·cos(b·y)\033[0m")
    print("  ═══════════════════════════════════════════════════")
    print()

    for a, b, c, d, name in CLIFFORD_PARAMS:
        print(f"  Computing {name} (a={a}, b={b}, c={c}, d={d})...")
        points = clifford(a, b, c, d, n=1_500_000)
        show_attractor(f"Clifford: {name}  (a={a}, b={b}, c={c}, d={d})", points)
        time.sleep(0.5)


def demo_dejong():
    """Show De Jong attractor variants."""
    print("\033[2J\033[H")
    print("  ═══════════════════════════════════════════════════")
    print("  \033[1m  DE JONG ATTRACTOR\033[0m")
    print("  \033[1m  x' = sin(a·y) - cos(b·x)\033[0m")
    print("  \033[1m  y' = sin(c·x) - cos(d·y)\033[0m")
    print("  ═══════════════════════════════════════════════════")
    print()

    for a, b, c, d, name in DEJONG_PARAMS:
        print(f"  Computing {name} (a={a}, b={b}, c={c}, d={d})...")
        points = dejong(a, b, c, d, n=1_500_000)
        show_attractor(f"De Jong: {name}  (a={a}, b={b}, c={c}, d={d})", points)
        time.sleep(0.5)


def demo_classics():
    """Hénon map and Ikeda attractor."""
    print("\033[2J\033[H")
    print("  ═══════════════════════════════════════════════════")
    print("  \033[1m  CLASSIC STRANGE ATTRACTORS\033[0m")
    print("  ═══════════════════════════════════════════════════")
    print()

    print("  Computing Hénon map (a=1.4, b=0.3)...")
    points = henon(a=1.4, b=0.3, n=500_000)
    show_attractor("Hénon Map: x' = 1 - 1.4x² + y,  y' = 0.3x", points)

    print("  Computing Ikeda map (u=0.918)...")
    points = ikeda(u=0.918, n=1_000_000)
    show_attractor("Ikeda Map: laser ring cavity chaos (u=0.918)", points)


def demo_sweep():
    """Sweep a parameter and show the attractor morphing."""
    print("\033[2J\033[H")
    print("  ═══════════════════════════════════════════════════")
    print("  \033[1m  PARAMETER SWEEP\033[0m")
    print("  \033[1m  Clifford attractor as 'a' varies\033[0m")
    print("  ═══════════════════════════════════════════════════")
    print()
    print("  Watch the attractor morph as a single parameter changes.")
    print("  Same equation, different shapes. The parameter space is")
    print("  a landscape of behavior, and small changes can produce")
    print("  dramatic qualitative shifts.")
    print()
    time.sleep(1)

    b, c, d = 1.7, 0.6, 1.2
    for a_10 in range(-30, 31, 5):
        a = a_10 / 10.0
        print(f"\033[2J\033[H")
        print(f"  Computing Clifford (a={a:.1f}, b={b}, c={c}, d={d})...")
        points = clifford(a, b, c, d, n=500_000)
        show_attractor(
            f"Clifford sweep: a = {a:.1f}  (b={b}, c={c}, d={d})",
            points, char_w=100, char_h=30
        )
        time.sleep(0.3)

    print("  Small changes in one parameter produce entirely different")
    print("  geometries. The attractor appears, transforms, dissolves,")
    print("  and reappears in a different form. The parameter space")
    print("  itself has structure — regions of similar behavior separated")
    print("  by sharp boundaries where the qualitative nature changes.")
    print()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "full"

    if mode == "full":
        print("\033[2J\033[H")
        print()
        print("  ═══════════════════════════════════════════════════════")
        print("  \033[1m  STRANGE ATTRACTOR GALLERY\033[0m")
        print("  \033[1m  Chaos as Art\033[0m")
        print("  ═══════════════════════════════════════════════════════")
        print()
        print("  An attractor is a shape that a chaotic orbit traces out")
        print("  over infinite time. The orbit never repeats, never crosses")
        print("  itself, but stays forever bound to this invisible shape.")
        print()
        print("  Each attractor is defined by a simple equation with a few")
        print("  parameters. Different parameters → different shapes.")
        print("  The parameter space is a landscape of behavior, and the")
        print("  boundaries between qualitative regimes are — once again —")
        print("  where the complexity lives.")
        print()
        time.sleep(2)

        demo_clifford()
        demo_dejong()
        demo_classics()

        print("  ═══════════════════════════════════════════════════════")
        print()
        print("  Every attractor here is produced by iterating a simple")
        print("  equation millions of times. The equation is deterministic")
        print("  — no randomness. Yet the orbit is chaotic: sensitive to")
        print("  initial conditions, never periodic, densely filling a")
        print("  structure of infinite intricacy.")
        print()
        print("  The structure is the attractor. It's not designed. It's")
        print("  not chosen. It emerges. The equation doesn't describe")
        print("  the shape — it generates it, point by point, from nothing")
        print("  but iteration and arithmetic.")
        print()

    elif mode == "clifford":
        demo_clifford()
    elif mode == "dejong":
        demo_dejong()
    elif mode == "classics":
        demo_classics()
    elif mode == "sweep":
        demo_sweep()
    else:
        print(f"Unknown mode: {mode}")
        print("Modes: clifford, dejong, classics, sweep")


if __name__ == "__main__":
    main()
