"""Endpoint JSON ricerca e creazione anagrafiche."""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.extensions import db
from app.services.anagrafiche_lookup import (
    cerca_beneficiari,
    cerca_richiedenti,
    cerca_uffici,
    item_beneficiario,
)
from app.services.anagrafiche_sync import salva_beneficiario
from app.services.audit_log import scrivi_audit

bp = Blueprint("anagrafiche_api", __name__, url_prefix="/api/anagrafiche")


@bp.route("/richiedenti")
@login_required
def richiedenti():
    return jsonify({"items": cerca_richiedenti(request.args.get("q"))})


@bp.route("/uffici")
@login_required
def uffici():
    return jsonify({"items": cerca_uffici(request.args.get("q"))})


@bp.route("/beneficiari")
@login_required
def beneficiari():
    return jsonify({"items": cerca_beneficiari(request.args.get("q"))})


@bp.route("/beneficiari", methods=["POST"])
@login_required
def beneficiari_crea():
    data = request.get_json(silent=True) or {}
    row = salva_beneficiario(data.get("denominazione"), data.get("cf_piva"))
    if row is None:
        return jsonify({"ok": False, "error": "Inserisci la denominazione del fornitore."}), 400
    db.session.flush()
    scrivi_audit(
        "anagrafica_beneficiario",
        row.id,
        "creazione",
        {"denominazione": row.denominazione},
    )
    db.session.commit()
    return jsonify({"ok": True, "item": item_beneficiario(row)})
