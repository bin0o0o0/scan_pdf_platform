from sqlalchemy import text
from flask import Blueprint, jsonify

from ..db.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    database_status = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    status = "ok" if database_status == "ok" else "degraded"
    code = 200 if status == "ok" else 503
    return (
        jsonify(
            {
                "status": status,
                "checks": {
                    "database": database_status,
                },
            }
        ),
        code,
    )

