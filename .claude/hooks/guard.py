"""Claude Code PreToolUse hook (B-10, R-01, R-02, R-03).

Claude Code sends the pending tool call as JSON on stdin. Exit code 2 blocks the call
and shows stderr to the agent. Exit 0 lets it through. Standard library only, so it
runs with any Python 3.

Blocks, for the agent, what CLAUDE.md and memory can only ask for:
- git push to main, force pushes, deleting remote branches;
- skipping or redirecting git hooks (--no-verify, core.hooksPath);
- reading or editing secret material (.env, secrets/, private keys, gh's config, gh auth token);
- editing the agent's own guardrails (.claude/settings*.json, .claude/hooks/).
"""

import json
import re
import shlex
import subprocess
import sys

SECRET_PATH = re.compile(
    r"(?<![\w.-])\.env(?!\.example)(?![\w-])"   # .env, .env.local; not .env.example
    r"|(?<![\w-])secrets[/\\]"
    r"|\.(pem|key|p12|pfx)\b|id_(rsa|ed25519|ecdsa)\b"
    r"|gh-config|\bgh\s+auth\s+token\b",
    re.I,
)
GUARDRAIL_PATH = re.compile(r"\.claude[/\\](settings[\w.]*\.json|hooks[/\\])", re.I)
WRITE_VERB = re.compile(r"(^|\s)(rm|mv|cp|tee|truncate|chmod|sed\s+-i|Set-Content|Out-File|Remove-Item)\b|>",
                        re.I)
FORCE_FLAGS = {"--force", "-f", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "-d"}
FILE_TOOLS = {"Read", "Edit", "MultiEdit", "Write", "NotebookEdit", "Grep", "Glob"}


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, each as a token list."""
    out = []
    for part in re.split(r"&&|\|\||[;|\n]", command):
        try:
            tokens = shlex.split(part, posix=True)
        except ValueError:
            tokens = part.split()
        if tokens:
            out.append(tokens)
    return out


def git_subcommand(tokens: list[str]) -> tuple[str | None, list[str]]:
    """('push', args) for `git [-C dir] [-c k=v] push args`, else (None, [])."""
    if not tokens or tokens[0] not in {"git", "git.exe"}:
        return None, []
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i].startswith("-c") and "core.hookspath" in " ".join(tokens[i:i + 2]).lower():
            return "hookspath", []
        i += 2 if tokens[i] in {"-C", "-c"} else 1
    return (tokens[i], tokens[i + 1:]) if i < len(tokens) else (None, [])


def current_branch(cwd: str | None) -> str:
    try:
        return subprocess.run(["git", "branch", "--show-current"], cwd=cwd or None,
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def check_push(args: list[str], cwd: str | None) -> str | None:
    flags = [a for a in args if a.startswith("-")]
    if any(f.split("=")[0] in FORCE_FLAGS for f in flags):
        return "force push / remote branch deletion is blocked; push a new commit instead"
    refspecs = [a for a in args if not a.startswith("-")][1:]  # first positional is the remote
    if any(r.startswith("+") for r in refspecs):
        return "force push (+refspec) is blocked"
    if any(re.search(r"(^|:)(refs/heads/)?main$", r) for r in refspecs):
        return "pushing to main is blocked; open a pull request"
    if not refspecs and current_branch(cwd) == "main":
        return "pushing while on main is blocked; switch to a branch and open a pull request"
    return None


def check_bash(command: str, cwd: str | None) -> str | None:
    if SECRET_PATH.search(command):
        return "command touches secret material (.env, secrets/, keys, gh credentials)"
    if GUARDRAIL_PATH.search(command) and WRITE_VERB.search(command):
        return "the agent may not modify its own guardrails in .claude/"
    for tokens in segments(command):
        sub, args = git_subcommand(tokens)
        if sub == "hookspath" or (sub == "config" and any("hookspath" in a.lower() for a in args)):
            return "changing core.hooksPath would switch off the git hooks"
        if sub in {"commit", "push", "merge", "rebase", "am"} and ("--no-verify" in args or
                                                                   (sub == "commit" and "-n" in args)):
            return "--no-verify skips the git hooks; fix what the hook reports instead"
        if sub == "push" and (reason := check_push(args, cwd)):
            return reason
    return None


def check_file_tool(tool: str, tool_input: dict) -> str | None:
    target = str(tool_input.get("file_path") or tool_input.get("notebook_path")
                 or tool_input.get("path") or "")
    if SECRET_PATH.search(target.replace("\\", "/")):
        return f"{tool} on secret material is blocked: {target}"
    if tool != "Read" and tool in FILE_TOOLS and GUARDRAIL_PATH.search(target):
        return "the agent may not modify its own guardrails in .claude/"
    return None


def main() -> int:
    try:
        call = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("guard: unreadable hook input, blocking to fail closed", file=sys.stderr)
        return 2
    tool, tool_input = call.get("tool_name", ""), call.get("tool_input") or {}
    if tool == "Bash":
        reason = check_bash(str(tool_input.get("command", "")), call.get("cwd"))
    elif tool in FILE_TOOLS:
        reason = check_file_tool(tool, tool_input)
    else:
        reason = None
    if reason:
        print(f"Blocked by .claude/hooks/guard.py: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
