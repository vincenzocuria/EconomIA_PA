"""Genera il modulo Word di richiesta rimborso da un buono economale."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.config import INSTANCE_DIR
from app.models.buono import BuonoEconomale
from app.services.docx_base import applica_intestazione_ente
from app.services.docx_tabelle import cella_multiline, tabella_griglia
from app.services.firme_rimborso import LINEA_FIRMA, linee_firma_richiesta
from app.services.numero_display import formato_numero_sezionale

_FONT = 11


def _eur(v) -> str:
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _data_it(d) -> str:
    if not d:
        return "____ / ____ / ______"
    return d.strftime("%d / %m / %Y")


def _para(
    doc: Document,
    text: str,
    *,
    center: bool = False,
    bold: bool = False,
    size: float | None = _FONT,
    space_before: float = 0,
    space_after: float = 4,
):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.0
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
    responsabile = (getattr(b, "responsabile_ufficio", None) or "").strip()
    causale = (b.causale or "").strip() or ("_" * 80)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(0.8)
        section.bottom_margin = Cm(0.8)
        section.left_margin = Cm(1.2)
        section.right_margin = Cm(1.2)
        section.header_distance = Cm(0.4)
        section.footer_distance = Cm(0.4)

    applica_intestazione_ente(doc, logo_cm=2.0, font_comune=11, font_provincia=10)

    _para(doc, "RICHIESTA DI RIMBORSO SPESA ECONOMALE", center=True, bold=True, size=11, space_after=6)

    tab_num = tabella_griglia(doc, 1, 2)
    cella_multiline(tab_num.rows[0].cells[0], [f"Buono economale n. {num}"], font_pt=_FONT)
    cella_multiline(tab_num.rows[0].cells[1], [f"Data {data}"], font_pt=_FONT)

    _para(
        doc,
        f"Il/La sottoscritto/a {richiedente}, dell’Ufficio {ufficio}, "
        f"chiede il rimborso di € {importo} per:",
        space_before=6,
        space_after=2,
    )
    _para(doc, causale, space_after=6)

    blocchi = linee_firma_richiesta(b.richiedente, b.ufficio_richiedente, responsabile)
    if len(blocchi) == 1:
        tab_firme = tabella_griglia(doc, 1, 2)
        cella_multiline(tab_firme.rows[0].cells[0], ["Data", data], font_pt=_FONT)
        cella_multiline(tab_firme.rows[0].cells[1], blocchi[0], font_pt=_FONT)
    else:
        # Richiedente e responsabile affiancati → meno altezza, una sola pagina
        tab_firme = tabella_griglia(doc, 1, 2)
        cella_multiline(tab_firme.rows[0].cells[0], blocchi[0], font_pt=_FONT)
        cella_multiline(tab_firme.rows[0].cells[1], blocchi[1], font_pt=_FONT)
        _para(doc, f"Data {data}", space_before=4, space_after=4)

    _para(doc, "QUIETANZA", center=True, bold=True, size=11, space_before=8, space_after=4)
    _para(
        doc,
        f"Il/La sottoscritto/a dichiara di aver ricevuto dall’Economo comunale "
        f"€ {importo} a rimborso della spesa sopra indicata.",
        space_after=4,
    )

    tab_q = tabella_griglia(doc, 1, 2)
    cella_multiline(tab_q.rows[0].cells[0], ["Data", data, "", "Firma per ricevuta", "", LINEA_FIRMA], font_pt=_FONT)
    cella_multiline(tab_q.rows[0].cells[1], ["L’Economo comunale", "", LINEA_FIRMA], font_pt=_FONT)

    doc.save(str(path))
    return path
