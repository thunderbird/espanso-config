import json

import pytest

from ahk_run import call_links, needs_autohotkey

pytestmark = needs_autohotkey

URL = "https://github.com/thunderbird/espanso-config/issues/29"


def links(text, issue):
    """Make the links from a selection and an API response, without the network."""
    return call_links("GitHubLinksFromIssue(ParseGitHubIssueUrl(A_Args[1]), JsonParse(A_Args[2]))", text, json.dumps(issue))


@pytest.mark.parametrize(
    "text",
    [URL, f" {URL}\n", f"{URL}#issuecomment-1", f"{URL}?foo=bar", URL.replace("https://", "http://www.")],
)
def test_issue_url(text):
    assert links(text, {"title": "Windows hotkeys", "html_url": URL}) == (
        f"[espanso-config #29: Windows hotkeys]({URL})\n"
        f'<a href="{URL}">espanso-config #29: Windows hotkeys</a>'
    )


def test_escapes_title():
    assert links(URL, {"title": '[Thundermail] a]b\\c <"&">', "html_url": URL}) == (
        f"[espanso-config #29: [Thundermail] a\\]b\\\\c <\"&\">]({URL})\n"
        f'<a href="{URL}">espanso-config #29: [Thundermail] a]b\\c &lt;&quot;&amp;&quot;&gt;</a>'
    )


def test_transferred_issue_uses_new_url():
    new = "https://github.com/thunderbird/other-repo/issues/7"
    assert links(URL, {"title": "Moved", "html_url": new}).split("\n")[0] == f"[other-repo #7: Moved]({new})"


def test_no_html_url():
    assert links(URL, {"title": "T"}).split("\n")[0] == f"[espanso-config #29: T]({URL})"


def test_no_title():
    assert links(URL, {"html_url": URL}) == (
        "Error: The GitHub API response for thunderbird/espanso-config#29 has no title."
    )


@pytest.mark.parametrize(
    "text",
    ["blah", "https://github.com/thunderbird/espanso-config/pull/29", "https://example.com/a/b/issues/1"],
)
def test_not_issue_url(text):
    assert links(text, {}) == f'Error: Select or copy a GitHub issue URL. The text was: "{text}"'
