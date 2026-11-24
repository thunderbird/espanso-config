# Windows setup

This page tells you how to install the `:ghl`, `:ghhtml`, `:zdl`, `:zdhtml`, `:bugl`, `:bughtml`, `:hamburger`, `:warmgreet`, and `:warmclose` macros on Windows. [README.md](README.md) describes what each macro does.

The Windows match files are in `windows/match/`. They have the same names and triggers as the macOS files in `match/`. On Windows, espanso runs `shell` variables in PowerShell, so the Windows files use `script` variables, which run uv directly.

## Requirements

- [espanso](https://espanso.org/install/win/) 2.2.1 or later.
- [uv](https://docs.astral.sh/uv/). To install it, run `winget install --id=astral-sh.uv -e` in PowerShell.
- Optional: the [GitHub CLI](https://cli.github.com/) (`gh`). To install it, run `winget install --id GitHub.cli -e`. Then run `gh auth login`. The GitHub macro uses a token for private repositories and a higher API rate limit.

If you install uv while espanso runs, restart espanso. Espanso reads the `PATH` one time, at start, and does not see later changes. A PowerShell window that was open before you installed uv also has the old `PATH`, and an espanso that you restart from it cannot find uv. Restart espanso from a new PowerShell window, or quit espanso from the tray icon and start it from the Start menu.

## The espanso command in PowerShell

On Windows, the `espanso` command prints nothing in PowerShell, because espanso is a GUI program. Commands such as `espanso restart` work, but commands that print a result, such as `espanso path`, do not show it. To see the result, run `espansod` instead of `espanso`, and send the output to `Out-String`. For example:

```powershell
espansod path | Out-String
```

`espansod` is in the same folder as `espanso`, so it is on your `PATH`.

## Install

You can copy the files or link them. After you pull this repository, a link shows the new version. A copy does not, so you must copy the files again after each update.

Do not install `scripts/run_uv_script.sh` or the files in `match/`. They are for macOS only. If you install them, espanso has two versions of each trigger.

### Copy the files

Open PowerShell in the root of this repository and run these commands:

```powershell
$config = (espansod path config | Out-String).Trim()
if (-not $config) { throw "espansod path config printed nothing" }
New-Item -ItemType Directory -Force "$config\scripts" | Out-Null
Copy-Item scripts\gh_issue_link.py, scripts\zd_ticket_link.py, scripts\bugzilla_link.py "$config\scripts\"
Copy-Item config\zendesk.yml "$config\config\"
Copy-Item windows\match\*.yml "$config\match\"
```

### Link the files

A symbolic link needs Developer Mode or an administrator PowerShell. To turn on Developer Mode, open Settings > System > For developers.

Open PowerShell in the root of this repository and run these commands:

```powershell
$config = (espansod path config | Out-String).Trim()
if (-not $config) { throw "espansod path config printed nothing" }
New-Item -ItemType Directory -Force "$config\scripts" | Out-Null
foreach ($f in "scripts\gh_issue_link.py", "scripts\zd_ticket_link.py", "scripts\bugzilla_link.py", "config\zendesk.yml") {
  New-Item -ItemType SymbolicLink -Path "$config\$f" -Target "$PWD\$f"
}
foreach ($f in Get-ChildItem windows\match\*.yml) {
  New-Item -ItemType SymbolicLink -Path "$config\match\$($f.Name)" -Target $f.FullName
}
```

### Make sure that espanso loaded the macros

Run these commands:

```powershell
espanso restart
espansod match list -t | Out-String
```

The list must include `:ghl`, `:ghhtml`, `:zdl`, `:zdhtml`, `:bugl`, `:bughtml`, `:hamburger`, `:warmgreet`, and `:warmclose`, each one time.

## Use

1. Copy a GitHub issue URL, a Zendesk ticket URL, or a Bugzilla bug URL.
2. Type the trigger.

In a browser tab with "Zendesk" in the title, `:ghl`, `:zdl`, and `:bugl` expand to HTML links. `config/zendesk.yml` controls this behavior.

## Troubleshooting

If no trigger expands, not even the built-in `:espanso`, and the trigger text stays on the screen, espanso does not see your keystrokes. This occurs if you type through Synergy, Barrier, Input Leap, or other software that sends the keys from a different computer. This software sends software events without a keyboard device, and by default espanso ignores these events. Add this line to `default.yml` in the `config` folder of the espanso config folder:

```yaml
win32_exclude_orphan_events: false
```

Espanso loads the change automatically.

If a trigger expands to nothing or to an espanso error, make sure that `uv --version` works in a new PowerShell window. Then run `espanso restart` in that window.

Make sure that the scripts are in the `scripts` folder directly below the espanso config folder, for example `C:\Users\<you>\AppData\Roaming\espanso\scripts\gh_issue_link.py`. The match files look for them there. If the scripts are in `C:\scripts` or in `espanso\config\scripts`, the install commands used an empty `$config`. Move the scripts to the correct folder.

To see the exact output of a macro, run the script yourself. First copy a URL, then run this command:

```powershell
uv run --script scripts\gh_issue_link.py
```

## Link hotkeys

The AutoHotkey script `windows/autohotkey/links.ahk` adds hotkeys that work without espanso and uv, as the macOS Quick Actions do. [windows/ZENDESK_HOTKEYS.md](windows/ZENDESK_HOTKEYS.md) is a one-page guide for support agents that installs them without a copy of this repository.

| Hotkey | Selection | Markdown link |
| --- | --- | --- |
| Ctrl+Win+Z | A Zendesk ticket number or URL | `[Zendesk ticket #12345: blah blah](https://tbpro.zendesk.com/agent/tickets/12345)` |
| Ctrl+Win+G | A GitHub issue URL | `[espanso-config #29: Issue title](https://github.com/thunderbird/espanso-config/issues/29)` |
| Ctrl+Win+H | A Bugzilla bug URL, `bugzil.la/N`, `N`, or `bug N` | `[Bug 1923456: Bug summary](https://bugzilla.mozilla.org/show_bug.cgi?id=1923456)` |
| Ctrl+Win+Y | A Notion page URL or page ID | `[Notion 89abcdef: Page title](https://www.notion.so/...)` |
| Ctrl+Win+L | None. Use it in Firefox, Chrome, or Edge. | `[Page title](https://example.com/)` |

The Zendesk, GitHub, Bugzilla, and Notion hotkeys replace the selection with the Markdown link. Add Shift, for example Shift+Ctrl+Win+Z, to copy the link as rich text and not change the selection. Then press Ctrl+V. Use the Shift hotkeys in Gmail and Slack. Slack shows a Markdown link as plain text.

- If nothing is selected, the hotkeys use the text on the clipboard and only copy the link.
- If the text is not a ticket, issue, bug, or Notion page, a tooltip shows the error and nothing changes.
- Zendesk: the hotkeys use the first number in the selection and ignore the text before it. Text after the number goes in the link text, so a selected `12345 blah blah` or a ticket URL followed by `blah blah` gives the link text `Zendesk ticket #12345: blah blah`.
- GitHub: the title comes from the GitHub API. For private repositories and a higher rate limit, install the [GitHub CLI](https://cli.github.com/) and run `gh auth login`. The hotkeys use the `gh` token, or the `GITHUB_TOKEN` or `GH_TOKEN` environment variable.
- Bugzilla: the summary comes from the Bugzilla API, so only public bugs work.
- Notion: the title comes from the words in the URL, because most Notion pages are private. The link text shows the last 8 characters of the page ID.
- Page link: Ctrl+Win+L and Shift+Ctrl+Win+L only copy the link. They take the title from the window title and the URL from the address bar with Ctrl+L and Ctrl+C, so the focus stays in the address bar. Firefox cuts a long title in the window title, so for a title with 250 or more characters, the hotkeys find the full title in the Firefox history. A Mozilla Support knowledge base article gets the link text `SUMO KB Article: ...` and a URL without the locale.

### Install the hotkeys

1. Install AutoHotkey v2. In PowerShell, run `winget install --id AutoHotkey.AutoHotkey -e`.
2. Open PowerShell in the root of this repository. To start the script now and at each login, run these commands:

   ```powershell
   $startup = [Environment]::GetFolderPath("Startup")
   $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$startup\links.lnk")
   $shortcut.TargetPath = "$PWD\windows\autohotkey\links.ahk"
   $shortcut.Save()
   Start-Process "$startup\links.lnk"
   ```

The green H icon in the notification area shows that the script runs. The shortcut points to the repository, so the script stays current when you pull. After you pull, right-click the icon and click **Reload Script**.

`links.ahk` needs the other `.ahk` files in `windows/autohotkey/` in the same folder. If you copy the script, copy all of them.

In VS Code, Ctrl+C without a selection copies the current line, so the hotkey uses that line. Select the text first.

## Test

```powershell
uv run --with pytest --with pyperclip pytest tests
```

The AutoHotkey tests run only if AutoHotkey v2 is installed.
