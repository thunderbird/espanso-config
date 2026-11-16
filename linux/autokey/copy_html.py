"""Copy an HTML link with a plain text version to the clipboard.

Usage: python3 copy_html.py <html> <text>

wl-copy offers only one type, so this script uses GTK 4 to offer both
text/html and text/plain. It uses the X11 backend (Xwayland), because GNOME
lets an X11 program own the clipboard without a focused window, and copies
the X11 clipboard to Wayland apps. A detached copy of the script keeps
the clipboard until another program copies something.
"""

import os
import subprocess
import sys


def own_clipboard(html, text, ready):
    """Own the clipboard until another program copies. Calls ready() when done."""
    import gi

    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk, GLib, Gtk

    Gtk.init()
    clipboard = Gdk.Display.get_default().get_clipboard()
    # A str value lets GTK offer all the plain text types with the right encoding.
    provider = Gdk.ContentProvider.new_union([
        Gdk.ContentProvider.new_for_bytes("text/html", GLib.Bytes.new(html.encode("utf-8"))),
        Gdk.ContentProvider.new_for_value(text),
    ])
    clipboard.set_content(provider)
    loop = GLib.MainLoop()

    def changed(cb):
        if not cb.is_local():
            loop.quit()

    clipboard.connect("changed", changed)
    GLib.idle_add(lambda: ready() or False)
    loop.run()


def copy_html(html, text):
    """Start a detached copy of this script that owns the clipboard.

    Returns when the clipboard has the links. Raises RuntimeError on failure.
    """
    env = dict(os.environ, GDK_BACKEND="x11")
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--serve", html, text],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, start_new_session=True,
    )
    if proc.stdout.read(1) != b"1":
        error = proc.stderr.read().decode("utf-8", "replace").strip()
        raise RuntimeError(f"Could not copy the link. {error}".strip())
    proc.stdout.close()
    proc.stderr.close()


def main(argv):
    if len(argv) == 4 and argv[1] == "--serve":
        def ready():
            sys.stdout.buffer.write(b"1")
            sys.stdout.flush()
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)

        own_clipboard(argv[2], argv[3], ready)
        return 0
    if len(argv) != 3:
        print("Usage: python3 copy_html.py <html> <text>", file=sys.stderr)
        return 2
    copy_html(argv[1], argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
