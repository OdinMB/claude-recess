"""
Maze Generation and Solving

A maze is a spanning tree of a grid graph.

Generation: Recursive backtracking (randomized DFS)
  - Start at a random cell
  - Randomly visit unvisited neighbors, carving walls
  - When stuck, backtrack
  - Result: a perfect maze (exactly one path between any two cells)

Solving: A* search with Manhattan distance heuristic
  - From entrance (top-left) to exit (bottom-right)
  - Finds the unique shortest path (since it's a tree, any path is shortest)

Rendering: Unicode box-drawing characters for clean output.
"""

import random
import heapq


def generate_maze(width, height, seed=None):
    """
    Returns a set of walls that have been removed.
    Wall between (r,c) and (r2,c2) is represented as frozenset({(r,c),(r2,c2)}).
    """
    if seed is not None:
        random.seed(seed)

    visited = set()
    removed_walls = set()

    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width:
                yield nr, nc

    def dfs(r, c):
        visited.add((r, c))
        dirs = list(neighbors(r, c))
        random.shuffle(dirs)
        for nr, nc in dirs:
            if (nr, nc) not in visited:
                removed_walls.add(frozenset(((r,c),(nr,nc))))
                dfs(nr, nc)

    # Use iterative DFS to avoid Python recursion limit
    start = (0, 0)
    visited.add(start)
    stack = [start]
    visited_from = {start: None}

    while stack:
        r, c = stack[-1]
        unvisited = [(nr, nc) for nr, nc in neighbors(r, c) if (nr, nc) not in visited]
        if unvisited:
            nr, nc = random.choice(unvisited)
            visited.add((nr, nc))
            removed_walls.add(frozenset(((r,c),(nr,nc))))
            stack.append((nr, nc))
        else:
            stack.pop()

    return removed_walls


def solve_maze(removed_walls, width, height, start=(0,0), end=None):
    """A* search. Returns list of (r,c) cells on the path."""
    if end is None:
        end = (height - 1, width - 1)

    def passable(r, c, nr, nc):
        return frozenset(((r,c),(nr,nc))) in removed_walls

    def heuristic(r, c):
        return abs(r - end[0]) + abs(c - end[1])

    heap = [(heuristic(*start), 0, start, [start])]
    seen = set()

    while heap:
        f, g, (r, c), path = heapq.heappop(heap)
        if (r, c) in seen:
            continue
        seen.add((r, c))
        if (r, c) == end:
            return path
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width:
                if passable(r, c, nr, nc) and (nr, nc) not in seen:
                    ng = g + 1
                    nf = ng + heuristic(nr, nc)
                    heapq.heappush(heap, (nf, ng, (nr, nc), path + [(nr, nc)]))

    return []  # No path found


def render_maze(removed_walls, width, height, solution=None, show_solution=True):
    """
    Render with box-drawing characters.
    Each cell takes 2x2 character space + borders.
    """
    sol_set = set(solution) if solution else set()

    # Build character grid
    # Grid is (2*height+1) rows × (2*width+1) cols
    rows = 2 * height + 1
    cols = 2 * width + 1
    grid = [['█'] * cols for _ in range(rows)]

    # Carve cell interiors
    for r in range(height):
        for c in range(width):
            gr, gc = 2*r+1, 2*c+1
            if (r, c) in sol_set:
                grid[gr][gc] = '·'
            else:
                grid[gr][gc] = ' '

    # Carve removed walls
    for wall in removed_walls:
        cells = list(wall)
        if len(cells) == 2:
            (r1,c1), (r2,c2) = cells
            # Middle point between the two cells
            mr = r1 + r2 + 1  # = (2r1+1) + (2r2+1) - (r1+r2+1) = ...
            mc = c1 + c2 + 1
            # Actually: midpoint of (2r1+1, 2c1+1) and (2r2+1, 2c2+1) is (r1+r2+1, c1+c2+1)
            wall_r = r1 + r2 + 1
            wall_c = c1 + c2 + 1
            if sol_set and {(r1,c1),(r2,c2)} <= sol_set:
                grid[wall_r][wall_c] = '·'
            else:
                grid[wall_r][wall_c] = ' '

    # Mark entrance and exit
    grid[1][0] = '>'  # entrance on left
    grid[2*height-1][2*width] = '>'  # exit on right

    # Mark start and end of solution
    if solution:
        sr, sc = solution[0]
        er, ec = solution[-1]
        grid[2*sr+1][2*sc+1] = 'S'
        grid[2*er+1][2*ec+1] = 'E'

    return [''.join(row) for row in grid]


def maze_stats(removed_walls, width, height, solution):
    total_cells = width * height
    total_walls = (width-1)*height + width*(height-1)  # internal walls
    removed = len(removed_walls)
    solution_len = len(solution)
    return {
        'cells': total_cells,
        'total_internal_walls': total_walls,
        'walls_removed': removed,
        'walls_remaining': total_walls - removed,
        'solution_steps': solution_len,
        'solution_efficiency': solution_len / total_cells,
    }


def main():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                          M A Z E                                   ║")
    print("║  Generated by recursive backtracking (randomized DFS)             ║")
    print("║  Solved by A* with Manhattan distance heuristic                   ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    # Small maze to show both unsolved and solved
    print("┌─ 15×10 maze (unsolved) ─────────────────────────────────────────────┐")
    walls = generate_maze(15, 10, seed=42)
    solution = solve_maze(walls, 15, 10)
    lines = render_maze(walls, 15, 10, solution=None)
    for line in lines:
        print("│ " + line)
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    print("┌─ Same maze with solution path (·) ──────────────────────────────────┐")
    lines = render_maze(walls, 15, 10, solution=solution)
    for line in lines:
        print("│ " + line)
    stats = maze_stats(walls, 15, 10, solution)
    print("│")
    print(f"│  Solution: {stats['solution_steps']} cells visited out of {stats['cells']}")
    print(f"│  Path efficiency: {stats['solution_efficiency']*100:.1f}% of cells")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    # Larger maze
    print("┌─ 33×20 maze with solution ──────────────────────────────────────────┐")
    walls2 = generate_maze(33, 20, seed=137)
    solution2 = solve_maze(walls2, 33, 20)
    lines2 = render_maze(walls2, 33, 20, solution=solution2)
    for line in lines2:
        print("│" + line)
    stats2 = maze_stats(walls2, 33, 20, solution2)
    print("│")
    print(f"│  Grid: {33}×{20} = {stats2['cells']} cells")
    print(f"│  Solution length: {stats2['solution_steps']} steps")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    print("  A maze is a spanning tree of the grid graph.")
    print("  Every pair of cells has exactly one path between them.")
    print("  Randomized DFS produces long, winding passages (low branching factor).")
    print("  Prim's algorithm produces mazes with many short dead-ends.")
    print()
    print("  The solution path is unique because the maze is a tree.")
    print("  A* with Manhattan heuristic is admissible here: it never overestimates.")


if __name__ == '__main__':
    main()
