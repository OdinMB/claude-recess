#!/usr/bin/env bash
set -euo pipefail

# sync.sh — Stage all run files into the root repo for committing/pushing.
#
# Git treats directories with .git/ as submodules (gitlinks), so it won't
# track their files. This script temporarily hides the nested .git dirs,
# stages everything, then restores them.
#
# Usage:
#   ./sync.sh              # Stage only
#   ./sync.sh -c "message" # Stage and commit
#   ./sync.sh -p "message" # Stage, commit, and push

commit_msg=""
do_push=false

while getopts "c:p:" opt; do
    case $opt in
        c) commit_msg="$OPTARG" ;;
        p) commit_msg="$OPTARG"; do_push=true ;;
        *) echo "Usage: $0 [-c \"commit message\"] [-p \"commit message\"]"; exit 1 ;;
    esac
done

# Collect nested .git directories
nested_gits=()
for d in runs/run-*/; do
    if [ -d "$d.git" ]; then
        nested_gits+=("$d")
    fi
done

if [ ${#nested_gits[@]} -eq 0 ]; then
    echo "No nested git repos found. Nothing to do."
    exit 0
fi

# Temporarily rename .git dirs
echo "Hiding nested .git directories..."
for d in "${nested_gits[@]}"; do
    mv "$d.git" "$d.git_local"
done

# Restore on exit (even on failure)
restore() {
    echo "Restoring nested .git directories..."
    for d in "${nested_gits[@]}"; do
        if [ -d "$d.git_local" ]; then
            mv "$d.git_local" "$d.git"
        fi
    done
}
trap restore EXIT

# Stage everything
echo "Staging files..."
git add -A

if [ -n "$commit_msg" ]; then
    echo "Committing..."
    git commit -m "$commit_msg"

    if $do_push; then
        echo "Pushing..."
        git push
    fi
else
    echo ""
    echo "Files staged. Review with 'git status' and commit when ready."
    echo "Or re-run with: ./sync.sh -c \"your commit message\""
fi
