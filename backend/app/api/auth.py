from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import create_access_token

from ..auth.decorators import current_user_required
from ..core.errors import ApiError
from ..services.user_service import (
    authenticate_user,
    create_user,
    update_password,
    validate_username_and_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """注册新用户并返回最小化的用户资料。"""

    payload = request.get_json(silent=True) or {}
    username, password = validate_username_and_password(payload)
    user = create_user(username, password)
    return jsonify({"message": "注册成功。", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    """校验账号密码并签发 JWT 令牌。"""

    payload = request.get_json(silent=True) or {}
    username, password = validate_username_and_password(payload)
    user = authenticate_user(username, password)

    # token 里只放 user id，而不把用户名、角色等都塞进去，
    # 是为了避免令牌里缓存太多“可能变化”的信息。
    # 真正需要当前用户资料时，再去查询数据库拿最新状态。
    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@current_user_required
def me():
    """返回当前登录用户信息。"""

    return jsonify({"user": g.current_user.to_dict()})


@auth_bp.patch("/password")
@current_user_required
def change_password():
    """修改当前用户密码。"""

    payload = request.get_json(silent=True) or {}
    old_password = payload.get("old_password") or ""
    new_password = payload.get("new_password") or ""
    if not old_password or not new_password:
        raise ApiError("旧密码和新密码都不能为空。", 400)

    update_password(g.current_user, old_password, new_password)
    return jsonify({"message": "密码修改成功。"})
