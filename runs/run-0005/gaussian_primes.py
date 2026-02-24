"""
Gaussian Primes

The Gaussian integers: ℤ[i] = {a + bi : a,b ∈ ℤ}
This is a ring, and it has its own notion of primes.

A Gaussian integer α is prime if it cannot be written as α = βγ
where neither β nor γ is a unit (units are ±1, ±i).

Which Gaussian integers are prime?

  α = a + bi is a Gaussian prime iff:
    1. a = 0 and |b| is a prime ≡ 3 (mod 4)  [e.g., 3i, 7i, 11i, ...]
    2. b = 0 and |a| is a prime ≡ 3 (mod 4)  [e.g., 3, 7, 11, ...]
    3. a ≠ 0, b ≠ 0, and a² + b² is prime    [e.g., 1+i (norm=2), 2+i (norm=5)]

The connection to ordinary primes:
  - If p ≡ 3 (mod 4), p is also a Gaussian prime (stays prime in ℤ[i])
  - If p ≡ 1 (mod 4), p splits: p = (a+bi)(a-bi) for some a,b (Fermat's theorem)
  - p = 2 ramifies: 2 = -i(1+i)²

This is Fermat's theorem on sums of two squares (1640):
  A prime p is a sum of two squares iff p = 2 or p ≡ 1 (mod 4).

The Gaussian prime spiral conjecture (open):
  Starting at 0 in the complex plane, can you spiral outward by steps of 1
  in cardinal directions, always landing on Gaussian primes?
  This seems to work empirically, but nobody has proved it can't get stuck.
  (This would follow from a conjecture about prime gaps in arithmetic progressions.)
"""

import math


def norm(a, b):
    """Squared norm of a + bi."""
    return a * a + b * b


