"""Eliminazione anagrafiche (richiedenti, uffici, fornitori)."""

from typing import Any

from app.extensions import db
from app.services.audit_log import scrivi_audit


def elimina_riga(row, *, entita: str, dettaglio: Any = None) -> None:
    ident = row.id
    scrivi_audit(entita, ident, "eliminazione", dettaglio)
    db.session.delete(row)
    db.session.commit()
