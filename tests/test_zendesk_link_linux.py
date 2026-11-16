import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "linux" / "autokey"))

from zendesk_link import zendesk_links  # noqa: E402

URL = "https://tbpro.zendesk.com/agent/tickets/"


def markdown(text):
    return zendesk_links(text)["markdown"]


@pytest.mark.parametrize(
    "text",
    ["12345", " 12345\n", "#12345", "Zendesk ticket #12345", f"{URL}12345", f"{URL}12345/", f"{URL}12345?foo=bar"],
)
def test_number_only(text):
    assert markdown(text) == f"[Zendesk ticket #12345]({URL}12345)"


@pytest.mark.parametrize(
    "text",
    [
        "12345 blah blah",
        "12345: blah blah",
        "12345 - blah blah",
        "12345 – blah blah",
        "12345\r\n  blah\tblah ",
        "ticket 12345 blah blah",
        f"{URL}12345 blah blah",
        f"{URL}12345#comment blah blah",
    ],
)
def test_text_after_number(text):
    assert markdown(text) == f"[Zendesk ticket #12345: blah blah]({URL}12345)"


def test_escapes_unpaired_brackets():
    assert markdown("12345 [Thundermail] a]b\\c") == (
        f"[Zendesk ticket #12345: [Thundermail] a\\]b\\\\c]({URL}12345)"
    )


def test_text_with_more_numbers_keeps_them():
    assert markdown("12345 crash in 128.0") == f"[Zendesk ticket #12345: crash in 128.0]({URL}12345)"


def test_non_ascii_text():
    assert markdown("12345 café → ok") == f"[Zendesk ticket #12345: café → ok]({URL}12345)"


def test_non_ascii_digits_are_not_a_number():
    assert markdown("١٢٣ 12345") == f"[Zendesk ticket #12345]({URL}12345)"


def test_html():
    assert zendesk_links('12345 a < b & "c"')["html"] == (
        f'<a href="{URL}12345">Zendesk ticket #12345: a &lt; b &amp; &quot;c&quot;</a>'
    )


def test_no_number():
    with pytest.raises(ValueError, match='^Select or copy text that contains a ticket number. The text was: "blah"$'):
        zendesk_links("blah")


def test_no_number_shortens_long_text():
    with pytest.raises(ValueError) as e:
        zendesk_links("x" * 100)
    assert str(e.value).endswith(f'"{"x" * 80}..."')
