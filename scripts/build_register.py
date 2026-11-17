"""Build RISK-REGISTER.xlsx and RISK-REGISTER.md from docs/risk-register.yaml.

Usage:
    python scripts/build_register.py          # write both files
    python scripts/build_register.py --check  # fail if the files drift or a rule is broken

The workbook starts from the course template, so its sheets, formulas, data
validations and conditional formatting are kept. Only the data cells of the
Risk Register sheet are written. Inherent and residual scores stay formulas.
"""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "risk-register.yaml"
TEMPLATE = ROOT / "docs" / "templates" / "risk-register-template.xlsx"
XLSX = ROOT / "RISK-REGISTER.xlsx"
MD = ROOT / "RISK-REGISTER.md"

SHEET = "Risk Register"
FIRST_ROW, LAST_ROW = 2, 26  # rows the template prepared with formulas
REGISTERS = {"Operational", "Internal", "External"}
STATUSES = {"Open", "Implemented", "Verified", "Accepted"}
ALL_BUGS = {f"B-{n:02d}" for n in range(1, 11)}

# Column letter -> how to get the cell value from a risk. None = template formula.
COLUMNS = {
    "A": lambda r: r["id"],
    "B": lambda r: r["register"],
    "C": lambda r: r["asset"],
    "D": lambda r: r["threat"],
    "E": lambda r: r["attack"] or None,
    "F": lambda r: (", ".join(r["bugs"]) + ": " if r["bugs"] else "") + r["vulnerability"],
    "G": lambda r: r["likelihood"],
    "H": lambda r: r["impact"],
    "I": None,
    "J": lambda r: r["control"],
    "K": lambda r: r["residual_likelihood"],
    "L": lambda r: r["residual_impact"],
    "M": None,
    "N": lambda r: r["evidence"] or None,
    "O": lambda r: r["owner"],
    "P": lambda r: r["status"],
}
FORMULA = '=IF(AND(ISNUMBER({a}{n}),ISNUMBER({b}{n})),{a}{n}*{b}{n},"")'


def load_risks() -> list[dict]:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["risks"]


def evidence_problems(risk: dict) -> list[str]:
    """Each Evidence item must be a URL or a path that exists, optionally path::test_name."""
    problems = []
    for item in filter(None, (s.strip() for s in risk["evidence"].split(";"))):
        if item.startswith("https://"):
            continue
        path, _, test = item.partition("::")
        target = ROOT / path
        if not target.exists():
            problems.append(f"{risk['id']}: evidence path does not exist: {path}")
        elif test and f"def {test}(" not in target.read_text(encoding="utf-8"):
            problems.append(f"{risk['id']}: test {test} not found in {path}")
    return problems


def validate(risks: list[dict]) -> list[str]:
    problems = []
    if not 8 <= len(risks) <= 10:
        problems.append(f"expected 8 to 10 risks, found {len(risks)}")
    if len(risks) > LAST_ROW - FIRST_ROW + 1:
        problems.append("more risks than template rows")
    for r in risks:
        rid = r["id"]
        if r["register"] not in REGISTERS:
            problems.append(f"{rid}: register {r['register']!r} not in {sorted(REGISTERS)}")
        if r["status"] not in STATUSES:
            problems.append(f"{rid}: status {r['status']!r} not in {sorted(STATUSES)}")
        for key in ("likelihood", "impact", "residual_likelihood", "residual_impact"):
            if not (isinstance(r[key], int) and 1 <= r[key] <= 5):
                problems.append(f"{rid}: {key} must be a whole number 1-5")
        if r["residual_likelihood"] * r["residual_impact"] > r["likelihood"] * r["impact"]:
            problems.append(f"{rid}: residual score is above inherent score")
        if r["status"] in {"Implemented", "Verified"} and not r["evidence"].strip():
            problems.append(f"{rid}: status {r['status']} with empty Evidence")
        problems += evidence_problems(r)
    mapped = {b for r in risks for b in r["bugs"]}
    if missing := ALL_BUGS - mapped:
        problems.append(f"bugs with no register row: {sorted(missing)}")
    if registers := REGISTERS - {r["register"] for r in risks}:
        problems.append(f"registers with no row: {sorted(registers)}")
    return problems


