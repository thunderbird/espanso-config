import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "zd_ticket_link.py"
spec = importlib.util.spec_from_file_location("zd_ticket_link", SCRIPT)
zd_ticket_link = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zd_ticket_link)


@pytest.mark.parametrize(
    "url",
    [
        "https://tbpro.zendesk.com/agent/tickets/8486",
        "  https://tbpro.zendesk.com/agent/tickets/8486\n",
        "https://tbpro.zendesk.com/agent/tickets/8486/",
        "https://tbpro.zendesk.com/agent/tickets/8486?foo=bar",
        "https://tbpro.zendesk.com/agent/tickets/8486#comment",
    ],
)
def test_parse_ticket_url(url):
    assert zd_ticket_link.parse_ticket_url(url) == 8486


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not a url",
        "https://tbpro.zendesk.com/agent/tickets/",
        "https://tbpro.zendesk.com/agent/tickets/abc",
        "https://tbpro.zendesk.com/agent/users/8486",
        "https://other.zendesk.com/agent/tickets/8486",
        "https://github.com/thunderbird/espanso-config/issues/1",
    ],
)
def test_parse_ticket_url_rejects(text):
    with pytest.raises(zd_ticket_link.LinkError):
        zd_ticket_link.parse_ticket_url(text)


def test_make_link_markdown():
    link = zd_ticket_link.make_link("https://tbpro.zendesk.com/agent/tickets/8486?foo=bar")
    assert link == "[Zendesk ticket #8486](https://tbpro.zendesk.com/agent/tickets/8486)"


def test_make_link_html():
    link = zd_ticket_link.make_link("https://tbpro.zendesk.com/agent/tickets/8486", as_html=True)
    assert link == '<a href="https://tbpro.zendesk.com/agent/tickets/8486">Zendesk ticket #8486</a>'
