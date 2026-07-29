import os
from pathlib import Path

from flask import Flask

from app.config import INSTANCE_DIR, config_by_name
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=True,
    )
    cfg = config_by_name.get(config_name or "development")
    app.config.from_object(cfg)

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    (INSTANCE_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (INSTANCE_DIR / "backups").mkdir(parents=True, exist_ok=True)
    (INSTANCE_DIR / "verbali" / "ufficiali").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from flask import redirect, request, url_for

    from app.models import user as user_models

    @login_manager.unauthorized_handler
    def _unauthorized():
        return redirect(url_for("auth.login", next=request.path))

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(user_models.User, int(user_id))

    @app.template_filter("eur")
    def _eur(v):
        try:
            return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return "€ —"

    @app.template_filter("data_ora_cassa")
    def _data_ora_cassa(m):
        from app.services.movimento_display import formato_data_ora

        return formato_data_ora(m)

    @app.template_filter("tipo_mov_label")
    def _tipo_mov_label(m):
        from app.services.movimento_tipi import TIPO_MOVIMENTO_LABELS

        return TIPO_MOVIMENTO_LABELS.get(m.tipo, m.tipo.value)

    @app.template_filter("tipo_allegato_label")
    def _tipo_allegato_label(a):
        from app.services.allegato_tipi import TIPO_ALLEGATO_LABELS

        return TIPO_ALLEGATO_LABELS.get(a.tipo_documento, a.tipo_documento.value)

    from app.routes.auth import bp as auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.movimenti import bp as movimenti_bp
    from app.routes.buoni import bp as buoni_bp
    from app.routes.allegati import bp as allegati_bp
    from app.routes.impostazioni import bp as impostazioni_bp
    from app.routes.backup_export import bp as backup_export_bp
    from app.routes.filiali_banca import bp as filiali_banca_bp
    from app.routes.verbali import bp as verbali_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(movimenti_bp)
    app.register_blueprint(buoni_bp)
    app.register_blueprint(allegati_bp)
    app.register_blueprint(verbali_bp)
    app.register_blueprint(impostazioni_bp)
    app.register_blueprint(backup_export_bp)
    app.register_blueprint(filiali_banca_bp)

    with app.app_context():
        db.create_all()
        from app.services.schema_allegato import applica_schema_allegato
        from app.services.schema_cassa import applica_schema_cassa
        from app.services.schema_filiale import applica_schema_filiale_banca
        from app.services.schema_movimento import applica_patch_movimento
        from app.services.schema_verbale_verifica import applica_schema_verbale_verifica

        applica_patch_movimento()
        applica_schema_filiale_banca()
        applica_schema_allegato()
        applica_schema_verbale_verifica()
        applica_schema_cassa()
        _ensure_default_user(app)
        _ensure_settings_rows()

    return app


def _env_flag_true(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _ensure_default_user(app: Flask) -> None:
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    username = os.environ.get("ECONOMIA_PA_ADMIN_USER", "economo")
    password = os.environ.get("ECONOMIA_PA_ADMIN_PASSWORD")
    n = User.query.count()

    if n > 0:
        # ECONOMIA_PA_* vale solo alla prima creazione; per allineare un DB già
        # esistente imposta ECONOMIA_PA_ADMIN_SYNC=1 (una volta) con password nel .env.
        if n == 1 and _env_flag_true("ECONOMIA_PA_ADMIN_SYNC") and password:
            u = User.query.first()
            u.username = username.strip()
            u.password_hash = generate_password_hash(password)
            db.session.commit()
            app.logger.warning(
                "ECONOMIA_PA_ADMIN_SYNC: credenziali aggiornate dal .env. "
                "Rimuovi ECONOMIA_PA_ADMIN_SYNC dopo l'uso."
            )
        return

    if not password:
        password = "economo"
        app.logger.warning(
            "Utente iniziale creato con password predefinita 'economo'. "
            "Imposta ECONOMIA_PA_ADMIN_PASSWORD e riavvia."
        )
    u = User(
        username=username.strip(),
        password_hash=generate_password_hash(password),
        is_active=True,
    )
    db.session.add(u)
    db.session.commit()


def _ensure_settings_rows() -> None:
    from datetime import date

    from app.models.cassetto import SaldoAnnuale
    from app.models.economo import EconomoSettings
    from app.models.ente import EnteSettings

    if EnteSettings.query.get(1) is None:
        db.session.add(EnteSettings(id=1))
    if EconomoSettings.query.get(1) is None:
        db.session.add(EconomoSettings(id=1))
    y = date.today().year
    if SaldoAnnuale.query.get(y) is None:
        db.session.add(SaldoAnnuale(anno=y, saldo_iniziale=0, saldo_conto_iniziale=0))
    db.session.commit()
