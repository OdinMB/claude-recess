"""
Gray-Scott Reaction-Diffusion System

Two chemicals U and V diffuse and react on a 2D grid:
    dU/dt = Du * ∇²U - U*V² + f*(1 - U)
    dV/dt = Dv * ∇²V + U*V² - (f + k)*V

Where:
    Du, Dv = diffusion rates (Du > Dv, so U diffuses faster)
    f = feed rate (how fast U is replenished)
    k = kill rate (how fast V decays)
    U*V² = autocatalytic reaction (V converts U into more V)

The magic is in the parameter space. Different (f, k) values produce:
    - spots       (f=0.035, k=0.065)  — like leopard spots
    - worms       (f=0.046, k=0.063)  — writhing vermiform patterns
    - coral       (f=0.062, k=0.061)  — branching coral-like structures
    - mitosis     (f=0.028, k=0.062)  — spots that divide like cells
    - spirals     (f=0.014, k=0.054)  — rotating spiral waves
    - stripes     (f=0.040, k=0.060)  — like zebra stripes
    - chaos       (f=0.026, k=0.051)  — turbulent patterns

This is Turing's morphogenesis: pattern formation from nothing but
diffusion and reaction. Two differential equations producing leopard
spots, zebra stripes, and seashell patterns.

Usage:
    python3 reaction_diffusion.py               # Spots (default)
    python3 reaction_diffusion.py worms          # Worms pattern
    python3 reaction_diffusion.py coral          # Coral branching
    python3 reaction_diffusion.py mitosis        # Cell-like division
    python3 reaction_diffusion.py stripes        # Stripe formation
    python3 reaction_diffusion.py all            # All patterns side by side
"""

import sys
import os
import math
import random


# --- Grid operations ---

def make_grid(w, h, val=1.0):
    return [[val] * w for _ in range(h)]


def laplacian(grid, x, y, w, h):
    """Discrete Laplacian (5-point stencil) with periodic boundaries."""
    center = grid[y][x]
    top    = grid[(y - 1) % h][x]
    bottom = grid[(y + 1) % h][x]
    left   = grid[y][(x - 1) % w]
    right  = grid[y][(x + 1) % w]
    return top + bottom + left + right - 4 * center


# --- Gray-Scott model ---

class GrayScott:
    def __init__(self, w, h, f=0.035, k=0.065, du=0.16, dv=0.08, dt=1.0):
        self.w = w
        self.h = h
        self.f = f
        self.k = k
        self.du = du
        self.dv = dv
        self.dt = dt

        # Initialize: U = 1 everywhere, V = 0 everywhere
        self.U = make_grid(w, h, 1.0)
        self.V = make_grid(w, h, 0.0)

    def seed_center(self, radius=5):
        """Place a seed of V in the center."""
        cx, cy = self.w // 2, self.h // 2
        for y in range(self.h):
            for x in range(self.w):
                dx = x - cx
                dy = y - cy
                if dx*dx + dy*dy < radius*radius:
                    self.U[y][x] = 0.5 + random.uniform(-0.01, 0.01)
                    self.V[y][x] = 0.25 + random.uniform(-0.01, 0.01)

    def seed_random(self, n_seeds=10, radius=3):
        """Place random seeds of V."""
        for _ in range(n_seeds):
            cx = random.randint(radius, self.w - radius - 1)
            cy = random.randint(radius, self.h - radius - 1)
            for y in range(max(0, cy - radius), min(self.h, cy + radius + 1)):
                for x in range(max(0, cx - radius), min(self.w, cx + radius + 1)):
                    if (x - cx)**2 + (y - cy)**2 < radius * radius:
                        self.U[y][x] = 0.5 + random.uniform(-0.01, 0.01)
                        self.V[y][x] = 0.25 + random.uniform(-0.01, 0.01)

    def step(self):
        """Advance one time step."""
        w, h = self.w, self.h
        U, V = self.U, self.V
        f, k = self.f, self.k
        du, dv = self.du, self.dv
        dt = self.dt

        newU = make_grid(w, h, 0.0)
        newV = make_grid(w, h, 0.0)

        for y in range(h):
            for x in range(w):
                u = U[y][x]
                v = V[y][x]
                uvv = u * v * v
                lap_u = laplacian(U, x, y, w, h)
                lap_v = laplacian(V, x, y, w, h)

                newU[y][x] = u + dt * (du * lap_u - uvv + f * (1.0 - u))
                newV[y][x] = v + dt * (dv * lap_v + uvv - (f + k) * v)

                # Clamp
                newU[y][x] = max(0.0, min(1.0, newU[y][x]))
                newV[y][x] = max(0.0, min(1.0, newV[y][x]))

        self.U = newU
        self.V = newV

    def run(self, n_steps, report_every=0):
        """Run n steps."""
        for i in range(n_steps):
            self.step()
            if report_every > 0 and (i + 1) % report_every == 0:
                print(f"    step {i + 1}/{n_steps}", flush=True)


# --- Rendering ---

DOT_BITS = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}


