"""
The Collatz Conjecture — Hailstones of Mathematics

Take any positive integer n.
  If n is even:  n → n/2
  If n is odd:   n → 3n + 1

Repeat. Conjecture: you always reach 1.

Nobody can prove it. Nobody can find a counterexample.
Paul Erdős said "Mathematics is not yet ready for such problems."
It's been open since 1937.

The sequences are called "hailstone numbers" — like hailstones
in a thundercloud, they bounce up and down erratically before
eventually falling to earth. The 3n+1 step launches a number
upward (roughly tripling it); the n/2 step brings it back down.
Sometimes a number rises to incredible heights before collapsing.

27 reaches 9232 before returning to 1 (takes 111 steps).
The number 27 is small. Its journey is not.

Usage:
    python3 collatz.py                   # Overview
    python3 collatz.py trajectory 27     # Single trajectory
    python3 collatz.py stopping          # Stopping time scatter
    python3 collatz.py records           # Record-holding numbers
    python3 collatz.py binary 27         # Binary evolution
"""

import sys
import os
import math


# ═══════════════════════════════════════════════════════════════
#  Collatz computation
# ═══════════════════════════════════════════════════════════════

def collatz_step(n):
    if n % 2 == 0:
        return n // 2
    return 3 * n + 1


def trajectory(n):
    """Return the full sequence from n to 1."""
    seq = [n]
    while n != 1:
        n = collatz_step(n)
        seq.append(n)
    return seq


def stopping_time(n):
    """Count steps to reach 1."""
    steps = 0
    while n != 1:
        n = collatz_step(n)
        steps += 1
    return steps


# ═══════════════════════════════════════════════════════════════
#  Braille canvas
# ═══════════════════════════════════════════════════════════════

BRAILLE_BASE = 0x2800
BRAILLE_BITS = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}


