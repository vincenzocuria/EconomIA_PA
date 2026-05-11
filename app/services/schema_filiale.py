"""Tabella filiali e collegamento su movimento (DB esistenti SQLite)."""

from sqlalchemy import inspect, text

from app.extensions import db


def applica_schema_filiale_banca() -> None:
    from app.models.filiale_banca import FilialeBanca

    engine = db.engine
    insp = inspect(engine)
    if not insp.has_table("filiale_banca"):
        FilialeBanca.__table__.create(bind=engine)
    insp = inspect(engine)
    if insp.has_table("movimento"):
        cols = {c["name"] for c in insp.get_columns("movimento")}
        if "filiale_id" not in cols:
            db.session.execute(text("ALTER TABLE movimento ADD COLUMN filiale_id INTEGER"))
            db.session.commit()
    if FilialeBanca.query.count() == 0:
        db.session.add(
            FilialeBanca(
                denominazione="Filiale principale",
                indirizzo="",
                attiva=True,
                ordinamento=0,
            )
        )
        db.session.commit()