def is_rational_prime(n):
    """Is n an ordinary (rational) prime?"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def is_gaussian_prime(a, b):
    """Is a + bi a Gaussian prime?"""
    if a == 0:
        return is_rational_prime(abs(b)) and abs(b) % 4 == 3
    if b == 0:
        return is_rational_prime(abs(a)) and abs(a) % 4 == 3
    return is_rational_prime(a * a + b * b)


def gaussian_prime_grid(size):
    """
    Return a 2D boolean grid: True if (a + bi) is a Gaussian prime,
    where a, b range from -size to +size.
    """
    n = 2 * size + 1
    grid = [[False] * n for _ in range(n)]
    for row, b in enumerate(range(-size, size + 1)):
        for col, a in enumerate(range(-size, size + 1)):
            grid[row][col] = is_gaussian_prime(a, b)
    return grid


# ── Sections ──────────────────────────────────────────────────────────────────

def section_factorization():
    print("┌─ Ordinary Primes in ℤ[i] ──────────────────────────────────────────┐")
    print("│  How rational primes factor in the Gaussian integers")
    print("│")

    primes_to_show = [p for p in range(2, 50) if is_rational_prime(p)]

    print(f"│  {'p':>4}  {'p mod 4':>7}  {'Behavior in ℤ[i]':>40}")
    print(f"│  {'─'*4}  {'─'*7}  {'─'*40}")

    for p in primes_to_show:
        mod4 = p % 4
        if p == 2:
            behavior = "2 = -i(1+i)²  (ramifies)"
        elif mod4 == 3:
            behavior = f"{p} stays prime  (inert)"
        else:  # mod4 == 1
            # Find Fermat decomposition p = a² + b²
            a_sq = None
            for a in range(1, int(p**0.5) + 1):
                b_sq = p - a * a
                b = int(b_sq**0.5)
                if b * b == b_sq and b > 0:
                    a_sq = (a, b)
                    break
            if a_sq:
                a, b = a_sq
                behavior = f"{p} = ({a}+{b}i)({a}-{b}i)  (splits)"
            else:
                behavior = f"{p} = ?  (splits)"
        print(f"│  {p:>4}  {mod4:>7}  {behavior:>40}")

    print("│")
    print("│  Pattern:")
    print("│    p ≡ 1 (mod 4): splits into two conjugate Gaussian primes")
    print("│    p ≡ 3 (mod 4): remains prime (inert) in ℤ[i]")
    print("│    p = 2: special — ramifies (perfect square times unit, up to associates)")
    print("└" + "─" * 73)
    print()


def section_fermat_sums():
    print("┌─ Fermat's Theorem on Sums of Two Squares ───────────────────────────┐")
    print("│  Which primes are sums of two squares?  p = a² + b²")
    print("│")
    print("│  Fermat (1640): p = a² + b² iff p = 2 or p ≡ 1 (mod 4)")
    print("│  Euler proved this rigorously ~100 years later.")
    print("│")

    print(f"│  {'p':>6}  {'p mod 4':>7}  {'Sum of squares?':>16}  {'Decomposition'}")
    print(f"│  {'─'*6}  {'─'*7}  {'─'*16}  {'─'*25}")

    for p in [p for p in range(2, 80) if is_rational_prime(p)]:
        mod4 = p % 4
        if p == 2:
            print(f"│  {p:>6}  {'2 (spec)':>7}  {'Yes':>16}  1² + 1²")
            continue

        # Try to find decomposition
        decomp = None
        for a in range(0, int(p**0.5) + 1):
            b_sq = p - a * a
            b = int(b_sq**0.5 + 0.5)
            if b * b == b_sq:
                decomp = (a, b)
                break

        if decomp:
            a, b = decomp
            decomp_str = f"{a}² + {b}² = {a*a} + {b*b}"
        else:
            decomp_str = "—"

        is_sum = "Yes" if decomp else "No"
        print(f"│  {p:>6}  {mod4:>7}  {is_sum:>16}  {decomp_str}")

    print("│")
    print("│  The Gaussian integers make this obvious: p = a² + b² = (a+bi)(a-bi)")
    print("│  iff p splits in ℤ[i]. It splits iff p ≡ 1 (mod 4) (by quadratic reciprocity).")
    print("└" + "─" * 73)
    print()


def section_visualization(size=24):
    """Draw the Gaussian primes as a grid in the complex plane."""
    print("┌─ Gaussian Primes in the Complex Plane ─────────────────────────────┐")
    print(f"│  Region: [{-size}, {size}] × [{-size}i, {size}i]")
    print("│  '█' = Gaussian prime   '·' = not prime")
    print("│")

    # Width fits in 70 chars: 2*size+1 columns, with 2 chars per cell
    # Use size = 24, grid is 49 wide × 49 tall — that's 98 chars wide
    # Use a smaller display with 1 char per cell
    grid = gaussian_prime_grid(size)

    for row_idx in range(len(grid) - 1, -1, -1):  # Draw from top (high imag) to bottom
        b = row_idx - size  # imaginary part
        line = "│  "
        for cell in grid[row_idx]:
            line += '█' if cell else '·'
        # Add axis label for b=0
        if b == 0:
            line += " ← real axis"
        print(line)

    print("│")
    print(f"│  Real axis ↔   Imaginary axis ↕")
    print(f"│  Note the 4-fold symmetry (conjugation and multiplication by i)")
    print(f"│  and the 'moats' — regions of non-primes surrounding clusters")
    print("└" + "─" * 73)
    print()


def section_spiral_conjecture():
    """Demonstrate the Gaussian prime spiral (walk outward on primes)."""
    print("┌─ Gaussian Prime Spiral Conjecture ─────────────────────────────────┐")
    print("│  Can you walk from any point to infinity on Gaussian primes,")
    print("│  taking unit steps in axis-aligned directions?")
    print("│")
    print("│  More precisely: starting at 0, is there an infinite path through")
    print("│  Gaussian primes using steps of ±1 or ±i?")
    print("│")
    print("│  The conjecture: YES, always. But it's unproven.")
    print("│  It would follow from sufficiently strong bounds on prime gaps")
    print("│  in arithmetic progressions.")
    print("│")

    # Simulate a Gaussian prime walk, turning to find a prime at each step
    print("│  Simulated walk from the origin — finding the nearest Gaussian prime")
    print("│  in each direction, then taking the closest step:")
    print("│")

    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # E, N, W, S
    dir_names = ['E', 'N', 'W', 'S']

    pos = (0, 0)
    path = [pos]
    max_steps = 20

    for step in range(max_steps):
        a, b = pos
        # Try to step to an adjacent Gaussian prime
        found = False
        for (da, db), name in zip(directions, dir_names):
            na, nb = a + da, b + db
            if is_gaussian_prime(na, nb):
                pos = (na, nb)
                path.append(pos)
                found = True
                # Don't print all steps, just summarize
                break
        if not found:
            # Look a bit further
            for dist in range(2, 10):
                for (da, db) in directions:
                    na, nb = a + da * dist, b + db * dist
                    if is_gaussian_prime(na, nb):
                        pos = (na, nb)
                        path.append(pos)
                        found = True
                        break
                if found:
                    break
        if not found:
            break

    # Show path
    print(f"│  Starting at 0+0i:")
    for i, (a, b) in enumerate(path[:15]):
        gp = "✓" if is_gaussian_prime(a, b) else " "
        ni = f"{'+' if b >= 0 else ''}{b}i" if b != 0 else ""
        na = str(a) if a != 0 else ("0" if b == 0 else "")
        coord = f"{na}{ni}" or "0"
        norm_val = a*a + b*b
        print(f"│    step {i:2d}: {coord:>10}  (norm={norm_val:4d})  {gp}")

    print("│")
    print("│  Known: the Gaussian primes have 'moats' — unbounded regions of")
    print("│  composite Gaussian integers. Whether these moats disconnect infinity")
    print("│  is the open question.")
    print("│")

    # Moat widths
    print("│  Moat widths (annular regions with no Gaussian primes):")
    moat_data = [
        (0, "Moat of width 0 — no moat, primes dense near origin"),
        (2, "Moat of width 2 — exists (first nontrivial moat)"),
        (26, "Moat of width 26 — conjectured widths grow unboundedly"),
    ]
    for width, desc in moat_data:
        print(f"│    Width {width}: {desc}")
    print("└" + "─" * 73)
    print()


def section_norm_distribution():
    """Distribution of Gaussian prime norms."""
    print("┌─ Gaussian Prime Norms ──────────────────────────────────────────────┐")
    print("│  The norm N(a+bi) = a²+b² of a Gaussian prime")
    print("│")

    # Find all Gaussian primes up to norm 100
    gp_by_norm = {}
    for a in range(-15, 16):
        for b in range(-15, 16):
            n = norm(a, b)
            if n <= 200 and is_gaussian_prime(a, b):
                if n not in gp_by_norm:
                    gp_by_norm[n] = []
                gp_by_norm[n].append((a, b))

    print("│  Norm  Count  Examples (up to associates = ×units ±1, ±i)")
    print("│  ────  ─────  ─────────────────────────────────────────")

    for n in sorted(gp_by_norm.keys())[:20]:
        gps = gp_by_norm[n]
        # Show a few examples
        examples = [f"{a}+{b}i" if b >= 0 else f"{a}{b}i" for a, b in gps[:4]]
        example_str = ", ".join(examples)
        if len(gps) > 4:
            example_str += f" ... ({len(gps)} total)"
        print(f"│  {n:>4d}  {len(gps):>5d}  {example_str}")

    print("│")
    print("│  Norms of Gaussian primes are: 2, and primes ≡ 1 (mod 4) (from splits)")
    print("│  and squares of primes ≡ 3 (mod 4) (from inerts: norm(p) = p²)")
    print("│")
    print("│  Gaussian prime theorem (analog of PNT):")
    print("│  The number of Gaussian primes with norm ≤ x is ~ x/ln(x)")
    print("│  (same asymptotic as ordinary prime counting function)")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           G A U S S I A N   P R I M E S                           ║")
    print("║  Primes in the complex plane: ℤ[i]                                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  Gauss extended the integers to ℤ[i] = {a+bi : a,b ∈ ℤ}.")
    print("  This new ring has its own primes — and they reveal deep truths about")
    print("  the ordinary primes, especially which are sums of two squares.")
    print()

    section_factorization()
    section_fermat_sums()
    section_visualization(size=24)
    section_norm_distribution()
    section_spiral_conjecture()

    print("  Gaussian integers are a Euclidean domain — division with remainder works,")
    print("  so unique factorization holds (unlike in ℤ[√-5], where 6 = 2×3 = (1+√-5)(1-√-5)).")
    print("  This uniqueness is what makes Fermat's two-square theorem work.")
    print()


if __name__ == '__main__':
    main()
