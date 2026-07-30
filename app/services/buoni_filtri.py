"""Filtri e ricerca per elenco buoni economali."""

from sqlalchemy import or_

from app.models.buono import BuonoEconomale, StatoBuono
from app.services.anagrafiche_testo import pulisci_testo

STATI_APERTI = (StatoBuono.bozza, StatoBuono.autorizzato, StatoBuono.pagato)
STATI_DA_CHIUDERE = (StatoBuono.autorizzato, StatoBuono.pagato)


def parametri_filtro(args) -> dict:
    q = pulisci_testo(args.get("q"), max_len=120)
    stato = (args.get("stato") or "").strip()
    stati_validi = {e.value for e in StatoBuono}
    if stato and stato not in stati_validi:
        stato = ""
    try:
        sezionale_id = int(args.get("sezionale_id") or 0)
    except (TypeError, ValueError):
        sezionale_id = 0
    rapido = (args.get("rapido") or "").strip()
    if rapido not in ("aperti", "da_chiudere"):
        rapido = ""
    return {
        "q": q,
        "stato": stato,
        "sezionale_id": sezionale_id,
        "rapido": rapido,
    }


def query_buoni(anno: int, filtri: dict):
    q = BuonoEconomale.query.filter_by(anno=anno)
    if filtri.get("sezionale_id"):
        q = q.filter_by(sezionale_id=filtri["sezionale_id"])
    if filtri.get("stato"):
        q = q.filter_by(stato=StatoBuono(filtri["stato"]))
    elif filtri.get("rapido") == "aperti":
        q = q.filter(BuonoEconomale.stato.in_(STATI_APERTI))
    elif filtri.get("rapido") == "da_chiudere":
        q = q.filter(BuonoEconomale.stato.in_(STATI_DA_CHIUDERE))
    testo = filtri.get("q") or ""
    if testo:
        like = f"%{testo}%"
        cond = [
            BuonoEconomale.richiedente.ilike(like),
            BuonoEconomale.ufficio_richiedente.ilike(like),
            BuonoEconomale.beneficiario.ilike(like),
            BuonoEconomale.causale.ilike(like),
            BuonoEconomale.note.ilike(like),
        ]
        if testo.isdigit():
            cond.append(BuonoEconomale.numero_progressivo == int(testo))
        q = q.filter(or_(*cond))
    return q.order_by(BuonoEconomale.numero_progressivo.desc())


def filtri_attivi(filtri: dict) -> bool:
    return bool(filtri.get("q") or filtri.get("stato") or filtri.get("sezionale_id") or filtri.get("rapido"))
