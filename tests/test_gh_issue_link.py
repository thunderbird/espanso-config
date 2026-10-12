import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "gh_issue_link.py"
spec = importlib.util.spec_from_file_location("gh_issue_link", SCRIPT)
gh_issue_link = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh_issue_link)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/thunderbird/espanso-config/issues/1",
        "  https://github.com/thunderbird/espanso-config/issues/1\n",
        "https://github.com/thunderbird/espanso-config/issues/1#issuecomment-123",
        "https://github.com/thunderbird/espanso-config/issues/1?foo=bar",
        "http://www.github.com/thunderbird/espanso-config/issues/1/",
    ],
)
def test_parse_issue_url(url):
    assert gh_issue_link.parse_issue_url(url) == ("thunderbird", "espanso-config", 1)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not a url",
        "https://github.com/thunderbird/espanso-config",
        "https://github.com/thunderbird/espanso-config/pull/1",
        "https://github.com/thunderbird/espanso-config/issues/abc",
        "https://example.com/thunderbird/espanso-config/issues/1",
    ],
)
def test_parse_issue_url_rejects(text):
    with pytest.raises(gh_issue_link.LinkError):
        gh_issue_link.parse_issue_url(text)


@pytest.mark.parametrize(
    "title, expected",
    [
        ("[bug] fix", "[bug] fix"),
        ("[a [b]] c", "[a [b]] c"),
        ("a ] b", r"a \] b"),
        ("a [ b", r"a \[ b"),
        ("] [x] [", r"\] [x] \["),
        (r"a\b", r"a\\b"),
    ],
)
def test_escape_markdown_link_text(title, expected):
    assert gh_issue_link.escape_markdown_link_text(title) == expected


def test_make_link(monkeypatch):
    def fake_fetch(owner, repo, number, token):
        assert (owner, repo, number, token) == ("o", "r", 7, "tok")
        return {"title": "Fix [thing] ]", "html_url": "https://github.com/o/r/issues/7"}

    monkeypatch.setattr(gh_issue_link, "fetch_issue", fake_fetch)
    link = gh_issue_link.make_link("https://github.com/o/r/issues/7", "tok")
    assert link == r"[r #7: Fix [thing] \]](https://github.com/o/r/issues/7)"


def test_make_link_transferred_issue(monkeypatch):
    monkeypatch.setattr(
        gh_issue_link,
        "fetch_issue",
        lambda *a: {"title": "Moved", "html_url": "https://github.com/o/new/issues/42"},
    )
    link = gh_issue_link.make_link("https://github.com/o/r/issues/7", None)
    assert link == "[new #42: Moved](https://github.com/o/new/issues/42)"


def test_make_link_html(monkeypatch):
    monkeypatch.setattr(
        gh_issue_link,
        "fetch_issue",
        lambda *a: {"title": 'Fix <b> & "q"', "html_url": "https://github.com/o/r/issues/7"},
    )
    link = gh_issue_link.make_link("https://github.com/o/r/issues/7", None, as_html=True)
    assert link == (
        '<a href="https://github.com/o/r/issues/7">r #7: Fix &lt;b&gt; &amp; &quot;q&quot;</a>'
    )


def test_make_link_without_title(monkeypatch):
    monkeypatch.setattr(gh_issue_link, "fetch_issue", lambda *a: {"title": ""})
    with pytest.raises(gh_issue_link.LinkError):
        gh_issue_link.make_link("https://github.com/o/r/issues/7", None)
