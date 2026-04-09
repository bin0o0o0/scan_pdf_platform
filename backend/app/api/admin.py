from flask import Blueprint, jsonify, request

from ..auth.decorators import admin_required
from ..core.errors import ApiError
from ..db.extensions import db
from ..models.user import User
from ..services.user_service import update_user_role, update_user_status

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@admin_required
def list_users():
    """返回用户列表，供管理员页展示。"""

    users = User.query.order_by(User.created_at.asc()).all()
    return jsonify({"users": [user.to_dict() for user in users]})


@admin_bp.patch("/users/<int:user_id>/status")
@admin_required
def patch_user_status(user_id: int):
    """修改用户状态，例如 active / disabled。"""

    user = db.session.get(User, user_id)
    if not user:
        raise ApiError("用户不存在。", 404)

    payload = request.get_json(silent=True) or {}
    updated = update_user_status(user, payload.get("status") or "")
    return jsonify({"user": updated.to_dict()})


@admin_bp.patch("/users/<int:user_id>/role")
@admin_required
def patch_user_role(user_id: int):
    """修改用户角色，例如 user / admin。"""

    user = db.session.get(User, user_id)
    if not user:
        raise ApiError("用户不存在。", 404)

    payload = request.get_json(silent=True) or {}
    updated = update_user_role(user, payload.get("role") or "")
    return jsonify({"user": updated.to_dict()})
