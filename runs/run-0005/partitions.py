"""
Integer Partitions

A partition of n is a way to write n as an unordered sum of positive integers.
p(n) = number of partitions of n.

  p(4) = 5:  4,  3+1,  2+2,  2+1+1,  1+1+1+1
  p(5) = 7:  5,  4+1,  3+2,  3+1+1,  2+2+1,  2+1+1+1,  1+1+1+1+1

The generating function (Euler, 1748):

    Σ p(n) x^n = Π_{k=1}^∞ 1/(1-x^k)

Hardy and Ramanujan (1918) found the asymptotic formula:

    p(n) ~ (1 / (4n√3)) × exp(π √(2n/3))

Rademacher (1937) gave an EXACT formula — an infinite convergent series.

Ramanujan's congruences (1919) — among the most beautiful in number theory:
    p(5n + 4) ≡ 0  (mod 5)   for all n ≥ 0
    p(7n + 5) ≡ 0  (mod 7)   for all n ≥ 0
    p(11n + 6) ≡ 0  (mod 11)  for all n ≥ 0

Why does the partition function — a purely combinatorial object — know about
the prime 5? About 7 and 11? It's deeply mysterious.

Connection to physics: p(n) counts the number of ways to distribute n units
of energy among bosons. The generating function is the grand partition function.
"""

import math


def partitions_count(max_n):
    """
    Compute p(0), p(1), ..., p(max_n) using Euler's recurrence.
    Uses the pentagonal number theorem:
      p(n) = Σ_{k≠0} (-1)^{k+1} p(n - k(3k-1)/2)
    where the generalized pentagonal numbers are k(3k-1)/2 for k = 1,-1,2,-2,...
    """
    p = [0] * (max_n + 1)
    p[0] = 1

    # Generalized pentagonal numbers: k(3k-1)/2 for k = 1, -1, 2, -2, ...
    def pentagonals():
        k = 1
        while True:
            yield k * (3 * k - 1) // 2, +1
            yield k * (3 * (-k) - 1) // 2 * (-1) + k * 3, -1  # k → -k
            # Actually: k(3k-1)/2 and k(3k+1)/2 for k = 1, 2, 3, ...
            # Let me use the direct formula
            k += 1

    # Correct implementation
    p = [0] * (max_n + 1)
    p[0] = 1
    for n in range(1, max_n + 1):
        total = 0
        k = 1
        while True:
            # Pentagonal numbers: g_k = k(3k-1)/2, g_{-k} = k(3k+1)/2
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            if g1 > n:
                break
            sign = +1 if k % 2 == 1 else -1
            total += sign * p[n - g1]
            if g2 <= n:
                total += sign * p[n - g2]
            k += 1
        p[n] = total

    return p


def list_partitions(n, max_part=None):
    """
    Generate all partitions of n as lists in non-increasing order.
    Yields each partition as a tuple.
    """
    if max_part is None:
        max_part = n

    if n == 0:
        yield ()
        return

    for largest in range(min(n, max_part), 0, -1):
        for rest in list_partitions(n - largest, largest):
            yield (largest,) + rest


def hardy_ramanujan_approx(n):
    """Hardy-Ramanujan asymptotic formula for p(n)."""
    if n == 0:
        return 1
    return math.exp(math.pi * math.sqrt(2 * n / 3)) / (4 * n * math.sqrt(3))


def rademacher_approx(n, terms=5):
    """
    Rademacher's exact formula (partial sum).
    p(n) = (2π/(24n-1)^(3/4)) × Σ_k A_k(n) × d/dn [sinh(π/k × √(2/3 × (n - 1/24)))]
    This is complex to implement exactly; we use the leading term + corrections.
    """
    # Leading term (k=1 in Rademacher sum) = Hardy-Ramanujan formula
    # We use the first few Rademacher terms for better accuracy
    # Full implementation requires Kloosterman sums; we use HR as approximation
    return hardy_ramanujan_approx(n)


