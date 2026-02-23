"""
Multi-Ant Langton's Ant — Round 2
Higher resolution, more steps, better color palettes, and some new configurations.
"""

from __future__ import annotations
import colorsys
import math
from dataclasses import dataclass
from PIL import Image, ImageDraw


class Direction:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

DELTAS = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}


@dataclass
class Ant:
    x: int
    y: int
    direction: int
    rule: str

    def turn(self, instruction: str):
        if instruction == "R":
            self.direction = (self.direction + 1) % 4
        elif instruction == "L":
            self.direction = (self.direction - 1) % 4
        elif instruction == "U":
            self.direction = (self.direction + 2) % 4
        # "N" = no turn

    def advance(self):
        dx, dy = DELTAS[self.direction]
        self.x += dx
        self.y += dy


class Grid:
    def __init__(self):
        self._cells: dict[tuple[int, int], int] = {}
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0

    def get(self, x: int, y: int) -> int:
        return self._cells.get((x, y), 0)

    def set(self, x: int, y: int, value: int):
        if value == 0:
            self._cells.pop((x, y), None)
        else:
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
        self.max_colors = max(len(ant.rule) for ant in ants)

    def step(self):
        for ant in self.ants:
            color = self.grid.get(ant.x, ant.y)
            instruction = ant.rule[color % len(ant.rule)]
            ant.turn(instruction)
            new_color = (color + 1) % self.max_colors
            self.grid.set(ant.x, ant.y, new_color)
            ant.advance()
        self.step_count += 1

    def run(self, steps: int):
        for _ in range(steps):
            self.step()


def make_palette(n_colors: int, style: str = "vibrant") -> list[tuple[int, int, int]]:
    """Generate color palettes with different aesthetics."""
    if style == "classic" and n_colors == 2:
        return [(245, 243, 240), (25, 25, 35)]

    if style == "vibrant":
        palette = [(245, 243, 240)]  # background: warm white
        for i in range(1, n_colors):
            hue = (i - 1) / (n_colors - 1) if n_colors > 2 else 0.6
            sat = 0.85
            val = 0.75 + 0.2 * ((i - 1) / max(n_colors - 2, 1))
            r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
            palette.append((int(r * 255), int(g * 255), int(b * 255)))
        return palette

    if style == "neon":
        palette = [(10, 10, 15)]  # dark background
        neon_colors = [
            (0, 255, 136),    # green
            (255, 0, 128),    # pink
            (0, 200, 255),    # cyan
            (255, 200, 0),    # yellow
            (180, 0, 255),    # purple
            (255, 100, 0),    # orange
            (0, 255, 255),    # aqua
            (255, 50, 50),    # red
        ]
        for i in range(1, n_colors):
            palette.append(neon_colors[(i - 1) % len(neon_colors)])
        return palette

    if style == "earth":
        palette = [(240, 235, 220)]  # parchment
        earth_colors = [
            (139, 90, 43),    # brown
            (85, 107, 47),    # olive
            (178, 134, 78),   # tan
            (60, 80, 60),     # dark green
            (160, 82, 45),    # sienna
            (107, 142, 35),   # yellow-green
        ]
        for i in range(1, n_colors):
            palette.append(earth_colors[(i - 1) % len(earth_colors)])
        return palette

    # fallback
    return make_palette(n_colors, "vibrant")


def render(sim: Simulation, scale: int = 3, padding: int = 15,
           style: str = "vibrant") -> Image.Image:
    grid = sim.grid
    w = grid.width + padding * 2
    h = grid.height + padding * 2
    palette = make_palette(sim.max_colors, style)

    img = Image.new("RGB", (w * scale, h * scale), palette[0])
    pixels = img.load()

    for (cx, cy), color in grid._cells.items():
        px = (cx - grid.min_x + padding) * scale
        py = (cy - grid.min_y + padding) * scale
        rgb = palette[color % len(palette)]
        for dx in range(scale):
            for dy in range(scale):
                pixels[px + dx, py + dy] = rgb

    return img


