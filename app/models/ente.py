from app.extensions import db


class EnteSettings(db.Model):
    """Dati ente per documenti e carta intestata (singola riga id=1)."""

    __tablename__ = "ente_settings"

    id = db.Column(db.Integer, primary_key=True)
    denominazione = db.Column(db.String(500), default="")
    codice_fiscale_ente = db.Column(db.String(32), default="")
    codice_istat = db.Column(db.String(16), default="")
    indirizzo = db.Column(db.String(500), default="")
    cap = db.Column(db.String(16), default="")
    comune = db.Column(db.String(200), default="")
    provincia = db.Column(db.String(8), default="")
    pec = db.Column(db.String(200), default="")
    email = db.Column(db.String(200), default="")
    telefono = db.Column(db.String(80), default="")
    logo_path = db.Column(db.String(500), default="")
    note_legali = db.Column(db.Text, default="")
