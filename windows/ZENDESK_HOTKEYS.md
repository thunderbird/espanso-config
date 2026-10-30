# Zendesk ticket links on Windows

Select a Zendesk ticket number, press a hotkey, and get a link to the ticket. Setup takes about five minutes. You do not need espanso, Git, or Python.

## Install

1. Press the Windows key, type `PowerShell`, and press Enter.
2. Copy all of this block, paste it into PowerShell, and press Enter:

   ```powershell
   winget install --id AutoHotkey.AutoHotkey -e --accept-source-agreements --accept-package-agreements
   $dir = "$HOME\Documents\zendesk-hotkeys"
   New-Item -ItemType Directory -Force $dir | Out-Null
   foreach ($f in "links.ahk", "zendesk_link.ahk", "clipboard.ahk") {
     Invoke-WebRequest "https://raw.githubusercontent.com/thunderbird/espanso-config/main/windows/autohotkey/$f" -OutFile "$dir\$f" -UseBasicParsing
   }
   $startup = [Environment]::GetFolderPath("Startup")
   $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$startup\zendesk-hotkeys.lnk")
   $shortcut.TargetPath = "$dir\links.ahk"
   $shortcut.Save()
   Start-Process "$startup\zendesk-hotkeys.lnk"
   ```

3. Look for the green **H** icon in the notification area, next to the clock. If you do not see it, click the **^** arrow. The icon shows that the hotkeys work. They start again each time you log in.

If winget is not available, install AutoHotkey v2 from [autohotkey.com](https://www.autohotkey.com/), then paste the block again without its first line.

## Use

Select a ticket number, for example `12345` or `12345 Can't send mail`, or a ticket URL. Then:

| Where | Press | Result |
| --- | --- | --- |
| Zendesk, Gmail, Slack, Google Docs | **Shift+Ctrl+Win+Z**, then **Ctrl+V** | A link: [Zendesk ticket #12345: Can't send mail](https://tbpro.zendesk.com/agent/tickets/12345) |
| GitHub, Bugzilla, text editors | **Ctrl+Win+Z** | The selection changes to `[Zendesk ticket #12345: Can't send mail](https://tbpro.zendesk.com/agent/tickets/12345)` |

- Text after the number goes in the link. Text before it is ignored.
- If nothing is selected, the hotkeys use the text that you copied, and you press Ctrl+V.
- Customers usually cannot open ticket links. Use them in internal notes, Slack, GitHub, and Bugzilla.
- A reply to a Google Play review is plain text. There, Zendesk shows the link as text with the URL in parentheses.

The hotkeys were tested in Firefox.

## Problems

- **Nothing happens:** the green **H** icon is missing. Double-click `links.ahk` in `Documents\zendesk-hotkeys`.
- **A tooltip says that there is no ticket number:** select text that contains the number.
- **Update:** paste the install block again. It downloads the new files and restarts the hotkeys.
