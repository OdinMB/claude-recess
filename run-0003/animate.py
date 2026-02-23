"""
Animated GIF of Langton's Ant — watching order emerge from chaos.

The classic RL ant spends ~10,000 steps in apparent chaos, then
spontaneously begins constructing a perfectly regular diagonal highway.
This animation captures that phase transition.
"""

from __future__ import annotations
import colorsys
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont


DELTAS = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}
DIR_NAMES = {0: "N", 1: "E", 2: "S", 3: "W"}


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


def render_frame(grid: dict, ants: list[Ant], n_colors: int,
                 step_num: int, fixed_bounds: tuple | None = None,
                 scale: int = 3, padding: int = 20) -> Image.Image:
    """Render one frame of the animation."""
    if fixed_bounds:
        min_x, min_y, max_x, max_y = fixed_bounds
    else:
        if not grid:
            min_x = min_y = -50
            max_x = max_y = 50
        else:
            xs = [k[0] for k in grid]
            ys = [k[1] for k in grid]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

    w = (max_x - min_x + 1 + padding * 2) * scale
    h = (max_y - min_y + 1 + padding * 2) * scale + 30  # extra for label

    # Background
    bg = (15, 15, 20)
    img = Image.new("RGB", (w, h), bg)
    pixels = img.load()

    # Color palette
    if n_colors == 2:
        palette = [(30, 30, 40), (200, 220, 255)]  # dark bg cell, light trail
    else:
        palette = [(30, 30, 40)]
        for i in range(1, n_colors):
            hue = (i - 1) / (n_colors - 1) if n_colors > 2 else 0.6
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.85)
            palette.append((int(r * 255), int(g * 255), int(b * 255)))

    # Draw cells
    for (cx, cy), color in grid.items():
        if color == 0:
            continue
        px = (cx - min_x + padding) * scale
        py = (cy - min_y + padding) * scale
        rgb = palette[color % len(palette)]
        for dx in range(scale):
            for dy in range(scale):
                if 0 <= px + dx < w and 0 <= py + dy < h - 30:
                    pixels[px + dx, py + dy] = rgb

    # Draw ant positions
    for ant in ants:
        px = (ant.x - min_x + padding) * scale
        py = (ant.y - min_y + padding) * scale
        for dx in range(scale):
            for dy in range(scale):
                if 0 <= px + dx < w and 0 <= py + dy < h - 30:
                    pixels[px + dx, py + dy] = (255, 80, 60)

    # Draw step counter at bottom
    draw = ImageDraw.Draw(img)
    label = f"Step {step_num:,}"
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((10, h - 25), label, fill=(180, 180, 190), font=font)

    return img


def animate_classic(filename: str = "anim_classic_highway.gif"):
    """Animate the classic RL ant showing the chaos-to-highway transition."""
    print("Animating classic RL ant...")

    ant = Ant(0, 0, 0, "RL")
    grid: dict[tuple[int, int], int] = {}
    frames = []

    total_steps = 13000
    # Capture frames at varying intervals:
    # - Dense early on (chaos phase is visually active)
    # - Sparser during highway (it's repetitive)
    frame_steps = []
    # Every 50 steps for first 1000
    frame_steps.extend(range(0, 1000, 50))
    # Every 100 steps from 1000 to 5000
    frame_steps.extend(range(1000, 5000, 100))
    # Every 200 steps from 5000 to 10000
    frame_steps.extend(range(5000, 10000, 200))
    # Every 300 steps from 10000 to 13000
    frame_steps.extend(range(10000, total_steps + 1, 300))
    frame_steps = sorted(set(frame_steps))

    # First pass: run simulation to get final bounds
    test_ant = Ant(0, 0, 0, "RL")
    test_grid: dict[tuple[int, int], int] = {}
    for _ in range(total_steps):
        test_ant.step(test_grid)
    xs = [k[0] for k in test_grid]
    ys = [k[1] for k in test_grid]
    fixed_bounds = (min(xs), min(ys), max(xs), max(ys))
    del test_ant, test_grid
    print(f"  Bounds: {fixed_bounds}")

    # Second pass: render frames
    current_step = 0
    for target_step in frame_steps:
        while current_step < target_step:
            ant.step(grid)
            current_step += 1
        frame = render_frame(grid, [ant], 2, current_step,
                             fixed_bounds=fixed_bounds, scale=3)
        frames.append(frame)
        if current_step % 2000 == 0:
            print(f"    Frame at step {current_step:,}")

    print(f"  {len(frames)} frames captured")

    # Save as GIF
    # Durations: faster during chaos, pause at interesting moments
    durations = []
    for s in frame_steps:
        if s < 1000:
            durations.append(80)
        elif s < 5000:
            durations.append(60)
        elif s < 10000:
            durations.append(50)
        else:
            durations.append(40)
    # Hold last frame longer
    durations[-1] = 2000

    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )
    print(f"  Saved: {filename}")


