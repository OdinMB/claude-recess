"""
Fourier Series

Jean-Baptiste Joseph Fourier (1768–1830) claimed that any periodic
function could be written as a sum of sines and cosines. His contemporaries
(including Lagrange) thought this absurd. He was right.

    f(x) = a_0/2 + Σ [a_n cos(nx) + b_n sin(nx)]

This program shows several classic waveforms being built up,
harmonic by harmonic, watching them converge to the target shape.

At the edges of discontinuities, you see Gibbs phenomenon:
the approximation overshoots by ~9%, no matter how many harmonics.
This was a mystery for decades.
"""

import math


def fourier_square(x, n_harmonics):
    """Square wave: f(x) = 4/π Σ sin((2k-1)x)/(2k-1) for k=1,2,..."""
    result = 0.0
    for k in range(1, n_harmonics + 1):
        result += math.sin((2*k - 1) * x) / (2*k - 1)
    return result * 4 / math.pi


def fourier_sawtooth(x, n_harmonics):
    """Sawtooth wave: f(x) = 2/π Σ (-1)^(k+1) sin(kx)/k"""
    result = 0.0
    for k in range(1, n_harmonics + 1):
        result += ((-1)**(k+1)) * math.sin(k * x) / k
    return result * 2 / math.pi


def fourier_triangle(x, n_harmonics):
    """Triangle wave: f(x) = 8/π² Σ (-1)^k sin((2k+1)x)/(2k+1)²"""
    result = 0.0
    for k in range(n_harmonics):
        result += ((-1)**k) * math.sin((2*k + 1) * x) / (2*k + 1)**2
    return result * 8 / (math.pi ** 2)


def fourier_half_wave(x, n_harmonics):
    """Half-wave rectified sine: cos components dominate"""
    result = 1/math.pi
    if n_harmonics >= 1:
        result += 0.5 * math.sin(x)
    for k in range(1, n_harmonics + 1):
        n = 2*k
        result += (2/math.pi) * math.cos(n*x) / (1 - n*n) if n*n != 1 else 0
    return result


# True waveforms
def true_square(x):
    x = x % (2*math.pi)
    return 1.0 if x < math.pi else -1.0

def true_sawtooth(x):
    x = x % (2*math.pi)
    return 1 - x / math.pi  # from 1 to -1

def true_triangle(x):
    x = x % (2*math.pi)
    if x < math.pi/2:
        return x * 2 / math.pi
    elif x < 3*math.pi/2:
        return 1 - (x - math.pi/2) * 2 / math.pi * 2
    else:
        return (x - 2*math.pi) * 2 / math.pi


def render_curve(func, width=70, height=20, x_min=0, x_max=2*math.pi,
                 y_min=-1.3, y_max=1.3, char='█'):
    """Render a function as ASCII art."""
    grid = [[' '] * width for _ in range(height)]

    # Draw x-axis
    y_axis = int((0 - y_min) / (y_max - y_min) * (height - 1))
    y_axis = height - 1 - y_axis
    if 0 <= y_axis < height:
        for c in range(width):
            grid[y_axis][c] = '─'

    # Draw the curve
    prev_row = None
    for col in range(width):
        x = x_min + (x_max - x_min) * col / (width - 1)
        try:
            y = func(x)
        except (ValueError, ZeroDivisionError):
            continue

        if y_min <= y <= y_max:
            row = int((y_max - y) / (y_max - y_min) * (height - 1))
            row = max(0, min(height - 1, row))
            grid[row][col] = char

            # Fill vertical gaps
            if prev_row is not None and abs(row - prev_row) > 1:
                for r in range(min(row, prev_row) + 1, max(row, prev_row)):
                    grid[r][col-1] = '│'

            prev_row = row

    return [''.join(row) for row in grid]


