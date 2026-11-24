; Turn a Notion page URL into a link with the page title and a short page
; ID. links.ahk includes this file with markup.ahk, and
; tests/test_notion_link_ahk.py tests it.
;
; Accepts a notion.so, notion.com, or notion.site page URL and a page ID
; (32 hex characters, with or without hyphens), and gives
; `[Notion 89abcdef: Page title](url)`. The link text shows only the last
; 8 characters of the page ID. The link target keeps the full ID, because
; Notion accepts only the full ID. The title comes from the words before
; the ID in the URL, because most Notion pages are private. Without these
; words, the link text is `Notion 89abcdef`. The rules are the same as in
; macos/shortcuts/notion_link.js.

#Requires AutoHotkey v2.0

; Returns {markdown, html}. Throws an Error if the text is not a Notion page.
NotionLinks(text) {
    page := ParseNotion(text)
    shortId := SubStr(page.id, -8)
    label := page.title != "" ? "Notion " shortId ": " page.title : "Notion " shortId
    return MakeLinks(label, page.url)
}

; Returns {id, title, url}. The title can be empty.
ParseNotion(text) {
    trimmed := Trim(text, " `t`r`n")
    if trimmed ~= "i)^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$" {
        id := StrLower(StrReplace(trimmed, "-"))
        return {id: id, title: "", url: "https://www.notion.so/" id}
    }
    if !RegExMatch(trimmed, "i)^https?://(?:(?:www\.|app\.)?notion\.(?:so|com)|[\w-]+\.notion\.site)/([^?#\s]*)(\?[^#\s]*)?(#\S*)?$", &m)
        throw NotNotion(text)
    path := m[1], query := m[2], fragment := m[3]
    ; A page that opens on top of a database has its ID in the p parameter.
    if RegExMatch(query, "i)[?&]p=([0-9a-f]{32})(?:&|$)", &peek) {
        id := StrLower(peek[1])
        return {id: id, title: "", url: "https://www.notion.so/" id}
    }
    ; The last path segment is "Page-title-<id>" or "<id>".
    segments := StrSplit(Trim(path, "/"), "/")
    if !RegExMatch(segments.Length ? segments[segments.Length] : "", "i)^(?:(.*)-)?([0-9a-f]{32})$", &segment)
        throw NotNotion(text)
    title := StrReplace(PercentDecode(segment[1]), "-", " ")
    title := Trim(RegExReplace(title, "(*UCP)\s+", " "))
    ; The query, for example ?pvs=4, only tells Notion where the link came from.
    base := SubStr(trimmed, 1, StrLen(trimmed) - StrLen(query) - StrLen(fragment))
    return {id: StrLower(segment[2]), title: title, url: base fragment}
}

NotNotion(text) {
    return Error('Select or copy a Notion page URL or ID. The text was: "' ShownText(text) '"')
}

; Decodes %XX escapes as UTF-8, as decodeURIComponent does. Returns the
; text as it is if an escape is not valid.
PercentDecode(text) {
    if !InStr(text, "%")
        return text
    bytes := Buffer(StrPut(text, "UTF-8"))
    n := 0
    i := 1
    while i <= StrLen(text) {
        c := SubStr(text, i, 1)
        if c == "%" {
            if !RegExMatch(text, "\G[0-9A-Fa-f]{2}", &hex, i + 1)
                return text  ; As decodeURIComponent, which fails here.
            NumPut("UChar", Integer("0x" hex[0]), bytes, n++)
            i += 3
        } else {
            ; Characters that are not escaped stay as they are.
            n += StrPut(c, bytes.Ptr + n, "UTF-8") - 1
            i++
        }
    }
    ; MB_ERR_INVALID_CHARS makes invalid UTF-8 fail.
    size := DllCall("MultiByteToWideChar", "UInt", 65001, "UInt", 8, "Ptr", bytes, "Int", n, "Ptr", 0, "Int", 0)
    if size = 0 && n > 0
        return text
    result := Buffer(size * 2 + 2, 0)
    DllCall("MultiByteToWideChar", "UInt", 65001, "UInt", 8, "Ptr", bytes, "Int", n, "Ptr", result, "Int", size)
    return StrGet(result, size, "UTF-16")
}
