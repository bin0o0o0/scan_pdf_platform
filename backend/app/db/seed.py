from ..db.extensions import db
from ..models.user import User
from ..services.user_service import hash_password
from flask import current_app


def bootstrap_admin() -> None:
    """默认管理员只在不存在时创建，避免每次启动都覆盖用户真实数据。"""

    admin = User.query.filter_by(username=current_app.config["DEFAULT_ADMIN_USERNAME"]).first()
    if admin:
        return

    admin = User(
        username=current_app.config["DEFAULT_ADMIN_USERNAME"],
        password_hash=hash_password(current_app.config["DEFAULT_ADMIN_PASSWORD"]),
        role="admin",
        status="active",
    )
    db.session.add(admin)
    db.session.commit()

