"""
Conway's Game of Life

A 2D cellular automaton. Each cell is alive or dead.
Rules (apply simultaneously to all cells):
  1. Live cell with 2 or 3 live neighbors → survives
  2. Live cell with <2 neighbors → dies (underpopulation)
  3. Live cell with >3 neighbors → dies (overpopulation)
  4. Dead cell with exactly 3 neighbors → becomes alive (reproduction)

John Conway (1937–2020) invented this in 1970. It was published in
Martin Gardner's Scientific American column.

Surprising consequences:
  - Gliders (move across the grid)
  - Oscillators (return to original state after N steps)
  - Glider guns (produce infinite streams of gliders)
  - Self-reproducing patterns exist
  - Turing complete (Rendell, 2002)

This file shows several famous patterns running for multiple generations.
"""

def step(alive):
    """One generation. alive is a set of (row, col) tuples."""
    # Count neighbors for all relevant cells
    neighbor_count = {}
    for r, c in alive:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                neighbor_count[(nr, nc)] = neighbor_count.get((nr, nc), 0) + 1

    new_alive = set()
    for cell, count in neighbor_count.items():
        if count == 3 or (count == 2 and cell in alive):
            new_alive.add(cell)

    return new_alive


def run(alive, generations):
    """Run for N generations, return list of states."""
    states = [alive]
    for _ in range(generations):
        alive = step(alive)
        states.append(alive)
    return states


def render(alive, min_r, min_c, max_r, max_c, alive_char='█', dead_char=' '):
    """Render a state to a list of strings."""
    lines = []
    for r in range(min_r, max_r + 1):
        line = ''
        for c in range(min_c, max_c + 1):
            line += alive_char if (r, c) in alive else dead_char
        lines.append(line)
    return lines


def bounding_box(states):
    """Find bounding box across all states."""
    all_cells = set().union(*states)
    if not all_cells:
        return 0, 0, 0, 0
    rows = [r for r, c in all_cells]
    cols = [c for r, c in all_cells]
    return min(rows), min(cols), max(rows), max(cols)


def parse_pattern(lines, offset_r=0, offset_c=0):
    """Parse ASCII pattern where '#' or 'O' or '█' = alive."""
    alive = set()
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch in '#O█*':
                alive.add((r + offset_r, c + offset_c))
    return alive


def show_evolution(name, description, initial, generations, cols_per_row=4, spacing=2):
    """Show a pattern evolving over N generations."""
    states = run(initial, generations)
    min_r, min_c, max_r, max_c = bounding_box(states)
    # Add a small margin
    margin = 2
    min_r -= margin
    min_c -= margin
    max_r += margin
    max_c += margin

    width = max_c - min_c + 1
    height = max_r - min_r + 1

    print(f"┌─ {name} " + "─" * max(1, 65 - len(name)) + "┐")
    print(f"│  {description}")
    print(f"│  {generations+1} generations  (height={height}, width={width})")
    print("│")

    # Show generations in rows
    gen_per_row = min(cols_per_row, generations + 1)
    sep = "  │  "

    gen = 0
    while gen <= generations:
        batch = list(range(gen, min(gen + gen_per_row, generations + 1)))

        # Header
        header = "│ "
        for g in batch:
            label = f"gen {g}"
            header += label + ' ' * max(0, width - len(label))
            if g != batch[-1]:
                header += sep
        print(header)

        # Render each generation side by side
        rendered = [render(states[g], min_r, min_c, max_r, max_c) for g in batch]
        for row_idx in range(height):
            line = "│ "
            for i, lines in enumerate(rendered):
                line += lines[row_idx]
                if i < len(rendered) - 1:
                    line += sep
            print(line)

        print("│")
        gen += gen_per_row

    print("└" + "─" * 72)
    print()


# ── Famous patterns ──────────────────────────────────────────────────────────

# Still lifes (don't change)
BLOCK = parse_pattern([
    "##",
    "##",
], offset_r=0, offset_c=0)

BEEHIVE = parse_pattern([
    ".##.",
    "#..#",
    ".##.",
])

LOAF = parse_pattern([
    ".##.",
    "#..#",
    ".#.#",
    "..#.",
])

# Oscillators
BLINKER = parse_pattern(["###"])

TOAD = parse_pattern([
    ".###",
    "###.",
])

BEACON = parse_pattern([
    "##..",
    "##..",
    "..##",
    "..##",
])

PULSAR = parse_pattern([
    "..#####...",
    "..#...#...",
    "..#...#...",
    "..#####...",
    "..........",
    "..........",
    "..#####...",
    "..#...#...",
    "..#...#...",
    "..#####...",
])

# More common pulsar form
PULSAR2 = parse_pattern([
    "..###...###..",
    ".............",
    "#....#.#....#",
    "#....#.#....#",
    "#....#.#....#",
    "..###...###..",
    ".............",
    "..###...###..",
    "#....#.#....#",
    "#....#.#....#",
    "#....#.#....#",
    ".............",
    "..###...###..",
])

# Glider (period 4, moves diagonally)
GLIDER = parse_pattern([
    ".#.",
    "..#",
    "###",
])

