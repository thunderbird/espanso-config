; Turn a Mozilla Bugzilla bug into a link with the bug summary. links.ahk
; includes this file with markup.ahk and web.ahk, and
; tests/test_bugzilla_link_ahk.py tests it.
;
; Accepts `https://bugzilla.mozilla.org/show_bug.cgi?id=N`, `bugzil.la/N`,
; a bug number N, and `bug N`, and gives
; `[Bug N: summary](https://bugzilla.mozilla.org/show_bug.cgi?id=N)`.
; The rules are the same as in macos/shortcuts/bugzilla_link.js. Public
; bugs do not need an API key.

#Requires AutoHotkey v2.0

; Returns {markdown, html}. Throws an Error on failure.
BugzillaLinks(text) {
    bug := ParseBugzillaBug(text)
    return BugzillaLinksFromBug(bug, FetchBugzillaBug(bug))
}

; Returns the bug number. Throws an Error if the text is not a bug.
ParseBugzillaBug(text) {
    trimmed := Trim(text, " `t`r`n")
    ; Mozilla has only one Bugzilla, so a number alone is a bug.
    for re in [
        "^https?://bugzilla\.mozilla\.org/show_bug\.cgi\?(?:[^#]*&)?id=(\d+)(?:[&#].*)?$",
        "^(?:https?://)?bugzil\.la/(\d+)/?(?:[?#].*)?$",
        "i)^(?:bug\s+)?(\d+)$",
    ] {
        if RegExMatch(trimmed, re, &m)
            return m[1]
    }
    throw Error('Select or copy a Bugzilla bug URL or number. The text was: "' ShownText(text) '"')
}

; data is the JSON response as a Map.
BugzillaLinksFromBug(bug, data) {
    bugs := data is Map ? data.Get("bugs", "") : ""
    if !(bugs is Array) || !bugs.Length || !(bugs[1] is Map)
        throw Error("The Bugzilla API response for bug " bug " has no bug.")
    summary := bugs[1].Get("summary", "")
    if summary = ""
        throw Error("The Bugzilla API response for bug " bug " has no summary.")
    return MakeLinks("Bug " bug ": " summary, "https://bugzilla.mozilla.org/show_bug.cgi?id=" bug)
}

FetchBugzillaBug(bug) {
    response := HttpGet(
        "https://bugzilla.mozilla.org/rest/bug/" bug "?include_fields=id,summary",
        Map("Accept", "application/json", "User-Agent", "espanso-bugzilla-link"),
    )
    try
        data := JsonParse(response.body)
    catch
        data := ""
    if response.status != 200 {
        ; Bugzilla explains the error in the JSON body, for example "Bug 1 does not exist."
        message := "The Bugzilla API returned HTTP " response.status " for bug " bug "."
        if data is Map && data.Get("message", "") != ""
            message .= " " data["message"]
        throw Error(message)
    }
    if !(data is Map)
        throw Error("The Bugzilla API returned invalid JSON.")
    return data
}
