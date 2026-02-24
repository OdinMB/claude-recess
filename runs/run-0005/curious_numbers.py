"""
A Cabinet of Curious Numbers

Numbers with unusual or beautiful properties.
Some are ancient discoveries; some are modern. Some have deep
connections to mathematics; some are recreational curiosities.

Each is a small window into number theory.
"""

import math
import itertools
from functools import reduce


def divisors(n):
    """Return all proper divisors of n (all divisors except n itself)."""
    if n <= 1:
        return []
    divs = [1]
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    return sorted(divs)


def sigma(n):
    """Sum of proper divisors of n."""
    return sum(divisors(n))


def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0: return False
    return True


def digit_power_sum(n, power):
    """Sum of digits each raised to given power."""
    return sum(int(d)**power for d in str(n))


# ── Perfect Numbers ────────────────────────────────────────────────────────────

def section_perfect():
    print("┌─ Perfect Numbers ───────────────────────────────────────────────────────┐")
    print("│  A perfect number equals the sum of its proper divisors.")
    print("│  Known since ancient Greece (Euclid proved infinitely many exist if")
    print("│  Mersenne primes are infinite — still unproven).")
    print("│  No odd perfect number has ever been found.")
    print("│")

    perfect = []
    for n in range(2, 10000):
        if sigma(n) == n:
            perfect.append(n)

    for n in perfect:
        divs = divisors(n)
        divs_str = '+'.join(str(d) for d in divs)
        print(f"│  {n:6d} = {divs_str}")

    print("│")
    print("│  The next perfect number is 33,550,336 (too large to show here).")
    print("│  Known perfect numbers: 6, 28, 496, 8128, 33550336, 8589869056, ...")
    print("│  All known perfect numbers are even. Are there odd ones? Unknown.")
    print("└" + "─" * 73)
    print()


# ── Amicable Numbers ───────────────────────────────────────────────────────────

def section_amicable():
    print("┌─ Amicable Numbers ──────────────────────────────────────────────────────┐")
    print("│  Two numbers are amicable if each is the sum of the other's divisors.")
    print("│  Known to Pythagoras. 220 and 284 are the first pair.")
    print("│  Thabit ibn Qurra (836–901) found a formula for generating some pairs.")
    print("│")

    amicable = []
    for n in range(2, 10000):
        m = sigma(n)
        if m != n and m > n and sigma(m) == n:
            amicable.append((n, m))

    for a, b in amicable:
        print(f"│  ({a:5d}, {b:5d})")
        print(f"│         σ({a}) = {sigma(a)} = {b}")
        print(f"│         σ({b}) = {sigma(b)} = {a}")
        print("│")

    print("└" + "─" * 73)
    print()


# ── Happy Numbers ──────────────────────────────────────────────────────────────

def section_happy():
    print("┌─ Happy Numbers ─────────────────────────────────────────────────────────┐")
    print("│  A number is happy if repeatedly summing the squares of its digits")
    print("│  eventually reaches 1. Unhappy numbers cycle to ...89→145→42→...")
    print("│")

    def happy_sequence(n, max_steps=30):
        seen = set()
        seq = [n]
        while n != 1 and n not in seen:
            seen.add(n)
            n = digit_power_sum(n, 2)
            seq.append(n)
        return seq, n == 1

    happy_nums = []
    for n in range(1, 150):
        _, is_happy = happy_sequence(n)
        if is_happy:
            happy_nums.append(n)

    print(f"│  Happy numbers up to 150: {', '.join(str(n) for n in happy_nums)}")
    print(f"│  ({len(happy_nums)} out of 150 = {100*len(happy_nums)/150:.1f}%)")
    print("│")

    # Show sequences for first few
    for n in [7, 19, 44, 89]:
        seq, is_happy = happy_sequence(n)
        emoji = "→ 1 ✓" if is_happy else "→ cycle"
        seq_str = " → ".join(str(x) for x in seq[:10])
        if len(seq) > 10:
            seq_str += " → ..."
        print(f"│  {n:3d}: {seq_str} {emoji}")

    print("└" + "─" * 73)
    print()


# ── Kaprekar Constant ──────────────────────────────────────────────────────────

def section_kaprekar():
    print("┌─ Kaprekar Routine ──────────────────────────────────────────────────────┐")
    print("│  D.R. Kaprekar (1949): take any 4-digit number (not all same digits).")
    print("│  Sort digits descending and ascending, subtract. Repeat.")
    print("│  You always reach 6174 — the 'Kaprekar constant' — in ≤7 steps.")
    print("│")

    def kaprekar_step(n):
        digits = sorted(f"{n:04d}")
        asc = int(''.join(digits))
        desc = int(''.join(reversed(digits)))
        return desc - asc

    def kaprekar_sequence(n):
        seq = [n]
        while n != 6174:
            n = kaprekar_step(n)
            seq.append(n)
            if len(seq) > 20:
                break
        return seq

    for start in [1000, 1234, 3524, 9999, 5432, 1111, 2020]:
        if len(set(f"{start:04d}")) == 1:
            print(f"│  {start:4d}: (all same digits — not valid)")
            continue
        seq = kaprekar_sequence(start)
        seq_str = " → ".join(str(x) for x in seq)
        print(f"│  {start:4d}: {seq_str}  ({len(seq)-1} steps)")

    print("│")
    print("│  6174 = 7641 - 1467 (it's a fixed point of the routine)")
    print("│  The 3-digit version converges to 495.")
    print("└" + "─" * 73)
    print()


# ── Narcissistic Numbers ───────────────────────────────────────────────────────

