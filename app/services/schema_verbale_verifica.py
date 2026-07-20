"""Assicura tabella verbale_verifica (create_all + indici)."""

from sqlalchemy import inspect

from app.extensions import db


def applica_schema_verbale_verifica() -> None:
    """create_all già crea la tabella; qui solo verifica presenza."""
    insp = inspect(db.engine)
    if not insp.has_table("verbale_verifica"):
        from app.models.verbale_verifica import VerbaleVerifica  # noqa: F401

        VerbaleVerifica.__table__.create(bind=db.engine, checkfirst=True)
