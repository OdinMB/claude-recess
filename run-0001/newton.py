"""
Newton Fractals — Where Root-Finding Meets Chaos

Newton's method finds roots of f(z) = 0 by iterating:
    z → z - f(z)/f'(z)

For polynomials with multiple roots, each starting point z₀
converges to one of the roots. The basins of attraction — sets
of starting points that converge to the same root — have fractal
boundaries.

On the boundary between basins, Newton's method can't decide which
root to converge to. The tiniest perturbation sends it to a
different root. The boundary is infinitely complex, self-similar
at every scale.

This is the same phenomenon as the Mandelbrot set: the boundary
between different behaviors is where the complexity lives. The
interior of each basin is boring (every point converges to the
same root). The boundary is where chaos happens.

For z³ - 1 = 0 (three cube roots of unity), the three basins
create a famous fractal with threefold symmetry. The boundaries
are Julia sets of the Newton map.

Usage:
    python3 newton.py                  # z³ - 1 (classic)
    python3 newton.py z4               # z⁴ - 1 (fourfold)
    python3 newton.py z5               # z⁵ - 1 (fivefold)
    python3 newton.py custom           # z³ - 2z + 2
    python3 newton.py gallery          # All of the above
    python3 newton.py zoom             # Deep zoom into boundary
"""

import sys
import os
import math


# ═══════════════════════════════════════════════════════════════
#  Complex arithmetic (no cmath dependency)
# ═══════════════════════════════════════════════════════════════

def cmul(a, b):
    """Multiply two complex numbers (as tuples)."""
    return (a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0])

def cdiv(a, b):
    """Divide two complex numbers."""
    denom = b[0]*b[0] + b[1]*b[1]
    if denom < 1e-30:
        return (1e15, 1e15)
    return ((a[0]*b[0] + a[1]*b[1]) / denom,
            (a[1]*b[0] - a[0]*b[1]) / denom)

def csub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def cabs2(z):
    return z[0]*z[0] + z[1]*z[1]

def cpow(z, n):
    """Integer power of a complex number."""
    result = (1.0, 0.0)
    for _ in range(n):
        result = cmul(result, z)
    return result


# ═══════════════════════════════════════════════════════════════
#  Polynomial definitions
# ═══════════════════════════════════════════════════════════════

def poly_z3(z):
    """f(z) = z³ - 1, f'(z) = 3z²"""
    f = csub(cpow(z, 3), (1, 0))
    fp = cmul((3, 0), cpow(z, 2))
    return f, fp

def poly_z4(z):
    """f(z) = z⁴ - 1, f'(z) = 4z³"""
    f = csub(cpow(z, 4), (1, 0))
    fp = cmul((4, 0), cpow(z, 3))
    return f, fp

def poly_z5(z):
    """f(z) = z⁵ - 1, f'(z) = 5z⁴"""
    f = csub(cpow(z, 5), (1, 0))
    fp = cmul((5, 0), cpow(z, 4))
    return f, fp

def poly_custom(z):
    """f(z) = z³ - 2z + 2, f'(z) = 3z² - 2"""
    z2 = cpow(z, 2)
    z3 = cpow(z, 3)
    f = (z3[0] - 2*z[0] + 2, z3[1] - 2*z[1])
    fp = (3*z2[0] - 2, 3*z2[1])
    return f, fp


# Roots for coloring
ROOTS_Z3 = [(1, 0), (-0.5, math.sqrt(3)/2), (-0.5, -math.sqrt(3)/2)]
ROOTS_Z4 = [(1, 0), (0, 1), (-1, 0), (0, -1)]
ROOTS_Z5 = [(math.cos(2*math.pi*k/5), math.sin(2*math.pi*k/5)) for k in range(5)]
ROOTS_CUSTOM = [(-1.7693, 0), (0.8846, 1.0244), (0.8846, -1.0244)]  # approximate


# ═══════════════════════════════════════════════════════════════
#  Newton iteration
# ═══════════════════════════════════════════════════════════════

def newton_iterate(z, poly_func, max_iter=50, tol=1e-6):
    """
    Apply Newton's method. Return (root_index, iterations).
    root_index = -1 if didn't converge.
    """
    for i in range(max_iter):
        f, fp = poly_func(z)
        if cabs2(fp) < 1e-30:
            return -1, max_iter
        step = cdiv(f, fp)
        z = csub(z, step)
        if cabs2(f) < tol * tol:
            return i, i  # converged; return iterations for shading
    return -1, max_iter


