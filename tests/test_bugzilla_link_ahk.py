import json

import pytest

from ahk_run import call_links, needs_autohotkey

pytestmark = needs_autohotkey

URL = "https://bugzilla.mozilla.org/show_bug.cgi?id=2064458"


def links(text, data):
    """Make the links from a selection and an API response, without the network."""
    return call_links("BugzillaLinksFromBug(ParseBugzillaBug(A_Args[1]), JsonParse(A_Args[2]))", text, json.dumps(data))


def bug(summary):
    return {"bugs": [{"id": 2064458, "summary": summary}]}


@pytest.mark.parametrize(
    "text",
    [
        URL,
        f"  {URL}\n",
        URL.replace("https", "http"),
        f"{URL}#c3",
        f"{URL}&foo=bar",
        "https://bugzilla.mozilla.org/show_bug.cgi?foo=bar&id=2064458",
        "bugzil.la/2064458",
        "bugzil.la/2064458/",
        "https://bugzil.la/2064458#c3",
        "2064458",
        "bug 2064458",
        "Bug  2064458",
        "BUG 2064458",
    ],
)
def test_bug(text):
    assert links(text, bug("Crash on start")) == (
        f"[Bug 2064458: Crash on start]({URL})\n"
        f'<a href="{URL}">Bug 2064458: Crash on start</a>'
    )


def test_escapes_summary():
    assert links("2064458", bug("[meta] a]b & <c>")) == (
        f"[Bug 2064458: [meta] a\\]b & <c>]({URL})\n"
        f'<a href="{URL}">Bug 2064458: [meta] a]b &amp; &lt;c&gt;</a>'
    )


@pytest.mark.parametrize("data", [{}, {"bugs": []}, {"bugs": [{"id": 1}]}])
def test_no_summary(data):
    assert links("2064458", data).startswith("Error: The Bugzilla API response for bug 2064458 has no")


@pytest.mark.parametrize(
    "text",
    ["blah", "bug", "bug abc", "https://bugzilla.mozilla.org/show_bug.cgi?id=abc", "https://example.com/show_bug.cgi?id=1"],
)
def test_not_bug(text):
    assert links(text, {}) == f'Error: Select or copy a Bugzilla bug URL or number. The text was: "{text}"'
