#!/usr/bin/env bash
set -euo pipefail

# Find the next available run number
last=$(ls -d run-[0-9][0-9][0-9][0-9] 2>/dev/null | sort -V | tail -n1 | grep -oP '\d+' || echo "0")
next=$(printf "%04d" $((10#$last + 1)))
dir="run-$next"

echo "Creating $dir..."

cp -r run-template "$dir"
git init -b main "$dir"
git -C "$dir" add -A
git -C "$dir" commit -m "Init leisure run $next"

echo ""
echo "Created $dir — open it with: claude -p $dir"
