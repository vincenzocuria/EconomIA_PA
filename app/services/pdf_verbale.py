from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.movimento import Movimento, StatoMovimento
from app.models.verbale import VerbaleTrimestrale
from app.services.cassa import effetto_su_cassa, effetto_su_conto
from app.services.movimento_display import dettaglio_banca_breve
from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS
from app.services.numero_display import formato_numero_sezionale
from app.services.pdf_base import disclaimer_registro, intestazione_flowables


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    """Testo tabella con a capo automatico (evita sovrapposizione colonne)."""
    return Paragraph(escape(text or ""), style)


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
    ps_th = ParagraphStyle(
        name="verb_th",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#1a365d"),
    )
    ps_td = ParagraphStyle(
        name="verb_td",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6,
        leading=7.5,
        textColor=colors.black,
    )
    ps_td_num = ParagraphStyle(
        name="verb_td_num",
        parent=ps_td,
        alignment=TA_RIGHT,
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
    def _eur(v: Decimal) -> str:
        return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    rows: list[list] = [
        [
            _p("N.", ps_th),
            _p("Data", ps_th),
            _p("Tipo", ps_th),
            _p("Δ cassa", ps_th),
            _p("Δ conto", ps_th),
            _p("Causale", ps_th),
            _p("Beneficiario", ps_th),
            _p("Banca / ora", ps_th),
        ]
    ]
    tot_cassa = Decimal("0")
    tot_conto = Decimal("0")
    for m in movs:
        eff_c = effetto_su_cassa(m)
        eff_b = effetto_su_conto(m)
        tot_cassa += eff_c
        tot_conto += eff_b
        tipo_v = TIPO_MOVIMENTO_LABELS.get(m.tipo, m.tipo.value if hasattr(m.tipo, "value") else str(m.tipo))
        rows.append(
            [
                _p(formato_numero_sezionale(m), ps_td),
                _p(m.data_movimento.strftime("%d/%m/%Y"), ps_td),
                _p(tipo_v, ps_td),
                _p(_eur(eff_c), ps_td_num),
                _p(_eur(eff_b), ps_td_num),
                _p(m.causale or "—", ps_td),
                _p(m.beneficiario_fornitore or "—", ps_td),
                _p(dettaglio_banca_breve(m) or "—", ps_td),
            ]
        )
    rows.append(
        [
            _p("Variazione trimestre", ps_th),
            "",
            "",
            _p(_eur(tot_cassa), ps_td_num),
            _p(_eur(tot_conto), ps_td_num),
            "",
            "",
            "",
        ]
    )

    usable_w = A4[0] - 4 * cm
    col_w = [
        0.9 * cm,
        1.7 * cm,
        2.4 * cm,
        1.7 * cm,
        1.7 * cm,
        usable_w - (0.9 + 1.7 + 2.4 + 1.7 + 1.7 + 2.1 + 2.1) * cm,
        2.1 * cm,
        2.1 * cm,
    ]

    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff7ed")),
                ("SPAN", (0, -1), (2, -1)),
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
