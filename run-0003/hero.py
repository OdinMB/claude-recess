"""
Hero render — one beautiful high-resolution image of the most visually
striking Langton's Ant configuration: the 12-state rule RRLLLRLLLRRR
with its dramatic geometric triangles.

Also renders a composite "gallery" of the best results.
"""

from __future__ import annotations
import colorsys
import math
from PIL import Image, ImageDraw, ImageFont

DELTAS = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}


def run_ant(rule: str, steps: int) -> tuple[dict, int, int]:
    """Run a single ant and return (grid, final_x, final_y)."""
    x, y, d = 0, 0, 0
    n = len(rule)
    grid: dict[tuple[int, int], int] = {}
    for _ in range(steps):
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
    return grid, x, y


def run_multi(ants_config: list[tuple[int, int, int, str]], steps: int) -> dict:
    """Run multiple ants on a shared grid."""
    ants = [[x, y, d, rule] for x, y, d, rule in ants_config]
    max_colors = max(len(a[3]) for a in ants)
    grid: dict[tuple[int, int], int] = {}
    for _ in range(steps):
        for ant in ants:
            x, y, d, rule = ant
            n = len(rule)
            color = grid.get((x, y), 0)
            instruction = rule[color % n]
            if instruction == "R":
                d = (d + 1) % 4
            elif instruction == "L":
                d = (d - 1) % 4
            grid[(x, y)] = (color + 1) % max_colors
            dx, dy = DELTAS[d]
            ant[0] = x + dx
            ant[1] = y + dy
            ant[2] = d
    return grid


def render_grid(grid: dict, n_colors: int, scale: int = 3, padding: int = 20,
                palette_style: str = "neon", bg: tuple = None) -> Image.Image:
    """Render a grid to a high-quality image."""
    if not grid:
        return Image.new("RGB", (100, 100), (0, 0, 0))

    xs = [k[0] for k in grid]
    ys = [k[1] for k in grid]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    w = (max_x - min_x + 1 + padding * 2) * scale
    h = (max_y - min_y + 1 + padding * 2) * scale

    # Palettes
    if palette_style == "neon":
        background = bg or (8, 8, 12)
        colors = [
            background,
            (0, 255, 140),    # electric green
            (255, 30, 120),   # hot pink
            (40, 200, 255),   # cyan
            (255, 200, 30),   # gold
            (180, 50, 255),   # violet
            (255, 120, 30),   # orange
            (30, 255, 255),   # aqua
            (255, 60, 60),    # red
            (100, 255, 50),   # lime
            (255, 150, 200),  # rose
            (50, 150, 255),   # blue
            (200, 200, 50),   # chartreuse
        ]
    elif palette_style == "monochrome":
        background = bg or (250, 248, 245)
        colors = [background, (20, 25, 30)]
    elif palette_style == "warm":
        background = bg or (12, 8, 15)
        colors = [
            background,
            (255, 100, 50),   # orange-red
            (255, 180, 30),   # amber
            (200, 50, 30),    # deep red
            (255, 220, 100),  # pale gold
            (180, 40, 60),    # burgundy
            (255, 140, 80),   # salmon
        ]
    elif palette_style == "ocean":
        background = bg or (5, 10, 20)
        colors = [
            background,
            (30, 180, 220),   # cerulean
            (20, 100, 180),   # deep blue
            (100, 220, 200),  # teal
            (180, 240, 255),  # ice
            (10, 60, 120),    # navy
            (50, 200, 160),   # sea green
        ]
    else:
        background = bg or (0, 0, 0)
        colors = [background]
        for i in range(1, n_colors):
            hue = (i - 1) / max(n_colors - 1, 1)
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 0.9)
            colors.append((int(r * 255), int(g * 255), int(b * 255)))

    img = Image.new("RGB", (w, h), background)
    pixels = img.load()

    for (cx, cy), color in grid.items():
        if color == 0:
            continue
        px = (cx - min_x + padding) * scale
        py = (cy - min_y + padding) * scale
        rgb = colors[color % len(colors)]
        for ddx in range(scale):
            for ddy in range(scale):
                if 0 <= px + ddx < w and 0 <= py + ddy < h:
                    pixels[px + ddx, py + ddy] = rgb

    return img


def main():
    print("Generating hero renders...\n")

    # 1. Twelve-state rule — the dramatic triangles
    print("1. RRLLLRLLLRRR (12-state, 1M steps)...")
    grid, _, _ = run_ant("RRLLLRLLLRRR", 1_000_000)
    img = render_grid(grid, 12, scale=2, padding=15, palette_style="neon")
    img.save("hero_twelve_state.png")
    print(f"   Saved: hero_twelve_state.png ({img.width}x{img.height})")

    # 2. RLLR at high steps — the bounded fractal
    print("2. RLLR (300k steps)...")
    grid, _, _ = run_ant("RLLR", 300_000)
    img = render_grid(grid, 4, scale=5, padding=12, palette_style="neon")
    img.save("hero_rllr.png")
    print(f"   Saved: hero_rllr.png ({img.width}x{img.height})")

    # 3. Classic highway — elegant simplicity
    print("3. Classic RL (15k steps)...")
    grid, _, _ = run_ant("RL", 15_000)
    img = render_grid(grid, 2, scale=5, padding=15, palette_style="monochrome")
    img.save("hero_classic.png")
    print(f"   Saved: hero_classic.png ({img.width}x{img.height})")

    # 4. Four ants collision in warm palette
    print("4. Four-ant collision (18k steps)...")
    d = 25
    grid = run_multi([
        (-d, -d, 0, "RL"),
        (d, -d, 1, "RL"),
        (d, d, 2, "RL"),
        (-d, d, 3, "RL"),
    ], 18_000)
    img = render_grid(grid, 2, scale=3, padding=20, palette_style="monochrome",
                      bg=(245, 240, 235))
    img.save("hero_four_ants.png")
    print(f"   Saved: hero_four_ants.png ({img.width}x{img.height})")

    # 5. RLLR swarm — 8 ants, ocean palette
    print("5. RLLR swarm (120k steps)...")
    swarm = []
    for i in range(8):
        angle = 2 * math.pi * i / 8
        x = int(20 * math.cos(angle))
        y = int(20 * math.sin(angle))
        swarm.append((x, y, i % 4, "RLLR"))
    grid = run_multi(swarm, 120_000)
    img = render_grid(grid, 4, scale=4, padding=12, palette_style="ocean")
    img.save("hero_swarm.png")
    print(f"   Saved: hero_swarm.png ({img.width}x{img.height})")

    # 6. RRL highway — produces a fast highway with wider trail
    print("6. RRL (80k steps)...")
    grid, _, _ = run_ant("RRL", 80_000)
    img = render_grid(grid, 3, scale=2, padding=15, palette_style="warm")
    img.save("hero_rrl.png")
    print(f"   Saved: hero_rrl.png ({img.width}x{img.height})")

    print("\nAll hero renders complete.")


if __name__ == "__main__":
    main()
