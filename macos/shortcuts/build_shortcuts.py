#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build the Zendesk Quick Action shortcuts for the macOS Shortcuts app.

Writes unsigned shortcut files and signs them with `shortcuts sign`, so
that other people can import them. Each Quick Action gets the selected
text and finds the first number in it.

"Zendesk Link" replaces the selection with a Markdown link. "Zendesk HTML
Link" copies an HTML link, with the Markdown link as plain text, and does
not change the selection, so that Command-V replaces it. A Quick Action
cannot replace the selection with rich text in Firefox, and the Shortcuts
"Copy to Clipboard" action copies HTML in a format that Firefox cannot
paste. If the selection has no number, both Quick Actions show a
notification and do not change the selection.
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
OBJECT_REPLACEMENT = "￼"

MARKDOWN_NAME = "Zendesk Link"
HTML_NAME = "Zendesk HTML Link"

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


def build_workflow(as_html: bool) -> dict:
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

    return {
        "WFWorkflowActions": actions,
        "WFWorkflowClientVersion": "2607.0.3",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 4282601983,
            "WFWorkflowIconGlyphNumber": 59511,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": ["WFStringContentItem", "WFRichTextContentItem"],
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

    for name, as_html in ((MARKDOWN_NAME, False), (HTML_NAME, True)):
        output = args.output_dir / f"{name}.shortcut"
        write_signed(build_workflow(as_html), output)
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
