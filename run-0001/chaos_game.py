"""
The Chaos Game — structure from randomness.

The algorithm:
    1. Pick N vertices of a polygon (start with a triangle)
    2. Pick a random starting point
    3. Pick a random vertex
    4. Move halfway toward it
    5. Plot the point
    6. Repeat from step 3

After enough iterations, a fractal appears. For a triangle with ratio 1/2,
you get the Sierpinski triangle — the same shape produced by Rule 90,
by Pascal's triangle mod 2, and by the XOR function on coordinates.

This is one of the most surprising results in mathematics: a purely random
process producing a perfectly self-similar fractal. The randomness doesn't
wash out the structure — it reveals it.

Different polygons and ratios produce different fractals:
    - Triangle, r=1/2:  Sierpinski triangle
    - Square, r=1/2:    fills the whole square (boring)
    - Square, r=1/2, no-repeat:  fractal carpet (forbid same vertex twice)
    - Pentagon, r=1/(1+φ): Sierpinski pentagon (φ = golden ratio)
    - Hexagon, r=1/3:   hexagonal fractal

Usage:
    python3 chaos_game.py                    # Sierpinski triangle
    python3 chaos_game.py pentagon            # Pentagon fractal
    python3 chaos_game.py square              # Square with no-repeat rule
    python3 chaos_game.py hexagon             # Hexagonal fractal
    python3 chaos_game.py fern               # Barnsley fern (IFS)
    python3 chaos_game.py all                # Side by side comparison
"""

import sys
import os
import math
import random


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


# --- Polygon vertices ---

def polygon_vertices(n, radius=1.0):
    """Generate vertices of a regular n-gon centered at origin."""
    verts = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2  # Start from top
        verts.append((radius * math.cos(angle), radius * math.sin(angle)))
    return verts


# --- Chaos game ---

def chaos_game(vertices, n_points, ratio=0.5, no_repeat=False,
               no_adjacent=False):
    """Run the chaos game and return list of (x, y) points.

    vertices: list of (x, y) polygon vertices
    n_points: number of points to generate
    ratio: fraction to move toward chosen vertex
    no_repeat: if True, can't choose same vertex twice in a row
    no_adjacent: if True, can't choose adjacent vertex to last one
    """
    n_verts = len(vertices)

    # Start at a random vertex
    x, y = vertices[random.randint(0, n_verts - 1)]

    points = []
    last = -1

    for _ in range(n_points):
        # Choose a vertex
        while True:
            idx = random.randint(0, n_verts - 1)
            if no_repeat and idx == last:
                continue
            if no_adjacent and last >= 0:
                if idx == (last + 1) % n_verts or idx == (last - 1) % n_verts:
                    continue
            break

        vx, vy = vertices[idx]
        x = x + ratio * (vx - x)
        y = y + ratio * (vy - y)
        points.append((x, y))
        last = idx

    return points


# --- Barnsley Fern (IFS - Iterated Function System) ---

def barnsley_fern(n_points):
    """Generate points of the Barnsley fern using an IFS.

    Four affine transformations with different probabilities:
    - Stem:      1% probability
    - Small leaf: 7%
    - Left leaf:  7%
    - Main body: 85%
    """
    x, y = 0.0, 0.0
    points = []

    for _ in range(n_points):
        r = random.random()
        if r < 0.01:
            # Stem
            nx = 0.0
            ny = 0.16 * y
        elif r < 0.08:
            # Smaller leaflet left
            nx = 0.20 * x - 0.26 * y
            ny = 0.23 * x + 0.22 * y + 1.6
        elif r < 0.15:
            # Smaller leaflet right
            nx = -0.15 * x + 0.28 * y
            ny = 0.26 * x + 0.24 * y + 0.44
        else:
            # Main
            nx = 0.85 * x + 0.04 * y
            ny = -0.04 * x + 0.85 * y + 1.6
        x, y = nx, ny
        points.append((x, y))

    return points


# --- Rendering ---

