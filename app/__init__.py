"""Sentinel-Lite: a small log-enrichment service."""

import hmac
import logging
import re
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from app import config, logsafe, store
from app.intel import IntelProvider, LocalFeedProvider
from app.pipeline import INDICATOR_TAG, InvalidEvent, process
from app.rules import RuleError, load_rules

log = logging.getLogger("sentinel")
REPORT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.txt")


def create_app(overrides: dict | None = None, intel: IntelProvider | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(config.load_settings())
    app.config.from_mapping(overrides or {})
    # Debug stays off (Flask's default): the Werkzeug debugger is a remote Python console.

    logsafe.install(log, [app.config["API_KEY"]])
    store.init(app.config["DB_PATH"])
    state = {
        "intel": intel or LocalFeedProvider(app.config["INTEL_FEED"]),
        "rules": load_rules(app.config["RULES_DIR"]),
    }

    @app.before_request
    def require_api_key():
        """Every endpoint except /health needs X-API-Key. No key configured means no access."""
        if request.endpoint == "health":
            return None
        expected = app.config["API_KEY"] or ""
        supplied = request.headers.get("X-API-Key", "")
        if not expected or not hmac.compare_digest(supplied.encode(), expected.encode()):
            return {"error": "missing or invalid API key"}, 401
        return None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ingest")
    def ingest():
        raw = request.get_json(silent=True)  # None for a non-JSON body or content type
        try:
            event = process(raw, state["intel"], state["rules"])
        except InvalidEvent as exc:
            return {"error": f"invalid event: {exc}"}, 400
        log.info("ingest user=%s src_ip=%s message=%s",
                 event["user"]["name"], event["source"]["ip"], event["message"])
        event_id = store.insert(app.config["DB_PATH"], event)
        return jsonify({"id": event_id, "event": event}), 201

    @app.get("/events/search")
    def search():
        user = request.args.get("user", "")
        events = store.search_by_user(app.config["DB_PATH"], user)
        return jsonify({"count": len(events), "events": events})

    @app.get("/reports/<name>")
    def report(name):
        # One plain file name, no separators or dots-only names, served only from REPORTS_DIR.
        reports_dir = Path(app.config["REPORTS_DIR"]).resolve()
        path = (reports_dir / name).resolve()
        if not REPORT_NAME.fullmatch(name) or path.parent != reports_dir or not path.is_file():
            return {"error": "report not found"}, 404
        return send_from_directory(reports_dir, name, mimetype="text/plain")

    @app.get("/intel/check")
    def intel_check():
        ip = request.args.get("ip", "")
        indicator = state["intel"].lookup(ip)
        return {"ip": ip, "matched": indicator is not None, "tag": INDICATOR_TAG if indicator else None}

    @app.post("/admin/rules/reload")
    def reload_rules():
        try:
            rules = load_rules(app.config["RULES_DIR"])
        except RuleError as exc:
            log.warning("rules reload refused, keeping %d active rules: %s", len(state["rules"]), exc)
            return {"error": str(exc)}, 400
        state["rules"] = rules
        log.info("rules reloaded: %d", len(rules))
        return {"loaded": [r.id for r in rules]}

    return app
