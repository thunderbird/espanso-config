; Turn a GitHub issue URL into a link with the issue title. links.ahk
; includes this file with markup.ahk and web.ahk, and
; tests/test_github_link_ahk.py tests it.
;
; Gives `[repo #number: title](url)`, with the title from the GitHub API.
; The rules are the same as in macos/shortcuts/github_link.js and
; scripts/gh_issue_link.py. A token gives access to private repositories
; and a higher rate limit. The script uses GITHUB_TOKEN, GH_TOKEN, or
; `gh auth token`, in that order.

#Requires AutoHotkey v2.0

; Returns {markdown, html}. Throws an Error on failure.
GitHubLinks(text) {
    issue := ParseGitHubIssueUrl(text)
    return GitHubLinksFromIssue(issue, FetchGitHubIssue(issue))
}

; Returns {owner, repo, number}. Throws an Error if the text is not an issue URL.
ParseGitHubIssueUrl(text) {
    if !RegExMatch(Trim(text, " `t`r`n"), "^https?://(?:www\.)?github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9._-]+)/issues/(\d+)(?:[/?#].*)?$", &m)
        throw Error('Select or copy a GitHub issue URL. The text was: "' ShownText(text) '"')
    return {owner: m[1], repo: m[2], number: m[3]}
}

; data is the issue JSON as a Map.
GitHubLinksFromIssue(issue, data) {
    title := data is Map ? data.Get("title", "") : ""
    if title = ""
        throw Error("The GitHub API response for " issue.owner "/" issue.repo "#" issue.number " has no title.")
    url := data.Get("html_url", "")
    if url = ""
        url := "https://github.com/" issue.owner "/" issue.repo "/issues/" issue.number
    ; A transferred issue has a new repo and number, so label it from html_url.
    repo := issue.repo, issueNumber := issue.number
    try {
        moved := ParseGitHubIssueUrl(url)
        repo := moved.repo, issueNumber := moved.number
    }
    return MakeLinks(repo " #" issueNumber ": " title, url)
}

FetchGitHubIssue(issue) {
    headers := Map(
        "Accept", "application/vnd.github+json",
        "X-GitHub-Api-Version", "2022-11-28",
        "User-Agent", "espanso-gh-issue-link",
    )
    token := GitHubToken()
    if token != ""
        headers["Authorization"] := "Bearer " token
    response := HttpGet("https://api.github.com/repos/" issue.owner "/" issue.repo "/issues/" issue.number, headers)
    if response.status != 200 {
        hint := token = "" ? " Without a token, only public repositories work. Install the GitHub CLI and run gh auth login." : ""
        throw Error("The GitHub API returned HTTP " response.status " for " issue.owner "/" issue.repo "#" issue.number "." hint)
    }
    try
        return JsonParse(response.body)
    catch
        throw Error("The GitHub API returned invalid JSON.")
}

; Returns the token, or "" if there is none. Keeps a token from gh, because
; gh takes some time to start.
GitHubToken() {
    static ghToken := ""
    for name in ["GITHUB_TOKEN", "GH_TOKEN"] {
        if (token := EnvGet(name)) != ""
            return token
    }
    if ghToken != ""
        return ghToken
    gh := A_ProgramFiles "\GitHub CLI\gh.exe"
    if !FileExist(gh)
        gh := "gh"  ; On the PATH, or not installed.
    ; gh is a console program. A hidden cmd window keeps its output in a file.
    out := A_Temp "\links-ahk-gh-" DllCall("GetCurrentProcessId") ".txt"
    try {
        RunWait(A_ComSpec ' /c ""' gh '" auth token > "' out '" 2>nul"', , "Hide")
        ghToken := Trim(FileRead(out, "UTF-8"), " `t`r`n")
    } catch {
        ghToken := ""
    }
    try FileDelete(out)
    if !(ghToken ~= "^[A-Za-z0-9_]+$")
        ghToken := ""
    return ghToken
}
