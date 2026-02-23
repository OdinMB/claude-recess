# Claude Recess - Root

This is the root repository that archives all recess runs. Each `run-xxxx/` folder is an independent Claude Code session with its own git history.

## Structure

```
leisure/
  run-0001/           # Each run is its own git repo
  run-0002/
  ...
  run-template/       # Copied into new runs (CLAUDE.md, .claude/, .gitignore)
  new-run.sh          # Creates the next run folder
  sync.sh             # Stages nested repo files for the root repo
```

## For Claude Code instances

If you're opened at the root level, your job is repo management — not creative work. To do creative work, open one of the `run-xxxx/` directories directly.
