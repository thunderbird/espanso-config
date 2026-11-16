import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "linux" / "autokey"))

import github_link  # noqa: E402
from github_link import github_links, parse_issue_url  # noqa: E402

URL = "https://github.com/thunderbird/espanso-config/issues/1"


def fake_fetch(data):
    calls = []

    def fetch(owner, repo, number):
        calls.append((owner, repo, number))
        return data

    fetch.calls = calls
    return fetch


@pytest.mark.parametrize(
    "text",
    [URL, f" {URL}\n", f"{URL}/", f"{URL}#issuecomment-1", f"{URL}?q=1", "http://www.github.com/thunderbird/espanso-config/issues/1"],
)
def test_parse_issue_url(text):
    assert parse_issue_url(text) == ("thunderbird", "espanso-config", "1")


@pytest.mark.parametrize(
    "text",
    ["", "1", "https://github.com/thunderbird/espanso-config/pull/1", "see " + URL, "https://example.com/a/b/issues/1"],
)
def test_parse_issue_url_rejects(text):
    with pytest.raises(ValueError, match="GitHub issue URL"):
        parse_issue_url(text)


def test_links():
    fetch = fake_fetch({"title": "Add a [draft] macro ]", "html_url": URL})
    assert github_links(URL + "#x", fetch) == {
        "markdown": f"[espanso-config #1: Add a [draft] macro \\]]({URL})",
        "html": f'<a href="{URL}">espanso-config #1: Add a [draft] macro ]</a>',
    }
    assert fetch.calls == [("thunderbird", "espanso-config", "1")]


def test_html_escapes():
    links = github_links(URL, fake_fetch({"title": 'a <b> & "c"', "html_url": URL}))
    assert links["html"] == f'<a href="{URL}">espanso-config #1: a &lt;b&gt; &amp; &quot;c&quot;</a>'


def test_transferred_issue():
    new = "https://github.com/thunderbird/other-repo/issues/7"
    links = github_links(URL, fake_fetch({"title": "Moved", "html_url": new}))
    assert links["markdown"] == f"[other-repo #7: Moved]({new})"


def test_no_html_url():
    links = github_links(URL + "/", fake_fetch({"title": "T"}))
    assert links["markdown"] == f"[espanso-config #1: T]({URL})"


def test_no_title():
    with pytest.raises(RuntimeError, match="no title"):
        github_links(URL, fake_fetch({"html_url": URL}))


def test_not_a_url_does_not_call_api():
    fetch = fake_fetch({"title": "T"})
    with pytest.raises(ValueError):
        github_links("12345", fetch)
    assert fetch.calls == []


@pytest.mark.parametrize("name", ["GITHUB_TOKEN", "GH_TOKEN"])
def test_token_from_environment(monkeypatch, name):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv(name, "abc")
    assert github_link.get_token() == "abc"


def test_no_token_without_gh(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(github_link.shutil, "which", lambda name: None)
    monkeypatch.setattr(github_link, "GH_PATHS", [])
    assert github_link.get_token() is None
