import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or "dev-only-cambia-in-produzione"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    UPLOAD_ALLOWED_EXT = frozenset({"pdf", "jpg", "jpeg", "png", "webp"})
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14


class DevelopmentConfig(Config):
    DEBUG = True
    # HTTP locale: evita controlli referrer HTTPS che possono confondere proxy/dev
    WTF_CSRF_SSL_STRICT = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + str(INSTANCE_DIR / "economia_pa.sqlite3")
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + str(INSTANCE_DIR / "economia_pa.sqlite3")
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
