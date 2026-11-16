"""Turn a Zendesk ticket number into a link. links.py uses this file, and
tests/test_zendesk_link_linux.py tests it.

Uses the first number in the text and ignores the text before it. If text
follows the number, it goes in the link text: "12345 blah blah" gives
`[Zendesk ticket #12345: blah blah](https://tbpro.zendesk.com/agent/tickets/12345)`.
A ticket URL followed by text gives the same link. The rules are the same
as in macos/shortcuts/zendesk_link.js and windows/autohotkey/zendesk_link.ahk.
Does not call the Zendesk API.
"""

import re

from markup import escape_html, escape_markdown_link_text

TICKET_URL = "https://tbpro.zendesk.com/agent/tickets/"
NUMBER_RE = re.compile(r"[0-9]+")
# The rest of a ticket URL after the number, for example "/", "?foo=bar", or "#comment".
URL_REST_RE = re.compile(r"^[/?#]\S*")
# Separators between the number and the text, for example "12345: blah" or "12345 - blah".
SEPARATOR_RE = re.compile(r"^[\s:\-\u2013\u2014|]+")


def zendesk_links(text):
    """Return {"markdown": ..., "html": ...}. Raise ValueError if the text has no number."""
    match = NUMBER_RE.search(text)
    if not match:
        shown = text[:80] + "..." if len(text) > 80 else text
        raise ValueError(f'Select or copy text that contains a ticket number. The text was: "{shown}"')
    number = match.group()
    rest = text[match.end():]
    if text[:match.start()].endswith("/tickets/"):
        rest = URL_REST_RE.sub("", rest)
    title = " ".join(SEPARATOR_RE.sub("", rest).split())
    url = TICKET_URL + number
    label = f"Zendesk ticket #{number}: {title}" if title else f"Zendesk ticket #{number}"
    return {
        "markdown": f"[{escape_markdown_link_text(label)}]({url})",
        "html": f'<a href="{escape_html(url)}">{escape_html(label)}</a>',
    }
