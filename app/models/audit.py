from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    entita = db.Column(db.String(80), nullable=False, index=True)
    entita_id = db.Column(db.Integer, nullable=True, index=True)
    azione = db.Column(db.String(80), nullable=False)
    dettaglio = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    utente = db.relationship("User", backref=db.backref("audit_logs", lazy="dynamic"))
