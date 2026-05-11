from app.extensions import db


class BackupRun(db.Model):
    __tablename__ = "backup_run"

    id = db.Column(db.Integer, primary_key=True)
    eseguito_il = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    percorso_zip = db.Column(db.String(500), default="")
    ok = db.Column(db.Boolean, default=True, nullable=False)
    messaggio = db.Column(db.String(500), default="")
