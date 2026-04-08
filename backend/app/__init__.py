from flask import Flask

from .api.admin import admin_bp
from .api.auth import auth_bp
from .api.health import health_bp
from .api.scan import scan_bp
from .core.config import Config
from .core.errors import register_error_handlers
from .db.extensions import cors, db, jwt
from .db.seed import bootstrap_admin


def create_app(config_object: type[Config] | None = None) -> Flask:
    """应用工厂模式的价值在于：测试、开发、生产都能按需创建不同配置的实例。"""

    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}},
        supports_credentials=False,
    )

    register_error_handlers(app)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(scan_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    with app.app_context():
        # 这里把“建表”和“默认管理员初始化”放在应用启动早期，是为了让空库也能直接进入可用状态。
        db.create_all()
        bootstrap_admin()

    return app

