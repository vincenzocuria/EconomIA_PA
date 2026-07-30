"""Ricerca incrementale anagrafiche."""

from sqlalchemy import or_

from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_testo import pulisci_testo


def _limite(limit: int) -> int:
    return max(1, min(int(limit or 15), 30))


def cerca_richiedenti(q: str | None, limit: int = 15) -> list[dict]:
    testo = pulisci_testo(q)
    query = AnagraficaRichiedente.query
    if testo:
        like = f"%{testo}%"
        query = query.filter(AnagraficaRichiedente.nome.ilike(like))
    rows = query.order_by(AnagraficaRichiedente.nome).limit(_limite(limit)).all()
    return [
        {
            "id": r.id,
            "label": r.nome,
            "ufficio": r.ufficio_default or "",
        }
        for r in rows
    ]


def cerca_uffici(q: str | None, limit: int = 15) -> list[dict]:
    testo = pulisci_testo(q)
    query = AnagraficaUfficio.query
    if testo:
        like = f"%{testo}%"
        query = query.filter(AnagraficaUfficio.denominazione.ilike(like))
    rows = query.order_by(AnagraficaUfficio.denominazione).limit(_limite(limit)).all()
    return [{"id": r.id, "label": r.denominazione} for r in rows]


def cerca_beneficiari(q: str | None, limit: int = 15) -> list[dict]:
    testo = pulisci_testo(q)
    query = AnagraficaBeneficiario.query
    if testo:
        like = f"%{testo}%"
        query = query.filter(
            or_(
                AnagraficaBeneficiario.denominazione.ilike(like),
                AnagraficaBeneficiario.cf_piva.ilike(like),
            )
        )
    rows = query.order_by(AnagraficaBeneficiario.denominazione).limit(_limite(limit)).all()
    return [
        {
            "id": r.id,
            "label": r.denominazione,
            "cf_piva": r.cf_piva or "",
            "hint": r.cf_piva or "",
        }
        for r in rows
    ]
