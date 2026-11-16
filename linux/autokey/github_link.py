"""Turn a GitHub issue URL into a link with the issue title. links.py uses
this file, and tests/test_github_link_linux.py tests it.

Gives `[repo #number: title](url)`, with the title from the GitHub API. The
rules are the same as in macos/shortcuts/github_link.js and
scripts/gh_issue_link.py. A token gives access to private repositories
and a higher rate limit. The script uses GITHUB_TOKEN, GH_TOKEN, or
`gh auth token`, in that order.
"""

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request

from markup import escape_html, escape_markdown_link_text

ISSUE_URL_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9._-]+)/issues/(?P<number>\d+)"
    r"(?:[/?#].*)?$"
)
API_TIMEOUT_SECONDS = 10
GH_PATHS = ["/usr/bin/gh", "/usr/local/bin/gh", "/snap/bin/gh", os.path.expanduser("~/.local/bin/gh")]


def parse_issue_url(text):
    """Return (owner, repo, number). Raise ValueError if the text is not an issue URL."""
    match = ISSUE_URL_RE.match(text.strip())
    if not match:
        shown = text[:80] + "..." if len(text) > 80 else text
        raise ValueError(f'Select or copy a GitHub issue URL. The text was: "{shown}"')
    return match["owner"], match["repo"], match["number"]


def get_token():
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if token := os.environ.get(name):
            return token
    # AutoKey can have a shorter PATH than the login shell.
    gh = shutil.which("gh") or next((p for p in GH_PATHS if os.access(p, os.X_OK)), None)
    if not gh:
        return None
    try:
        result = subprocess.run([gh, "auth", "token"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def fetch_issue(owner, repo, number):
    """Return the issue JSON from the GitHub API. Raise RuntimeError on failure."""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{number}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "espanso-gh-issue-link",
        },
    )
    token = get_token()
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        hint = "" if token else " Without a token, only public repositories work."
        raise RuntimeError(f"GitHub API returned HTTP {e.code} for {owner}/{repo}#{number}.{hint}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"GitHub API request failed: {getattr(e, 'reason', e)}")
    except json.JSONDecodeError:
        raise RuntimeError("GitHub API returned invalid JSON")


def github_links(text, fetch=fetch_issue):
    """Return {"markdown": ..., "html": ...}. Raise ValueError or RuntimeError on failure."""
    owner, repo, number = parse_issue_url(text)
    issue = fetch(owner, repo, number)
    title = issue.get("title")
    if not title:
        raise RuntimeError(f"GitHub API response for {owner}/{repo}#{number} has no title")
    url = issue.get("html_url") or f"https://github.com/{owner}/{repo}/issues/{number}"
    # A transferred issue has a new repo and number, so label it from html_url.
    try:
        _, repo, number = parse_issue_url(url)
    except ValueError:
        pass
    label = f"{repo} #{number}: {title}"
    return {
        "markdown": f"[{escape_markdown_link_text(label)}]({url})",
        "html": f'<a href="{escape_html(url)}">{escape_html(label)}</a>',
    }
