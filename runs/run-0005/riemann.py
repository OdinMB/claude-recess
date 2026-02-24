"""
The Riemann Zeta Function

Bernhard Riemann (1859): a 8-page paper that changed mathematics.

The zeta function: ζ(s) = 1 + 1/2^s + 1/3^s + 1/4^s + ...

Euler had studied this for real s > 1. Riemann extended it to the
complex plane and discovered a deep connection to prime numbers:

    ζ(s) = Π_{p prime} 1/(1 - p^(-s))     [Euler product]

This identity encodes the fundamental theorem of arithmetic:
the connection between every integer (the sum) and every prime (the product).

The non-trivial zeros of ζ(s) — complex numbers where ζ(s) = 0 —
control the distribution of prime numbers.

The Riemann Hypothesis: all non-trivial zeros have real part 1/2.
Equivalently: the "errors" in the prime counting function are
as small as they possibly could be.

Unproven since 1859. One of the Millennium Prize Problems ($1,000,000).
"""

import math
import cmath


def zeta_real(s, terms=10000):
    """
    Compute ζ(s) for real s > 1 using the series.
    For s ≤ 1 the series diverges (must use analytic continuation).
    """
    if s <= 1:
        return float('inf')
    return sum(1 / n**s for n in range(1, terms + 1))


def euler_product(s, primes):
    """Compute Euler product up to given primes: Π 1/(1-p^(-s))."""
    result = 1.0
    for p in primes:
        factor = 1.0 / (1 - p**(-s))
        result *= factor
    return result


def sieve(n):
    """Return all primes up to n."""
    composite = [False] * (n + 1)
    composite[0] = composite[1] = True
    for i in range(2, int(n**0.5) + 1):
        if not composite[i]:
            for j in range(i*i, n + 1, i):
                composite[j] = True
    return [i for i in range(2, n + 1) if not composite[i]]


def zeta_partial_sum(s, n):
    """Partial sum: Σ_{k=1}^{n} k^(-s)"""
    return sum(1 / k**s for k in range(1, n + 1))


def prime_counting(x):
    """π(x) = number of primes ≤ x."""
    primes = sieve(int(x))
    return len(primes)


def prime_counting_approx(x):
    """Li(x) = ∫_2^x dt/ln(t) ≈ x/ln(x) — the asymptotic approximation."""
    if x < 2:
        return 0
    return x / math.log(x)


def li(x, terms=100):
    """Logarithmic integral Li(x) = PV ∫_0^x dt/ln(t).
    Uses the series: Li(x) = γ + ln(ln(x)) + Σ ln(x)^k/(k·k!)"""
    if x <= 0:
        return 0
    t = math.log(x)
    result = 0.577216 + math.log(abs(t))  # γ + ln|ln(x)|
    power_t = t
    factorial = 1
    for k in range(1, terms):
        factorial *= k
        result += power_t / (k * factorial)
        power_t *= t
        if abs(power_t / (k * factorial)) < 1e-12:
            break
    return result


def section_euler_product():
    print("┌─ Euler Product Formula ─────────────────────────────────────────────┐")
    print("│  ζ(s) = Σ n^(-s) = Π_p 1/(1-p^(-s))")
    print("│  The sum over all integers equals a product over all primes.")
    print("│  This is the fundamental theorem of arithmetic made analytic.")
    print("│")
    print("│  Convergence of ζ(2) = π²/6 ≈ 1.6449...")
    print("│")

    primes = sieve(1000)
    true_val = math.pi**2 / 6

    print(f"│  {'Method':<35s}  {'Value':>12s}  {'Error':>10s}")
    print(f"│  {'─'*35}  {'─'*12}  {'─'*10}")

    for n in [10, 50, 100, 500, 1000, 10000]:
        series_val = zeta_partial_sum(2, n)
        err = abs(series_val - true_val)
        print(f"│  Series: Σ 1/k²  k=1..{n:<6d}  {series_val:>12.8f}  {err:>10.2e}")

    print("│")
    for n_primes in [10, 25, 50, 100, 168]:  # 168 = π(1000)
        ep_val = euler_product(2, primes[:n_primes])
        err = abs(ep_val - true_val)
        print(f"│  Euler product: {n_primes:3d} primes      {ep_val:>12.8f}  {err:>10.2e}")

    print("│")
    print(f"│  True value: π²/6 = {true_val:.10f}")
    print("└" + "─" * 73)
    print()


