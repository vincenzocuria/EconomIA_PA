"""Scelte filiale per form (anagrafica + movimenti)."""

from app.extensions import db
from app.models.filiale_banca import FilialeBanca
from app.models.movimento import Movimento


def scelte_filiale_per_movimento(m: Movimento | None) -> list[tuple[int, str]]:
    opts: list[tuple[int, str]] = [(0, "— Nessuna filiale —")]
    attive = (
        FilialeBanca.query.filter_by(attiva=True)
        .order_by(FilialeBanca.ordinamento, FilialeBanca.denominazione)
        .all()
    )
    seen: set[int] = set()
    for f in attive:
        opts.append((f.id, f.denominazione))
        seen.add(f.id)
    fid = m.filiale_id if m else None
    if fid and fid not in seen:
        fx = db.session.get(FilialeBanca, fid)
        if fx:
            opts.append((fx.id, f"{fx.denominazione} (non attiva)"))
    return opts
