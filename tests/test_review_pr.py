"""The mechanical half of skills/review-pr flags banned patterns, not prose about them."""

import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import review_pr  # noqa: E402


def hits(path, line):
    return [name for name, found in review_pr.scan([(path, line)]).items() if found]


def test_flags_banned_code():
    assert hits("app/store.py", "q = f\"SELECT * FROM events WHERE user = '{u}'\"") == ["String-built SQL"]
    assert hits("app/rules.py", "doc = yaml.load(f, Loader=yaml.Loader)") == ["Unsafe YAML load"]
    assert hits("app/__init__.py", "app.run(host='0.0.0.0')") == ["Bind to all interfaces"]
    assert hits(".github/workflows/ci.yml", "      - uses: actions/checkout@v4") == ["Unpinned action"]
    assert hits("app/config.py", 'API_KEY = "sl_api_abcdefghijklmnop"') == ["Hardcoded secret"]


def test_allows_the_safe_forms():
    assert hits("app/store.py", 'conn.execute("SELECT doc FROM events WHERE user = ?", (u,))') == []
    sha = "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"
    assert hits(".github/workflows/ci.yml", sha) == []


def test_skips_comments_and_markdown():
    assert hits(".github/workflows/ci.yml", "# pull_request_target is never used here") == []
    assert hits("CONTRIBUTING.md", "Never bypass them with --no-verify.") == []
