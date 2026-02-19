"""
Lorenz attractor rendered with Unicode braille characters.

The braille block U+2800..U+28FF encodes a 2x4 dot grid per character cell,
giving effectively 2x horizontal and 4x vertical resolution. Each character
is an 8-bit pattern:

    (0,0) (1,0)      bit 0  bit 3
    (0,1) (1,1)      bit 1  bit 4
    (0,2) (1,2)      bit 2  bit 5
    (0,3) (1,3)      bit 6  bit 7

So braille_char = chr(0x2800 + dot_bits)

The Lorenz system:
    dx/dt = sigma * (y - x)
    dy/dt = x * (rho - z) - y
    dz/dt = x * y - beta * z

With the classic parameters (sigma=10, rho=28, beta=8/3), it produces the
famous butterfly-shaped strange attractor.

Usage: python lorenz.py [points] [spin]
  points: number of points to compute (default 100000)
  spin: if 'spin', animate rotation; if a number, fixed Y-axis rotation in degrees
"""

import sys
import math
import os
import time


# --- Lorenz integrator (RK4) ---

def lorenz(state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    x, y, z = state
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return (dx, dy, dz)


def rk4_step(state, dt, deriv_fn):
    k1 = deriv_fn(state)
    s2 = tuple(s + 0.5*dt*k for s, k in zip(state, k1))
    k2 = deriv_fn(s2)
    s3 = tuple(s + 0.5*dt*k for s, k in zip(state, k2))
    k3 = deriv_fn(s3)
    s4 = tuple(s + dt*k for s, k in zip(state, k3))
    k4 = deriv_fn(s4)
    return tuple(
        s + (dt/6.0)*(a + 2*b + 2*c + d)
        for s, a, b, c, d in zip(state, k1, k2, k3, k4)
    )


def generate_trajectory(n_points, dt=0.005):
    """Generate n_points on the Lorenz attractor."""
    state = (1.0, 1.0, 1.0)
    # skip transient
    for _ in range(500):
        state = rk4_step(state, dt, lorenz)

    points = []
    for _ in range(n_points):
        state = rk4_step(state, dt, lorenz)
        points.append(state)
    return points


# --- Braille canvas ---

class BrailleCanvas:
    """A canvas that renders to Unicode braille characters.

    Each character cell is 2 dots wide and 4 dots tall,
    so canvas resolution is (width*2, height*4) in dots.
    """

    # Bit positions for each dot within a braille character
    # (dx, dy) -> bit index
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
        """Set a single dot at pixel coordinates (x, y)."""
        if 0 <= x < self.dot_w and 0 <= y < self.dot_h:
            cx = x // 2
            cy = y // 4
            dx = x % 2
            dy = y % 4
            self.grid[cy][cx] |= self.DOT_BITS[(dx, dy)]

    def render(self):
        """Return the canvas as a string of braille characters."""
        lines = []
        for row in self.grid:
            lines.append(''.join(chr(0x2800 + bits) for bits in row))
        return '\n'.join(lines)


# --- 3D projection ---

def rotate_y(points, angle_deg):
    """Rotate points around the Y axis."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x*ca + z*sa, y, -x*sa + z*ca) for x, y, z in points]


def rotate_x(points, angle_deg):
    """Rotate points around the X axis."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(x, y*ca - z*sa, y*sa + z*ca) for x, y, z in points]


def project_and_render(points, canvas, angle_y=30, angle_x=15):
    """Project 3D points onto the braille canvas."""
    canvas.clear()

    # Apply rotations
    pts = rotate_x(points, angle_x)
    pts = rotate_y(pts, angle_y)

    # The Lorenz attractor lives roughly in:
    # x: [-20, 20], y: [-25, 25], z: [5, 45]
    # After rotation, we project x->screen_x, y->screen_y (ignoring z for parallel projection)

    # Find bounds of projected coordinates
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # Add margin
    xrange = xmax - xmin or 1
    yrange = ymax - ymin or 1

    # Scale to fit canvas with some padding
    pad = 0.05
    sx = canvas.dot_w * (1 - 2*pad) / xrange
    sy = canvas.dot_h * (1 - 2*pad) / yrange
    scale = min(sx, sy)  # uniform scaling to preserve aspect ratio

    # Center
    cx = canvas.dot_w / 2
    cy = canvas.dot_h / 2
    xmid = (xmin + xmax) / 2
    ymid = (ymin + ymax) / 2

    for px, py, pz in pts:
        dx = int(cx + (px - xmid) * scale)
        dy = int(cy + (py - ymid) * scale)
        canvas.set_dot(dx, dy)

    return canvas.render()


# --- Density rendering (more sophisticated) ---

def project_to_density(points, width, height, angle_y=30, angle_x=15):
    """Project 3D points and count density per pixel."""
    pts = rotate_x(points, angle_x)
    pts = rotate_y(pts, angle_y)

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xrange = xmax - xmin or 1
    yrange = ymax - ymin or 1

    pad = 0.05
    sx = width * (1 - 2*pad) / xrange
    sy = height * (1 - 2*pad) / yrange
    scale = min(sx, sy)

    cx_off = width / 2
    cy_off = height / 2
    xmid = (xmin + xmax) / 2
    ymid = (ymin + ymax) / 2

    density = [[0] * width for _ in range(height)]

    for px, py, pz in pts:
        dx = int(cx_off + (px - xmid) * scale)
        dy = int(cy_off + (py - ymid) * scale)
        if 0 <= dx < width and 0 <= dy < height:
            density[dy][dx] += 1

    return density


def density_to_block(density, width, height):
    """Render density map using block characters with varying intensity."""
    # Characters from empty to full, roughly ordered by visual density
    shades = ' ·∙•●'
    max_d = max(max(row) for row in density) or 1

    lines = []
    for row in density:
        line = []
        for val in row:
            idx = int((val / max_d) * (len(shades) - 1))
            line.append(shades[idx])
        lines.append(''.join(line))
    return '\n'.join(lines)


# --- Main ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


def main():
    n_points = 100000
    mode = 'static'
    angle = 25

    for arg in sys.argv[1:]:
        if arg == 'spin':
            mode = 'spin'
        elif arg == 'density':
            mode = 'density'
        else:
            try:
                val = int(arg)
                if val > 360:
                    n_points = val
                else:
                    angle = val
            except ValueError:
                try:
                    n_points = int(arg)
                except ValueError:
                    pass

    cols, rows = get_terminal_size()
    # Leave room for header/footer
    canvas_rows = rows - 4
    canvas_cols = cols - 2

    print(f"Computing {n_points} points on the Lorenz attractor...", flush=True)
    points = generate_trajectory(n_points)

    if mode == 'density':
        # Simple density rendering
        result = project_to_density(points, canvas_cols, canvas_rows, angle_y=angle, angle_x=15)
        os.system("cls" if os.name == "nt" else "clear")
        print(f"  Lorenz attractor  |  {n_points} points  |  density mode  |  angle: {angle}°")
        print(density_to_block(result, canvas_cols, canvas_rows))
        return

    if mode == 'spin':
        # Animated rotation
        canvas = BrailleCanvas(canvas_cols, canvas_rows)
        a = 0
        try:
            while True:
                frame = project_and_render(points, canvas, angle_y=a, angle_x=20)
                os.system("cls" if os.name == "nt" else "clear")
                print(f"  Lorenz attractor  |  {n_points} points  |  angle: {a:.0f}°  |  ctrl+c to quit")
                print(frame)
                a = (a + 2) % 360
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n  Stopped.")
        return

    # Static render
    canvas = BrailleCanvas(canvas_cols, canvas_rows)
    frame = project_and_render(points, canvas, angle_y=angle, angle_x=20)
    print(f"\n  Lorenz attractor  |  {n_points} points  |  angle: {angle}°")
    print(frame)


if __name__ == "__main__":
    main()
