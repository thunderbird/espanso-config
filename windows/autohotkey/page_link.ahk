; Make a link to the current web page, with the page title as link text.
; links.ahk includes this file with markup.ahk, and
; tests/test_page_link_ahk.py tests it.
;
; links.ahk gets the title from the window title and the URL from the
; address bar. The browser adds its name to the window title, so
; PageTitle removes it. The link text rules are the same as in
; macos/shortcuts/page_link.js: escape only backslashes and unpaired
; brackets, and format a Mozilla Support (SUMO) knowledge base article as
; "SUMO KB Article: ...".

#Requires AutoHotkey v2.0

; Returns "Firefox", "Chrome", "Edge", or "" for the program file name.
PageBrowser(exe) {
    switch StrLower(exe) {
        case "firefox.exe": return "Firefox"
        case "chrome.exe": return "Chrome"
        case "msedge.exe": return "Edge"
    }
    return ""
}

; Removes the browser name and the profile name from the window title.
PageTitle(windowTitle, browser) {
    switch browser {
        case "Firefox":
            ; "Title — Mozilla Firefox", "Title — Mozilla Firefox Private Browsing",
            ; or with a profile, "Title — Mozilla Firefox — Work".
            re := "\s+[—–-]\s+(?:Mozilla Firefox|Firefox(?: Developer Edition| Nightly)?)(?: Private Browsing)?(?:\s+—\s+[^—]*)?$"
        case "Chrome":
            ; "Title - Google Chrome", or "Title - Google Chrome - Work".
            re := "\s+-\s+Google Chrome(?: (?:Beta|Dev|Canary))?(?:\s+-\s+.*)?$"
        case "Edge":
            ; "Title and 2 more pages - Work - Microsoft​ Edge". The name has a
            ; zero-width space, and the profile name is optional.
            re := "(?: and \d+ more pages?)?(?:\s+-\s+[^-]*)??\s+-\s+Microsoft\x{200B}? Edge(?: (?:Beta|Dev|Canary))?$"
        default:
            return windowTitle
    }
    return RegExReplace(windowTitle, re)
}

