"""Endpoint JSON per proporre il prossimo progressivo."""
from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.progressivi import prossimo_numero_buono, prossimo_numero_movimento

bp = Blueprint("progressivi_api", __name__, url_prefix="/api/progressivi")


@bp.route("/movimento")
@login_required
def prossimo_movimento():
    anno = int(request.args.get("anno", 0) or 0)
    sezionale_id = int(request.args.get("sezionale_id", 0) or 0)
    if not anno or not sezionale_id:
        return jsonify({"error": "parametri mancanti"}), 400
    return jsonify({"numero": prossimo_numero_movimento(anno, sezionale_id)})


@bp.route("/buono")
@login_required
def prossimo_buono():
    anno = int(request.args.get("anno", 0) or 0)
    sezionale_id = int(request.args.get("sezionale_id", 0) or 0)
    if not anno or not sezionale_id:
        return jsonify({"error": "parametri mancanti"}), 400
    return jsonify({"numero": prossimo_numero_buono(anno, sezionale_id)})
