"""Redirect solo su path interno (niente open-redirect)."""
from flask import redirect, request


def redirect_interno(default_url: str):
    nxt = (request.form.get("next") or request.args.get("next") or "").strip()
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect(default_url)
