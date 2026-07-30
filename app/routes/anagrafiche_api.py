"""Endpoint JSON ricerca incrementale anagrafiche."""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.anagrafiche_lookup import (
    cerca_beneficiari,
    cerca_richiedenti,
    cerca_uffici,
)

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
