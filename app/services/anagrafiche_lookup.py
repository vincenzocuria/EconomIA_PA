"""Ricerca incrementale anagrafiche."""

from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_testo import normalizza_chiave, normalizza_nome_persona
from app.services.ricerca_completa import applica_ricerca, token_ricerca
from app.services.responsabile_da_ufficio import responsabile_per_ufficio


def _limite(limit: int) -> int:
    return max(1, min(int(limit or 15), 30))


def cerca_richiedenti(q: str | None, limit: int = 15) -> list[dict]:
    lim = _limite(limit)
    query = AnagraficaRichiedente.query
    query = applica_ricerca(query, AnagraficaRichiedente.nome, q=q)
    rows = query.order_by(AnagraficaRichiedente.nome).limit(lim).all()
    out = []
    visti = set()
    for r in rows:
        chiave = r.nome_norm or normalizza_chiave(r.nome)
        visti.add(chiave)
        uff = r.ufficio_default or ""
        out.append(
            {
                "id": r.id,
                "label": r.nome,
                "ufficio": uff,
                "responsabile": responsabile_per_ufficio(uff),
                "hint": uff,
            }
        )
    # Responsabili in anagrafica uffici non ancora presenti come richiedenti
    if token_ricerca(q) and len(out) < lim:
        q_uff = AnagraficaUfficio.query
        q_uff = applica_ricerca(q_uff, AnagraficaUfficio.responsabile, q=q)
        for u in q_uff.order_by(AnagraficaUfficio.responsabile).limit(lim).all():
            nome = normalizza_nome_persona(u.responsabile)
            if not nome:
                continue
            chiave = normalizza_chiave(nome)
            if chiave in visti:
                continue
            visti.add(chiave)
            out.append(
                {
                    "id": None,
                    "label": nome,
                    "ufficio": u.denominazione or "",
                    "responsabile": nome,
                    "hint": u.denominazione or "",
                }
            )
            if len(out) >= lim:
                break
    return out[:lim]


def cerca_uffici(q: str | None, limit: int = 15) -> list[dict]:
    query = AnagraficaUfficio.query
    query = applica_ricerca(
        query,
        AnagraficaUfficio.denominazione,
        AnagraficaUfficio.responsabile,
        q=q,
    )
    rows = query.order_by(AnagraficaUfficio.denominazione).limit(_limite(limit)).all()
    return [
        {
            "id": r.id,
            "label": r.denominazione,
            "responsabile": r.responsabile or "",
            "hint": r.responsabile or "",
        }
        for r in rows
    ]


def item_beneficiario(row: AnagraficaBeneficiario) -> dict:
    return {
        "id": row.id,
        "label": row.denominazione,
        "cf_piva": row.cf_piva or "",
        "hint": row.cf_piva or "",
    }


def cerca_beneficiari(q: str | None, limit: int = 15) -> list[dict]:
    query = AnagraficaBeneficiario.query
    query = applica_ricerca(
        query,
        AnagraficaBeneficiario.denominazione,
        AnagraficaBeneficiario.cf_piva,
        q=q,
    )
    rows = query.order_by(AnagraficaBeneficiario.denominazione).limit(_limite(limit)).all()
    return [item_beneficiario(r) for r in rows]
