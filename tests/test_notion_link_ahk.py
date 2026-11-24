import pytest

from ahk_run import call_links, needs_autohotkey

pytestmark = needs_autohotkey

ID = "0123456789abcdef0123456789abcdef"
PAGE = f"https://www.notion.so/mzthunderbird/Release-checklist-{ID}"


def links(text):
    return call_links("NotionLinks(A_Args[1])", text)


def markdown(text):
    return links(text).split("\n")[0]


@pytest.mark.parametrize(
    "text",
    [PAGE, f" {PAGE}\n", f"{PAGE}?pvs=4", f"http://notion.so/mzthunderbird/Release-checklist-{ID}"],
)
def test_title_from_url(text):
    url = PAGE if text.strip().startswith("https://www.") else text.strip()
    assert markdown(text) == f"[Notion 89abcdef: Release checklist]({url})"


def test_keeps_block_fragment():
    assert markdown(f"{PAGE}?pvs=4#fedcba") == f"[Notion 89abcdef: Release checklist]({PAGE}#fedcba)"


def test_app_notion_com():
    url = f"https://app.notion.com/p/mzthunderbird/GDPR-DSARs-for-Thundermail-{ID}"
    assert markdown(f"{url}?source=copy_link") == f"[Notion 89abcdef: GDPR DSARs for Thundermail]({url})"


def test_notion_site():
    url = f"https://thunderbird.notion.site/Release-checklist-{ID}"
    assert markdown(url) == f"[Notion 89abcdef: Release checklist]({url})"


def test_decodes_and_escapes_title():
    url = f"https://www.notion.so/ws/Caf%C3%A9-%5DQ3-plan-{ID}"
    assert markdown(url) == f"[Notion 89abcdef: Café \\]Q3 plan]({url})"


def test_invalid_escape_keeps_title():
    url = f"https://www.notion.so/ws/100%-done-{ID}"
    assert markdown(url) == f"[Notion 89abcdef: 100% done]({url})"


def test_html():
    assert links(PAGE).split("\n")[1] == f'<a href="{PAGE}">Notion 89abcdef: Release checklist</a>'


@pytest.mark.parametrize(
    "text",
    [
        f"https://www.notion.so/{ID}",
        f"https://www.notion.so/mzthunderbird/{ID}?pvs=4",
        ID,
        ID.upper(),
        "01234567-89ab-cdef-0123-456789abcdef",
        f"https://www.notion.so/ws/{'f' * 32}?v={'1' * 32}&p={ID}&pm=s",
    ],
)
def test_no_title(text):
    url = text if text.startswith("https://www.notion.so/mzthunderbird/") else f"https://www.notion.so/{ID}"
    assert markdown(text) == f"[Notion 89abcdef]({url.removesuffix('?pvs=4')})"


@pytest.mark.parametrize(
    "text", ["blah", "https://www.notion.so/mzthunderbird", f"https://example.com/{ID}", ID[:-1]]
)
def test_not_notion(text):
    assert markdown(text) == f'Error: Select or copy a Notion page URL or ID. The text was: "{text}"'
