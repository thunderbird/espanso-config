#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyperclip>=1.9"]
# ///
"""Turn a GitHub issue URL in the clipboard into a Markdown link.

Reads the clipboard, fetches the issue title from the GitHub API, and
copies `[title](url)` back to the clipboard. Prints the link on success,
or a message on error. On error, the clipboard does not change.

Token lookup order: GITHUB_TOKEN, GH_TOKEN, then `gh auth token`.
"""

from __future__ import annotations

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
    return re.sub(r"([\\\[\]])", r"\\\1", title)


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


def make_link(clipboard_text: str, token: str | None) -> str:
    owner, repo, number = parse_issue_url(clipboard_text)
    issue = fetch_issue(owner, repo, number, token)
    title = issue.get("title")
    if not title:
        raise LinkError(f"GitHub API response for {owner}/{repo}#{number} has no title")
    url = issue.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"
    return f"[{escape_markdown_link_text(title)}]({url})"


def main() -> int:
    import pyperclip

    try:
        link = make_link(pyperclip.paste(), get_token())
        pyperclip.copy(link)
        # Espanso 2.2.1 crashes on an empty expansion, so always print something.
        print(link, end="")
    except (LinkError, pyperclip.PyperclipException) as e:
        # Espanso types stdout, so the user sees the error where they typed the trigger.
        print(f"gh-issue-link error: {e}", end="")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
