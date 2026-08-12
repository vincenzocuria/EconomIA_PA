from datetime import date
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models.buono import BuonoEconomale
from app.models.cassetto import SaldoAnnuale
from app.models.movimento import Movimento
from app.models.verbale_verifica import VerbaleVerifica
from app.services.alerts import prossima_scadenza_verbale, raccogli_alert, trimestre_corrente, ultimo_backup
from app.services.cassa import (
    saldo_cassa_calcolato,
    saldo_conto_calcolato,
    totale_entrate,
    totale_uscite,
)
from app.services.cassa_livello import badge_cassa
from app.services.dashboard_charts import dati_grafici_dashboard
from app.services.dashboard_todo import cose_da_fare
from app.services.ultimo_banca import ultimo_prelievo, ultimo_versamento

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    anno = int(request.args.get("anno", date.today().year))
    saldo_row = SaldoAnnuale.query.get(anno)
    ini_cassa = Decimal(str(saldo_row.saldo_iniziale)) if saldo_row else Decimal("0")
    ini_conto = (
        Decimal(str(getattr(saldo_row, "saldo_conto_iniziale", 0) or 0)) if saldo_row else Decimal("0")
    )
    saldo_cassa = saldo_cassa_calcolato(anno, ini_cassa)
    saldo_conto = saldo_conto_calcolato(anno, ini_conto)
    n_mov = Movimento.query.filter_by(anno=anno).count()
    n_buoni = BuonoEconomale.query.filter_by(anno=anno).count()
    ultimo_v = (
        VerbaleVerifica.query.filter_by(anno=anno)
        .order_by(VerbaleVerifica.data_verbale.desc(), VerbaleVerifica.numero.desc())
        .first()
    )
    ultimo_verbale_label = None
    if ultimo_v is not None:
        ultimo_verbale_label = (
            f"n. {ultimo_v.numero} — T{ultimo_v.trimestre} — "
            f"{ultimo_v.data_verbale.strftime('%d/%m/%Y')}"
        )
    recenti = Movimento.query.filter_by(anno=anno).order_by(Movimento.created_at.desc()).limit(8).all()
    todo = cose_da_fare(anno)
    alert_extra = [a for a in raccogli_alert(anno) if a["livello"] in ("danger", "secondary")]
    charts = dati_grafici_dashboard(anno, ini_cassa)
    y, t = trimestre_corrente()
    scad = prossima_scadenza_verbale(anno)
    return render_template(
        "dashboard.html",
        anno=anno,
        saldo_cassa_iniziale=ini_cassa,
        saldo_cassa_attuale=saldo_cassa,
        badge_cassa_attuale=badge_cassa(saldo_cassa),
        saldo_conto_iniziale=ini_conto,
        saldo_conto_attuale=saldo_conto,
        tot_entrate=totale_entrate(anno),
        tot_uscite=totale_uscite(anno),
        n_mov=n_mov,
        n_buoni=n_buoni,
        ultimo_verbale_label=ultimo_verbale_label,
        prossima_scadenza=scad,
        trimestre_corrente=t if anno == y else 4,
        movimenti_recenti=recenti,
        ultimo_prelievo=ultimo_prelievo(anno),
        ultimo_versamento=ultimo_versamento(anno),
        todo=todo,
        alert_extra=alert_extra,
        charts=charts,
        ultimo_backup=ultimo_backup(),
    )
