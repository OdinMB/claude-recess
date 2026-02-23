"""
Rule Space Survey for Generalized Langton's Ants
=================================================

There's an open conjecture (attributed to various people) that ALL
Langton's ant rule strings eventually produce highways. For rules with
more states, this remains unproven.

This script surveys all rule strings of length 2-5 using only R and L,
runs each for many steps, and classifies the behavior:
  - "highway": bounding box grows linearly (ant escaping)
  - "bounded": bounding box stays small relative to steps
  - "unclear": ambiguous (might need more steps)

We produce a visual catalog of the results.
"""

from __future__ import annotations
import itertools
import colorsys
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

DELTAS = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}


@dataclass
class Ant:
    x: int
    y: int
    direction: int
    rule: str

    def step(self, grid: dict) -> None:
        color = grid.get((self.x, self.y), 0)
        n = len(self.rule)
        instruction = self.rule[color % n]
        if instruction == "R":
            self.direction = (self.direction + 1) % 4
        elif instruction == "L":
            self.direction = (self.direction - 1) % 4
        grid[(self.x, self.y)] = (color + 1) % n
        dx, dy = DELTAS[self.direction]
        self.x += dx
        self.y += dy


def classify_rule(rule: str, steps: int = 100000) -> dict:
    """Run a rule and classify its behavior."""
    ant = Ant(0, 0, 0, rule)
    grid: dict[tuple[int, int], int] = {}

    # Track bounding box over time
    checkpoints = []
    check_interval = steps // 10

    for i in range(1, steps + 1):
        ant.step(grid)
        if i % check_interval == 0:
            if grid:
                xs = [k[0] for k in grid]
                ys = [k[1] for k in grid]
                bbox_size = max(max(xs) - min(xs), max(ys) - min(ys))
            else:
                bbox_size = 0
            checkpoints.append((i, bbox_size))

    # Classify based on growth pattern
    if len(checkpoints) >= 4:
        # Check last few checkpoints for linear growth
        sizes = [c[1] for c in checkpoints]
        # Growth rate in last half
        mid = len(sizes) // 2
        early_growth = sizes[mid] - sizes[0] if sizes[0] > 0 else sizes[mid]
        late_growth = sizes[-1] - sizes[mid]

        # If the bounding box is small relative to steps, it's bounded
        final_size = sizes[-1]
        if final_size < steps ** 0.4:  # Much less than sqrt growth
            behavior = "bounded"
        elif late_growth > early_growth * 0.5:  # Still growing
            behavior = "highway"
        elif final_size > steps ** 0.5:  # Large but slowing — probably highway
            behavior = "highway"
        else:
            behavior = "unclear"
    else:
        behavior = "unclear"

    # Get final bounds for rendering
    if grid:
        xs = [k[0] for k in grid]
        ys = [k[1] for k in grid]
        bounds = (min(xs), min(ys), max(xs), max(ys))
    else:
        bounds = (0, 0, 0, 0)

    return {
        "rule": rule,
        "behavior": behavior,
        "steps": steps,
        "final_bbox": bounds,
        "final_size": checkpoints[-1][1] if checkpoints else 0,
        "cells": len(grid),
        "grid": grid,
        "checkpoints": checkpoints,
    }


def render_thumbnail(grid: dict, n_colors: int, size: int = 150) -> Image.Image:
    """Render a small thumbnail of the grid state."""
    bg = (15, 15, 20)
    img = Image.new("RGB", (size, size), bg)

    if not grid:
        return img

    xs = [k[0] for k in grid]
    ys = [k[1] for k in grid]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x + 1
    h = max_y - min_y + 1

    # Scale to fit in thumbnail
    scale = min((size - 10) / max(w, 1), (size - 10) / max(h, 1))
    scale = max(scale, 0.1)  # minimum scale
    offset_x = (size - w * scale) / 2
    offset_y = (size - h * scale) / 2

    # Palette
    if n_colors == 2:
        palette = [(30, 30, 40), (180, 200, 240)]
    else:
        palette = [(30, 30, 40)]
        for i in range(1, n_colors):
            hue = (i - 1) / max(n_colors - 1, 1)
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.85)
            palette.append((int(r * 255), int(g * 255), int(b * 255)))

    pixels = img.load()
    for (cx, cy), color in grid.items():
        if color == 0:
            continue
        px = int((cx - min_x) * scale + offset_x)
        py = int((cy - min_y) * scale + offset_y)
        rgb = palette[color % len(palette)]
        # Draw pixel (possibly sub-pixel at low scales, that's fine)
        for dx in range(max(1, int(scale))):
            for dy in range(max(1, int(scale))):
                if 0 <= px + dx < size and 0 <= py + dy < size:
                    pixels[px + dx, py + dy] = rgb

    return img


