; Clipboard functions for links.ahk.

#Requires AutoHotkey v2.0

; Copies html as "HTML Format" and text as plain text, so that Ctrl+V
; pastes a rich text link in apps that accept HTML and the text in others.
CopyHtml(html, text) {
    header := "Version:0.9`r`nStartHTML:{1:010}`r`nEndHTML:{2:010}`r`nStartFragment:{3:010}`r`nEndFragment:{4:010}`r`n"
    before := "<html><body>`r`n<!--StartFragment-->"
    after := "<!--EndFragment-->`r`n</body></html>"
    headerLength := Utf8Length(Format(header, 0, 0, 0, 0))
    startFragment := headerLength + Utf8Length(before)
    endFragment := startFragment + Utf8Length(html)
    endHtml := endFragment + Utf8Length(after)
    cfHtml := Format(header, headerLength, endHtml, startFragment, endFragment) before html after

    ; Another app can have the clipboard open for a short time.
    Loop 10 {
        if DllCall("OpenClipboard", "Ptr", A_ScriptHwnd)
            break
        if A_Index = 10
            throw Error("Could not open the clipboard.")
        Sleep 20
    }
    try {
        DllCall("EmptyClipboard")
        SetClipboardString(DllCall("RegisterClipboardFormat", "Str", "HTML Format", "UInt"), cfHtml, "UTF-8")
        SetClipboardString(13, text, "UTF-16")  ; CF_UNICODETEXT
    } finally {
        DllCall("CloseClipboard")
    }
}

Utf8Length(text) {
    return StrPut(text, "UTF-8") - 1
}

SetClipboardString(format, text, encoding) {
    size := StrPut(text, encoding) * (encoding = "UTF-16" ? 2 : 1)
    handle := DllCall("GlobalAlloc", "UInt", 0x42, "UPtr", size, "Ptr")  ; GMEM_MOVEABLE | GMEM_ZEROINIT
    StrPut(text, DllCall("GlobalLock", "Ptr", handle, "Ptr"), encoding)
    DllCall("GlobalUnlock", "Ptr", handle)
    if !DllCall("SetClipboardData", "UInt", format, "Ptr", handle, "Ptr") {
        DllCall("GlobalFree", "Ptr", handle)
        throw Error("Could not copy to the clipboard.")
    }
}
