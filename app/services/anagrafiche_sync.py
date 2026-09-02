"""Upsert anagrafiche da form buoni/movimenti."""

from app.extensions import db
from app.models.anagrafica_beneficiario import AnagraficaBeneficiario
from app.models.anagrafica_richiedente import AnagraficaRichiedente
from app.models.anagrafica_ufficio import AnagraficaUfficio
from app.services.anagrafiche_testo import (
    normalizza_chiave,
    normalizza_denominazione,
    normalizza_nome_persona,
    pulisci_testo,
)


def salva_ufficio(
    denominazione: str | None,
    responsabile: str | None = None,
    *,
    collega_responsabile: bool = True,
) -> AnagraficaUfficio | None:
    nome = normalizza_denominazione(denominazione)
    if not nome:
        return None
    chiave = normalizza_chiave(nome)
    resp = normalizza_nome_persona(responsabile)
    row = AnagraficaUfficio.query.filter_by(denominazione_norm=chiave).first()
    if row is None:
        row = AnagraficaUfficio(
            denominazione=nome,
            denominazione_norm=chiave,
            responsabile=resp,
        )
        db.session.add(row)
    else:
        row.denominazione = nome
        if resp:
            row.responsabile = resp
    if resp and collega_responsabile:
        # Non ri-entra in salva_ufficio: evita duplicati in sessione non flushed
        salva_richiedente(resp, nome, collega_ufficio=False)
    return row


def salva_richiedente(
    nome: str | None,
    ufficio: str | None = None,
    responsabile: str | None = None,
    *,
    collega_ufficio: bool = True,
) -> AnagraficaRichiedente | None:
    valore = normalizza_nome_persona(nome)
    if not valore:
        return None
    chiave = normalizza_chiave(valore)
    uff = normalizza_denominazione(ufficio)
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
    if uff and collega_ufficio:
        salva_ufficio(uff, responsabile, collega_responsabile=False)
        if responsabile:
            salva_richiedente(responsabile, uff, collega_ufficio=False)
    return row


def salva_beneficiario(
    denominazione: str | None,
    cf_piva: str | None = None,
) -> AnagraficaBeneficiario | None:
    nome = normalizza_denominazione(denominazione)
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


def aggiorna_beneficiario(
    row: AnagraficaBeneficiario,
    denominazione: str | None,
    cf_piva: str | None,
) -> str | None:
    nome = normalizza_denominazione(denominazione)
    if not nome:
        return "Inserisci la denominazione del fornitore."
    chiave = normalizza_chiave(nome)
    altro = AnagraficaBeneficiario.query.filter(
        AnagraficaBeneficiario.denominazione_norm == chiave,
        AnagraficaBeneficiario.id != row.id,
    ).first()
    if altro:
        return "Esiste già un fornitore con questa denominazione."
    row.denominazione = nome
    row.denominazione_norm = chiave
    row.cf_piva = pulisci_testo(cf_piva, max_len=32)
    return None


def sync_da_buono(
    richiedente: str | None,
    ufficio: str | None,
    beneficiario: str | None,
    responsabile: str | None = None,
) -> None:
    salva_richiedente(richiedente, ufficio, responsabile)
    salva_ufficio(ufficio, responsabile)
    salva_beneficiario(beneficiario)


def sync_da_movimento(beneficiario: str | None, cf_piva: str | None) -> None:
    salva_beneficiario(beneficiario, cf_piva)
