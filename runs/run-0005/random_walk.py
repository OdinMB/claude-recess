"""
Random Walks

A particle starts at the origin. Each step, it moves one unit in a random
direction. Where does it end up after N steps?

Expected distance from origin: √N  (not N — counterintuitive)
Probability of returning to origin in 2D: 1  (it always comes back)
Probability of returning to origin in 3D: ≈ 0.34  (often lost forever)

Pólya's theorem (1921):
  - 1D random walk: returns to origin with probability 1
  - 2D random walk: returns to origin with probability 1
  - 3D random walk: returns to origin with probability ≈ 0.3405

George Pólya proved this in a Zurich tram, supposedly.
"""

import random
import math


random.seed(42)  # Reproducible, but still "random"


def random_walk_2d(steps, step_size=1):
    x, y = 0.0, 0.0
    path = [(x, y)]
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    for _ in range(steps):
        dx, dy = random.choice(directions)
        x += dx * step_size
        y += dy * step_size
        path.append((x, y))
    return path


def render_walk(path, width=70, height=36, show_start_end=True):
    if not path:
        return []

    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1

    margin = 1

    def to_col(x):
        return int((x - min_x) / span_x * (width - 2*margin - 1)) + margin

    def to_row(y):
        return int((max_y - y) / span_y * (height - 2*margin - 1)) + margin

    grid = [[' '] * width for _ in range(height)]

    # Draw the path
    for i in range(len(path) - 1):
        c0, r0 = to_col(path[i][0]), to_row(path[i][1])
        c1, r1 = to_col(path[i+1][0]), to_row(path[i+1][1])

        # Bresenham line, mark with trail intensity
        dc, dr = c1 - c0, r1 - r0
        steps = max(abs(dc), abs(dr), 1)
        for s in range(steps + 1):
            c = c0 + int(dc * s / steps)
            r = r0 + int(dr * s / steps)
            if 0 <= r < height and 0 <= c < width:
                if grid[r][c] == ' ':
                    grid[r][c] = '·'
                elif grid[r][c] == '·':
                    grid[r][c] = '+'
                elif grid[r][c] == '+':
                    grid[r][c] = '*'

    if show_start_end:
        # Mark start
        sr, sc = to_row(path[0][1]), to_col(path[0][0])
        if 0 <= sr < height and 0 <= sc < width:
            grid[sr][sc] = 'S'

        # Mark end
        er, ec = to_row(path[-1][1]), to_col(path[-1][0])
        if 0 <= er < height and 0 <= ec < width:
            grid[er][ec] = 'E'

    return [''.join(row) for row in grid]


def multiple_walks_endpoint_cloud(num_walks=2000, steps=500, width=72, height=36):
    """Show where many walks end up after N steps (should form a Gaussian)."""
    endpoints = []
    for _ in range(num_walks):
        x, y = 0.0, 0.0
        for _ in range(steps):
            dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
            x += dx
            y += dy
        endpoints.append((x, y))

    xs = [p[0] for p in endpoints]
    ys = [p[1] for p in endpoints]

    # Bin into grid
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    margin = 1

    def to_col(x):
        return int((x - min_x) / (max_x - min_x + 1) * (width - 2*margin)) + margin
    def to_row(y):
        return int((max_y - y) / (max_y - min_y + 1) * (height - 2*margin)) + margin

    grid = [[0] * width for _ in range(height)]
    for x, y in endpoints:
        c, r = to_col(x), to_row(y)
        if 0 <= r < height and 0 <= c < width:
            grid[r][c] += 1

    max_d = max(max(row) for row in grid) or 1
    shade = ' ·:;+=xX#@█'

    lines = []
    for row in grid:
        line = ''
        for d in row:
            idx = int(d / max_d * (len(shade) - 1))
            line += shade[idx]
        lines.append(line)

    return lines, endpoints


def statistics(num_walks=500):
    """Show how distance grows with steps — should scale as √steps."""
    print("  Expected distance from origin after N steps  (averaged over 500 walks)")
    print()
    print("  steps │ expected   actual    ratio actual/√N")
    print("  ──────┼──────────────────────────────────────")

    for steps in [10, 25, 50, 100, 200, 500, 1000, 2000]:
        distances = []
        for _ in range(num_walks):
            x, y = 0.0, 0.0
            for _ in range(steps):
                dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
                x += dx
                y += dy
            distances.append(math.sqrt(x*x + y*y))

        avg = sum(distances) / len(distances)
        expected = math.sqrt(steps) * math.sqrt(math.pi / 4)  # known formula for 2D lattice
        bar_len = int(avg / 2)
        print(f"  {steps:5d} │ {expected:7.2f}    {avg:7.2f}   {avg/math.sqrt(steps):.4f}  {'█' * min(30, bar_len)}")


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                      R A N D O M   W A L K S                       ║")
    print("║  Each step: N, S, E, or W with equal probability                   ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    # Single long walk
    print("┌─ One walk: 5,000 steps ─────────────────────────────────────────────┐")
    path = random_walk_2d(5000)
    final_dist = math.sqrt(path[-1][0]**2 + path[-1][1]**2)
    print(f"│  Final position: ({path[-1][0]:.0f}, {path[-1][1]:.0f})")
    print(f"│  Distance from origin: {final_dist:.1f}  (√5000 = {math.sqrt(5000):.1f})")
    print("│")
    lines = render_walk(path, width=70, height=32)
    for line in lines:
        print("│ " + line)
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    # Many walks, where do they end up?
    print("┌─ Where do 2,000 walks end up after 500 steps? ─────────────────────┐")
    print("│  (each walk starts at center — density shows Gaussian distribution)")
    print("│")
    cloud_lines, endpoints = multiple_walks_endpoint_cloud(num_walks=2000, steps=500)
    for line in cloud_lines:
        print("│ " + line)
    avg_dist = sum(math.sqrt(x*x+y*y) for x,y in endpoints) / len(endpoints)
    print("│")
    print(f"│  Average distance: {avg_dist:.2f}  (expected √500 × √π/4 ≈ {math.sqrt(500)*math.sqrt(math.pi/4):.2f})")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    print("┌─ Scaling law: distance grows as √N ────────────────────────────────┐")
    print("│")
    statistics()
    print("│")
    print("│  The ratio actual/√N converges to √(π/4) ≈ 0.8862  (known result)")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    print("  Pólya's theorem: a 2D random walker always returns home.")
    print("  A 3D random walker escapes with probability ≈ 65.95%.")
    print()


if __name__ == '__main__':
    main()
