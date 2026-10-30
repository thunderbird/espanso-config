// Turn a Notion page URL into a link with the page title and a short page ID.
//
// Usage: osascript -l JavaScript notion_link.js markdown|html <text>
//
// Accepts a notion.so, notion.com, or notion.site page URL and a page ID (32 hex
// characters, with or without hyphens), and prints
// `[Notion 89abcdef: Page title](url)`. The link text shows only the last 8
// characters of the page ID, so that the link is short. The link target
// keeps the full ID, because Notion accepts only the full ID.
//
// Most Notion pages are private, so the script does not use the Notion API.
// It takes the title from the words before the ID in the URL. Without these
// words, the link text is `Notion 89abcdef`.
//
// In html mode, the script also copies `<a href="url">Notion 89abcdef: Page title</a>`
// with the Markdown link as plain text, so that Command-V pastes a rich text
// link. On error, the script prints "Error: <message>" and does not change
// the clipboard.
//
// If the selection is empty, the script uses the plain text on the clipboard.
//
// build_shortcuts.py puts this file in single quotes in a shell script, so
// do not use single quotes here.

ObjC.import("AppKit");

const URL_RE = /^https?:\/\/(?:(?:www\.|app\.)?notion\.(?:so|com)|[\w-]+\.notion\.site)\/([^?#\s]*)(\?[^#\s]*)?(#\S*)?$/i;
const ID_RE = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
// The last path segment is "Page-title-<id>" or "<id>".
const SEGMENT_RE = /^(?:(.*)-)?([0-9a-f]{32})$/i;
// A page that opens on top of a database has its ID in the p parameter.
const PEEK_RE = /[?&]p=([0-9a-f]{32})(?:&|$)/i;

function notInput(text) {
  const shown = text.length > 80 ? `${text.slice(0, 80)}...` : text;
  return new Error(`the selection is not a Notion page URL or ID: "${shown}"`);
}

function pageUrl(id) {
  return `https://www.notion.so/${id}`;
}

function decode(text) {
  try {
    return decodeURIComponent(text);
  } catch (e) {
    return text;
  }
}

// Returns the page ID, the title from the URL (can be empty), and the link target.
function parseNotion(text) {
  const trimmed = text.trim();
  if (ID_RE.test(trimmed)) {
    const id = trimmed.replace(/-/g, "").toLowerCase();
    return { id, title: "", url: pageUrl(id) };
  }
  const match = URL_RE.exec(trimmed);
  if (!match) {
    throw notInput(text);
  }
  const [, path, query = "", fragment = ""] = match;
  const peek = PEEK_RE.exec(query);
  if (peek) {
    const id = peek[1].toLowerCase();
    return { id, title: "", url: pageUrl(id) };
  }
  const segments = path.split("/").filter((s) => s);
  const segment = SEGMENT_RE.exec(segments.length ? segments[segments.length - 1] : "");
  if (!segment) {
    throw notInput(text);
  }
  const title = decode(segment[1] || "").replace(/-/g, " ").replace(/\s+/g, " ").trim();
  // The query, for example ?pvs=4, only tells Notion where the link came from.
  const base = trimmed.slice(0, trimmed.length - query.length - fragment.length);
  return { id: segment[2].toLowerCase(), title, url: base + fragment };
}

// Paired brackets are valid in Markdown link text, so escape only
// backslashes and brackets without a partner.
function escapeMarkdownLinkText(title) {
  const chars = Array.from(title);
  const openBrackets = [];
  chars.forEach((c, i) => {
    if (c === "\\") {
      chars[i] = "\\\\";
    } else if (c === "[") {
      openBrackets.push(i);
    } else if (c === "]") {
      if (openBrackets.length) {
        openBrackets.pop();
      } else {
        chars[i] = "\\]";
      }
    }
  });
  openBrackets.forEach((i) => {
    chars[i] = "\\[";
  });
  return chars.join("");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function makeLinks(text) {
  const { id, title, url } = parseNotion(text);
  const shortId = id.slice(-8);
  const label = title ? `Notion ${shortId}: ${title}` : `Notion ${shortId}`;
  return {
    markdown: `[${escapeMarkdownLinkText(label)}](${url})`,
    html: `<a href="${escapeHtml(url)}">${escapeHtml(label)}</a>`,
  };
}

function copyHtml(links) {
  const pasteboard = $.NSPasteboard.generalPasteboard;
  pasteboard.clearContents;
  pasteboard.setStringForType($(links.html), $("public.html"));
  pasteboard.setStringForType($(links.markdown), $("public.utf8-plain-text"));
}

function copyMarkdown(links) {
  const pasteboard = $.NSPasteboard.generalPasteboard;
  pasteboard.clearContents;
  pasteboard.setStringForType($(links.markdown), $("public.utf8-plain-text"));
}

function readClipboard() {
  const text = $.NSPasteboard.generalPasteboard.stringForType($("public.utf8-plain-text"));
  return text.isNil() ? "" : text.js;
}

// Google Docs gives an empty selection. Then the script uses the copied
// text, and markdown mode also copies the link, so that Command-V pastes it.
function run(argv) {
  const [mode, selection = ""] = argv;
  try {
    const fromClipboard = !selection.trim();
    const links = makeLinks(fromClipboard ? readClipboard() : selection);
    if (mode === "html") {
      copyHtml(links);
    } else if (fromClipboard) {
      copyMarkdown(links);
    }
    return links.markdown;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