def animate_four_ants(filename: str = "anim_four_ants.gif"):
    """Animate four ants colliding from corners."""
    print("Animating four-ant collision...")

    d = 25
    ants = [
        Ant(-d, -d, 0, "RL"),
        Ant(d, -d, 1, "RL"),
        Ant(d, d, 2, "RL"),
        Ant(-d, d, 3, "RL"),
    ]
    grid: dict[tuple[int, int], int] = {}
    frames = []

    total_steps = 12000
    frame_steps = list(range(0, 3000, 80)) + list(range(3000, total_steps + 1, 150))
    frame_steps = sorted(set(frame_steps))

    # Get bounds
    test_ants = [Ant(a.x, a.y, a.direction, a.rule) for a in ants]
    test_grid: dict[tuple[int, int], int] = {}
    for _ in range(total_steps):
        for a in test_ants:
            a.step(test_grid)
    xs = [k[0] for k in test_grid]
    ys = [k[1] for k in test_grid]
    fixed_bounds = (min(xs), min(ys), max(xs), max(ys))
    del test_ants, test_grid
    print(f"  Bounds: {fixed_bounds}")

    current_step = 0
    for target_step in frame_steps:
        while current_step < target_step:
            for a in ants:
                a.step(grid)
            current_step += 1
        frame = render_frame(grid, ants, 2, current_step,
                             fixed_bounds=fixed_bounds, scale=2)
        frames.append(frame)
        if current_step % 3000 == 0:
            print(f"    Frame at step {current_step:,}")

    print(f"  {len(frames)} frames captured")

    durations = [70] * len(frames)
    durations[-1] = 2000

    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )
    print(f"  Saved: {filename}")


def animate_rllr_growth(filename: str = "anim_rllr_growth.gif"):
    """Animate RLLR bounded growth — watch the rectangles form."""
    print("Animating RLLR bounded growth...")

    ant = Ant(0, 0, 0, "RLLR")
    grid: dict[tuple[int, int], int] = {}
    frames = []

    total_steps = 80000
    frame_steps = (list(range(0, 5000, 100))
                   + list(range(5000, 20000, 300))
                   + list(range(20000, total_steps + 1, 800)))
    frame_steps = sorted(set(frame_steps))

    # Get bounds
    test_ant = Ant(0, 0, 0, "RLLR")
    test_grid: dict[tuple[int, int], int] = {}
    for _ in range(total_steps):
        test_ant.step(test_grid)
    xs = [k[0] for k in test_grid]
    ys = [k[1] for k in test_grid]
    fixed_bounds = (min(xs), min(ys), max(xs), max(ys))
    del test_ant, test_grid
    print(f"  Bounds: {fixed_bounds}")

    current_step = 0
    for target_step in frame_steps:
        while current_step < target_step:
            ant.step(grid)
            current_step += 1
        frame = render_frame(grid, [ant], 4, current_step,
                             fixed_bounds=fixed_bounds, scale=4)
        frames.append(frame)
        if current_step % 20000 == 0:
            print(f"    Frame at step {current_step:,}")

    print(f"  {len(frames)} frames captured")

    durations = [80] * len(frames)
    durations[-1] = 2000

    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )
    print(f"  Saved: {filename}")


if __name__ == "__main__":
    animate_classic()
    animate_four_ants()
    animate_rllr_growth()
    print("\nAll animations complete.")
