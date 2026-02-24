"""
Ulam Spiral

Stanisław Ulam was doodling during a boring presentation at Los Alamos
in 1963. He wrote integers in a spiral:

    17 16 15 14 13
    18  5  4  3 12
    19  6  1  2 11
    20  7  8  9 10
    21 22 23 24 25

Then he circled the primes. They lined up along diagonals.

Nobody fully understands why. The diagonals correspond to quadratic
polynomials — some generate many primes (Euler's famous n²+n+41 gives
primes for n=0..39), others give few. But why the primes prefer diagonals
over other patterns in the spiral: still mysterious.

This is related to the Riemann Hypothesis, the distribution of primes,
and some of the deepest unsolved problems in mathematics.
"""

import math


def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0: return False
    return True


def ulam_spiral(size):
    """
    Return a 2D grid of numbers arranged in the Ulam spiral.
    size must be odd. Grid is size×size.
    """
    grid = [[0] * size for _ in range(size)]
    x, y = size // 2, size // 2
    dx, dy = 1, 0  # start moving right
    step, step_count, turn = 1, 0, 0

    n = 1
    while n <= size * size:
        grid[y][x] = n
        n += 1
        x += dx
        y += dy
        step_count += 1

        if step_count == step:
            # Turn left
            dx, dy = -dy, dx
            step_count = 0
            turn += 1
            if turn % 2 == 0:
                step += 1

    return grid


def render_primes(size=71, mark_prime='█', mark_composite=' ', color_diag=True):
    """Render the Ulam spiral, marking primes."""
    grid = ulam_spiral(size)
    lines = []

    for row in grid:
        line = ''
        for n in row:
            if n == 1:
                line += '·'
            elif is_prime(n):
                line += mark_prime
            else:
                line += mark_composite
        lines.append(line)

    return lines


def render_density(size=71, window=5):
    """Render prime density in a sliding window around each cell."""
    grid = ulam_spiral(size)
    # Precompute which numbers are prime
    max_n = size * size
    sieve = [False, False] + [True] * (max_n - 1)
    for i in range(2, int(math.sqrt(max_n)) + 1):
        if sieve[i]:
            for j in range(i*i, max_n + 1, i):
                sieve[j] = False

    # Build position map: number → (row, col)
    lines = []
    shade = ' ·:;+=xX#@█'

    for row_idx, row in enumerate(grid):
        line = ''
        for col_idx, n in enumerate(row):
            # Count primes in neighborhood
            count = 0
            total = 0
            for dr in range(-window//2, window//2 + 1):
                for dc in range(-window//2, window//2 + 1):
                    r2, c2 = row_idx + dr, col_idx + dc
                    if 0 <= r2 < size and 0 <= c2 < size:
                        v = grid[r2][c2]
                        if v >= 2:
                            total += 1
                            if sieve[v]:
                                count += 1
            if total == 0:
                line += ' '
            else:
                density = count / total
                idx = int(density * (len(shade) - 1))
                line += shade[idx]
        lines.append(line)

    return lines


def diagonal_analysis(size=71):
    """
    For each diagonal direction in the Ulam spiral, count primes.
    The four main diagonals pass through numbers of the form:
      4n²+n+?  etc. (quadratic polynomials)
    """
    grid = ulam_spiral(size)
    cx = cy = size // 2

    # Count primes along each diagonal direction
    results = []
    for dx, dy, name in [(1,1,"↗ NE"), (-1,1,"↖ NW"), (-1,-1,"↙ SW"), (1,-1,"↘ SE")]:
        primes = 0
        total = 0
        x, y = cx, cy
        while 0 <= x < size and 0 <= y < size:
            n = grid[y][x]
            if n >= 2:
                total += 1
                if is_prime(n): primes += 1
            x += dx
            y += dy
        results.append((name, primes, total))

    return results


def euler_prime_polynomial():
    """
    Euler discovered that n²+n+41 is prime for n=0,1,...,39.
    Show which values are prime and locate them in the spiral.
    """
    print("  Euler's polynomial: n² + n + 41")
    print()
    print("  n  │ n²+n+41  │ prime?")
    print("  ───┼──────────┼───────")
    for n in range(42):
        v = n*n + n + 41
        p = is_prime(v)
        marker = '██ YES' if p else '   no '
        if n % 5 == 0 or not p:
            print(f"  {n:2d} │ {v:8d} │ {marker}")
    print()
    print("  This polynomial produces primes for n = 0 through 39.")
    print("  At n=40: 40²+40+41 = 1681 = 41² (composite)")
    print("  No polynomial generates primes for ALL n. (Proven.)")


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                      U L A M   S P I R A L                         ║")
    print("║  Integers in a spiral — primes cluster on diagonals                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    size = 71

    print(f"┌─ Ulam spiral: primes shown as █  ({size}×{size}, numbers 1 to {size*size:,}) ─┐")
    print("│")
    lines = render_primes(size=size)
    for line in lines:
        print("│" + line)
    print("│")

    # Count primes
    total = size * size
    primes = sum(1 for n in range(2, total + 1) if is_prime(n))
    print(f"│  {primes:,} primes out of {total:,} integers ({100*primes/total:.1f}%)")
    print("└" + "─" * (size + 1))
    print()

    print(f"┌─ Prime density heatmap  (5×5 window average) ──────────────────────┐")
    print("│  Higher density = more primes nearby (█ = dense, · = sparse)")
    print("│")
    dlines = render_density(size=size, window=7)
    for line in dlines:
        print("│" + line)
    print("└" + "─" * (size + 1))
    print()

    print("┌─ Diagonal prime counts ─────────────────────────────────────────────┐")
    print("│")
    results = diagonal_analysis(size)
    for name, primes, total in results:
        pct = 100 * primes / total if total > 0 else 0
        bar = '█' * int(pct)
        print(f"│  {name}  {primes:3d}/{total:3d} primes ({pct:.1f}%)  {bar}")
    overall_pct = 100 * sum(p for _,p,_ in results) / sum(t for _,_,t in results)
    print(f"│")
    print(f"│  The diagonals have higher prime density than the spiral overall.")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    print("┌─ Euler's prime-generating polynomial ───────────────────────────────┐")
    print("│")
    euler_prime_polynomial()
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    print("  The Ulam spiral was discovered in a meeting at Los Alamos, 1963.")
    print("  The diagonal patterns relate to quadratic forms and L-functions.")
    print("  Understanding them fully would require understanding prime distribution")
    print("  at a depth we don't yet have.")
    print()


if __name__ == '__main__':
    main()
