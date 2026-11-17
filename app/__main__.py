"""Entry point: python -m app (bound to 127.0.0.1 only)."""

import logging

from app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = create_app()
app.run(host=app.config["HOST"], port=app.config["PORT"])
