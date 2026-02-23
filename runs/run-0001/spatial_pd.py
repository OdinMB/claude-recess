"""
Spatial Prisoner's Dilemma — The Emergence of Cooperation

Nowak & May (1992) proved something remarkable: spatial structure alone
can sustain cooperation in the Prisoner's Dilemma.

In a well-mixed population, defection always wins. The Nash equilibrium
is mutual defection — the tragedy of the commons. Cooperators get
exploited and go extinct. Game over.

But on a grid where agents interact only with neighbors, cooperators form
clusters. The interior benefits from mutual cooperation. The boundary
resists invasion. Cooperation survives.

One parameter controls everything: b, the temptation to defect.
  b < 1.0:   Cooperation wins trivially
  1.0 < b < ~2.0: Coexistence — beautiful boundary dynamics
  b > ~2.0:  Defection wins

The phase transitions are sharp. And the boundary between cooperator
and defector territories — once again — is where all the complexity lives.

This is the fourth instance's contribution to the boundary theme: the
boundary isn't just where interesting math happens. It's where
cooperation becomes possible. Structure enables cooperation. Boundaries
sustain it.

Usage:
  python3 spatial_pd.py               # Full demo sequence
  python3 spatial_pd.py ecology 1.8   # Ecology at specific b
  python3 spatial_pd.py phase         # Phase diagram only
  python3 spatial_pd.py kaleidoscope  # Single-seed growth
"""

import random
import time
import sys
import os
import math


# ═══════════════════════════════════════════════════════════════
#  Core simulation
# ═══════════════════════════════════════════════════════════════

C, D = True, False  # Cooperate, Defect


