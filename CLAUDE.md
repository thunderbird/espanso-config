# CLAUDE.md

Project decisions for Claude Code sessions on macOS and Windows. README.md and WINDOWS.md describe use and install.

## Layout

- `scripts/*.py` are uv scripts with inline dependencies (only `pyperclip`). macOS and Windows share them.
- `match/` and `scripts/run_uv_script.sh` are for macOS only. `windows/match/` is for Windows only, with the same file names and triggers.
- If the window title contains "Zendesk", `config/zendesk.yml` and the `_zendesk_html.yml` files make `:ghl` and `:zdl` expand to HTML. Espanso does not load match files that start with `_` by default.
- Triggers: `:ghl` and `:ghhtml` for GitHub issues, `:zdl` and `:zdhtml` for Zendesk tickets (`tbpro.zendesk.com` only).
- Tests: `uv run --with pytest --with pyperclip pytest tests`.

## Espanso facts that caused bugs

- In `shell` vars, espanso sets the environment variable `$CONFIG`. It replaces `%CONFIG%` only in `script` var args.
- Espanso 2.2.1 crashes on an empty expansion. Every macro must print something, also on errors.
- If the program exits with a nonzero code or writes anything to stderr, a `script` var fails. The Windows files use `ignore_error: true`, so the scripts must print errors to stdout and keep stderr empty.
- On macOS, a `script` var does not get the login shell `PATH`, so espanso cannot find uv. For this reason, macOS uses `shell` vars with `run_uv_script.sh`, and Windows uses `script` vars.
- On Windows, espanso runs `shell` vars in PowerShell.
- After an HTML expansion, espanso restores only plain text to the clipboard. For this reason, `--html` mode does not change the clipboard.
- Test a match without typing: `espanso match list -t --title "<window title>"`. To load other files, set `ESPANSO_CONFIG_DIR` to a temporary folder.
- On Windows, `espanso` is a GUI program and prints nothing in PowerShell, also with a pipe. `$config = espanso path config` was empty, so the install copied the scripts to `C:\scripts`. Use `espansod <command> | Out-String`.
- `%CONFIG%` is the espanso config root (`%APPDATA%\espanso` on Windows), not its `config` subfolder. The scripts go in `%CONFIG%\scripts`.

## Workflow

- Two Claude Code sessions can run at the same time: one on macOS, one on Windows 11 in native PowerShell. Do not use WSL, because espanso on Windows runs Windows programs.
- Use one short-lived branch and pull request for each issue, and merge with a merge commit. Do not keep long-lived platform branches, because the folders separate the platforms.
- Give each session a different issue, so that the sessions do not change the same files.
- Test changes to `scripts/*.py` on both systems before you merge.
- Issue #9 is the Windows test checklist.
