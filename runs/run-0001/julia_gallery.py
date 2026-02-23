"""
Julia Set Gallery — the Mandelbrot set as a map of Julia sets.

The deep connection: each point c in the complex plane defines a Julia set
(the set of z where z → z² + c doesn't diverge). The Mandelbrot set is
the set of c values for which the Julia set is connected (a single piece
rather than dust).

This script renders a gallery of Julia sets sampled from different regions:
    - Inside the Mandelbrot set → connected Julia sets
    - Outside the Mandelbrot set → disconnected (Cantor dust)
    - On the boundary → infinitely complex, but still connected

Each Julia set has a "personality" determined by where c sits:
    - Near 0: circle (boring)
    - Main cardioid edge: fat, blobby shapes
    - Period-2 bulb: pinched figures
    - Filaments: dendrites and snowflakes
    - Deep in a bulb: nearly circular with n-fold symmetry

Usage:
    python3 julia_gallery.py            # Gallery of interesting Julia sets
    python3 julia_gallery.py boundary   # Julia sets from the boundary
"""

import sys
import os
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


# --- Julia set computation ---

def julia_escape(zr, zi, cr, ci, max_iter):
    for i in range(max_iter):
        zr2, zi2 = zr * zr, zi * zi
        if zr2 + zi2 > 4.0:
            return i
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return max_iter


def render_julia(cr, ci, cw, ch, max_iter=200, radius=1.8):
    """Render a Julia set into a BrailleCanvas."""
    canvas = BrailleCanvas(cw, ch)
    dot_w = canvas.dot_w
    dot_h = canvas.dot_h

    aspect = dot_w / dot_h
    x_radius = radius * aspect
    y_radius = radius

    for py in range(dot_h):
        zi = -y_radius + 2 * y_radius * py / dot_h
        for px in range(dot_w):
            zr = -x_radius + 2 * x_radius * px / dot_w
            iters = julia_escape(zr, zi, cr, ci, max_iter)
            if iters == max_iter:
                canvas.set_dot(px, py)

    return canvas


# --- Gallery ---

GALLERY = [
    # (cr, ci, name, description)
    (0.0, 0.0, "c = 0", "Circle (deep inside main cardioid)"),
    (-0.123, 0.745, "Douady rabbit", "Three-fold symmetry from period-3 bulb"),
    (-0.7, 0.27015, "Classic spiral", "Near main cardioid boundary"),
    (0.285, 0.01, "Near elephant", "Near the real axis, elephant valley"),
    (-0.8, 0.156, "Dendrite edge", "Branching filaments"),
    (-1.0, 0.0, "Basilica", "Two-fold symmetry from period-2 bulb"),
    (-0.4, 0.6, "Cantor dust", "Disconnected — c is outside Mandelbrot set"),
    (0.355, 0.355, "Near cusp", "Nearly disconnected, fine structure"),
    (-0.75, 0.0, "Parabolic", "At the cusp between cardioid and period-2"),
    (-0.1, 0.651, "Siegel disk", "Near a Siegel disk center"),
    (-1.476, 0.0, "Near tip", "Near the leftmost tip of the Mandelbrot set"),
    (0.0, 1.0, "Dendrite", "At the very top of the Mandelbrot set"),
]

BOUNDARY_GALLERY = [
    # Points right on the boundary of the Mandelbrot set
    (-0.75, 0.0, "Cusp point", "Boundary between cardioid and period-2"),
    (-1.25, 0.0, "Period-2 tip", "Tip of the period-2 bulb"),
    (0.25, 0.0, "Cardioid cusp", "Rightmost cusp of the main cardioid"),
    (-0.122561, 0.744862, "Period-3 boundary", "Edge of the period-3 bulb"),
    (-1.0, 0.266, "Boundary spiral", "Spiral structure on the boundary"),
    (0.0, 0.66, "Upper boundary", "Near the top of the Mandelbrot set"),
]


def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


def main():
    cols, rows = get_terminal_size()

    gallery = GALLERY
    if len(sys.argv) > 1 and sys.argv[1] == 'boundary':
        gallery = BOUNDARY_GALLERY

    # Render each Julia set at a size that fits 2 per row
    panel_cw = (cols - 6) // 2
    panel_ch = max(6, (rows - 4) // (len(gallery) // 2 + 1))

    print("  Julia Set Gallery — the Mandelbrot set as a map")
    print("  Each point c defines a Julia set; the Mandelbrot set tells us which are connected")
    print()

    # Render pairs side by side
    for i in range(0, len(gallery), 2):
        entries = gallery[i:i+2]
        canvases = []
        headers = []

        for cr, ci, name, desc in entries:
            canvas = render_julia(cr, ci, panel_cw, panel_ch)
            canvases.append(canvas)
            sign = "+" if ci >= 0 else ""
            headers.append(f"  {name} (c = {cr}{sign}{ci}i)")

        # Print headers
        for h in headers:
            print(f"{h:{panel_cw + 3}s}", end='')
        print()

        # Print canvases side by side
        for row_idx in range(canvases[0].ch):
            for cidx, canvas in enumerate(canvases):
                line = ''.join(chr(0x2800 + bits)
                               for bits in canvas.grid[row_idx])
                print(f"  {line}", end=' ')
            print()
        print()


if __name__ == "__main__":
    main()
