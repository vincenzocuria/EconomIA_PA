"""Elementi comuni ReportLab per intestazione ente/economo."""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings
from app.services.economo_testo import nome_da_economo
from app.services.logo_ente import logo_ente_path


def intestazione_flowables():
    """Economo e blocchi collegati a sinistra; dati ente (ragione sociale, sede, CF) a destra."""
    ente = EnteSettings.query.get(1)
    eco = EconomoSettings.query.get(1)
    styles = getSampleStyleSheet()

    st_ente_tit = ParagraphStyle(
        name="IntestEnteTit",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1a365d"),
    )
    st_ente = ParagraphStyle(
        name="IntestEnte",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
    )
    st_eco_lab = ParagraphStyle(
        name="IntestEcoLab",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#4a5568"),
    )
    st_eco = ParagraphStyle(
        name="IntestEco",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    )

    usable_w = A4[0] - 4 * cm
    col_dx = usable_w * 0.54
    col_sx = usable_w - col_dx

    logo_riga = None
    pth = logo_ente_path()
    if pth is not None:
        try:
            img = Image(str(pth), width=3 * cm, height=2 * cm, kind="proportional")
            logo_riga = Table([[img]], colWidths=[usable_w])
            logo_riga.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
        except OSError:
            pass

    left_cell: list = []
    left_cell.append(Paragraph("<b>Economo</b>", st_eco_lab))
    if eco:
        nome = nome_da_economo(eco)
        if nome:
            left_cell.append(Paragraph(escape(nome), st_eco))
        if (eco.qualifica or "").strip():
            left_cell.append(Paragraph(escape(eco.qualifica.strip()), st_eco))
        if (eco.email or "").strip():
            left_cell.append(Paragraph(escape(f"e-mail: {eco.email.strip()}"), st_eco))
        if (eco.telefono or "").strip():
            left_cell.append(Paragraph(escape(f"tel. {eco.telefono.strip()}"), st_eco))
    else:
        left_cell.append(Paragraph("—", st_eco))

    right_cell: list = []
    if ente:
        denom = (ente.denominazione or "").strip() or "Ente"
        right_cell.append(Paragraph(escape(denom), st_ente_tit))
        ind = " ".join(
            x
            for x in [ente.indirizzo, ente.cap, ente.comune, ente.provincia]
            if (x or "").strip()
        )
        if ind:
            right_cell.append(Paragraph(escape(ind), st_ente))
        cf = (ente.codice_fiscale_ente or "").strip()
        if cf:
            right_cell.append(Paragraph(escape(f"C.F. / P.IVA: {cf}"), st_ente))
        if (ente.pec or "").strip():
            right_cell.append(Paragraph(escape(f"PEC: {ente.pec.strip()}"), st_ente))
        if (ente.telefono or "").strip():
            right_cell.append(Paragraph(escape(f"tel. {ente.telefono.strip()}"), st_ente))
    else:
        right_cell.append(Paragraph("—", st_ente))

    tab = Table([[left_cell, right_cell]], colWidths=[col_sx, col_dx])
    tab.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    out: list = []
    if logo_riga is not None:
        out.append(logo_riga)
        out.append(Spacer(1, 0.15 * cm))
    out.append(tab)
    out.append(Spacer(1, 0.55 * cm))
    return out


def disclaimer_registro():
    styles = getSampleStyleSheet()
    small = ParagraphStyle(
        name="Disclaimer",
        parent=styles["Normal"],
        fontSize=7,
        leading=10,
        textColor=colors.grey,
    )
    txt = (
        "Documento generato da registro locale di supporto (EconomIA_PA). "
        "Non costituisce sistema di conservazione digitale ai sensi delle norme vigenti; "
        "gli atti ufficiali restano nel protocollo e nella documentazione contabile dell'ente."
    )
    return Paragraph(txt, small)


def page_size():
    return A4
