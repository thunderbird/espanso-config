import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "macos" / "shortcuts" / "page_link.js"
KB = "https://support.mozilla.org/kb/thunderbird-and-gmail"

pytestmark = pytest.mark.skipif(shutil.which("osascript") is None, reason="needs macOS osascript")


def links(title, url):
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", str(SCRIPT), "format", title, url],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.removesuffix("\n").split("\n")


def markdown(title, url):
    return links(title, url)[0]


def test_other_page_does_not_change():
    assert links("Example [draft]", "https://example.com/en-US/kb/x") == [
        "[Example [draft]](https://example.com/en-US/kb/x)",
        '<a href="https://example.com/en-US/kb/x">Example [draft]</a>',
    ]


@pytest.mark.parametrize(
    "url",
    [
        "https://support.mozilla.org/en-US/kb/thunderbird-and-gmail",
        "https://support.mozilla.org/de/kb/thunderbird-and-gmail",
        "https://support.mozilla.org/pt-BR/kb/thunderbird-and-gmail",
        "https://support.mozilla.org/zh-CN/kb/thunderbird-and-gmail",
        KB,
    ],
)
def test_sumo_kb_removes_locale(url):
    assert links("Thunderbird and Gmail | Thunderbird Help", url) == [
        f"[SUMO KB Article: Thunderbird and Gmail | TB]({KB})",
        f'<a href="{KB}">SUMO KB Article: Thunderbird and Gmail | TB</a>',
    ]


def test_sumo_kb_thunderbird_for_android():
    assert markdown("Set up email | Thunderbird for Android Help", KB) == (
        f"[SUMO KB Article: Set up email | TB for Android]({KB})"
    )


def test_sumo_kb_other_product_keeps_name():
    assert markdown("Clear the cache | Firefox Help", KB) == f"[SUMO KB Article: Clear the cache | Firefox]({KB})"


def test_sumo_kb_keeps_query_and_fragment():
    url = "https://support.mozilla.org/en-US/kb/thunderbird-and-gmail?as=u#w_imap"
    assert markdown("Thunderbird and Gmail | Thunderbird Help", url) == (
        f"[SUMO KB Article: Thunderbird and Gmail | TB]({KB}?as=u#w_imap)"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://support.mozilla.org/en-US/questions/123",
        "https://support.mozilla.org/en-US/kbx/foo",
        "https://example.com/kb/foo",
    ],
)
def test_not_sumo_kb(url):
    assert markdown("Question | Thunderbird Help", url) == f"[Question | Thunderbird Help]({url})"
