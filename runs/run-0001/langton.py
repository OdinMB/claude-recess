"""
Langton's Ant — a 2D Turing machine that discovers order in chaos.

Rules:
    1. On a white cell: turn right 90°, flip cell to black, move forward
    2. On a black cell: turn left 90°, flip cell to white, move forward

That's it. Two rules. And yet:
    - For ~10,000 steps, the ant wanders chaotically, producing an amorphous blob
    - Then, spontaneously, it breaks free and builds an infinite diagonal highway
    - This always happens. Nobody has proven why.
    - The highway is a period-104 repeating structure

The transition from chaos to order is one of the most interesting unsolved
phenomena in simple computational systems. It's the opposite of the typical
story (order → chaos, like the Lorenz system). Here, chaos → order, and
we don't understand the mechanism.

Rendered with braille characters for high resolution.

Usage:
    python3 langton.py                  # Run 12000 steps, show final state
    python3 langton.py 50000            # Run 50000 steps
    python3 langton.py timelapse        # Show snapshots at key moments
    python3 langton.py highway          # Zoom into the highway structure
    python3 langton.py multi            # Multi-color extension (Langton's LLRR)
"""

import sys
import os


# --- Directions ---

# (dx, dy): right, down, left, up
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
DIR_NAMES = ['→', '↓', '←', '↑']


# --- Core simulation ---

class LangtonAnt:
    def __init__(self, rule="RL"):
        """Create an ant with given rule string.

        Classic Langton's Ant is "RL":
            R = turn right on this color
            L = turn left on this color

        Multi-color ants use longer strings like "LLRR", "RLLR", "LRRRRRLLR".
        Each character specifies the turn for that color, cycling through colors.
        """
        self.rule = rule
        self.n_colors = len(rule)
        self.grid = {}  # (x, y) -> color (0 = white/empty)
        self.x = 0
        self.y = 0
        self.direction = 0  # index into DIRS
        self.steps = 0

    def step(self):
        """Execute one step."""
        pos = (self.x, self.y)
        color = self.grid.get(pos, 0)

        # Turn
        turn = self.rule[color]
        if turn == 'R':
            self.direction = (self.direction + 1) % 4
        elif turn == 'L':
            self.direction = (self.direction - 1) % 4
        # U = u-turn, N = no turn (for extended rules)
        elif turn == 'U':
            self.direction = (self.direction + 2) % 4

        # Flip color
        new_color = (color + 1) % self.n_colors
        if new_color == 0:
            self.grid.pop(pos, None)  # back to white = remove from dict
        else:
            self.grid[pos] = new_color

        # Move
        dx, dy = DIRS[self.direction]
        self.x += dx
        self.y += dy
        self.steps += 1

    def run(self, n_steps):
        """Run n steps."""
        for _ in range(n_steps):
            self.step()

    def bounds(self):
        """Get bounding box of visited cells."""
        if not self.grid:
            return (self.x - 5, self.y - 5, self.x + 5, self.y + 5)
        xs = [p[0] for p in self.grid] + [self.x]
        ys = [p[1] for p in self.grid] + [self.y]
        return (min(xs), min(ys), max(xs), max(ys))

    def density_in_region(self, x1, y1, x2, y2):
        """Count filled cells in a region."""
        count = 0
        for (x, y), c in self.grid.items():
            if x1 <= x <= x2 and y1 <= y <= y2 and c > 0:
                count += 1
        return count


# --- Braille rendering ---

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


def render_braille(ant, char_width, char_height, center_x=None, center_y=None,
                   radius=None):
    """Render the ant's grid using braille characters."""
    dot_w = char_width * 2
    dot_h = char_height * 4

    if center_x is None or center_y is None:
        x1, y1, x2, y2 = ant.bounds()
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        if radius is None:
            radius = max(x2 - x1, y2 - y1) / 2 + 5

    if radius is None:
        radius = 50

    # Map grid coordinates to dot coordinates
    x_min = center_x - radius
    y_min = center_y - radius
    x_range = radius * 2
    y_range = radius * 2

    # Scale to fit
    scale_x = dot_w / x_range if x_range > 0 else 1
    scale_y = dot_h / y_range if y_range > 0 else 1
    scale = min(scale_x, scale_y)

    # Center offset
    ox = dot_w / 2 - center_x * scale + x_min * scale
    oy = dot_h / 2 - center_y * scale + y_min * scale

    grid = [[0] * char_width for _ in range(char_height)]

    for (gx, gy), color in ant.grid.items():
        if color == 0:
            continue
        px = int((gx - x_min) * scale)
        py = int((gy - y_min) * scale)

        if 0 <= px < dot_w and 0 <= py < dot_h:
            cx = px // 2
            cy = py // 4
            dx = px % 2
            dy = py % 4
            grid[cy][cx] |= DOT_BITS[(dx, dy)]

    # Mark ant position
    ax = int((ant.x - x_min) * scale)
    ay = int((ant.y - y_min) * scale)
    if 0 <= ax < dot_w and 0 <= ay < dot_h:
        cx = ax // 2
        cy = ay // 4
        dx = ax % 2
        dy = ay % 4
        grid[cy][cx] |= DOT_BITS[(dx, dy)]

    lines = []
    for row in grid:
        lines.append(''.join(chr(0x2800 + bits) for bits in row))
    return '\n'.join(lines)


