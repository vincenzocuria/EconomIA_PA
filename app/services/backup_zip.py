import zipfile
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.config import INSTANCE_DIR
from app.extensions import db
from app.models.backup_run import BackupRun


def esegui_backup_zip() -> tuple[bool, str, Path | None]:
    """Crea ZIP con database SQLite, uploads e verbali."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = INSTANCE_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    zip_path = backup_dir / f"economia_pa_backup_{ts}.zip"

    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not db_uri.startswith("sqlite:///"):
        msg = "Backup automatico supportato solo per SQLite."
        db.session.add(BackupRun(ok=False, messaggio=msg, percorso_zip=""))
        db.session.commit()
        return False, msg, None

    db_path = Path(db_uri.replace("sqlite:///", "", 1))
    uploads = INSTANCE_DIR / "uploads"
    verbali = INSTANCE_DIR / "verbali"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if db_path.is_file():
                zf.write(db_path, arcname="economia_pa.sqlite3")
            if uploads.is_dir():
                for f in uploads.rglob("*"):
                    if f.is_file():
                        zf.write(f, arcname=f"uploads/{f.relative_to(uploads).as_posix()}")
            if verbali.is_dir():
                for f in verbali.rglob("*"):
                    if f.is_file():
                        zf.write(f, arcname=f"verbali/{f.relative_to(verbali).as_posix()}")
        db.session.add(BackupRun(ok=True, messaggio="OK", percorso_zip=str(zip_path)))
        db.session.commit()
        return True, "Backup creato.", zip_path
    except OSError as e:
        db.session.add(BackupRun(ok=False, messaggio=str(e), percorso_zip=""))
        db.session.commit()
        return False, str(e), None
