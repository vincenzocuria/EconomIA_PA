from app.extensions import db


class EconomoSettings(db.Model):
    """Dati economo per intestazioni e verbali (singola riga id=1)."""

    __tablename__ = "economo_settings"

    id = db.Column(db.Integer, primary_key=True)
    cognome = db.Column(db.String(120), default="")
    nome = db.Column(db.String(120), default="")
    codice_fiscale = db.Column(db.String(32), default="")
    qualifica = db.Column(db.String(200), default="Economo comunale")
    incarico_dal = db.Column(db.Date, nullable=True)
    delibera_nomina = db.Column(db.String(200), default="")
    telefono = db.Column(db.String(80), default="")
    email = db.Column(db.String(200), default="")
    note = db.Column(db.Text, default="")
    determina_path = db.Column(db.String(500), default="")
    regolamento_path = db.Column(db.String(500), default="")
