"""Controlli del fascicolo di chiusura, allineati alla documentazione trimestrale."""

from flask import url_for
from sqlalchemy import or_

from app.models.allegato import Allegato, TipoAllegato
from app.models.buono import StatoBuono
from app.models.verbale_verifica import VerbaleVerifica
from app.services.chiusura_documenti import documento_presente
from app.services.chiusura_quadratura import movimenti_attivi, quadratura_trimestre
from app.services.chiusura_record import chiusura_di
from app.services.euro import formato_euro
from app.services.incarico_periodo import trimestre_dovuto
from app.services.numero_display import formato_numero_sezionale


def _voce(codice: str, titolo: str, stato: str, bloccante: bool, dettaglio: str, mancanti=None) -> dict:
    return {
        "codice": codice,
        "titolo": titolo,
        "stato": stato,
        "bloccante": bloccante,
        "dettaglio": dettaglio,
        "mancanti": mancanti or [],
    }


def _link(etichetta: str, endpoint: str, **kwargs) -> dict:
    return {"etichetta": etichetta, "url": url_for(endpoint, **kwargs), "upload": None, "buono_id": None}


def _mappa_allegati(mov_ids: list[int], buono_ids: list[int]) -> list[Allegato]:
    filtri = []
    if mov_ids:
        filtri.append(Allegato.movimento_id.in_(mov_ids))
    if buono_ids:
        filtri.append(Allegato.buono_id.in_(buono_ids))
    if not filtri:
        return []
    return Allegato.query.filter(or_(*filtri)).all()