def section_special_values():
    print("┌─ Special Values of ζ(s) ────────────────────────────────────────────┐")
    print("│")
    print("│  For positive even integers, ζ(2n) = rational × π^(2n):")
    print("│  This was proven by Euler. For odd integers, no closed form is known.")
    print("│")

    values = [
        (2,   "π²/6",          math.pi**2 / 6),
        (3,   "Apéry's constant", None),  # ζ(3) ≈ 1.2020569...
        (4,   "π⁴/90",         math.pi**4 / 90),
        (6,   "π⁶/945",        math.pi**6 / 945),
        (8,   "π⁸/9450",       math.pi**8 / 9450),
        (10,  "π¹⁰/93555",     math.pi**10 / 93555),
    ]

    APERY = 1.2020569031595942854  # Apéry's constant ζ(3)

    for s, name, expected in values:
        computed = zeta_partial_sum(s, 100000)
        if expected is None:
            expected = APERY
        err = abs(computed - expected)
        rational = ""
        if s == 3:
            rational = f" ← irrational (Apéry 1978), transcendental?"
        print(f"│  ζ({s:2d}) = {computed:.10f}  [{name}]{rational}")

    print("│")
    print("│  ζ(1) = 1 + 1/2 + 1/3 + 1/4 + ...  →  ∞  (harmonic series diverges)")
    print("│  ζ(0) = -1/2  (by analytic continuation)")
    print("│  ζ(-1) = -1/12  ← the famous '1+2+3+4+... = -1/12' (regularization)")
    print("│  ζ(-2) = ζ(-4) = ζ(-6) = ... = 0  (trivial zeros)")
    print("└" + "─" * 73)
    print()


def section_prime_connection():
    print("┌─ Primes and the Zeta Function ──────────────────────────────────────┐")
    print("│  The prime counting function π(x) and its approximations")
    print("│")
    print(f"│  {'x':>10s}  {'π(x)':>8s}  {'x/ln(x)':>12s}  {'Error':>10s}  {'Li(x)':>12s}  {'Error':>10s}")
    print(f"│  {'─'*10}  {'─'*8}  {'─'*12}  {'─'*10}  {'─'*12}  {'─'*10}")

    for x in [10, 50, 100, 500, 1000, 5000, 10000, 50000]:
        pi_x = prime_counting(x)
        approx = prime_counting_approx(x)
        li_x = li(x)
        err1 = abs(pi_x - approx)
        err2 = abs(pi_x - li_x)
        print(f"│  {x:>10,d}  {pi_x:>8d}  {approx:>12.2f}  {err1:>10.2f}  {li_x:>12.2f}  {err2:>10.2f}")

    print("│")
    print("│  Li(x) (logarithmic integral) is a much better approximation.")
    print("│  The Riemann Hypothesis: |π(x) - Li(x)| = O(√x × log(x))")
    print("│  Known unconditionally: |π(x) - Li(x)| < some larger bound")
    print("│")
    print("│  Riemann showed that the exact error involves the zeros of ζ(s):")
    print("│")
    print("│    π(x) = Li(x) - Σ_{ρ: ζ(ρ)=0} Li(x^ρ) + small terms")
    print("│")
    print("│  If all zeros have real part 1/2, the errors are √x × log(x).")
    print("│  Each non-trivial zero with real part ≠ 1/2 would make the errors larger.")
    print("└" + "─" * 73)
    print()


