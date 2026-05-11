"""Log di diagnostica: attivi solo con app.debug (Flask development)."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def configure_dev_debug_logging(app: Flask) -> None:
    if not app.debug:
        return
    log = app.logger
    log.setLevel(logging.DEBUG)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        log.addHandler(h)
        log.propagate = False
    else:
        for h in log.handlers:
            h.setLevel(logging.DEBUG)


def dlog(app: Flask, msg: str, *args) -> None:
    if app.debug:
        app.logger.debug(msg, *args)
