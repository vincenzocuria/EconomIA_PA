"""Filtri e ricerca per elenco buoni economali."""

from sqlalchemy import or_

from app.models.buono import BuonoEconomale, StatoBuono
from app.services.anagrafiche_testo import pulisci_testo
from app.services.ricerca_completa import condizione_ricerca_completa

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
    if rapido not in ("aperti", "da_chiudere", "da_firmare"):
        rapido = ""
    return {
        "q": q,
        "stato": stato,
        "sezionale_id": sezionale_id,
        "rapido": rapido,
    }


def query_buoni(anno: int, filtri: dict):
    if filtri.get("rapido") == "da_firmare" and not filtri.get("stato"):
        from app.services.buoni_senza_firma import query_senza_firma

        q = query_senza_firma(anno)
    else:
        q = BuonoEconomale.query.filter_by(anno=anno)
        if filtri.get("stato"):
            q = q.filter_by(stato=StatoBuono(filtri["stato"]))
        elif filtri.get("rapido") == "aperti":
            q = q.filter(BuonoEconomale.stato.in_(STATI_APERTI))
        elif filtri.get("rapido") == "da_chiudere":
            q = q.filter(BuonoEconomale.stato.in_(STATI_DA_CHIUDERE))

    if filtri.get("sezionale_id"):
        q = q.filter_by(sezionale_id=filtri["sezionale_id"])

    testo = filtri.get("q") or ""
    if testo:
        cond_testo = condizione_ricerca_completa(
            BuonoEconomale.richiedente,
            BuonoEconomale.ufficio_richiedente,
            BuonoEconomale.responsabile_ufficio,
            BuonoEconomale.beneficiario,
            BuonoEconomale.causale,
            BuonoEconomale.note,
            q=testo,
        )
        if testo.isdigit():
            num = BuonoEconomale.numero_progressivo == int(testo)
            q = q.filter(or_(cond_testo, num) if cond_testo is not None else num)
        elif cond_testo is not None:
            q = q.filter(cond_testo)
    return q.order_by(BuonoEconomale.numero_progressivo.desc())


def filtri_attivi(filtri: dict) -> bool:
    return bool(filtri.get("q") or filtri.get("stato") or filtri.get("sezionale_id") or filtri.get("rapido"))
