// Turn a selected Zendesk ticket number into a link.
//
// Usage: osascript -l JavaScript zendesk_link.js markdown|html <text>
//
// Uses the first number in the text and ignores the text before it. If text
// follows the number, it goes in the link text: "12345 blah blah" gives
// `[Zendesk ticket #12345: blah blah](https://tbpro.zendesk.com/agent/tickets/12345)`.
// A ticket URL followed by text gives the same link.
// In html mode, the script also copies `<a href="url">Zendesk ticket #12345: blah blah</a>`
// with the Markdown link as plain text, so that Command-V pastes a rich text
// link. On error, the script prints "Error: <message>" and does not change
// the clipboard. The script does not call the Zendesk API.
//
// build_shortcuts.py puts this file in single quotes in a shell script, so
// do not use single quotes here.

ObjC.import("AppKit");

const TICKET_URL = "https://tbpro.zendesk.com/agent/tickets/";
const NUMBER_RE = /\d+/;
// The rest of a ticket URL after the number, for example "/", "?foo=bar", or "#comment".
const URL_REST_RE = /^[/?#]\S*/;
// Separators between the number and the text, for example "12345: blah" or "12345 - blah".
const SEPARATOR_RE = /^[\s:\-\u2013\u2014|]+/;

function parseTicket(text) {
  const match = NUMBER_RE.exec(text);
  if (!match) {
    throw new Error("Select text that contains a ticket number.");
  }
  const number = match[0];
  let rest = text.slice(match.index + number.length);
  if (text.slice(0, match.index).endsWith("/tickets/")) {
    rest = rest.replace(URL_REST_RE, "");
  }
  const title = rest.replace(SEPARATOR_RE, "").replace(/\s+/g, " ").trim();
  return { number, title };
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
  const { number, title } = parseTicket(text);
  const url = TICKET_URL + number;
  const label = title ? `Zendesk ticket #${number}: ${title}` : `Zendesk ticket #${number}`;
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

function run(argv) {
  const [mode, text = ""] = argv;
  try {
    const links = makeLinks(text);
    if (mode === "html") {
      copyHtml(links);
    }
    return links.markdown;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
