import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "macos" / "shortcuts" / "zendesk_link.js"
URL = "https://tbpro.zendesk.com/agent/tickets/"

pytestmark = pytest.mark.skipif(shutil.which("osascript") is None, reason="needs macOS osascript")


def markdown(text):
    return run_script("markdown", text)


def run_script(mode, text):
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", str(SCRIPT), mode, text],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.removesuffix("\n")


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
        "12345\n  blah\tblah ",
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


def test_no_number():
    assert markdown("blah") == 'Error: Select or copy text that contains a ticket number. The text was: "blah"'


@pytest.fixture
def clipboard():
    saved = subprocess.run(["pbpaste"], capture_output=True, check=True).stdout
    yield lambda text: subprocess.run(["pbcopy"], input=text.encode(), check=True)
    subprocess.run(["pbcopy"], input=saved, check=True)


def paste():
    return subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout


def html_on_clipboard():
    return subprocess.run(
        ["osascript", "-l", "JavaScript", "-e",
         'ObjC.import("AppKit"); $.NSPasteboard.generalPasteboard.stringForType($("public.html")).js'],
        capture_output=True, text=True, check=True,
    ).stdout.removesuffix("\n")


@pytest.mark.parametrize("selection", ["", " \n"])
def test_empty_selection_uses_clipboard(clipboard, selection):
    clipboard("12345 blah blah")
    link = f"[Zendesk ticket #12345: blah blah]({URL}12345)"
    assert markdown(selection) == link
    assert paste() == link


def test_empty_selection_html_uses_clipboard(clipboard):
    clipboard("12345 blah blah")
    assert run_script("html", "") == f"[Zendesk ticket #12345: blah blah]({URL}12345)"
    assert html_on_clipboard() == f'<a href="{URL}12345">Zendesk ticket #12345: blah blah</a>'


def test_selection_does_not_change_clipboard_in_markdown_mode(clipboard):
    clipboard("keep")
    markdown("12345")
    assert paste() == "keep"


def test_empty_selection_and_clipboard_without_number(clipboard):
    clipboard("blah")
    assert markdown("") == 'Error: Select or copy text that contains a ticket number. The text was: "blah"'
    assert paste() == "blah"
