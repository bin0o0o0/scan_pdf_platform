import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


class Config:
    """集中读取环境变量，避免在业务代码里到处散落 os.getenv。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "scan-pdf-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        (
            f"mysql+pymysql://{os.getenv('MYSQL_USER', 'scan_user')}:"
            f"{os.getenv('MYSQL_PASSWORD', 'scan_pass')}@"
            f"{os.getenv('MYSQL_HOST', 'localhost')}:"
            f"{os.getenv('MYSQL_PORT', '3306')}/"
            f"{os.getenv('MYSQL_DATABASE', 'scan_pdf')}"
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123456")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_ROOT = BASE_DIR / "uploads"
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"
    TESTING = False


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    FRONTEND_ORIGIN = "*"

