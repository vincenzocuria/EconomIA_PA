"""Filtri e query per l'elenco movimenti."""

import calendar
from datetime import date

from app.models.movimento import Movimento, StatoMovimento, TipoMovimento
from app.services.movimenti_ordine import ordina_movimenti
from app.services.movimenti_senza_allegato import query_senza_allegato

RAPIDI = ("uscite", "prelievi", "versamenti", "da_giustificare", "senza_allegato")

_TIPI_RAPIDO = {
    "uscite": (TipoMovimento.uscita,),
    "prelievi": (TipoMovimento.prelievo_banca,),
    "versamenti": (TipoMovimento.versamento_banca,),
}

TRIMESTRI = (
    ("t1", "1° trimestre (gen–mar)"),
    ("t2", "2° trimestre (apr–giu)"),
    ("t3", "3° trimestre (lug–set)"),
    ("t4", "4° trimestre (ott–dic)"),
)
MESI = (
    ("m1", "Gennaio"),
    ("m2", "Febbraio"),
    ("m3", "Marzo"),
    ("m4", "Aprile"),
    ("m5", "Maggio"),
    ("m6", "Giugno"),
    ("m7", "Luglio"),
    ("m8", "Agosto"),
    ("m9", "Settembre"),
    ("m10", "Ottobre"),
    ("m11", "Novembre"),
    ("m12", "Dicembre"),
)
_PERIODI = {codice: etichetta for codice, etichetta in (*TRIMESTRI, *MESI)}
_PERIODI["intervallo"] = "Intervallo di date"


def scelte_periodo() -> dict:
    return {"trimestri": TRIMESTRI, "mesi": MESI}


def _intero(args, nome: str) -> int:
    try:
        return int(args.get(nome) or 0)
    except (TypeError, ValueError):
        return 0


def _data(args, nome: str) -> date | None:
    raw = (args.get(nome) or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _etichetta_periodo(periodo: str, dal: date | None, al: date | None) -> str:
    if periodo == "intervallo":
        if dal and al:
            return f"{dal.strftime('%d/%m/%Y')} – {al.strftime('%d/%m/%Y')}"
        if dal:
            return f"dal {dal.strftime('%d/%m/%Y')}"
        if al:
            return f"fino al {al.strftime('%d/%m/%Y')}"
    return _PERIODI.get(periodo, "")


def parametri_filtro(args) -> dict:
    tipo = (args.get("tipo") or "").strip()
    if tipo not in {e.value for e in TipoMovimento}:
        tipo = ""
    stato = (args.get("stato") or "").strip()
    if stato not in {e.value for e in StatoMovimento}:
        stato = ""
    sezionale_id = _intero(args, "sezionale_id")
    if sezionale_id < 0:
        sezionale_id = 0
    periodo = (args.get("periodo") or "").strip()
    if not periodo:
        trimestre = _intero(args, "trimestre")
        if trimestre in (1, 2, 3, 4):
            periodo = f"t{trimestre}"
    if periodo not in _PERIODI:
        periodo = ""
    dal = _data(args, "dal")
    al = _data(args, "al")
    if periodo != "intervallo":
        dal = None
        al = None
    elif dal and al and dal > al:
        dal, al = al, dal
    rapido = (args.get("rapido") or "").strip()
    if args.get("da_giustificare") == "1":
        rapido = "da_giustificare"
    elif args.get("senza_allegato") == "1":
        rapido = "senza_allegato"
    if rapido not in RAPIDI:
        rapido = ""
    if tipo and rapido in _TIPI_RAPIDO:
        rapido = ""
    return {
        "tipo": tipo,
        "stato": stato,
        "sezionale_id": sezionale_id,
        "periodo": periodo,
        "periodo_label": _etichetta_periodo(periodo, dal, al),
        "dal": dal,
        "al": al,
        "rapido": rapido,
    }


def filtri_attivi(filtri: dict) -> bool:
    return bool(
        filtri.get("tipo")
        or filtri.get("stato")
        or filtri.get("sezionale_id")
        or filtri.get("periodo")
        or filtri.get("rapido")
    )


def query_movimenti(anno: int, filtri: dict):
    rapido = filtri.get("rapido") or ""
    if rapido == "senza_allegato":
        q = query_senza_allegato(anno)
    else:
        q = Movimento.query.filter_by(anno=anno)
        if rapido == "da_giustificare":
            q = q.filter_by(da_giustificare=True).filter(
                Movimento.stato != StatoMovimento.stornato
            )
        elif rapido in _TIPI_RAPIDO and not filtri.get("tipo"):
            q = q.filter(Movimento.tipo.in_(_TIPI_RAPIDO[rapido]))
    if filtri.get("tipo"):
        q = q.filter(Movimento.tipo == TipoMovimento(filtri["tipo"]))
    if filtri.get("stato"):
        q = q.filter(Movimento.stato == StatoMovimento(filtri["stato"]))
    if filtri.get("sezionale_id"):
        q = q.filter_by(sezionale_id=filtri["sezionale_id"])
    q = _applica_periodo(q, anno, filtri)
    return ordina_movimenti(q)


def _applica_periodo(q, anno: int, filtri: dict):
    periodo = filtri.get("periodo") or ""
    if periodo.startswith("t") and periodo[1:].isdigit():
        return q.filter_by(trimestre=int(periodo[1:]))
    if periodo.startswith("m") and periodo[1:].isdigit():
        mese = int(periodo[1:])
        ultimo = calendar.monthrange(anno, mese)[1]
        return q.filter(
            Movimento.data_movimento >= date(anno, mese, 1),
            Movimento.data_movimento <= date(anno, mese, ultimo),
        )
    if periodo == "intervallo":
        if filtri.get("dal"):
            q = q.filter(Movimento.data_movimento >= filtri["dal"])
        if filtri.get("al"):
            q = q.filter(Movimento.data_movimento <= filtri["al"])
    return q