def controlla_chiusura(anno: int, trimestre: int) -> dict:
    row = chiusura_di(anno, trimestre)
    q = quadratura_trimestre(anno, trimestre, row, movimenti_attivi(anno))
    chiusa = row is not None and row.stato == "chiusa"
    mov_ids = [m.id for m in q["nel"]]
    buono_ids = [m.buono_id for m in q["uscite"] if m.buono_id]
    allegati = _mappa_allegati(mov_ids, buono_ids)
    mov_con_file = {a.movimento_id for a in allegati if a.movimento_id}
    firmati = {
        a.buono_id
        for a in allegati
        if a.buono_id and a.tipo_documento == TipoAllegato.autorizzazione
    }
    quietanze = {
        a.buono_id
        for a in allegati
        if a.buono_id and a.tipo_documento == TipoAllegato.ricevuta
    }

    voci: list[dict] = []

    if documento_presente(row, "estratto"):
        voci.append(
            _voce(
                "estratto",
                "Estratto conto del trimestre",
                "ok",
                True,
                "Caricato nel fascicolo (movimenti di conto del periodo).",
            )
        )
    else:
        voci.append(
            _voce(
                "estratto",
                "Estratto conto del trimestre",
                "manca",
                True,
                "Serve il PDF o la stampa della banca sull'intero trimestre.",
            )
        )

    if documento_presente(row, "promemoria"):
        voci.append(
            _voce(
                "promemoria",
                "Promemoria del conto",
                "ok",
                True,
                "Caricato nel fascicolo (saldo a credito a fine periodo).",
            )
        )
    else:
        voci.append(
            _voce(
                "promemoria",
                "Promemoria del conto",
                "manca",
                True,
                "Serve il promemoria banca con il saldo a credito.",
            )
        )

    if not q["saldi_estratto_inseriti"]:
        voci.append(
            _voce(
                "quadratura",
                "Quadratura estratto / conto",
                "manca",
                True,
                "Indica il saldo iniziale e il saldo finale scritti sull'estratto.",
            )
        )
    elif q["scostamento"] == 0:
        voci.append(
            _voce(
                "quadratura",
                "Quadratura estratto / conto",
                "ok",
                True,
                (
                    f"Variazione estratto {formato_euro(q['delta_estratto'])} = "
                    f"registro {formato_euro(q['delta_conto'])} + voci {formato_euro(q['somma_voci'])}."
                ),
            )
        )
    else:
        voci.append(
            _voce(
                "quadratura",
                "Quadratura estratto / conto",
                "manca",
                True,
                (
                    f"Scostamento {formato_euro(q['scostamento'])}. "
                    "Registra le voci dell'estratto che non sono prelievi o versamenti "
                    "(anticipazione fondi, interessi, ritenute) oppure correggi i movimenti."
                ),
            )
        )

    distinte = []
    for m in q["prelievi"]:
        if m.id not in mov_con_file:
            distinte.append(
                _link(
                    f"Prelievo {formato_numero_sezionale(m)} del {m.data_movimento.strftime('%d/%m/%Y')} "
                    f"({formato_euro(m.importo)}) senza distinta di sportello",
                    "movimenti.modifica",
                    id=m.id,
                )
            )
    if distinte:
        voci.append(
            _voce(
                "distinte",
                "Distinte di prelievo",
                "manca",
                True,
                "Ogni prelievo contanti allo sportello deve avere la distinta allegata.",
                distinte,
            )
        )
    else:
        n = len(q["prelievi"])
        voci.append(
            _voce(
                "distinte",
                "Distinte di prelievo",
                "ok",
                True,
                "Nessun prelievo nel trimestre." if n == 0 else f"{n} prelievi con distinta allegata.",
            )
        )

    ricevute_vers = []
    for m in q["versamenti"]:
        if m.id not in mov_con_file:
            ricevute_vers.append(
                _link(
                    f"Versamento {formato_numero_sezionale(m)} senza ricevuta",
                    "movimenti.modifica",
                    id=m.id,
                )
            )
    if ricevute_vers:
        voci.append(
            _voce(
                "versamenti",
                "Ricevute di versamento",
                "manca",
                True,
                "Ogni versamento in banca deve avere la ricevuta allegata.",
                ricevute_vers,
            )
        )
    else:
        n = len(q["versamenti"])
        voci.append(
            _voce(
                "versamenti",
                "Ricevute di versamento",
                "ok",
                True,
                "Nessun versamento nel trimestre." if n == 0 else f"{n} versamenti con ricevuta.",
            )
        )

    senza_buono = []
    senza_firma = []
    senza_quietanza = []
    non_chiusi = []
    visti_firma: set[int] = set()
    visti_quietanza: set[int] = set()
    visti_chiusi: set[int] = set()
    for m in q["uscite"]:
        etichetta = (
            f"{formato_numero_sezionale(m)} · {m.data_movimento.strftime('%d/%m/%Y')} · "
            f"{(m.beneficiario_fornitore or 'senza beneficiario')} · {formato_euro(m.importo)}"
        )
        b = m.buono
        if b is None or b.stato == StatoBuono.annullato:
            senza_buono.append(_link(etichetta, "movimenti.dettaglio", id=m.id))
            continue
        if b.id not in firmati and b.id not in visti_firma:
            visti_firma.add(b.id)
            senza_firma.append(_link(f"Buono {formato_numero_sezionale(b)} senza firma dell'economo", "buoni.modifica", id=b.id))
        if b.id not in quietanze and b.id not in visti_quietanza:
            visti_quietanza.add(b.id)
            item = _link(
                f"Buono {formato_numero_sezionale(b)} senza quietanza del beneficiario",
                "buoni.modifica",
                id=b.id,
            )
            item["upload"] = "quietanza"
            item["buono_id"] = b.id
            senza_quietanza.append(item)
        if b.stato != StatoBuono.chiuso and b.id not in visti_chiusi:
            visti_chiusi.add(b.id)
            non_chiusi.append(
                _link(
                    f"Buono {formato_numero_sezionale(b)} in stato {b.stato.value}",
                    "buoni.lista",
                    anno=anno,
                )
            )

    if senza_buono:
        voci.append(_voce("buoni", "Buoni di pagamento", "manca", True, "Ogni uscita del trimestre deve avere un buono.", senza_buono))
    else:
        voci.append(
            _voce(
                "buoni",
                "Buoni di pagamento",
                "ok",
                True,
                f"{len(q['uscite'])} uscite collegate a un buono, totale {formato_euro(q['totale_uscite'])}.",
            )
        )

    if senza_firma:
        voci.append(
            _voce(
                "firme",
                "Firma dell'economo sui buoni",
                "manca",
                True,
                "Ricarica il buono firmato (modulo firmato).",
                senza_firma,
            )
        )
    else:
        voci.append(_voce("firme", "Firma dell'economo sui buoni", "ok", True, "Tutti i buoni del trimestre hanno il modulo firmato."))

    if senza_quietanza:
        voci.append(
            _voce(
                "quietanze",
                "Quietanza del beneficiario",
                "manca",
                True,
                "Sul buono cartaceo la riga «Ricevo la somma» deve essere firmata. Allega qui la scansione.",
                senza_quietanza,
            )
        )
    else:
        voci.append(_voce("quietanze", "Quietanza del beneficiario", "ok", True, "Ogni buono ha la quietanza allegata."))

    senza_giust = []
    for m in q["uscite"]:
        if m.id not in mov_con_file:
            senza_giust.append(
                _link(
                    f"{formato_numero_sezionale(m)} senza scontrino, fattura o ricevuta",
                    "movimenti.modifica",
                    id=m.id,
                )
            )
    if senza_giust:
        voci.append(
            _voce(
                "giustificativi",
                "Giustificativi di spesa",
                "manca",
                True,
                "Ogni uscita deve avere il documento fiscale allegato al movimento.",
                senza_giust,
            )
        )
    else:
        voci.append(_voce("giustificativi", "Giustificativi di spesa", "ok", True, "Tutte le uscite hanno un allegato."))

    da_giust = [
        _link(
            f"{formato_numero_sezionale(m)} ancora da giustificare",
            "movimenti.modifica",
            id=m.id,
        )
        for m in q["nel"]
        if m.da_giustificare
    ]
    if da_giust:
        voci.append(_voce("da_giustificare", "Movimenti da giustificare", "manca", True, "Vanno chiusi prima del trimestre.", da_giust))
    else:
        voci.append(_voce("da_giustificare", "Movimenti da giustificare", "ok", True, "Nessun movimento del trimestre è ancora da giustificare."))

    if non_chiusi:
        voci.append(
            _voce(
                "buoni_chiusi",
                "Buoni in stato chiuso",
                "manca",
                True,
                "I buoni pagati del trimestre vanno portati a stato chiuso.",
                non_chiusi,
            )
        )
    else:
        voci.append(_voce("buoni_chiusi", "Buoni in stato chiuso", "ok", True, "Nessun buono del trimestre è ancora aperto."))

    if q["giacenza_fine"] < 0:
        voci.append(
            _voce(
                "giacenza",
                "Giacenza di cassa",
                "manca",
                True,
                f"Giacenza a fine trimestre {formato_euro(q['giacenza_fine'])}: non può essere negativa.",
            )
        )
    else:
        voci.append(
            _voce(
                "giacenza",
                "Giacenza di cassa",
                "ok",
                True,
                (
                    f"Inizio {formato_euro(q['giacenza_inizio'])} + prelievi {formato_euro(q['totale_prelievi'])} "
                    f"+ entrate {formato_euro(q['totale_entrate'])} − pagamenti {formato_euro(q['totale_uscite'])} "
                    f"− versamenti {formato_euro(q['totale_versamenti'])} = {formato_euro(q['giacenza_fine'])}."
                ),
            )
        )

    voci.append(
        _voce(
            "prospetto",
            "Prospetto pagamenti",
            "ok",
            False,
            "Calcolato dai movimenti (numero buoni, totale, prelievi, giacenza). Non va ricopiato a mano.",
        )
    )
    voci.append(
        _voce(
            "giornale",
            "Giornale di cassa",
            "ok",
            False,
            "Calcolato dai movimenti del periodo, con la stessa giacenza del prospetto.",
        )
    )

    verbale = VerbaleVerifica.query.filter_by(anno=anno, trimestre=trimestre).first()
    if verbale is not None:
        voci.append(
            _voce(
                "verbale",
                "Verbale del revisore",
                "ok",
                False,
                f"Verbale n. {verbale.numero} del {verbale.data_verbale.strftime('%d/%m/%Y')} archiviato.",
            )
        )
    else:
        voci.append(
            _voce(
                "verbale",
                "Verbale del revisore",
                "avviso",
                False,
                "Non blocca la chiusura dell'economo: si archivia quando il revisore lo consegna.",
                [_link("Apri verbali", "verbali.lista", anno=anno)],
            )
        )

    mancanti = [v for v in voci if v["stato"] == "manca"]
    presenti = [v for v in voci if v["stato"] == "ok"]
    avvisi = [v for v in voci if v["stato"] == "avviso"]
    bloccanti_mancanti = [v for v in mancanti if v["bloccante"]]
    return {
        "chiusura": row,
        "chiusa": chiusa,
        "dovuto": trimestre_dovuto(anno, trimestre),
        "quadratura": q,
        "voci": voci,
        "presenti": presenti,
        "mancanti": mancanti,
        "avvisi": avvisi,
        "pronto": not bloccanti_mancanti,
        "n_mancanti": len(bloccanti_mancanti),
    }


def voci_da_fare_chiusura(anno: int) -> list[dict]:
    """Voci dashboard per i trimestri già terminati e non chiusi."""
    from app.services.incarico_periodo import trimestri_in_incarico

    out = []
    for t in trimestri_in_incarico(anno):
        if not trimestre_dovuto(anno, t):
            continue
        esito = controlla_chiusura(anno, t)
        if esito["chiusa"]:
            continue
        n = esito["n_mancanti"]
        if n:
            titolo = f"Chiusura T{t}: mancano {n} controlli del fascicolo"
            livello = "warning"
        else:
            titolo = f"Chiusura T{t} pronta: fascicolo completo"
            livello = "info"
        out.append(
            {
                "titolo": titolo,
                "n": n or 1,
                "livello": livello,
                "url": url_for("chiusura.dettaglio", anno=anno, trimestre=t),
            }
        )
    return out
