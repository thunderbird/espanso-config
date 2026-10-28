# CLAUDE.md

Project decisions for Claude Code sessions on macOS and Windows. README.md and WINDOWS.md describe use and install.

## Layout

- `scripts/*.py` are uv scripts with inline dependencies (only `pyperclip`). macOS and Windows share them.
- `match/` and `scripts/run_uv_script.sh` are for macOS only. `windows/match/` is for Windows only, with the same file names and triggers.
- If the window title contains "Zendesk" and the program is a browser (`filter_exec`), `config/zendesk.yml` and the `_zendesk_html.yml` files make `:ghl`, `:zdl`, and `:bugl` expand to HTML. Espanso does not load match files that start with `_` by default.
- The title filter alone is not enough: VS Code puts the first line of an untitled file in the window title, so a `:zdl` link there made VS Code get HTML.
- Markdown link text escapes only backslashes and unpaired brackets. Paired brackets, as in `[Thundermail] summary`, stay as they are.
- Triggers: `:ghl` and `:ghhtml` for GitHub issues, `:zdl` and `:zdhtml` for Zendesk tickets (`tbpro.zendesk.com` only), `:bugl` and `:bughtml` for Mozilla Bugzilla bugs (public bugs only).
- Tests: `uv run --with pytest --with pyperclip pytest tests`.
- `macos/shortcuts/` has the macOS Quick Actions (issues #14, #17, #22, #26, and #31) and the script that builds and signs them. Do not edit the `.shortcut` files. Change `build_shortcuts.py` or a `.js` file and run `build_shortcuts.py`. It rewrites all files, so restore the `.shortcut` files that you did not change.
- The `.js` files run with `osascript -l JavaScript`, so you can test them in the terminal. The build puts `zendesk_link.js`, `github_link.js`, and `bugzilla_link.js` in single quotes in a shell script, so they must not contain single quotes.

## Quick Action decisions

- Keys: Command-Control-Z for Zendesk, Control-Command-G for GitHub, Control-Command-H for Bugzilla, and Control-Command-L for the page link. Add Shift for the HTML version. Windows uses the same letters with Ctrl+Win. Bugzilla does not use B, because Windows uses Shift+Ctrl+Win+B to restart the graphics driver. It does not use U, because Gmail blocks Shift-Control-Command-U. KeyGap does not know Gmail keys, so test a new HTML key in Gmail in Firefox. If the key does nothing, start the Quick Action from the Services menu to find out if the key or the Quick Action is the problem. KeyGap showed Control-Command-L as free in all tested apps except Warp, which the user does not use. But Safari takes Control-Command-L, also with the focus in the address bar, and we did not find the Safari command. The user and colleagues use Safari little, so the README tells Safari users to press Shift-Control-Command-L, which copies the Markdown link as plain text too. KeyGap showed Command-Control-Z and Control-Command-H as free in Firefox, Safari, Chrome, Warp, iTerm, Terminal, Notion, and VS Code.
- The Markdown Quick Actions replace the selection. The HTML Quick Actions copy the link and do not change the selection, and the user presses Command-V. This is the only method that worked in Gmail in Firefox.
- The Quick Actions do not use espanso, uv, or Python, because a Quick Action does not get the login shell `PATH`.
- The Zendesk Quick Actions (#31) use the first number in the selection and ignore the text before it. Text after the number goes in the link text: `12345 blah blah` gives `Zendesk ticket #12345: blah blah`. A ticket URL followed by text gives the same link. Escaping and this text need `zendesk_link.js`, so the Zendesk Markdown Quick Action also needs "Allow Running Scripts". `:zdl` and `scripts/zd_ticket_link.py` do not change. The Windows hotkeys in #29 must do the same.
- If `/opt/homebrew/bin/gh` or `/usr/local/bin/gh` exists, the GitHub Quick Actions use its token. Other ways to give a token are still open.
- The Bugzilla Quick Actions accept the long URL, `bugzil.la/N`, a bare number, and `bug N` in any case, because Mozilla has only one Bugzilla. `:bugl` and `scripts/bugzilla_link.py` still accept only URLs. A change there needs a test on Windows too.
- The README documents import and building by hand, because we do not know whether colleagues can import the files.
- The page Quick Actions (#26) get no input, so they work without a selection, and they only copy the link. Safari and Chrome give the tab title and URL with AppleScript. Firefox gives only the window title, with " — <profile name>" if there is more than one profile. The Quick Action finds the most recent URL with this title in a copy of `places.sqlite` and `places.sqlite-wal` of each open profile. A profile is open if its `places.sqlite-wal` is not empty. The user chose this over keystrokes, because keystrokes need Accessibility permission (see below). `page_link.js` runs in a "Run JavaScript for Mac Automation" action (`runjavascriptforautomation`, parameter `Script`).
- Windows uses AutoHotkey v2 for the same hotkeys. Issue #29 covers all of them and replaces #15, #18, and #23.

## macOS Shortcuts facts that caused bugs

- The "begins with" condition needs a parameter name that we did not find. To test text, use "Match Text" and the "has any value" condition (`WFCondition` 100).
- Shortcuts imports a file with the name of an existing shortcut as "<name> 1". Delete the old shortcut first, and add the keyboard shortcut again.

- Some action fields take only a variable, for example `WFHTML` of "Make Rich Text from HTML" and `Input` of "Run Shell Script". A text value with a variable in it (`WFTextTokenString`) leaves the field empty. Use `WFTextTokenAttachment`.
- To find the parameter names of an action, search the dyld shared cache in `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/` for the action name, for example `Run Shell Script (Action Name)`.
- Firefox ignores rich text that a Quick Action returns. "Copy to Clipboard" copies rich text only as UTF-16 `public.html`, and Gmail in Firefox pastes nothing. For this reason, the HTML Quick Action copies UTF-8 HTML and plain text with `NSPasteboard` in a shell script.
- A Quick Action with no output does not change the selection.
- In VS Code, a Markdown Quick Action adds a `]` at the end, because "editor.autoSurround" puts brackets around the selection when the link starts with `[`. Set `"editor.autoSurround": "quotes"` in VS Code.
- The Services key of a Shift shortcut is in `defaults read pbs NSServicesStatus`, for example `@^$H`. Old entries stay there after you delete a shortcut. The case of the letter did not matter.
- "Run Shell Script" keeps the newline that `osascript` adds after the result, and the Markdown link then ends with a newline. The scripts use `printf %s "$(osascript ...)"` to remove it.
- A Quick Action that presses keys with System Events needs Accessibility permission. In "Run Shell Script", macOS asks it for `osascript`, and permission for `osascript` lets every script press keys. In "Run JavaScript for Mac Automation", macOS asks it for "Shortcuts", but this is `BackgroundShortcutRunner.xpc` in `WorkflowKit.framework`, and System Settings does not accept it in the Accessibility list. Permission for Shortcuts.app or Shortcuts Events.app does not help.
- In JavaScript for Automation, `doShellScript` returns lines that end with `\r`.
- "Run Shell Script" needs Shortcuts > Settings > Advanced > "Allow Running Scripts".
- `NSURLConnection` in JavaScript for Automation crashes `osascript` (exit code 139). `github_link.js` calls `curl` with `doShellScript`.
- `shortcuts sign` uses an Apple server and sometimes times out. Run the build again.
- `shortcuts run -i <file>` gives the Quick Action a file, not text. "Get Text from Input" then gives the file path, so the GitHub Quick Actions fail in the terminal. Test them with a real selection.
- `shortcuts run` and the importing of a file work from the terminal. Adding a shortcut, deleting it, and testing a keyboard shortcut need a person, because the terminal has no Accessibility permission.

## Espanso facts that caused bugs

- In `shell` vars, espanso sets the environment variable `$CONFIG`. It replaces `%CONFIG%` only in `script` var args.
- Espanso 2.2.1 crashes on an empty expansion. Every macro must print something, also on errors.
- If the program exits with a nonzero code or writes anything to stderr, a `script` var fails. The Windows files use `ignore_error: true`, so the scripts must print errors to stdout and keep stderr empty.
- On macOS, a `script` var does not get the login shell `PATH`, so espanso cannot find uv. For this reason, macOS uses `shell` vars with `run_uv_script.sh`, and Windows uses `script` vars.
- On Windows, espanso runs `shell` vars in PowerShell.
- After an HTML expansion, espanso restores only plain text to the clipboard. For this reason, `--html` mode does not change the clipboard.
- Test a match without typing: `espanso match list -t --title "<window title>"`. To load other files, set `ESPANSO_CONFIG_DIR` to a temporary folder.
- Espanso watches its own config folder, not the repo files behind the symlinks. After you change a linked file, run `espanso restart`.
- On Windows, `espanso` is a GUI program and prints nothing in PowerShell, also with a pipe. `$config = espanso path config` was empty, so the install copied the scripts to `C:\scripts`. Use `espansod <command> | Out-String`.
- On Windows, espanso ignores keystrokes from Synergy and similar software, because they have no HID device. The Windows laptop uses Synergy, so its `default.yml` has `win32_exclude_orphan_events: false`.
- `%CONFIG%` is the espanso config root (`%APPDATA%\espanso` on Windows), not its `config` subfolder. The scripts go in `%CONFIG%\scripts`.

## Workflow

- Two Claude Code sessions can run at the same time: one on macOS, one on Windows 11 in native PowerShell. Do not use WSL, because espanso on Windows runs Windows programs.
- Use one short-lived branch and pull request for each issue, and merge with a merge commit. Do not keep long-lived platform branches, because the folders separate the platforms.
- Give each session a different issue, so that the sessions do not change the same files.
- Test changes to `scripts/*.py` on both systems before you merge.
- Issue #9 is the Windows test checklist.
- CONTRIBUTING.md tells a colleague, for example a Windows user, how to work on an issue with Claude Code. Update it when the workflow changes.
