"""
Deep investigation of the RLR rule — one of the most studied
ambiguous Langton's Ant variants.

RLR is known to eventually produce a highway, but the transient
chaotic phase is exceptionally long. Let's track its bounding box
growth over time to see if we can catch the transition.
"""

from __future__ import annotations
import colorsys
from PIL import Image, ImageDraw, ImageFont

DELTAS = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}


def run_investigation():
    x, y, d = 0, 0, 0
    rule = "RLR"
    n = len(rule)
    grid: dict[tuple[int, int], int] = {}

    total_steps = 2_000_000
    check_interval = 10_000
    history = []

    print(f"Running RLR for {total_steps:,} steps...")
    print(f"{'Step':>12s} {'BBox':>8s} {'Cells':>10s} {'Ant pos':>16s}")
    print("-" * 52)

    for step in range(1, total_steps + 1):
        color = grid.get((x, y), 0)
        instruction = rule[color % n]
        if instruction == "R":
            d = (d + 1) % 4
        elif instruction == "L":
            d = (d - 1) % 4
        grid[(x, y)] = (color + 1) % n
        dx, dy = DELTAS[d]
        x += dx
        y += dy

        if step % check_interval == 0:
            if grid:
                xs = [k[0] for k in grid]
                ys = [k[1] for k in grid]
                bbox = max(max(xs) - min(xs), max(ys) - min(ys))
                bounds = (min(xs), min(ys), max(xs), max(ys))
            else:
                bbox = 0
                bounds = (0, 0, 0, 0)
            history.append((step, bbox, len(grid), x, y))
            if step % 200_000 == 0:
                print(f"{step:12,d} {bbox:8d} {len(grid):10,d} ({x:6d},{y:6d})")

    # Check if it escaped
    final_bbox = history[-1][1]
    mid_bbox = history[len(history)//2][1]
    growth = final_bbox - mid_bbox

    print(f"\nFinal analysis:")
    print(f"  Final bbox: {final_bbox}")
    print(f"  Mid bbox:   {mid_bbox}")
    print(f"  Growth in 2nd half: {growth}")
    print(f"  Final cells: {len(grid):,}")
    print(f"  Final ant position: ({x}, {y})")

    if growth > final_bbox * 0.3:
        print(f"  --> HIGHWAY detected! Still growing.")
    elif final_bbox > 500:
        print(f"  --> Likely highway (large bbox)")
    else:
        print(f"  --> Still appears bounded at {total_steps:,} steps")

    # Render the result
    if grid:
        xs_all = [k[0] for k in grid]
        ys_all = [k[1] for k in grid]
        min_x, max_x = min(xs_all), max(xs_all)
        min_y, max_y = min(ys_all), max(ys_all)
        w = max_x - min_x + 1
        h = max_y - min_y + 1
        padding = 20

        scale = max(1, min(4, 800 // max(w, h)))
        print(f"  Grid: {w}x{h}, using scale={scale}")

        iw = (w + padding * 2) * scale
        ih = (h + padding * 2) * scale + 40
        img = Image.new("RGB", (iw, ih), (10, 10, 15))
        pixels = img.load()

        palette = [
            (10, 10, 15),
            (0, 255, 136),
            (255, 0, 128),
        ]

        for (cx, cy), color in grid.items():
            if color == 0:
                continue
            px = (cx - min_x + padding) * scale
            py = (cy - min_y + padding) * scale
            rgb = palette[color % len(palette)]
            for ddx in range(scale):
                for ddy in range(scale):
                    if 0 <= px + ddx < iw and 0 <= py + ddy < ih - 40:
                        pixels[px + ddx, py + ddy] = rgb

        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, ih - 35),
                  f"RLR | {total_steps:,} steps | bbox={final_bbox} | {len(grid):,} cells",
                  fill=(180, 180, 190), font=font)
        img.save("output_RLR_deep.png")
        print(f"  Saved: output_RLR_deep.png ({iw}x{ih})")

    # Also plot bbox growth over time (as a simple text sparkline)
    print(f"\nBBox growth over time:")
    max_bbox = max(h[1] for h in history)
    bar_width = 60
    for i in range(0, len(history), len(history) // 20):
        step, bbox, cells, ax, ay = history[i]
        bar_len = int(bbox / max(max_bbox, 1) * bar_width)
        bar = "#" * bar_len
        print(f"  {step:10,d} |{bar:<{bar_width}s}| {bbox}")


if __name__ == "__main__":
    run_investigation()
