"""
Feigenbaum Universality — The Same Constant Everywhere

The most surprising discovery in chaos theory: the Feigenbaum constant
δ ≈ 4.669201... appears in EVERY one-dimensional map with a quadratic
maximum, regardless of the specific equation.

  x → r·x·(1-x)        (logistic map)
  x → r·sin(πx)         (sine map)
  x → r·x·exp(1-x)      (Ricker map, ecology)
  x → r - x²            (quadratic map)

These are different equations. Different shapes. Different dynamics.
But they all undergo period-doubling, and the ratios of successive
bifurcation intervals all converge to the SAME constant: δ ≈ 4.669.

This is universality: quantitative agreement across qualitatively
different systems, arising from a shared mathematical structure
(the renormalization group fixed point).

Feigenbaum discovered this in 1975 on an HP-65 calculator. He
computed the bifurcation points of the logistic map, noticed the
ratios converging, then tried the sine map — same constant. Then
he knew it was universal and proved it via renormalization.

Usage:
    python3 universality.py            # Compare all four maps
    python3 universality.py bifurcate  # Show all four bifurcation diagrams
    python3 universality.py measure    # Measure δ for each map
"""

import sys
import os
import math


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


def get_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# ═══════════════════════════════════════════════════════════════
#  Maps
# ═══════════════════════════════════════════════════════════════

def logistic_map(r, x):
    """x → r·x·(1-x)"""
    return r * x * (1.0 - x)

def sine_map(r, x):
    """x → r·sin(πx)"""
    return r * math.sin(math.pi * x)

def ricker_map(r, x):
    """x → r·x·exp(1-x)"""
    return r * x * math.exp(1.0 - x)

def quadratic_map(r, x):
    """x → r - x²"""
    return r - x * x


# Map configurations: (function, name, r_range, x_range, x0, r_search_ranges)
MAPS = {
    "logistic": (
        logistic_map,
        "x → r·x·(1-x)",
        (2.5, 4.0),      # r range for diagram
        (0.0, 1.0),      # x range for diagram
        0.2,             # initial x
        [                # (from_period, to_period, r_lo, r_hi)
            (1, 2, 2.5, 3.2),
            (2, 4, 3.2, 3.5),
            (4, 8, 3.5, 3.56),
            (8, 16, 3.56, 3.567),
            (16, 32, 3.567, 3.5696),
        ],
    ),
    "sine": (
        sine_map,
        "x → r·sin(πx)",
        (0.5, 1.0),
        (0.0, 1.0),
        0.2,
        [
            (1, 2, 0.710, 0.730),
            (2, 4, 0.828, 0.838),
            (4, 8, 0.855, 0.862),
            (8, 16, 0.862, 0.866),
            (16, 32, 0.8650, 0.8656),
        ],
    ),
    "ricker": (
        ricker_map,
        "x → r·x·exp(1-x)",
        (1.0, 6.0),
        (0.0, 8.0),
        0.5,
        [
            (1, 2, 2.50, 2.75),
            (2, 4, 4.40, 4.65),
            (4, 8, 5.10, 5.30),
            (8, 16, 5.35, 5.42),
            (16, 32, 5.42, 5.44),
        ],
    ),
    "quadratic": (
        quadratic_map,
        "x → r - x²",
        (0.5, 2.0),
        (-2.0, 2.0),
        0.0,
        [
            (1, 2, 0.5, 1.0),
            (2, 4, 1.0, 1.35),
            (4, 8, 1.30, 1.40),
            (8, 16, 1.38, 1.402),
            (16, 32, 1.396, 1.406),
        ],
    ),
}


# ═══════════════════════════════════════════════════════════════
#  Iteration and period detection
# ═══════════════════════════════════════════════════════════════

def iterate(map_func, r, x0, warmup=500, samples=200):
    """Iterate a map, discard transient, return samples."""
    x = x0
    for _ in range(warmup):
        x = map_func(r, x)
        if abs(x) > 1e10 or math.isnan(x):
            return []
    results = []
    for _ in range(samples):
        x = map_func(r, x)
        if abs(x) > 1e10 or math.isnan(x):
            break
        results.append(x)
    return results


def find_period(map_func, r, x0, warmup=3000, tol=1e-8, max_period=256):
    """Detect the period of the orbit at parameter r."""
    x = x0
    for _ in range(warmup):
        x = map_func(r, x)
        if abs(x) > 1e10 or math.isnan(x):
            return -1
    orbit = [x]
    for _ in range(max_period):
        x = map_func(r, x)
        if abs(x) > 1e10 or math.isnan(x):
            return -1
        for p, val in enumerate(orbit):
            if abs(x - val) < tol:
                return len(orbit) - p
        orbit.append(x)
    return -1


def find_bifurcation_r(map_func, from_period, to_period, r_lo, r_hi, x0, tol=1e-10):
    """Binary search for the bifurcation point."""
    for _ in range(200):
        if r_hi - r_lo < tol:
            break
        r_mid = (r_lo + r_hi) / 2
        p = find_period(map_func, r_mid, x0, warmup=5000, tol=1e-9)
        if p <= from_period:
            r_lo = r_mid
        else:
            r_hi = r_mid
    return (r_lo + r_hi) / 2


# ═══════════════════════════════════════════════════════════════
#  Bifurcation diagram
# ═══════════════════════════════════════════════════════════════

