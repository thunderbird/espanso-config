"""Make a link to the current web page, with the page title as link text.
links.py uses this file, and tests/test_page_link_linux.py tests it.

AutoKey gives the class and the title of the active window, but not the
URL. The browser adds its name to the window title, for example
"Title — Mozilla Firefox", so page_from_window removes it and finds the
URL of the most recent visit with this title in the browser history. It
needs no keystrokes, so the focus and the clipboard do not change. A
private window has no history, so it gives an error.

The link text rules are the same as in macos/shortcuts/page_link.js: escape
only backslashes and unpaired brackets, and format a Mozilla Support
(SUMO) knowledge base article as "SUMO KB Article: ...".
"""

import glob
import os
import re
import shutil
import sqlite3
import tempfile

from markup import escape_html, escape_markdown_link_text

HOME = os.path.expanduser("~")
# The snap, the newer XDG folder, and the old folder.
FIREFOX_DIRS = [
    os.path.join(HOME, "snap/firefox/common/.mozilla/firefox"),
    os.path.join(HOME, ".config/mozilla/firefox"),
    os.path.join(HOME, ".mozilla/firefox"),
]
CHROME_DIRS = [
    os.path.join(HOME, ".config/google-chrome"),
    os.path.join(HOME, ".config/chromium"),
    os.path.join(HOME, "snap/chromium/common/chromium"),
]

# Firefox adds the browser name or the profile name to the window title,
# for example "Title — Mozilla Firefox" or "Title — Work".
FIREFOX_SUFFIX_RE = re.compile(
    r"\s+[—–-]\s+(?:Mozilla Firefox|Firefox(?: Developer Edition| Nightly)?)(?: Private Browsing)?$"
)
PROFILE_SUFFIX_RE = re.compile(r"\s+—\s+[^—]*$")
# Chrome adds its name, and the profile name if there is more than one,
# for example "Title - Google Chrome" or "Title - Google Chrome - Work".
CHROME_SUFFIX_RE = re.compile(r"\s+-\s+(?:Google Chrome|Chromium)(?:\s+-\s+.*)?$")

# Matches a SUMO knowledge base URL. Group 2 is the locale path segment,
# for example "/en-US", and is None if the URL has no locale.
SUMO_KB_RE = re.compile(r"^(https?://support\.mozilla\.org)(/[a-z]{2,3}(?:-[a-z0-9]+)*)?(/kb(?:[/?#]|$))", re.I)
URL_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def browser_kind(wm_class):
    """Return "firefox", "chrome", or None for the window class."""
    name = (wm_class or "").lower()
    if "firefox" in name:
        return "firefox"
    if "chrome" in name or "chromium" in name:
        return "chrome"
    return None


def firefox_titles(window_title):
    """Return the window title and the titles without the suffixes."""
    titles = [window_title]
    without_name = FIREFOX_SUFFIX_RE.sub("", window_title)
    for title in (without_name, PROFILE_SUFFIX_RE.sub("", window_title), PROFILE_SUFFIX_RE.sub("", without_name)):
        if title and title not in titles:
            titles.append(title)
    return titles


def chrome_titles(window_title):
    titles = [window_title]
    title = CHROME_SUFFIX_RE.sub("", window_title)
    if title and title not in titles:
        titles.append(title)
    return titles


def sumo_kb_page(title, url):
    """Change the title and the URL of a SUMO knowledge base article.

    " Help" goes away from the end of the title, "Thunderbird" in the
    product name after the last " | " becomes "TB", and the URL loses its
    locale, so that SUMO shows the reader's language. Other pages do not
    change.
    """
    match = SUMO_KB_RE.match(url)
    if not match:
        return title, url
    url = match.group(1) + url[match.end(1) + len(match.group(2) or ""):]
    title = title.removesuffix(" Help")
    bar = title.rfind(" | ")
    if bar >= 0:
        title = title[:bar + 3] + re.sub(r"\bThunderbird\b", "TB", title[bar + 3:], count=1)
    return f"SUMO KB Article: {title}", url


