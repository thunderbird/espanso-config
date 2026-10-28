// Copy a link to the current web page, with the page title as link text.
//
// Usage: osascript -l JavaScript page_link.js markdown|html [browser]
//
// Gets the title and URL of the front tab of the front app, or of the
// browser that you give, for example "Safari", "Google Chrome", or
// "Firefox". Safari and Chrome give the title and URL with AppleScript.
// Firefox gives only the window title, so the script finds the URL of the
// most recent visit with this title in the Firefox history. The script needs
// no Accessibility permission.
//
// In markdown mode, the script copies `[title](url)`. In html mode, it copies
// `<a href="url">title</a>` with the Markdown link as plain text, so that
// Command-V pastes a rich text link. The script prints the Markdown link. On
// error, the script prints "Error: <message>" and does not change the
// clipboard.
//
// build_shortcuts.py puts this file in a "Run JavaScript for Mac Automation"
// action. It adds `var PAGE_LINK_MODE = "markdown";` or "html"
// before the file, because the action gives no arguments.

ObjC.import("AppKit");

const SAFARI_IDS = ["com.apple.Safari", "com.apple.SafariTechnologyPreview"];
const CHROME_IDS = ["com.google.Chrome", "com.google.Chrome.beta", "com.google.Chrome.canary"];
const FIREFOX_IDS = [
  "org.mozilla.firefox",
  "org.mozilla.firefoxdeveloperedition",
  "org.mozilla.nightly",
];
const BROWSER_NAMES = {
  safari: "com.apple.Safari",
  "google chrome": "com.google.Chrome",
  chrome: "com.google.Chrome",
  firefox: "org.mozilla.firefox",
};
// Firefox adds the browser name or the profile name to the window title,
// for example "Title — Mozilla Firefox" or "Title — Work".
const FIREFOX_SUFFIX_RE =
  /\s+[—–-]\s+(?:Mozilla Firefox|Firefox(?: Developer Edition| Nightly)?)(?: Private Browsing)?$/;
const PROFILE_SUFFIX_RE = /\s+—\s+[^—]*$/;

function frontBundleId() {
  return ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.bundleIdentifier);
}

function chromeTab(bundleId) {
  const app = Application(bundleId);
  if (!app.windows.length) {
    throw new Error("Chrome has no open window");
  }
  const tab = app.windows[0].activeTab;
  return { title: tab.title(), url: tab.url() };
}

function safariTab(bundleId) {
  const app = Application(bundleId);
  if (!app.windows.length) {
    throw new Error("Safari has no open window");
  }
  const tab = app.windows[0].currentTab;
  return { title: tab.name(), url: tab.url() };
}

function shellQuote(text) {
  return `'${text.replace(/'/g, `'\\''`)}'`;
}

function sqlQuote(text) {
  return `'${text.replace(/'/g, "''")}'`;
}

// Finds the most recent URL with one of the titles in the history of the
// open Firefox profiles. Firefox locks places.sqlite, so the script copies it
// with its write-ahead log, which has the recent visits. Only an open
// profile has a write-ahead log that is not empty.
function firefoxHistoryUrl(titles) {
  const sql =
    "SELECT last_visit_date, url, title FROM moz_places WHERE title IN (" +
    titles.map(sqlQuote).join(", ") +
    ") ORDER BY last_visit_date DESC LIMIT 1";
  const command = [
    'dir="$(mktemp -d)" || exit 1',
    'sep="$(printf "\\037")"',
    'for p in "$HOME/Library/Application Support/Firefox/Profiles/"*/; do',
    '  [ -s "$p/places.sqlite-wal" ] || continue',
    '  cp "$p/places.sqlite" "$dir/p.sqlite" && cp "$p/places.sqlite-wal" "$dir/p.sqlite-wal" &&',
    `  /usr/bin/sqlite3 -readonly -separator "$sep" "$dir/p.sqlite" ${shellQuote(sql)}`,
    '  rm -f "$dir"/p.sqlite*',
    "done",
    'rm -rf "$dir"',
  ].join("\n");

  const app = Application.currentApplication();
  app.includeStandardAdditions = true;
  let output;
  try {
    output = app.doShellScript(command);
  } catch (e) {
    throw new Error(`cannot read the Firefox history: ${e.message}`);
  }
  let best = null;
  output.split(/[\r\n]+/).forEach((line) => {
    const [visit, url, title] = line.split("\x1f");
    if (url && (!best || Number(visit) > Number(best.visit))) {
      best = { visit, url, title };
    }
  });
  return best;
}

// Firefox gives the window title with AppleScript, but not the URL, so the
// script finds the URL in the Firefox history. A private window has no
// history.
function firefoxTab(bundleId) {
  const app = Application(bundleId);
  if (!app.windows.length) {
    throw new Error("Firefox has no open window");
  }
  const windowTitle = app.windows[0].name();
  const titles = [windowTitle];
  [FIREFOX_SUFFIX_RE, PROFILE_SUFFIX_RE].forEach((re) => {
    const title = windowTitle.replace(re, "");
    if (title && !titles.includes(title)) {
      titles.push(title);
    }
  });
  const found = firefoxHistoryUrl(titles);
  if (!found) {
    throw new Error(`the Firefox history has no page with the title "${titles[titles.length - 1]}"`);
  }
  return { title: found.title, url: found.url };
}

function pageTab(browser) {
  const bundleId = browser ? BROWSER_NAMES[browser.toLowerCase()] || browser : frontBundleId();
  if (SAFARI_IDS.includes(bundleId)) {
    return safariTab(bundleId);
  }
  if (CHROME_IDS.includes(bundleId)) {
    return chromeTab(bundleId);
  }
  if (FIREFOX_IDS.includes(bundleId)) {
    return firefoxTab(bundleId);
  }
  throw new Error(`the front app is not Firefox, Safari, or Chrome: ${bundleId}`);
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

// A Markdown link target ends at a space or an unpaired parenthesis.
function escapeMarkdownUrl(url) {
  return url.replace(/ /g, "%20").replace(/\(/g, "%28").replace(/\)/g, "%29");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function makeLinks(browser) {
  const tab = pageTab(browser);
  if (!/^[a-z][a-z0-9+.-]*:/i.test(tab.url)) {
    throw new Error(`the page has no URL: "${tab.url}"`);
  }
  const title = tab.title.trim() || tab.url;
  return {
    markdown: `[${escapeMarkdownLinkText(title)}](${escapeMarkdownUrl(tab.url)})`,
    html: `<a href="${escapeHtml(tab.url)}">${escapeHtml(title)}</a>`,
  };
}

function copyLinks(links, mode) {
  const pasteboard = $.NSPasteboard.generalPasteboard;
  pasteboard.clearContents;
  if (mode === "html") {
    pasteboard.setStringForType($(links.html), $("public.html"));
  }
  pasteboard.setStringForType($(links.markdown), $("public.utf8-plain-text"));
}

function run(argv) {
  const mode = typeof PAGE_LINK_MODE === "undefined" ? argv[0] : PAGE_LINK_MODE;
  const browser = typeof PAGE_LINK_MODE === "undefined" ? argv[1] || "" : "";
  try {
    const links = makeLinks(browser);
    copyLinks(links, mode);
    return links.markdown;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
