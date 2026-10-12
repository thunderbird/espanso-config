// Turn a GitHub issue URL into a link with the issue title.
//
// Usage: osascript -l JavaScript github_link.js markdown|html <text>
//
// Prints `[repo #number: title](url)`. In html mode, the script also copies
// `<a href="url">repo #number: title</a>` with the Markdown link as plain
// text, so that Command-V pastes a rich text link. On error, the script
// prints "Error: <message>" and does not change the clipboard. If the
// GH_TOKEN environment variable is set, the script sends it to the GitHub API.
//
// build_shortcuts.py puts this file in single quotes in a shell script, so
// do not use single quotes here.

ObjC.import("AppKit");

const ISSUE_URL_RE =
  /^https?:\/\/(?:www\.)?github\.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+)\/issues\/(\d+)(?:[\/?#].*)?$/;
const API_TIMEOUT_SECONDS = 10;

function parseIssueUrl(text) {
  const match = ISSUE_URL_RE.exec(text.trim());
  if (!match) {
    const shown = text.length > 80 ? `${text.slice(0, 80)}...` : text;
    throw new Error(`the selection is not a GitHub issue URL: "${shown}"`);
  }
  return { owner: match[1], repo: match[2], number: match[3] };
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

function fetchIssue({ owner, repo, number }) {
  // The URL contains only the characters that ISSUE_URL_RE allows, so double
  // quotes are safe for it in the shell command.
  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${number}`;
  const headers = [
    "Accept: application/vnd.github+json",
    "X-GitHub-Api-Version: 2022-11-28",
    "User-Agent: espanso-gh-issue-link",
  ];
  const token = ObjC.unwrap($.NSProcessInfo.processInfo.environment.objectForKey("GH_TOKEN"));
  if (token && /^[A-Za-z0-9_]+$/.test(token)) {
    headers.push(`Authorization: Bearer ${token}`);
  }
  const command = [
    "curl --silent --show-error",
    `--max-time ${API_TIMEOUT_SECONDS}`,
    ...headers.map((h) => `--header "${h}"`),
    `--write-out "\\n%{http_code}" "${url}"`,
  ].join(" ");

  const app = Application.currentApplication();
  app.includeStandardAdditions = true;
  let output;
  try {
    output = app.doShellScript(command, { alteringLineEndings: false });
  } catch (e) {
    throw new Error(`GitHub API request failed: ${e.message}`);
  }
  const split = output.lastIndexOf("\n");
  const status = output.slice(split + 1);
  if (status !== "200") {
    throw new Error(`GitHub API returned HTTP ${status} for ${owner}/${repo}#${number}`);
  }
  try {
    return JSON.parse(output.slice(0, split));
  } catch (e) {
    throw new Error("GitHub API returned invalid JSON");
  }
}

function makeLinks(text) {
  const issue = parseIssueUrl(text);
  const data = fetchIssue(issue);
  if (!data.title) {
    throw new Error(`GitHub API response for ${issue.owner}/${issue.repo}#${issue.number} has no title`);
  }
  const url = data.html_url || `https://github.com/${issue.owner}/${issue.repo}/issues/${issue.number}`;
  // A transferred issue has a new repo and number, so label it from html_url.
  let { repo, number } = issue;
  try {
    ({ repo, number } = parseIssueUrl(url));
  } catch (e) {}
  const label = `${repo} #${number}: ${data.title}`;
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
