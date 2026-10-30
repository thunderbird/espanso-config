import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AHK_DIR = Path(__file__).resolve().parent.parent / "windows" / "autohotkey"
URL = "https://tbpro.zendesk.com/agent/tickets/"


def find_autohotkey():
    for path in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "AutoHotkey" / "v2" / "AutoHotkey64.exe",
        Path(os.environ.get("ProgramFiles", "")) / "AutoHotkey" / "v2" / "AutoHotkey64.exe",
    ]:
        if path.is_file():
            return str(path)
    return shutil.which("AutoHotkey64.exe")


AUTOHOTKEY = find_autohotkey() if sys.platform == "win32" else None

pytestmark = pytest.mark.skipif(AUTOHOTKEY is None, reason="needs AutoHotkey v2 on Windows")


def run_ahk(code, *args):
    """Run AutoHotkey code that can use the functions in the windows/autohotkey files."""
    script = f"#Include {AHK_DIR / 'zendesk_link.ahk'}\n#Include {AHK_DIR / 'clipboard.ahk'}\n{code}\n"
    result = subprocess.run(
        [AUTOHOTKEY, "/ErrorStdOut=UTF-8", "*", *args],
        input=script.encode("utf-8"), capture_output=True, check=True,
    )
    assert result.stderr == b""
    return result.stdout.decode("utf-8")


def links(text):
    return run_ahk(
        'try {\n'
        '    l := ZendeskLinks(A_Args[1])\n'
        '    FileAppend(l.markdown "`n" l.html, "*", "UTF-8-RAW")\n'
        '} catch Error as e\n'
        '    FileAppend("Error: " e.Message, "*", "UTF-8-RAW")',
        text,
    )


def markdown(text):
    return links(text).split("\n")[0]


@pytest.mark.parametrize(
    "text",
    ["12345", " 12345\n", "#12345", "Zendesk ticket #12345", f"{URL}12345", f"{URL}12345/", f"{URL}12345?foo=bar"],
)
def test_number_only(text):
    assert markdown(text) == f"[Zendesk ticket #12345]({URL}12345)"


@pytest.mark.parametrize(
    "text",
    [
        "12345 blah blah",
        "12345: blah blah",
        "12345 - blah blah",
        "12345 – blah blah",
        "12345\r\n  blah\tblah ",
        "ticket 12345 blah blah",
        f"{URL}12345 blah blah",
        f"{URL}12345#comment blah blah",
    ],
)
def test_text_after_number(text):
    assert markdown(text) == f"[Zendesk ticket #12345: blah blah]({URL}12345)"


def test_escapes_unpaired_brackets():
    assert markdown("12345 [Thundermail] a]b\\c") == (
        f"[Zendesk ticket #12345: [Thundermail] a\\]b\\\\c]({URL}12345)"
    )


def test_text_with_more_numbers_keeps_them():
    assert markdown("12345 crash in 128.0") == f"[Zendesk ticket #12345: crash in 128.0]({URL}12345)"


def test_non_ascii_text():
    assert markdown("12345 café → ok") == f"[Zendesk ticket #12345: café → ok]({URL}12345)"


def test_html():
    assert links('12345 a < b & "c"').split("\n")[1] == (
        f'<a href="{URL}12345">Zendesk ticket #12345: a &lt; b &amp; &quot;c&quot;</a>'
    )


def test_no_number():
    assert markdown("blah") == 'Error: Select or copy text that contains a ticket number. The text was: "blah"'


def test_no_number_shortens_long_text():
    assert markdown("x" * 100) == (
        f'Error: Select or copy text that contains a ticket number. The text was: "{"x" * 80}..."'
    )


def read_clipboard_format(name):
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.GetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
    fmt = 13 if name == "CF_UNICODETEXT" else user32.RegisterClipboardFormatW(name)
    assert user32.OpenClipboard(None)
    try:
        handle = user32.GetClipboardData(fmt)
        assert handle
        data = ctypes.string_at(kernel32.GlobalLock(handle), kernel32.GlobalSize(handle))
        kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
    if name == "CF_UNICODETEXT":
        return data.decode("utf-16-le").split("\0")[0]
    return data.split(b"\0")[0]


@pytest.fixture
def saved_clipboard():
    import pyperclip

    saved = pyperclip.paste()
    yield
    pyperclip.copy(saved)


def test_copy_html(saved_clipboard):
    html = f'<a href="{URL}12345">Zendesk ticket #12345: café</a>'
    text = f"[Zendesk ticket #12345: café]({URL}12345)"
    run_ahk("CopyHtml(A_Args[1], A_Args[2])", html, text)
    assert read_clipboard_format("CF_UNICODETEXT") == text
    data = read_clipboard_format("HTML Format")
    header = dict(
        line.split(b":", 1) for line in data.split(b"\r\n") if line.split(b":", 1)[0] in
        (b"StartHTML", b"EndHTML", b"StartFragment", b"EndFragment")
    )
    offsets = {k.decode(): int(v) for k, v in header.items()}
    assert data[offsets["StartFragment"]:offsets["EndFragment"]].decode("utf-8") == html
    assert data[offsets["StartHTML"]:].startswith(b"<html>")
    assert offsets["EndHTML"] == len(data)