def render_braille(grid, w, h, threshold=0.15):
    """Render V grid using braille characters. V > threshold = dot."""
    char_w = (w + 1) // 2
    char_h = (h + 3) // 4
    buf = [[0] * char_w for _ in range(char_h)]

    for y in range(h):
        for x in range(w):
            if grid[y][x] > threshold:
                cx = x // 2
                cy = y // 4
                dx = x % 2
                dy = y % 4
                if cy < char_h and cx < char_w:
                    buf[cy][cx] |= DOT_BITS[(dx, dy)]

    lines = []
    for row in buf:
        lines.append(''.join(chr(0x2800 + bits) for bits in row))
    return '\n'.join(lines)


def render_ascii(grid, w, h):
    """Render V grid using ASCII density characters."""
    palette = ' .·:;+*#%@'
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            v = grid[y][x]
            idx = int(v * (len(palette) - 1))
            idx = max(0, min(len(palette) - 1, idx))
            row.append(palette[idx])
        lines.append(''.join(row))
    return '\n'.join(lines)


# --- Named patterns ---

PATTERNS = {
    'spots': {
        'f': 0.035, 'k': 0.065,
        'desc': 'Leopard spots',
        'steps': 3000,
        'seed': 'random',
    },
    'worms': {
        'f': 0.046, 'k': 0.063,
        'desc': 'Writhing worms',
        'steps': 3000,
        'seed': 'random',
    },
    'coral': {
        'f': 0.062, 'k': 0.061,
        'desc': 'Branching coral',
        'steps': 4000,
        'seed': 'center',
    },
    'mitosis': {
        'f': 0.028, 'k': 0.062,
        'desc': 'Cell division',
        'steps': 4000,
        'seed': 'center',
    },
    'stripes': {
        'f': 0.040, 'k': 0.060,
        'desc': 'Zebra stripes',
        'steps': 4000,
        'seed': 'random',
    },
    'spirals': {
        'f': 0.014, 'k': 0.054,
        'desc': 'Rotating spirals',
        'steps': 5000,
        'seed': 'random',
    },
    'chaos': {
        'f': 0.026, 'k': 0.051,
        'desc': 'Turbulent chaos',
        'steps': 3000,
        'seed': 'random',
    },
}


# --- Terminal ---

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except (AttributeError, ValueError, OSError):
        return 80, 24


# --- Main ---

def main():
    cols, rows = get_terminal_size()
    mode = 'braille'

    if 'ascii' in sys.argv:
        mode = 'ascii'

    if mode == 'ascii':
        sim_w = cols - 2
        sim_h = rows - 5
    else:
        sim_w = (cols - 2) * 2
        sim_h = (rows - 5) * 4

    # Keep simulation size reasonable for pure Python
    sim_w = min(sim_w, 120)
    sim_h = min(sim_h, 80)

    pattern_name = 'spots'
    for arg in sys.argv[1:]:
        if arg in PATTERNS:
            pattern_name = arg
        elif arg == 'all':
            # Show all patterns as small thumbnails
            cmd_all()
            return
        elif arg == 'list':
            print("Available patterns:")
            for name, p in sorted(PATTERNS.items()):
                print(f"  {name:12s}  f={p['f']:.3f}  k={p['k']:.3f}  — {p['desc']}")
            return

    p = PATTERNS[pattern_name]
    f, k = p['f'], p['k']
    n_steps = p['steps']

    print(f"  Gray-Scott reaction-diffusion  |  {pattern_name}: {p['desc']}")
    print(f"  f={f}  k={k}  |  {sim_w}×{sim_h}  |  {n_steps} steps", flush=True)

    random.seed(42)  # Reproducible
    gs = GrayScott(sim_w, sim_h, f=f, k=k)

    if p['seed'] == 'center':
        gs.seed_center(radius=max(3, min(sim_w, sim_h) // 10))
    else:
        gs.seed_random(n_seeds=15, radius=max(2, min(sim_w, sim_h) // 15))

    gs.run(n_steps, report_every=500)

    # Compute statistics
    v_sum = sum(sum(row) for row in gs.V)
    v_max = max(max(row) for row in gs.V)
    v_avg = v_sum / (sim_w * sim_h)

    print(f"  V avg={v_avg:.4f}  max={v_max:.4f}")

    if mode == 'ascii':
        print(render_ascii(gs.V, sim_w, sim_h))
    else:
        print(render_braille(gs.V, sim_w, sim_h))


def cmd_all():
    """Show all patterns as small thumbnails."""
    # Small simulation for each pattern
    size = 40
    for name in ['spots', 'worms', 'coral', 'mitosis', 'stripes', 'chaos']:
        p = PATTERNS[name]
        random.seed(42)
        gs = GrayScott(size, size, f=p['f'], k=p['k'])
        if p['seed'] == 'center':
            gs.seed_center(radius=5)
        else:
            gs.seed_random(n_seeds=5, radius=3)

        # Fewer steps for overview
        gs.run(min(p['steps'], 2000))

        v_avg = sum(sum(row) for row in gs.V) / (size * size)
        print(f"\n  {name} ({p['desc']})  |  f={p['f']}  k={p['k']}  |  V_avg={v_avg:.4f}")
        print(render_braille(gs.V, size, size, threshold=0.12))


if __name__ == "__main__":
    main()
