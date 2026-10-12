#!/bin/sh
# Espanso wrapper for the uv scripts in this folder.
# Usage: run_uv_script.sh <script.py> [arguments...]
# Espanso can run with a minimal PATH, so add the usual uv and gh locations.
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH

script="$1"
shift
out=$(uv run --quiet --script "$(dirname "$0")/$script" "$@" 2>&1)
# Espanso 2.2.1 crashes on an empty expansion, so print an error if there is no output.
printf '%s' "${out:-$script error: no output}"
