"""
Mathematical Constants and Their Computation

π, e, φ, and friends. Each can be computed in multiple ways,
each with different convergence speeds. This program shows
them converging term by term, revealing the "shape" of each series.

Constants:
  π ≈ 3.14159265358979...  (pi, circle circumference/diameter)
  e ≈ 2.71828182845904...  (Euler's number, base of natural log)
  φ ≈ 1.61803398874989...  (golden ratio, (1+√5)/2)
  γ ≈ 0.57721566490153...  (Euler-Mascheroni constant, harder to compute)
  √2 ≈ 1.41421356237309... (square root of 2, first known irrational)

Each series below converges to its constant. Some quickly, some slowly.
The "error" at each step reveals the convergence rate.
"""

import math
from fractions import Fraction
from decimal import Decimal, getcontext

getcontext().prec = 50  # 50 decimal places of precision


# ── True values (from math module, enough for display) ──────────────────────
PI_TRUE   = math.pi
E_TRUE    = math.e
PHI_TRUE  = (1 + math.sqrt(5)) / 2
SQRT2_TRUE = math.sqrt(2)
GAMMA_TRUE = 0.5772156649015328606065120900824024310421593359399  # approx


def error_bar(actual, target, bar_width=30):
    """Visualize the absolute error as a shrinking bar."""
    err = abs(actual - target)
    if err == 0:
        return "▓" * bar_width + "  exact"
    log_err = -math.log10(err) if err > 0 else 50
    # Scale: 0 correct digits = full bar, 15+ digits = empty bar
    filled = min(bar_width, int(log_err * bar_width / 16))
    correct_digits = max(0, int(log_err))
    bar = "▓" * filled + "░" * (bar_width - filled)
    return f"{bar}  ~{correct_digits} digits"


def show_series(name, formula, true_value, terms, get_term_description=None):
    """Show a series converging to its limit."""
    print(f"  {name} = {true_value:.15f}...")
    print(f"  Formula: {formula}")
    print(f"  {'Step':>5}  {'Approximation':>20}  {'Error':>12}  Convergence")
    print(f"  {'─'*5}  {'─'*20}  {'─'*12}  {'─'*36}")
    for i, (approx, label) in enumerate(terms):
        err = abs(approx - true_value)
        bar = error_bar(approx, true_value)
        desc = f"  {label}" if label else ""
        print(f"  {i+1:>5}  {approx:>20.15f}  {err:>12.2e}  {bar}{desc}")
    print()


# ── π computations ────────────────────────────────────────────────────────────

def leibniz_pi(n_terms):
    """π/4 = 1 - 1/3 + 1/5 - 1/7 + ... (Leibniz 1673)"""
    terms = []
    total = 0.0
    for k in range(n_terms):
        total += (-1)**k / (2*k + 1)
        if k in [0, 1, 2, 4, 9, 19, 49, 99, 499, 999, 4999, 9999]:
            terms.append((total * 4, f"k={k}"))
    return terms


def nilakantha_pi(n_terms):
    """π = 3 + 4/(2·3·4) - 4/(4·5·6) + 4/(6·7·8) - ...  (Nilakantha ~1500)"""
    terms = []
    total = 3.0
    for k in range(1, n_terms + 1):
        n = 2 * k
        total += ((-1)**(k+1)) * 4 / (n * (n+1) * (n+2))
        if k in [1, 2, 3, 5, 10, 20, 50]:
            terms.append((total, f"k={k}"))
    return terms


def monte_carlo_pi(n_samples, seed=42):
    """π ≈ 4 × (points in unit circle) / (total points)"""
    import random
    random.seed(seed)
    inside = 0
    terms = []
    for i in range(1, n_samples + 1):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            inside += 1
        if i in [10, 50, 100, 500, 1000, 5000, 10000, 50000]:
            terms.append((4 * inside / i, f"n={i}"))
    return terms


def machin_pi():
    """
    Machin's formula (1706): π/4 = 4·arctan(1/5) - arctan(1/239)
    Much faster convergence than Leibniz.
    """
    def arctan_series(x, n_terms):
        total = 0.0
        for k in range(n_terms):
            total += ((-1)**k) * x**(2*k+1) / (2*k+1)
        return total

    terms = []
    for n in range(1, 16):
        a = arctan_series(1/5, n)
        b = arctan_series(1/239, n)
        approx = 4 * (4*a - b)
        terms.append((approx, f"n={n}"))
    return terms


# ── e computations ─────────────────────────────────────────────────────────────

def euler_e(n_terms):
    """e = 1/0! + 1/1! + 1/2! + 1/3! + ... (Taylor series for e^x at x=1)"""
    terms = []
    total = 0.0
    factorial = 1
    for k in range(n_terms):
        if k > 0:
            factorial *= k
        total += 1.0 / factorial
        terms.append((total, f"k={k}"))
    return terms


def euler_e_limit(n_terms):
    """e = lim_{n→∞} (1 + 1/n)^n  (classic limit definition)"""
    terms = []
    for n in [1, 2, 5, 10, 50, 100, 1000, 10000, 100000, 1000000]:
        approx = (1 + 1/n)**n
        terms.append((approx, f"n={n}"))
    return terms


# ── φ computations ─────────────────────────────────────────────────────────────

def fibonacci_phi(n_terms):
    """φ = lim F(n+1)/F(n) as n→∞  (ratio of consecutive Fibonacci numbers)"""
    a, b = 1, 1
    terms = []
    for k in range(n_terms):
        a, b = b, a + b
        terms.append((b/a, f"F({k+2})/F({k+1})"))
    return terms