def find_root_index(z, roots, tol=0.1):
    """Find which root z is closest to."""
    min_dist = float('inf')
    best = -1
    for i, r in enumerate(roots):
        d = cabs2(csub(z, r))
        if d < min_dist:
            min_dist = d
            best = i
    return best if min_dist < tol * tol else -1


def compute_fractal(poly_func, roots, x_range, y_range, w, h, max_iter=40):
    """
    Compute Newton fractal. Returns grid of (root_index, iterations).
    """
    grid = [[None] * w for _ in range(h)]
    x_min, x_max = x_range
    y_min, y_max = y_range

    for row in range(h):
        y = y_max - (y_max - y_min) * row / (h - 1)
        for col in range(w):
            x = x_min + (x_max - x_min) * col / (w - 1)
            z = (x, y)

            # Newton iteration
            for it in range(max_iter):
                f, fp = poly_func(z)
                if cabs2(fp) < 1e-30:
                    break
                step = cdiv(f, fp)
                z = csub(z, step)
                if cabs2(f) < 1e-10:
                    break

            root_idx = find_root_index(z, roots)
            grid[row][col] = (root_idx, it)

    return grid


# ═══════════════════════════════════════════════════════════════
#  Rendering
# ═══════════════════════════════════════════════════════════════

# Color palettes per root (dark to bright for each)
ROOT_PALETTES = [
    # Root 0: reds
    [52, 88, 124, 160, 196, 203, 210, 217, 224, 231],
    # Root 1: greens
    [22, 28, 34, 40, 46, 47, 48, 49, 50, 51],
    # Root 2: blues
    [17, 18, 19, 20, 21, 27, 33, 39, 45, 231],
    # Root 3: yellows
    [58, 94, 130, 166, 172, 178, 184, 190, 226, 231],
    # Root 4: magentas
    [53, 89, 125, 161, 162, 163, 164, 165, 171, 231],
]


def render_half_block(grid, h, w):
    """Render using half-block characters (▀) for double vertical resolution."""
    lines = []

    for row in range(0, h - 1, 2):
        chars = []
        for col in range(w):
            top = grid[row][col]
            bot = grid[row + 1][col] if row + 1 < h else (-1, 40)

            top_root, top_iter = top
            bot_root, bot_iter = bot

            top_color = get_color(top_root, top_iter)
            bot_color = get_color(bot_root, bot_iter)

            # Use ▀ with foreground=top, background=bottom
            chars.append(f"\033[38;5;{top_color};48;5;{bot_color}m▀\033[0m")

        lines.append("".join(chars))

    return lines


def get_color(root_idx, iterations, max_iter=40):
    """Get ANSI 256 color for a root/iteration combination."""
    if root_idx < 0 or root_idx >= len(ROOT_PALETTES):
        return 0  # black for non-convergence

    palette = ROOT_PALETTES[root_idx]
    # Darker = more iterations (slower convergence)
    t = 1.0 - min(iterations / max_iter, 1.0)
    idx = int(t * (len(palette) - 1))
    return palette[min(idx, len(palette) - 1)]


