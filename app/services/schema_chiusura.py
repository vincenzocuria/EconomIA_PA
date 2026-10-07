"""Assicura le tabelle del fascicolo di chiusura trimestre."""

from sqlalchemy import inspect

from app.extensions import db


def applica_schema_chiusura() -> None:
    insp = inspect(db.engine)
    if not insp.has_table("chiusura_trimestre"):
        from app.models.chiusura_trimestre import ChiusuraTrimestre

        ChiusuraTrimestre.__table__.create(bind=db.engine, checkfirst=True)
    if not insp.has_table("voce_riconciliazione_conto"):
        from app.models.chiusura_trimestre import VoceRiconciliazioneConto

        VoceRiconciliazioneConto.__table__.create(bind=db.engine, checkfirst=True)
