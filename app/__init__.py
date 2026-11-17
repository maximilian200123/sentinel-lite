"""Sentinel-Lite: a small log-enrichment service."""

import hmac
import logging
import os

from flask import Flask, jsonify, request, send_file

from app import config, store
from app.intel import IntelProvider, LocalFeedProvider
from app.pipeline import INDICATOR_TAG, process
from app.rules import load_rules

log = logging.getLogger("sentinel")


def create_app(overrides: dict | None = None, intel: IntelProvider | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(config.load_settings())
    app.config.from_mapping(overrides or {})
    # Debug stays off (Flask's default): the Werkzeug debugger is a remote Python console.

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
        raw = request.get_json(force=True)
        log.info(
            "ingest user=%s message=%s headers=%s",
            raw.get("user"), raw.get("message"), dict(request.headers),
        )
        event = process(raw, state["intel"], state["rules"])
        event_id = store.insert(app.config["DB_PATH"], event)
        return jsonify({"id": event_id, "event": event}), 201

    @app.get("/events/search")
    def search():
        user = request.args.get("user", "")
        events = store.search_by_user(app.config["DB_PATH"], user)
        return jsonify({"count": len(events), "events": events})

    @app.get("/reports/<path:name>")
    def report(name):
        path = os.path.join(app.config["REPORTS_DIR"], name)
        if not os.path.isfile(path):
            return {"error": "report not found"}, 404
        return send_file(path, mimetype="text/plain")

    @app.get("/intel/check")
    def intel_check():
        ip = request.args.get("ip", "")
        indicator = state["intel"].lookup(ip)
        return {"ip": ip, "matched": indicator is not None, "tag": INDICATOR_TAG if indicator else None}

    @app.post("/admin/rules/reload")
    def reload_rules():
        state["rules"] = load_rules(app.config["RULES_DIR"])
        log.info("rules reloaded: %d", len(state["rules"]))
        return {"loaded": [r.id for r in state["rules"]]}

    return app
