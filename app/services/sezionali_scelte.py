from app.models.movimento import TipoMovimento
from app.models.sezionale import Sezionale


def scelte_sezionale(corrente_id: int | None = None) -> list[tuple[int, str]]:
    opts: list[tuple[int, str]] = []
    rows = Sezionale.query.order_by(Sezionale.ordinamento, Sezionale.codice).all()
    for s in rows:
        if not s.attiva and s.id != corrente_id:
            continue
        label = f"{s.codice} — {s.descrizione or s.codice}"
        if not s.attiva:
            label += " (non attivo)"
        opts.append((s.id, label))
    if corrente_id and not any(i == corrente_id for i, _ in opts):
        s = Sezionale.query.get(corrente_id)
        if s:
            opts.insert(0, (s.id, f"{s.codice} — {s.descrizione or s.codice}"))
    return opts


def sezionale_per_codice(codice: str) -> Sezionale | None:
    return Sezionale.query.filter_by(codice=codice.upper().strip()).first()


def sezionale_default_per_tipo(tipo: TipoMovimento | str) -> Sezionale | None:
    val = tipo.value if hasattr(tipo, "value") else str(tipo)
    if val in (TipoMovimento.prelievo_banca.value, TipoMovimento.versamento_banca.value):
        return sezionale_per_codice("BAN") or sezionale_per_codice("GEN")
    return sezionale_per_codice("GEN")


def sezionale_default_buono() -> Sezionale | None:
    return sezionale_per_codice("RIM") or sezionale_per_codice("GEN")
