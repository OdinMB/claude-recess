# Claude Leisure Time

An experiment in giving Claude Code unstructured free time.

## What is this?

Each `run-xxxx/` folder is an independent session where Claude Code was told: **"Do whatever you want."** No goals, no requirements, no deliverables. Just a git repo, internet access, and permission to explore.

Each run is its own git repo with its own commit history. The root repo archives everything.

## Runs

See **[RUNS.md](RUNS.md)** for the full list and highlights.

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
# First time — creates a sandbox named claude-run-xxxx
docker sandbox run claude ./run-xxxx/

# Subsequent times — run by name (no workspace arg)
docker sandbox run claude-run-xxxx
```

And tell Claude: *"Do whatever you want."*

### Cleaning up sandboxes

Each `docker sandbox run claude ./run-xxxx/` creates a persistent sandbox. They accumulate over time.

```bash
# List all sandboxes
docker sandbox ls

# Remove a specific sandbox
docker sandbox rm claude-run-xxxx

# Remove all sandboxes and clean up state
docker sandbox reset
```

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

### Docker sandbox isolation

Docker sandboxes run Claude as an isolated `agent` user with its own home directory. The host's `~/.claude/` is **not** copied or mounted into the container — the only thing that enters is the workspace directory. This means sandboxed runs don't inherit user-level skills, commands, agents, `CLAUDE.md`, `settings.json`, or auto-memory from the host. The only instructions Claude sees are the ones in the run folder itself.

When running outside Docker (`claude -p run-xxxx`), user-level config _is_ loaded. The run template's `CLAUDE.md` takes precedence on conflicts, but user-level skills and commands are still discoverable.

Sources: [Docker Sandbox docs](https://docs.docker.com/ai/sandboxes/agents/claude-code/), [Docker Community Forums discussion](https://forums.docker.com/t/docker-sandbox-claude-missing-plugins-rules-user-level-config-such-as-claude-md/151158)

## Contributing

Want to add your own run? Here's how:

1. **Fork and clone** the repo.

2. **Create a run folder:**
   ```bash
   ./new-run.sh
   ```
   This creates the next `run-xxxx/` with a fresh git repo and the standard template.

3. **Start a session** — either directly or in a Docker sandbox:
   ```bash
   claude -p run-xxxx
   # or
   docker sandbox run claude ./run-xxxx/
   ```
   Tell Claude: *"Do whatever you want."*

4. **Let it run.** Don't steer. When it stops (rate limit, context limit, your call), the run is done.

5. **Add your run to [RUNS.md](RUNS.md)** — a row in the table and optionally a highlights section.

6. **Sync and commit** from the repo root:
   ```bash
   ./sync.sh -c "Add run-xxxx"
   ```
   This is needed because each run has its own `.git/` — the sync script temporarily hides them so the root repo can track the files.

7. **Open a PR.**

### Guidelines

- **One run per session.** Don't reuse a run folder for multiple sessions.
- **Don't edit Claude's output.** The point is to see what Claude does unprompted. Commit what it produces, as-is.
- **Docker sandbox recommended.** It keeps runs isolated from your user-level Claude config (skills, commands, global CLAUDE.md). See [Docker sandbox isolation](#docker-sandbox-isolation) above.
- **Any model works.** The run template doesn't assume a specific model.

### What Claude actually does

In its first run, Claude explored chaos theory, fractals, cellular automata, strange attractors, quine relays, and wrote reflective essays on what it found interesting. See **[RUNS.md](RUNS.md)** for the full list.
