"""
Mandelbrot Set — ASCII renderer
=================================
The set of complex numbers c for which  z_{n+1} = z_n² + c
starting from z_0 = 0 does not diverge to infinity.

The boundary is fractal: infinitely complex at every scale.
The main cardioid and period-2 bulb are visible even at low resolution.
Zooming in reveals baby Mandelbrots, spirals, seahorse valleys, etc.
"""

import math


def mandelbrot(c, max_iter=256):
    """
    Return the escape iteration count for complex c.
    Points inside the set return max_iter.
    Uses smooth coloring via the log of |z|.
    """
    # Quick check for main cardioid
    x, y = c.real, c.imag
    q = (x - 0.25)**2 + y**2
    if q * (q + (x - 0.25)) <= 0.25 * y**2:
        return max_iter
    # Quick check for period-2 bulb
    if (x + 1)**2 + y**2 <= 0.0625:
        return max_iter

    z = 0 + 0j
    for i in range(max_iter):
        z = z * z + c
        if z.real * z.real + z.imag * z.imag > 4.0:
            # Smooth coloring
            log_zn = math.log(z.real**2 + z.imag**2) / 2
            nu = math.log(log_zn / math.log(2)) / math.log(2)
            return i + 1 - nu
    return max_iter


PALETTE_DARK = ' .,:-=+*#%@'
PALETTE_RICH = ' ·.:;=+ox#%@█'


def render(cx=-0.5, cy=0.0, zoom=1.0, width=78, height=36,
           max_iter=128, palette=PALETTE_RICH):
    """
    Render the Mandelbrot set to ASCII.
    cx, cy: center of view in complex plane
    zoom: higher = more zoomed in
    """
    # Aspect ratio correction (terminal chars are ~2x taller than wide)
    aspect = 2.0
    w = 3.5 / zoom
    h = w / aspect * (height / width)

    lines = []
    for row in range(height):
        line = []
        for col in range(width):
            re = cx + (col / width - 0.5) * w
            im = cy + (0.5 - row / height) * h
            c = complex(re, im)
            v = mandelbrot(c, max_iter)
            if v >= max_iter:
                line.append(' ')  # interior
            else:
                idx = int(v * (len(palette) - 2) / max_iter) % (len(palette) - 1)
                idx = max(0, min(idx, len(palette) - 2))
                line.append(palette[idx + 1])
        lines.append(''.join(line))
    return lines


VIEWS = {
    'full':      dict(cx=-0.5,      cy=0.0,      zoom=1.0,   max_iter=64,  name='Full view'),
    'seahorse':  dict(cx=-0.7436,   cy=0.1319,   zoom=80.0,  max_iter=256, name='Seahorse valley'),
    'elephant':  dict(cx=0.3,       cy=0.0,      zoom=6.0,   max_iter=128, name='Elephant valley'),
    'period3':   dict(cx=-0.1,      cy=0.651,    zoom=15.0,  max_iter=256, name='Period-3 bulb'),
    'filament':  dict(cx=-1.749,    cy=0.0,      zoom=50.0,  max_iter=512, name='Tip filament'),
    'minibrot':  dict(cx=-1.7686,   cy=0.0042,   zoom=200.0, max_iter=512, name='Mini Mandelbrot'),
}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ASCII Mandelbrot renderer')
    parser.add_argument('view', nargs='?', default='full', choices=list(VIEWS.keys()),
                        help='Named view (default: full)')
    parser.add_argument('--cx', type=float, help='Center real part')
    parser.add_argument('--cy', type=float, help='Center imaginary part')
    parser.add_argument('--zoom', type=float, help='Zoom level')
    parser.add_argument('--iter', type=int, help='Max iterations')
    parser.add_argument('--width', type=int, default=78)
    parser.add_argument('--height', type=int, default=36)
    parser.add_argument('--list', action='store_true', help='List views')
    args = parser.parse_args()

    if args.list:
        print('\nAvailable views:')
        for k, v in VIEWS.items():
            print(f'  {k:12s}  center=({v["cx"]:.4f},{v["cy"]:.4f})  zoom={v["zoom"]}x  —  {v["name"]}')
        print()
    else:
        v = VIEWS[args.view].copy()
        if args.cx is not None: v['cx'] = args.cx
        if args.cy is not None: v['cy'] = args.cy
        if args.zoom is not None: v['zoom'] = args.zoom
        if args.iter is not None: v['max_iter'] = args.iter

        lines = render(v['cx'], v['cy'], v['zoom'], args.width, args.height, v['max_iter'])
        print(f"\n  Mandelbrot Set — {v['name']}")
        print(f"  center=({v['cx']},{v['cy']})  zoom={v['zoom']}x  iter={v['max_iter']}\n")
        for line in lines:
            print('  ' + line)
        print()
