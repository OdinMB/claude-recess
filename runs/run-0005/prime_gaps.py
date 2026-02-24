"""
Prime Gaps

Between consecutive primes, there are gaps. These gaps form a sequence
whose behavior is one of the deepest mysteries in mathematics.

Twin primes: primes that differ by 2. (3,5), (5,7), (11,13), ...
Twin Prime Conjecture: there are infinitely many. Unproven since antiquity.

Cramér's conjecture (1936): the maximal gap after prime p is O((log p)²).
Empirical data supports this beautifully, but it's unproven.

Zhang's theorem (2013): there exist infinitely many primes that differ by
at most 70,000,000. The first finite bound on prime gaps — a revolution.

Polymath 8 (2013-2014): the bound was rapidly reduced to 246.
Maynard (2013-2014): an independent, simpler proof; bound reduced further.

Assuming Elliott-Halberstam conjecture: the bound is 6 (almost twin primes!).
Under GRH + EH: bound 2 (the twin prime conjecture itself).

The gap between knowing "gaps are bounded" and knowing "gaps of 2 recur"
is the difference between a theorem and the twin prime conjecture.
"""

import math
from collections import Counter


def sieve(n):
    """Return all primes up to n."""
    composite = bytearray(n + 1)
    composite[0] = composite[1] = 1
    for i in range(2, int(n**0.5) + 1):
        if not composite[i]:
            composite[i*i::i] = b'\x01' * len(composite[i*i::i])
    return [i for i in range(2, n + 1) if not composite[i]]


def prime_gaps(primes):
    """Return list of gaps between consecutive primes."""
    return [primes[i+1] - primes[i] for i in range(len(primes) - 1)]


def maximal_gaps(primes):
    """
    Return list of (gap, prime) where gap is a new record maximal gap
    following that prime.
    """
    records = []
    max_gap = 0
    gaps = prime_gaps(primes)
    for i, g in enumerate(gaps):
        if g > max_gap:
            max_gap = g
            records.append((g, primes[i]))
    return records


def cramer_ratio(gap, p):
    """gap / (log p)² — should be ≤ 1 by Cramér's conjecture."""
    return gap / (math.log(p) ** 2)


# ── Sections ──────────────────────────────────────────────────────────────────

def section_gap_distribution(limit=100_000):
    print("┌─ Gap Distribution ──────────────────────────────────────────────────┐")
    print(f"│  Gaps between consecutive primes up to {limit:,}")
    print("│")

    primes = sieve(limit)
    gaps = prime_gaps(primes)
    freq = Counter(gaps)

    # All gaps are even except the first (2→3, gap=1)
    even_gaps = {g: c for g, c in freq.items() if g % 2 == 0}
    total = len(gaps)

    print(f"│  Total primes: {len(primes):,}   Total gaps: {total:,}")
    print(f"│  Mean gap: {sum(gaps)/len(gaps):.2f}  (ln({limit:,}) ≈ {math.log(limit):.2f})")
    print("│")
    print("│  Gap size  Count    %       Bar")
    print("│  ────────  ─────    ──      ───")

    for gap in sorted(even_gaps.keys())[:20]:
        count = even_gaps[gap]
        pct = count / total * 100
        bar_len = int(pct * 2)
        bar = '█' * bar_len
        twin = "  ← twin primes" if gap == 2 else ""
        print(f"│  {gap:6d}    {count:6d}   {pct:5.2f}%  {bar}{twin}")

    # How many gaps > 100?
    large = sum(c for g, c in freq.items() if g > 100)
    print(f"│")
    print(f"│  Gaps > 100: {large:,}")
    print(f"│  Largest gap in range: {max(gaps)} (after prime {primes[gaps.index(max(gaps))]:,})")
    print("│")
    print("│  Note: all gaps are even (both endpoints odd primes) except gap=1.")
    print("│  Divisibility explains the even-gap preference — multiples of 6 ± 1.")
    print("└" + "─" * 73)
    print()


def section_twin_primes(limit=100_000):
    print("┌─ Twin Primes ───────────────────────────────────────────────────────┐")
    print("│  Pairs of primes differing by 2")
    print("│")

    primes = sieve(limit)
    twins = [(p, p+2) for p in primes if p+2 in set(primes)]

    print(f"│  Twin prime pairs up to {limit:,}: {len(twins):,}")
    print("│")
    print("│  First 20 twin prime pairs:")
    for i, (p, q) in enumerate(twins[:20]):
        print(f"│    ({p}, {q})")
    print("│")

    # Density comparison
    print("│  Density of twin primes vs all primes:")
    checkpoints = [1000, 5000, 10000, 50000, 100000]
    prime_set = set(primes)
    print(f"│  {'x':>8}  {'π(x)':>8}  {'π₂(x)':>8}  {'π₂/π':>8}  {'Expected ~2C₂/ln²x':>20}")
    print(f"│  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*20}")

    C2 = 0.6601618158  # Twin prime constant
    for x in checkpoints:
        pi_x = sum(1 for p in primes if p <= x)
        twins_x = sum(1 for p in primes if p <= x and p+2 in prime_set)
        ratio = twins_x / pi_x if pi_x else 0
        expected = 2 * C2 / math.log(x)**2 * x  # Approx count ≈ 2C₂ x/ln²x
        print(f"│  {x:>8,}  {pi_x:>8,}  {twins_x:>8,}  {ratio:>8.4f}  {expected:>20.1f}")

    print("│")
    print("│  The Twin Prime Constant C₂ = Π_{p odd prime} p(p-2)/(p-1)² ≈ 0.6602")
    print("│  Hardy-Littlewood conjecture: π₂(x) ~ 2C₂ x / (ln x)²")
    print("│  Unproven — we don't even know if there are infinitely many.")
    print("└" + "─" * 73)
    print()


