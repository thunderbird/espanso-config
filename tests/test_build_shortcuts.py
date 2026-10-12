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


def test_zendesk_markdown_workflow_outputs_link():
    workflow = build_shortcuts.build_zendesk_workflow(as_html=False)
    assert identifiers(workflow) == [
        "text.match", "getitemfromlist", "conditional", "gettext", "output",
        "conditional", "notification", "conditional",
    ]
    text = workflow["WFWorkflowActions"][3]["WFWorkflowActionParameters"]["WFTextActionText"]
    assert text["Value"]["string"] == (
        "[Zendesk ticket #￼](https://tbpro.zendesk.com/agent/tickets/￼)"
    )


def test_zendesk_html_workflow_copies_without_output():
    workflow = build_shortcuts.build_zendesk_workflow(as_html=True)
    assert identifiers(workflow) == [
        "text.match", "getitemfromlist", "conditional", "runshellscript",
        "conditional", "notification", "conditional",
    ]
    params = workflow["WFWorkflowActions"][3]["WFWorkflowActionParameters"]
    assert params["InputMode"] == "as arguments"
    assert params["Input"]["WFSerializationType"] == "WFTextTokenAttachment"
    assert 'pasteboard.setStringForType($(`<a href="${url}">${text}</a>`), $("public.html"));' in params["Script"]


def test_github_markdown_workflow_outputs_script_result():
    workflow = build_shortcuts.build_github_workflow(as_html=False)
    assert identifiers(workflow) == [
        "detect.text", "runshellscript", "text.match", "conditional", "notification", "conditional", "output",
        "conditional",
    ]
    script = workflow["WFWorkflowActions"][1]["WFWorkflowActionParameters"]["Script"]
    assert script.endswith(' markdown "$1"\n')


def test_github_html_workflow_has_no_output():
    workflow = build_shortcuts.build_github_workflow(as_html=True)
    assert identifiers(workflow) == [
        "detect.text", "runshellscript", "text.match", "conditional", "notification", "conditional", "conditional",
    ]
    script = workflow["WFWorkflowActions"][1]["WFWorkflowActionParameters"]["Script"]
    assert script.endswith(' html "$1"\n')


def test_github_js_has_no_single_quotes():
    assert "'" not in build_shortcuts.GITHUB_JS
