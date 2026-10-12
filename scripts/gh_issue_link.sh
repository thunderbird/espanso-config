#!/bin/sh
# Espanso wrapper for gh_issue_link.py. Passes all arguments to the script.
# Espanso can run with a minimal PATH, so add the usual uv and gh locations.
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH

out=$(uv run --quiet --script "$(dirname "$0")/gh_issue_link.py" "$@" 2>&1)
# Espanso 2.2.1 crashes on an empty expansion, so print an error if there is no output.
printf '%s' "${out:-gh-issue-link error: no output}"
