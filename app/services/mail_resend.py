"""Invio email di notifica tramite Resend."""

import json
import os
import urllib.error
import urllib.request

_MITTENTE_PROVA = "Lidia <onboarding@resend.dev>"
_API = "https://api.resend.com/emails"


def mail_attiva() -> bool:
    return bool(os.environ.get("RESEND_API_KEY", "").strip())


def mittente_resend() -> str:
    return (os.environ.get("RESEND_FROM") or "").strip() or _MITTENTE_PROVA


def invia_email(destinatari: list[str], oggetto: str, corpo: str) -> tuple[bool, str]:
    """Ritorna (inviata, messaggio per l'operatore)."""
    chiave = os.environ.get("RESEND_API_KEY", "").strip()
    if not chiave:
        return False, "Resend non configurato (RESEND_API_KEY nel file .env)."
    if not destinatari:
        return False, "Nessun destinatario: indica l'email dell'economo o i destinatari della chiusura."
    payload = json.dumps(
        {
            "from": mittente_resend(),
            "to": destinatari,
            "subject": oggetto,
            "text": corpo,
        }
    ).encode("utf-8")
    richiesta = urllib.request.Request(
        _API,
        data=payload,
        headers={
            "Authorization": f"Bearer {chiave}",
            "Content-Type": "application/json",
            "User-Agent": "EconomIA_PA",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=20) as risposta:
            risposta.read()
    except urllib.error.HTTPError as exc:
        dettaglio = exc.read().decode("utf-8", errors="replace")[:300]
        return False, f"Resend ha rifiutato l'invio ({exc.code}): {dettaglio}"
    except urllib.error.URLError as exc:
        return False, f"Invio non riuscito: {exc.reason}"
    return True, f"Inviata con Resend a {', '.join(destinatari)}."
