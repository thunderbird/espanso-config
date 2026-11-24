"""Run AutoHotkey code with the functions in windows/autohotkey for the test_*_ahk.py files.

The code runs from stdin, not links.ahk, because #SingleInstance Force in
links.ahk would stop the running copy.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AHK_DIR = Path(__file__).resolve().parent.parent / "windows" / "autohotkey"
# Every file that links.ahk includes.
LIBRARIES = [
    "markup.ahk", "clipboard.ahk", "web.ahk", "zendesk_link.ahk", "github_link.ahk",
    "bugzilla_link.ahk", "notion_link.ahk", "page_link.ahk",
]


def find_autohotkey():
    if sys.platform != "win32":
        return None
    for path in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "AutoHotkey" / "v2" / "AutoHotkey64.exe",
        Path(os.environ.get("ProgramFiles", "")) / "AutoHotkey" / "v2" / "AutoHotkey64.exe",
    ]:
        if path.is_file():
            return str(path)
    return shutil.which("AutoHotkey64.exe")


AUTOHOTKEY = find_autohotkey()

needs_autohotkey = pytest.mark.skipif(AUTOHOTKEY is None, reason="needs AutoHotkey v2 on Windows")


def run_ahk(code, *args):
    """Run AutoHotkey code and return what it prints."""
    includes = "".join(f"#Include {AHK_DIR / name}\n" for name in LIBRARIES)
    # An uncaught error or a warning would open a dialog and wait for a person.
    on_error = '#Warn All, StdOut\nOnError((e, *) => (FileAppend("Uncaught: " e.Message " " e.What " line " e.Line, "**", "UTF-8-RAW"), ExitApp(1)))\n'
    result = subprocess.run(
        [AUTOHOTKEY, "/ErrorStdOut=UTF-8", "*", *args],
        input=f"{includes}{on_error}{code}\n".encode("utf-8"), capture_output=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stderr == b""
    return result.stdout.decode("utf-8")


def call_links(expression, *args):
    """Evaluate an expression that gives {markdown, html}. It gets args as A_Args.

    Returns "markdown\\nhtml", or "Error: <message>".
    """
    return run_ahk(
        "try {\n"
        f"    l := {expression}\n"
        '    FileAppend(l.markdown "`n" l.html, "*", "UTF-8-RAW")\n'
        "} catch Error as e\n"
        '    FileAppend("Error: " e.Message, "*", "UTF-8-RAW")',
        *args,
    )
