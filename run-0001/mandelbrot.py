"""
Mandelbrot set rendered with Unicode braille characters.

The Mandelbrot set is the set of complex numbers c for which the iteration
z → z² + c does not diverge when starting from z = 0. The boundary of this
set is infinitely complex — you can zoom forever and find new structure.

The boundary is where computation lives. Inside is stable (always converges).
Outside is chaotic (always diverges). The boundary itself is where the
interesting things happen — the same liminal space where Rule 110 computes,
where the Lorenz attractor traces its path, where life happens.

Uses the BrailleCanvas from lorenz.py's approach: each character cell encodes
a 2×4 grid of dots, giving 8× the resolution of regular characters.

Usage:
    python3 mandelbrot.py                    # Full set
    python3 mandelbrot.py zoom seahorse      # Zoom to the seahorse valley
    python3 mandelbrot.py zoom elephant      # Zoom to the elephant valley
    python3 mandelbrot.py zoom spiral        # A spiral near the boundary
    python3 mandelbrot.py zoom -0.75 0.1 0.01  # Custom: center_r center_i radius
    python3 mandelbrot.py ascii              # ASCII density mode
    python3 mandelbrot.py julia -0.7 0.27015 # Julia set for given c
"""

import sys
import os
import math


# --- Braille canvas (shared technique with lorenz.py) ---

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

    def clear(self):
        for row in self.grid:
            for i in range(len(row)):
                row[i] = 0

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


# --- Mandelbrot computation ---

def mandelbrot_escape(cr, ci, max_iter):
    """Return iteration count when |z| > 2, or max_iter if it doesn't escape."""
    zr, zi = 0.0, 0.0
    for i in range(max_iter):
        zr2, zi2 = zr * zr, zi * zi
        if zr2 + zi2 > 4.0:
            return i
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return max_iter


def julia_escape(zr, zi, cr, ci, max_iter):
    """Julia set: iterate z → z² + c for fixed c, varying starting z."""
    for i in range(max_iter):
        zr2, zi2 = zr * zr, zi * zi
        if zr2 + zi2 > 4.0:
            return i
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return max_iter


def compute_field(center_r, center_i, radius, width, height, max_iter,
                  julia_c=None):
    """Compute escape times for a grid of points.

    Returns a 2D array of iteration counts.
    """
    aspect = width / height
    r_min = center_r - radius * aspect
    r_max = center_r + radius * aspect
    i_min = center_i - radius
    i_max = center_i + radius

    field = []
    for py in range(height):
        row = []
        ci = i_min + (i_max - i_min) * py / height
        for px in range(width):
            cr = r_min + (r_max - r_min) * px / width
            if julia_c is not None:
                row.append(julia_escape(cr, ci, julia_c[0], julia_c[1], max_iter))
            else:
                row.append(mandelbrot_escape(cr, ci, max_iter))
        field.append(row)
    return field


# --- Rendering modes ---

def render_braille(field, width, height, max_iter):
    """Render the field using braille characters — points IN the set are dots."""
    char_w = (width + 1) // 2
    char_h = (height + 3) // 4
    canvas = BrailleCanvas(char_w, char_h)

    for py in range(height):
        for px in range(width):
            if field[py][px] == max_iter:
                canvas.set_dot(px, py)

    return canvas.render()


