"""
Multi-Ant Langton's Ant Simulator
=================================

Langton's Ant generalized to multiple ants with arbitrary rule strings.

A rule string like "RL" is the classic ant. Each character maps to a color state:
  R = turn right 90 degrees
  L = turn left 90 degrees

When an ant lands on a cell with color state i, it:
  1. Turns according to rule[i]
  2. Advances the cell color to (i+1) % len(rule)
  3. Moves forward one step

With rule strings longer than 2 (e.g., "RLR", "LLRR", "RLLR"), cells cycle
through more colors and produce wildly different emergent patterns.

Multiple ants on the same grid interact through the shared color state,
creating interference patterns, collisions, and sometimes surprising symmetry.
"""

from __future__ import annotations
import colorsys
from dataclasses import dataclass, field
from enum import IntEnum
from PIL import Image


class Direction(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


DELTAS = {
    Direction.NORTH: (0, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTH: (0, 1),
    Direction.WEST: (-1, 0),
}


@dataclass
class Ant:
    x: int
    y: int
    direction: Direction
    rule: str  # e.g., "RL", "RLR", "LLRR"

    def turn(self, instruction: str):
        if instruction == "R":
            self.direction = Direction((self.direction + 1) % 4)
        elif instruction == "L":
            self.direction = Direction((self.direction - 1) % 4)
        # Could add "U" (u-turn) and "N" (no turn) for even more variety

    def advance(self):
        dx, dy = DELTAS[self.direction]
        self.x += dx
        self.y += dy


class Grid:
    """Sparse grid — only stores non-zero cells."""

    def __init__(self):
        self._cells: dict[tuple[int, int], int] = {}
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0

    def get(self, x: int, y: int) -> int:
        return self._cells.get((x, y), 0)

    def set(self, x: int, y: int, value: int):
        self._cells[(x, y)] = value
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1


class Simulation:
    def __init__(self, ants: list[Ant]):
        self.grid = Grid()
        self.ants = ants
        self.step_count = 0
        # Determine the maximum number of color states needed
        self.max_colors = max(len(ant.rule) for ant in ants)

    def step(self):
        for ant in self.ants:
            color = self.grid.get(ant.x, ant.y)
            rule = ant.rule
            instruction = rule[color % len(rule)]
            ant.turn(instruction)
            new_color = (color + 1) % self.max_colors
            self.grid.set(ant.x, ant.y, new_color)
            ant.advance()
        self.step_count += 1

    def run(self, steps: int):
        for _ in range(steps):
            self.step()


def generate_palette(n_colors: int) -> list[tuple[int, int, int]]:
    """Generate n visually distinct colors using HSV rotation."""
    if n_colors == 2:
        return [(255, 255, 255), (20, 20, 30)]  # white and near-black
    palette = []
    for i in range(n_colors):
        hue = i / n_colors
        saturation = 0.75 if i > 0 else 0.0
        value = 1.0 if i == 0 else 0.5 + 0.4 * (i / n_colors)
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        palette.append((int(r * 255), int(g * 255), int(b * 255)))
    return palette


def render(sim: Simulation, scale: int = 2, padding: int = 10) -> Image.Image:
    """Render the grid state to a PIL Image."""
    grid = sim.grid
    w = grid.width + padding * 2
    h = grid.height + padding * 2
    palette = generate_palette(sim.max_colors)

    img = Image.new("RGB", (w * scale, h * scale), palette[0])
    pixels = img.load()

    for (cx, cy), color in grid._cells.items():
        if color == 0:
            continue
        px = (cx - grid.min_x + padding) * scale
        py = (cy - grid.min_y + padding) * scale
        rgb = palette[color % len(palette)]
        for dx in range(scale):
            for dy in range(scale):
                pixels[px + dx, py + dy] = rgb

    # Mark ant positions with a bright red dot
    for ant in sim.ants:
        px = (ant.x - grid.min_x + padding) * scale
        py = (ant.y - grid.min_y + padding) * scale
        for dx in range(scale):
            for dy in range(scale):
                if 0 <= px + dx < w * scale and 0 <= py + dy < h * scale:
                    pixels[px + dx, py + dy] = (255, 50, 50)

    return img


def run_experiment(name: str, ants: list[Ant], steps: int, scale: int = 2):
    """Run a simulation and save the result."""
    print(f"\n{'='*60}")
    print(f"  Experiment: {name}")
    print(f"  Ants: {len(ants)}, Steps: {steps:,}")
    for i, ant in enumerate(ants):
        print(f"    Ant {i}: rule={ant.rule}, start=({ant.x},{ant.y}), facing={ant.direction.name}")
    print(f"{'='*60}")

    sim = Simulation(ants)
    sim.run(steps)

    grid = sim.grid
    print(f"  Grid bounds: ({grid.min_x},{grid.min_y}) to ({grid.max_x},{grid.max_y})")
    print(f"  Grid size: {grid.width} x {grid.height}")
    print(f"  Non-zero cells: {len(grid._cells):,}")

    img = render(sim, scale=scale)
    filename = f"output_{name}.png"
    img.save(filename)
    print(f"  Saved: {filename} ({img.width}x{img.height})")
    return sim


if __name__ == "__main__":
    # ---------------------------------------------------------------
    # Experiment 1: Classic Langton's Ant — the highway emerges
    # ---------------------------------------------------------------
    run_experiment(
        "classic_highway",
        ants=[Ant(0, 0, Direction.NORTH, "RL")],
        steps=15000,
        scale=2,
    )

    # ---------------------------------------------------------------
    # Experiment 2: Four ants starting from corners, classic rules
    # They build highways that eventually interact
    # ---------------------------------------------------------------
    d = 30
    run_experiment(
        "four_ants_collision",
        ants=[
            Ant(-d, -d, Direction.NORTH, "RL"),
            Ant(d, -d, Direction.EAST, "RL"),
            Ant(d, d, Direction.SOUTH, "RL"),
            Ant(-d, d, Direction.WEST, "RL"),
        ],
        steps=20000,
        scale=2,
    )

    # ---------------------------------------------------------------
    # Experiment 3: "Chaos" rule — RLLR produces intricate fractals
    # ---------------------------------------------------------------
    run_experiment(
        "chaos_fractal",
        ants=[Ant(0, 0, Direction.NORTH, "RLLR")],
        steps=50000,
        scale=1,
    )

    # ---------------------------------------------------------------
    # Experiment 4: Two ants with different rules on the same grid
    # One builds structure, the other disrupts it
    # ---------------------------------------------------------------
    run_experiment(
        "competing_rules",
        ants=[
            Ant(-20, 0, Direction.EAST, "RL"),
            Ant(20, 0, Direction.WEST, "RLR"),
        ],
        steps=30000,
        scale=2,
    )

    # ---------------------------------------------------------------
    # Experiment 5: "Snowflake" — LLRR creates symmetric growth
    # ---------------------------------------------------------------
    run_experiment(
        "symmetric_growth",
        ants=[Ant(0, 0, Direction.NORTH, "LLRR")],
        steps=40000,
        scale=1,
    )

    # ---------------------------------------------------------------
    # Experiment 6: Swarm — 12 ants in a ring, mixed rules
    # ---------------------------------------------------------------
    import math
    swarm_ants = []
    rules = ["RL", "RLR", "RL", "RLLR", "RL", "RLR", "RL", "RLLR", "RL", "RLR", "RL", "RLLR"]
    for i in range(12):
        angle = 2 * math.pi * i / 12
        x = int(40 * math.cos(angle))
        y = int(40 * math.sin(angle))
        direction = Direction(i % 4)
        swarm_ants.append(Ant(x, y, direction, rules[i]))

    run_experiment(
        "swarm_ring",
        ants=swarm_ants,
        steps=30000,
        scale=1,
    )

    print("\n\nAll experiments complete.")
