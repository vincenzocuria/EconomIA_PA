from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.movimento import Movimento, StatoMovimento, TipoMovimento
from app.models.verbale import VerbaleTrimestrale
from app.services.cassa import effetto_su_saldo
from app.services.movimento_display import dettaglio_banca_breve
from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS
from app.services.pdf_base import disclaimer_registro, intestazione_flowables


def genera_verbale_trimestrale_pdf(anno: int, trimestre: int) -> Path:
    from decimal import Decimal

    pdf_dir = INSTANCE_DIR / "verbali"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    fname = f"verbale_{anno}_T{trimestre}.pdf"
    path = pdf_dir / fname

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a365d"),
    )

    story = intestazione_flowables()
    story.append(
        Paragraph(
            f"Verbale trimestrale cassa economale — Anno {anno} — Trimestre {trimestre}",
            h1,
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    movs = (
        Movimento.query.filter(
            Movimento.anno == anno,
            Movimento.trimestre == trimestre,
            Movimento.stato != StatoMovimento.stornato,
        )
        .order_by(Movimento.numero_progressivo)
        .all()
    )
    rows = [["N.", "Data", "Tipo", "Importo", "Causale", "Beneficiario", "Banca / ora"]]
    tot = Decimal("0")
    for m in movs:
        eff = effetto_su_saldo(m)
        tot += eff
        tipo_v = TIPO_MOVIMENTO_LABELS.get(m.tipo, m.tipo.value if hasattr(m.tipo, "value") else str(m.tipo))
        rows.append(
            [
                f"{m.numero_progressivo:04d}",
                m.data_movimento.isoformat(),
                tipo_v,
                f"{eff:,.2f}",
                (m.causale or "")[:55],
                (m.beneficiario_fornitore or "")[:35],
                dettaglio_banca_breve(m)[:42],
            ]
        )
    rows.append(["", "", "Saldo movimenti trim.", f"{tot:,.2f}", "", "", ""])

    t = Table(rows, colWidths=[1.1 * cm, 2 * cm, 2 * cm, 2.2 * cm, 4.2 * cm, 2.5 * cm, 2.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff7ed")),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.8 * cm))
    now = datetime.now(timezone.utc).astimezone()
    story.append(Paragraph(f"Generato il {now.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(disclaimer_registro())

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)

    rel = path.relative_to(INSTANCE_DIR).as_posix()
    v = VerbaleTrimestrale.query.filter_by(anno=anno, trimestre=trimestre).first()
    if v:
        v.percorso_pdf = rel
        v.generato_il = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        db.session.add(
            VerbaleTrimestrale(
                anno=anno,
                trimestre=trimestre,
                percorso_pdf=rel,
            )
        )
    db.session.commit()
    return path
