"""Text reports written to reports/. Run: python -m app.reports"""

from datetime import UTC, datetime
from pathlib import Path

from app import config, store


def write_summary(db_path: str, reports_dir: str) -> Path:
    s = store.summary(db_path)
    lines = [
        "Sentinel-Lite summary",
        f"generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"events stored: {s['total']}",
        f"high-risk events (score >= 50): {s['high_risk']}",
        "top sources by risk:",
        *[f"  {ip}  {score}" for ip, score in s["top_sources"]],
    ]
    path = Path(reports_dir) / "summary.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    settings = config.load_settings()
    store.init(settings["DB_PATH"])
    print(write_summary(settings["DB_PATH"], settings["REPORTS_DIR"]))