def section_maximal_gaps(limit=1_000_000):
    print("┌─ Record Prime Gaps (Maximal Gaps) ──────────────────────────────────┐")
    print("│  Each entry: the largest gap seen so far between consecutive primes")
    print("│")

    primes = sieve(limit)
    records = maximal_gaps(primes)

    print(f"│  {'Gap':>6}  {'After prime':>12}  {'Cramér ratio':>14}  {'log p':>8}")
    print(f"│  {'─'*6}  {'─'*12}  {'─'*14}  {'─'*8}")

    for gap, p in records:
        cr = cramer_ratio(gap, p)
        lp = math.log(p)
        print(f"│  {gap:6d}  {p:>12,}  {cr:>14.4f}  {lp:>8.3f}")

    print("│")
    print("│  Cramér's conjecture: maximal gap after p should be ~ (log p)²")
    print(f"│  Max Cramér ratio seen (up to {limit:,}): {max(cramer_ratio(g, p) for g, p in records):.4f}")
    print("│  (Should stay ≤ 1 if Cramér is correct — so far it does)")
    print("│")
    print("│  Known maximal gap record (as of 2023): gap 1510 after prime 18,361,375,334,787,046,697")
    print("│  Cramér ratio ≈ 0.921 — tantalizingly close to 1 but never exceeding it")
    print("└" + "─" * 73)
    print()


def section_gap_fingerprint(limit=5000):
    """Visualize the gap sequence as a 2D fingerprint."""
    print("┌─ Gap Sequence Fingerprint ──────────────────────────────────────────┐")
    print("│  The sequence of prime gaps, visualized")
    print("│  Each column = a gap. Height encodes gap size. Lighter = smaller gap.")
    print("│")

    primes = sieve(limit)
    gaps = prime_gaps(primes)

    WIDTH = 70
    HEIGHT = 20
    max_gap = max(gaps)

    # Sample gaps to fill width
    n = len(gaps)
    sampled = [gaps[int(i * (n-1) / (WIDTH-1))] for i in range(WIDTH)]

    shade = ' ░▒▓█'

    # Build column heights
    rows = []
    for row in range(HEIGHT, 0, -1):
        threshold = row / HEIGHT * max_gap
        line = "│  "
        for g in sampled:
            frac = g / max_gap
            idx = int(frac * (len(shade) - 1))
            char = shade[idx] if g >= threshold else ' '
            line += char
        rows.append(line)

    for row in rows:
        print(row)

    print("│")
    print(f"│  x-axis: prime index 1 to {len(primes):,}  (primes up to {limit:,})")
    print(f"│  y-axis: gap size, max = {max_gap}")
    print("│  The 'stripes' are gaps that recur — especially gap=2 (twin primes)")
    print("│  and gap=6 (the most common gap for large primes due to mod 6 arithmetic)")
    print("└" + "─" * 73)
    print()


def section_gap_structure():
    print("┌─ Structure in Gaps ─────────────────────────────────────────────────┐")
    print("│")
    print("│  Why most gaps are multiples of 6:")
    print("│")
    print("│  Every integer is one of: 6k, 6k+1, 6k+2, 6k+3, 6k+4, 6k+5")
    print("│  Primes > 3 must be of the form 6k±1 (else divisible by 2 or 3)")
    print("│  So gaps between primes must bridge from one 6k±1 to another:")
    print("│")

    forms = {
        (1, 1): "6k+1 → 6k+1",
        (1, 5): "6k+1 → 6(k+1)-1",
        (5, 1): "6k-1 → 6k+1",
        (5, 5): "6k-1 → 6(k+1)-1",
    }

    examples = {
        (1, 1): 6,   # e.g., 7→13
        (1, 5): 4,   # e.g., 7→11
        (5, 1): 2,   # e.g., 5→7
        (5, 5): 6,   # e.g., 11→17
    }

    print("│  Transition      Min gap  Example")
    for key, name in forms.items():
        gap = examples[key]
        primes = sieve(50)
        # Find an example
        prime_set = set(primes)
        ex = ""
        for p in primes:
            if p % 6 == key[0] % 6 or (key[0] == 5 and p % 6 == 5):
                next_p = p + gap
                if next_p in prime_set:
                    if (p % 6 == (key[0] % 6) or (key[0] == 5 and p % 6 == 5)):
                        ex = f"{p}→{next_p}"
                        break
        print(f"│    {name:<20s}  {gap}        {ex}")

    print("│")
    print("│  Gaps of 2 (twin primes): both numbers are 6k±1 with the ± flipping")
    print("│  Gaps of 4: from 6k+1 to 6k+5 (= 6(k+1)-1)")
    print("│  Gaps of 6: most common for large primes — from 6k-1 to 6(k+1)-1")
    print("│                                           or from 6k+1 to 6(k+1)+1")
    print("│")
    print("│  Prime constellations: patterns like (0, 2, 6, 8) = prime 4-tuple")
    print("│  First: 5, 7, 11, 13 — the 'prime quadruple'")
    print("│  These have their own (unproven) Hardy-Littlewood conjectures")
    print("└" + "─" * 73)
    print()


