; Hotkeys that turn the selection into a link, as the macOS Quick Actions do.
; WINDOWS.md tells you how to install this script. Issue #29 lists the hotkeys.
;
; Ctrl+Win+Z        Replace a selected Zendesk ticket number with the Markdown link.
; Ctrl+Win+G        Replace a selected GitHub issue URL with the Markdown link.
; Ctrl+Win+H        Replace a selected Bugzilla bug URL or number with the Markdown link.
; Ctrl+Win+Y        Replace a selected Notion page URL with the Markdown link.
; Ctrl+Win+L        Copy the Markdown link to the page in Firefox, Chrome, or Edge.
;
; Add Shift to copy the link as rich text. Then press Ctrl+V.

#Requires AutoHotkey v2.0
#SingleInstance Force

#Include %A_ScriptDir%\markup.ahk
#Include %A_ScriptDir%\clipboard.ahk
#Include %A_ScriptDir%\web.ahk
#Include %A_ScriptDir%\zendesk_link.ahk
#Include %A_ScriptDir%\github_link.ahk
#Include %A_ScriptDir%\bugzilla_link.ahk
#Include %A_ScriptDir%\notion_link.ahk
#Include %A_ScriptDir%\page_link.ahk

^#z::LinkHotkey(ZendeskLinks, "markdown")
+^#z::LinkHotkey(ZendeskLinks, "html")
^#g::LinkHotkey(GitHubLinks, "markdown")
+^#g::LinkHotkey(GitHubLinks, "html")
^#h::LinkHotkey(BugzillaLinks, "markdown")
+^#h::LinkHotkey(BugzillaLinks, "html")
^#y::LinkHotkey(NotionLinks, "markdown")
+^#y::LinkHotkey(NotionLinks, "html")
^#l::PageLinkHotkey("markdown")
+^#l::PageLinkHotkey("html")

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

; Copies a link to the page in the active Firefox, Chrome, or Edge window.
; Gets the title from the window title, and the URL with Ctrl+L, Ctrl+C,
; and Escape. The focus stays in the address bar. Firefox cuts a long title
; in the window title, so the full title comes from the Firefox history.
;
; markdown mode copies the Markdown link. html mode copies the HTML link
; with the Markdown link as plain text. On error, shows a tooltip and does
; not change the clipboard.
PageLinkHotkey(mode) {
    try {
        hwnd := WinExist("A")
        exe := hwnd ? WinGetProcessName(hwnd) : ""
        browser := PageBrowser(exe)
        if browser = ""
            throw Error("The active window is not Firefox, Chrome, or Edge: " (exe != "" ? exe : "no window"))
        title := PageTitle(WinGetTitle(hwnd), browser)
    } catch Error as e {
        ShowTip("Error: " e.Message)
        return
    }
    saved := ClipboardAll()
    ; Win+L locks Windows, so wait until the Win key is up before Ctrl+L.
    KeyWait "LWin", "T2"
    KeyWait "RWin", "T2"
    A_Clipboard := ""
    Send "^l"
    Sleep 50
    Send "^c"
    url := ClipWait(1) ? Trim(A_Clipboard, " `t`r`n") : ""
    Send "{Escape}"
    try {
        if browser = "Firefox"
            title := FirefoxFullTitle(title, url)
        links := PageLinks(title, url)
        if mode = "html"
            CopyHtml(links.html, links.markdown)
        else
            A_Clipboard := links.markdown
        ShowTip("Copied " links.markdown "`nPress Ctrl+V.")
    } catch Error as e {
        A_Clipboard := saved
        ShowTip("Error: " e.Message)
    }
}

ShowTip(message) {
    ToolTip message
    SetTimer () => ToolTip(), -4000
}
