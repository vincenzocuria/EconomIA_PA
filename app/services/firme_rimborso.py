"""Logica linee firma del modulo rimborso (richiedente / responsabile / economo)."""

from app.services.anagrafiche_testo import normalizza_chiave, pulisci_testo

_LINEA_FIRMA = "________________________________"
LINEA_FIRMA = _LINEA_FIRMA


def stesse_persone(a: str | None, b: str | None) -> bool:
    ka = normalizza_chiave(a)
    kb = normalizza_chiave(b)
    return bool(ka) and ka == kb


def _blocco_responsabile(ufficio: str, responsabile: str) -> list[str]:
    etichetta = f"Il Responsabile dell’Ufficio {ufficio}"
    if responsabile:
        return [etichetta, responsabile, _LINEA_FIRMA]
    return [etichetta, _LINEA_FIRMA]


def _blocco_unico(ufficio: str, nome: str) -> list[str]:
    etichetta = f"Il/La Richiedente e Responsabile dell’Ufficio {ufficio}"
    if nome:
        return [etichetta, nome, _LINEA_FIRMA]
    return [etichetta, _LINEA_FIRMA]


def _blocco_richiedente(nome: str) -> list[str]:
    if nome:
        return ["Il/La Richiedente", nome, _LINEA_FIRMA]
    return ["Il/La Richiedente", _LINEA_FIRMA]


def _blocco_economo(nome: str) -> list[str]:
    etichetta = "L’Economo comunale"
    if nome:
        return [etichetta, nome, _LINEA_FIRMA]
    return [etichetta, _LINEA_FIRMA]


def linee_firma_richiesta(
    richiedente: str | None,
    ufficio: str | None,
    responsabile: str | None,
) -> list[list[str]]:
    """Sempre firma responsabile; se richiedente == responsabile → un solo blocco."""
    rich = pulisci_testo(richiedente)
    uff = pulisci_testo(ufficio) or "____________________________"
    resp = pulisci_testo(responsabile)

    if stesse_persone(rich, resp):
        return [_blocco_unico(uff, rich or resp)]

    if rich:
        return [_blocco_richiedente(rich), _blocco_responsabile(uff, resp)]

    return [_blocco_responsabile(uff, resp)]


def linee_firma_modulo(
    richiedente: str | None,
    ufficio: str | None,
    responsabile: str | None,
    nome_economo: str | None = None,
) -> list[list[str]]:
    """Firme del modulo: richiedente/responsabile (unificati se coincidono) + economo."""
    blocchi = linee_firma_richiesta(richiedente, ufficio, responsabile)
    blocchi.append(_blocco_economo(pulisci_testo(nome_economo)))
    return blocchi