# Lightweight spaceship (moves horizontally)
LWSS = parse_pattern([
    ".#..#",
    "#....",
    "#...#",
    "####.",
])

# R-pentomino (long-lived methuselah — lives for 1103 generations)
R_PENTOMINO = parse_pattern([
    ".##",
    "##.",
    ".#.",
])

# Gosper glider gun (first discovered period-30 oscillator that grows forever)
GOSPER_GUN = parse_pattern([
    "........................#...........",
    "......................#.#...........",
    "............##......##............##",
    "...........#...#....##............##",
    "##........#.....#...##..............",
    "##........#...#.##....#.#...........",
    "..........#.....#.......#...........",
    "...........#...#.....................",
    "............##......................",
])


def life_stats(states, name):
    """Print population statistics over generations."""
    pops = [len(s) for s in states]
    print(f"  {name}: population over {len(states)-1} generations")
    print(f"  min={min(pops)}  max={max(pops)}  final={pops[-1]}")
    # Sparkline
    if max(pops) > 0:
        spark_chars = '▁▂▃▄▅▆▇█'
        spark = ''.join(
            spark_chars[int(p / max(pops) * (len(spark_chars)-1))]
            for p in pops
        )
        print(f"  {spark}")
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║            C O N W A Y ' S   G A M E   O F   L I F E               ║")
    print("║  Four rules. Infinite complexity. Turing complete.                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    # Still lifes
    show_evolution(
        "Block (still life)",
        "Stable 2×2 square — the simplest still life",
        BLOCK, generations=4, cols_per_row=5
    )

    show_evolution(
        "Beehive (still life)",
        "Another common stable configuration",
        BEEHIVE, generations=4, cols_per_row=5
    )

    # Oscillators
    show_evolution(
        "Blinker (period 2)",
        "Three cells in a row — alternates between horizontal and vertical",
        BLINKER, generations=5, cols_per_row=6
    )

    show_evolution(
        "Toad (period 2)",
        "Two offset rows of three cells — blinks between two states",
        TOAD, generations=5, cols_per_row=6
    )

    show_evolution(
        "Beacon (period 2)",
        "Two diagonal blocks — corner cells turn on and off",
        BEACON, generations=5, cols_per_row=6
    )

    # Glider
    show_evolution(
        "Glider (period 4, diagonal motion)",
        "Discovered by Richard Guy. Travels diagonally at c/4.",
        GLIDER, generations=16, cols_per_row=4
    )

    # LWSS
    show_evolution(
        "Lightweight Spaceship (period 4, horizontal)",
        "Smallest spaceship. Travels horizontally at c/2.",
        LWSS, generations=8, cols_per_row=4
    )

    # R-pentomino (show first 20 generations of this long-lived pattern)
    print("┌─ R-pentomino (methuselah) " + "─" * 46 + "┐")
    print("│  5 initial cells. Lives for 1,103 generations before stabilizing.")
    print("│  Final state: 116 cells — 8 gliders, 4 blocks, 1 boat, 1 ship, .....")
    print("│")
    r_states = run(R_PENTOMINO, 50)
    life_stats(r_states, "R-pentomino (50 gen)")
    # Show selected generations
    selected = [0, 5, 10, 20, 30, 50]
    min_r, min_c, max_r, max_c = bounding_box(r_states)
    margin = 1
    for g in selected:
        lines = render(r_states[g], min_r-margin, min_c-margin, max_r+margin, max_c+margin)
        pop = len(r_states[g])
        print(f"│  gen {g:3d}  (population: {pop})")
        for line in lines:
            print("│  " + line)
        print("│")
    print("└" + "─" * 72)
    print()

    # Gosper Glider Gun (abbreviated view)
    print("┌─ Gosper Glider Gun ─────────────────────────────────────────────────┐")
    print("│  Period 30. The first pattern known to grow unboundedly.")
    print("│  Discovered by Bill Gosper in 1970 as a $50 prize-winning answer.")
    print("│  Each period: emits one glider. Population grows forever.")
    print("│")
    gun_states = run(GOSPER_GUN, 90)
    life_stats(gun_states, "Gosper Gun (90 gen)")
    # Show gen 0, 30, 60, 90
    gun_bb = bounding_box(gun_states)
    gr0, gc0, gr1, gc1 = gun_bb
    for g in [0, 30, 60, 90]:
        lines = render(gun_states[g], gr0-1, gc0-1, gr1+1, gc1+1)
        pop = len(gun_states[g])
        print(f"│  gen {g:3d}  (population: {pop})")
        for line in lines[:20]:  # Limit height
            print("│  " + line[:65])
        if len(lines) > 20:
            print(f"│  ... ({len(lines)-20} more rows)")
        print("│")
    print("└" + "─" * 72)
    print()

    print("  Conway's Game of Life: invented 1970. Proven Turing complete: 2002.")
    print("  The glider gun allowed construction of logic gates from colliding gliders.")
    print("  Self-replicating patterns exist (first found: ~2010s).")
    print()


if __name__ == '__main__':
    main()
