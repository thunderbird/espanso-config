#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build the Zendesk, GitHub, Bugzilla, and page Quick Actions for the macOS Shortcuts app.

Writes unsigned shortcut files and signs them with `shortcuts sign`, so
that other people can import them. Each Quick Action gets the selected
text. The Zendesk Quick Actions find the first number in it. The GitHub
Quick Actions need a GitHub issue URL and get the title from the GitHub API
with github_link.js. The Bugzilla Quick Actions need a Bugzilla bug URL and
get the summary from the Bugzilla REST API with bugzilla_link.js. The page
Quick Actions get no input. They copy a link to the page in the front browser
tab, with the page title as link text, with page_link.js.

The Markdown Quick Actions replace the selection with a Markdown link. The
HTML Quick Actions copy an HTML link, with the Markdown link as plain text,
and do not change the selection, so that Command-V replaces it. A Quick
Action cannot replace the selection with rich text in Firefox, and the
Shortcuts "Copy to Clipboard" action copies HTML in a format that Firefox
cannot paste. On error, the Quick Actions show a notification and do not
change the selection.
"""

from __future__ import annotations

import argparse
import plistlib
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ZENDESK_TICKET_URL = "https://tbpro.zendesk.com/agent/tickets/"
OBJECT_REPLACEMENT = "\ufffc"

ZENDESK_NAME = "Zendesk Link"
ZENDESK_HTML_NAME = "Zendesk HTML Link"
GITHUB_NAME = "GitHub Link"
GITHUB_HTML_NAME = "GitHub HTML Link"
BUGZILLA_NAME = "Bugzilla Link"
BUGZILLA_HTML_NAME = "Bugzilla HTML Link"
PAGE_NAME = "Page Link"
PAGE_HTML_NAME = "Page HTML Link"

# Gets the ticket number as $1 and puts the HTML link and the Markdown link
# on the clipboard as UTF-8.
COPY_HTML_SCRIPT = f"""osascript -l JavaScript -e '
function run(argv) {{
  ObjC.import("AppKit");
  const number = argv[0];
  const url = "{ZENDESK_TICKET_URL}" + number;
  const text = "Zendesk ticket #" + number;
  const pasteboard = $.NSPasteboard.generalPasteboard;
  pasteboard.clearContents;
  pasteboard.setStringForType($(`<a href="${{url}}">${{text}}</a>`), $("public.html"));
  pasteboard.setStringForType($(`[${{text}}](${{url}})`), $("public.utf8-plain-text"));
}}' "$1"
"""

GITHUB_JS = (Path(__file__).parent / "github_link.js").read_text(encoding="utf-8")
BUGZILLA_JS = (Path(__file__).parent / "bugzilla_link.js").read_text(encoding="utf-8")
PAGE_JS = (Path(__file__).parent / "page_link.js").read_text(encoding="utf-8")


def osascript_line(js: str, name: str, mode: str) -> str:
    if "'" in js:
        raise ValueError(f"{name} must not contain single quotes")
    # osascript adds a newline after the result, and "Run Shell Script" keeps
    # it. The command substitution removes it.
    return f"printf %s \"$(osascript -l JavaScript -e '{js}' {mode} \"$1\")\"\n"


def github_script(mode: str) -> str:
    """Make the shell script that runs github_link.js on $1.

    The script uses the GitHub CLI token if gh is installed, because a token
    gives access to private repositories and a higher API rate limit.
    """
    return (
        "for gh in /opt/homebrew/bin/gh /usr/local/bin/gh; do\n"
        '  [ -z "$GH_TOKEN" ] && [ -x "$gh" ] && GH_TOKEN="$("$gh" auth token 2>/dev/null)"\n'
        "done\n"
        "export GH_TOKEN\n"
        + osascript_line(GITHUB_JS, "github_link.js", mode)
    )


def bugzilla_script(mode: str) -> str:
    """Make the shell script that runs bugzilla_link.js on $1."""
    return osascript_line(BUGZILLA_JS, "bugzilla_link.js", mode)


def new_uuid() -> str:
    return str(uuid.uuid4()).upper()


def shortcut_input() -> dict:
    return {"Type": "ExtensionInput"}


def action_output(output_uuid: str, output_name: str) -> dict:
    return {"Type": "ActionOutput", "OutputUUID": output_uuid, "OutputName": output_name}


def attachment(variable: dict) -> dict:
    """Make a value for a field that takes only a variable."""
    return {"Value": variable, "WFSerializationType": "WFTextTokenAttachment"}


def token_string(*parts: str | dict) -> dict:
    """Make a text value. A str part is literal text, a dict part is a variable."""
    text = ""
    attachments = {}
    for part in parts:
        if isinstance(part, str):
            text += part
        else:
            # Shortcuts counts positions in UTF-16 code units.
            position = len(text.encode("utf-16-le")) // 2
            attachments[f"{{{position}, 1}}"] = part
            text += OBJECT_REPLACEMENT
    return {
        "Value": {"string": text, "attachmentsByRange": attachments},
        "WFSerializationType": "WFTextTokenString",
    }


def action(identifier: str, **parameters) -> dict:
    return {
        "WFWorkflowActionIdentifier": f"is.workflow.actions.{identifier}",
        "WFWorkflowActionParameters": parameters,
    }


def markdown_actions(number: dict) -> list[dict]:
    text_uuid = new_uuid()
    return [
        action(
            "gettext",
            UUID=text_uuid,
            WFTextActionText=token_string(
                "[Zendesk ticket #", number, f"]({ZENDESK_TICKET_URL}", number, ")"
            ),
        ),
        action(
            "output",
            WFOutput=token_string(action_output(text_uuid, "Text")),
            WFNoOutputSurfaceBehavior="Do Nothing",
        ),
    ]


def html_actions(number: dict) -> list[dict]:
    # No output, so the selection stays and Command-V replaces it.
    return [
        action(
            "runshellscript",
            Script=COPY_HTML_SCRIPT,
            Shell="/bin/zsh",
            Input=attachment(number),
            InputMode="as arguments",
            RunAsRoot=False,
        )
    ]


def build_zendesk_workflow(as_html: bool) -> dict:
    match_uuid = new_uuid()
    item_uuid = new_uuid()
    group = new_uuid()
    number = action_output(item_uuid, "Item from List")

    actions = [
        action(
            "text.match",
            UUID=match_uuid,
            WFMatchTextPattern=r"\d+",
            text=token_string(shortcut_input()),
        ),
        action(
            "getitemfromlist",
            UUID=item_uuid,
            WFItemSpecifier="First Item",
            WFInput=attachment(action_output(match_uuid, "Matches")),
        ),
        # 100 is "has any value".
        action(
            "conditional",
            GroupingIdentifier=group,
            WFControlFlowMode=0,
            WFCondition=100,
            WFInput={"Type": "Variable", "Variable": attachment(number)},
        ),
        *(html_actions(number) if as_html else markdown_actions(number)),
        action("conditional", GroupingIdentifier=group, WFControlFlowMode=1),
        action(
            "notification",
            WFNotificationActionTitle="No Zendesk ticket number",
            WFNotificationActionBody="Select text that contains a ticket number.",
            WFNotificationActionSound=False,
        ),
        action("conditional", GroupingIdentifier=group, WFControlFlowMode=2),
    ]
    return workflow(actions)


def build_github_workflow(as_html: bool) -> dict:
    return build_script_workflow(github_script, "No GitHub link", as_html)


def build_bugzilla_workflow(as_html: bool) -> dict:
    return build_script_workflow(bugzilla_script, "No Bugzilla link", as_html)


def build_page_workflow(as_html: bool) -> dict:
    """Make a Quick Action without input that runs page_link.js.

    page_link.js copies the link in both modes. It runs in a "Run JavaScript
    for Mac Automation" action, so the file can contain single quotes.
    """
    script_uuid = new_uuid()
    match_uuid = new_uuid()
    group = new_uuid()
    result = action_output(script_uuid, "Result")
    error = action_output(match_uuid, "Matches")
    mode = "html" if as_html else "markdown"

    actions = [
        action(
            "runjavascriptforautomation",
            UUID=script_uuid,
            Script=f'var PAGE_LINK_MODE = "{mode}";\n{PAGE_JS}',
            Input=attachment(shortcut_input()),
        ),
        action(
            "text.match",
            UUID=match_uuid,
            WFMatchTextPattern="^Error:",
            text=token_string(result),
        ),
        # 100 is "has any value".
        action(
            "conditional",
            GroupingIdentifier=group,
            WFControlFlowMode=0,
            WFCondition=100,
            WFInput={"Type": "Variable", "Variable": attachment(error)},
        ),
        action(
            "notification",
            WFNotificationActionTitle="No page link",
            WFNotificationActionBody=token_string(result),
            WFNotificationActionSound=False,
        ),
        action("conditional", GroupingIdentifier=group, WFControlFlowMode=2),
    ]
    return workflow(actions, with_input=False)


def build_script_workflow(make_script, error_title: str, as_html: bool) -> dict:
    """Make a Quick Action that runs a link script on the selected text."""
    text_uuid = new_uuid()
    script_uuid = new_uuid()
    match_uuid = new_uuid()
    group = new_uuid()
    result = action_output(script_uuid, "Shell Script Result")
    error = action_output(match_uuid, "Matches")

    actions = [
        # Make plain text from a rich text selection or a file.
        action("detect.text", UUID=text_uuid, WFInput=attachment(shortcut_input())),
        action(
            "runshellscript",
            UUID=script_uuid,
            Script=make_script("html" if as_html else "markdown"),
            Shell="/bin/zsh",
            Input=attachment(action_output(text_uuid, "Text")),
            InputMode="as arguments",
            RunAsRoot=False,
        ),
        action(
            "text.match",
            UUID=match_uuid,
            WFMatchTextPattern="^Error:",
            text=token_string(result),
        ),
        # 100 is "has any value".
        action(
            "conditional",
            GroupingIdentifier=group,
            WFControlFlowMode=0,
            WFCondition=100,
            WFInput={"Type": "Variable", "Variable": attachment(error)},
        ),
        action(
            "notification",
            WFNotificationActionTitle=error_title,
            WFNotificationActionBody=token_string(result),
            WFNotificationActionSound=False,
        ),
        action("conditional", GroupingIdentifier=group, WFControlFlowMode=1),
    ]
    if not as_html:
        actions.append(
            action(
                "output",
                WFOutput=token_string(result),
                WFNoOutputSurfaceBehavior="Do Nothing",
            )
        )
    # The HTML script already copied the link. No output, so the selection
    # stays and Command-V replaces it.
    actions.append(action("conditional", GroupingIdentifier=group, WFControlFlowMode=2))
    return workflow(actions)


def workflow(actions: list[dict], with_input: bool = True) -> dict:
    # A Quick Action without input classes needs no selection, so its
    # keyboard shortcut works in every app.
    input_classes = ["WFStringContentItem", "WFRichTextContentItem"] if with_input else []
    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "2607.0.3",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": with_input,
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4282601983,
            "WFWorkflowIconGlyphNumber": 59511,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": input_classes,
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": ["QuickActions"],
        "WFQuickActionSurfaces": ["Services"],
    }


def write_signed(workflow: dict, output: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        unsigned = Path(tmp) / "unsigned.shortcut"
        with unsigned.open("wb") as f:
            plistlib.dump(workflow, f, fmt=plistlib.FMT_BINARY)
        subprocess.run(
            ["shortcuts", "sign", "--mode", "anyone", "--input", unsigned, "--output", output],
            check=True,
        )
    output.chmod(0o644)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).parent, help="folder for the files"
    )
    args = parser.parse_args()

    for name, build, as_html in (
        (ZENDESK_NAME, build_zendesk_workflow, False),
        (ZENDESK_HTML_NAME, build_zendesk_workflow, True),
        (GITHUB_NAME, build_github_workflow, False),
        (GITHUB_HTML_NAME, build_github_workflow, True),
        (BUGZILLA_NAME, build_bugzilla_workflow, False),
        (BUGZILLA_HTML_NAME, build_bugzilla_workflow, True),
        (PAGE_NAME, build_page_workflow, False),
        (PAGE_HTML_NAME, build_page_workflow, True),
    ):
        output = args.output_dir / f"{name}.shortcut"
        write_signed(build(as_html), output)
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