def draw_bifurcation(map_func, r_range, x_range, x0, cw, ch,
                      warmup=300, samples=150):
    """Compute and render a bifurcation diagram."""
    canvas = BrailleCanvas(cw, ch)
    n_r = cw * 2

    for i in range(n_r):
        r = r_range[0] + (r_range[1] - r_range[0]) * i / (n_r - 1)
        points = iterate(map_func, r, x0, warmup=warmup, samples=samples)
        for x in points:
            canvas.plot(r, x, r_range, x_range)

    return canvas


# ═══════════════════════════════════════════════════════════════
#  Modes
# ═══════════════════════════════════════════════════════════════

def measure_mode():
    """Measure the Feigenbaum constant for each map."""
    print("  Measuring δ for four different maps...")
    print()
    print("  If universality holds, all four should give δ ≈ 4.669201...")
    print()

    true_delta = 4.669201609102990

    for name in ["logistic", "sine", "ricker", "quadratic"]:
        map_func, formula, _, _, x0, searches = MAPS[name]

        print(f"  \033[1m{formula}\033[0m")

        bifurcations = []
        for from_p, to_p, lo, hi in searches:
            r = find_bifurcation_r(map_func, from_p, to_p, lo, hi, x0)
            bifurcations.append((from_p, to_p, r))
            print(f"    Period {from_p:2d} → {to_p:2d}  at  r = {r:.10f}")

        print()
        if len(bifurcations) >= 3:
            print(f"    Feigenbaum ratios:")
            for i in range(2, len(bifurcations)):
                r_prev = bifurcations[i - 2][2]
                r_curr = bifurcations[i - 1][2]
                r_next = bifurcations[i][2]
                delta_prev = r_curr - r_prev
                delta_curr = r_next - r_curr
                if abs(delta_curr) > 1e-12:
                    ratio = delta_prev / delta_curr
                    error = abs(ratio - true_delta) / true_delta * 100
                    print(f"      δ_{i} = {ratio:.6f}  (error: {error:.1f}%)")
            print()

    print(f"  True value: δ = {true_delta}")
    print()
    print(f"  Four different equations. Four different dynamics.")
    print(f"  The same constant. This is universality.")


def bifurcate_mode():
    """Show bifurcation diagrams side by side."""
    cols, rows = get_size()
    cw = cols - 10
    ch = max(6, (rows - 16) // 4)

    for name in ["logistic", "sine", "ricker", "quadratic"]:
        map_func, formula, r_range, x_range, x0, _ = MAPS[name]

        print(f"  \033[1m{formula}\033[0m  (r = {r_range[0]} to {r_range[1]})")

        canvas = draw_bifurcation(map_func, r_range, x_range, x0, cw, ch)
        for line in canvas.render():
            print(f"    {line}")
        print()


def overview_mode():
    """Show everything: diagrams + measurements."""
    cols, rows = get_size()
    cw = cols - 10
    ch = max(5, (rows - 30) // 4)

    print(f"  Four maps. Four equations. One constant.")
    print()

    # Show mini bifurcation diagrams
    for name in ["logistic", "sine", "ricker", "quadratic"]:
        map_func, formula, r_range, x_range, x0, _ = MAPS[name]

        canvas = draw_bifurcation(map_func, r_range, x_range, x0, cw, ch)
        print(f"  \033[1m{formula}\033[0m")
        for line in canvas.render():
            print(f"    {line}")
        print()

    # Measure delta for each
    print(f"  ─────────────────────────────────────────────────────")
    print(f"  Feigenbaum constant measured from each map:")
    print()

    true_delta = 4.669201609102990

    for name in ["logistic", "sine", "ricker", "quadratic"]:
        map_func, formula, _, _, x0, searches = MAPS[name]

        bifurcations = []
        for from_p, to_p, lo, hi in searches:
            r = find_bifurcation_r(map_func, from_p, to_p, lo, hi, x0)
            bifurcations.append(r)

        if len(bifurcations) >= 4:
            d1 = bifurcations[1] - bifurcations[0]
            d2 = bifurcations[2] - bifurcations[1]
            d3 = bifurcations[3] - bifurcations[2]
            delta1 = d1 / d2 if abs(d2) > 1e-15 else 0
            delta2 = d2 / d3 if abs(d3) > 1e-15 else 0
            print(f"    {formula:>20s}:  δ₁ = {delta1:.3f}   δ₂ = {delta2:.3f}")
        else:
            print(f"    {formula:>20s}:  insufficient bifurcation data")

    print()
    print(f"    {'True value':>20s}:  δ  = {true_delta:.6f}...")
    print()
    print(f"  The ratios converge to the same number regardless of")
    print(f"  which equation produced them. Feigenbaum's constant is")
    print(f"  as fundamental as π — but for chaos instead of circles.")
    print()
    print(f"  The proof uses renormalization group theory: period-doubling")
    print(f"  is a fixed point of a functional operator on the space of")
    print(f"  maps. At the fixed point, only the shape of the maximum")
    print(f"  matters. Quadratic maximum → δ. Universal.")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "overview"

    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  FEIGENBAUM UNIVERSALITY\033[0m")
    print("  \033[1m  The Same Constant in Every Map\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()

    if mode == "overview":
        overview_mode()
    elif mode == "bifurcate":
        bifurcate_mode()
    elif mode == "measure":
        measure_mode()
    else:
        print(f"  Unknown mode: {mode}")
        print(f"  Modes: overview, bifurcate, measure")
        return

    print()


if __name__ == "__main__":
    main()