def render_points(points, canvas):
    """Plot points onto a braille canvas, auto-scaling to fit."""
    if not points:
        return canvas.render()

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xrange = xmax - xmin or 1
    yrange = ymax - ymin or 1

    # Uniform scale with padding
    pad = 0.02
    sx = canvas.dot_w * (1 - 2*pad) / xrange
    sy = canvas.dot_h * (1 - 2*pad) / yrange
    scale = min(sx, sy)

    cx = canvas.dot_w / 2
    cy = canvas.dot_h / 2
    xmid = (xmin + xmax) / 2
    ymid = (ymin + ymax) / 2

    for px, py in points:
        dx = int(cx + (px - xmid) * scale)
        dy = int(cy + (py - ymid) * scale)
        canvas.set_dot(dx, dy)

    return canvas.render()


# --- Named fractals ---

FRACTALS = {
    'sierpinski': {
        'desc': 'Sierpinski triangle',
        'vertices': 3,
        'ratio': 0.5,
        'points': 100000,
    },
    'pentagon': {
        'desc': 'Sierpinski pentagon',
        'vertices': 5,
        'ratio': 1 / (1 + (1 + math.sqrt(5)) / 2),  # 1/(1+φ)
        'points': 200000,
    },
    'square': {
        'desc': 'Square fractal (no-repeat rule)',
        'vertices': 4,
        'ratio': 0.5,
        'no_repeat': True,
        'points': 100000,
    },
    'hexagon': {
        'desc': 'Hexagonal fractal',
        'vertices': 6,
        'ratio': 1/3,
        'points': 200000,
    },
    'vicsek': {
        'desc': 'Vicsek fractal (square + center)',
        'vertices': 'vicsek',
        'ratio': 1/3,
        'points': 200000,
    },
}


# --- Terminal ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Commands ---

def cmd_fractal(name):
    """Render a named fractal."""
    cols, rows = get_terminal_size()
    cw = cols - 2
    ch = rows - 4

    if name == 'fern':
        n_points = 200000
        print(f"  Barnsley Fern  |  {n_points} points  |  IFS (Iterated Function System)")
        random.seed(42)
        points = barnsley_fern(n_points)
        canvas = BrailleCanvas(cw, ch)
        print(render_points(points, canvas))
        return

    f = FRACTALS[name]

    if f['vertices'] == 'vicsek':
        # Square vertices + center point
        verts = polygon_vertices(4)
        verts.append((0, 0))
    else:
        verts = polygon_vertices(f['vertices'])

    n_points = f['points']
    ratio = f['ratio']
    no_repeat = f.get('no_repeat', False)

    print(f"  Chaos Game: {f['desc']}  |  {n_points} points  |  r={ratio:.4f}")

    random.seed(42)
    points = chaos_game(verts, n_points, ratio=ratio, no_repeat=no_repeat)

    canvas = BrailleCanvas(cw, ch)
    print(render_points(points, canvas))


def cmd_all():
    """Show all fractals as thumbnails."""
    cols, rows = get_terminal_size()
    cw = (cols - 4) // 3
    ch = max(8, (rows - 6) // 2)

    names = ['sierpinski', 'pentagon', 'square', 'hexagon', 'fern']

    for name in names:
        random.seed(42)

        if name == 'fern':
            points = barnsley_fern(50000)
            label = "Barnsley Fern (IFS)"
        else:
            f = FRACTALS[name]
            if f['vertices'] == 'vicsek':
                verts = polygon_vertices(4) + [(0, 0)]
            else:
                verts = polygon_vertices(f['vertices'])
            points = chaos_game(verts, 50000, ratio=f['ratio'],
                                no_repeat=f.get('no_repeat', False))
            label = f['desc']

        canvas = BrailleCanvas(cols - 2, ch)
        print(f"\n  {label}")
        print(render_points(points, canvas))


def main():
    args = sys.argv[1:]

    if not args:
        cmd_fractal('sierpinski')
    elif args[0] == 'all':
        cmd_all()
    elif args[0] in FRACTALS:
        cmd_fractal(args[0])
    elif args[0] == 'fern':
        cmd_fractal('fern')
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