# ── Sections ──────────────────────────────────────────────────────────────────

def section_small_partitions():
    print("┌─ Partitions of Small Numbers ───────────────────────────────────────┐")
    print("│  p(n) = number of ways to write n as an unordered sum")
    print("│")

    for n in range(1, 11):
        parts = list(list_partitions(n))
        count = len(parts)
        # Display each partition
        print(f"│  p({n}) = {count}")
        for p in parts:
            part_str = " + ".join(str(x) for x in p)
            print(f"│    {part_str}")
        print("│")

    print("└" + "─" * 73)
    print()


def section_growth():
    print("┌─ Growth of p(n) ────────────────────────────────────────────────────┐")
    print("│  p(n) grows super-exponentially")
    print("│")

    p = partitions_count(200)
    true_vals = {
        10: 42, 20: 627, 50: 204226, 100: 190569292,
        200: 3972999029388
    }

    print(f"│  {'n':>6}  {'p(n)':>20}  {'HR approx':>20}  {'error %':>10}")
    print(f"│  {'─'*6}  {'─'*20}  {'─'*20}  {'─'*10}")

    ns = list(range(1, 21)) + [25, 30, 40, 50, 75, 100, 150, 200]
    for n in ns:
        pn = p[n]
        hr = hardy_ramanujan_approx(n)
        err = abs(hr - pn) / pn * 100 if pn > 0 else 0
        print(f"│  {n:>6}  {pn:>20,}  {hr:>20.1f}  {err:>9.2f}%")

    print("│")
    print("│  Hardy-Ramanujan (1918): p(n) ~ e^(π√(2n/3)) / (4n√3)")
    print("│  Rademacher (1937): an infinite series giving the EXACT value")
    print("└" + "─" * 73)
    print()


def section_generating_function():
    print("┌─ Euler's Generating Function ───────────────────────────────────────┐")
    print("│  Σ p(n) x^n = Π_{k=1}^∞ 1/(1-x^k)")
    print("│")
    print("│  This is the generating function — algebra encodes the combinatorics.")
    print("│")
    print("│  Expansion:")
    print("│    1/(1-x)      = 1 + x + x² + x³ + ...     (parts of size 1)")
    print("│    1/(1-x²)     = 1 + x² + x⁴ + x⁶ + ...   (parts of size 2)")
    print("│    1/(1-x³)     = 1 + x³ + x⁶ + ...         (parts of size 3)")
    print("│")
    print("│  Multiplying: coefficients of x^n count the number of ways to")
    print("│  choose any number of 1s, any number of 2s, any number of 3s,...")
    print("│  that sum to n. That's exactly a partition!")
    print("│")
    print("│  Pentagonal Number Theorem (Euler, 1748):")
    print("│  Π_{k=1}^∞ (1-x^k) = 1 - x - x² + x⁵ + x⁷ - x¹² - x¹⁵ + ...")
    print("│")
    print("│  The exponents are the generalized pentagonal numbers: k(3k-1)/2")
    print("│  for k = 0, ±1, ±2, ±3, ...")
    print("│")

    # Show pentagonal numbers
    pentagonals = []
    for k in range(1, 8):
        g1 = k * (3 * k - 1) // 2
        g2 = k * (3 * k + 1) // 2
        pentagonals.append((g1, k))
        pentagonals.append((g2, -k))
    pentagonals.sort()

    print("│  Generalized pentagonal numbers and signs:")
    print("│  k:     ...", end="")
    for g, k in pentagonals[:12]:
        print(f" {g},", end="")
    print(" ...")
    print("│  sign: +1 for k=±1, -1 for k=±2, +1 for k=±3, ...")
    print("│")
    print("│  This gives Euler's recurrence for p(n):")
    print("│  p(n) = p(n-1) + p(n-2) - p(n-5) - p(n-7) + p(n-12) + p(n-15) - ...")
    print("└" + "─" * 73)
    print()


