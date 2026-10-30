; Turn a Zendesk ticket number into a link. links.ahk includes this file,
; and tests/test_zendesk_link_ahk.py tests it.
;
; Uses the first number in the text and ignores the text before it. If text
; follows the number, it goes in the link text: "12345 blah blah" gives
; `[Zendesk ticket #12345: blah blah](https://tbpro.zendesk.com/agent/tickets/12345)`.
; A ticket URL followed by text gives the same link. The rules are the same
; as in macos/shortcuts/zendesk_link.js. Does not call the Zendesk API.

#Requires AutoHotkey v2.0

; Returns {markdown, html}. Throws an Error if the text has no number.
ZendeskLinks(text) {
    if !RegExMatch(text, "\d+", &match) {
        shown := StrLen(text) > 80 ? SubStr(text, 1, 80) "..." : text
        throw Error('Select or copy text that contains a ticket number. The text was: "' shown '"')
    }
    number := match[0]
    rest := SubStr(text, match.Pos + match.Len)
    ; The rest of a ticket URL after the number, for example "/", "?foo=bar", or "#comment".
    if SubStr(text, 1, match.Pos - 1) ~= "/tickets/$"
        rest := RegExReplace(rest, "^[/?#]\S*")
    ; Separators between the number and the text, for example "12345: blah" or "12345 - blah".
    title := RegExReplace(rest, "(*UCP)^[\s:\-\x{2013}\x{2014}|]+")
    title := Trim(RegExReplace(title, "(*UCP)\s+", " "))
    url := "https://tbpro.zendesk.com/agent/tickets/" number
    label := title != "" ? "Zendesk ticket #" number ": " title : "Zendesk ticket #" number
    return {
        markdown: "[" EscapeMarkdownLinkText(label) "](" url ")",
        html: '<a href="' EscapeHtml(url) '">' EscapeHtml(label) "</a>",
    }
}

; Paired brackets are valid in Markdown link text, so escape only
; backslashes and brackets without a partner.
EscapeMarkdownLinkText(title) {
    chars := StrSplit(title)
    openBrackets := []
    for i, c in chars {
        if c == "\"
            chars[i] := "\\"
        else if c == "["
            openBrackets.Push(i)
        else if c == "]" {
            if openBrackets.Length
                openBrackets.Pop()
            else
                chars[i] := "\]"
        }
    }
    for i in openBrackets
        chars[i] := "\["
    result := ""
    for c in chars
        result .= c
    return result
}

EscapeHtml(text) {
    text := StrReplace(text, "&", "&amp;")
    text := StrReplace(text, "<", "&lt;")
    text := StrReplace(text, ">", "&gt;")
    return StrReplace(text, '"', "&quot;")
}
