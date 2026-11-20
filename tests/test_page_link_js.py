import shutil
import sqlite3
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


LONG_TITLE = (
    "Quixotic Quest Part 2 The PlumbShop Delta Handle Kit from Canadian Tire didn't work well "
    "(you have to move it with force with very subtle movements) because it has a round hole "
    "which doesn't connect snuggly with our shower's diamond shaped broach. It works but it's "
    "a kludge. And it 100% doesn't work if you try it with the hexagonal adapter."
)
LONG_URL = "https://example.com/long"


def firefox_history_title(window_title, places):
    """Run the Firefox query for a window title on a test history."""
    sql = subprocess.run(
        ["osascript", "-l", "JavaScript", str(SCRIPT), "firefox-sql", window_title],
        capture_output=True, text=True, check=True,
    ).stdout.removesuffix("\n")
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE moz_places (url TEXT, title TEXT, last_visit_date INTEGER)")
    db.executemany("INSERT INTO moz_places VALUES (?, ?, ?)", places)
    return db.execute(sql).fetchone()


@pytest.mark.parametrize("suffix", ["", " — Mozilla Firefox", " — 2026-06-29"])
def test_firefox_long_title_matches_start(suffix):
    window_title = LONG_TITLE[:256].rstrip() + suffix
    places = [(LONG_URL, LONG_TITLE, 2), ("https://example.com/short", "Short", 3)]
    assert firefox_history_title(window_title, places) == (2, LONG_URL, LONG_TITLE)


def test_firefox_long_title_uses_most_recent_visit():
    window_title = LONG_TITLE[:256] + " — 2026-06-29"
    places = [(LONG_URL, LONG_TITLE, 2), ("https://example.com/new", LONG_TITLE[:256] + " v2", 5)]
    assert firefox_history_title(window_title, places)[1] == "https://example.com/new"


def test_firefox_short_title_needs_exact_match():
    places = [("https://example.com/a", "Short title and more", 2), ("https://example.com/b", "Short title", 1)]
    assert firefox_history_title("Short title — Mozilla Firefox", places)[1] == "https://example.com/b"
