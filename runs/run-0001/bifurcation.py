"""
Logistic Map Bifurcation Diagram — The Road to Chaos

The logistic map: x_{n+1} = r * x_n * (1 - x_n)

One equation. One parameter. An entire universe of behavior.

  r < 1.0:    extinction (x → 0)
  1.0 < r < 3.0:  stable fixed point at x = (r-1)/r
  3.0 < r < 3.449: period-2 oscillation
  3.449 < r < 3.544: period-4
  ... period-doubling cascade ...
  r ≈ 3.5699: onset of chaos
  r ≈ 3.8284: period-3 window (Li-Yorke: "period 3 implies chaos")
  r = 4.0:    full chaos, the orbit fills [0, 1]

The bifurcation diagram plots long-term behavior (y) vs parameter (r).
It's the Mandelbrot set's one-dimensional cousin — both are maps of
how the behavior of z → z² + c changes with the parameter.

The Feigenbaum constant δ ≈ 4.669201... is the ratio of successive
bifurcation intervals. It's UNIVERSAL: it appears in ANY map with a
quadratic maximum, regardless of the specific equation. It's as
fundamental as π, but for chaos instead of circles.

Usage:
  python3 bifurcation.py              # Full diagram
  python3 bifurcation.py zoom         # Zoom into period-doubling cascade
  python3 bifurcation.py feigenbaum   # Measure the Feigenbaum constant
  python3 bifurcation.py lyapunov     # Lyapunov exponent diagram
"""

import sys
import math
import time


# ═══════════════════════════════════════════════════════════════
#  Braille rendering
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_MAP = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


class BrailleCanvas:
    """A canvas that renders using Unicode braille characters."""

    def __init__(self, char_w, char_h):
        self.char_w = char_w
        self.char_h = char_h
        self.dot_w = char_w * 2
        self.dot_h = char_h * 4
        self.canvas = [[0] * char_w for _ in range(char_h)]

    def set(self, dx, dy):
        """Set a dot at pixel coordinates (dx, dy)."""
        if 0 <= dx < self.dot_w and 0 <= dy < self.dot_h:
            cx, cy = dx // 2, dy // 4
            bx, by = dx % 2, dy % 4
            self.canvas[cy][cx] |= BRAILLE_MAP[(bx, by)]

    def plot(self, x, y, x_range, y_range):
        """Plot a point in data coordinates."""
        x_min, x_max = x_range
        y_min, y_max = y_range
        dx = int((x - x_min) / (x_max - x_min + 1e-15) * (self.dot_w - 1))
        # Flip Y: top of canvas = high y values
        dy = int((1.0 - (y - y_min) / (y_max - y_min + 1e-15)) * (self.dot_h - 1))
        self.set(dx, dy)

    def render(self):
        """Return list of strings, one per character row."""
        return [
            "".join(chr(BRAILLE_BASE + cell) for cell in row)
            for row in self.canvas
        ]


# ═══════════════════════════════════════════════════════════════
#  Logistic map
# ═══════════════════════════════════════════════════════════════

def logistic(r, x):
    return r * x * (1.0 - x)


def iterate(r, x0=0.5, warmup=500, samples=200):
    """Iterate the logistic map, discard transient, return samples."""
    x = x0
    for _ in range(warmup):
        x = logistic(r, x)
    results = []
    for _ in range(samples):
        x = logistic(r, x)
        results.append(x)
    return results