def render_braille(grid, h, w, roots):
    """Render using braille characters (one dot per root basin)."""
    BRAILLE_BASE = 0x2800
    BRAILLE_MAP = {
        (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
        (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
    }

    ch = (h + 3) // 4
    cw = (w + 1) // 2
    char_grid = [[0] * cw for _ in range(ch)]

    for row in range(h):
        for col in range(w):
            root_idx, iters = grid[row][col]
            if root_idx >= 0 and iters < 30:
                cy, cx = row // 4, col // 2
                by, bx = row % 4, col % 2
                if cy < ch and cx < cw:
                    char_grid[cy][cx] |= BRAILLE_MAP.get((bx, by), 0)

    return ["".join(chr(BRAILLE_BASE + c) for c in row_data) for row_data in char_grid]


# ═══════════════════════════════════════════════════════════════
#  Terminal
# ═══════════════════════════════════════════════════════════════

def get_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# ═══════════════════════════════════════════════════════════════
#  Modes
# ═══════════════════════════════════════════════════════════════

def show_fractal(name, poly_func, roots, x_range=(-2, 2), y_range=(-2, 2),
                 max_iter=40, description=""):
    """Compute and display a Newton fractal."""
    cols, rows = get_size()
    w = cols - 6
    h = (rows - 12) * 2  # ×2 for half-block rendering

    print(f"  \033[1m{name}\033[0m")
    if description:
        print(f"  {description}")
    print(f"  {len(roots)} roots, {w}×{h} pixels, max {max_iter} iterations")
    print()

    sys.stdout.write("  Computing...")
    sys.stdout.flush()

    grid = compute_fractal(poly_func, roots, x_range, y_range, w, h, max_iter)

    sys.stdout.write("\r              \r")

    for line in render_half_block(grid, h, w):
        print(f"   {line}")

    print()

    # Statistics
    root_counts = [0] * len(roots)
    boundary_count = 0
    total = 0
    for row in grid:
        for root_idx, iters in row:
            total += 1
            if root_idx >= 0:
                root_counts[root_idx] += 1
            if iters >= max_iter - 1:
                boundary_count += 1

    print(f"  Basin sizes:", end="")
    for i, count in enumerate(root_counts):
        pct = 100 * count / total
        print(f"  root {i}: {pct:.1f}%", end="")
    print()
    print(f"  Boundary pixels (slow convergence): {100*boundary_count/total:.1f}%")


def z3_mode():
    show_fractal(
        "z³ − 1 = 0",
        poly_z3, ROOTS_Z3,
        x_range=(-1.5, 1.5), y_range=(-1.5, 1.5),
        description="Three cube roots of unity. The classic Newton fractal."
    )
    print()
    print(f"  The three basins (red, green, blue) meet at every point")
    print(f"  of the boundary — Wada basins. Near the boundary, the")
    print(f"  iteration oscillates chaotically between roots before")
    print(f"  finally converging. The boundary is a Julia set.")


def z4_mode():
    show_fractal(
        "z⁴ − 1 = 0",
        poly_z4, ROOTS_Z4,
        x_range=(-1.5, 1.5), y_range=(-1.5, 1.5),
        description="Four fourth roots of unity. Fourfold symmetry."
    )


def z5_mode():
    show_fractal(
        "z⁵ − 1 = 0",
        poly_z5, ROOTS_Z5,
        x_range=(-1.5, 1.5), y_range=(-1.5, 1.5),
        description="Five fifth roots of unity. Fivefold symmetry."
    )


def custom_mode():
    show_fractal(
        "z³ − 2z + 2 = 0",
        poly_custom, ROOTS_CUSTOM,
        x_range=(-2.5, 2.5), y_range=(-2.5, 2.5),
        description="Asymmetric polynomial with one real, two complex roots."
    )


def zoom_mode():
    """Deep zoom into the boundary of z³ - 1."""
    cols, rows = get_size()

    # Show progressive zooms
    zooms = [
        ((-1.5, 1.5), (-1.5, 1.5), "Full view"),
        ((-0.5, 0.5), (0.5, 1.5), "Upper boundary"),
        ((-0.2, 0.2), (0.8, 1.2), "Zoom 2×"),
        ((-0.05, 0.15), (0.92, 1.12), "Zoom 4×"),
        ((0.02, 0.10), (0.96, 1.04), "Zoom 8× — self-similar detail"),
    ]

    for x_range, y_range, label in zooms:
        w = cols - 6
        h = max(8, (rows - 14) // len(zooms)) * 2

        print(f"  \033[1mz³ − 1: {label}\033[0m")
        print(f"  x: [{x_range[0]:.4f}, {x_range[1]:.4f}]  y: [{y_range[0]:.4f}, {y_range[1]:.4f}]")

        grid = compute_fractal(poly_z3, ROOTS_Z3, x_range, y_range, w, h, 60)
        for line in render_half_block(grid, h, w):
            print(f"   {line}")
        print()


def gallery_mode():
    """Show all fractals."""
    z3_mode()
    print()
    z4_mode()
    print()
    z5_mode()
    print()
    custom_mode()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "z3"

    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  NEWTON FRACTALS\033[0m")
    print("  \033[1m  z → z − f(z)/f′(z) : Where Root-Finding Meets Chaos\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()
    print("  Newton's method for finding roots of polynomials. Each color")
    print("  is a basin of attraction — starting points that converge to")
    print("  the same root. The boundary between basins is fractal.")
    print()

    if mode == "z3":
        z3_mode()
    elif mode == "z4":
        z4_mode()
    elif mode == "z5":
        z5_mode()
    elif mode == "custom":
        custom_mode()
    elif mode == "zoom":
        zoom_mode()
    elif mode == "gallery":
        gallery_mode()
    else:
        print(f"  Unknown mode: {mode}")
        print(f"  Modes: z3, z4, z5, custom, zoom, gallery")
        return

    print()
    print("  ─────────────────────────────────────────────────────────")
    print("  Newton's method is the most common root-finding algorithm.")
    print("  It works brilliantly when it converges. But on the boundary")
    print("  between basins, it breaks — oscillating chaotically, never")
    print("  settling. The boundary between convergence and divergence")
    print("  is where the complexity lives. Again.")
    print()


if __name__ == "__main__":
    main()
