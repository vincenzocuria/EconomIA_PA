from datetime import date
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models.buono import BuonoEconomale
from app.models.cassetto import SaldoAnnuale
from app.models.movimento import Movimento, StatoMovimento
from app.models.verbale import VerbaleTrimestrale
from app.services.alerts import prossima_scadenza_verbale, raccogli_alert, trimestre_corrente, ultimo_backup
from app.services.cassa import saldo_calcolato, totale_entrate, totale_uscite

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    anno = int(request.args.get("anno", date.today().year))
    saldo_row = SaldoAnnuale.query.get(anno)
    ini = Decimal(str(saldo_row.saldo_iniziale)) if saldo_row else Decimal("0")
    saldo = saldo_calcolato(anno, ini)
    n_mov = Movimento.query.filter_by(anno=anno).count()
    n_buoni = BuonoEconomale.query.filter_by(anno=anno).count()
    allegati_mancanti = 0
    for m in Movimento.query.filter_by(anno=anno).filter(Movimento.stato != StatoMovimento.stornato):
        if m.allegati.count() == 0:
            allegati_mancanti += 1
    ultimo_v = (
        VerbaleTrimestrale.query.filter_by(anno=anno).order_by(VerbaleTrimestrale.generato_il.desc()).first()
    )
    recenti = Movimento.query.filter_by(anno=anno).order_by(Movimento.created_at.desc()).limit(8).all()
    alert = raccogli_alert(anno)
    y, t = trimestre_corrente()
    scad = prossima_scadenza_verbale(anno)
    return render_template(
        "dashboard.html",
        anno=anno,
        saldo_iniziale=ini,
        saldo_attuale=saldo,
        tot_entrate=totale_entrate(anno),
        tot_uscite=totale_uscite(anno),
        n_mov=n_mov,
        n_buoni=n_buoni,
        allegati_mancanti=allegati_mancanti,
        ultimo_verbale=ultimo_v,
        prossima_scadenza=scad,
        trimestre_corrente=t if anno == y else 4,
        movimenti_recenti=recenti,
        alert=alert,
        ultimo_backup=ultimo_backup(),
    )