def section_narcissistic():
    print("┌─ Narcissistic Numbers ──────────────────────────────────────────────────┐")
    print("│  An n-digit number that equals the sum of its digits each raised to")
    print("│  the n-th power. Also called 'pluperfect digital invariants'.")
    print("│")

    narcissistic = []
    for n in range(1, 100000):
        d = len(str(n))
        if digit_power_sum(n, d) == n:
            narcissistic.append(n)

    for n in narcissistic:
        d = len(str(n))
        formula = '+'.join(f"{ch}^{d}" for ch in str(n))
        result = '+'.join(str(int(ch)**d) for ch in str(n))
        print(f"│  {n:7d} = {formula} = {result} = {n}")

    print("│")
    print("│  There are exactly 88 narcissistic numbers (in base 10).")
    print("│  The largest is 39-digit: 115,132,219,018,763,992,565,095,597,973,971,522,401")
    print("└" + "─" * 73)
    print()


# ── Sociable Chains ────────────────────────────────────────────────────────────

def section_sociable():
    print("┌─ Sociable Number Chains ────────────────────────────────────────────────┐")
    print("│  A sociable chain: σ(a)=b, σ(b)=c, ..., σ(z)=a")
    print("│  Perfect numbers are chains of length 1; amicable are length 2.")
    print("│  Long chains (≥3) are rare.")
    print("│")

    # Find chains up to 10000
    visited = set()
    chains = []

    for start in range(2, 10000):
        if start in visited:
            continue
        chain = [start]
        n = sigma(start)
        while n not in chain and n not in visited and len(chain) < 20:
            chain.append(n)
            n = sigma(chain[-1])

        if n in chain:
            # Found a cycle
            cycle_start = chain.index(n)
            cycle = chain[cycle_start:]
            if len(cycle) >= 3:
                if not any(c[0] in visited for c in chains):
                    chains.append(cycle)
                for x in cycle:
                    visited.add(x)

    if chains:
        for chain in chains[:3]:
            print(f"│  Chain of length {len(chain)}: {' → '.join(str(x) for x in chain)} → {chain[0]}")
    else:
        print("│  No sociable chains of length ≥ 3 found below 10,000.")
        print("│  The first one starts at 12,496:  12496 → 14288 → 15472 → 14536 → 14264 → 12496")

    print("└" + "─" * 73)
    print()


# ── Digit Curiosities ──────────────────────────────────────────────────────────

def section_digit_curiosities():
    print("┌─ Digit Curiosities ─────────────────────────────────────────────────────┐")
    print("│")
    print("│  Automorphic numbers: n² ends in n")
    autos = [n for n in range(1, 10000) if str(n*n).endswith(str(n))]
    print(f"│  {', '.join(str(n) for n in autos[:10])} ...")
    print("│")

    print("│  Cyclic numbers: 142857 × 1..6 = permutations of 142857")
    n = 142857
    for k in range(1, 7):
        result = n * k
        print(f"│  142857 × {k} = {result:7d} (digits: {''.join(sorted(str(result)))} vs 124578)")
    print("│")

    print("│  Kaprekar numbers: 9² = 81, 8+1 = 9")
    print("│  n such that n² split into two parts summing to n:")
    kaprekar_sq = []
    for n in range(1, 10000):
        sq = str(n*n)
        for split in range(1, len(sq)):
            left = int(sq[:split]) if sq[:split] else 0
            right = int(sq[split:]) if sq[split:] else 0
            if left + right == n and right > 0:
                kaprekar_sq.append((n, sq, left, right))
                break
    for n, sq, l, r in kaprekar_sq[:10]:
        print(f"│  {n:5d}² = {sq}  →  {l}+{r} = {n}")
    print("│")

    print("│  Fibonacci identities:")
    a, b = 1, 1
    fibs = [1, 1]
    for _ in range(15):
        a, b = b, a+b
        fibs.append(b)

    print("│  Sum of first n Fibonacci²: 1+1+4+9+25+64 = 104 = 8×13 = F(6)×F(7)")
    for n in range(2, 9):
        s = sum(f**2 for f in fibs[:n])
        product = fibs[n-1] * fibs[n]
        print(f"│  Σ F(k)² for k=1..{n}: {s:6d} = F({n-1})×F({n}) = {fibs[n-1]}×{fibs[n]} = {product}  {'✓' if s==product else '✗'}")
    print("└" + "─" * 73)
    print()


# ── Collatz statistics ─────────────────────────────────────────────────────────

def section_look_and_say():
    print("┌─ Look-and-Say Sequence ─────────────────────────────────────────────────┐")
    print("│  John Conway (1986): describe the previous number.")
    print("│  1 → 11 (one 1) → 21 (two 1s) → 1211 → 111221 → ...")
    print("│  Length grows by Conway's constant: λ ≈ 1.303577269...")
    print("│")

    def look_and_say(s):
        result = ''
        i = 0
        while i < len(s):
            ch = s[i]
            count = 1
            while i + count < len(s) and s[i + count] == ch:
                count += 1
            result += str(count) + ch
            i += count
        return result

    seq = "1"
    for step in range(12):
        print(f"│  {step:2d}: {seq[:60]}{'...' if len(seq) > 60 else ''}")
        print(f"│      length = {len(seq)}")
        seq = look_and_say(seq)

    print("│")
    print("│  Conway proved: the sequence eventually splits into 92 'elements'")
    print("│  that evolve independently (like chemical elements). For example,")
    print("│  '22' is stable (stays as '22'), '3' becomes '13' becomes '1113' ...")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         A   C A B I N E T   O F   C U R I O U S   N U M B E R S   ║")
    print("║  Mathematical objects with unusual or beautiful properties          ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    section_perfect()
    section_amicable()
    section_happy()
    section_kaprekar()
    section_narcissistic()
    section_sociable()
    section_digit_curiosities()
    section_look_and_say()


if __name__ == '__main__':
    main()