def section_nontrivial_zeros():
    print("┌─ Non-Trivial Zeros ─────────────────────────────────────────────────┐")
    print("│  All known non-trivial zeros lie on the critical line Re(s) = 1/2")
    print("│  They come in conjugate pairs: ρ and 1-ρ = 1/2 ± i·t")
    print("│")

    # First several imaginary parts of non-trivial zeros (well-known values)
    zero_imaginary_parts = [
        14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
        37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
        52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
        67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
    ]

    print(f"│  {'k':>5}  {'Zero: 1/2 + i·t':>25s}  {'Spacing':>10s}")
    print(f"│  {'─'*5}  {'─'*25}  {'─'*10}")

    prev_t = None
    for k, t in enumerate(zero_imaginary_parts, 1):
        spacing = t - prev_t if prev_t else 0
        print(f"│  {k:5d}  {f'1/2 + {t:.6f}i':>25s}  {spacing:>10.6f}")
        prev_t = t

    print("│")
    print("│  As of 2023, the first 10^13 zeros have been verified on the critical line.")
    print("│  By the functional equation, zeros also appear at 1/2 - i·t.")
    print("│")
    print("│  Average spacing near height T ≈ 2π/ln(T/(2π))")
    T = 100
    avg_spacing = 2*math.pi / math.log(T/(2*math.pi))
    print(f"│  Near T={T}: average spacing ≈ {avg_spacing:.3f}  (observed above: ~8)")
    print("└" + "─" * 73)
    print()


def section_what_it_means():
    print("┌─ Why the Riemann Hypothesis Matters ───────────────────────────────┐")
    print("│")
    print("│  The primes seem random, yet follow patterns.")
    print("│  The zeta function encodes both — it is simultaneously")
    print("│  an analytic function and an arithmetic object.")
    print("│")
    print("│  The Riemann Hypothesis is equivalent to:")
    print("│   1. π(x) = Li(x) + O(√x log x)  (optimal prime distribution)")
    print("│   2. The zeros of ζ lie on Re(s)=1/2 (Riemann's claim)")
    print("│   3. Certain bounds on the M(x) = Σ μ(n) (Mertens function)")
    print("│   4. Hundreds of other consequences in number theory")
    print("│")
    print("│  Known results:")
    print("│   - ζ(s) has infinitely many zeros on the critical line (Hardy 1914)")
    print("│   - At least 40% of zeros are on the critical line (Selberg 1942)")
    print("│   - At least 2/5 of zeros are on the critical line")
    print("│   - The first 10^13 zeros are all on the critical line (2023)")
    print("│")
    print("│  Progress is agonizingly slow. Wiles proved Fermat's Last Theorem.")
    print("│  The ABC conjecture might be (controversially) proved by Mochizuki.")
    print("│  The Riemann Hypothesis: nobody knows where to even begin.")
    print("│")
    print("│  Andrew Granville: 'This problem is so hard that even understanding")
    print("│  what it would mean to have an approach seems very far away.'")
    print("└" + "─" * 73)
    print()


def section_zeta_values_visualization():
    """Show ζ(s) for real s from 1.1 to 5, visualized."""
    print("┌─ ζ(s) for real s > 1 ──────────────────────────────────────────────┐")
    print("│")
    print(f"│  {'s':>5}  {'ζ(s)':>12}  Bar")
    print(f"│  {'─'*5}  {'─'*12}  {'─'*30}")

    for s_10 in range(11, 51):
        s = s_10 / 10
        val = zeta_partial_sum(s, 100000)
        bar_len = min(30, int((val - 1) * 10))
        bar = '█' * bar_len
        print(f"│  {s:>5.1f}  {val:>12.6f}  {bar}")

    print("│")
    print("│  As s → 1⁺, ζ(s) → ∞ (the harmonic series diverges)")
    print("│  As s → ∞, ζ(s) → 1 (only the n=1 term matters)")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         R I E M A N N   Z E T A   F U N C T I O N                  ║")
    print("║  ζ(s) = Σ n^{-s} = Π_p 1/(1-p^{-s})   Riemann 1859               ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("  'A single eight-page paper that changed mathematics forever.'")
    print()

    section_euler_product()
    section_special_values()
    section_zeta_values_visualization()
    section_prime_connection()
    section_nontrivial_zeros()
    section_what_it_means()

    print("  The Riemann Hypothesis has been open for 165 years.")
    print("  It is widely considered the most important unsolved problem in mathematics.")
    print("  A proof would have implications throughout number theory, cryptography,")
    print("  and our understanding of what it means for something to be random.")
    print()


if __name__ == '__main__':
    main()