def section_zhang():
    print("┌─ Zhang's Theorem and Bounded Gaps ─────────────────────────────────┐")
    print("│")
    print("│  Before 2013: we knew prime gaps grew (on average) like ln p.")
    print("│  But did infinitely many gaps stay bounded? Unknown.")
    print("│")
    print("│  May 2013: Yitang Zhang (then unknown lecturer, UNH) proved:        ")
    print("│")
    print("│    lim inf (p_{n+1} - p_n) < 70,000,000")
    print("│")
    print("│  That is: infinitely many consecutive prime pairs differ by < 70M.")
    print("│  Zhang's proof: a sieve method (GPY sieve), admissible k-tuples,")
    print("│  exponential sum estimates, and a Bombieri-Vinogradov-type result")
    print("│  with a carefully chosen level of distribution.")
    print("│")
    print("│  The bound improved rapidly (Polymath 8, Maynard 2013-2014):")
    print("│")
    improvements = [
        ("Zhang (May 2013)",              70_000_000),
        ("Scott Morrison",                59_470_640),
        ("Polymath 8a (Jul 2013)",         4_680_000),
        ("Polymath 8a (Jul 2013)",           247_000),
        ("Polymath 8a (Aug 2013)",            12_006),
        ("Maynard (Nov 2013)",                   600),
        ("Polymath 8b (Dec 2013)",               270),
        ("Polymath 8b (2014)",                   246),
    ]

    for who, bound in improvements:
        bar_len = max(1, int(math.log10(bound) * 5))
        bar = '█' * bar_len
        print(f"│    {who:<30s}  {bound:>12,}  {bar}")

    print("│")
    print("│  Current best unconditional bound: 246")
    print("│  Assuming Elliott-Halberstam conjecture: 6")
    print("│  Assuming EH + GRH: 2  (the Twin Prime Conjecture itself)")
    print("│")
    print("│  Zhang's proof was a sensation — pure mathematics, no computation,")
    print("│  by someone working in near-isolation. A reminder that deep results")
    print("│  can come from unexpected places.")
    print("└" + "─" * 73)
    print()


def section_prime_desert(limit=500_000):
    """Find prime deserts — long stretches with no primes."""
    print("┌─ Prime Deserts ─────────────────────────────────────────────────────┐")
    print("│  Large gaps: stretches where no primes appear")
    print("│")

    primes = sieve(limit)
    gaps = prime_gaps(primes)

    # Find top 15 largest gaps
    gap_with_prime = sorted(zip(gaps, primes[:-1]), reverse=True)[:15]

    print(f"│  {'Gap':>6}  {'After prime':>12}  {'Desert':>25}  {'Cramér':>8}")
    print(f"│  {'─'*6}  {'─'*12}  {'─'*25}  {'─'*8}")

    for gap, p in gap_with_prime:
        cr = cramer_ratio(gap, p)
        desert = f"{p+1} .. {p+gap-1}"
        print(f"│  {gap:6d}  {p:>12,}  {desert:>25}  {cr:>8.4f}")

    print("│")
    print("│  Primorial gaps: p# + 2 through p# + p_next - 1 are all composite")
    print("│  (all divisible by one of 2, 3, 5, ..., p)")
    print("│")
    print("│  Smallest guaranteed desert of length n:")
    for n in [10, 20, 50, 100]:
        # (n+1)! + 2 through (n+1)! + n are all composite
        start = math.factorial(n + 1) + 2
        print(f"│    Length ≥ {n:3d}: starting at {n+1}! + 2 = {start:,}")
    print("│  (These are just guaranteed minimums — actual first occurrence is much earlier)")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           P R I M E   G A P S                                      ║")
    print("║  The spaces between primes — and what they reveal                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  Between every pair of consecutive primes is a gap.")
    print("  These gaps are where the deepest mysteries of number theory live.")
    print()

    section_gap_distribution()
    section_twin_primes()
    section_maximal_gaps()
    section_gap_fingerprint()
    section_gap_structure()
    section_prime_desert()
    section_zhang()

    print("  The gap between what we know and what we suspect:")
    print("  We can prove gaps are sometimes bounded (Zhang, 2013).")
    print("  We cannot prove they are sometimes 2 (Twin Prime Conjecture).")
    print("  The distance from 246 to 2 is 244 — and also infinite.")
    print()


if __name__ == '__main__':
    main()
