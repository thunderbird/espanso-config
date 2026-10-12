# espanso-config

Shared [espanso](https://espanso.org/) matches.

## `:ghlink` and `:ghhtml`: GitHub issue URL to a link

Copy a GitHub issue URL, then type `:ghlink`. The trigger expands to a Markdown link with the repository name, issue number, and issue title, and the clipboard also contains the link. For example:

```
[espanso-config #1: Add macro that turns a GitHub issue URL in the clipboard into a Markdown link](https://github.com/thunderbird/espanso-config/issues/1)
```

For apps that use HTML instead of Markdown, type `:ghhtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://github.com/thunderbird/espanso-config/issues/1">espanso-config #1: Add macro that turns a GitHub issue URL in the clipboard into a Markdown link</a>
```

In Zendesk, `:ghlink` also expands to the HTML link. Espanso finds Zendesk by the window title, so the browser tab title must contain "Zendesk". To add another HTML app, add a configuration file like `config/gh_issue_link_zendesk.yml` with a different `filter_title`.

The script can fail for two reasons: the clipboard does not contain an issue URL, or the GitHub API call fails. On a failure, the trigger expands to an error message and the clipboard does not change.

### Requirements

- [uv](https://docs.astral.sh/uv/). The script declares its dependencies inline, and uv installs them on the first run.
- Optional: the [GitHub CLI](https://cli.github.com/) (`gh`), logged in. The script uses `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token`, in that order. A token gives access to private repositories and a higher API rate limit.

### Install

Run these commands from the root of this repository:

```sh
CONFIG="$(espanso path config)"
mkdir -p "$CONFIG/scripts"
for f in scripts/gh_issue_link.py scripts/gh_issue_link.sh \
  match/gh_issue_link.yml match/gh_issue_html.yml match/_gh_issue_link_html.yml \
  config/gh_issue_link_zendesk.yml; do
  ln -s "$PWD/$f" "$CONFIG/$f"
done
```

Espanso reloads the configuration automatically.

### Test

```sh
uv run --with pytest --with pyperclip pytest tests
```