def render_comparison(true_func, approx_func, width=70, height=22,
                      x_min=0, x_max=2*math.pi):
    """Render true function (░) and approximation (█) overlaid."""
    y_min, y_max = -1.4, 1.4
    grid = [[' '] * width for _ in range(height)]

    # x-axis
    y_axis = height - 1 - int((0 - y_min) / (y_max - y_min) * (height - 1))
    if 0 <= y_axis < height:
        for c in range(width):
            if grid[y_axis][c] == ' ':
                grid[y_axis][c] = '─'

    # True function
    for col in range(width):
        x = x_min + (x_max - x_min) * col / (width - 1)
        try:
            y = true_func(x)
            row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
            row = max(0, min(height - 1, row))
            grid[row][col] = '░' if grid[row][col] == ' ' else '▒'
        except (ValueError, ZeroDivisionError):
            pass

    # Approximation
    for col in range(width):
        x = x_min + (x_max - x_min) * col / (width - 1)
        try:
            y = approx_func(x)
            row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
            row = max(0, min(height - 1, row))
            if grid[row][col] == '░':
                grid[row][col] = '▒'  # overlap
            elif grid[row][col] != '─':
                grid[row][col] = '█'
        except (ValueError, ZeroDivisionError):
            pass

    return [''.join(row) for row in grid]


def show_harmonic_buildup(name, true_func, fourier_func, harmonic_steps):
    """Show a waveform being built up harmonic by harmonic."""
    print(f"┌─ {name} " + "─" * max(1, 62 - len(name)) + "┐")
    print(f"│  ░ = true waveform   █ = Fourier approximation   ▒ = overlap")
    print("│")

    for n in harmonic_steps:
        approx = lambda x, n=n: fourier_func(x, n)
        # Compute max error
        xs = [2*math.pi * i / 200 for i in range(201)]
        errors = [abs(approx(x) - true_func(x)) for x in xs]
        max_err = max(errors)

        label = f"n={n} harmonic{'s' if n>1 else ''}"
        print(f"│  {label}  (max error: {max_err:.4f})")

        lines = render_comparison(true_func, approx, width=68, height=14)
        for line in lines:
            print("│ " + line)
        print("│")

    print("└" + "─" * 70)
    print()


def gibbs_phenomenon(width=70, height=22):
    """Show Gibbs phenomenon: ~9% overshoot at discontinuities."""
    print("┌─ Gibbs Phenomenon ──────────────────────────────────────────────────┐")
    print("│  At a jump discontinuity, Fourier series overshoots by ~9%")
    print("│  regardless of how many harmonics are used.")
    print("│")
    print("│  Square wave with n=1, 5, 20, 100 harmonics (zoomed near x=0):")
    print("│")

    x_min = -0.3
    x_max = 0.3

    for n in [1, 5, 20, 100]:
        approx = lambda x, n=n: fourier_square(x, n)

        # Find max value in the first positive lobe
        xs = [x_min + (x_max - x_min) * i / 500 for i in range(501)]
        vals = [approx(x) for x in xs]
        max_val = max(vals)
        overshoot = (max_val - 1.0) * 100

        grid = [[' '] * width for _ in range(height)]

        # Axis lines
        y_min_r, y_max_r = -1.5, 1.5
        y_ax = height - 1 - int((0 - y_min_r) / (y_max_r - y_min_r) * (height - 1))
        if 0 <= y_ax < height:
            for c in range(width): grid[y_ax][c] = '─'
        x_ax = int((0 - x_min) / (x_max - x_min) * (width - 1))
        if 0 <= x_ax < width:
            for r in range(height):
                if grid[r][x_ax] == ' ':
                    grid[r][x_ax] = '│'

        # True square
        for col in range(width):
            x = x_min + (x_max - x_min) * col / (width - 1)
            y = true_square(x)
            row = height - 1 - int((y - y_min_r) / (y_max_r - y_min_r) * (height - 1))
            row = max(0, min(height - 1, row))
            if grid[row][col] == ' ':
                grid[row][col] = '░'

        # Approximation
        for col in range(width):
            x = x_min + (x_max - x_min) * col / (width - 1)
            y = approx(x)
            if y_min_r <= y <= y_max_r:
                row = height - 1 - int((y - y_min_r) / (y_max_r - y_min_r) * (height - 1))
                row = max(0, min(height - 1, row))
                if grid[row][col] == '░':
                    grid[row][col] = '▒'
                elif grid[row][col] not in ('─', '│'):
                    grid[row][col] = '█'

        print(f"│  n={n:3d} harmonics  (overshoot: {overshoot:+.2f}%)")
        for row in grid:
            print("│ " + ''.join(row))
        print("│")

    print("│  The overshoot approaches ~8.9% as n→∞. It never disappears.")
    print("│  This is called Gibbs phenomenon (discovered by Michelson, named for Gibbs).")
    print("└" + "─" * 70)
    print()


