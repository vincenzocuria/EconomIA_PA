"""Tabelle anagrafiche e seed da dati già presenti."""

from sqlalchemy import inspect

from app.extensions import db
from app.services.anagrafiche_sync import salva_beneficiario, salva_richiedente, salva_ufficio


def applica_schema_anagrafiche() -> None:
    from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
    from app.models.anagrafica_richiedente import AnagraficaRichiedente
    from app.models.anagrafica_ufficio import AnagraficaUfficio

    engine = db.engine
    insp = inspect(engine)
    for model in (AnagraficaRichiedente, AnagraficaUfficio, AnagraficaBeneficiario):
        if not insp.has_table(model.__tablename__):
            model.__table__.create(bind=engine)
            insp = inspect(engine)

    _seed_da_documenti()


def _seed_da_documenti() -> None:
    from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
    from app.models.anagrafica_richiedente import AnagraficaRichiedente
    from app.models.anagrafica_ufficio import AnagraficaUfficio
    from app.models.buono import BuonoEconomale
    from app.models.movimento import Movimento

    need_rich = AnagraficaRichiedente.query.count() == 0
    need_uff = AnagraficaUfficio.query.count() == 0
    need_ben = AnagraficaBeneficiario.query.count() == 0
    if not (need_rich or need_uff or need_ben):
        return

    for b in BuonoEconomale.query.all():
        if need_rich:
            salva_richiedente(b.richiedente, b.ufficio_richiedente)
        if need_uff:
            salva_ufficio(b.ufficio_richiedente)
        if need_ben:
            salva_beneficiario(b.beneficiario)

    if need_ben:
        for m in Movimento.query.all():
            salva_beneficiario(m.beneficiario_fornitore, m.cf_piva)

    db.session.commit()
