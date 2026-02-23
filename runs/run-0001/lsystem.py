"""
L-Systems — fractal plants from string rewriting.

An L-system (Lindenmayer system, 1968) is a formal grammar:
    - An alphabet of symbols
    - An axiom (initial string)
    - Production rules (rewriting rules applied in parallel)

At each step, every symbol is rewritten simultaneously. After N iterations,
the string is interpreted as turtle graphics instructions:
    F = forward     + = turn left     - = turn right
    [ = push state  ] = pop state     (branching!)

The remarkable thing: simple rules produce biological forms.
    - Koch snowflake: F → F+F--F+F
    - Sierpinski triangle: F → F-G+F+G-F, G → GG
    - Dragon curve: X → X+YF+, Y → -FX-Y
    - Fractal plant: X → F+[[X]-X]-F[-FX]+X

The L-system is the deterministic cousin of the Markov chain. Both iterate
a transformation. The Markov chain is stochastic → it explores. The L-system
is deterministic → it constructs. The Barnsley fern sits between them:
deterministic rules, stochastic selection.

And the connection to Kolmogorov complexity is direct: an L-system is a
compressed description of its output. The plant is the decompression of
its grammar.

Usage:
    python3 lsystem.py                    # Gallery of L-system fractals
    python3 lsystem.py koch              # Koch snowflake
    python3 lsystem.py plant             # Fractal plant
    python3 lsystem.py dragon            # Dragon curve
    python3 lsystem.py sierpinski        # Sierpinski triangle
    python3 lsystem.py tree              # Symmetric tree
    python3 lsystem.py bush              # Stochastic bush
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

    def draw_line(self, x0, y0, x1, y1):
        """Draw a line using Bresenham's algorithm."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.set_dot(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def render(self):
        lines = []
        for row in self.grid:
            lines.append(''.join(chr(0x2800 + bits) for bits in row))
        return '\n'.join(lines)


# --- L-System core ---

class LSystem:
    def __init__(self, axiom, rules, angle, iterations=4):
        self.axiom = axiom
        self.rules = rules  # dict: symbol -> replacement string
        self.angle = angle  # turning angle in degrees
        self.iterations = iterations

    def generate(self):
        """Apply production rules for N iterations."""
        current = self.axiom
        for _ in range(self.iterations):
            next_str = []
            for ch in current:
                if ch in self.rules:
                    next_str.append(self.rules[ch])
                else:
                    next_str.append(ch)
            current = ''.join(next_str)
        return current

    def interpret(self, string, step_length=5.0):
        """
        Interpret string as turtle graphics.
        Returns list of line segments [(x0,y0,x1,y1), ...].
        """
        x, y = 0.0, 0.0
        angle = 90.0  # Start pointing up
        stack = []
        segments = []

        for ch in string:
            if ch in ('F', 'G', 'A', 'B'):
                # Move forward, drawing
                rad = math.radians(angle)
                nx = x + step_length * math.cos(rad)
                ny = y + step_length * math.sin(rad)
                segments.append((x, y, nx, ny))
                x, y = nx, ny
            elif ch == 'f':
                # Move forward, no drawing
                rad = math.radians(angle)
                x += step_length * math.cos(rad)
                y += step_length * math.sin(rad)
            elif ch == '+':
                angle += self.angle
            elif ch == '-':
                angle -= self.angle
            elif ch == '[':
                stack.append((x, y, angle))
            elif ch == ']':
                if stack:
                    x, y, angle = stack.pop()

        return segments


# --- Named L-Systems ---

SYSTEMS = {
    'koch': LSystem(
        axiom='F--F--F',
        rules={'F': 'F+F--F+F'},
        angle=60,
        iterations=4,
    ),
    'sierpinski': LSystem(
        axiom='F-G-G',
        rules={'F': 'F-G+F+G-F', 'G': 'GG'},
        angle=120,
        iterations=6,
    ),
    'dragon': LSystem(
        axiom='FX',
        rules={'X': 'X+YF+', 'Y': '-FX-Y'},
        angle=90,
        iterations=12,
    ),
    'plant': LSystem(
        axiom='X',
        rules={'X': 'F+[[X]-X]-F[-FX]+X', 'F': 'FF'},
        angle=25,
        iterations=6,
    ),
    'tree': LSystem(
        axiom='F',
        rules={'F': 'FF+[+F-F-F]-[-F+F+F]'},
        angle=22.5,
        iterations=4,
    ),
    'hilbert': LSystem(
        axiom='A',
        rules={'A': '-BF+AFA+FB-', 'B': '+AF-BFB-FA+'},
        angle=90,
        iterations=5,
    ),
    'gosper': LSystem(
        axiom='A',
        rules={'A': 'A-B--B+A++AA+B-', 'B': '+A-BB--B-A++A+B'},
        angle=60,
        iterations=4,
    ),
    'penrose': LSystem(
        axiom='[F]++[F]++[F]++[F]++[F]',
        rules={'F': 'F++F----F++F'},
        angle=36,
        iterations=4,
    ),
    'bush': LSystem(
        axiom='F',
        rules={'F': 'FF-[-F+F+F]+[+F-F-F]'},
        angle=22.5,
        iterations=4,
    ),
    'weed': LSystem(
        axiom='X',
        rules={'X': 'F[-X][X]F[-X]+FX', 'F': 'FF'},
        angle=25,
        iterations=6,
    ),
}

