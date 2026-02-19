"""
Elementary Cellular Automata — with focus on Rule 110.

An elementary cellular automaton is a 1D binary grid that evolves by a local
rule: each cell's next state depends on itself and its two neighbors.
There are 256 possible rules (2^8). They're numbered by encoding the output
table as a binary number.

Rule 110 is special: it's one of the simplest systems proven to be Turing-
complete. It can simulate any computation. It's a universal computer made
from a single row of bits and a lookup table with 8 entries.

This program renders the time evolution vertically — each row is one
generation, and you watch complexity emerge from a single cell.

Usage:
    python3 rule110.py              # Rule 110, single cell initial state
    python3 rule110.py 30           # Rule 30 (Wolfram's favorite)
    python3 rule110.py 90           # Rule 90 (Sierpinski triangle)
    python3 rule110.py 110 random   # Rule 110 with random initial state
    python3 rule110.py all          # Display all 256 rules as thumbnails
"""

import sys
import os
import random


def make_rule(n):
    """Create a rule function from a rule number (0-255).

    The rule number encodes the output for each of the 8 possible
    3-cell neighborhoods:
        111 -> bit 7
        110 -> bit 6
        101 -> bit 5
        100 -> bit 4
        011 -> bit 3
        010 -> bit 2
        001 -> bit 1
        000 -> bit 0
    """
    table = {}
    for i in range(8):
        pattern = ((i >> 2) & 1, (i >> 1) & 1, i & 1)
        table[pattern] = (n >> i) & 1
    return table


def step(cells, rule_table, wrap=True):
    """Evolve one generation."""
    n = len(cells)
    new = [0] * n
    for i in range(n):
        if wrap:
            left = cells[(i - 1) % n]
            right = cells[(i + 1) % n]
        else:
            left = cells[i - 1] if i > 0 else 0
            right = cells[i + 1] if i < n - 1 else 0
        new[i] = rule_table[(left, cells[i], right)]
    return new


def render_row(cells, chars=None):
    """Render a single row using block characters."""
    if chars is None:
        chars = (' ', '\u2588')  # space and full block
    return ''.join(chars[c] for c in cells)


def render_row_braille(row1, row2, row3, row4):
    """Combine 4 rows into braille characters (2 dots wide per char).

    Each braille character is 2 dots wide, 4 dots tall.
    We pack pairs of cells horizontally and groups of 4 vertically.
    """
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

    width = len(row1)
    chars = []
    for x in range(0, width, 2):
        bits = 0
        rows = [row1, row2, row3, row4]
        for dy, row in enumerate(rows):
            for dx in range(2):
                if x + dx < width and row[x + dx]:
                    bits |= DOT_BITS[(dx, dy)]
        chars.append(chr(0x2800 + bits))
    return ''.join(chars)


def run_automaton(rule_num, width, generations, init='single', wrap=False):
    """Run an elementary cellular automaton and collect all generations."""
    rule_table = make_rule(rule_num)

    cells = [0] * width
    if init == 'single':
        cells[width - 1] = 1  # single cell on the right
    elif init == 'random':
        cells = [random.randint(0, 1) for _ in range(width)]
    elif init == 'center':
        cells[width // 2] = 1

    history = [cells[:]]
    for _ in range(generations - 1):
        cells = step(cells, rule_table, wrap=wrap)
        history.append(cells[:])

    return history


def render_full(history):
    """Render with full block characters (1 cell = 1 character)."""
    return '\n'.join(render_row(row) for row in history)


def render_braille(history):
    """Render using braille characters (4x density vertically, 2x horizontally)."""
    lines = []
    empty_row = [0] * len(history[0])
    for i in range(0, len(history), 4):
        rows = []
        for j in range(4):
            if i + j < len(history):
                rows.append(history[i + j])
            else:
                rows.append(empty_row)
        lines.append(render_row_braille(*rows))
    return '\n'.join(lines)


def render_thumbnail(history, label=""):
    """Render a small thumbnail of a rule for the 'all' display."""
    lines = []
    if label:
        lines.append(f" {label:^18s} ")
    for row in history:
        lines.append(' ' + render_row(row, (' ', '\u2588')) + ' ')
    return lines


def display_all_rules():
    """Display all 256 rules as small thumbnails in a grid."""
    thumb_w = 21
    thumb_h = 12
    cols = 8

    print("  All 256 Elementary Cellular Automata Rules")
    print("  " + "=" * (cols * (thumb_w + 1)))
    print()

    for start in range(0, 256, cols):
        thumbnails = []
        for rule_num in range(start, min(start + cols, 256)):
            history = run_automaton(rule_num, thumb_w - 2, thumb_h, init='center')
            thumb = render_thumbnail(history, f"Rule {rule_num}")
            thumbnails.append(thumb)

        # Print side by side
        max_lines = max(len(t) for t in thumbnails)
        for line_idx in range(max_lines):
            parts = []
            for thumb in thumbnails:
                if line_idx < len(thumb):
                    parts.append(f"{thumb[line_idx]:{thumb_w}s}")
                else:
                    parts.append(" " * thumb_w)
            print(''.join(parts))
        print()


def main():
    rule_num = 110
    init = 'single'

    for arg in sys.argv[1:]:
        if arg == 'all':
            display_all_rules()
            return
        elif arg == 'random':
            init = 'random'
        elif arg == 'center':
            init = 'center'
        elif arg == 'single':
            init = 'single'
        else:
            try:
                rule_num = int(arg)
            except ValueError:
                pass

    cols, rows = 80, 24
    try:
        cols, rows = os.get_terminal_size()
    except (AttributeError, ValueError, OSError):
        pass

    # Use braille for compact rendering
    width = (cols - 2) * 2  # 2 dots per character
    generations = (rows - 4) * 4  # 4 rows per character line

    history = run_automaton(rule_num, width, generations, init=init)

    alive = sum(sum(row) for row in history)
    total = width * generations

    print(f"  Rule {rule_num}  |  {width}x{generations}  |  init: {init}  |  density: {alive/total:.1%}")
    print(render_braille(history))


if __name__ == "__main__":
    main()
