import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "macos" / "shortcuts" / "build_shortcuts.py"
spec = importlib.util.spec_from_file_location("build_shortcuts", SCRIPT)
build_shortcuts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_shortcuts)


def identifiers(workflow):
    return [a["WFWorkflowActionIdentifier"].removeprefix("is.workflow.actions.") for a in workflow["WFWorkflowActions"]]


def test_token_string_positions():
    variable = {"Type": "ExtensionInput"}
    value = build_shortcuts.token_string("#", variable, "é", variable)["Value"]
    assert value["string"] == "#￼é￼"
    assert list(value["attachmentsByRange"]) == ["{1, 1}", "{3, 1}"]


def test_markdown_workflow_outputs_link():
    workflow = build_shortcuts.build_workflow(as_html=False)
    assert identifiers(workflow) == [
        "text.match", "getitemfromlist", "conditional", "gettext", "output",
        "conditional", "notification", "conditional",
    ]
    text = workflow["WFWorkflowActions"][3]["WFWorkflowActionParameters"]["WFTextActionText"]
    assert text["Value"]["string"] == (
        "[Zendesk ticket #￼](https://tbpro.zendesk.com/agent/tickets/￼)"
    )


def test_html_workflow_copies_without_output():
    workflow = build_shortcuts.build_workflow(as_html=True)
    assert identifiers(workflow) == [
        "text.match", "getitemfromlist", "conditional", "runshellscript",
        "conditional", "notification", "conditional",
    ]
    params = workflow["WFWorkflowActions"][3]["WFWorkflowActionParameters"]
    assert params["InputMode"] == "as arguments"
    assert params["Input"]["WFSerializationType"] == "WFTextTokenAttachment"
    assert 'pasteboard.setStringForType($(`<a href="${url}">${text}</a>`), $("public.html"));' in params["Script"]
