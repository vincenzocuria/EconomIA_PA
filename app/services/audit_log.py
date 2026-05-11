import json
from typing import Any

from flask_login import current_user

from app.extensions import db
from app.models.audit import AuditLog


def scrivi_audit(entita: str, entita_id: int | None, azione: str, dettaglio: Any = None) -> None:
    uid = current_user.id if current_user.is_authenticated else None
    testo = ""
    if dettaglio is not None:
        if isinstance(dettaglio, str):
            testo = dettaglio
        else:
            testo = json.dumps(dettaglio, ensure_ascii=False, default=str)
    row = AuditLog(entita=entita, entita_id=entita_id, azione=azione, dettaglio=testo, user_id=uid)
    db.session.add(row)
