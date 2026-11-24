; HTTP and JSON for the GitHub and Bugzilla hotkeys. AutoHotkey v2 has no
; JSON parser, so this file has a small one. tests/test_web_ahk.py tests it.

#Requires AutoHotkey v2.0

; Sends a GET request and returns {status, body}. Reads the body as UTF-8.
; Throws an Error if the request fails, for example without a network.
HttpGet(url, headers := Map()) {
    static timeoutMs := 10000
    request := ComObject("WinHttp.WinHttpRequest.5.1")
    try {
        request.Open("GET", url, false)
        request.SetTimeouts(timeoutMs, timeoutMs, timeoutMs, timeoutMs)
        for name, value in headers
            request.SetRequestHeader(name, value)
        request.Send()
    } catch Error as err {
        throw Error("The request to " RegExReplace(url, "^https://([^/]+).*", "$1") " failed: " Trim(err.Message, " `r`n"))
    }
    return {status: request.Status, body: Utf8FromSafeArray(request.ResponseBody)}
}

; ResponseText guesses the encoding, so decode the bytes as UTF-8.
Utf8FromSafeArray(bytes) {
    length := bytes.MaxIndex() + 1
    if length <= 0
        return ""
    data := NumGet(ComObjValue(bytes), 8 + A_PtrSize, "Ptr")  ; SAFEARRAY.pvData
    return StrGet(data, length, "UTF-8")
}

; Parses JSON text. Objects become Maps, arrays become Arrays, true and
; false become 1 and 0, and null becomes "". Throws an Error for invalid JSON.
JsonParse(text) {
    pos := 1
    value := JsonValue(text, &pos)
    JsonSkipSpace(text, &pos)
    if pos <= StrLen(text)
        throw Error("Invalid JSON at position " pos)
    return value
}

JsonSkipSpace(text, &pos) {
    if RegExMatch(text, "\G[ \t\r\n]+", &m, pos)
        pos += m.Len
}

JsonValue(text, &pos) {
    JsonSkipSpace(text, &pos)
    c := SubStr(text, pos, 1)
    if c == "{" {
        result := Map()
        pos++
        JsonSkipSpace(text, &pos)
        if SubStr(text, pos, 1) == "}" {
            pos++
            return result
        }
        Loop {
            JsonSkipSpace(text, &pos)
            if SubStr(text, pos, 1) != '"'
                throw Error("Invalid JSON at position " pos)
            key := JsonString(text, &pos)
            JsonSkipSpace(text, &pos)
            if SubStr(text, pos, 1) != ":"
                throw Error("Invalid JSON at position " pos)
            pos++
            result[key] := JsonValue(text, &pos)
            JsonSkipSpace(text, &pos)
            c := SubStr(text, pos++, 1)
            if c == "}"
                return result
            if c != ","
                throw Error("Invalid JSON at position " (pos - 1))
        }
    }
    if c == "[" {
        result := []
        pos++
        JsonSkipSpace(text, &pos)
        if SubStr(text, pos, 1) == "]" {
            pos++
            return result
        }
        Loop {
            result.Push(JsonValue(text, &pos))
            JsonSkipSpace(text, &pos)
            c := SubStr(text, pos++, 1)
            if c == "]"
                return result
            if c != ","
                throw Error("Invalid JSON at position " (pos - 1))
        }
    }
    if c == '"'
        return JsonString(text, &pos)
    if RegExMatch(text, "\G-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", &m, pos) {
        pos += m.Len
        return Number(m[0])
    }
    for word, value in Map("true", 1, "false", 0, "null", "") {
        if SubStr(text, pos, StrLen(word)) == word {
            pos += StrLen(word)
            return value
        }
    }
    throw Error("Invalid JSON at position " pos)
}

JsonString(text, &pos) {
    if !RegExMatch(text, '\G"((?:[^"\\\x00-\x1F]++|\\(?:["\\/bfnrt]|u[0-9A-Fa-f]{4}))*+)"', &m, pos)
        throw Error("Invalid JSON string at position " pos)
    pos += m.Len
    raw := m[1]
    if !InStr(raw, "\")
        return raw
    result := ""
    i := 1
    while RegExMatch(raw, "\\(?:u([0-9A-Fa-f]{4})|(.))", &esc, i) {
        result .= SubStr(raw, i, esc.Pos - i)
        if esc[1] != ""
            result .= Chr(Integer("0x" esc[1]))  ; A surrogate pair gives two UTF-16 units, as AutoHotkey strings use.
        else
            result .= Map("b", "`b", "f", "`f", "n", "`n", "r", "`r", "t", "`t")
                .Get(esc[2], esc[2])
        i := esc.Pos + esc.Len
    }
    return result SubStr(raw, i)
}
