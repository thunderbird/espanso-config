# Windows setup

This page tells you how to install the `:ghl`, `:ghhtml`, `:zdl`, and `:zdhtml` macros on Windows. [README.md](README.md) describes what each macro does.

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
Copy-Item scripts\gh_issue_link.py, scripts\zd_ticket_link.py "$config\scripts\"
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
foreach ($f in "scripts\gh_issue_link.py", "scripts\zd_ticket_link.py", "config\zendesk.yml") {
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

The list must include `:ghl`, `:ghhtml`, `:zdl`, and `:zdhtml`, each one time.

## Use

1. Copy a GitHub issue URL or a Zendesk ticket URL.
2. Type the trigger.

In a browser tab with "Zendesk" in the title, `:ghl` and `:zdl` expand to HTML links. `config/zendesk.yml` controls this behavior.

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

## Test

```powershell
uv run --with pytest --with pyperclip pytest tests
```