def find_period(r, x0=0.5, warmup=2000, tol=1e-8, max_period=512):
    """Detect the period of the orbit at parameter r."""
    x = x0
    for _ in range(warmup):
        x = logistic(r, x)

    # Record orbit and check for recurrence
    orbit = [x]
    for i in range(max_period):
        x = logistic(r, x)
        for p, val in enumerate(orbit):
            if abs(x - val) < tol:
                return len(orbit) - p  # period = distance back to match
        orbit.append(x)

    # Fallback: check for periodicity in recent orbit
    recent = orbit[-max_period:]
    for p in range(1, max_period // 4):
        match = True
        for i in range(p, min(4 * p, len(recent))):
            if abs(recent[i] - recent[i - p]) > tol:
                match = False
                break
        if match:
            return p
    return -1  # Chaotic or period > max_period


def lyapunov_exponent(r, x0=0.5, iterations=10000):
    """Compute the Lyapunov exponent for the logistic map at parameter r."""
    x = x0
    total = 0.0
    # Warmup
    for _ in range(500):
        x = logistic(r, x)
    # Accumulate
    for _ in range(iterations):
        deriv = abs(r * (1.0 - 2.0 * x))
        if deriv < 1e-15:
            return float('-inf')
        total += math.log(deriv)
        x = logistic(r, x)
    return total / iterations


# ═══════════════════════════════════════════════════════════════
#  Bifurcation diagram
# ═══════════════════════════════════════════════════════════════

def bifurcation_diagram(r_min=2.5, r_max=4.0, char_w=120, char_h=35,
                         warmup=300, samples=150):
    """Compute and render the bifurcation diagram."""
    canvas = BrailleCanvas(char_w, char_h)

    n_r = char_w * 2  # One r value per dot column
    for i in range(n_r):
        r = r_min + (r_max - r_min) * i / (n_r - 1)
        points = iterate(r, warmup=warmup, samples=samples)
        for x in points:
            canvas.plot(r, x, (r_min, r_max), (0.0, 1.0))

        # Progress
        if (i + 1) % 20 == 0:
            pct = (i + 1) / n_r * 100
            sys.stdout.write(f"\r  Computing... {pct:.0f}%")
            sys.stdout.flush()

    sys.stdout.write("\r  " + " " * 30 + "\r")
    return canvas


def print_diagram(canvas, r_min, r_max, title=""):
    """Print a bifurcation diagram with axes."""
    lines = canvas.render()
    char_w = canvas.char_w

    if title:
        print(f"  \033[1m{title}\033[0m")
        print()

    y_labels = {0: "1.0", canvas.char_h // 4: "0.75",
                canvas.char_h // 2: "0.5", 3 * canvas.char_h // 4: "0.25",
                canvas.char_h - 1: "0.0"}

    for i, line in enumerate(lines):
        label = y_labels.get(i, "")
        pad = " " * (4 - len(label))
        print(f"  {pad}{label} │{line}")

    print(f"       └{'─' * char_w}")

    # X-axis labels
    n_marks = 6
    parts = []
    for j in range(n_marks + 1):
        r = r_min + (r_max - r_min) * j / n_marks
        pos = int(char_w * j / n_marks)
        label = f"{r:.2f}"
        parts.append((pos, label))

    x_line = [' '] * (char_w + 8)
    for pos, label in parts:
        for k, ch in enumerate(label):
            if pos + k + 8 < len(x_line):
                x_line[pos + k + 8] = ch

    print("".join(x_line))


# ═══════════════════════════════════════════════════════════════
#  Feigenbaum constant measurement
# ═══════════════════════════════════════════════════════════════

def find_bifurcation_r(from_period, to_period, r_lo, r_hi, tol=1e-10):
    """Binary search for the r where period transitions from from_period to to_period."""
    for _ in range(200):  # max iterations
        if r_hi - r_lo < tol:
            break
        r_mid = (r_lo + r_hi) / 2
        p = find_period(r_mid, warmup=5000, tol=1e-9)
        # We want the boundary: below it period <= from_period, above it period >= to_period
        if p <= from_period:
            r_lo = r_mid
        else:
            r_hi = r_mid
    return (r_lo + r_hi) / 2


def measure_feigenbaum():
    """Measure the Feigenbaum constant from the bifurcation cascade."""
    print("  Finding bifurcation points by binary search...")
    print()

    # Known values for verification:
    # Period 1→2:   r₁ ≈ 3.0000000
    # Period 2→4:   r₂ ≈ 3.4494897
    # Period 4→8:   r₃ ≈ 3.5440903
    # Period 8→16:  r₄ ≈ 3.5644073
    # Period 16→32: r₅ ≈ 3.5687594
    # Period 32→64: r₆ ≈ 3.5696916

    # Search ranges for each bifurcation
    searches = [
        (1, 2, 2.5, 3.2),
        (2, 4, 3.2, 3.5),
        (4, 8, 3.5, 3.56),
        (8, 16, 3.56, 3.567),
        (16, 32, 3.567, 3.5696),
        (32, 64, 3.5690, 3.5698),
    ]

    bifurcations = []
    for from_p, to_p, lo, hi in searches:
        r = find_bifurcation_r(from_p, to_p, lo, hi)
        bifurcations.append((from_p, to_p, r))
        print(f"    Period {from_p:2d} → {to_p:2d}  at  r = {r:.10f}")

    print()
    print("  Feigenbaum ratios (should converge to δ ≈ 4.669201...):")
    print()

    for i in range(2, len(bifurcations)):
        r_prev = bifurcations[i - 2][2]
        r_curr = bifurcations[i - 1][2]
        r_next = bifurcations[i][2]
        delta_prev = r_curr - r_prev
        delta_curr = r_next - r_curr
        if delta_curr > 1e-12:
            ratio = delta_prev / delta_curr
            fp, tp = bifurcations[i - 2][0], bifurcations[i - 2][1]
            fc, tc = bifurcations[i - 1][0], bifurcations[i - 1][1]
            fn, tn = bifurcations[i][0], bifurcations[i][1]
            print(f"    (r_{fc}→{tc} - r_{fp}→{tp}) / (r_{fn}→{tn} - r_{fc}→{tc}) = {ratio:.6f}")

    print()
    print(f"  True value: δ = 4.669201609102990...")
    print()
    print("  This constant is UNIVERSAL. It appears in any 1D map with a")
    print("  quadratic maximum: x → r·sin(πx), x → r·x·exp(-x), any of them.")
    print("  Feigenbaum discovered it empirically in 1975 on an HP-65 calculator")
    print("  and proved universality via renormalization group theory.")


# ═══════════════════════════════════════════════════════════════
#  Lyapunov exponent diagram
# ═══════════════════════════════════════════════════════════════

def lyapunov_diagram(r_min=2.5, r_max=4.0, char_w=120, char_h=20):
    """Compute Lyapunov exponent vs r and render."""
    canvas = BrailleCanvas(char_w, char_h)

    n_r = char_w * 2
    r_vals = []
    lya_vals = []

    for i in range(n_r):
        r = r_min + (r_max - r_min) * i / (n_r - 1)
        lya = lyapunov_exponent(r, iterations=5000)
        r_vals.append(r)
        lya_vals.append(lya)

        if (i + 1) % 20 == 0:
            sys.stdout.write(f"\r  Computing Lyapunov exponents... {(i+1)/n_r*100:.0f}%")
            sys.stdout.flush()

    sys.stdout.write("\r  " + " " * 50 + "\r")

    # Clamp values for plotting
    lya_min, lya_max = -2.0, 1.0
    for r, lya in zip(r_vals, lya_vals):
        lya_c = max(lya_min, min(lya_max, lya))
        canvas.plot(r, lya_c, (r_min, r_max), (lya_min, lya_max))

    # Also plot the zero line (λ=0 marks boundary between order and chaos)
    for i in range(canvas.dot_w):
        r = r_min + (r_max - r_min) * i / (canvas.dot_w - 1)
        canvas.plot(r, 0.0, (r_min, r_max), (lya_min, lya_max))

    return canvas, lya_min, lya_max


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "full"

    print("\033[2J\033[H")
    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  THE LOGISTIC MAP\033[0m")
    print("  \033[1m  x → r·x·(1-x) : The Road to Chaos\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()

    if mode in ("full", "diagram"):
        print("  One equation. One parameter. An entire universe of behavior.")
        print()
        print("  As r increases from 2.5 to 4.0:")
        print("    • Stable fixed point → period 2 → period 4 → period 8 → ...")
        print("    • Period-doubling cascade accelerates toward chaos")
        print("    • Within chaos: windows of order (period 3, 5, 6, ...)")
        print("    • At r = 4.0: fully chaotic, orbit fills [0, 1]")
        print()

        print("  \033[1mBifurcation Diagram\033[0m (r = 2.5 to 4.0)")
        print()
        canvas = bifurcation_diagram(r_min=2.5, r_max=4.0, char_w=120, char_h=35)
        print_diagram(canvas, 2.5, 4.0)
        print()

        # Annotate key features
        print("  Key features visible in the diagram:")
        print("    r = 3.0:    First bifurcation (fixed point → period 2)")
        print("    r ≈ 3.449:  Period 2 → 4")
        print("    r ≈ 3.544:  Period 4 → 8")
        print("    r ≈ 3.570:  Onset of chaos (accumulation point)")
        print("    r ≈ 3.628:  Band-merging crisis (4 bands → 2)")
        print("    r ≈ 3.679:  2 bands → 1 (full chaos)")
        print("    r ≈ 3.828:  Period-3 window (Li-Yorke theorem: period 3 ⟹ chaos)")
        print("    r = 4.0:    Orbit fills [0, 1], maximum entropy")
        print()

    if mode in ("full", "zoom"):
        print("  \033[1mZoom: Period-Doubling Cascade\033[0m (r = 3.4 to 3.6)")
        print()
        canvas = bifurcation_diagram(r_min=3.4, r_max=3.6, char_w=120, char_h=25,
                                      warmup=500, samples=200)
        print_diagram(canvas, 3.4, 3.6)
        print()
        print("  Each bifurcation interval is δ ≈ 4.669 times smaller than the last.")
        print("  The cascade accelerates, accumulating at r ≈ 3.5699..., where")
        print("  the period is infinite and chaos begins.")
        print()

    if mode in ("full", "feigenbaum"):
        measure_feigenbaum()
        print()

    if mode in ("full", "lyapunov"):
        print("  \033[1mLyapunov Exponent\033[0m (r = 2.5 to 4.0)")
        print()
        print("  The Lyapunov exponent λ measures sensitivity to initial conditions.")
        print("  λ < 0: trajectories converge (order)")
        print("  λ = 0: marginal (bifurcation points)")
        print("  λ > 0: trajectories diverge exponentially (chaos)")
        print()

        canvas, lya_min, lya_max = lyapunov_diagram(r_min=2.5, r_max=4.0,
                                                      char_w=120, char_h=20)
        lines = canvas.render()
        for i, line in enumerate(lines):
            y = lya_max - (lya_max - lya_min) * i / (len(lines) - 1)
            if abs(y) < 0.15:
                label = " λ=0"
            elif i == 0:
                label = f" {lya_max:.0f}"
            elif i == len(lines) - 1:
                label = f"{lya_min:.0f}"
            else:
                label = "    "
            print(f"  {label:>4s} │{line}")
        print(f"       └{'─' * 120}")
        print()
        print("  The λ = 0 line is the boundary between order and chaos.")
        print("  Every dip below zero within the chaotic region is a periodic window.")
        print("  The largest is the period-3 window near r ≈ 3.83.")
        print()

    if mode == "full":
        print("  ═══════════════════════════════════════════════════════════")
        print()
        print("  The bifurcation diagram is the Mandelbrot set's shadow.")
        print()
        print("  The logistic map x → rx(1-x) is conjugate to z → z² + c")
        print("  via c = r/2 - r²/4. The Mandelbrot set IS the bifurcation")
        print("  diagram extended to the complex plane. The period-doubling")
        print("  cascade along the real axis of the Mandelbrot set exactly")
        print("  reproduces this diagram.")
        print()
        print("  And the Feigenbaum constant δ ≈ 4.669 is as fundamental as π.")
        print("  π appears whenever you have circles. δ appears whenever you")
        print("  have period-doubling. It doesn't depend on the equation —")
        print("  only on the shape of the maximum. Quadratic maximum → δ.")
        print("  Every route to chaos through period-doubling passes through")
        print("  the same universal constant.")
        print()
        print("  The road to chaos has a speed limit. And that speed limit")
        print("  is a universal constant of nature.")
        print()


if __name__ == "__main__":
    main()