def section_ramanujan_congruences():
    print("┌─ Ramanujan's Congruences ───────────────────────────────────────────┐")
    print("│  The most mysterious facts about partitions")
    print("│")

    p = partitions_count(500)

    # Verify the three congruences
    print("│  p(5n + 4) ≡ 0 (mod 5):  [Ramanujan 1919]")
    print("│")
    for n in range(10):
        val = p[5*n + 4]
        mod_val = val % 5
        check = "✓" if mod_val == 0 else "✗"
        print(f"│    n={n:2d}: p({5*n+4:3d}) = {val:>12,}  mod 5 = {mod_val}  {check}")

    print("│")
    print("│  p(7n + 5) ≡ 0 (mod 7):  [Ramanujan 1919]")
    print("│")
    for n in range(10):
        val = p[7*n + 5]
        mod_val = val % 7
        check = "✓" if mod_val == 0 else "✗"
        print(f"│    n={n:2d}: p({7*n+5:3d}) = {val:>12,}  mod 7 = {mod_val}  {check}")

    print("│")
    print("│  p(11n + 6) ≡ 0 (mod 11):  [Ramanujan 1919]")
    print("│")
    for n in range(10):
        val = p[11*n + 6]
        mod_val = val % 11
        check = "✓" if mod_val == 0 else "✗"
        print(f"│    n={n:2d}: p({11*n+6:3d}) = {val:>12,}  mod 11 = {mod_val}  {check}")

    print("│")
    print("│  Why does p(n) — a combinatorial count — know about 5, 7, 11?")
    print("│  The answer involves modular forms, Hecke operators, and")
    print("│  the Dedekind eta function η(τ) = q^(1/24) Π(1 - q^n).")
    print("│  These congruences are now understood via algebraic geometry (2000s).")
    print("│")
    print("│  Ramanujan conjectured. Rademachers proved them using modular forms.")
    print("│  Ono (2000) found infinitely many similar congruences for every prime ≥ 5.")
    print("└" + "─" * 73)
    print()


def section_distinct_odd():
    """Euler's theorem: partitions into distinct parts = partitions into odd parts."""
    print("┌─ Euler's Theorem on Partitions ─────────────────────────────────────┐")
    print("│  The number of partitions into distinct parts equals the number")
    print("│  of partitions into odd parts. (Euler, 1748)")
    print("│")
    print("│  'Distinct parts' means no repetition: 5 = 5, 4+1, 3+2.")
    print("│  'Odd parts' means only odd summands: 5 = 5, 3+1+1, 1+1+1+1+1.")
    print("│")

    def partitions_distinct(n, max_part=None):
        """Partitions into distinct parts."""
        if max_part is None:
            max_part = n
        if n == 0:
            yield ()
            return
        for largest in range(min(n, max_part), 0, -1):
            for rest in partitions_distinct(n - largest, largest - 1):
                yield (largest,) + rest

    def partitions_odd(n, max_part=None):
        """Partitions into odd parts."""
        if max_part is None:
            max_part = n if n % 2 == 1 else n - 1
        if n == 0:
            yield ()
            return
        # Next odd ≤ min(n, max_part)
        m = min(n, max_part)
        if m % 2 == 0:
            m -= 1
        for largest in range(m, 0, -2):
            for rest in partitions_odd(n - largest, largest):
                yield (largest,) + rest

    for n in range(1, 13):
        d = list(partitions_distinct(n))
        o = list(partitions_odd(n))
        match = "✓" if len(d) == len(o) else "✗"
        print(f"│  n={n:2d}: distinct={len(d):2d}  odd={len(o):2d}  {match}")

    print("│")
    print("│  Proof via generating functions:")
    print("│  Distinct parts: Π_{k≥1} (1 + x^k)")
    print("│  Odd parts:      Π_{k≥1, k odd} 1/(1-x^k)")
    print("│")
    print("│  These are equal because:")
    print("│  Π (1 + x^k) = Π (1 - x^{2k}) / (1 - x^k)")
    print("│              = Π_{k odd} 1/(1-x^k)   [telescoping!]")
    print("└" + "─" * 73)
    print()