def continued_fraction_phi(n_terms):
    """φ = 1 + 1/(1 + 1/(1 + 1/...))  (all 1s continued fraction)"""
    terms = []
    x = 1.0
    for k in range(n_terms):
        x = 1 + 1/x
        terms.append((x, f"depth={k+1}"))
    return terms


# ── √2 computations ──────────────────────────────────────────────────────────

def babylonian_sqrt2(n_terms):
    """
    Babylonian method / Newton's method for √2.
    x_{n+1} = (x_n + 2/x_n) / 2
    Known to ancient Babylonians (≈1800 BCE).
    Quadratic convergence — doubles the correct digits each step!
    """
    x = 1.0
    terms = [(x, "x_0=1")]
    for k in range(1, n_terms):
        x = (x + 2/x) / 2
        terms.append((x, f"step {k}"))
    return terms


# ── Euler-Mascheroni γ ────────────────────────────────────────────────────────

def euler_mascheroni(n_terms):
    """
    γ = lim_{n→∞} (H_n - ln(n))  where H_n = 1 + 1/2 + 1/3 + ... + 1/n
    No formula is known for γ like Leibniz's for π.
    Even its irrationality is unproven.
    """
    terms = []
    H = 0.0
    for n in range(1, n_terms + 1):
        H += 1.0 / n
        approx = H - math.log(n)
        if n in [1, 2, 5, 10, 50, 100, 1000, 10000, 100000]:
            terms.append((approx, f"n={n}"))
    return terms


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         M A T H E M A T I C A L   C O N S T A N T S               ║")
    print("║  Computing π, e, φ, √2, γ — watching them converge                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("━" * 72)
    print("  π (pi) — ratio of circle's circumference to diameter")
    print("━" * 72)
    print()

    show_series(
        "Leibniz series for π (1673)",
        "π/4 = 1 - 1/3 + 1/5 - 1/7 + ...   [alternating, very slow]",
        PI_TRUE,
        leibniz_pi(10000)
    )

    show_series(
        "Nilakantha series for π (~1500)",
        "π = 3 + 4/(2·3·4) - 4/(4·5·6) + ...   [faster: cubic convergence]",
        PI_TRUE,
        nilakantha_pi(50)
    )

    show_series(
        "Machin's formula (1706)",
        "π/4 = 4·arctan(1/5) - arctan(1/239)   [each term ≈ 5× more digits]",
        PI_TRUE,
        machin_pi()
    )

    show_series(
        "Monte Carlo π (statistical)",
        "π ≈ 4 × (random points in unit circle) / (total)   [√n convergence]",
        PI_TRUE,
        monte_carlo_pi(50000)
    )

    print("━" * 72)
    print("  e — Euler's number, base of natural logarithm")
    print("━" * 72)
    print()

    show_series(
        "Taylor series: e = Σ 1/k!",
        "e = 1/0! + 1/1! + 1/2! + ...   [super-exponential convergence]",
        E_TRUE,
        euler_e(15)
    )

    show_series(
        "Limit definition: e = lim (1+1/n)^n",
        "e = lim_{n→∞} (1 + 1/n)^n   [log(n) convergence — very slow]",
        E_TRUE,
        euler_e_limit(0)
    )

    print("━" * 72)
    print("  φ (phi) — the golden ratio")
    print("━" * 72)
    print()

    show_series(
        "Fibonacci ratios converging to φ",
        "φ = lim F(n+1)/F(n)   [linear convergence with ratio 1/φ²]",
        PHI_TRUE,
        fibonacci_phi(20)
    )

    show_series(
        "Continued fraction: φ = [1; 1, 1, 1, ...]",
        "φ = 1 + 1/(1 + 1/(1 + ...))   [same as Fibonacci ratios!]",
        PHI_TRUE,
        continued_fraction_phi(20)
    )

    print("━" * 72)
    print("  √2 — the first number proved irrational (ancient Greeks)")
    print("━" * 72)
    print()

    show_series(
        "Babylonian method / Newton's method",
        "x_{n+1} = (x + 2/x)/2   [quadratic convergence — doubles digits!]",
        SQRT2_TRUE,
        babylonian_sqrt2(10)
    )

    print("━" * 72)
    print("  γ (gamma) — Euler-Mascheroni constant")
    print("━" * 72)
    print()

    show_series(
        "γ = lim (H_n - ln n)  where H_n = harmonic sum",
        "γ ≈ 0.5772...  Irrationality unknown. No closed form known.",
        GAMMA_TRUE,
        euler_mascheroni(100000)
    )

    print("━" * 72)
    print("  Convergence comparison")
    print("━" * 72)
    print()
    print("  Method                    Rate       Terms for 10 digits")
    print("  ─────────────────────────────────────────────────────────")
    print("  Leibniz (π)               linear     ~10^10 terms")
    print("  Nilakantha (π)            cubic      ~1000 terms")
    print("  Machin (π)                5×/term    ~14 terms")
    print("  BBP formula (π)           linear     1 term per hex digit!")
    print("  Taylor series (e)         factorial  ~13 terms")
    print("  Limit def (e)             log(n)     ~10^10 steps")
    print("  Fibonacci ratios (φ)      linear     ~50 terms")
    print("  Babylonian (√2)           quadratic  ~6 steps")
    print()
    print("  The Babylonian method is remarkable: it takes just 6 iterations")
    print("  starting from x=1 to compute √2 to 15+ decimal places.")
    print("  Each step approximately doubles the correct digits.")
    print()
    print("  γ's slow convergence reflects our limited understanding of it.")
    print("  We can compute it to millions of digits but don't know if it's rational.")
    print()


if __name__ == '__main__':
    main()
