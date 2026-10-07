"""Prospetto pagamenti del trimestre (buoni, prelievi, giacenza)."""

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
from app.services.numero_display import formato_numero_sezionale
from app.services.pdf_base import disclaimer_registro, intestazione_flowables


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text or ""), style)


def genera_prospetto_pagamenti(anno: int, trimestre: int, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    q = quadratura_trimestre(anno, trimestre, chiusura_di(anno, trimestre))
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("prop_h", parent=styles["Heading1"], fontSize=14, textColor=colors.HexColor("#1a365d"))
    th = ParagraphStyle("prop_th", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10)
    td = ParagraphStyle("prop_td", parent=styles["Normal"], fontSize=8, leading=10)
    story = intestazione_flowables()
    story.append(Paragraph(f"Prospetto pagamenti — {trimestre}° trimestre {anno}", h1))
    story.append(
        Paragraph(
            f"Periodo {q['inizio'].strftime('%d/%m/%Y')} – {q['fine'].strftime('%d/%m/%Y')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    rows = [[_p("N. buono", th), _p("Data", th), _p("Beneficiario", th), _p("Causale", th), _p("Somma", th)]]
    for m in q["uscite"]:
        num = formato_numero_sezionale(m.buono) if m.buono else formato_numero_sezionale(m)
        rows.append(
            [
                _p(num, td),
                _p(m.data_movimento.strftime("%d/%m/%Y"), td),
                _p(m.beneficiario_fornitore or "—", td),
                _p(m.causale or "—", td),
                _p(formato_euro(m.importo), td),
            ]
        )
    if len(rows) == 1:
        rows.append([_p("Nessuna uscita nel trimestre", td), "", "", "", ""])
    usable = A4[0] - 4 * cm
    table = Table(rows, colWidths=[2.6 * cm, 2.2 * cm, 4.2 * cm, usable - 11.2 * cm, 2.2 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"N. {len(q['uscite'])} buoni — totale {formato_euro(q['totale_uscite'])}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Prelievi contanti", th))
    if q["prelievi"]:
        for m in q["prelievi"]:
            story.append(
                Paragraph(
                    f"{m.data_movimento.strftime('%d/%m/%Y')} — {formato_euro(m.importo)} — {formato_numero_sezionale(m)}",
                    td,
                )
            )
    else:
        story.append(Paragraph("Nessun prelievo nel trimestre.", td))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            f"Giacenza di cassa a fine trimestre: {formato_euro(q['giacenza_fine'])}",
            th,
        )
    )
    story.append(Spacer(1, 0.6 * cm))
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
