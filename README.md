# espanso-config

Shared [espanso](https://espanso.org/) matches for macOS and Windows. For the Windows setup, read [WINDOWS.md](WINDOWS.md).

## `:ghl` and `:ghhtml`: GitHub issue URL to a link

Copy a GitHub issue URL, then type `:ghl`. The trigger expands to a Markdown link with the repository name, issue number, and issue title, and the clipboard also contains the link. For example:

```
[espanso-config #1: Add macro that turns a GitHub issue URL in the clipboard into a Markdown link](https://github.com/thunderbird/espanso-config/issues/1)
```

For apps that use HTML instead of Markdown, type `:ghhtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://github.com/thunderbird/espanso-config/issues/1">espanso-config #1: Add macro that turns a GitHub issue URL in the clipboard into a Markdown link</a>
```

The script can fail for two reasons: the clipboard does not contain an issue URL, or the GitHub API call fails. On a failure, the trigger expands to an error message and the clipboard does not change.

## `:zdl` and `:zdhtml`: Zendesk ticket URL to a link

Copy an MZLA Zendesk ticket URL, then type `:zdl`. The trigger expands to a Markdown link with the ticket number, and the clipboard also contains the link. For example:

```
[Zendesk ticket #8486](https://tbpro.zendesk.com/agent/tickets/8486)
```

For apps that use HTML instead of Markdown, type `:zdhtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://tbpro.zendesk.com/agent/tickets/8486">Zendesk ticket #8486</a>
```

The script does not call the Zendesk API. If the clipboard does not contain a `https://tbpro.zendesk.com/agent/tickets/<number>` URL, the trigger expands to an error message and the clipboard does not change.

## `:bugl` and `:bughtml`: Bugzilla bug URL to a link

Copy a Mozilla Bugzilla bug URL, then type `:bugl`. The trigger accepts the long URL, `https://bugzilla.mozilla.org/show_bug.cgi?id=2064458`, and the short URL, `bugzil.la/2064458`. The trigger expands to a Markdown link with the bug number and bug summary, and the clipboard also contains the link. The link always uses the long URL. For example:

```
[Bug 2064458: \[Thundermail\] Thundermail Send add-on doesn't display an error message if cookies are blocked](https://bugzilla.mozilla.org/show_bug.cgi?id=2064458)
```

For apps that use HTML instead of Markdown, type `:bughtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=2064458">Bug 2064458: [Thundermail] Thundermail Send add-on doesn't display an error message if cookies are blocked</a>
```

The script gets the summary from the Bugzilla REST API without an API key, so it works only for public bugs. If the clipboard does not contain a bug URL, or the API call fails, the trigger expands to an error message and the clipboard does not change.

## HTML links in Zendesk

In Zendesk, `:ghl`, `:zdl`, and `:bugl` expand to HTML links instead of Markdown. Espanso finds Zendesk by the window title, so the browser tab title must contain "Zendesk". To add another HTML app, add a configuration file like `config/zendesk.yml` with a different `filter_title`.

## Requirements

- [uv](https://docs.astral.sh/uv/). The scripts declare their dependencies inline, and uv installs them on the first run.
- Optional: the [GitHub CLI](https://cli.github.com/) (`gh`), logged in. The GitHub script uses `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token`, in that order. A token gives access to private repositories and a higher API rate limit.

## Install on macOS

Run these commands from the root of this repository:

```sh
CONFIG="$(espanso path config)"
mkdir -p "$CONFIG/scripts"
for f in scripts/run_uv_script.sh scripts/gh_issue_link.py scripts/zd_ticket_link.py \
  scripts/bugzilla_link.py \
  match/gh_issue_link.yml match/gh_issue_html.yml \
  match/zd_ticket_link.yml match/zd_ticket_html.yml \
  match/bugzilla_link.yml match/bugzilla_html.yml match/_zendesk_html.yml \
  config/zendesk.yml; do
  ln -s "$PWD/$f" "$CONFIG/$f"
done
```

Espanso reloads the configuration automatically.

## Test

```sh
uv run --with pytest --with pyperclip pytest tests
```