def expected_cells(risks: list[dict]) -> dict[str, object]:
    cells = {}
    for n in range(FIRST_ROW, LAST_ROW + 1):
        risk = risks[n - FIRST_ROW] if n - FIRST_ROW < len(risks) else None
        for col, get in COLUMNS.items():
            if get is None:
                a, b = ("G", "H") if col == "I" else ("K", "L")
                cells[f"{col}{n}"] = FORMULA.format(a=a, b=b, n=n)
            else:
                cells[f"{col}{n}"] = get(risk) if risk else None
    return cells


def score_check(risks: list[dict]) -> list[str]:
    """Evaluate the template formula the way a spreadsheet would and reject errors."""
    problems = []
    for r in risks:
        for a, b, label in (("likelihood", "impact", "inherent"),
                            ("residual_likelihood", "residual_impact", "residual")):
            value = r[a] * r[b]
            if not 1 <= value <= 25:
                problems.append(f"{r['id']}: {label} score {value} outside 1-25")
    return problems


def build_xlsx(risks: list[dict]) -> openpyxl.Workbook:
    wb = openpyxl.load_workbook(TEMPLATE)
    ws = wb[SHEET]
    for ref, value in expected_cells(risks).items():
        ws[ref] = value
    wb.calculation.fullCalcOnLoad = True  # Excel/LibreOffice recompute scores on open
    return wb


def build_md(risks: list[dict]) -> str:
    def band(score: int) -> str:
        return "High" if score >= 15 else "Medium" if score >= 8 else "Low"

    lines = [
        "# Risk register",
        "",
        "Generated from `docs/risk-register.yaml` by `scripts/build_register.py`. "
        "Do not edit by hand. The graded file is `RISK-REGISTER.xlsx`.",
        "",
        "| ID | Register | Asset | Bugs | L x I | Inherent | Res. L x I | Residual | Status | Evidence |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in risks:
        inh = r["likelihood"] * r["impact"]
        res = r["residual_likelihood"] * r["residual_impact"]
        lines.append(
            f"| {r['id']} | {r['register']} | {r['asset']} | {', '.join(r['bugs']) or '-'} "
            f"| {r['likelihood']} x {r['impact']} | {inh} ({band(inh)}) "
            f"| {r['residual_likelihood']} x {r['residual_impact']} | {res} ({band(res)}) "
            f"| {r['status']} | {r['evidence'] or '-'} |"
        )
    lines += ["", "## Threat and control per risk", ""]
    for r in risks:
        lines += [
            f"### {r['id']}, {r['asset']}",
            f"- Threat: {r['threat']}" + (f" ({r['attack']})" if r["attack"] else ""),
            f"- Vulnerability: {r['vulnerability']}",
            f"- Control and why the score drops: {r['control']}",
            "",
        ]
    return "\n".join(lines)


def check_files(risks: list[dict]) -> list[str]:
    problems = []
    if not XLSX.exists():
        return ["RISK-REGISTER.xlsx missing, run make register"]
    ws = openpyxl.load_workbook(XLSX)[SHEET]
    for ref, value in expected_cells(risks).items():
        if ws[ref].value != value:
            problems.append(f"RISK-REGISTER.xlsx {ref} is stale, run make register")
            break
    if any(isinstance(c.value, str) and c.value.startswith("#") for row in ws.iter_rows() for c in row):
        problems.append("RISK-REGISTER.xlsx contains an error value")
    if not MD.exists() or MD.read_text(encoding="utf-8") != build_md(risks):
        problems.append("RISK-REGISTER.md is stale, run make register")
    return problems


def main() -> int:
    risks = load_risks()
    problems = validate(risks) + score_check(risks)
    if "--check" in sys.argv:
        problems += check_files(risks)
    else:
        build_xlsx(risks).save(XLSX)
        MD.write_text(build_md(risks), encoding="utf-8", newline="\n")
    for p in problems:
        print(f"register: {p}")
    if not problems:
        print(f"register: OK, {len(risks)} risks, all bugs mapped")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
