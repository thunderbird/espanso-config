import importlib.util
import io
import urllib.error
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "bugzilla_link.py"
spec = importlib.util.spec_from_file_location("bugzilla_link", SCRIPT)
bugzilla_link = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bugzilla_link)


@pytest.mark.parametrize(
    "url",
    [
        "https://bugzilla.mozilla.org/show_bug.cgi?id=2064458",
        "  https://bugzilla.mozilla.org/show_bug.cgi?id=2064458\n",
        "http://bugzilla.mozilla.org/show_bug.cgi?id=2064458",
        "https://bugzilla.mozilla.org/show_bug.cgi?id=2064458#c3",
        "https://bugzilla.mozilla.org/show_bug.cgi?id=2064458&foo=bar",
        "https://bugzilla.mozilla.org/show_bug.cgi?foo=bar&id=2064458",
        "bugzil.la/2064458",
        "bugzil.la/2064458/",
        "http://bugzil.la/2064458",
        "https://bugzil.la/2064458",
        "https://bugzil.la/2064458#c3",
    ],
)
def test_parse_bug_url(url):
    assert bugzilla_link.parse_bug_url(url) == 2064458


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not a url",
        "2064458",
        "https://bugzilla.mozilla.org/show_bug.cgi?id=abc",
        "https://bugzilla.mozilla.org/show_bug.cgi?bugid=2064458",
        "https://bugzilla.example.org/show_bug.cgi?id=2064458",
        "https://bugzil.la/",
        "https://bugzil.la/2064458abc",
    ],
)
def test_parse_bug_url_rejects(text):
    with pytest.raises(bugzilla_link.LinkError):
        bugzilla_link.parse_bug_url(text)


def test_make_link(monkeypatch):
    def fake_fetch(number):
        assert number == 7
        return {"id": 7, "summary": "[Thundermail] Fix [thing]"}

    monkeypatch.setattr(bugzilla_link, "fetch_bug", fake_fetch)
    link = bugzilla_link.make_link("bugzil.la/7")
    assert link == (
        "[Bug 7: [Thundermail] Fix [thing]]"
        "(https://bugzilla.mozilla.org/show_bug.cgi?id=7)"
    )


def test_make_link_html(monkeypatch):
    monkeypatch.setattr(
        bugzilla_link, "fetch_bug", lambda n: {"id": n, "summary": 'Fix <b> & "q"'}
    )
    link = bugzilla_link.make_link(
        "https://bugzilla.mozilla.org/show_bug.cgi?id=7", as_html=True
    )
    assert link == (
        '<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=7">'
        "Bug 7: Fix &lt;b&gt; &amp; &quot;q&quot;</a>"
    )


def test_make_link_without_summary(monkeypatch):
    monkeypatch.setattr(bugzilla_link, "fetch_bug", lambda n: {"id": n, "summary": ""})
    with pytest.raises(bugzilla_link.LinkError):
        bugzilla_link.make_link("bugzil.la/7")


def _http_error(code, body):
    return urllib.error.HTTPError(
        "https://bugzilla.mozilla.org/rest/bug/7", code, "error", {}, io.BytesIO(body)
    )


@pytest.mark.parametrize(
    "error, expected",
    [
        (
            _http_error(401, b'{"error":true,"code":102,"message":"You are not authorized."}'),
            "HTTP 401 for bug 7: You are not authorized.",
        ),
        (_http_error(500, b"not json"), "HTTP 500 for bug 7"),
        (urllib.error.URLError("no network"), "request failed: no network"),
    ],
)
def test_fetch_bug_errors(monkeypatch, error, expected):
    def fake_urlopen(*args, **kwargs):
        raise error

    monkeypatch.setattr(bugzilla_link.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(bugzilla_link.LinkError, match=expected):
        bugzilla_link.fetch_bug(7)


def test_fetch_bug_without_bugs(monkeypatch):
    monkeypatch.setattr(
        bugzilla_link.urllib.request,
        "urlopen",
        lambda *a, **k: io.BytesIO(b'{"faults":[],"bugs":[]}'),
    )
    with pytest.raises(bugzilla_link.LinkError):
        bugzilla_link.fetch_bug(7)