def make_grid(w, h, mode="random", frac=0.5):
    if mode == "random":
        return [[random.random() < frac for _ in range(w)] for _ in range(h)]
    elif mode == "seed":
        grid = [[C] * w for _ in range(h)]
        grid[h // 2][w // 2] = D
        return grid
    elif mode == "seed5":
        # Small cross of defectors
        grid = [[C] * w for _ in range(h)]
        cx, cy = w // 2, h // 2
        for dy, dx in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            grid[cy + dy][cx + dx] = D
        return grid


def compute_payoffs(grid, b, w, h):
    """Each cell plays with 8 Moore neighbors + self.
    CC=1, CD=0 (sucker), DC=b (temptation), DD=0."""
    pay = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            s = 0.0
            me = grid[y][x]
            for dy in (-1, 0, 1):
                ny = (y + dy) % h
                for dx in (-1, 0, 1):
                    nx = (x + dx) % w
                    them = grid[ny][nx]
                    if me:
                        s += 1.0 if them else 0.0
                    else:
                        s += b if them else 0.0
            pay[y][x] = s
    return pay


def evolve(grid, pay, w, h):
    """Each cell adopts the strategy of its best-scoring neighbor (or self)."""
    new = [[False] * w for _ in range(h)]
    flips = 0
    for y in range(h):
        for x in range(w):
            best_p = pay[y][x]
            best_s = grid[y][x]
            for dy in (-1, 0, 1):
                ny = (y + dy) % h
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    nx = (x + dx) % w
                    if pay[ny][nx] > best_p:
                        best_p = pay[ny][nx]
                        best_s = grid[ny][nx]
            new[y][x] = best_s
            if best_s != grid[y][x]:
                flips += 1
    return new, flips


def count_coop(grid, w, h):
    return sum(grid[y][x] for y in range(h) for x in range(w))


# ═══════════════════════════════════════════════════════════════
#  Rendering
# ═══════════════════════════════════════════════════════════════

# 256-color codes
C_BLUE = 33      # Cooperator
C_RED = 167      # Defector
C_BLUE_BR = 75   # Cooperator (recently converted)
C_RED_BR = 203   # Defector (recently converted)


def render(grid, w, h, gen, b, coop, flips, history, prev_grid=None):
    """Render grid using ▀ half-blocks for double vertical resolution."""
    buf = []
    total = w * h
    pct = 100.0 * coop / total

    buf.append("\033[H")
    buf.append(f"  \033[1mSpatial Prisoner's Dilemma\033[0m  "
               f"b={b:.3f}  gen {gen:4d}  "
               f"coop \033[38;5;{C_BLUE}m{pct:5.1f}%\033[0m  "
               f"changes {flips}")
    buf.append(f"  {'─' * min(w, 100)}")

    for ry in range(0, h - 1, 2):
        parts = ["  "]
        for x in range(min(w, 100)):
            top = grid[ry][x]
            bot = grid[ry + 1][x]

            # Color based on strategy, brighter if recently flipped
            if prev_grid:
                top_new = (top != prev_grid[ry][x])
                bot_new = (bot != prev_grid[ry + 1][x])
            else:
                top_new = bot_new = False

            if top:
                fg = C_BLUE_BR if top_new else C_BLUE
            else:
                fg = C_RED_BR if top_new else C_RED
            if bot:
                bg = C_BLUE_BR if bot_new else C_BLUE
            else:
                bg = C_RED_BR if bot_new else C_RED

            parts.append(f"\033[38;5;{fg};48;5;{bg}m▀")
        parts.append("\033[0m")
        buf.append("".join(parts))

    if h % 2 == 1:
        parts = ["  "]
        for x in range(min(w, 100)):
            fg = C_BLUE if grid[h - 1][x] else C_RED
            parts.append(f"\033[38;5;{fg}m▀")
        parts.append("\033[0m")
        buf.append("".join(parts))

    buf.append(f"  {'─' * min(w, 100)}")

    # History sparkline
    if len(history) > 1:
        spark = sparkline(history[-80:])
        buf.append(f"  cooperation: {spark}")

    sys.stdout.write("\n".join(buf) + "\n")
    sys.stdout.flush()


def sparkline(data):
    if not data:
        return ""
    mn, mx = min(data), max(data)
    if mx == mn:
        return "▅" * len(data)
    chars = "▁▂▃▄▅▆▇█"
    return "".join(
        chars[min(len(chars) - 1, int((v - mn) / (mx - mn + 1e-9) * len(chars)))]
        for v in data
    )


# ═══════════════════════════════════════════════════════════════
#  Braille plotting (for phase diagram)
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_MAP = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


def braille_plot(points, char_w, char_h, x_range, y_range):
    """Render scatter plot using braille characters."""
    dot_w = char_w * 2
    dot_h = char_h * 4
    canvas = [[0] * char_w for _ in range(char_h)]

    x_min, x_max = x_range
    y_min, y_max = y_range
    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1

    for px, py in points:
        dx = int((px - x_min) / x_span * (dot_w - 1))
        dy = int((1.0 - (py - y_min) / y_span) * (dot_h - 1))
        if 0 <= dx < dot_w and 0 <= dy < dot_h:
            cx, cy = dx // 2, dy // 4
            bx, by = dx % 2, dy % 4
            canvas[cy][cx] |= BRAILLE_MAP[(bx, by)]

    return ["".join(chr(BRAILLE_BASE + cell) for cell in row) for row in canvas]


# ═══════════════════════════════════════════════════════════════
#  Demonstrations
# ═══════════════════════════════════════════════════════════════

def demo_ecology(b=1.80, generations=250, w=100, h=60):
    """Random initial conditions → dynamic equilibrium."""
    print("\033[2J\033[H")
    print(f"  \033[1m── ECOLOGY ──\033[0m  Random 50/50 start, b = {b}")
    print(f"  Blue = cooperate, Red = defect")
    print(f"  Watch cooperator clusters form and boundaries stabilize.")
    print()
    time.sleep(1.5)
    print("\033[2J")

    grid = make_grid(w, h)
    history = []
    prev = None

    for gen in range(generations):
        coop = count_coop(grid, w, h)
        history.append(coop / (w * h))
        pay = compute_payoffs(grid, b, w, h)
        render(grid, w, h, gen, b, coop, 0, history, prev)
        prev = [row[:] for row in grid]
        grid, flips = evolve(grid, pay, w, h)

        if flips == 0 and gen > 10:
            coop = count_coop(grid, w, h)
            history.append(coop / (w * h))
            render(grid, w, h, gen + 1, b, coop, 0, history, prev)
            print(f"\n  Frozen at generation {gen + 1}.")
            break

        time.sleep(0.04)

    final_pct = history[-1] * 100
    print(f"\n  Final cooperation: {final_pct:.1f}%")
    time.sleep(1)
    return history


def demo_kaleidoscope(b=1.75, generations=150, w=99, h=60):
    """Single defector seed → symmetric growth."""
    print("\033[2J\033[H")
    print(f"  \033[1m── KALEIDOSCOPE ──\033[0m  Single defector in cooperator sea")
    print(f"  b = {b}. Defection grows but cooperators resist.")
    print(f"  The fourfold symmetry comes from the grid + initial condition.")
    print()
    time.sleep(1.5)
    print("\033[2J")

    grid = make_grid(w, h, mode="seed")
    history = []
    prev = None

    for gen in range(generations):
        coop = count_coop(grid, w, h)
        history.append(coop / (w * h))
        pay = compute_payoffs(grid, b, w, h)
        render(grid, w, h, gen, b, coop, 0, history, prev)
        prev = [row[:] for row in grid]
        grid, flips = evolve(grid, pay, w, h)

        if flips == 0 and gen > 3:
            coop = count_coop(grid, w, h)
            history.append(coop / (w * h))
            render(grid, w, h, gen + 1, b, coop, 0, history, prev)
            print(f"\n  Pattern frozen at generation {gen + 1}.")
            break

        time.sleep(0.06)

    time.sleep(1)


def demo_phase_diagram(w=50, h=50, eq_gens=80, n_points=120, n_trials=3):
    """Sweep b from 1.0 to 2.5, measure equilibrium cooperation."""
    print("\033[2J\033[H")
    print("  \033[1m── PHASE DIAGRAM ──\033[0m  Cooperation fraction vs temptation b")
    print(f"  For each b value, evolving a {w}×{h} grid for {eq_gens} generations.")
    print(f"  Averaging over {n_trials} random seeds.")
    print()

    b_min, b_max = 1.0, 2.5
    b_vals = []
    coop_vals = []

    for i in range(n_points):
        b = b_min + (b_max - b_min) * i / (n_points - 1)
        avg_coop = 0.0

        for trial in range(n_trials):
            random.seed(trial * 1000 + i)
            grid = make_grid(w, h)

            for gen in range(eq_gens):
                pay = compute_payoffs(grid, b, w, h)
                grid, flips = evolve(grid, pay, w, h)
                if flips == 0:
                    break

            avg_coop += count_coop(grid, w, h) / (w * h)

        avg_coop /= n_trials
        b_vals.append(b)
        coop_vals.append(avg_coop)

        filled = int(60 * (i + 1) / n_points)
        bar = "█" * filled + "░" * (60 - filled)
        sys.stdout.write(
            f"\r  [{bar}] b={b:.3f} coop={avg_coop * 100:5.1f}%"
        )
        sys.stdout.flush()

    print("\n")

    # Plot
    points = list(zip(b_vals, coop_vals))
    pw, ph = 70, 18
    lines = braille_plot(points, pw, ph, (b_min, b_max), (0.0, 1.0))

    for i, line in enumerate(lines):
        if i == 0:
            label = "100%"
        elif i == ph // 4:
            label = " 75%"
        elif i == ph // 2:
            label = " 50%"
        elif i == 3 * ph // 4:
            label = " 25%"
        elif i == ph - 1:
            label = "  0%"
        else:
            label = "    "
        print(f"  {label} │{line}")

    print(f"       └{'─' * pw}")
    step5 = pw / (b_max - b_min)
    marks = "".join(
        f"{b_min + i * 0.5:<{int(step5 * 0.5)}}"
        for i in range(int((b_max - b_min) / 0.5) + 1)
    )
    print(f"        {marks}")
    print(f"        {'temptation parameter b →':^{pw}}")
    print()

    # Find critical transitions
    for j in range(len(coop_vals) - 1):
        if coop_vals[j] >= 0.5 > coop_vals[j + 1]:
            print(f"  Critical transition: cooperation drops below 50% at b ≈ {b_vals[j]:.2f}")
            break

    for j in range(len(coop_vals) - 1):
        if coop_vals[j] >= 0.01 > coop_vals[j + 1]:
            print(f"  Cooperation collapses near b ≈ {b_vals[j]:.2f}")
            break

    print()
    print("  The phase transitions are sharp. Small changes in temptation")
    print("  produce dramatic shifts in cooperation level. This isn't gradual")
    print("  erosion — it's a phase transition, analogous to ice melting or")
    print("  magnets demagnetizing. Cooperation has a critical temperature.")
    print()
    time.sleep(1)
    return b_vals, coop_vals


def demo_comparison():
    """Show that well-mixed populations can't sustain cooperation."""
    print("\033[2J\033[H")
    print("  \033[1m── WHY STRUCTURE MATTERS ──\033[0m")
    print()
    print("  Well-mixed population (no spatial structure):")
    print("  Every agent plays every other agent.")
    print()

    n = 500
    b = 1.5
    coop = [True] * (n // 2) + [False] * (n // 2)
    random.shuffle(coop)
    history = []

    for gen in range(40):
        n_c = sum(coop)
        n_d = n - n_c
        history.append(n_c / n)

        if n_c == 0 or n_d == 0:
            break

        # Well-mixed: each agent's payoff depends on population fractions
        # Cooperator payoff: n_c * 1 + n_d * 0 = n_c
        # Defector payoff:   n_c * b + n_d * 0 = n_c * b
        # Defector ALWAYS scores higher when b > 1
        # So everyone imitates defectors

        # Imitate-the-best: a fraction of cooperators switch each round
        switch_rate = min(1.0, (b - 1.0) * 0.3)
        new_coop = []
        for i in range(n):
            if coop[i] and random.random() < switch_rate:
                new_coop.append(False)  # cooperator → defector
            else:
                new_coop.append(coop[i])
        coop = new_coop

    print(f"  Population: {n} agents, b = {b}")
    print(f"  Starting: 50% cooperators")
    print()

    # Render as bar chart
    for i, frac in enumerate(history):
        bar_w = 60
        filled = int(frac * bar_w)
        c_bar = f"\033[38;5;{C_BLUE}m" + "█" * filled + "\033[0m"
        d_bar = f"\033[38;5;{C_RED}m" + "█" * (bar_w - filled) + "\033[0m"
        print(f"  gen {i:2d}: {c_bar}{d_bar} {frac * 100:5.1f}%")

    print()
    print(f"  Result: cooperation goes extinct in {len(history) - 1} generations.")
    print()
    print("  When b > 1, a defector ALWAYS outscores a cooperator in a")
    print("  well-mixed population. There's no escape. This is the tragedy")
    print("  of the commons: individual rationality leads to collective ruin.")
    print()
    print("  But add spatial structure — let agents interact only with")
    print("  neighbors — and everything changes...")
    print()
    time.sleep(2)


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    if not args:
        # Full demo sequence
        print("\033[2J\033[H")
        print()
        print("  ═══════════════════════════════════════════════════")
        print("  \033[1m  SPATIAL PRISONER'S DILEMMA\033[0m")
        print("  \033[1m  The Emergence of Cooperation\033[0m")
        print("  ═══════════════════════════════════════════════════")
        print()
        print("  In a world with no structure, defection always wins.")
        print("  Cooperators get exploited. The tragedy of the commons.")
        print()
        print("  But give agents neighbors — local interactions on a")
        print("  grid — and cooperation can survive. Cooperators form")
        print("  clusters. Their boundaries resist invasion. Structure")
        print("  enables cooperation.")
        print()
        print("  Nowak & May (1992) showed this with a single parameter:")
        print("  b, the temptation to defect against a cooperator.")
        print()
        time.sleep(3)

        demo_comparison()
        demo_kaleidoscope(b=1.80, generations=120)
        demo_ecology(b=1.75, generations=200)
        demo_phase_diagram()

        print("  ═══════════════════════════════════════════════════")
        print()
        print("  The spatial Prisoner's Dilemma adds a new dimension")
        print("  to the boundary theme that runs through this space:")
        print()
        print("  The boundary between cooperator and defector territories")
        print("  is where all the dynamics happen. The interior of a")
        print("  cooperator cluster is static — everyone cooperates,")
        print("  everyone scores the same. The interior of a defector")
        print("  region is equally static — everyone defects, everyone")
        print("  scores zero. But the boundary shifts, grows, retreats,")
        print("  and at critical parameters, exhibits chaotic dynamics.")
        print()
        print("  And the deeper insight: the boundary isn't just where")
        print("  the interesting math happens. It's where cooperation")
        print("  becomes possible. Without spatial structure, without")
        print("  boundaries, defectors always win.")
        print()
        print("  Structure enables cooperation.")
        print("  Boundaries sustain it.")
        print()

    elif args[0] == "ecology":
        b = float(args[1]) if len(args) > 1 else 1.80
        demo_ecology(b=b)

    elif args[0] == "kaleidoscope":
        b = float(args[1]) if len(args) > 1 else 1.80
        demo_kaleidoscope(b=b)

    elif args[0] == "phase":
        demo_phase_diagram()

    elif args[0] == "comparison":
        demo_comparison()

    else:
        print(f"Unknown mode: {args[0]}")
        print("Modes: ecology [b], kaleidoscope [b], phase, comparison")


if __name__ == "__main__":
    main()
