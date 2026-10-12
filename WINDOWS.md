# Windows setup

This page tells you how to install the `:ghl`, `:ghhtml`, `:zdl`, and `:zdhtml` macros on Windows. [README.md](README.md) describes what each macro does.

The Windows match files are in `windows/match/`. They have the same names and triggers as the macOS files in `match/`. On Windows, espanso runs `shell` variables in PowerShell, so the Windows files use `script` variables, which run uv directly.

## Requirements

- [espanso](https://espanso.org/install/win/) 2.2.1 or later.
- [uv](https://docs.astral.sh/uv/). To install it, run `winget install --id=astral-sh.uv -e` in PowerShell.
- Optional: the [GitHub CLI](https://cli.github.com/) (`gh`). To install it, run `winget install --id GitHub.cli -e`. Then run `gh auth login`. The GitHub macro uses a token for private repositories and a higher API rate limit.

If you install uv while espanso runs, run `espanso restart`. Espanso reads the `PATH` one time, at start, and does not see later changes.

## Install

You can copy the files or link them. After you pull this repository, a link shows the new version. A copy does not, so you must copy the files again after each update.

Do not install `scripts/run_uv_script.sh` or the files in `match/`. They are for macOS only. If you install them, espanso has two versions of each trigger.

### Copy the files

Open PowerShell in the root of this repository and run these commands:

```powershell
$config = espanso path config
New-Item -ItemType Directory -Force "$config\scripts" | Out-Null
Copy-Item scripts\gh_issue_link.py, scripts\zd_ticket_link.py "$config\scripts\"
Copy-Item config\zendesk.yml "$config\config\"
Copy-Item windows\match\*.yml "$config\match\"
```

### Link the files

A symbolic link needs Developer Mode or an administrator PowerShell. To turn on Developer Mode, open Settings > System > For developers.

Open PowerShell in the root of this repository and run these commands:

```powershell
$config = espanso path config
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
espanso match list -t
```

The list must include `:ghl`, `:ghhtml`, `:zdl`, and `:zdhtml`, each one time.

## Use

1. Copy a GitHub issue URL or a Zendesk ticket URL.
2. Type the trigger.

In a browser tab with "Zendesk" in the title, `:ghl` and `:zdl` expand to HTML links. `config/zendesk.yml` controls this behavior.

## Troubleshooting

If a trigger expands to nothing or to an espanso error, make sure that `uv --version` works in a new PowerShell window. Then run `espanso restart`.

To see the exact output of a macro, run the script yourself. First copy a URL, then run this command:

```powershell
uv run --script scripts\gh_issue_link.py
```

## Test

```powershell
uv run --with pytest --with pyperclip pytest tests
```