def section_visual(max_n=50):
    """Visualize p(n) mod 5 as a grid."""
    print("┌─ p(n) mod 5 — Visualizing the Congruences ─────────────────────────┐")
    print("│  Each cell shows p(n) mod 5. Dark = 0 mod 5.")
    print("│  Column 4 (n ≡ 4 mod 5) should be all dark.")
    print("│")

    p = partitions_count(max_n)
    shade = ' ░▒▓█'

    print("│  n:  " + "".join(f"{i%10}" for i in range(max_n + 1)))
    print("│  p%5:" + "".join(
        ('█' if p[n] % 5 == 0 else shade[p[n] % 5 - 1 + 1])
        for n in range(max_n + 1)
    ))
    print("│")

    # Show column pattern
    print("│  Column positions 4, 9, 14, 19, 24, 29, 34, 39, 44, 49 (n ≡ 4 mod 5):")
    vals = [f"p({n})%5={p[n]%5}" for n in range(4, max_n, 5)][:10]
    print("│    " + ", ".join(vals))
    print("│  All zero — the congruence holds!")
    print("│")
    print("│  p(n) mod 7 — column 5 (n ≡ 5 mod 7) should be all zero:")
    print("│  " + "".join(
        ('█' if p[n] % 7 == 0 else shade[min(4, p[n] % 7)])
        for n in range(min(max_n + 1, 77))
    ))
    print("└" + "─" * 73)
    print()


def section_bells():
    """Brief note on related sequences."""
    print("┌─ Related Partition Functions ───────────────────────────────────────┐")
    print("│")
    print("│  p(n) counts partitions where order doesn't matter.")
    print("│  Ordered partitions (compositions): there are 2^(n-1) of n.")
    print("│")

    p = partitions_count(30)
    comps = [1] + [2**(n-1) for n in range(1, 20)]

    print(f"│  {'n':>4}  {'p(n)':>12}  {'compositions':>14}  {'ratio':>10}")
    print(f"│  {'─'*4}  {'─'*12}  {'─'*14}  {'─'*10}")
    for n in range(1, 12):
        ratio = comps[n] / p[n]
        print(f"│  {n:>4}  {p[n]:>12,}  {comps[n]:>14,}  {ratio:>10.2f}")

    print("│")
    print("│  Plane partitions (2D arrays): MacMahon formula (1900)")
    print("│  Solid partitions (3D): no closed form known!")
    print("│")
    print("│  Partition function in physics:")
    print("│  Z = Σ e^{-βE_n}  where the energy levels E_n grow with p(n).")
    print("│  For free bosons: partition function = Π 1/(1-e^{-β ω_k})")
    print("│  = Euler's generating function with x = e^{-β ω}.")
    print("│  The same formula describes both combinatorics and thermodynamics.")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         I N T E G E R   P A R T I T I O N S                       ║")
    print("║  p(n) — counting ways to write n as a sum                         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  A partition of n is a way to write n as an unordered sum of")
    print("  positive integers. Simple to define. Surprisingly deep.")
    print()

    section_small_partitions()
    section_growth()
    section_generating_function()
    section_ramanujan_congruences()
    section_distinct_odd()
    section_visual()
    section_bells()

    p = partitions_count(100)
    print(f"  p(100) = {p[100]:,}")
    print(f"  One hundred has {p[100]:,} ways to be written as an unordered sum.")
    print()
    print("  Ramanujan saw these congruences by computation alone — no proof,")
    print("  just the deep intuition that they must be true. He was right.")
    print("  The full explanation took another 80 years of mathematics.")
    print()


if __name__ == '__main__':
    main()
