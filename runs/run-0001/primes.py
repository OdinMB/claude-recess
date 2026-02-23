"""
The Ulam Spiral — hidden order in the primes.

In 1963, Stanislaw Ulam was doodling during a boring meeting. He wrote
integers in a spiral pattern, starting from the center, and circled the
primes. To his surprise, the primes weren't scattered randomly — they
tended to line up along certain diagonals.

    37                      37
    36  17  18  19  20       . 17  .  . 20
    35  16   5   6  21      35  .  5  .  .
    34  15   4   1   2      .  .  .  1  2
    33  14   3   8   7      .  .  3  .  7
    32  13  12  11  10      .  13  . 11  .
    31  30  29  28  27      31  .  29  .  .

This is still unexplained. The Hardy-Littlewood conjecture provides a
partial explanation (quadratic polynomials can be prime-rich along
diagonals), but the visual structure is striking and not fully understood.

The primes sit at a boundary: they have MORE structure than random numbers
(those diagonal lines) but LESS structure than any simple pattern (the
prime counting function has no closed form). They're ordered enough to
have a rhythm, but disordered enough that predicting the next prime is
hard. The boundary between order and chaos — again.

The Sacks spiral (Robert Sacks, 1994) uses a continuous spiral (r = √n,
θ = 2π√n) and reveals even more structure: curves rather than lines.

Usage:
    python3 primes.py                    # Ulam spiral
    python3 primes.py sacks             # Sacks spiral
    python3 primes.py gap               # Prime gap distribution
    python3 primes.py race              # Prime race (π vs Li)
"""

import sys
import os
import math


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

    def render(self):
        lines = []
        for row in self.grid:
            lines.append(''.join(chr(0x2800 + bits) for bits in row))
        return '\n'.join(lines)


# --- Primality ---

def sieve(limit):
    """Sieve of Eratosthenes. Return set of primes up to limit."""
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return set(i for i, v in enumerate(is_prime) if v)


# --- Ulam Spiral ---

def ulam_spiral(n_max, cw, ch):
    """
    Generate an Ulam spiral and render it.

    The spiral starts at 1 in the center and winds outward:
    right, up, left, left, down, down, right, right, right, ...
    Each "arm" extends by one more step than the previous same-direction arm.
    """
    primes = sieve(n_max)
    canvas = BrailleCanvas(cw, ch)

    cx = canvas.dot_w // 2
    cy = canvas.dot_h // 2

    # Generate spiral coordinates
    x, y = 0, 0
    dx, dy = 1, 0  # Start moving right
    steps_in_direction = 1
    steps_taken = 0
    turns = 0

    for n in range(1, n_max + 1):
        if n in primes:
            canvas.set_dot(cx + x, cy + y)

        # Move
        x += dx
        y += dy
        steps_taken += 1

        if steps_taken == steps_in_direction:
            steps_taken = 0
            # Turn left
            dx, dy = dy, -dx
            turns += 1
            if turns % 2 == 0:
                steps_in_direction += 1

    return canvas


def ulam_mode(cw, ch):
    """Display the Ulam spiral with analysis."""
    # Estimate how many numbers fit in our canvas
    dot_w = cw * 2
    dot_h = ch * 4
    radius = min(dot_w, dot_h) // 2
    n_max = (2 * radius + 1) ** 2  # approximate

    print(f"  Ulam Spiral — primes arranged in a spiral from the center")
    print(f"  {n_max:,} integers, primes marked as dots")
    print()

    canvas = ulam_spiral(n_max, cw, ch)
    print(canvas.render())
    print()

    primes = sieve(n_max)
    print(f"  Primes up to {n_max:,}: {len(primes):,}")
    print(f"  Prime density: {100*len(primes)/n_max:.1f}%")
    print(f"  Expected (1/ln(n)): {100/math.log(n_max):.1f}%")
    print()

    # Diagonal analysis: check if primes cluster on certain diagonals
    # The main diagonals of the Ulam spiral correspond to quadratic polynomials
    print(f"  The diagonal lines are real — primes cluster along polynomials")
    print(f"  like 4n²+bn+c for certain values of b,c.")
    print(f"  Euler's n²+n+41 is prime for n=0..39 (the famous prime-generating polynomial).")


# --- Sacks Spiral ---

def sacks_spiral(n_max, cw, ch):
    """
    Sacks spiral: plot n at (r, θ) = (√n, 2π√n).

    This maps integers to a continuous spiral where primes
    form visible curves rather than lines.
    """
    primes = sieve(n_max)
    canvas = BrailleCanvas(cw, ch)

    cx = canvas.dot_w // 2
    cy = canvas.dot_h // 2
    max_r = min(canvas.dot_w, canvas.dot_h) // 2 - 2

    # Scale factor
    sqrt_max = math.sqrt(n_max)
    scale = max_r / sqrt_max

    for n in range(2, n_max + 1):
        if n not in primes:
            continue

        sqrt_n = math.sqrt(n)
        theta = 2 * math.pi * sqrt_n
        r = sqrt_n * scale

        x = int(cx + r * math.cos(theta))
        y = int(cy + r * math.sin(theta))
        canvas.set_dot(x, y)

    return canvas


