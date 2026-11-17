"""Log hygiene for the 'sentinel' logger (B-07): one event per line, no secrets."""

import logging
import re

CONTROL = re.compile(r"[\x00-\x1f\x7f]")
KEY_FORMAT = re.compile(r"sl_api_[A-Za-z0-9_\-]{8,}")


class SafeLogFilter(logging.Filter):
    """Renders the message, escapes CR/LF and other control characters so user input
    cannot start a forged log line, and redacts API keys (the configured one and any
    value in the sl_api_ format)."""

    def __init__(self, secrets: list[str]):
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in self._secrets:
            message = message.replace(secret, "[REDACTED]")
        message = KEY_FORMAT.sub("[REDACTED]", message)
        record.msg = CONTROL.sub(lambda m: f"\\x{ord(m.group()):02x}", message)
        record.args = None
        return True


def install(logger: logging.Logger, secrets: list[str]) -> None:
    for old in [f for f in logger.filters if isinstance(f, SafeLogFilter)]:
        logger.removeFilter(old)
    logger.addFilter(SafeLogFilter(secrets))
