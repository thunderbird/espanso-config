; Hotkeys that turn the selection into a link, as the macOS Quick Actions do.
; WINDOWS.md tells you how to install this script. Issue #29 lists the hotkeys.
;
; Ctrl+Win+Z        Replace a selected Zendesk ticket number with the Markdown link.
; Shift+Ctrl+Win+Z  Copy the Zendesk link as rich text. Then press Ctrl+V.

#Requires AutoHotkey v2.0
#SingleInstance Force

#Include %A_ScriptDir%\zendesk_link.ahk
#Include %A_ScriptDir%\clipboard.ahk

^#z::LinkHotkey(ZendeskLinks, "markdown")
+^#z::LinkHotkey(ZendeskLinks, "html")

; Copies the selection with Ctrl+C and makes the links with makeLinks.
; If nothing is selected, uses the text that was on the clipboard, because
; Google Docs gives an empty selection to the macOS Quick Actions.
;
; markdown mode replaces the selection with the Markdown link and restores
; the clipboard. If nothing was selected, it only copies the link.
; html mode copies the HTML link with the Markdown link as plain text, and
; does not change the selection.
; On error, shows a tooltip and does not change the selection or the clipboard.
LinkHotkey(makeLinks, mode) {
    oldText := A_Clipboard
    saved := ClipboardAll()
    A_Clipboard := ""
    Send "^c"
    selection := ClipWait(0.5) ? A_Clipboard : ""
    fromClipboard := Trim(selection, " `t`r`n") = ""
    try {
        links := makeLinks(fromClipboard ? oldText : selection)
        if mode = "html" {
            CopyHtml(links.html, links.markdown)
            ShowTip("Copied " links.markdown "`nPress Ctrl+V.")
        } else if fromClipboard {
            A_Clipboard := links.markdown
            ShowTip("Copied " links.markdown "`nPress Ctrl+V.")
        } else {
            A_Clipboard := links.markdown
            Send "^v"
            ; Give the app time to read the clipboard before it changes back.
            Sleep 300
            A_Clipboard := saved
        }
    } catch Error as e {
        A_Clipboard := saved
        ShowTip("Error: " e.Message)
    }
}

ShowTip(message) {
    ToolTip message
    SetTimer () => ToolTip(), -4000
}