def create_catalog(results: list[dict], filename: str = "catalog.png"):
    """Create a visual catalog of all tested rules."""
    thumb_size = 160
    label_height = 40
    cell_size = thumb_size + label_height
    padding = 10

    # Sort: highways first, then bounded, then unclear
    order = {"highway": 0, "bounded": 1, "unclear": 2}
    results.sort(key=lambda r: (order.get(r["behavior"], 3), r["rule"]))

    # Layout in a grid
    cols = 8
    rows = (len(results) + cols - 1) // cols

    img_w = cols * (cell_size + padding) + padding
    img_h = rows * (cell_size + padding) + padding + 60  # title area
    img = Image.new("RGB", (img_w, img_h), (5, 5, 10))
    draw = ImageDraw.Draw(img)

    # Title
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((padding, 10),
              f"Langton's Ant Rule Survey — {len(results)} rules tested",
              fill=(200, 200, 210), font=font)

    # Count behaviors
    n_highway = sum(1 for r in results if r["behavior"] == "highway")
    n_bounded = sum(1 for r in results if r["behavior"] == "bounded")
    n_unclear = sum(1 for r in results if r["behavior"] == "unclear")
    draw.text((padding, 30),
              f"Highway: {n_highway}  |  Bounded: {n_bounded}  |  Unclear: {n_unclear}",
              fill=(150, 150, 160), font=font)

    # Draw each result
    for idx, result in enumerate(results):
        col = idx % cols
        row = idx // cols
        x = padding + col * (cell_size + padding)
        y = 60 + padding + row * (cell_size + padding)

        # Render thumbnail
        n_colors = len(result["rule"])
        thumb = render_thumbnail(result["grid"], n_colors, thumb_size)
        img.paste(thumb, (x, y))

        # Border color by behavior
        border_color = {
            "highway": (80, 200, 120),
            "bounded": (200, 120, 80),
            "unclear": (150, 150, 80),
        }.get(result["behavior"], (100, 100, 100))

        # Draw border
        draw.rectangle([x-1, y-1, x+thumb_size, y+thumb_size],
                       outline=border_color, width=2)

        # Label
        label = f"{result['rule']}"
        draw.text((x + 4, y + thumb_size + 4), label,
                  fill=(220, 220, 230), font=font)

        behavior_short = result["behavior"][0].upper()  # H, B, U
        size_str = f"{result['final_size']}"
        info = f"{behavior_short} | bbox:{size_str} | {result['cells']:,}c"
        draw.text((x + 4, y + thumb_size + 18), info,
                  fill=(140, 140, 150), font=font)

    img.save(filename)
    print(f"\nCatalog saved: {filename} ({img.width}x{img.height})")


def main():
    # Generate all rule strings of length 2-5 using R and L
    rules = []
    for length in range(2, 6):
        for combo in itertools.product("RL", repeat=length):
            rule = "".join(combo)
            # Skip "all same" rules (trivially circular)
            if len(set(rule)) == 1:
                continue
            rules.append(rule)

    print(f"Testing {len(rules)} rule strings...")
    print(f"Rules: {', '.join(rules[:10])}... (and {len(rules)-10} more)")

    results = []
    for i, rule in enumerate(rules):
        # Use fewer steps for longer rules (they're slower)
        steps = {2: 120000, 3: 80000, 4: 60000, 5: 40000}[len(rule)]
        result = classify_rule(rule, steps=steps)
        results.append(result)
        behavior = result["behavior"]
        symbol = {"highway": "+", "bounded": "o", "unclear": "?"}[behavior]
        print(f"  [{i+1:3d}/{len(rules)}] {rule:6s} -> {behavior:8s} "
              f"(bbox={result['final_size']:5d}, cells={result['cells']:6,}) {symbol}")

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for behavior in ["highway", "bounded", "unclear"]:
        matching = [r for r in results if r["behavior"] == behavior]
        print(f"\n  {behavior.upper()} ({len(matching)}):")
        for r in matching:
            print(f"    {r['rule']:8s}  bbox={r['final_size']:5d}  cells={r['cells']:,}")

    create_catalog(results)


if __name__ == "__main__":
    main()
