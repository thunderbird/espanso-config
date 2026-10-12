#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyperclip>=1.9"]
# ///
"""Turn a GitHub issue URL in the clipboard into a Markdown or HTML link.

Reads the clipboard, fetches the issue title from the GitHub API, and
prints `[repo #number: title](url)`. In Markdown mode, the script also
copies the link to the clipboard. With --html, the script prints
`<a href="url">repo #number: title</a>` and does not change the
clipboard, because espanso restores only plain text after an HTML
expansion. On error, the script prints a message and does not change
the clipboard.

Token lookup order: GITHUB_TOKEN, GH_TOKEN, then `gh auth token`.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ISSUE_URL_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9._-]+)/issues/(?P<number>\d+)"
    r"(?:[/?#].*)?$"
)

API_TIMEOUT_SECONDS = 10


class LinkError(Exception):
    pass


def parse_issue_url(text: str) -> tuple[str, str, int]:
    match = ISSUE_URL_RE.match(text.strip())
    if not match:
        raise LinkError("clipboard does not contain a GitHub issue URL")
    return match["owner"], match["repo"], int(match["number"])


def escape_markdown_link_text(title: str) -> str:
    # Paired brackets are valid in Markdown link text, so escape only
    # backslashes and brackets without a partner.
    chars = list(title)
    open_brackets = []
    for i, c in enumerate(chars):
        if c == "\\":
            chars[i] = "\\\\"
        elif c == "[":
            open_brackets.append(i)
        elif c == "]":
            if open_brackets:
                open_brackets.pop()
            else:
                chars[i] = "\\]"
    for i in open_brackets:
        chars[i] = "\\["
    return "".join(chars)


def get_token() -> str | None:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if token := os.environ.get(name):
            return token
    gh = shutil.which("gh")
    if not gh:
        return None
    try:
        result = subprocess.run(
            [gh, "auth", "token"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def fetch_issue(owner: str, repo: str, number: int, token: str | None) -> dict:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{number}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "espanso-gh-issue-link",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise LinkError(f"GitHub API returned HTTP {e.code} for {owner}/{repo}#{number}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise LinkError(f"GitHub API request failed: {getattr(e, 'reason', e)}")
    except json.JSONDecodeError:
        raise LinkError("GitHub API returned invalid JSON")


def make_link(clipboard_text: str, token: str | None, as_html: bool = False) -> str:
    owner, repo, number = parse_issue_url(clipboard_text)
    issue = fetch_issue(owner, repo, number, token)
    title = issue.get("title")
    if not title:
        raise LinkError(f"GitHub API response for {owner}/{repo}#{number} has no title")
    url = issue.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"
    # A transferred issue has a new repo and number, so label it from html_url.
    try:
        _, repo, number = parse_issue_url(url)
    except LinkError:
        pass
    text = f"{repo} #{number}: {title}"
    if as_html:
        return f'<a href="{html.escape(url)}">{html.escape(text)}</a>'
    return f"[{escape_markdown_link_text(text)}]({url})"


def main() -> int:
    import pyperclip

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--html", action="store_true", help="print an HTML link")
    args = parser.parse_args()

    try:
        link = make_link(pyperclip.paste(), get_token(), as_html=args.html)
        if not args.html:
            pyperclip.copy(link)
        # Espanso 2.2.1 crashes on an empty expansion, so always print something.
        print(link, end="")
    except (LinkError, pyperclip.PyperclipException) as e:
        # Espanso types stdout, so the user sees the error where they typed the trigger.
        message = f"gh-issue-link error: {e}"
        print(html.escape(message) if args.html else message, end="")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