; Returns the full title of a long Firefox title, or the title if it is
; short or not in the history. Looks in the history of the open profiles
; for the most recent page whose title starts with the cut title, and
; prefers the page with the URL. Only an open profile has a write-ahead
; log that is not empty. If no profile is open, looks in all profiles.
FirefoxFullTitle(title, url, profilesDir := "") {
    ; Firefox cuts the page title in the window title to 256 characters
    ; (#56). A title without its suffix can also lose a space at the cut,
    ; so the limit is a little lower.
    static cutTitleLength := 250
    length := CodePointLength(title)
    if length < cutTitleLength
        return title
    if profilesDir = ""
        profilesDir := A_AppData "\Mozilla\Firefox\Profiles"
    open := [], all := []
    Loop Files profilesDir "\*", "D" {
        db := A_LoopFileFullPath "\places.sqlite"
        if !FileExist(db)
            continue
        all.Push(db)
        if FileExist(db "-wal") && FileGetSize(db "-wal")
            open.Push(db)
    }
    best := ""
    for db in open.Length ? open : all {
        try row := FirefoxHistoryTitle(db, title, length, url)
        catch
            continue
        if row != "" && (best = "" || row.score > best.score)
            best := row
    }
    return best != "" ? best.title : title
}

; AutoHotkey strings are UTF-16, but SQLite counts characters.
CodePointLength(text) {
    length := 0
    Loop Parse text {
        if (Ord(A_LoopField) & 0xFC00) != 0xDC00  ; Not the second half of a surrogate pair.
            length++
    }
    return length
}

; Firefox locks places.sqlite, so the query runs on a copy of it and its
; write-ahead log, which has the recent visits. winsqlite3.dll is part of
; Windows 10 and later. Returns {title, score} or "".
FirefoxHistoryTitle(db, title, length, url) {
    dir := A_Temp "\links-ahk-places-" DllCall("GetCurrentProcessId")
    DirCreate dir
    try {
        FileCopy db, dir "\p.sqlite", true
        if FileExist(db "-wal")
            FileCopy db "-wal", dir "\p.sqlite-wal", true
        return SqliteFirstRow(dir "\p.sqlite",
            "SELECT title, (url = ?3) * 1e18 + IFNULL(last_visit_date, 0) AS score FROM moz_places "
            "WHERE substr(title, 1, ?1) = ?2 ORDER BY score DESC LIMIT 1",
            [length, title, url])
    } finally {
        try DirDelete dir, true
    }
}

; Runs a query with Integer and String parameters and returns the first row
; as {title, score}, or "" if there is no row.
SqliteFirstRow(path, sql, params) {
    static dll := "winsqlite3.dll"
    if !DllCall("GetModuleHandle", "Str", dll, "Ptr")
        DllCall("LoadLibrary", "Str", dll, "Ptr")
    if DllCall(dll "\sqlite3_open16", "Str", path, "Ptr*", &handle := 0, "Int") {
        DllCall(dll "\sqlite3_close", "Ptr", handle)
        throw Error("Cannot open " path)
    }
    try {
        if DllCall(dll "\sqlite3_prepare16_v2", "Ptr", handle, "Str", sql, "Int", -1, "Ptr*", &stmt := 0, "Ptr", 0, "Int")
            throw Error(StrGet(DllCall(dll "\sqlite3_errmsg16", "Ptr", handle, "Ptr"), "UTF-16"))
        try {
            for i, value in params {
                if value is Integer
                    DllCall(dll "\sqlite3_bind_int64", "Ptr", stmt, "Int", i, "Int64", value)
                else
                    DllCall(dll "\sqlite3_bind_text16", "Ptr", stmt, "Int", i, "Str", value, "Int", -1, "Ptr", -1)  ; SQLITE_TRANSIENT
            }
            if DllCall(dll "\sqlite3_step", "Ptr", stmt, "Int") != 100  ; SQLITE_ROW
                return ""
            text := DllCall(dll "\sqlite3_column_text16", "Ptr", stmt, "Int", 0, "Ptr")
            return {
                title: text ? StrGet(text, "UTF-16") : "",
                score: DllCall(dll "\sqlite3_column_double", "Ptr", stmt, "Int", 1, "Double"),
            }
        } finally {
            DllCall(dll "\sqlite3_finalize", "Ptr", stmt)
        }
    } finally {
        DllCall(dll "\sqlite3_close", "Ptr", handle)
    }
}

; Changes the title and the URL of a SUMO knowledge base article: " Help"
; goes away from the end of the title, "Thunderbird" in the product name
; after the last " | " becomes "TB", and the URL loses its locale, so that
; SUMO shows the reader's language. Other pages do not change.
SumoKbPage(title, url) {
    if !RegExMatch(url, "i)^(https?://support\.mozilla\.org)(/[a-z]{2,3}(?:-[a-z0-9]+)*)?(/kb(?:[/?#]|$))", &m)
        return {title: title, url: url}
    url := m[1] SubStr(url, StrLen(m[1]) + StrLen(m[2]) + 1)
    title := RegExReplace(title, " Help$")
    bar := InStr(title, " | ", true, -1)
    if bar
        title := SubStr(title, 1, bar + 2) RegExReplace(SubStr(title, bar + 3), "\bThunderbird\b", "TB", , 1)
    return {title: "SUMO KB Article: " title, url: url}
}

; Returns {markdown, html}. Throws an Error if the URL has no scheme.
PageLinks(title, url) {
    if !(url ~= "i)^[a-z][a-z0-9+.-]*:")
        throw Error('The address bar has no URL: "' ShownText(url) '"')
    title := Trim(title, " `t`r`n")
    page := SumoKbPage(title != "" ? title : url, url)
    return MakeLinks(page.title, page.url)
}
