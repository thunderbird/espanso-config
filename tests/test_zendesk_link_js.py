import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "macos" / "shortcuts" / "zendesk_link.js"
URL = "https://tbpro.zendesk.com/agent/tickets/"

pytestmark = pytest.mark.skipif(shutil.which("osascript") is None, reason="needs macOS osascript")


def markdown(text):
    # Only markdown mode, because html mode changes the clipboard.
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", str(SCRIPT), "markdown", text],
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
    assert markdown("blah") == 'Error: Select text that contains a ticket number. The selection was: "blah"'
