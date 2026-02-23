"""
Conway's Game of Life — a small universe that runs itself.

I like that this is one of the simplest possible systems that produces
genuinely surprising behavior. Four rules, infinite complexity.

Usage: python life.py [pattern]
Patterns: random, glider, rpentomino, acorn, gosper
"""

import sys
import time
import random
import os

W, H = 60, 30

def make_grid():
    return [[0]*W for _ in range(H)]

def neighbors(g, r, c):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r+dr) % H, (c+dc) % W
            count += g[nr][nc]
    return count

def step(g):
    new = make_grid()
    for r in range(H):
        for c in range(W):
            n = neighbors(g, r, c)
            if g[r][c]:
                new[r][c] = 1 if n in (2, 3) else 0
            else:
                new[r][c] = 1 if n == 3 else 0
    return new

def render(g, gen):
    lines = [f"  gen {gen}  |  alive: {sum(sum(row) for row in g)}"]
    lines.append("+" + "-"*W + "+")
    for row in g:
        lines.append("|" + "".join("\u2588" if c else " " for c in row) + "|")
    lines.append("+" + "-"*W + "+")
    return "\n".join(lines)

# --- patterns ---

def random_soup(g):
    for r in range(H):
        for c in range(W):
            g[r][c] = 1 if random.random() < 0.3 else 0

def stamp(g, cells, offset_r=None, offset_c=None):
    """Place a pattern centered on the grid (or at given offset)."""
    if offset_r is None:
        offset_r = H // 2 - len(cells) // 2
    if offset_c is None:
        offset_c = W // 2 - len(cells[0]) // 2
    for r, row in enumerate(cells):
        for c, val in enumerate(row):
            g[(offset_r + r) % H][(offset_c + c) % W] = val

def glider(g):
    stamp(g, [
        [0,1,0],
        [0,0,1],
        [1,1,1],
    ])

def rpentomino(g):
    stamp(g, [
        [0,1,1],
        [1,1,0],
        [0,1,0],
    ])

def acorn(g):
    stamp(g, [
        [0,1,0,0,0,0,0],
        [0,0,0,1,0,0,0],
        [1,1,0,0,1,1,1],
    ])

def gosper(g):
    """Gosper glider gun — produces a stream of gliders forever."""
    stamp(g, [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ], offset_r=2, offset_c=1)

PATTERNS = {
    "random": random_soup,
    "glider": glider,
    "rpentomino": rpentomino,
    "acorn": acorn,
    "gosper": gosper,
}

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "rpentomino"
    if name not in PATTERNS:
        print(f"Unknown pattern '{name}'. Choose from: {', '.join(PATTERNS)}")
        sys.exit(1)

    g = make_grid()
    PATTERNS[name](g)

    try:
        gen = 0
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            print(render(g, gen))
            print(f"\n  pattern: {name}  |  ctrl+c to quit")
            time.sleep(0.1)
            g = step(g)
            gen += 1
    except KeyboardInterrupt:
        print(f"\n  Stopped at generation {gen}.")

if __name__ == "__main__":
    main()
