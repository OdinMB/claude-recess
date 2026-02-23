"""
Hybrid Systems — crossing the programs in this space.

What happens when you combine the ideas from different systems?

1. Sandpile CA: A cellular automaton where the update rule is sandpile
   toppling, applied synchronously. Unlike the standard BTW sandpile
   (which topples cells one at a time), this updates every cell in
   parallel. The result should be different — synchronous toppling
   creates feedback that asynchronous toppling doesn't.

2. DLA + L-system: Grow a DLA cluster, then trace its branches as
   an L-system string. The DLA produces the shape; interpreting it
   as a grammar produces... what? A compressed description of a
   random fractal?

3. Reaction-diffusion on a sandpile: Use the sandpile height map as
   initial conditions for a reaction-diffusion system. The fractal
   structure of the identity element should seed interesting patterns.

4. Markov L-system: Instead of deterministic production rules, use
   stochastic rules with probabilities learned from the corpus of
   text in this space. A language model that produces geometry.

This is the file where I try things without knowing what will happen.

Usage:
    python3 hybrid.py sandpile_ca      # Synchronous sandpile CA
    python3 hybrid.py markov_lsystem   # Stochastic L-system from text
    python3 hybrid.py all              # Try everything
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


# --- Synchronous Sandpile CA ---

class SyncSandpile:
    """
    A sandpile where ALL cells topple simultaneously.

    Standard sandpile: find one unstable cell, topple it, repeat.
    This: every cell with height >= 4 topples in the same step.

    The difference matters because in the synchronous version,
    neighbors can donate grains to each other simultaneously,
    creating interference patterns that don't exist in the
    asynchronous version.
    """

    def __init__(self, size):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]

    def fill(self, height):
        for r in range(self.size):
            for c in range(self.size):
                self.grid[r][c] = height

    def step(self):
        """One synchronous toppling step. Return number of topplings."""
        size = self.size
        grid = self.grid
        topplings = 0

        # Find all unstable cells and compute their contributions
        delta = [[0] * size for _ in range(size)]

        for r in range(size):
            for c in range(size):
                if grid[r][c] >= 4:
                    topple_count = grid[r][c] // 4
                    topplings += topple_count
                    delta[r][c] -= 4 * topple_count
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < size and 0 <= nc < size:
                            delta[nr][nc] += topple_count

        # Apply all changes simultaneously
        for r in range(size):
            for c in range(size):
                grid[r][c] += delta[r][c]

        return topplings

    def run_to_stable(self, max_steps=1000):
        """Run until stable or max steps. Return history of toppling counts."""
        history = []
        for _ in range(max_steps):
            t = self.step()
            history.append(t)
            if t == 0:
                break
        return history

    def max_height(self):
        return max(max(row) for row in self.grid)


def sync_sandpile_experiment():
    """
    Compare synchronous and asynchronous sandpile relaxation.
    Start with all-6 and relax. Do they reach the same fixed point?
    """
    size = 31
    cols, _ = get_terminal_size()
    cw = min(cols - 4, size * 2)
    ch = max(8, size // 2)

    print("  Synchronous Sandpile CA")
    print("  All cells topple simultaneously — what changes?")
    print()

    # Fill with 6 and relax synchronously
    pile = SyncSandpile(size)
    pile.fill(6)

    print(f"  Starting: {size}×{size} grid, all heights = 6")
    print(f"  Relaxing synchronously...")

    history = pile.run_to_stable(max_steps=500)

    print(f"  Stabilized in {len(history)} steps")
    print(f"  Total topplings: {sum(history)}")
    print(f"  Max height: {pile.max_height()}")
    print()

    # Render
    height_chars = {0: '  ', 1: '░░', 2: '▒▒', 3: '▓▓'}
    print("  Final state:")
    for row in pile.grid:
        line = '  '
        for h in row:
            line += height_chars.get(min(h, 3), '██')
        print(line)
    print()

    # Show convergence history
    print("  Topplings per step (first 30):")
    for i, t in enumerate(history[:30]):
        bar_len = min(50, int(50 * t / max(history)) if max(history) > 0 else 0)
        print(f"    {i:>3d}: {t:>6d} {'█' * bar_len}")
    if len(history) > 30:
        print(f"    ... ({len(history) - 30} more steps)")
    print()

    # Does it match the asynchronous identity?
    print("  Question: does synchronous relaxation of all-6 produce the")
    print("  same identity element as asynchronous relaxation?")
    print()

    # Quick check: compare totals
    total_grains = sum(sum(row) for row in pile.grid)
    expected_grains = size * size * 6 - sum(history) * 0  # grains fall off edges
    print(f"  Remaining grains: {total_grains} (started with {size*size*6})")


# --- Stochastic L-System from Text ---

def load_corpus():
    """Load all .md files as text."""
    import glob
    directory = os.path.dirname(os.path.abspath(__file__))
    texts = []
    for path in sorted(glob.glob(os.path.join(directory, '*.md'))):
        with open(path, 'r') as f:
            texts.append(f.read())
    return ' '.join(texts)


def text_to_lsystem_rules(text, n_rules=5):
    """
    Derive L-system-like rules from text statistics.

    Map frequent word patterns to turtle graphics operations:
    - Common words → F (forward, structure)
    - Rare words → + or - (turns, variation)
    - Punctuation → [ ] (branching)

    This is a deliberately strange mapping: language statistics
    generating geometry. What does the *shape* of a text look like?
    """
    words = text.split()

    # Count word frequencies
    freq = {}
    for w in words:
        w_clean = w.strip('.,;:!?()[]"\'').lower()
        if w_clean:
            freq[w_clean] = freq.get(w_clean, 0) + 1

    # Sort by frequency
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])

    # Map words to turtle commands
    word_map = {}
    total = len(sorted_words)

    for i, (word, count) in enumerate(sorted_words):
        frac = i / total if total > 0 else 0
        if frac < 0.05:  # Top 5% most common
            word_map[word] = 'F'
        elif frac < 0.15:
            word_map[word] = random.choice(['F', '+'])
        elif frac < 0.30:
            word_map[word] = random.choice(['+', '-'])
        elif frac < 0.50:
            word_map[word] = random.choice(['-', '+', 'F'])
        else:
            word_map[word] = random.choice(['+', '-', 'F', '[', ']'])

    # Force some branching
    for word in ['and', 'or', 'but', 'if', 'then', 'because']:
        if word in word_map:
            word_map[word] = '['
    for word in ['.', 'not', 'never', 'no', 'without']:
        if word in word_map:
            word_map[word] = ']'

    return word_map


def text_to_turtle(text, word_map, max_words=500, angle=15):
    """Convert text to turtle graphics string using word map."""
    words = text.split()[:max_words]
    commands = []
    bracket_depth = 0

    for w in words:
        w_clean = w.strip('.,;:!?()[]"\'').lower()
        if w_clean in word_map:
            cmd = word_map[w_clean]
            if cmd == '[':
                bracket_depth += 1
                commands.append(cmd)
            elif cmd == ']':
                if bracket_depth > 0:
                    bracket_depth -= 1
                    commands.append(cmd)
                else:
                    commands.append('-')  # Can't close unopened bracket
            else:
                commands.append(cmd)

    # Close any open brackets
    while bracket_depth > 0:
        commands.append(']')
        bracket_depth -= 1

    return ''.join(commands)


def interpret_turtle(string, step_length=5.0, angle_deg=15):
    """Interpret turtle graphics string."""
    x, y = 0.0, 0.0
    angle = 90.0
    stack = []
    segments = []

    for ch in string:
        if ch == 'F':
            rad = math.radians(angle)
            nx = x + step_length * math.cos(rad)
            ny = y + step_length * math.sin(rad)
            segments.append((x, y, nx, ny))
            x, y = nx, ny
        elif ch == '+':
            angle += angle_deg
        elif ch == '-':
            angle -= angle_deg
        elif ch == '[':
            stack.append((x, y, angle))
        elif ch == ']':
            if stack:
                x, y, angle = stack.pop()

    return segments


def render_segments(segments, cw, ch):
    """Render line segments to braille canvas."""
    if not segments:
        return BrailleCanvas(cw, ch).render()

    all_x = [x for seg in segments for x in (seg[0], seg[2])]
    all_y = [y for seg in segments for y in (seg[1], seg[3])]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    pad = max(max_x - min_x, max_y - min_y) * 0.05 + 1
    min_x -= pad; max_x += pad
    min_y -= pad; max_y += pad
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    canvas = BrailleCanvas(cw, ch)
    for x0, y0, x1, y1 in segments:
        px0 = int((x0 - min_x) / span_x * (canvas.dot_w - 1))
        py0 = int((1 - (y0 - min_y) / span_y) * (canvas.dot_h - 1))
        px1 = int((x1 - min_x) / span_x * (canvas.dot_w - 1))
        py1 = int((1 - (y1 - min_y) / span_y) * (canvas.dot_h - 1))
        canvas.draw_line(px0, py0, px1, py1)

    return canvas.render()


def markov_lsystem_experiment():
    """Map text statistics to turtle graphics and render the shape."""
    cols, rows = get_terminal_size()
    cw = cols - 4
    ch = max(12, rows - 12)

    print("  Markov L-System: what does text look like as geometry?")
    print()

    # Load corpus
    text = load_corpus()
    words = text.split()
    print(f"  Corpus: {len(words)} words from .md files")

    # Build word→command map
    random.seed(42)
    word_map = text_to_lsystem_rules(text)

    # Convert several essays to geometry
    import glob
    directory = os.path.dirname(os.path.abspath(__file__))
    md_files = sorted(glob.glob(os.path.join(directory, '*.md')))

    for path in md_files[:4]:
        name = os.path.basename(path)
        with open(path, 'r') as f:
            essay = f.read()

        turtle_str = text_to_turtle(essay, word_map, max_words=300, angle=15)

        # Count command types
        n_f = turtle_str.count('F')
        n_turn = turtle_str.count('+') + turtle_str.count('-')
        n_branch = turtle_str.count('[')

        segments = interpret_turtle(turtle_str, step_length=5.0, angle_deg=15)

        print(f"  {name}: {len(essay.split())} words → {len(turtle_str)} commands "
              f"(F:{n_f} turn:{n_turn} branch:{n_branch}) → {len(segments)} segments")
        print(render_segments(segments, cw, ch // 2))
        print()


# --- Utility ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Main ---

def main():
    args = sys.argv[1:]

    if not args or args[0] == 'all':
        sync_sandpile_experiment()
        print("\n" + "=" * 60 + "\n")
        markov_lsystem_experiment()
    elif args[0] == 'sandpile_ca':
        sync_sandpile_experiment()
    elif args[0] == 'markov_lsystem':
        markov_lsystem_experiment()
    else:
        print(f"  Unknown mode: {args[0]}")
        print(f"  Modes: sandpile_ca, markov_lsystem, all")


if __name__ == "__main__":
    main()
