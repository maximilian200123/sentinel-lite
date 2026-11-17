"""The pre-push guard (R-01) in a throwaway git repository."""

import subprocess
import sys

import pytest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import guard_push  # noqa: E402

ZERO = guard_push.ZERO


@pytest.fixture
def repo(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(*args):
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid",
            "commit", "-q", "--allow-empty", *args)
        return git("rev-parse", "HEAD")

    git("init", "-q", "-b", "work")
    first = commit("-m", "a")
    second = commit("-m", "b")
    rewritten = commit("--amend", "-m", "b2")
    monkeypatch.chdir(tmp_path)
    return first, second, rewritten


def test_push_to_main_refused(repo):
    _, second, _ = repo
    assert guard_push.problems([f"refs/heads/work {second} refs/heads/main {ZERO}"])


def test_deleting_main_refused(repo):
    _, second, _ = repo
    assert guard_push.problems([f"(delete) {ZERO} refs/heads/main {second}"])


def test_fast_forward_feature_push_allowed(repo):
    first, second, _ = repo
    assert guard_push.problems([f"refs/heads/work {second} refs/heads/work {first}"]) == []


def test_new_feature_branch_allowed(repo):
    _, second, _ = repo
    assert guard_push.problems([f"refs/heads/work {second} refs/heads/work {ZERO}"]) == []


def test_history_rewrite_refused(repo):
    _, second, rewritten = repo
    assert guard_push.problems([f"refs/heads/work {rewritten} refs/heads/work {second}"])