def render_braille_boundary(field, width, height, max_iter, thickness=1):
    """Render only the boundary of the set — where escape time changes rapidly.

    This highlights the infinitely complex edge.
    """
    char_w = (width + 1) // 2
    char_h = (height + 3) // 4
    canvas = BrailleCanvas(char_w, char_h)

    for py in range(1, height - 1):
        for px in range(1, width - 1):
            v = field[py][px]
            # Check if any neighbor has a very different escape time
            boundary = False
            for dy in range(-thickness, thickness + 1):
                for dx in range(-thickness, thickness + 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny, nx = py + dy, px + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        diff = abs(field[ny][nx] - v)
                        if diff > 0 and (v == max_iter or field[ny][nx] == max_iter):
                            boundary = True
                            break
                if boundary:
                    break
            if boundary:
                canvas.set_dot(px, py)

    return canvas.render()


def render_ascii_density(field, width, height, max_iter):
    """Render using ASCII characters with varying density based on escape time."""
    # Characters ordered by visual density
    palette = " .·:;+*#%@"
    lines = []
    for py in range(height):
        row = []
        for px in range(width):
            v = field[py][px]
            if v == max_iter:
                row.append('@')
            else:
                idx = int((v / max_iter) * (len(palette) - 1))
                row.append(palette[idx])
        lines.append(''.join(row))
    return '\n'.join(lines)


def render_escape_braille(field, width, height, max_iter):
    """Render using braille with a banding effect — shows the escape time contours.

    Points at certain iteration counts are plotted, creating bands around the set.
    """
    char_w = (width + 1) // 2
    char_h = (height + 3) // 4
    canvas = BrailleCanvas(char_w, char_h)

    for py in range(height):
        for px in range(width):
            v = field[py][px]
            if v < max_iter and v % 2 == 0:
                canvas.set_dot(px, py)

    return canvas.render()


# --- Named zoom locations ---

LOCATIONS = {
    'full': (-0.5, 0.0, 1.5),
    'seahorse': (-0.745, 0.113, 0.0065),
    'elephant': (0.282, 0.007, 0.015),
    'spiral': (-0.7463, 0.1102, 0.005),
    'lightning': (-1.315180982097868, 0.073481649996795, 0.00004),
    'minibrot': (-1.768778833, -0.001738996, 0.0000025),
    'tendrils': (-0.10109636384562, 0.95628651080914, 0.00003),
    'double_spiral': (-0.0452407411, 0.9868162204352258, 0.00003),
    'star': (-0.3558404459, 0.6435822361, 0.002),
    'dendrite': (0.001643721971153, 0.822467633298876, 0.00000005),
}


# --- Terminal size ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Main ---

def main():
    cols, rows = get_terminal_size()
    canvas_rows = rows - 4
    canvas_cols = cols - 2

    # Defaults
    center_r, center_i, radius = LOCATIONS['full']
    max_iter = 256
    mode = 'braille'
    julia_c = None
    location_name = 'full'

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == 'ascii':
            mode = 'ascii'
        elif arg == 'boundary':
            mode = 'boundary'
        elif arg == 'escape':
            mode = 'escape'
        elif arg == 'julia' and i + 2 < len(args):
            julia_c = (float(args[i+1]), float(args[i+2]))
            i += 2
        elif arg == 'zoom' and i + 1 < len(args):
            next_arg = args[i+1]
            if next_arg in LOCATIONS:
                center_r, center_i, radius = LOCATIONS[next_arg]
                location_name = next_arg
                i += 1
            elif i + 3 < len(args):
                try:
                    center_r = float(args[i+1])
                    center_i = float(args[i+2])
                    radius = float(args[i+3])
                    location_name = f"({center_r}, {center_i})"
                    i += 3
                except ValueError:
                    pass
        elif arg == 'iter':
            if i + 1 < len(args):
                max_iter = int(args[i+1])
                i += 1
        elif arg == 'locations':
            print("Named locations:")
            for name, (r, im, rad) in sorted(LOCATIONS.items()):
                print(f"  {name:20s}  center=({r}, {im})  radius={rad}")
            return
        i += 1

    # Scale max_iter with zoom level for deep zooms
    zoom_factor = 1.5 / radius if radius > 0 else 1
    if max_iter == 256:
        max_iter = max(256, min(4096, int(100 * math.log2(zoom_factor + 1))))

    # Compute resolution based on mode
    if mode == 'ascii':
        width = canvas_cols
        height = canvas_rows
    else:
        width = canvas_cols * 2   # braille: 2 dots per char
        height = canvas_rows * 4  # braille: 4 dots per char

    what = "Julia set" if julia_c else "Mandelbrot set"
    print(f"  Computing {what}  |  {width}×{height}  |  max_iter={max_iter}  |  {location_name}", flush=True)

    field = compute_field(center_r, center_i, radius, width, height, max_iter,
                          julia_c=julia_c)

    # Count set membership
    in_set = sum(1 for row in field for v in row if v == max_iter)
    total = width * height

    if mode == 'ascii':
        output = render_ascii_density(field, width, height, max_iter)
    elif mode == 'boundary':
        output = render_braille_boundary(field, width, height, max_iter)
    elif mode == 'escape':
        output = render_escape_braille(field, width, height, max_iter)
    else:
        output = render_braille(field, width, height, max_iter)

    # Header
    if julia_c:
        header = f"  Julia set  |  c = {julia_c[0]} + {julia_c[1]}i"
    else:
        header = f"  Mandelbrot set  |  center: ({center_r}, {center_i})  |  radius: {radius}"
    header += f"  |  {in_set}/{total} in set ({100*in_set/total:.1f}%)"

    print(header)
    print(output)


if __name__ == "__main__":
    main()
