"""Aggiunge colonne opzionali alla tabella movimento (SQLite) se mancanti."""

from sqlalchemy import inspect, text

from app.extensions import db


def applica_patch_movimento() -> None:
    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("movimento"):
        return
    names = {c["name"] for c in insp.get_columns("movimento")}
    stmts: list[str] = []
    if "ora_movimento" not in names:
        stmts.append("ALTER TABLE movimento ADD COLUMN ora_movimento VARCHAR(16)")
    if "filiale_banca" not in names:
        stmts.append("ALTER TABLE movimento ADD COLUMN filiale_banca VARCHAR(200) DEFAULT ''")
    if "rif_ricevuta" not in names:
        stmts.append("ALTER TABLE movimento ADD COLUMN rif_ricevuta VARCHAR(120) DEFAULT ''")
    if "da_giustificare" not in names:
        stmts.append(
            "ALTER TABLE movimento ADD COLUMN da_giustificare BOOLEAN NOT NULL DEFAULT 0"
        )
    for sql in stmts:
        db.session.execute(text(sql))
    if stmts:
        db.session.commit()
