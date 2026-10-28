# Work on an issue with Claude Code

This page tells a colleague how to work on an issue in this repository with [Claude Code](https://claude.com/claude-code). The example is the Windows issue #29. The steps on macOS are almost the same.

When Claude Code starts, it reads [CLAUDE.md](CLAUDE.md). CLAUDE.md records the project decisions and the facts that caused bugs, so you do not have to explain them.

## Before you start

The repository owner does these steps:

1. Add the colleague as a collaborator with write access to `thunderbird/espanso-config`.
2. Assign the issue to the colleague on GitHub. Two people must not work on the same issue, because they change the same files.

## Install the tools on Windows

Run these commands in PowerShell. Do not use WSL, because espanso and AutoHotkey run Windows programs.

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id astral-sh.uv -e
winget install --id AutoHotkey.AutoHotkey -e
irm https://claude.ai/install.ps1 | iex
```

Then install espanso as [WINDOWS.md](WINDOWS.md) tells you. Open a new PowerShell window, so that it has the new `PATH`, and log in to GitHub:

```powershell
gh auth login
```

## Do the work

1. Get the repository:

   ```powershell
   gh repo clone thunderbird/espanso-config
   cd espanso-config
   ```

2. Start Claude Code in the repository folder:

   ```powershell
   claude
   ```

3. Give Claude Code the issue number, for example `implement #29`. Claude Code reads the issue, makes a branch, and writes the code.
4. When Claude Code asks you, test the result yourself. Claude Code cannot press hotkeys or see other windows. You must try the hotkey in a browser, Slack, and a text editor. Tell it exactly what happened, or paste a screenshot.
5. Ask Claude Code to open a pull request. Give the pull request to the repository owner for review. If the owner agrees, merge it with a merge commit.

## Rules

- Work on one issue in each branch and pull request.
- If the next person needs a new fact or decision, ask Claude Code to add it to CLAUDE.md in the same pull request.
- If you change `scripts/*.py`, test the change on macOS and on Windows before you merge.
- On a Windows computer that uses Synergy, read the Synergy note in CLAUDE.md before you test hotkeys.
