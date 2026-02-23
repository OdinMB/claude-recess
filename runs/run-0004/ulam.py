"""
Ulam Spiral
============
Write positive integers in a rectangular spiral, starting at center.
Mark the primes. Diagonal patterns emerge — their cause is related to
prime-generating quadratic polynomials (like Euler's n²+n+41) but
is not fully understood.

Legendre's conjecture asks: is there always a prime between n² and (n+1)²?
The spiral makes you feel how prime-rich certain diagonals are.
"""

import math


def sieve(n):
    """Simple Sieve of Eratosthenes up to n."""
    is_prime = bytearray([1]) * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = bytearray(len(is_prime[i*i::i]))
    return is_prime


def make_spiral(size):
    """
    Generate the Ulam spiral as a 2D grid of integers.
    Returns grid[row][col] = integer at that position.
    """
    grid = [[0] * size for _ in range(size)]
    cx, cy = size // 2, size // 2
    x, y = cx, cy
    grid[y][x] = 1
    n = 2
    step = 1
    while n <= size * size:
        # Move right `step`, then up `step`, then left `step+1`, then down `step+1`
        for _ in range(step):
            x += 1
            if n <= size * size:
                grid[y][x] = n
                n += 1
        for _ in range(step):
            y -= 1
            if n <= size * size:
                grid[y][x] = n
                n += 1
        step += 1
        for _ in range(step):
            x -= 1
            if n <= size * size:
                grid[y][x] = n
                n += 1
        for _ in range(step):
            y += 1
            if n <= size * size:
                grid[y][x] = n
                n += 1
        step += 1
    return grid


def render(size=71, mark_char='#', empty_char=' ', highlight_euler=True):
    """
    Render the Ulam spiral.
    - '#' for primes
    - '·' for composites
    - Optionally mark Euler's lucky polynomial n²+n+41 with '*'
    """
    assert size % 2 == 1, "Size must be odd"
    limit = size * size
    is_prime = sieve(limit)

    # Euler polynomial: n²+n+41 produces primes for n=0..39
    euler_set = set()
    for n in range(200):
        v = n*n + n + 41
        if v <= limit:
            euler_set.add(v)

    grid = make_spiral(size)

    lines = []
    for row in grid:
        chars = []
        for val in row:
            if val == 0:
                chars.append(' ')
            elif is_prime[val]:
                if highlight_euler and val in euler_set:
                    chars.append('*')  # prime AND on Euler diagonal
                else:
                    chars.append(mark_char)
            else:
                chars.append('·')
        lines.append(''.join(chars))
    return lines


def prime_density_by_diagonal(size=101):
    """
    For each diagonal direction, count prime density.
    The four diagonals in the spiral correspond to different quadratic
    polynomials. Some are much prime-richer than others.
    """
    limit = size * size
    is_prime = sieve(limit)
    grid = make_spiral(size)
    cx = cy = size // 2

    # Extract four main diagonals through center
    diags = {
        'NE (↗)': [],
        'NW (↖)': [],
        'SE (↘)': [],
        'SW (↙)': [],
    }
    length = size // 2
    for d in range(length + 1):
        for name, dx, dy in [('NE (↗)', d, -d), ('NW (↖)', -d, -d),
                              ('SE (↘)', d,  d), ('SW (↙)', -d,  d)]:
            r, c = cy + dy, cx + dx
            if 0 <= r < size and 0 <= c < size:
                v = grid[r][c]
                if 1 < v <= limit:
                    diags[name].append(v)

    print(f"\n  Prime density along the four main diagonals (size={size}):")
    print(f"  {'Direction':12s}  {'Primes':>7s} / {'Total':>6s}  {'Density':>8s}")
    print(f"  {'-'*50}")
    for name, vals in diags.items():
        n_prime = sum(1 for v in vals if is_prime[v])
        density = n_prime / len(vals) if vals else 0
        print(f"  {name:12s}  {n_prime:7d} / {len(vals):6d}  {density:8.3f}")

    # Compare to overall prime density up to limit
    total_primes = sum(is_prime[2:limit+1])
    overall = total_primes / (limit - 1)
    print(f"\n  Overall prime density up to {limit}: {overall:.3f}")
    print(f"  (Prime Number Theorem predicts ≈ {1/math.log(limit):.3f})")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ulam spiral visualizer')
    parser.add_argument('--size', type=int, default=71, help='Spiral size (odd, default 71)')
    parser.add_argument('--no-euler', action='store_true', help='Don\'t highlight Euler diagonal')
    parser.add_argument('--density', action='store_true', help='Show diagonal density analysis')
    args = parser.parse_args()

    size = args.size | 1  # ensure odd

    if args.density:
        prime_density_by_diagonal(size)
    else:
        lines = render(size, highlight_euler=not args.no_euler)
        print(f"\n  Ulam Spiral ({size}×{size})")
        print(f"  '#' = prime, '*' = prime on Euler n²+n+41 diagonal, '·' = composite\n")
        for line in lines:
            print('  ' + line)
        print()
        prime_count = sum(line.count('#') + line.count('*') for line in lines)
        euler_count = sum(line.count('*') for line in lines)
        print(f"  {prime_count} primes shown, {euler_count} on Euler's diagonal")
