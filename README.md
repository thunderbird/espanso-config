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
[Bug 2064458: [Thundermail] Thundermail Send add-on doesn't display an error message if cookies are blocked](https://bugzilla.mozilla.org/show_bug.cgi?id=2064458)
```

For apps that use HTML instead of Markdown, type `:bughtml`. The trigger expands to a rich text link, and the clipboard does not change. For example:

```html
<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=2064458">Bug 2064458: [Thundermail] Thundermail Send add-on doesn't display an error message if cookies are blocked</a>
```

The script gets the summary from the Bugzilla REST API without an API key, so it works only for public bugs. If the clipboard does not contain a bug URL, or the API call fails, the trigger expands to an error message and the clipboard does not change.

## HTML links in Zendesk

In Zendesk, `:ghl`, `:zdl`, and `:bugl` expand to HTML links instead of Markdown. Espanso finds Zendesk by the window title and the program, so the browser tab title must contain "Zendesk", and the browser must be Firefox, Chrome, Edge, or Safari. Other apps, for example VS Code, always get Markdown, also if their window title contains "Zendesk". To add another HTML app, add a configuration file like `config/zendesk.yml` with a different `filter_title`.

## macOS Quick Actions: selected text to a link

Four Quick Actions for the macOS Shortcuts app change selected text into a link. A Quick Action is a shortcut that runs on the selected text in any app. The Quick Actions do not use espanso, uv, or Python.

Two Quick Actions change a selected ticket number into a Zendesk ticket link:

- Zendesk Link, Command-Control-Z: replaces the selection with the Markdown link, for example `[Zendesk ticket #8486](https://tbpro.zendesk.com/agent/tickets/8486)`.
- Zendesk HTML Link, Shift-Command-Control-Z: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link. Apps that do not accept rich text, for example VS Code, paste the Markdown link.
- If the selection has no number, both Quick Actions show a notification and do not change the selection. If the selection has more than one number, they use the first number.

Two Quick Actions change a selected GitHub issue URL into a link with the issue title, the same link that `:ghl` makes:

- GitHub Link, Control-Command-G: replaces the selection with the Markdown link.
- GitHub HTML Link, Shift-Control-Command-G: copies a rich text link and does not change the selection. Press Command-V to replace the selection with the link.
- The Quick Actions get the title from the GitHub API. If the GitHub CLI (`gh`) is installed with Homebrew and you are logged in, they send its token, so private repositories also work. Without a token, only public repositories work, and GitHub allows 60 requests an hour.
- If the selection is not a GitHub issue URL, or the API call fails, both Quick Actions show the error in a notification. The selection does not change.

Gmail in Firefox does not accept a rich text link from a Quick Action. For this reason, the HTML Quick Actions copy the link, and you paste it.

### Install by import

1. Download the `.shortcut` files that you want from `macos/shortcuts/`.
2. Double-click each file and select "Add Shortcut".
3. In Shortcuts, open Settings > Advanced and turn on "Allow Running Scripts". The HTML Quick Actions and the GitHub Quick Actions need it.
4. Add the keyboard shortcuts. Open System Settings > Keyboard > Keyboard Shortcuts > Services. In the Text group, double-click to the right of the Quick Action name and press its keys from the lists above.

If a shortcut with the same name exists, Shortcuts adds the new one with a number, for example "Zendesk HTML Link 1". Delete the old shortcut before you import a new version, and add the keyboard shortcut again.

### Build by hand

If you cannot import the files, make each Zendesk Quick Action in the Shortcuts app:

1. Select File > New Shortcut, and give it the name "Zendesk Link" or "Zendesk HTML Link".
2. Open the shortcut details with the "i" button. Turn on "Use as Quick Action" and "Services Menu", and set it to receive Text.
3. Add the action "Match Text". Set the pattern to `\d+`, and set the text to Shortcut Input.
4. Add "Get Item from List" with "First Item" from Matches.
5. Add "If" with Item from List and "has any value".
6. For Zendesk Link, add these actions after "If":
   1. Add "Text" with `[Zendesk ticket #Item from List](https://tbpro.zendesk.com/agent/tickets/Item from List)`. Insert "Item from List" as a variable two times.
   2. Add "Stop and Output" with the Text variable.
7. For Zendesk HTML Link, add "Run Shell Script" after "If". Set the shell to zsh, set "Pass Input" to "as arguments", set the input to Item from List, and use this script:

   ```sh
   osascript -l JavaScript -e '
   function run(argv) {
     ObjC.import("AppKit");
     const number = argv[0];
     const url = "https://tbpro.zendesk.com/agent/tickets/" + number;
     const text = "Zendesk ticket #" + number;
     const pasteboard = $.NSPasteboard.generalPasteboard;
     pasteboard.clearContents;
     pasteboard.setStringForType($(`<a href="${url}">${text}</a>`), $("public.html"));
     pasteboard.setStringForType($(`[${text}](${url})`), $("public.utf8-plain-text"));
   }' "$1"
   ```

8. After "Otherwise", add "Show Notification" with the text "Select text that contains a ticket number."
9. Do steps 3 and 4 of "Install by import".

To make a GitHub Quick Action by hand, save `macos/shortcuts/github_link.js` in your home folder, and make a Quick Action with these actions:

1. "Get Text from Input" with Shortcut Input.
2. "Run Shell Script" with the shell zsh and "Pass Input" set to "as arguments". Set the input to Text, and use this script. For GitHub HTML Link, change `markdown` to `html`.

   ```sh
   [ -x /opt/homebrew/bin/gh ] && export GH_TOKEN="$(/opt/homebrew/bin/gh auth token 2>/dev/null)"
   osascript -l JavaScript ~/github_link.js markdown "$1"
   ```

3. "Match Text" with the pattern `^Error:` in Shell Script Result.
4. "If" with Matches and "has any value". After "If", add "Show Notification" with Shell Script Result.
5. For GitHub Link only, add "Stop and Output" with Shell Script Result after "Otherwise".

### Change the Quick Actions

`macos/shortcuts/build_shortcuts.py` makes the `.shortcut` files and signs them with `shortcuts sign`. It puts `macos/shortcuts/github_link.js` in the GitHub Quick Actions. After you change one of the two files, run the build script on a Mac:

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
