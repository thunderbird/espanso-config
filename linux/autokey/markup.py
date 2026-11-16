"""Escaping for the Markdown and HTML links that the Linux hotkeys make."""


def escape_markdown_link_text(title):
    """Escape backslashes and unpaired brackets.

    Paired brackets are valid in Markdown link text, so they stay as they are.
    """
    chars = list(title)
    open_brackets = []
    for i, c in enumerate(chars):
        if c == "\\":
            chars[i] = "\\\\"
        elif c == "[":
            open_brackets.append(i)
        elif c == "]":
            if open_brackets:
                open_brackets.pop()
            else:
                chars[i] = "\\]"
    for i in open_brackets:
        chars[i] = "\\["
    return "".join(chars)


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
