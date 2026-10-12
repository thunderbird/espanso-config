# espanso-config

Shared [espanso](https://espanso.org/) matches.

## `:ghlink`: GitHub issue URL to Markdown link

Copy a GitHub issue URL, then type `:ghlink`. The trigger expands to a Markdown link with the repository name, issue number, and issue title, and the clipboard also contains the link. For example:

```
[espanso-config #1: Add macro that turns a GitHub issue URL in the clipboard into a Markdown link](https://github.com/thunderbird/espanso-config/issues/1)
```

The script can fail for two reasons: the clipboard does not contain an issue URL, or the GitHub API call fails. On a failure, the trigger expands to an error message and the clipboard does not change.

### Requirements

- [uv](https://docs.astral.sh/uv/). The script declares its dependencies inline, and uv installs them on the first run.
- Optional: the [GitHub CLI](https://cli.github.com/) (`gh`), logged in. The script uses `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token`, in that order. A token gives access to private repositories and a higher API rate limit.

### Install

Run these commands from the root of this repository:

```sh
CONFIG="$(espanso path config)"
mkdir -p "$CONFIG/scripts"
ln -s "$PWD/scripts/gh_issue_link.py" "$CONFIG/scripts/gh_issue_link.py"
ln -s "$PWD/match/gh_issue_link.yml" "$CONFIG/match/gh_issue_link.yml"
```

Espanso reloads the configuration automatically.

### Test

```sh
uv run --with pytest --with pyperclip pytest tests
```