def sacks_mode(cw, ch):
    """Display the Sacks spiral."""
    dot_w = cw * 2
    dot_h = ch * 4
    radius = min(dot_w, dot_h) // 2
    n_max = int(radius ** 2)

    print(f"  Sacks Spiral — primes on a continuous spiral r=√n, θ=2π√n")
    print(f"  {n_max:,} integers, primes marked")
    print()

    canvas = sacks_spiral(n_max, cw, ch)
    print(canvas.render())
    print()

    print(f"  The curves you see are real: they correspond to quadratic")
    print(f"  residue classes. Primes avoid certain spiral arms entirely")
    print(f"  (multiples of small primes) and concentrate on others.")


# --- Prime Gap Distribution ---

def gap_mode():
    """Analyze prime gap distribution."""
    limit = 100000
    primes_set = sieve(limit)
    primes_list = sorted(primes_set)

    print(f"  Prime Gap Distribution — first {len(primes_list):,} primes")
    print()

    # Compute gaps
    gaps = [primes_list[i+1] - primes_list[i] for i in range(len(primes_list) - 1)]

    # Distribution
    gap_freq = {}
    for g in gaps:
        gap_freq[g] = gap_freq.get(g, 0) + 1

    # Statistics
    avg_gap = sum(gaps) / len(gaps)
    max_gap = max(gaps)
    max_gap_pos = gaps.index(max_gap)

    print(f"  Average gap: {avg_gap:.2f}")
    print(f"  Expected (ln(n)): {math.log(limit):.2f}")
    print(f"  Largest gap: {max_gap} (between {primes_list[max_gap_pos]} and {primes_list[max_gap_pos+1]})")
    print()

    # Show distribution
    print(f"  Gap size distribution:")
    max_count = max(gap_freq.values())
    for gap in sorted(gap_freq.keys())[:25]:
        count = gap_freq[gap]
        bar = '█' * int(50 * count / max_count)
        print(f"    {gap:>3d}: {count:>5d} {bar}")

    # Twin primes (gap = 2)
    twins = gap_freq.get(2, 0)
    print()
    print(f"  Twin primes (gap 2): {twins}")
    print(f"  Twin prime conjecture: infinitely many? Unknown.")
    print()

    # Note the pattern: gap 2 and gap 4 are most common, but
    # odd gaps > 1 are rare (only gap 1 between 2 and 3)
    even_gaps = sum(c for g, c in gap_freq.items() if g % 2 == 0)
    odd_gaps = sum(c for g, c in gap_freq.items() if g % 2 != 0)
    print(f"  Even gaps: {even_gaps} ({100*even_gaps/len(gaps):.1f}%)")
    print(f"  Odd gaps:  {odd_gaps} ({100*odd_gaps/len(gaps):.1f}%)")
    print(f"  (The only odd gap is 1, between 2 and 3. All other")
    print(f"   consecutive primes have even gaps — because all primes")
    print(f"   > 2 are odd, and odd - odd = even.)")


# --- Prime Race ---

def prime_race_mode(cw, ch):
    """
    Prime race: π(x) vs Li(x).

    π(x) = number of primes ≤ x
    Li(x) = logarithmic integral = integral from 2 to x of 1/ln(t)

    The prime number theorem says π(x) ~ Li(x) for large x.
    But which one leads? Li(x) almost always leads, but there's
    a proven crossover point (the Skewes number) where π(x) > Li(x).
    """
    canvas = BrailleCanvas(cw, ch)
    limit = 10000

    primes = sieve(limit)

    # Compute π(x) and Li(x) at each x
    pi_vals = []
    li_vals = []

    count = 0
    for x in range(2, limit + 1):
        if x in primes:
            count += 1
        pi_vals.append(count)

        # Approximate Li(x) using trapezoidal rule
        if x <= 2:
            li_vals.append(0)
        else:
            # Li(x) ≈ sum of 1/ln(k) for k=2..x
            li_val = sum(1/math.log(k) for k in range(2, x + 1))
            li_vals.append(li_val)

    # Plot the difference Li(x) - π(x)
    diffs = [li - pi for pi, li in zip(pi_vals, li_vals)]

    min_diff = min(diffs)
    max_diff = max(diffs)
    diff_range = max_diff - min_diff if max_diff > min_diff else 1

    for i, d in enumerate(diffs):
        x = int(i / len(diffs) * (canvas.dot_w - 1))
        y = int((1 - (d - min_diff) / diff_range) * (canvas.dot_h - 1))
        canvas.set_dot(x, y)

    # Also draw the zero line
    zero_y = int((1 - (0 - min_diff) / diff_range) * (canvas.dot_h - 1))
    for x in range(canvas.dot_w):
        canvas.set_dot(x, zero_y)

    print(f"  Prime Race: Li(x) - π(x) for x up to {limit:,}")
    print(f"  Horizontal line is zero; curve shows how much Li(x) leads")
    print()
    print(canvas.render())
    print()
    print(f"  Li(x) almost always overestimates π(x).")
    print(f"  The first crossover (where π(x) > Li(x)) occurs near")
    print(f"  the Skewes number: somewhere below e^(e^(e^79)) ≈ 10^(10^(10^34)).")
    print(f"  This is proven to exist but has never been computed exactly.")


# --- Main ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


def main():
    cols, rows = get_terminal_size()
    cw = cols - 4
    ch = max(10, rows - 8)

    args = sys.argv[1:]

    if not args:
        ulam_mode(cw, ch)
    elif args[0] == 'sacks':
        sacks_mode(cw, ch)
    elif args[0] == 'gap':
        gap_mode()
    elif args[0] == 'race':
        prime_race_mode(cw, ch)
    else:
        print(f"  Unknown mode: {args[0]}")
        print(f"  Modes: (default), sacks, gap, race")


if __name__ == "__main__":
    main()