def escape_markdown_url(url):
    """A Markdown link target ends at a space or an unpaired parenthesis."""
    return url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def page_links(title, url):
    """Return {"markdown": ..., "html": ...}. Raise ValueError if there is no URL."""
    if not URL_SCHEME_RE.match(url):
        raise ValueError(f'The page has no URL: "{url}"')
    title, url = sumo_kb_page(title.strip() or url, url)
    return {
        "markdown": f"[{escape_markdown_link_text(title)}]({escape_markdown_url(url)})",
        "html": f'<a href="{escape_html(url)}">{escape_html(title)}</a>',
    }


def query_copy(files, sql, params):
    """Copy the database files, because the browser locks them, and run the query.

    files[0] is the database. The others, for example the write-ahead log
    with the recent visits, must be next to it. Return the rows, or [] if
    the database cannot be read.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "history.sqlite")
        try:
            shutil.copyfile(files[0], db)
            for f in files[1:]:
                if os.path.exists(f):
                    shutil.copyfile(f, db + f[len(files[0]):])
            con = sqlite3.connect(f"file:{db}", uri=True)
            try:
                return con.execute(sql, params).fetchall()
            finally:
                con.close()
        except (OSError, sqlite3.Error):
            return []


def firefox_profile_is_open(profile):
    """Firefox on Linux links "lock" to "<host>:+<pid>" while the profile is open."""
    try:
        target = os.readlink(os.path.join(profile, "lock"))
    except OSError:
        return False
    pid = target.rpartition("+")[2]
    return pid.isdigit() and os.path.exists(f"/proc/{pid}")


def firefox_profiles(dirs=FIREFOX_DIRS):
    """Return the open profiles, or all profiles if none is open."""
    profiles = [os.path.dirname(p) for d in dirs for p in glob.glob(os.path.join(glob.escape(d), "*", "places.sqlite"))]
    return [p for p in profiles if firefox_profile_is_open(p)] or profiles


def firefox_history_page(titles, dirs=FIREFOX_DIRS):
    """Return (title, url) of the most recent visit with one of the titles, or None."""
    marks = ", ".join("?" * len(titles))
    sql = (
        f"SELECT last_visit_date, title, url FROM moz_places WHERE title IN ({marks}) "
        "AND last_visit_date IS NOT NULL ORDER BY last_visit_date DESC LIMIT 1"
    )
    rows = []
    for profile in firefox_profiles(dirs):
        db = os.path.join(profile, "places.sqlite")
        rows += query_copy([db, db + "-wal"], sql, titles)
    if not rows:
        return None
    _, title, url = max(rows)
    return title, url


def chrome_history_page(titles, dirs=CHROME_DIRS):
    """Return (title, url) of the most recent visit with one of the titles, or None.

    Chrome writes the history late, so the newest visit can be missing.
    """
    marks = ", ".join("?" * len(titles))
    sql = (
        f"SELECT last_visit_time, title, url FROM urls WHERE title IN ({marks}) "
        "ORDER BY last_visit_time DESC LIMIT 1"
    )
    rows = []
    for d in dirs:
        for db in glob.glob(os.path.join(glob.escape(d), "*", "History")):
            # A rollback journal has only old pages, so do not copy it.
            rows += query_copy([db, db + "-wal"], sql, titles)
    if not rows:
        return None
    _, title, url = max(rows)
    return title, url


def page_from_window(wm_class, window_title):
    """Return (title, url) of the page in the active window. Raise ValueError if not found."""
    kind = browser_kind(wm_class)
    if kind is None:
        raise ValueError(f"The active window is not Firefox or Chrome: {wm_class}")
    if not window_title:
        raise ValueError("The browser window has no title.")
    if kind == "firefox":
        titles = firefox_titles(window_title)
        page = firefox_history_page(titles)
        name = "Firefox"
    else:
        titles = chrome_titles(window_title)
        page = chrome_history_page(titles)
        name = "Chrome"
    if page is None:
        raise ValueError(f'The {name} history has no page with the title "{titles[-1]}". A private window has no history.')
    return page
