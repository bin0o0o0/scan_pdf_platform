from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """表示“可预期的业务错误”。

    比如参数不合法、用户不存在、权限不足等，都可以抛 ApiError，
    然后统一转成 JSON 响应返回给前端。
    """

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_error_handlers(app: Flask) -> None:
    """集中注册全局错误处理器。"""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        """把自定义业务错误统一转成 JSON。"""

        return jsonify({"message": error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        """兜底处理 Flask / Werkzeug 自带的 HTTP 错误。"""

        return jsonify({"message": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """处理未捕获异常，避免把 Python 堆栈直接暴露给前端。"""

        app.logger.exception("unexpected_error", exc_info=error)
        return jsonify({"message": "服务器内部错误，请稍后重试。"}), 500
