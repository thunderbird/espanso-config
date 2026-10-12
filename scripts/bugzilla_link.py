#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyperclip>=1.9"]
# ///
"""Turn a Mozilla Bugzilla bug URL in the clipboard into a Markdown or HTML link.

Reads the clipboard, accepts `https://bugzilla.mozilla.org/show_bug.cgi?id=N`
or `bugzil.la/N`, fetches the bug summary from the Bugzilla REST API, and
prints `[Bug N: summary](https://bugzilla.mozilla.org/show_bug.cgi?id=N)`.
In Markdown mode, the script also copies the link to the clipboard. With
--html, the script prints `<a href="url">Bug N: summary</a>` and does not
change the clipboard, because espanso restores only plain text after an
HTML expansion. On error, the script prints a message and does not change
the clipboard.

Public bugs do not need an API key.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request

LONG_URL_RE = re.compile(
    r"^https?://bugzilla\.mozilla\.org/show_bug\.cgi\?(?:[^#]*&)?id=(?P<number>\d+)"
    r"(?:[&#].*)?$"
)
SHORT_URL_RE = re.compile(r"^(?:https?://)?bugzil\.la/(?P<number>\d+)/?(?:[?#].*)?$")

API_TIMEOUT_SECONDS = 10


class LinkError(Exception):
    pass


def parse_bug_url(text: str) -> int:
    text = text.strip()
    match = LONG_URL_RE.match(text) or SHORT_URL_RE.match(text)
    if not match:
        raise LinkError("clipboard does not contain a Bugzilla bug URL")
    return int(match["number"])


def bug_url(number: int) -> str:
    return f"https://bugzilla.mozilla.org/show_bug.cgi?id={number}"


def escape_markdown_link_text(title: str) -> str:
    return re.sub(r"([\\\[\]])", r"\\\1", title)


def fetch_bug(number: int) -> dict:
    request = urllib.request.Request(
        f"https://bugzilla.mozilla.org/rest/bug/{number}?include_fields=id,summary",
        headers={"Accept": "application/json", "User-Agent": "espanso-bugzilla-link"},
    )
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            data = json.load(response)
    except urllib.error.HTTPError as e:
        # Bugzilla explains the error in the JSON body, for example "Bug 1 does not exist."
        try:
            detail = json.load(e).get("message")
        except (json.JSONDecodeError, AttributeError, OSError):
            detail = None
        message = f"Bugzilla API returned HTTP {e.code} for bug {number}"
        raise LinkError(f"{message}: {detail}" if detail else message)
    except (urllib.error.URLError, TimeoutError) as e:
        raise LinkError(f"Bugzilla API request failed: {getattr(e, 'reason', e)}")
    except json.JSONDecodeError:
        raise LinkError("Bugzilla API returned invalid JSON")
    bugs = data.get("bugs") if isinstance(data, dict) else None
    if not bugs:
        raise LinkError(f"Bugzilla API response for bug {number} has no bug")
    return bugs[0]


def make_link(clipboard_text: str, as_html: bool = False) -> str:
    number = parse_bug_url(clipboard_text)
    summary = fetch_bug(number).get("summary")
    if not summary:
        raise LinkError(f"Bugzilla API response for bug {number} has no summary")
    url = bug_url(number)
    text = f"Bug {number}: {summary}"
    if as_html:
        return f'<a href="{html.escape(url)}">{html.escape(text)}</a>'
    return f"[{escape_markdown_link_text(text)}]({url})"


def main() -> int:
    import pyperclip

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--html", action="store_true", help="print an HTML link")
    args = parser.parse_args()

    try:
        link = make_link(pyperclip.paste(), as_html=args.html)
        if not args.html:
            pyperclip.copy(link)
        # Espanso 2.2.1 crashes on an empty expansion, so always print something.
        print(link, end="")
    except (LinkError, pyperclip.PyperclipException) as e:
        # Espanso types stdout, so the user sees the error where they typed the trigger.
        message = f"bugzilla-link error: {e}"
        print(html.escape(message) if args.html else message, end="")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
