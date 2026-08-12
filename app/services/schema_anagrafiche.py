"""Tabelle anagrafiche, colonne opzionali e seed da dati già presenti."""

from sqlalchemy import inspect, text

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

    _assicura_colonne()
    _seed_da_documenti()
    _rinormalizza_anagrafiche()


def _assicura_colonne() -> None:
    engine = db.engine
    insp = inspect(engine)
    stmts: list[str] = []

    if insp.has_table("anagrafica_ufficio"):
        cols = {c["name"] for c in insp.get_columns("anagrafica_ufficio")}
        if "responsabile" not in cols:
            stmts.append(
                "ALTER TABLE anagrafica_ufficio ADD COLUMN responsabile VARCHAR(300) DEFAULT ''"
            )

    if insp.has_table("buono_economale"):
        cols = {c["name"] for c in insp.get_columns("buono_economale")}
        if "responsabile_ufficio" not in cols:
            stmts.append(
                "ALTER TABLE buono_economale ADD COLUMN responsabile_ufficio VARCHAR(300) DEFAULT ''"
            )

    for sql in stmts:
        db.session.execute(text(sql))
    if stmts:
        db.session.commit()


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
        resp = getattr(b, "responsabile_ufficio", None)
        if need_rich:
            salva_richiedente(b.richiedente, b.ufficio_richiedente, resp)
        if need_uff:
            salva_ufficio(b.ufficio_richiedente, resp)
        if need_ben:
            salva_beneficiario(b.beneficiario)

    if need_ben:
        for m in Movimento.query.all():
            salva_beneficiario(m.beneficiario_fornitore, m.cf_piva)

    db.session.commit()


def _rinormalizza_anagrafiche() -> None:
    """Allinea maiuscole/apostrofi sui record già presenti."""
    from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
    from app.models.anagrafica_richiedente import AnagraficaRichiedente
    from app.models.anagrafica_ufficio import AnagraficaUfficio
    from app.services.anagrafiche_testo import (
        normalizza_chiave,
        normalizza_denominazione,
        normalizza_nome_persona,
    )

    cambiato = False

    for r in AnagraficaRichiedente.query.all():
        nome = normalizza_nome_persona(r.nome)
        chiave = normalizza_chiave(nome)
        uff = normalizza_denominazione(r.ufficio_default)
        if r.nome != nome or r.nome_norm != chiave or (r.ufficio_default or "") != uff:
            conflitto = AnagraficaRichiedente.query.filter(
                AnagraficaRichiedente.nome_norm == chiave,
                AnagraficaRichiedente.id != r.id,
            ).first()
            if conflitto:
                continue
            r.nome = nome
            r.nome_norm = chiave
            r.ufficio_default = uff
            cambiato = True

    for u in AnagraficaUfficio.query.all():
        nome = normalizza_denominazione(u.denominazione)
        chiave = normalizza_chiave(nome)
        resp = normalizza_nome_persona(u.responsabile)
        if (
            u.denominazione != nome
            or u.denominazione_norm != chiave
            or (u.responsabile or "") != resp
        ):
            conflitto = AnagraficaUfficio.query.filter(
                AnagraficaUfficio.denominazione_norm == chiave,
                AnagraficaUfficio.id != u.id,
            ).first()
            if conflitto:
                continue
            u.denominazione = nome
            u.denominazione_norm = chiave
            u.responsabile = resp
            cambiato = True
        if resp:
            salva_richiedente(resp, nome)

    for b in AnagraficaBeneficiario.query.all():
        nome = normalizza_denominazione(b.denominazione)
        chiave = normalizza_chiave(nome)
        if b.denominazione != nome or b.denominazione_norm != chiave:
            conflitto = AnagraficaBeneficiario.query.filter(
                AnagraficaBeneficiario.denominazione_norm == chiave,
                AnagraficaBeneficiario.id != b.id,
            ).first()
            if conflitto:
                continue
            b.denominazione = nome
            b.denominazione_norm = chiave
            cambiato = True

    if cambiato or db.session.new or db.session.dirty:
        db.session.commit()
