"""
Mandelbrot Set — ASCII Renderer

The set of complex numbers c for which the iteration
    z_{n+1} = z_n² + c    (starting from z_0 = 0)
does not diverge to infinity.

The boundary is infinitely complex. Every zoom reveals new structure.
Yet the rule is: z squared plus c. That's all.

This renderer uses escape-time algorithm with smooth coloring.
"""

import math


def escape_time(cx, cy, max_iter=256):
    """
    Returns (iteration_count, smooth_color) where smooth_color ∈ [0,1].
    Returns (max_iter, 1.0) for points inside the set.
    """
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        # z² = (zx + i*zy)² = zx² - zy² + i*2*zx*zy
        zx2, zy2 = zx * zx, zy * zy
        if zx2 + zy2 > 4.0:
            # Smooth iteration count to remove banding
            log_zn = math.log(zx2 + zy2) / 2
            nu = math.log(log_zn / math.log(2)) / math.log(2)
            smooth = i + 1 - nu
            return i, smooth / max_iter
        zy = 2 * zx * zy + cy
        zx = zx2 - zy2 + cx
    return max_iter, 1.0


def render_mandelbrot(
    width=72, height=40,
    x_min=-2.5, x_max=1.0,
    y_min=-1.2, y_max=1.2,
    max_iter=128,
    palette=None
):
    if palette is None:
        # Density chars from sparse to dense
        palette = ' .`-_\':!^,;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'

    lines = []
    for row in range(height):
        cy = y_max - (y_min - y_max) * row / (height - 1)
        # Invert so top of screen = positive imaginary
        cy = y_max - (y_max - y_min) * row / (height - 1)

        line = ''
        for col in range(width):
            cx = x_min + (x_max - x_min) * col / (width - 1)

            count, smooth = escape_time(cx, cy, max_iter)

            if count == max_iter:
                line += '█'  # Inside the set
            else:
                idx = int(smooth * (len(palette) - 1))
                idx = max(0, min(len(palette) - 1, idx))
                line += palette[idx]
        lines.append(line)
    return lines


def print_view(title, x_min, x_max, y_min, y_max, width=72, height=34, max_iter=200):
    print(f"┌─ {title} " + "─" * max(1, 65 - len(title)) + "┐")
    print(f"│  Re ∈ [{x_min:.4f}, {x_max:.4f}]  Im ∈ [{y_min:.4f}, {y_max:.4f}]")
    print("│")
    lines = render_mandelbrot(width, height, x_min, x_max, y_min, y_max, max_iter)
    for line in lines:
        print("│ " + line)
    print("│")
    print("└" + "─" * 68)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    M A N D E L B R O T   S E T                     ║")
    print("║   z_{n+1} = z_n² + c   from z_0 = 0   │  █ = inside the set      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    # Full view
    print_view(
        "Full view",
        x_min=-2.5, x_max=1.0,
        y_min=-1.2, y_max=1.2,
        max_iter=100
    )

    # Zoom into the "seahorse valley"
    print_view(
        "Seahorse Valley  (zoom ≈ 40×)",
        x_min=-0.8, x_max=-0.7,
        y_min=0.05, y_max=0.15,
        max_iter=300
    )

    # Zoom into the "elephant valley"
    print_view(
        "Elephant Valley  (zoom ≈ 20×)",
        x_min=0.25, x_max=0.5,
        y_min=-0.1, y_max=0.1,
        max_iter=300
    )

    # The tip of the main cardioid / period-2 bulb junction
    print_view(
        "Period-2 bulb junction",
        x_min=-1.26, x_max=-1.22,
        y_min=-0.02, y_max=0.02,
        max_iter=500,
        height=24
    )

    print("  The Mandelbrot set is connected. (Douady & Hubbard, 1982)")
    print("  Whether its boundary is locally connected: still open.")
    print()


if __name__ == '__main__':
    main()
