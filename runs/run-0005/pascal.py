"""
Pascal's Triangle

One of the most fertile objects in mathematics.
C(n,k) = n! / (k! × (n-k)!)  — also written ⁿCₖ or (n choose k)

Things hiding inside:
  - Binomial coefficients
  - Row sums: powers of 2
  - Row as digits: powers of 11 (for small rows)
  - Fibonacci numbers (diagonal sums)
  - Sierpinski triangle (mod 2)
  - Catalan numbers (from center column)
  - Hockey stick identity
  - Pascal's rule: C(n,k) = C(n-1,k-1) + C(n-1,k)
  - And many more...
"""

import math


def pascal_row(n):
    """Return the n-th row of Pascal's triangle (0-indexed)."""
    row = [1]
    for k in range(1, n + 1):
        row.append(row[-1] * (n - k + 1) // k)
    return row


def pascal_triangle(rows):
    """Return all rows 0..rows-1."""
    return [pascal_row(n) for n in range(rows)]


def render_triangle(rows, width=72, transform=None, char_map=None):
    """
    Render Pascal's triangle, optionally transforming values.
    transform: function applied to each value before display
    char_map: function mapping transformed value to display char
    """
    triangle = pascal_triangle(rows)

    if char_map is None:
        # Default: show numbers, centered
        max_val = max(max(row) for row in triangle)
        cell_width = max(1, len(str(max_val)) + 1)

        lines = []
        for r, row in enumerate(triangle):
            nums = ' '.join(f"{v:{cell_width}d}" for v in row)
            padding = (width - len(nums)) // 2
            lines.append(' ' * max(0, padding) + nums)
        return lines
    else:
        # char_map mode: each cell is one character
        lines = []
        for r, row in enumerate(triangle):
            if transform:
                row = [transform(v) for v in row]
            chars = ''.join(char_map(v) for v in row)
            # Center
            padding = (width - len(chars) * 2 + 1) // 2
            lines.append(' ' * max(0, padding) + ' '.join(chars))
        return lines


def show_basic(rows=12):
    print("┌─ Pascal's Triangle ─────────────────────────────────────────────────┐")
    print(f"│  C(n,k) = C(n-1,k-1) + C(n-1,k)  (Pascal's rule)")
    print("│")
    lines = render_triangle(rows)
    for line in lines:
        print("│" + line)
    print("│")
    print("└" + "─" * 73)
    print()


def show_patterns(rows=16):
    print("┌─ Hidden Patterns ───────────────────────────────────────────────────┐")
    print("│")

    triangle = pascal_triangle(rows)

    # Row sums (powers of 2)
    print("│  Row sums = powers of 2:")
    for r in range(8):
        s = sum(triangle[r])
        print(f"│    Row {r}: {' '.join(str(v) for v in triangle[r])} = {s} = 2^{r}")
    print("│")

    # Powers of 11
    print("│  Rows as digits = powers of 11:")
    for r in range(6):
        row = triangle[r]
        if max(row) < 10:
            num = int(''.join(str(v) for v in row))
            print(f"│    Row {r}: {''.join(str(v) for v in row)} = 11^{r} = {11**r}")
    print("│  (breaks at row 5 when digits exceed 1)")
    print("│")

    # Fibonacci in diagonals
    print("│  Fibonacci numbers in diagonal sums:")
    max_diag = rows
    fibs = [0]
    for diag in range(max_diag):
        total = 0
        for k in range(diag + 1):
            r = diag - k
            c = k
            if r < rows and c <= r:
                total += triangle[r][c]
        fibs.append(total)
    print(f"│    Sums: {' '.join(str(f) for f in fibs[1:15])}")
    print(f"│    These are: 1, 1, 2, 3, 5, 8, 13, 21, 34, ...")
    print("│")

    # Catalan numbers
    print("│  Catalan numbers (center / center+1 of even rows):")
    catalan = []
    for n in range(8):
        row = triangle[2*n]
        if len(row) >= n + 1:
            cat = row[n] - (row[n+1] if n+1 < len(row) else 0)
            # Better: C(n) = C(2n,n)/(n+1)
            cat = math.comb(2*n, n) // (n+1)
            catalan.append(cat)
    print(f"│    C_n = {', '.join(str(c) for c in catalan)}")
    print(f"│    C_n counts: binary trees, valid parenthesizations, monotonic paths...")
    print("│")

    print("└" + "─" * 73)
    print()


def show_sierpinski(rows=32):
    print("┌─ Sierpinski Triangle (Pascal mod 2) ───────────────────────────────┐")
    print("│  Shade = even, space = odd")
    print("│  Odd entries form the Sierpinski triangle fractal")
    print("│")
    lines = render_triangle(
        rows,
        transform=lambda v: v % 2,
        char_map=lambda v: '█' if v == 0 else '·'
    )
    for line in lines:
        print("│" + line)
    print("│")
    print("│  Lucas' theorem: C(n,k) is odd iff k AND n = k (bitwise)")
    print("└" + "─" * 73)
    print()


def show_mod3(rows=27):
    print("┌─ Pascal's Triangle mod 3 ───────────────────────────────────────────┐")
    print("│  0=space, 1=·, 2=█")
    print("│")
    shade = {0: ' ', 1: '·', 2: '█'}
    lines = render_triangle(
        rows,
        transform=lambda v: v % 3,
        char_map=lambda v: shade[v]
    )
    for line in lines:
        print("│" + line)
    print("│")
    print("└" + "─" * 73)
    print()


def show_identities():
    print("┌─ Combinatorial Identities ──────────────────────────────────────────┐")
    print("│")

    print("│  Hockey stick identity: Σ C(i,r) for i=r..n = C(n+1, r+1)")
    print("│")
    for r in range(1, 5):
        for n in range(r, r + 6):
            left = sum(math.comb(i, r) for i in range(r, n + 1))
            right = math.comb(n + 1, r + 1)
            row_sums = '+'.join(f"C({i},{r})" for i in range(r, min(r+4, n+1)))
            if n == r + 2:
                print(f"│    r={r}: {row_sums}+... = C({n+1},{r+1}) = {right}")
    print("│")

    print("│  Vandermonde's identity: Σ C(m,k)·C(n,r-k) = C(m+n, r)")
    for m, n, r in [(3,4,4), (5,3,6), (4,4,5)]:
        left = sum(math.comb(m,k) * math.comb(n, r-k) for k in range(r+1) if k<=m and r-k<=n)
        right = math.comb(m+n, r)
        print(f"│    m={m},n={n},r={r}: Σ C({m},k)·C({n},{r}-k) = C({m+n},{r}) = {right}  {'✓' if left==right else '✗'}")
    print("│")

    print("│  Sum of squares: Σ C(n,k)² = C(2n, n)")
    for n in range(7):
        left = sum(math.comb(n,k)**2 for k in range(n+1))
        right = math.comb(2*n, n)
        print(f"│    n={n}: {left} = C({2*n},{n}) = {right}  {'✓' if left==right else '✗'}")
    print("│")

    print("│  Binomial theorem: (1+x)^n = Σ C(n,k) x^k")
    print("│  Setting x=1: 2^n = Σ C(n,k)  (all row sums)")
    print("│  Setting x=-1: 0 = Σ (-1)^k C(n,k)  (alternating row sums cancel!)")
    print("│")
    for n in [3, 5, 7, 10]:
        alt = sum((-1)**k * math.comb(n,k) for k in range(n+1))
        print(f"│    n={n:2d}: Σ(-1)^k·C({n},k) = {alt}")
    print("└" + "─" * 73)
    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              P A S C A L ' S   T R I A N G L E                     ║")
    print("║  C(n,k) — one of the most fertile objects in mathematics           ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    show_basic(rows=12)
    show_patterns(rows=16)
    show_sierpinski(rows=32)
    show_mod3(rows=27)
    show_identities()

    print("  Blaise Pascal (1623–1662) popularized this triangle in 'Traité du")
    print("  triangle arithmétique' (1653), though it was known to al-Karaji (~1000),")
    print("  Omar Khayyám (~1100), and Yang Hui (~1261) before him.")
    print()


if __name__ == '__main__':
    main()
