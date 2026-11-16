import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "linux" / "autokey"))

import page_link  # noqa: E402
from page_link import browser_kind, chrome_titles, firefox_titles, page_links  # noqa: E402

KB = "https://support.mozilla.org/kb/thunderbird-and-gmail"


def links(title, url):
    result = page_links(title, url)
    return [result["markdown"], result["html"]]


def markdown(title, url):
    return page_links(title, url)["markdown"]


# The same cases as tests/test_page_link_js.py.


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


# Linux only.


def test_escapes_unpaired_brackets_backslash_and_url():
    assert links("a ] b [ c \\ <d>", "https://example.com/a b(c)") == [
        "[a \\] b \\[ c \\\\ <d>](https://example.com/a%20b%28c%29)",
        '<a href="https://example.com/a b(c)">a ] b [ c \\ &lt;d&gt;</a>',
    ]


def test_empty_title_uses_url():
    assert markdown("  ", "https://example.com/") == "[https://example.com/](https://example.com/)"


def test_no_url():
    with pytest.raises(ValueError):
        page_links("Title", "")


@pytest.mark.parametrize(
    ("wm_class", "kind"),
    [
        ("firefox_firefox", "firefox"),
        ("firefox", "firefox"),
        ("firefox-nightly", "firefox"),
        ("google-chrome", "chrome"),
        ("Google-chrome", "chrome"),
        ("chromium", "chrome"),
        ("org.gnome.TextEditor", None),
        ("", None),
    ],
)
def test_browser_kind(wm_class, kind):
    assert browser_kind(wm_class) == kind


@pytest.mark.parametrize(
    "window_title",
    [
        "Santiago! (film) - Wikipedia — Mozilla Firefox",
        "Santiago! (film) - Wikipedia — Mozilla Firefox Private Browsing",
        "Santiago! (film) - Wikipedia — Firefox Nightly",
        "Santiago! (film) - Wikipedia — Work",
    ],
)
def test_firefox_titles(window_title):
    titles = firefox_titles(window_title)
    assert titles[0] == window_title
    assert "Santiago! (film) - Wikipedia" in titles


def test_firefox_titles_profile_and_name():
    assert "Page" in firefox_titles("Page — Work — Mozilla Firefox")


@pytest.mark.parametrize(
    "window_title",
    ["Page - Site - Google Chrome", "Page - Site - Google Chrome - Work", "Page - Site - Chromium"],
)
def test_chrome_titles(window_title):
    assert chrome_titles(window_title) == [window_title, "Page - Site"]


def make_firefox_profile(root, name, rows, lock_pid=None):
    profile = root / name
    profile.mkdir(parents=True)
    con = sqlite3.connect(profile / "places.sqlite")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE moz_places (url TEXT, title TEXT, last_visit_date INTEGER)")
    con.executemany("INSERT INTO moz_places VALUES (?, ?, ?)", rows)
    con.commit()
    if lock_pid is not None:
        os.symlink(f"127.0.1.1:+{lock_pid}", profile / "lock")
    return profile, con


def test_firefox_history_most_recent_visit(tmp_path):
    _, con = make_firefox_profile(tmp_path, "a.default", [
        ("https://old.example/", "Page", 100),
        ("https://new.example/", "Page", 300),
        ("https://other.example/", "Other", 500),
        ("https://never.example/", "Page", None),
    ], lock_pid=os.getpid())
    # The connection stays open, so the new rows are only in the write-ahead log.
    assert page_link.firefox_history_page(["Page — Mozilla Firefox", "Page"], [tmp_path]) == (
        "Page", "https://new.example/"
    )
    con.close()


def test_firefox_history_skips_closed_profile(tmp_path):
    _, a = make_firefox_profile(tmp_path, "open", [("https://open.example/", "Page", 100)], lock_pid=os.getpid())
    _, b = make_firefox_profile(tmp_path, "closed", [("https://closed.example/", "Page", 900)])
    assert page_link.firefox_history_page(["Page"], [tmp_path]) == ("Page", "https://open.example/")
    a.close()
    b.close()


def test_firefox_history_all_profiles_if_none_open(tmp_path):
    _, con = make_firefox_profile(tmp_path, "closed", [("https://closed.example/", "Page", 900)], lock_pid=999999999)
    assert page_link.firefox_history_page(["Page"], [tmp_path]) == ("Page", "https://closed.example/")
    assert page_link.firefox_history_page(["Missing"], [tmp_path]) is None
    con.close()


def test_chrome_history(tmp_path):
    for profile, rows in [
        ("Default", [("https://a.example/", "Page", 100)]),
        ("Profile 1", [("https://b.example/", "Page", 200)]),
    ]:
        (tmp_path / profile).mkdir()
        con = sqlite3.connect(tmp_path / profile / "History")
        con.execute("CREATE TABLE urls (url TEXT, title TEXT, last_visit_time INTEGER)")
        con.executemany("INSERT INTO urls VALUES (?, ?, ?)", rows)
        con.commit()
        con.close()
    assert page_link.chrome_history_page(["Page - Google Chrome", "Page"], [tmp_path]) == (
        "Page", "https://b.example/"
    )


def test_page_from_window_not_a_browser():
    with pytest.raises(ValueError, match="not Firefox or Chrome"):
        page_link.page_from_window("org.gnome.TextEditor", "Notes")
