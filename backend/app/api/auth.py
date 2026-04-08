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
    payload = request.get_json(silent=True) or {}
    username, password = validate_username_and_password(payload)
    user = create_user(username, password)
    return jsonify({"message": "注册成功。", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username, password = validate_username_and_password(payload)
    user = authenticate_user(username, password)

    # token 里只放 user id，是为了尽量避免把易变化的信息固化到令牌里。
    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@current_user_required
def me():
    return jsonify({"user": g.current_user.to_dict()})


@auth_bp.patch("/password")
@current_user_required
def change_password():
    payload = request.get_json(silent=True) or {}
    old_password = payload.get("old_password") or ""
    new_password = payload.get("new_password") or ""
    if not old_password or not new_password:
        raise ApiError("旧密码和新密码都不能为空。", 400)

    update_password(g.current_user, old_password, new_password)
    return jsonify({"message": "密码修改成功。"})

