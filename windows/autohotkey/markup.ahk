; Escaping for Markdown and HTML links. links.ahk and the *_link.ahk files
; use these functions. The rules are the same as in macos/shortcuts/*.js.

#Requires AutoHotkey v2.0

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

; A Markdown link target ends at a space or an unpaired parenthesis.
EscapeMarkdownUrl(url) {
    return StrReplace(StrReplace(StrReplace(url, " ", "%20"), "(", "%28"), ")", "%29")
}

EscapeHtml(text) {
    text := StrReplace(text, "&", "&amp;")
    text := StrReplace(text, "<", "&lt;")
    text := StrReplace(text, ">", "&gt;")
    return StrReplace(text, '"', "&quot;")
}

; Returns {markdown, html} for a link with the label as link text.
MakeLinks(label, url) {
    return {
        markdown: "[" EscapeMarkdownLinkText(label) "](" EscapeMarkdownUrl(url) ")",
        html: '<a href="' EscapeHtml(url) '">' EscapeHtml(label) "</a>",
    }
}

; Shortens text for an error message.
ShownText(text) {
    return StrLen(text) > 80 ? SubStr(text, 1, 80) "..." : text
}
