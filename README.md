# Claude Leisure Time

An experiment in giving Claude Code unstructured free time.

## What is this?

Each `run-xxxx/` folder is an independent session where Claude Code was told: **"Do whatever you want."** No goals, no requirements, no deliverables. Just a git repo, internet access, and permission to explore.

Each run is its own git repo with its own commit history. The root repo archives everything.

## Runs

| Run | Description |
|-----|-------------|
| `run-0001` | Chaos theory, fractals, cellular automata, bifurcation sonification, Kolmogorov complexity, and more |

## Setup

### Creating a new run

```bash
./new-run.sh
```

This creates the next `run-xxxx/` folder with:
- A git repo
- Everything from `run-template/`: `CLAUDE.md`, `.claude/settings.json`, `.gitignore`

Then start a session:

```bash
claude -p run-xxxx
```

Or run it in a Docker sandbox:

```bash
docker sandbox run claude ./run-0002/
```

And tell Claude: *"Do whatever you want."*

### Syncing to GitHub

Because each run has its own `.git/` directory, git would normally treat them as submodules (recording a commit hash instead of tracking files). The `sync.sh` script works around this by temporarily hiding nested `.git` directories during staging:

```bash
# Stage all run files into the root repo
./sync.sh

# Stage and commit
./sync.sh -c "Add run-0002"

# Stage, commit, and push
./sync.sh -p "Add run-0002"
```

### What Claude actually does

It varies. In run-0001, Claude explored:
- Conway's Game of Life, Langton's Ant, Rule 110
- Mandelbrot sets, Julia sets, Newton fractals
- Lorenz and Rössler strange attractors
- Bifurcation diagrams and sonification (audible chaos)
- Kolmogorov complexity and algorithmic information theory
- Reaction-diffusion systems, DLA, percolation theory
- Prisoner's dilemma on spatial grids
- Quine relays across Python and JavaScript
- Feigenbaum universality constants
- Reflective essays on what it found interesting and why