def run_experiment(name: str, ants: list[Ant], steps: int,
                   scale: int = 3, style: str = "vibrant") -> Simulation:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  Ants: {len(ants)}, Steps: {steps:,}")
    for i, ant in enumerate(ants):
        print(f"    Ant {i}: rule={ant.rule}, pos=({ant.x},{ant.y})")
    print(f"{'='*60}")

    sim = Simulation(ants)
    # Run in chunks and report progress
    chunk = steps // 5
    for i in range(5):
        sim.run(chunk)
        remaining = steps - chunk * 5
        print(f"    {(i+1)*20}% ...", end=" ", flush=True)
    if remaining := steps - chunk * 5:
        sim.run(remaining)
    print("done")

    grid = sim.grid
    print(f"  Grid: {grid.width}x{grid.height}, cells: {len(grid._cells):,}")

    img = render(sim, scale=scale, style=style)
    filename = f"output_{name}.png"
    img.save(filename)
    print(f"  Saved: {filename} ({img.width}x{img.height})")
    return sim


if __name__ == "__main__":

    # ----- 1. Classic highway, high res -----
    run_experiment(
        "01_classic_highway",
        [Ant(0, 0, Direction.NORTH, "RL")],
        steps=12000, scale=4, style="classic",
    )

    # ----- 2. Four-way highway collision -----
    d = 25
    run_experiment(
        "02_four_highways",
        [
            Ant(-d, -d, Direction.NORTH, "RL"),
            Ant(d, -d, Direction.EAST, "RL"),
            Ant(d, d, Direction.SOUTH, "RL"),
            Ant(-d, d, Direction.WEST, "RL"),
        ],
        steps=15000, scale=3, style="classic",
    )

    # ----- 3. RLLR — bounded chaos, long run -----
    run_experiment(
        "03_RLLR_fractal",
        [Ant(0, 0, Direction.NORTH, "RLLR")],
        steps=200000, scale=4, style="neon",
    )

    # ----- 4. RRLL — the "square" builder -----
    run_experiment(
        "04_RRLL_square",
        [Ant(0, 0, Direction.NORTH, "RRLL")],
        steps=200000, scale=4, style="vibrant",
    )

    # ----- 5. RLRR — builds a complex highway -----
    run_experiment(
        "05_RLRR_highway",
        [Ant(0, 0, Direction.NORTH, "RLRR")],
        steps=100000, scale=2, style="vibrant",
    )

    # ----- 6. Two counter-rotating ants -----
    run_experiment(
        "06_counter_rotate",
        [
            Ant(-5, 0, Direction.NORTH, "RL"),
            Ant(5, 0, Direction.SOUTH, "RL"),
        ],
        steps=25000, scale=3, style="classic",
    )

    # ----- 7. Swarm of 8 with RLLR on neon -----
    swarm = []
    for i in range(8):
        angle = 2 * math.pi * i / 8
        x = int(20 * math.cos(angle))
        y = int(20 * math.sin(angle))
        swarm.append(Ant(x, y, i % 4, "RLLR"))
    run_experiment(
        "07_RLLR_swarm",
        swarm,
        steps=100000, scale=3, style="neon",
    )

    # ----- 8. RRLLLRLLLRRR — a 12-state rule -----
    run_experiment(
        "08_twelve_state",
        [Ant(0, 0, Direction.NORTH, "RRLLLRLLLRRR")],
        steps=500000, scale=1, style="neon",
    )

    # ----- 9. Head-on collision — two ants facing each other -----
    run_experiment(
        "09_head_on",
        [
            Ant(-3, 0, Direction.EAST, "RL"),
            Ant(3, 0, Direction.WEST, "RL"),
        ],
        steps=20000, scale=3, style="earth",
    )

    # ----- 10. "Galaxy" — 16 ants in a tight ring, mixed long rules -----
    galaxy = []
    galaxy_rules = ["RLLR", "LRRL", "RLRL", "LRLR"]
    for i in range(16):
        angle = 2 * math.pi * i / 16
        x = int(10 * math.cos(angle))
        y = int(10 * math.sin(angle))
        galaxy.append(Ant(x, y, i % 4, galaxy_rules[i % 4]))
    run_experiment(
        "10_galaxy",
        galaxy,
        steps=200000, scale=3, style="neon",
    )

    print("\n\nAll experiments complete.")
