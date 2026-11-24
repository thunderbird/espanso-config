import json

import pytest

from ahk_run import needs_autohotkey, run_ahk

pytestmark = needs_autohotkey

# Prints a parsed value as JSON again, so that Python can compare it.
DUMP = r"""
Dump(v) {
    if v is Map {
        s := ""
        for k, x in v
            s .= (s = "" ? "" : ",") Quote(k) ":" Dump(x)
        return "{" s "}"
    }
    if v is Array {
        s := ""
        for x in v
            s .= (s = "" ? "" : ",") Dump(x)
        return "[" s "]"
    }
    if v is Number
        return v
    return Quote(v)
}
Quote(s) {
    out := ""
    for c in StrSplit(s)
        out .= Ord(c) < 0x20 || c == '"' || c == "\" ? Format("\u{:04x}", Ord(c)) : c
    return '"' out '"'
}
try
    FileAppend(Dump(JsonParse(A_Args[1])), "*", "UTF-8-RAW")
catch Error as e
    FileAppend("Error: " e.Message, "*", "UTF-8-RAW")
"""


def parse(text):
    out = run_ahk(DUMP, text)
    return out if out.startswith("Error: ") else json.loads(out)


def test_github_like_object():
    data = {
        "title": 'Crash with "quotes" \\ and\nnewline',
        "html_url": "https://github.com/thunderbird/espanso-config/issues/29",
        "number": 29,
        "milestone": {"title": "other"},
        "labels": [{"name": "windows"}, {"name": "x"}],
        "empty": {},
        "none": [],
    }
    assert parse(json.dumps(data, indent=2)) == data


def test_unicode_escapes_and_raw_utf8():
    assert parse('{"a": "caf\\u00e9 \\ud83d\\ude00 →"}') == {"a": "café 😀 →"}


def test_literals_and_numbers():
    assert parse('[true, false, null, -1.5e2, 0]') == [1, 0, "", -150, 0]


@pytest.mark.parametrize("text", ['{"a": 1', '{"a" 1}', "[1,]", '"\x01"', "nope", '{"a": 1} x'])
def test_invalid(text):
    assert parse(text).startswith("Error: Invalid JSON")
