# espanso-config

Shared [espanso](https://espanso.org/) matches for macOS and Windows. For the Windows setup, read [WINDOWS.md](WINDOWS.md). To work on an issue with Claude Code, read [CONTRIBUTING.md](CONTRIBUTING.md).

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
[Bug 2064458: [Thundermail] Thundermail Send add-on doesn't display an error message if cookies are blocked](https://bugzilla.mozilla.org/show_bug.cgi?id=2064458)
```

For apps that use HTML instead of Markdown, type `:bughtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=2064458">Bug 2064458: [Thundermail] Thundermail Send add-on doesn't display an error message if cookies are blocked</a>
```

The script gets the summary from the Bugzilla REST API without an API key, so it works only for public bugs. If the clipboard does not contain a bug URL, or the API call fails, the trigger expands to an error message and the clipboard does not change.

## HTML links in Zendesk

In Zendesk, `:ghl`, `:zdl`, and `:bugl` expand to HTML links instead of Markdown. Espanso finds Zendesk by the window title and the program, so the browser tab title must contain "Zendesk", and the browser must be Firefox, Chrome, Edge, or Safari. Other apps, for example VS Code, always get Markdown, also if their window title contains "Zendesk". To add another HTML app, add a configuration file like `config/zendesk.yml` with a different `filter_title`.

## macOS Quick Actions: selected text or web page to a link

Eight Quick Actions for the macOS Shortcuts app change selected text into a link. Two more Quick Actions copy a link to the current web page. A Quick Action is a shortcut that runs from the Services menu or a keyboard shortcut in any app. The Quick Actions do not use espanso, uv, or Python.

Two Quick Actions change a selected ticket number into a Zendesk ticket link:

- Zendesk Link, Command-Control-Z: replaces the selection with the Markdown link, for example `[Zendesk ticket #8486](https://tbpro.zendesk.com/agent/tickets/8486)`.
- Zendesk HTML Link, Shift-Command-Control-Z: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link. Apps that do not accept rich text, for example VS Code, paste the Markdown link.
- The Quick Actions use the first number in the selection and ignore the text before it. If text follows the number, it goes in the link text. For example, `8486 Cannot log in` gives `[Zendesk ticket #8486: Cannot log in](https://tbpro.zendesk.com/agent/tickets/8486)`. A selected ticket URL followed by text gives the same link.
- If the selection has no number, both Quick Actions show a notification and do not change the selection.

Two Quick Actions change a selected GitHub issue URL into a link with the issue title, the same link that `:ghl` makes:

- GitHub Link, Control-Command-G: replaces the selection with the Markdown link.
- GitHub HTML Link, Shift-Control-Command-G: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link.
- The Quick Actions get the title from the GitHub API. If the GitHub CLI (`gh`) is installed with Homebrew and you are logged in, they send its token, so private repositories also work. Without a token, only public repositories work, and GitHub allows 60 requests an hour.
- If the selection is not a GitHub issue URL, or the API call fails, both Quick Actions show the error in a notification. The selection does not change.

Two Quick Actions change a selected Mozilla Bugzilla bug URL into a link with the bug summary, the same link that `:bugl` makes:

- Bugzilla Link, Control-Command-H: replaces the selection with the Markdown link.
- Bugzilla HTML Link, Shift-Control-Command-H: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link.
- The Quick Actions accept the long URL, `https://bugzilla.mozilla.org/show_bug.cgi?id=2064458`, the short URL, `bugzil.la/2064458`, the bug number alone, `2064458`, and `bug 2064458`. The link always uses the long URL.
- The Quick Actions get the summary from the Bugzilla REST API without an API key, so they work only for public bugs.
- If the selection is not a Bugzilla bug URL or bug number, or the API call fails, both Quick Actions show the error in a notification. The selection does not change.

Two Quick Actions change a selected Notion page URL into a link with the page title and the last 8 characters of the page ID:

- Notion Link, Control-Command-Y: replaces the selection with the Markdown link, for example `[Notion 89abcdef: Release checklist](https://www.notion.so/mzthunderbird/Release-checklist-0123456789abcdef0123456789abcdef)`.
- Notion HTML Link, Shift-Control-Command-Y: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link.
- A Notion page ID has 32 characters. The link text shows only the last 8, so that the link is short. The link target keeps the full ID, because Notion accepts only the full ID.
- The Quick Actions take the title from the words before the ID in the URL, because most Notion pages are private and the Notion API needs a token. These words do not have the punctuation of the title. If the URL has no title words, the link text is only `Notion 89abcdef`.
- The Quick Actions accept `notion.so` and `notion.site` URLs and a page ID alone, with or without hyphens. They remove the query, for example `?pvs=4`, and keep a block link after `#`. For a page that opens on top of a database (`?p=<id>`), the link goes to the page.
- If the selection is not a Notion page URL or page ID, both Quick Actions show the error in a notification. The selection does not change.

Two Quick Actions copy a link to the page in the front tab of Firefox, Safari, or Chrome, with the page title as link text. They need no selection:

- Page Link, Control-Command-L: copies the Markdown link, for example `[Change a selected Bugzilla bug URL into a link with macOS Quick Actions · Issue #22 · thunderbird/espanso-config](https://github.com/thunderbird/espanso-config/issues/22)`.
- Page HTML Link, Shift-Control-Command-L: copies a rich text link, with the Markdown link as plain text.
- In Safari, Control-Command-L does nothing, because Safari uses this key. Use Shift-Control-Command-L. It copies both links: apps that accept rich text paste the HTML link, and apps that accept only plain text, for example VS Code, paste the Markdown link. Page Link also works from the Services menu in Safari.
- Firefox gives only the window title, so the Quick Actions find the URL of the most recent visit with this title in the Firefox history (`places.sqlite`) of the open profiles. Private windows do not work, because they have no history. If two pages have the same title, the link goes to the one that you visited last.
- If the front app is not one of these browsers, or the page has no URL, both Quick Actions show the error in a notification.

Gmail in Firefox does not accept a rich text link from a Quick Action. For this reason, the HTML Quick Actions copy the link, and you paste it.

Google Docs gives the Quick Actions an empty selection. If the selection is empty, the Zendesk, GitHub, Bugzilla, and Notion Quick Actions use the text on the clipboard and copy the link. In Google Docs, do these steps:

1. Select the text and press Command-C.
2. Press the keys of the Quick Action, for example Shift-Command-Control-Z.
3. Press Command-V to replace the selection with the link.

### Install by import

1. Download the `.shortcut` files that you want from `macos/shortcuts/`.
2. Double-click each file and select "Add Shortcut".
3. In Shortcuts, open Settings > Advanced and turn on "Allow Running Scripts". All Quick Actions need it.
4. Add the keyboard shortcuts. Open System Settings > Keyboard > Keyboard Shortcuts > Services. Double-click to the right of the Quick Action name and press its keys from the lists above. The page Quick Actions are in the Shortcuts group, and the other Quick Actions are in the Text group.
5. The first time that you use a page Quick Action in a browser, macOS asks if Shortcuts can control the browser. Select "Allow".

If a shortcut with the same name exists, Shortcuts adds the new one with a number, for example "Zendesk HTML Link 1". Delete the old shortcut before you import a new version, and add the keyboard shortcut again.

### Build by hand

If you cannot import the files, make the Quick Actions in the Shortcuts app. Give each shortcut the name from the lists above. Open the shortcut details with the "i" button, and turn on "Use as Quick Action" and "Services Menu". After you make them, do steps 3 and 4 of "Install by import".

To make a GitHub Quick Action by hand, save `macos/shortcuts/github_link.js` in your home folder. Set the Quick Action to receive Text, and add these actions:

1. "Get Text from Input" with Shortcut Input.
2. "Run Shell Script" with the shell zsh and "Pass Input" set to "as arguments". Set the input to Text, and use this script. For GitHub HTML Link, change `markdown` to `html`.

   ```sh
   [ -x /opt/homebrew/bin/gh ] && export GH_TOKEN="$(/opt/homebrew/bin/gh auth token 2>/dev/null)"
   printf %s "$(osascript -l JavaScript ~/github_link.js markdown "$1")"
   ```

3. "Match Text" with the pattern `^Error:` in Shell Script Result.
4. "If" with Matches and "has any value". After "If", add "Show Notification" with Shell Script Result.
5. For GitHub Link only, add "Stop and Output" with Shell Script Result after "Otherwise".

To make a Bugzilla Quick Action by hand, save `macos/shortcuts/bugzilla_link.js` in your home folder. Then make a Quick Action with the same actions as a GitHub Quick Action, but use this script in "Run Shell Script". For Bugzilla HTML Link, change `markdown` to `html`.

```sh
printf %s "$(osascript -l JavaScript ~/bugzilla_link.js markdown "$1")"
```

To make a Notion Quick Action by hand, save `macos/shortcuts/notion_link.js` in your home folder. Then make a Quick Action with the same actions as a GitHub Quick Action, but use this script in "Run Shell Script". For Notion HTML Link, change `markdown` to `html`.

```sh
printf %s "$(osascript -l JavaScript ~/notion_link.js markdown "$1")"
```

To make a Zendesk Quick Action by hand, save `macos/shortcuts/zendesk_link.js` in your home folder. Then make a Quick Action with the same actions as a GitHub Quick Action, but use this script in "Run Shell Script". For Zendesk HTML Link, change `markdown` to `html`.

```sh
printf %s "$(osascript -l JavaScript ~/zendesk_link.js markdown "$1")"
```

To make a page Quick Action by hand, set the Quick Action to receive no input. Add these actions:

1. "Run JavaScript for Mac Automation". Replace its script with `var PAGE_LINK_MODE = "markdown";` on the first line and the contents of `macos/shortcuts/page_link.js` after it. For Page HTML Link, change `markdown` to `html`.
2. "Match Text" with the pattern `^Error:` in Result.
3. "If" with Matches and "has any value". After "If", add "Show Notification" with Result.

### Change the Quick Actions

`macos/shortcuts/build_shortcuts.py` makes the `.shortcut` files and signs them with `shortcuts sign`. It puts `macos/shortcuts/zendesk_link.js` in the Zendesk Quick Actions, `macos/shortcuts/github_link.js` in the GitHub Quick Actions, `macos/shortcuts/bugzilla_link.js` in the Bugzilla Quick Actions, `macos/shortcuts/notion_link.js` in the Notion Quick Actions, and `macos/shortcuts/page_link.js` in the page Quick Actions. After you change one of these files, run the build script on a Mac:

```sh
uv run macos/shortcuts/build_shortcuts.py
```

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
