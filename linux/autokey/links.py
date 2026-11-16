"""Hotkey logic that turns the selection into a link, as the macOS Quick
Actions and windows/autohotkey/links.ahk do. The AutoKey scripts in
Links/ call link_hotkey.

Copies the selection with Ctrl+C and makes the links with make_links.
If nothing is selected, uses the text that was on the clipboard, because
Google Docs gives an empty selection to the macOS Quick Actions.

markdown mode replaces the selection with the Markdown link and restores
the clipboard text. If nothing was selected, it only copies the link.
html mode copies the HTML link with the Markdown link as plain text, and
does not change the selection.
On error, shows a notification and does not change the selection or the
clipboard.
"""

import subprocess
import time

from copy_html import copy_html

COPY_TIMEOUT = 0.5
PASTE_DELAY = 0.3


def read_clipboard():
    """Return the clipboard text, or "" if the clipboard has no text."""
    result = subprocess.run(
        ["wl-paste", "--no-newline", "--type", "text/plain;charset=utf-8"],
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", "replace")


def write_clipboard(text):
    subprocess.run(["wl-copy", "--type", "text/plain;charset=utf-8", "--", text], check=True)


def clear_clipboard():
    subprocess.run(["wl-copy", "--clear"], check=True)


def copy_selection(keyboard):
    """Copy the selection with Ctrl+C and return it, or "" if nothing is selected."""
    clear_clipboard()
    keyboard.send_keys("<ctrl>+c")
    deadline = time.monotonic() + COPY_TIMEOUT
    while time.monotonic() < deadline:
        text = read_clipboard()
        if text:
            return text
        time.sleep(0.05)
    return ""


def notify(message):
    subprocess.run(["notify-send", "--app-name=Links", "--expire-time=4000", "Links", message])


def link_hotkey(make_links, mode, keyboard):
    old_text = read_clipboard()
    selection = copy_selection(keyboard)
    from_clipboard = not selection.strip()
    try:
        links = make_links(old_text if from_clipboard else selection)
        if mode == "html":
            copy_html(links["html"], links["markdown"])
            notify(f"Copied {links['markdown']}\nPress Ctrl+V.")
        elif from_clipboard:
            write_clipboard(links["markdown"])
            notify(f"Copied {links['markdown']}\nPress Ctrl+V.")
        else:
            write_clipboard(links["markdown"])
            keyboard.send_keys("<ctrl>+v")
            # Give the app time to read the clipboard before it changes back.
            time.sleep(PASTE_DELAY)
            restore(old_text)
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as e:
        restore(old_text)
        notify(f"Error: {e}")


def restore(text):
    if text:
        write_clipboard(text)
    else:
        clear_clipboard()
