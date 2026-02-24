"""
Lindenmayer Systems (L-systems)

A formal grammar that rewrites strings — invented by biologist Aristid
Lindenmayer in 1968 to model plant growth. The startling thing is how
biological the output looks even though the rules are purely mechanical.

Turtle graphics interpretation:
    F = draw forward
    f = move forward (no draw)
    + = turn left by angle δ
    - = turn right by angle δ
    [ = push state (branch start)
    ] = pop state (branch end)

Each system here runs for N iterations then renders to ASCII.
"""

import math


def rewrite(axiom, rules, iterations):
    s = axiom
    for _ in range(iterations):
        s = ''.join(rules.get(c, c) for c in s)
    return s


def turtle_to_lines(string, angle_deg, start_x=0.0, start_y=0.0, start_angle=90.0):
    """Convert L-system string to list of line segments via turtle interpretation."""
    x, y = start_x, start_y
    angle = start_angle  # degrees, 0=right, 90=up
    stack = []
    lines = []
    angle_rad = math.radians(angle_deg)

    for c in string:
        if c in ('F', 'f', 'A', 'B', 'X', 'Y', '0', '1'):  # forward-drawing chars
            nx = x + math.cos(math.radians(angle))
            ny = y + math.sin(math.radians(angle))
            if c not in ('f',):  # 'f' moves without drawing
                lines.append((x, y, nx, ny))
            x, y = nx, ny
        elif c == '+':
            angle += angle_deg
        elif c == '-':
            angle -= angle_deg
        elif c == '[':
            stack.append((x, y, angle))
        elif c == ']':
            x, y, angle = stack.pop()

    return lines


def render_to_ascii(lines, width=70, height=40):
    """Project line segments to ASCII grid."""
    if not lines:
        return ["(empty)"]

    # Find bounds
    all_x = [x for x, y, nx, ny in lines for x in [x, nx]]
    all_y = [y for x, y, nx, ny in lines for y in [y, ny]]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1

    # Maintain aspect ratio (terminal chars are ~2x taller than wide)
    aspect = span_x / span_y
    effective_width = width
    effective_height = height

    margin = 2
    def to_col(x):
        return int((x - min_x) / span_x * (effective_width - 2*margin)) + margin
    def to_row(y):
        # Invert y (screen y goes down)
        return int((max_y - y) / span_y * (effective_height - 2*margin)) + margin

    grid = [[' '] * (effective_width + margin) for _ in range(effective_height + margin)]

    for x0, y0, x1, y1 in lines:
        # Bresenham's line
        c0, r0 = to_col(x0), to_row(y0)
        c1, r1 = to_col(x1), to_row(y1)
        dc, dr = c1 - c0, r1 - r0
        steps = max(abs(dc), abs(dr), 1)
        for i in range(steps + 1):
            c = c0 + int(dc * i / steps)
            r = r0 + int(dr * i / steps)
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                # Choose char based on direction
                if abs(dc) > abs(dr) * 2:
                    grid[r][c] = '─'
                elif abs(dr) > abs(dc) * 2:
                    grid[r][c] = '│'
                elif (dc > 0 and dr < 0) or (dc < 0 and dr > 0):
                    grid[r][c] = '/'
                else:
                    grid[r][c] = '\\'

    return [''.join(row) for row in grid]


SYSTEMS = {
    "Koch Snowflake": {
        "description": "n=4  Infinite perimeter, finite area",
        "axiom": "F--F--F",
        "rules": {"F": "F+F--F+F"},
        "angle": 60,
        "iterations": 4,
    },
    "Dragon Curve": {
        "description": "n=12  Fold a paper strip in half, repeatedly",
        "axiom": "FX",
        "rules": {"X": "X+YF+", "Y": "-FX-Y"},
        "angle": 90,
        "iterations": 12,
    },
    "Sierpinski Triangle": {
        "description": "n=7  Self-similar fractal triangle",
        "axiom": "F-G-G",
        "rules": {"F": "F-G+F+G-F", "G": "GG"},
        "angle": 120,
        "iterations": 6,
    },
    "Plant 1 (Fractal Bush)": {
        "description": "n=5  Branching plant structure",
        "axiom": "X",
        "rules": {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        "angle": 25,
        "iterations": 5,
    },
    "Gosper Curve": {
        "description": "n=4  Space-filling flowsnake",
        "axiom": "A",
        "rules": {"A": "A-B--B+A++AA+B-", "B": "+A-BB--B-A++A+B"},
        "angle": 60,
        "iterations": 4,
    },
    "Hilbert Curve": {
        "description": "n=5  Space-filling curve (visits every point)",
        "axiom": "A",
        "rules": {"A": "+BF-AFA-FB+", "B": "-AF+BFB+FA-"},
        "angle": 90,
        "iterations": 5,
    },
}


def main():
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║              L I N D E N M A Y E R   S Y S T E M S                     ║")
    print("║  String rewriting rules that accidentally describe nature               ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print()

    for name, system in SYSTEMS.items():
        print(f"┌─ {name} {'─' * max(1, 60 - len(name))}┐")
        print(f"│  {system['description']}")
        print(f"│  Axiom: {system['axiom']}  │  Rules: {', '.join(f'{k}→{v}' for k,v in system['rules'].items())}  │  δ={system['angle']}°")
        print("│")

        string = rewrite(system['axiom'], system['rules'], system['iterations'])
        lines = turtle_to_lines(string, system['angle'])

        rows = render_to_ascii(lines, width=72, height=28)
        for row in rows:
            print("│ " + row[:72])

        print(f"│  String length after {system['iterations']} iterations: {len(string):,} chars")
        print("└" + "─" * 75)
        print()


if __name__ == '__main__':
    main()
