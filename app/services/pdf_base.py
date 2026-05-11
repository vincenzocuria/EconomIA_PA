"""Elementi comuni ReportLab per intestazione ente/economo."""
from pathlib import Path

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Spacer

from app.models.economo import EconomoSettings
from app.models.ente import EnteSettings


def intestazione_flowables():
    ente = EnteSettings.query.get(1)
    eco = EconomoSettings.query.get(1)
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        name="TitoloEnte",
        parent=styles["Title"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1a365d"),
    )
    normal = ParagraphStyle(
        name="TestoEnte",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    out = []
    logo_path = (ente.logo_path or "").strip() if ente else ""
    if logo_path:
        p = Path(logo_path)
        if not p.is_absolute():
            p = Path(current_app.instance_path) / p
        if p.is_file():
            try:
                img = Image(str(p), width=3 * cm, height=2 * cm, kind="proportional")
                out.append(img)
                out.append(Spacer(1, 0.2 * cm))
            except OSError:
                pass
    if ente:
        out.append(Paragraph(ente.denominazione or "Ente", title))
        ind = " ".join(
            x
            for x in [ente.indirizzo, ente.cap, ente.comune, ente.provincia]
            if (x or "").strip()
        )
        if ind:
            out.append(Paragraph(ind, normal))
        cf = (ente.codice_fiscale_ente or "").strip()
        if cf:
            out.append(Paragraph(f"C.F. / P.IVA: {cf}", normal))
    out.append(Spacer(1, 0.4 * cm))
    if eco:
        nome = " ".join(x for x in [eco.nome, eco.cognome] if (x or "").strip())
        if nome:
            out.append(Paragraph(f"Economo: {nome}", normal))
        if (eco.qualifica or "").strip():
            out.append(Paragraph(eco.qualifica, normal))
    out.append(Spacer(1, 0.6 * cm))
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