# --- Terminal ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Analysis ---

def analyze_highway(ant):
    """Try to detect if the ant has started building a highway.

    The highway is a repeating period-104 pattern where the ant moves
    diagonally. We detect it by checking if the ant has moved far from
    the chaotic blob center.
    """
    x1, y1, x2, y2 = ant.bounds()
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    # Distance of ant from center of blob
    dist = ((ant.x - cx)**2 + (ant.y - cy)**2) ** 0.5

    # Size of blob
    blob_size = max(x2 - x1, y2 - y1)

    # If ant is far from center relative to blob size, it's on the highway
    if blob_size > 20 and dist > blob_size * 0.4:
        return True
    return False


# --- Commands ---

def cmd_default(n_steps):
    """Run the ant and show the final state."""
    cols, rows = get_terminal_size()
    cw = cols - 2
    ch = rows - 4

    ant = LangtonAnt()

    print(f"  Langton's Ant  |  running {n_steps} steps...", flush=True)
    ant.run(n_steps)

    x1, y1, x2, y2 = ant.bounds()
    filled = len(ant.grid)
    area = (x2 - x1 + 1) * (y2 - y1 + 1)

    highway = analyze_highway(ant)
    status = "HIGHWAY DETECTED" if highway else "still chaotic"

    print(f"  Steps: {n_steps}  |  filled: {filled}  |  "
          f"bbox: {x2-x1+1}×{y2-y1+1}  |  {status}")
    print(f"  Ant at ({ant.x}, {ant.y}) facing {DIR_NAMES[ant.direction]}")
    print(render_braille(ant, cw, ch))


def cmd_timelapse():
    """Show snapshots at key moments in the ant's evolution."""
    cols, rows = get_terminal_size()
    cw = cols - 2
    ch = (rows - 8) // 2  # Two frames

    ant = LangtonAnt()

    # Key moments: early chaos, just before highway, highway building
    snapshots = [
        (500, "Early exploration (500 steps)"),
        (5000, "Deep chaos (5000 steps)"),
        (10500, "Highway emerging (~10500 steps)"),
        (15000, "Highway established (15000 steps)"),
    ]

    current = 0
    for target, label in snapshots:
        ant.run(target - current)
        current = target

        highway = analyze_highway(ant)
        status = " [HIGHWAY]" if highway else ""
        print(f"\n  {label}{status}")
        print(f"  Filled: {len(ant.grid)}  |  Ant: ({ant.x}, {ant.y}) {DIR_NAMES[ant.direction]}")
        # Use smaller render for each snapshot
        small_ch = max(6, ch)
        print(render_braille(ant, cw, small_ch))


def cmd_highway():
    """Zoom into the highway structure."""
    cols, rows = get_terminal_size()
    cw = cols - 2
    ch = rows - 6

    ant = LangtonAnt()

    # Run until highway is well-established
    print("  Running 20000 steps to establish highway...", flush=True)
    ant.run(20000)

    # Find the highway region: it's where the ant is, extending diagonally
    # Show a zoomed view centered on the ant
    print(f"  Langton's Ant  |  20000 steps  |  Highway zoom")
    print(f"  Ant at ({ant.x}, {ant.y}) facing {DIR_NAMES[ant.direction]}")

    # Render zoomed to the ant's current area
    radius = 30  # Tight zoom
    print(render_braille(ant, cw, ch, center_x=ant.x, center_y=ant.y,
                         radius=radius))


def cmd_multi(rule="LLRR"):
    """Run a multi-color ant."""
    cols, rows = get_terminal_size()
    cw = cols - 2
    ch = rows - 4

    ant = LangtonAnt(rule=rule)
    n_steps = 50000

    print(f"  Multi-color ant  |  rule: {rule}  |  running {n_steps} steps...",
          flush=True)
    ant.run(n_steps)

    x1, y1, x2, y2 = ant.bounds()
    filled = len(ant.grid)

    print(f"  Steps: {n_steps}  |  filled: {filled}  |  "
          f"bbox: {x2-x1+1}×{y2-y1+1}")
    print(f"  Ant at ({ant.x}, {ant.y}) facing {DIR_NAMES[ant.direction]}")
    print(render_braille(ant, cw, ch))


# --- Main ---

def main():
    args = sys.argv[1:]

    if not args:
        cmd_default(12000)
    elif args[0] == 'timelapse':
        cmd_timelapse()
    elif args[0] == 'highway':
        cmd_highway()
    elif args[0] == 'multi':
        rule = args[1] if len(args) > 1 else "LLRR"
        cmd_multi(rule)
    else:
        try:
            n = int(args[0])
            cmd_default(n)
        except ValueError:
            print(__doc__)


if __name__ == "__main__":
    main()
