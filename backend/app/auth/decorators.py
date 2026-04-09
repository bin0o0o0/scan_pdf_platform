from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.errors import ApiError
from ..db.extensions import db
from ..models.user import User


def current_user_required(view_func):
    """验证 token，并把当前用户对象挂到 g.current_user 上。

    菜鸟教程里常见的是“路由函数里直接处理请求”。
    这里使用装饰器把重复的鉴权逻辑抽出来，接口层就能只关注自己的业务。
    """

    @wraps(view_func)
    @jwt_required()
    def wrapped(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user:
            raise ApiError("用户不存在。", 404)
        if user.status != "active":
            raise ApiError("当前用户已被禁用。", 403)

        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapped


def admin_required(view_func):
    """要求当前用户必须是管理员。"""

    @wraps(view_func)
    @current_user_required
    def wrapped(*args, **kwargs):
        if g.current_user.role != "admin":
            raise ApiError("需要管理员权限。", 403)
        return view_func(*args, **kwargs)

    return wrapped
