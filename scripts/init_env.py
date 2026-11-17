"""Create .env with a fresh random API key if it does not exist yet (run by make setup).

.env is gitignored and stays on this machine. The key is generated per install, so no
two clones share one and no key ever needs to be written into the repository.
"""

import secrets
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"

if ENV.exists():
    print(".env exists, leaving it unchanged")
else:
    ENV.write_text(f"SENTINEL_API_KEY=sl_api_{secrets.token_urlsafe(24)}\n", encoding="utf-8")
    print(".env created with a new random SENTINEL_API_KEY")
