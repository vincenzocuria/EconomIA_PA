"""Genera il modulo Word di richiesta rimborso da un buono economale."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.config import INSTANCE_DIR
from app.models.buono import BuonoEconomale
from app.services.docx_base import applica_intestazione_ente
from app.services.docx_tabelle import cella_multiline, tabella_griglia
from app.services.numero_display import formato_numero_sezionale

_LINEA_FIRMA = "________________________________"


def _eur(v) -> str:
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _data_it(d) -> str:
    if not d:
        return "____ / ____ / ______"
    return d.strftime("%d / %m / %Y")


def _para(doc: Document, text: str, *, center: bool = False, bold: bool = False, size: float | None = 14):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = bold
    if size is not None:
        run.font.size = Pt(size)
    return p


def genera_docx_rimborso(b: BuonoEconomale) -> Path:
    out_dir = INSTANCE_DIR / "buoni_docx"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"modulo_rimborso_{b.anno}_{b.numero_progressivo:04d}.docx"

    num = formato_numero_sezionale(b)
    importo = _eur(b.importo_speso or b.importo_autorizzato)
    data = _data_it(b.data_buono)
    richiedente = (b.richiedente or "").strip() or "___________________________________________________"
    ufficio = (b.ufficio_richiedente or "").strip() or "____________________________"
    causale = (b.causale or "").strip() or ("_" * 80)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)

    applica_intestazione_ente(doc)

    _para(doc, "RICHIESTA DI RIMBORSO SPESA ECONOMALE", center=True, bold=True, size=12)
    doc.add_paragraph()

    tab_num = tabella_griglia(doc, 1, 2)
    cella_multiline(tab_num.rows[0].cells[0], [f"Buono economale n. {num}"])
    cella_multiline(tab_num.rows[0].cells[1], [f"Data {data}"])

    doc.add_paragraph()
    _para(
        doc,
        f"Il/La sottoscritto/a {richiedente}, dell’Ufficio {ufficio}, "
        f"chiede il rimborso di € {importo} per:",
    )
    causale_p = _para(doc, causale)
    causale_p.paragraph_format.space_after = Pt(12)

    tab_firme = tabella_griglia(doc, 1, 2)
    cella_multiline(tab_firme.rows[0].cells[0], ["Data", data])
    cella_multiline(
        tab_firme.rows[0].cells[1],
        [f"Il Responsabile dell’Ufficio {ufficio}", "", _LINEA_FIRMA],
    )

    doc.add_paragraph()
    _para(doc, "QUIETANZA", center=True, bold=True, size=14)
    quiet = _para(
        doc,
        f"Il/La sottoscritto/a dichiara di aver ricevuto dall’Economo comunale "
        f"€ {importo} a rimborso della spesa sopra indicata.",
    )
    quiet.paragraph_format.space_before = Pt(6)

    doc.add_paragraph()
    tab_q = tabella_griglia(doc, 2, 2)
    cella_multiline(tab_q.rows[0].cells[0], ["Data", data])
    cella_multiline(tab_q.rows[0].cells[1], ["Firma per ricevuta", "", _LINEA_FIRMA])
    q_a = tab_q.rows[1].cells[0]
    q_b = tab_q.rows[1].cells[1]
    q_a.merge(q_b)
    cella_multiline(q_a, ["L’Economo comunale", "", _LINEA_FIRMA])

    doc.save(str(path))
    return path
