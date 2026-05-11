from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import INSTANCE_DIR
from app.models.buono import BuonoEconomale

from app.services.pdf_base import disclaimer_registro, intestazione_flowables


def genera_pdf_buono(b: BuonoEconomale) -> Path:
    pdf_dir = INSTANCE_DIR / "buoni_pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    path = pdf_dir / f"buono_{b.anno}_{b.numero_progressivo:04d}.pdf"

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        name="H1b",
        parent=styles["Heading1"],
        fontSize=15,
        textColor=colors.HexColor("#1a365d"),
    )

    story = intestazione_flowables()
    story.append(Paragraph("Buono economale", h1))
    story.append(Spacer(1, 0.3 * cm))

    stato_v = b.stato.value if hasattr(b.stato, "value") else str(b.stato)
    data = [
        ["Numero", f"{b.numero_progressivo:04d} / {b.anno}"],
        ["Data", b.data_buono.isoformat()],
        ["Stato", stato_v],
        ["Richiedente", b.richiedente or ""],
        ["Ufficio", b.ufficio_richiedente or ""],
        ["Causale", b.causale or ""],
        ["Importo autorizzato", f"{b.importo_autorizzato:,.2f}"],
        ["Importo speso", f"{b.importo_speso:,.2f}"],
        ["Beneficiario", b.beneficiario or ""],
        ["Note", b.note or ""],
    ]
    t = Table(data, colWidths=[4 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 1 * cm))
    now = datetime.now(timezone.utc).astimezone()
    story.append(Paragraph(f"Generato il {now.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(disclaimer_registro())

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    doc.build(story)
    return path
