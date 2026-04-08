from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from ..core.errors import ApiError
from ..db.extensions import db
from ..models.user import User


def hash_password(raw_password: str) -> str:
    # 使用 werkzeug 自带哈希足以覆盖当前学习项目，代码也更容易读懂。
    return generate_password_hash(raw_password)


def verify_password(password_hash: str, raw_password: str) -> bool:
    return check_password_hash(password_hash, raw_password)


def validate_username_and_password(payload: dict[str, Any]) -> tuple[str, str]:
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if len(username) < 3:
        raise ApiError("用户名至少需要 3 个字符。", 400)
    if len(password) < 6:
        raise ApiError("密码至少需要 6 个字符。", 400)

    return username, password


def create_user(username: str, password: str) -> User:
    if User.query.filter_by(username=username).first():
        raise ApiError("用户名已存在。", 409)

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username: str, password: str) -> User:
    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        raise ApiError("用户名或密码错误。", 401)
    if user.status != "active":
        raise ApiError("当前用户已被禁用。", 403)
    return user


def update_password(user: User, old_password: str, new_password: str) -> None:
    if not verify_password(user.password_hash, old_password):
        raise ApiError("旧密码不正确。", 400)
    if len(new_password) < 6:
        raise ApiError("新密码至少需要 6 个字符。", 400)

    user.password_hash = hash_password(new_password)
    db.session.commit()


def update_user_role(user: User, role: str) -> User:
    if role not in {"user", "admin"}:
        raise ApiError("角色只能是 user 或 admin。", 400)
    user.role = role
    db.session.commit()
    return user


def update_user_status(user: User, status: str) -> User:
    if status not in {"active", "disabled"}:
        raise ApiError("状态只能是 active 或 disabled。", 400)
    user.status = status
    db.session.commit()
    return user

