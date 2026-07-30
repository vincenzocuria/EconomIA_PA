"""Upsert anagrafiche da form buoni/movimenti."""

from app.extensions import db
from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_testo import normalizza_chiave, pulisci_testo


def salva_ufficio(denominazione: str | None) -> AnagraficaUfficio | None:
    nome = pulisci_testo(denominazione)
    if not nome:
        return None
    chiave = normalizza_chiave(nome)
    row = AnagraficaUfficio.query.filter_by(denominazione_norm=chiave).first()
    if row is None:
        row = AnagraficaUfficio(denominazione=nome, denominazione_norm=chiave)
        db.session.add(row)
    else:
        row.denominazione = nome
    return row


def salva_richiedente(
    nome: str | None,
    ufficio: str | None = None,
) -> AnagraficaRichiedente | None:
    valore = pulisci_testo(nome)
    if not valore:
        return None
    chiave = normalizza_chiave(valore)
    uff = pulisci_testo(ufficio)
    row = AnagraficaRichiedente.query.filter_by(nome_norm=chiave).first()
    if row is None:
        row = AnagraficaRichiedente(
            nome=valore,
            nome_norm=chiave,
            ufficio_default=uff,
        )
        db.session.add(row)
    else:
        row.nome = valore
        if uff:
            row.ufficio_default = uff
    if uff:
        salva_ufficio(uff)
    return row


def salva_beneficiario(
    denominazione: str | None,
    cf_piva: str | None = None,
) -> AnagraficaBeneficiario | None:
    nome = pulisci_testo(denominazione)
    if not nome:
        return None
    chiave = normalizza_chiave(nome)
    piva = pulisci_testo(cf_piva, max_len=32)
    row = AnagraficaBeneficiario.query.filter_by(denominazione_norm=chiave).first()
    if row is None:
        row = AnagraficaBeneficiario(
            denominazione=nome,
            denominazione_norm=chiave,
            cf_piva=piva,
        )
        db.session.add(row)
    else:
        row.denominazione = nome
        if piva:
            row.cf_piva = piva
    return row


def sync_da_buono(richiedente: str | None, ufficio: str | None, beneficiario: str | None) -> None:
    salva_richiedente(richiedente, ufficio)
    salva_ufficio(ufficio)
    salva_beneficiario(beneficiario)


def sync_da_movimento(beneficiario: str | None, cf_piva: str | None) -> None:
    salva_beneficiario(beneficiario, cf_piva)
