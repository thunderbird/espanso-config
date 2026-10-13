// Turn a Mozilla Bugzilla bug URL into a link with the bug summary.
//
// Usage: osascript -l JavaScript bugzilla_link.js markdown|html <text>
//
// Accepts `https://bugzilla.mozilla.org/show_bug.cgi?id=N`, `bugzil.la/N`,
// a bug number N, and `bug N`, and prints `[Bug N: summary](https://bugzilla.mozilla.org/show_bug.cgi?id=N)`.
// In html mode, the script also copies `<a href="url">Bug N: summary</a>` with
// the Markdown link as plain text, so that Command-V pastes a rich text link.
// On error, the script prints "Error: <message>" and does not change the
// clipboard. Public bugs do not need an API key.
//
// build_shortcuts.py puts this file in single quotes in a shell script, so
// do not use single quotes here.

ObjC.import("AppKit");

const LONG_URL_RE =
  /^https?:\/\/bugzilla\.mozilla\.org\/show_bug\.cgi\?(?:[^#]*&)?id=(\d+)(?:[&#].*)?$/;
const SHORT_URL_RE = /^(?:https?:\/\/)?bugzil\.la\/(\d+)\/?(?:[?#].*)?$/;
// Mozilla has only one Bugzilla, so a number alone is a bug.
const NUMBER_RE = /^(?:bug\s+)?(\d+)$/i;
const API_TIMEOUT_SECONDS = 10;

function parseBugUrl(text) {
  const trimmed = text.trim();
  const match = LONG_URL_RE.exec(trimmed) || SHORT_URL_RE.exec(trimmed) || NUMBER_RE.exec(trimmed);
  if (!match) {
    const shown = text.length > 80 ? `${text.slice(0, 80)}...` : text;
    throw new Error(`the selection is not a Bugzilla bug URL or number: "${shown}"`);
  }
  return match[1];
}

function bugUrl(number) {
  return `https://bugzilla.mozilla.org/show_bug.cgi?id=${number}`;
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

function fetchBug(number) {
  // The number contains only digits, so double quotes are safe for the URL
  // in the shell command.
  const url = `https://bugzilla.mozilla.org/rest/bug/${number}?include_fields=id,summary`;
  const command = [
    "curl --silent --show-error",
    `--max-time ${API_TIMEOUT_SECONDS}`,
    `--header "Accept: application/json"`,
    `--header "User-Agent: espanso-bugzilla-link"`,
    `--write-out "\\n%{http_code}" "${url}"`,
  ].join(" ");

  const app = Application.currentApplication();
  app.includeStandardAdditions = true;
  let output;
  try {
    output = app.doShellScript(command, { alteringLineEndings: false });
  } catch (e) {
    throw new Error(`Bugzilla API request failed: ${e.message}`);
  }
  const split = output.lastIndexOf("\n");
  const status = output.slice(split + 1);
  let data;
  try {
    data = JSON.parse(output.slice(0, split));
  } catch (e) {
    data = null;
  }
  if (status !== "200") {
    // Bugzilla explains the error in the JSON body, for example "Bug 1 does not exist."
    const message = `Bugzilla API returned HTTP ${status} for bug ${number}`;
    throw new Error(data && data.message ? `${message}: ${data.message}` : message);
  }
  if (!data) {
    throw new Error("Bugzilla API returned invalid JSON");
  }
  const bugs = data.bugs;
  if (!bugs || !bugs.length) {
    throw new Error(`Bugzilla API response for bug ${number} has no bug`);
  }
  return bugs[0];
}

function makeLinks(text) {
  const number = parseBugUrl(text);
  const summary = fetchBug(number).summary;
  if (!summary) {
    throw new Error(`Bugzilla API response for bug ${number} has no summary`);
  }
  const url = bugUrl(number);
  const label = `Bug ${number}: ${summary}`;
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
