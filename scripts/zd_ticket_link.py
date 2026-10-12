#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyperclip>=1.9"]
# ///
"""Turn a Zendesk ticket URL in the clipboard into a Markdown or HTML link.

Reads the clipboard and prints `[Zendesk ticket #number](url)`. In
Markdown mode, the script also copies the link to the clipboard. With
--html, the script prints `<a href="url">Zendesk ticket #number</a>` and
does not change the clipboard, because espanso restores only plain text
after an HTML expansion. On error, the script prints a message and does
not change the clipboard.
"""

from __future__ import annotations

import argparse
import html
import re
import sys

ZENDESK_HOST = "tbpro.zendesk.com"

TICKET_URL_RE = re.compile(
    rf"^https?://{re.escape(ZENDESK_HOST)}/agent/tickets/(?P<number>\d+)(?:[/?#].*)?$"
)


class LinkError(Exception):
    pass


def parse_ticket_url(text: str) -> int:
    match = TICKET_URL_RE.match(text.strip())
    if not match:
        raise LinkError("clipboard does not contain a Zendesk ticket URL")
    return int(match["number"])


def make_link(clipboard_text: str, as_html: bool = False) -> str:
    number = parse_ticket_url(clipboard_text)
    url = f"https://{ZENDESK_HOST}/agent/tickets/{number}"
    text = f"Zendesk ticket #{number}"
    if as_html:
        return f'<a href="{html.escape(url)}">{html.escape(text)}</a>'
    return f"[{text}]({url})"


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
        message = f"zd-ticket-link error: {e}"
        print(html.escape(message) if args.html else message, end="")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
