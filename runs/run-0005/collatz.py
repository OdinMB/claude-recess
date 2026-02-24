"""
Collatz Conjecture Visualizer

Take any positive integer n:
    if n is even: n → n/2
    if n is odd:  n → 3n + 1

Repeat until n = 1. (As far as anyone has checked, you always reach 1.)
Nobody has proved this. Nobody knows why it works.

This program visualizes the "stopping times" — how many steps each number
takes to reach 1 — as an ASCII heatmap.

Columns = starting numbers (left to right)
Rows    = step count (top = few steps, bottom = many steps)

A lit cell means: "this number was at this height on its journey down."
"""

import sys


def collatz_sequence(n):
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq


def stopping_time(n):
    count = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        count += 1
    return count


def max_value(n):
    peak = n
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        if n > peak:
            peak = n
    return peak


def render_stopping_times(start=1, count=120, height=40):
    """Show stopping times as a bar chart using ASCII."""
    times = [stopping_time(n) for n in range(start, start + count)]
    max_t = max(times)

    width = count
    chars = '▁▂▃▄▅▆▇█'

    print(f"  Collatz stopping times: n = {start} to {start + count - 1}")
    print(f"  Max stopping time: {max_t} steps (n={start + times.index(max_t)})")
    print()

    # Row-based rendering: top row = tallest bars
    grid = []
    for row in range(height):
        threshold = max_t * (height - row) / height
        line = ''
        for t in times:
            frac = t / max_t * height
            row_pos = height - row
            if frac >= row_pos:
                line += '█'
            elif frac >= row_pos - 1:
                # Partial block
                partial = frac - (row_pos - 1)
                idx = int(partial * len(chars))
                idx = max(0, min(len(chars) - 1, idx))
                line += chars[idx]
            else:
                line += ' '
        grid.append(line)

    # Add left axis
    for i, line in enumerate(grid):
        if i == 0:
            label = f"{max_t:4d}│"
        elif i == height - 1:
            label = f"   1│"
        elif i == height // 2:
            label = f"{max_t//2:4d}│"
        else:
            label = "    │"
        print(label + line)

    print("    └" + "─" * width)
    print(f"     {start}" + " " * (width - len(str(start)) - len(str(start + count - 1))) + str(start + count - 1))


def render_trajectory_heatmap(start=1, count=80, height=50):
    """
    Heatmap where each column is a starting number,
    each row is a value range. Lit = the trajectory passed through here.
    """
    print(f"\n  Trajectory heatmap: where do numbers go on their way down?")
    print(f"  n = {start} to {start + count - 1}  (rows = value ranges)")
    print()

    # Find global max across all trajectories
    global_max = 1
    seqs = []
    for n in range(start, start + count):
        seq = collatz_sequence(n)
        seqs.append(seq)
        global_max = max(global_max, max(seq))

    # Bin values into rows
    density = [[0] * count for _ in range(height)]
    for col, seq in enumerate(seqs):
        for val in seq:
            row = int((1 - val / global_max) * (height - 1))
            row = max(0, min(height - 1, row))
            density[row][col] += 1

    shade = ' ·:;+x#@'
    max_d = max(max(row) for row in density)

    for i, row in enumerate(density):
        if i == 0:
            label = f"{global_max:6d}│"
        elif i == height - 1:
            label = f"     1│"
        elif i == height // 2:
            label = f"{global_max//2:6d}│"
        else:
            label = "      │"

        line = ''
        for d in row:
            if d == 0:
                line += ' '
            else:
                idx = max(1, int(d / max_d * (len(shade) - 1)))
                line += shade[idx]
        print(label + line)

    print("      └" + "─" * count)
    print(f"       {start}" + " " * (count - len(str(start)) - len(str(start + count - 1))) + str(start + count - 1))


def interesting_numbers():
    """Find some numbers with unusually long stopping times."""
    print("\n  Numbers with long stopping times (up to 10,000):")
    print()

    results = []
    for n in range(1, 10001):
        t = stopping_time(n)
        results.append((t, n))

    results.sort(reverse=True)
    top = results[:15]

    for rank, (t, n) in enumerate(top, 1):
        peak = max_value(n)
        bar = '█' * min(50, t // 5)
        print(f"  {rank:2d}. n={n:5d}  steps={t:4d}  peak={peak:12,d}  {bar}")


def main():
    print("=" * 80)
    print("  THE COLLATZ CONJECTURE")
    print("  if n even: n → n/2    if n odd: n → 3n+1    always reaches 1?")
    print("=" * 80)
    print()

    render_stopping_times(start=1, count=120, height=30)
    render_trajectory_heatmap(start=1, count=80, height=35)
    interesting_numbers()

    print()
    print("  \"Mathematics is not yet ready for such problems.\" — Paul Erdős")
    print()


if __name__ == '__main__':
    main()