class BrailleCanvas:
    def __init__(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.dw, self.dh = cw * 2, ch * 4
        self.grid = [[0] * cw for _ in range(ch)]

    def set(self, dx, dy):
        if 0 <= dx < self.dw and 0 <= dy < self.dh:
            self.grid[dy // 4][dx // 2] |= BRAILLE_BITS[(dx % 2, dy % 4)]

    def plot(self, x, y, xr, yr):
        dx = int((x - xr[0]) / (xr[1] - xr[0] + 1e-15) * (self.dw - 1))
        dy = int((1 - (y - yr[0]) / (yr[1] - yr[0] + 1e-15)) * (self.dh - 1))
        self.set(dx, dy)

    def render(self):
        return ["".join(chr(BRAILLE_BASE + c) for c in row) for row in self.grid]


# ═══════════════════════════════════════════════════════════════
#  Terminal size
# ═══════════════════════════════════════════════════════════════

def get_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# ═══════════════════════════════════════════════════════════════
#  Trajectory visualization
# ═══════════════════════════════════════════════════════════════

def show_trajectory(n, cw=None, ch=None):
    """Plot the trajectory of n as a braille graph."""
    if cw is None:
        cols, rows = get_size()
        cw = cols - 8
        ch = max(8, rows // 3)

    seq = trajectory(n)
    steps = len(seq) - 1
    peak = max(seq)
    peak_step = seq.index(peak)

    print(f"  Trajectory of {n:,}")
    print(f"  Steps: {steps}  |  Peak: {peak:,} (at step {peak_step})")
    print()

    # Use log scale for y-axis if range is large
    use_log = peak > 100 * n

    canvas = BrailleCanvas(cw, ch)

    if use_log:
        y_vals = [math.log2(max(v, 1)) for v in seq]
        y_min, y_max = 0, max(y_vals)
        label = "log₂(n)"
    else:
        y_vals = [float(v) for v in seq]
        y_min, y_max = 0, float(peak)
        label = "n"

    for i, y in enumerate(y_vals):
        canvas.plot(i, y, (0, len(seq) - 1), (y_min, y_max))

    lines = canvas.render()
    for i, line in enumerate(lines):
        if i == 0:
            yl = f"{peak:>8,}" if not use_log else f"  2^{y_max:.0f}"
        elif i == len(lines) - 1:
            yl = f"{'1':>8s}" if not use_log else f"  2^0"
        else:
            yl = "        "
        print(f"  {yl} │{line}")

    print(f"  {'':>8s} └{'─' * cw}")
    print(f"  {'':>8s}  0{' ' * (cw - 6)}{steps}")
    print(f"  {'':>8s}  {'step':^{cw}s}")


# ═══════════════════════════════════════════════════════════════
#  Binary evolution
# ═══════════════════════════════════════════════════════════════

def show_binary(n, cw=None, ch=None):
    """
    Show the Collatz sequence as evolving binary numbers.

    Each step is a row. Bits are dots in a braille matrix.
    Even step (n/2) = right-shift: visually drops the lowest bit.
    Odd step (3n+1): bits grow and shift.

    The shape of the binary representation — growing wider with
    3n+1, narrowing with n/2 — creates a landscape showing the
    hailstone's flight through the atmosphere of integers.
    """
    if cw is None:
        cols, _ = get_size()
        cw = cols - 6

    seq = trajectory(n)
    max_bits = max(v.bit_length() for v in seq)

    # Limit width
    max_bit_cols = cw * 2  # 2 dots per braille char width
    if max_bits > max_bit_cols:
        max_bits = max_bit_cols

    # Build binary matrix: rows = steps, cols = bit positions
    # Bit 0 (LSB) on the RIGHT
    n_rows = len(seq)
    ch_needed = (n_rows + 3) // 4  # braille chars needed vertically
    cw_needed = (max_bits + 1) // 2

    # Limit vertical size
    max_ch = 50
    if ch_needed > max_ch:
        # Subsample
        step = n_rows / (max_ch * 4)
        indices = [int(i * step) for i in range(max_ch * 4)]
        indices = list(dict.fromkeys(indices))  # dedupe
        sub_seq = [seq[i] for i in indices]
    else:
        sub_seq = seq
        indices = list(range(len(seq)))

    n_display_rows = len(sub_seq)
    ch_actual = (n_display_rows + 3) // 4
    cw_actual = min(cw_needed, cw)

    canvas = BrailleCanvas(cw_actual, ch_actual)

    for row, val in enumerate(sub_seq):
        bits = val.bit_length()
        for bit_pos in range(min(bits, cw_actual * 2)):
            if val & (1 << bit_pos):
                # MSB on the left: x = max_bits - 1 - bit_pos
                x = min(max_bits - 1, cw_actual * 2 - 1) - bit_pos
                if 0 <= x < cw_actual * 2:
                    canvas.set(x, row)

    print(f"  Binary evolution of {n:,} ({len(seq)} steps, max {max_bits} bits)")
    print(f"  Each row = one Collatz step. MSB left, LSB right.")
    print(f"  n/2 shifts right (drops last bit); 3n+1 grows and shifts.")
    print()

    for line in canvas.render():
        print(f"    {line}")


# ═══════════════════════════════════════════════════════════════
#  Stopping time scatter plot
# ═══════════════════════════════════════════════════════════════

def show_stopping_times(n_max=10000, cw=None, ch=None):
    """Scatter plot: stopping time vs starting number."""
    if cw is None:
        cols, rows = get_size()
        cw = cols - 8
        ch = max(10, rows // 2 - 4)

    print(f"  Stopping Times for n = 1 to {n_max:,}")
    print(f"  (number of steps to reach 1)")
    print()

    # Compute stopping times
    times = []
    max_time = 0
    for i in range(1, n_max + 1):
        t = stopping_time(i)
        times.append(t)
        if t > max_time:
            max_time = t

    canvas = BrailleCanvas(cw, ch)
    for i, t in enumerate(times):
        canvas.plot(i + 1, t, (1, n_max), (0, max_time))

    lines = canvas.render()
    for i, line in enumerate(lines):
        if i == 0:
            yl = f"{max_time:>6d}"
        elif i == len(lines) - 1:
            yl = f"{'0':>6s}"
        else:
            yl = "      "
        print(f"  {yl} │{line}")

    print(f"  {'':>6s} └{'─' * cw}")
    print(f"  {'':>6s}  1{' ' * (cw - 8)}{n_max:,}")

    # Statistics
    avg_time = sum(times) / len(times)
    print()
    print(f"  Average stopping time: {avg_time:.1f}")
    print(f"  Maximum stopping time: {max_time} (n = {times.index(max_time) + 1})")

    # Distribution of stopping times
    print()
    print(f"  Stopping time distribution:")
    freq = {}
    for t in times:
        freq[t] = freq.get(t, 0) + 1

    # Show as histogram, binned
    n_bins = 40
    bin_size = max(1, (max_time + 1) // n_bins)
    binned = {}
    for t, c in freq.items():
        b = t // bin_size
        binned[b] = binned.get(b, 0) + c

    max_count = max(binned.values()) if binned else 1
    for b in range(max(binned.keys()) + 1):
        count = binned.get(b, 0)
        bar = '█' * int(40 * count / max_count)
        t_start = b * bin_size
        t_end = t_start + bin_size - 1
        if count > 0:
            print(f"    {t_start:>3d}-{t_end:<3d}: {count:>5d} {bar}")


# ═══════════════════════════════════════════════════════════════
#  Records
# ═══════════════════════════════════════════════════════════════

def show_records(n_max=100000):
    """Find numbers with record-setting stopping times."""
    print(f"  Record-holding stopping times (n = 1 to {n_max:,})")
    print()
    print(f"  {'n':>10s}  {'steps':>6s}  {'peak':>14s}  trajectory shape")
    print(f"  {'─'*10}  {'─'*6}  {'─'*14}  {'─'*30}")

    record = 0
    records = []

    for n in range(1, n_max + 1):
        t = stopping_time(n)
        if t > record:
            record = t
            seq = trajectory(n)
            peak = max(seq)
            peak_step = seq.index(peak)

            # Mini sparkline of trajectory
            n_spark = 30
            spark_chars = " ▁▂▃▄▅▆▇█"
            spark_vals = []
            for i in range(n_spark):
                idx = int(i * len(seq) / n_spark)
                spark_vals.append(seq[idx])
            s_max = max(spark_vals)
            sparkline = ""
            for v in spark_vals:
                level = int(v / s_max * 8) if s_max > 0 else 0
                sparkline += spark_chars[min(level, 8)]

            records.append((n, t, peak))
            print(f"  {n:>10,}  {t:>6d}  {peak:>14,}  {sparkline}")

    print()
    print(f"  Total records: {len(records)}")

    # Show the growth rate of records
    if len(records) > 3:
        print()
        print(f"  Record-holders grow roughly as n^α where α is unknown.")
        print(f"  The conjecture says every n reaches 1, but the stopping")
        print(f"  time seems to grow without bound: there are always larger")
        print(f"  numbers with longer journeys.")


# ═══════════════════════════════════════════════════════════════
#  Overview mode
# ═══════════════════════════════════════════════════════════════

def overview_mode():
    """Show the Collatz conjecture with examples."""
    cols, rows = get_size()
    cw = cols - 8
    ch = max(8, (rows - 20) // 3)

    # Start with a famous example
    print(f"  Take n = 27. Apply the rules:")
    print(f"    If even: n → n/2")
    print(f"    If odd:  n → 3n + 1")
    print()

    seq = trajectory(27)
    # Show first 20 steps
    print(f"  27 → ", end="")
    for i, v in enumerate(seq[1:21]):
        if i > 0:
            print(f" → ", end="")
        print(f"{v}", end="")
    print(f" → ... → 1")
    print()
    print(f"  27 is a small number. Its journey takes {len(seq)-1} steps")
    print(f"  and reaches a peak of {max(seq):,} before collapsing to 1.")
    print()

    show_trajectory(27, cw, ch)
    print()

    # Show a few more examples
    famous = [(7, "short"), (27, "famous"), (97, "persistent"),
              (871, "soaring"), (6171, "marathon")]

    print(f"  Notable trajectories:")
    for n, adj in famous:
        s = trajectory(n)
        t = len(s) - 1
        p = max(s)
        # Sparkline
        spark_chars = " ▁▂▃▄▅▆▇█"
        spark_n = 20
        spark = ""
        for i in range(spark_n):
            idx = int(i * len(s) / spark_n)
            level = int(s[idx] / p * 8) if p > 0 else 0
            spark += spark_chars[min(level, 8)]
        print(f"    {n:>6,}: {t:>4d} steps, peak {p:>10,}  {spark}  ({adj})")

    print()
    print(f"  Every number tested — up to 2^68 — reaches 1.")
    print(f"  The conjecture says ALL positive integers do.")
    print(f"  Nobody can prove it. Nobody can find a counterexample.")
    print()

    # Show stopping times for first 5000
    show_stopping_times(5000, cw, max(6, ch - 2))


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    mode = args[0] if args else "overview"

    print()
    print("  ═══════════════════════════════════════════════════════════")
    print("  \033[1m  THE COLLATZ CONJECTURE\033[0m")
    print("  \033[1m  n → n/2 or n → 3n+1 : Hailstones of Mathematics\033[0m")
    print("  ═══════════════════════════════════════════════════════════")
    print()

    if mode == "overview":
        overview_mode()

    elif mode == "trajectory":
        n = int(args[1]) if len(args) > 1 else 27
        show_trajectory(n)
        print()

        # Also show some stats
        seq = trajectory(n)
        odd_steps = sum(1 for i in range(len(seq) - 1) if seq[i] % 2 != 0)
        even_steps = len(seq) - 1 - odd_steps
        print(f"  Odd steps (3n+1): {odd_steps}  |  Even steps (n/2): {even_steps}")
        print(f"  Ratio even/odd: {even_steps/max(odd_steps,1):.2f}")
        print(f"  (Expected ratio for random sequences: ~1.585 = log₂(3))")
        print()

        # Show the sequence in a compact form
        if len(seq) <= 60:
            print(f"  Full sequence:")
            line = f"    {seq[0]}"
            for v in seq[1:]:
                addition = f" → {v}"
                if len(line) + len(addition) > 75:
                    print(line)
                    line = f"    {v}"
                else:
                    line += addition
            print(line)
        print()

    elif mode == "stopping":
        n_max = int(args[1]) if len(args) > 1 else 10000
        show_stopping_times(n_max)
        print()

    elif mode == "records":
        n_max = int(args[1]) if len(args) > 1 else 100000
        show_records(n_max)
        print()

    elif mode == "binary":
        n = int(args[1]) if len(args) > 1 else 27
        show_binary(n)
        print()
        show_trajectory(n)
        print()

    else:
        print(f"  Unknown mode: {mode}")
        print(f"  Modes: overview, trajectory <n>, stopping [n_max],")
        print(f"         records [n_max], binary <n>")
        return

    if mode != "overview":
        print("  ─────────────────────────────────────────────────────")
        print("  The Collatz conjecture is the simplest unsolved problem")
        print("  in mathematics. The rules are trivial. The behavior is not.")
        print("  The stopping times look random but aren't. The trajectories")
        print("  look chaotic but always collapse. Order or chaos?")
        print("  We don't know. We can't prove either.")
        print()


if __name__ == "__main__":
    main()
