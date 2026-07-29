"""Patch tabella saldo_annuale: saldo conto + migrazione da saldo cassa errato."""

from decimal import Decimal

from sqlalchemy import inspect, text

from app.extensions import db


def applica_schema_cassa() -> None:
    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("saldo_annuale"):
        return
    names = {c["name"] for c in insp.get_columns("saldo_annuale")}
    if "saldo_conto_iniziale" not in names:
        db.session.execute(
            text(
                "ALTER TABLE saldo_annuale "
                "ADD COLUMN saldo_conto_iniziale NUMERIC(12, 2) NOT NULL DEFAULT 0"
            )
        )
        db.session.commit()
        _migra_saldo_conto_da_cassa()


def _migra_saldo_conto_da_cassa() -> None:
    """Una tantum: se cassa > 0 e conto = 0, sposta l'importo sul conto (estratto)."""
    rows = db.session.execute(
        text(
            "SELECT anno, saldo_iniziale, saldo_conto_iniziale, note "
            "FROM saldo_annuale"
        )
    ).fetchall()
    for anno, saldo_cassa, saldo_conto, note in rows:
        cassa = Decimal(str(saldo_cassa or 0))
        conto = Decimal(str(saldo_conto or 0))
        if cassa <= 0 or conto != 0:
            continue
        nota = (note or "").strip()
        marker = "[migrazione] saldo iniziale spostato da cassa a conto"
        if marker in nota:
            continue
        nuova_nota = f"{nota}\n{marker}".strip() if nota else marker
        db.session.execute(
            text(
                "UPDATE saldo_annuale "
                "SET saldo_conto_iniziale = :conto, saldo_iniziale = 0, note = :note "
                "WHERE anno = :anno"
            ),
            {"conto": str(cassa), "note": nuova_nota, "anno": anno},
        )
    db.session.commit()
