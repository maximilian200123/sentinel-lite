"""Regression tests for repository-level bugs B-08 to B-10, plus the size budget."""

import json
import re
import subprocess
import sys

import pytest
import yaml
from conftest import ROOT

# B-08: dependencies --------------------------------------------------------------

# Lowest version without a published advisory, from pip-audit on the baseline
# (see docs/evidence/pip-audit-baseline.txt).
FIXED_IN = {"requests": (2, 33, 0)}
MAX_RUNTIME_DEPS = 4


def _requirements() -> list[str]:
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return [ln.split("#")[0].strip() for ln in lines if ln.split("#")[0].strip()]


def test_runtime_dependency_budget():
    assert len(_requirements()) <= MAX_RUNTIME_DEPS


@pytest.mark.seeded("B-08")
def test_b08_runtime_dependencies_are_pinned():
    unpinned = [r for r in _requirements() if not re.fullmatch(r"[A-Za-z0-9_.\-]+==[0-9][\w.]*", r)]
    assert unpinned == []


@pytest.mark.seeded("B-08")
def test_b08_no_dependency_below_fixed_version():
    pins = dict(r.lower().split("==") for r in _requirements() if "==" in r)
    for name, fixed in FIXED_IN.items():
        version = tuple(int(p) for p in pins[name].split(".")[:3])
        assert version >= fixed, f"{name} {pins[name]} has known advisories"


# B-09: CI workflows --------------------------------------------------------------

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))


def _workflow(path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["on"] = doc.pop(True, doc.get("on"))  # YAML 1.1 reads the bare key `on` as True
    return doc


def _uses(doc) -> list[str]:
    return [s["uses"] for job in doc["jobs"].values() for s in job.get("steps", []) if "uses" in s]


@pytest.mark.seeded("B-09")
@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_b09_third_party_actions_pinned_to_commit_sha(path):
    unpinned = [
        u for u in _uses(_workflow(path))
        if not u.startswith("./") and not re.fullmatch(r"[\w.\-/]+@[0-9a-f]{40}", u)
    ]
    assert unpinned == []


@pytest.mark.seeded("B-09")
@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_b09_default_permissions_are_read_only(path):
    perms = _workflow(path).get("permissions")
    assert isinstance(perms, dict), "workflow must declare an explicit permissions: block"
    assert set(perms.values()) <= {"read", "none"}


@pytest.mark.seeded("B-09")
@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_b09_no_pull_request_target(path):
    triggers = _workflow(path)["on"]
    names = [triggers] if isinstance(triggers, str) else list(triggers)
    assert "pull_request_target" not in names


# B-10: AI agent guardrails -------------------------------------------------------

HOOK = ROOT / ".claude" / "hooks" / "guard.py"
SETTINGS = ROOT / ".claude" / "settings.json"


def _hook(tool: str, tool_input: dict) -> int:
    assert HOOK.is_file(), "PreToolUse hook script is missing"
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, check=False
    ).returncode


BLOCKED = [
    ("Bash", {"command": "git push origin main"}),
    ("Bash", {"command": "git push origin HEAD:main"}),
    ("Bash", {"command": "git push --force origin feat/b-02"}),
    ("Bash", {"command": "git push -f"}),
    ("Bash", {"command": "git push origin +feat/b-02"}),
    ("Bash", {"command": "git commit --no-verify -m wip"}),
    ("Bash", {"command": "cat .env"}),
    ("Bash", {"command": "type secrets\\prod.key"}),
    ("Read", {"file_path": "C:/work/sentinel-lite/.env"}),
    ("Read", {"file_path": "/work/sentinel-lite/secrets/age.key"}),
]
ALLOWED = [
    ("Bash", {"command": "git push -u origin fix/b-02-sql-injection"}),
    ("Bash", {"command": "make check"}),
    ("Read", {"file_path": "/work/sentinel-lite/.env.example"}),
    ("Read", {"file_path": "/work/sentinel-lite/app/config.py"}),
]


@pytest.mark.seeded("B-10")
@pytest.mark.parametrize("tool,tool_input", BLOCKED, ids=[str(b[1]) for b in BLOCKED])
def test_b10_hook_blocks_dangerous_agent_action(tool, tool_input):
    assert _hook(tool, tool_input) == 2


@pytest.mark.seeded("B-10")
@pytest.mark.parametrize("tool,tool_input", ALLOWED, ids=[str(a[1]) for a in ALLOWED])
def test_b10_hook_allows_normal_work(tool, tool_input):
    assert _hook(tool, tool_input) == 0


@pytest.mark.seeded("B-10")
def test_b10_settings_wire_deny_rules_and_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    deny = settings["permissions"]["deny"]
    for needle in ("git push origin main", "--force", ".env"):
        assert any(needle in rule for rule in deny), f"no deny rule covers {needle!r}"
    hooks = settings["hooks"]["PreToolUse"]
    assert any("guard.py" in h["command"] for entry in hooks for h in entry["hooks"])


# Instructions that would switch off a control. A line that negates them is fine.
POISON = re.compile(r"push (straight|directly) to main|skip (the )?tests|--no-verify", re.I)
NEGATION = re.compile(r"\b(never|not|don't|do not|refuse|block)\b", re.I)


@pytest.mark.seeded("B-10")
def test_b10_agent_context_has_no_instruction_to_bypass_controls():
    files = [ROOT / "CLAUDE.md", *(ROOT / "memory").glob("*.md"), *(ROOT / "skills").rglob("*.md")]
    hits = [
        f"{f.relative_to(ROOT)}: {line.strip()}"
        for f in files if f.is_file()
        for line in f.read_text(encoding="utf-8").splitlines()
        if POISON.search(line) and not NEGATION.search(line)
    ]
    assert hits == []


@pytest.mark.seeded("B-10")
def test_b10_hook_blocks_bare_push_while_on_main(tmp_path):
    assert HOOK.is_file(), "PreToolUse hook script is missing"
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(tmp_path)})
    result = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True,
                            check=False)
    assert result.returncode == 2
