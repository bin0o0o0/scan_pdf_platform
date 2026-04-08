from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.errors import ApiError
from ..models.user import User


def current_user_required(view_func):
    """这个装饰器把“验证 token + 读取当前用户 + 校验状态”收敛到一处，避免每个接口重复写。"""

    @wraps(view_func)
    @jwt_required()
    def wrapped(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            raise ApiError("用户不存在。", 404)
        if user.status != "active":
            raise ApiError("当前用户已被禁用。", 403)

        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    @current_user_required
    def wrapped(*args, **kwargs):
        if g.current_user.role != "admin":
            raise ApiError("需要管理员权限。", 403)
        return view_func(*args, **kwargs)

    return wrapped
