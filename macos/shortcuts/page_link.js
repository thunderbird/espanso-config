// Copy a link to the current web page, with the page title as link text.
//
// Usage: osascript -l JavaScript page_link.js markdown|html [browser]
//
// Gets the title and URL of the front tab of the front app, or of the
// browser that you give, for example "Safari", "Google Chrome", or
// "Firefox". Safari and Chrome give the title and URL with AppleScript.
// Firefox gives only the window title, so the script presses Command-L and
// Command-C to copy the URL, and Escape to close the address bar. This needs
// Accessibility permission.
//
// In markdown mode, the script copies `[title](url)`. In html mode, it copies
// `<a href="url">title</a>` with the Markdown link as plain text, so that
// Command-V pastes a rich text link. The script prints the Markdown link. On
// error, the script prints "Error: <message>" and does not change the
// clipboard, except that the Firefox URL copy replaces it.
//
// build_shortcuts.py puts this file in single quotes in a shell script, so
// do not use single quotes here.

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
// Firefox adds the browser name to the window title, for example
// "Title — Mozilla Firefox" or "Title — Firefox Nightly Private Browsing".
const FIREFOX_SUFFIX_RE =
  /\s+[—–-]\s+(?:Mozilla Firefox|Firefox(?: Developer Edition| Nightly)?)(?: Private Browsing)?$/;
const MODIFIER_WAIT_SECONDS = 3;

function frontBundleId() {
  const process = Application("System Events").processes.whose({ frontmost: true })[0];
  return process.bundleIdentifier();
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

// The Quick Action starts while the person still holds Control-Command. A
// keystroke then gets these keys too, so wait until they are released.
function waitForModifierRelease() {
  const mask =
    $.NSEventModifierFlagCommand |
    $.NSEventModifierFlagControl |
    $.NSEventModifierFlagShift |
    $.NSEventModifierFlagOption;
  const end = Date.now() + MODIFIER_WAIT_SECONDS * 1000;
  while ($.NSEvent.modifierFlags & mask) {
    if (Date.now() > end) {
      throw new Error("release the keys of the keyboard shortcut");
    }
    delay(0.05);
  }
}

function firefoxTab(bundleId) {
  const events = Application("System Events");
  const process = events.processes.whose({ bundleIdentifier: bundleId })[0];
  if (!process.windows.length) {
    throw new Error("Firefox has no open window");
  }
  const title = process.windows[0].name().replace(FIREFOX_SUFFIX_RE, "");

  waitForModifierRelease();
  Application(bundleId).activate();
  const pasteboard = $.NSPasteboard.generalPasteboard;
  pasteboard.clearContents;
  events.keystroke("l", { using: "command down" });
  delay(0.2);
  events.keystroke("c", { using: "command down" });
  let url = "";
  for (let i = 0; i < 20 && !url; i++) {
    delay(0.05);
    url = ObjC.unwrap(pasteboard.stringForType($("public.utf8-plain-text"))) || "";
  }
  // Escape closes the address bar suggestions and then shows the URL again.
  events.keyCode(53);
  events.keyCode(53);
  return { title, url: url.trim() };
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
  const [mode, browser = ""] = argv;
  try {
    const links = makeLinks(browser);
    copyLinks(links, mode);
    return links.markdown;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