def frequency_spectrum(name, harmonics_and_amplitudes, width=60, height=15):
    """Show which frequencies are present in a waveform."""
    print(f"  Frequency spectrum: {name}")
    max_amp = max(a for _, a in harmonics_and_amplitudes) if harmonics_and_amplitudes else 1

    for freq, amp in harmonics_and_amplitudes:
        bar_len = int(amp / max_amp * (width - 10))
        bar = '█' * bar_len
        print(f"  {freq:>4}ω │{bar}")

    print()


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              F O U R I E R   S E R I E S                           ║")
    print("║  Any periodic function = sum of sines and cosines                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print("  Fourier's insight: f(x) = a₀/2 + Σ[aₙcos(nx) + bₙsin(nx)]")
    print()
    print("  The coefficients are computed by:")
    print("  aₙ = (1/π) ∫ f(x) cos(nx) dx")
    print("  bₙ = (1/π) ∫ f(x) sin(nx) dx")
    print()

    show_harmonic_buildup(
        "Square wave: f(x) = ±1  (only odd harmonics)",
        true_square,
        fourier_square,
        [1, 3, 7, 20]
    )

    show_harmonic_buildup(
        "Sawtooth wave: f(x) = 1 - x/π  (all harmonics)",
        true_sawtooth,
        fourier_sawtooth,
        [1, 3, 7, 20]
    )

    show_harmonic_buildup(
        "Triangle wave: f(x) = |x|/π - 1  (only odd harmonics, faster)",
        true_triangle,
        fourier_triangle,
        [1, 2, 4, 8]
    )

    gibbs_phenomenon()

    print("┌─ Frequency spectra ─────────────────────────────────────────────────┐")
    print("│")
    print("│  Square wave: only odd harmonics (1, 3, 5, ...)")
    print("│  Amplitude = 1/(2k-1) — decays as 1/n")
    frequency_spectrum("Square", [(2*k-1, 1/(2*k-1)) for k in range(1, 10)])

    print("│  Sawtooth wave: all harmonics (1, 2, 3, ...)")
    print("│  Amplitude = 1/k — decays as 1/n")
    frequency_spectrum("Sawtooth", [(k, 1/k) for k in range(1, 10)])

    print("│  Triangle wave: only odd harmonics, but faster decay")
    print("│  Amplitude = 1/(2k-1)² — decays as 1/n²  (smoother waveform!)")
    frequency_spectrum("Triangle", [(2*k-1, 1/(2*k-1)**2) for k in range(1, 10)])

    print("│  A smooth (infinitely differentiable) function has")
    print("│  Fourier coefficients that decay faster than any power of 1/n.")
    print("│  Discontinuities ↔ slow (algebraic) coefficient decay.")
    print("│  Smoothness ↔ fast (exponential) coefficient decay.")
    print("│")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    print("  Fourier analysis connects: heat equation, signal processing,")
    print("  quantum mechanics (Heisenberg uncertainty principle),")
    print("  number theory (Riemann zeta function), and image compression (JPEG).")
    print()


if __name__ == '__main__':
    main()
