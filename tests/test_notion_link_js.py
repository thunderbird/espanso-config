import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "macos" / "shortcuts" / "notion_link.js"
ID = "0123456789abcdef0123456789abcdef"
PAGE = f"https://www.notion.so/mzthunderbird/Release-checklist-{ID}"

pytestmark = pytest.mark.skipif(shutil.which("osascript") is None, reason="needs macOS osascript")


def markdown(text):
    return run_script("markdown", text)


def run_script(mode, text):
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", str(SCRIPT), mode, text],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.removesuffix("\n")


@pytest.mark.parametrize(
    "text",
    [PAGE, f" {PAGE}\n", f"{PAGE}?pvs=4", f"http://notion.so/mzthunderbird/Release-checklist-{ID}"],
)
def test_title_from_url(text):
    url = PAGE if text.strip().startswith("https://www.") else text.strip()
    assert markdown(text) == f"[Notion 89abcdef: Release checklist]({url})"


def test_keeps_block_fragment():
    assert markdown(f"{PAGE}?pvs=4#fedcba") == f"[Notion 89abcdef: Release checklist]({PAGE}#fedcba)"


def test_notion_site():
    url = f"https://thunderbird.notion.site/Release-checklist-{ID}"
    assert markdown(url) == f"[Notion 89abcdef: Release checklist]({url})"


def test_decodes_and_escapes_title():
    url = f"https://www.notion.so/ws/Caf%C3%A9-%5DQ3-plan-{ID}"
    assert markdown(url) == f"[Notion 89abcdef: Café \\]Q3 plan]({url})"


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
    assert markdown(text) == f'Error: the selection is not a Notion page URL or ID: "{text}"'


@pytest.fixture
def clipboard():
    saved = subprocess.run(["pbpaste"], capture_output=True, check=True).stdout
    yield lambda text: subprocess.run(["pbcopy"], input=text.encode(), check=True)
    subprocess.run(["pbcopy"], input=saved, check=True)


def paste():
    return subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout


def html_on_clipboard():
    return subprocess.run(
        ["osascript", "-l", "JavaScript", "-e",
         'ObjC.import("AppKit"); $.NSPasteboard.generalPasteboard.stringForType($("public.html")).js'],
        capture_output=True, text=True, check=True,
    ).stdout.removesuffix("\n")


def test_html_copies_link(clipboard):
    clipboard("keep")
    link = f"[Notion 89abcdef: Release checklist]({PAGE})"
    assert run_script("html", PAGE) == link
    assert html_on_clipboard() == f'<a href="{PAGE}">Notion 89abcdef: Release checklist</a>'
    assert paste() == link


def test_empty_selection_uses_clipboard(clipboard):
    clipboard(PAGE)
    link = f"[Notion 89abcdef: Release checklist]({PAGE})"
    assert markdown("") == link
    assert paste() == link


def test_selection_does_not_change_clipboard_in_markdown_mode(clipboard):
    clipboard("keep")
    markdown(PAGE)
    assert paste() == "keep"


def test_error_does_not_change_clipboard(clipboard):
    clipboard("blah")
    assert markdown("").startswith("Error:")
    assert paste() == "blah"
