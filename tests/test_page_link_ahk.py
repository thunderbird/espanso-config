import pytest

from ahk_run import call_links, needs_autohotkey, run_ahk

pytestmark = needs_autohotkey

KB = "https://support.mozilla.org/kb/thunderbird-and-gmail"


def links(title, url):
    return call_links("PageLinks(A_Args[1], A_Args[2])", title, url).split("\n")


def markdown(title, url):
    return links(title, url)[0]


def page_title(window_title, exe):
    return run_ahk('FileAppend(PageTitle(A_Args[1], PageBrowser(A_Args[2])), "*", "UTF-8-RAW")', window_title, exe)


@pytest.mark.parametrize(
    "window_title, exe",
    [
        ("Example — Mozilla Firefox", "firefox.exe"),
        ("Example — Mozilla Firefox Private Browsing", "firefox.exe"),
        ("Example — Mozilla Firefox — Work", "firefox.exe"),
        ("Example — Firefox Developer Edition", "FIREFOX.EXE"),
        ("Example - Google Chrome", "chrome.exe"),
        ("Example - Google Chrome - Work", "chrome.exe"),
        ("Example - Microsoft​ Edge", "msedge.exe"),
        ("Example - Personal - Microsoft​ Edge", "msedge.exe"),
        ("Example and 3 more pages - Work - Microsoft​ Edge", "msedge.exe"),
        ("Example and 1 more page - Microsoft Edge", "msedge.exe"),
        ("Example - InPrivate - Microsoft​ Edge", "msedge.exe"),
    ],
)
def test_removes_browser_name(window_title, exe):
    assert page_title(window_title, exe) == "Example"


def test_keeps_dashes_in_title():
    assert page_title("A - B — C — Mozilla Firefox", "firefox.exe") == "A - B — C"
    assert page_title("A - B - Google Chrome", "chrome.exe") == "A - B"


def test_other_program():
    assert page_title("Example - Notepad", "notepad.exe") == "Example - Notepad"


def test_other_page_does_not_change():
    assert links("Example [draft]", "https://example.com/en-US/kb/x (1)") == [
        "[Example [draft]](https://example.com/en-US/kb/x%20%281%29)",
        '<a href="https://example.com/en-US/kb/x (1)">Example [draft]</a>',
    ]


def test_empty_title_uses_url():
    assert markdown("", "https://example.com/") == "[https://example.com/](https://example.com/)"


@pytest.mark.parametrize("url", ["", "example.com", "some selected text"])
def test_no_url(url):
    assert markdown("Example", url) == f'Error: The address bar has no URL: "{url}"'


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
    "a kludge. And it 100% doesn't work if you try it with the hexagonal adapter. 😀 café"
)
LONG_URL = "https://example.com/long"


def make_profile(profiles, name, places):
    """Make a Firefox profile with a test history in the write-ahead log.

    Close the returned connection after the test. Closing removes the
    write-ahead log, as when Firefox closes the profile.
    """
    import sqlite3

    profile = profiles / name
    profile.mkdir()
    db = sqlite3.connect(profile / "places.sqlite")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA wal_autocheckpoint=0")
    db.execute("CREATE TABLE moz_places (url TEXT, title TEXT, last_visit_date INTEGER)")
    db.executemany("INSERT INTO moz_places VALUES (?, ?, ?)", places)
    db.commit()
    return db


def full_title(title, url, profiles):
    return run_ahk('FileAppend(FirefoxFullTitle(A_Args[1], A_Args[2], A_Args[3]), "*", "UTF-8-RAW")', title, url, str(profiles))


@pytest.mark.parametrize("cut", [250, 256])
def test_firefox_long_title_from_history(tmp_path, cut):
    db = make_profile(tmp_path, "a.default", [(LONG_URL, LONG_TITLE, 10), ("https://x", "Short", 20)])
    try:
        assert full_title(LONG_TITLE[:cut], LONG_URL, tmp_path) == LONG_TITLE
    finally:
        db.close()


def test_firefox_long_title_prefers_url_then_most_recent(tmp_path):
    other = LONG_TITLE + " (other)"
    db = make_profile(tmp_path, "a.default", [
        (LONG_URL, LONG_TITLE, 10), ("https://example.com/other", other, 30), ("https://example.com/older", other + "!", 20),
    ])
    try:
        assert full_title(LONG_TITLE[:256], LONG_URL, tmp_path) == LONG_TITLE
        assert full_title(LONG_TITLE[:256], "https://example.com/new", tmp_path) == other
    finally:
        db.close()


def test_firefox_long_title_uses_open_profile(tmp_path):
    closed = make_profile(tmp_path, "closed", [(LONG_URL, LONG_TITLE + " closed", 99)])
    closed.close()
    db = make_profile(tmp_path, "open", [(LONG_URL, LONG_TITLE + " open", 1)])
    try:
        assert full_title(LONG_TITLE[:256], LONG_URL, tmp_path) == LONG_TITLE + " open"
    finally:
        db.close()


def test_firefox_long_title_not_in_history(tmp_path):
    db = make_profile(tmp_path, "a.default", [("https://x", "Short", 20)])
    try:
        assert full_title(LONG_TITLE[:256], LONG_URL, tmp_path) == LONG_TITLE[:256]
    finally:
        db.close()


def test_firefox_short_title_needs_no_history(tmp_path):
    assert full_title("Short", LONG_URL, tmp_path / "missing") == "Short"