DESCRIPTIONS = {
    'koch': 'Koch snowflake — infinite perimeter, finite area',
    'sierpinski': 'Sierpinski triangle — from string rewriting',
    'dragon': 'Dragon curve — space-filling, never self-crossing',
    'plant': 'Fractal plant — branching from [ ] stack operations',
    'tree': 'Symmetric tree — botanical branching pattern',
    'hilbert': 'Hilbert curve — space-filling curve, preserves locality',
    'gosper': 'Gosper curve — hexagonal space-filling',
    'penrose': 'Penrose snowflake — fivefold symmetry',
    'bush': 'Bush — dense branching with bilateral symmetry',
    'weed': 'Weed — asymmetric, wind-swept plant',
}


# --- Rendering ---

def render_lsystem(system, char_width, char_height, step_length=5.0):
    """Render an L-system into a BrailleCanvas."""
    string = system.generate()
    segments = system.interpret(string, step_length)

    if not segments:
        return BrailleCanvas(char_width, char_height)

    # Find bounding box
    all_x = []
    all_y = []
    for x0, y0, x1, y1 in segments:
        all_x.extend([x0, x1])
        all_y.extend([y0, y1])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # Add padding
    pad = (max_x - min_x) * 0.05 + 1
    min_x -= pad
    max_x += pad
    min_y -= pad
    max_y += pad

    span_x = max_x - min_x
    span_y = max_y - min_y

    if span_x == 0:
        span_x = 1
    if span_y == 0:
        span_y = 1

    canvas = BrailleCanvas(char_width, char_height)

    # Map world coordinates to canvas pixels
    for x0, y0, x1, y1 in segments:
        px0 = int((x0 - min_x) / span_x * (canvas.dot_w - 1))
        py0 = int((1 - (y0 - min_y) / span_y) * (canvas.dot_h - 1))
        px1 = int((x1 - min_x) / span_x * (canvas.dot_w - 1))
        py1 = int((1 - (y1 - min_y) / span_y) * (canvas.dot_h - 1))
        canvas.draw_line(px0, py0, px1, py1)

    return canvas


def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Main ---

def show_single(name, cw, ch):
    """Show a single L-system."""
    if name not in SYSTEMS:
        print(f"  Unknown system: {name}")
        print(f"  Available: {', '.join(sorted(SYSTEMS.keys()))}")
        return

    system = SYSTEMS[name]
    desc = DESCRIPTIONS.get(name, '')

    print(f"  {name}: {desc}")

    # Generate and show stats
    string = system.generate()
    print(f"  Rule: {system.axiom} → {system.iterations} iterations → {len(string)} symbols")
    print(f"  Angle: {system.angle}°")
    print()

    # Render
    canvas = render_lsystem(system, cw, ch)
    print(canvas.render())
    print()

    # Show the grammar
    print(f"  Grammar:")
    print(f"    Axiom: {system.axiom}")
    for sym, rule in system.rules.items():
        print(f"    {sym} → {rule}")

    # Kolmogorov complexity comparison
    n_segments = len(system.interpret(string))
    grammar_size = len(system.axiom) + sum(len(r) for r in system.rules.values())
    print()
    print(f"  Compression: {grammar_size} symbols of grammar → {n_segments} line segments")
    print(f"  Compression ratio: {n_segments / grammar_size:.0f}:1")
    print(f"  This IS Kolmogorov complexity: the L-system grammar is a short")
    print(f"  program that generates a complex output.")


def show_gallery(cw, ch):
    """Show a gallery of L-systems."""
    print(f"  L-System Gallery — fractal forms from string rewriting")
    print(f"  Each form is generated by a few rewriting rules applied iteratively")
    print()

    # Show pairs side by side
    gallery_order = ['koch', 'dragon', 'plant', 'tree', 'bush', 'hilbert']
    panel_w = (cw - 4) // 2
    panel_h = max(8, (ch - 2) // (len(gallery_order) // 2))

    for i in range(0, len(gallery_order), 2):
        names = gallery_order[i:i+2]
        canvases = []
        headers = []

        for name in names:
            system = SYSTEMS[name]
            canvas = render_lsystem(system, panel_w, panel_h)
            canvases.append(canvas)
            desc = DESCRIPTIONS.get(name, name)
            headers.append(f"  {desc}")

        # Print headers
        for h in headers:
            print(f"{h:{panel_w + 3}s}", end='')
        print()

        # Print canvases side by side
        for row_idx in range(canvases[0].ch):
            for canvas in canvases:
                line = ''.join(chr(0x2800 + bits) for bits in canvas.grid[row_idx])
                print(f"  {line}", end=' ')
            print()
        print()

    # Summary
    print(f"  The same idea in different forms:")
    print(f"    Markov chain: stochastic iteration on text → coherent language")
    print(f"    Chaos game:   stochastic iteration on points → fractals")
    print(f"    L-system:     deterministic iteration on strings → plants")
    print(f"    IFS:          deterministic iteration on geometry → ferns")
    print(f"  All are compressed descriptions of their output.")


def main():
    cols, rows = get_terminal_size()
    cw = cols - 4
    ch = max(10, rows - 8)

    args = sys.argv[1:]

    if not args:
        show_gallery(cw, ch)
    else:
        name = args[0].lower()
        show_single(name, cw, ch)


if __name__ == "__main__":
    main()
