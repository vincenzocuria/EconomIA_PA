"""Lettura e creazione della riga di chiusura trimestre."""

from app.extensions import db
from app.models.chiusura_trimestre import ChiusuraTrimestre


def chiusura_di(anno: int, trimestre: int) -> ChiusuraTrimestre | None:
    return ChiusuraTrimestre.query.filter_by(anno=anno, trimestre=trimestre).first()


def ottieni_chiusura(anno: int, trimestre: int, *, crea: bool = False) -> ChiusuraTrimestre | None:
    row = chiusura_di(anno, trimestre)
    if row is None and crea:
        row = ChiusuraTrimestre(anno=anno, trimestre=trimestre, stato="aperta")
        db.session.add(row)
        db.session.flush()
    return row


def trimestre_chiuso(anno: int, trimestre: int) -> bool:
    row = chiusura_di(anno, trimestre)
    return row is not None and row.stato == "chiusa"
