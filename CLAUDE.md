# Claude Recess - Root

GitHub: https://github.com/OdinMB/claude-recess

This is the root repository that archives all recess runs. Each `runs/run-xxxx/` folder is an independent Claude Code session with its own git history.

## Structure

```
leisure/
  runs/
    run-0001/           # Each run is its own git repo
    run-0002/
    ...
  run-template/         # Copied into new runs (CLAUDE.md, .claude/, .gitignore)
  new-run.sh            # Creates the next run folder
  sync.sh               # Stages nested repo files for the root repo
```

## Social card

The repo has a social/OG image at `social-card.png`, generated from `social-card.html`. Use `/update-social-card` after editing the HTML to regenerate the PNG.

Card titles must be max 24 characters (spaces included) to fit on one line.

## For Claude Code instances

If you're opened at the root level, your job is repo management — not creative work. To do creative work, open one of the `runs/run-xxxx/` directories directly.

## Starting a new run

When the user asks to start a new run:

1. Run `./new-run.sh` to create the next run folder.
2. Give the user the Docker sandbox command to copy into a new terminal:
   ```
   docker sandbox run claude ./runs/run-xxxx/
   ```
   (Replace `xxxx` with the actual run number.)
3. Do NOT start the sandbox yourself.
