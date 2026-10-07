"""Giornale di cassa del trimestre, calcolato dai movimenti registrati."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.chiusura_quadratura import quadratura_trimestre
from app.services.chiusura_record import chiusura_di
from app.services.euro import formato_euro
from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS
from app.services.numero_display import formato_numero_sezionale
from app.services.pdf_base import disclaimer_registro, intestazione_flowables


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text or ""), style)


def _tipo(m) -> str:
    return TIPO_MOVIMENTO_LABELS.get(m.tipo, m.tipo.value)


def genera_giornale_cassa(anno: int, trimestre: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    q = quadratura_trimestre(anno, trimestre, chiusura_di(anno, trimestre))
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("gio_h", parent=styles["Heading1"], fontSize=13, textColor=colors.HexColor("#1a365d"))
    th = ParagraphStyle("gio_th", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7, leading=9)
    td = ParagraphStyle("gio_td", parent=styles["Normal"], fontSize=7, leading=9)
    story = intestazione_flowables()
    story.append(
        Paragraph(
            f"Giornale di cassa — dal {q['inizio'].strftime('%d/%m/%Y')} al {q['fine'].strftime('%d/%m/%Y')}",
            h1,
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    rows = [[
        _p("N.", th),
        _p("Data", th),
        _p("Tipo", th),
        _p("Descrizione", th),
        _p("Entrata", th),
        _p("Uscita", th),
    ]]
    for i, m in enumerate(q["nel"], start=1):
        entrata = ""
        uscita = ""
        if m in q["uscite"] or m in q["versamenti"]:
            uscita = formato_euro(m.importo)
        else:
            entrata = formato_euro(m.importo)
        desc = " — ".join(
            p for p in (m.beneficiario_fornitore or "", m.causale or "", formato_numero_sezionale(m)) if p
        )
        rows.append([
            _p(str(i), td),
            _p(m.data_movimento.strftime("%d/%m/%Y"), td),
            _p(_tipo(m), td),
            _p(desc or "—", td),
            _p(entrata, td),
            _p(uscita, td),
        ])
    if len(rows) == 1:
        rows.append([_p("—", td), _p("Nessun movimento", td), "", "", "", ""])

    usable = A4[0] - 4 * cm
    table = Table(
        rows,
        colWidths=[1.1 * cm, 2 * cm, 3.2 * cm, usable - 10.7 * cm, 2.2 * cm, 2.2 * cm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Giacenza all'inizio del trimestre: {formato_euro(q['giacenza_inizio'])}", td))
    story.append(Paragraph(f"Giacenza alla fine del trimestre: {formato_euro(q['giacenza_fine'])}", th))
    story.append(Paragraph(f"Saldo conto da registro a fine trimestre: {formato_euro(q['conto_fine'])}", td))
    story.append(Spacer(1, 0.5 * cm))
    story.append(disclaimer_registro())
    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
    )
    doc.build(story)
    return dest
