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
    """创建并配置 Flask 应用实例。

    这就是菜鸟教程里常说的“应用对象”。
    这里进一步使用了应用工厂模式，方便测试环境、开发环境、生产环境
    按需创建不同配置的 app。
    """

    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    # 这些扩展对象先在 extensions.py 中创建，再在这里和具体 app 绑定。
    # 这样做的好处是：模块之间不会互相提前依赖，测试时也更容易替换配置。
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGIN"]}},
        supports_credentials=False,
    )

    register_error_handlers(app)

    # Blueprint 可以理解成“按功能拆分后的路由分组”。
    # 菜鸟教程里讲到路由时通常是直接写在 app 上，这里则是更适合中型项目的组织方式。
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(scan_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    with app.app_context():
        # create_all() 会根据模型定义建表。
        # 对学习项目来说，这样最直观；正式项目一般会换成迁移工具。
        # bootstrap_admin() 则确保空库第一次启动时也有默认管理员账号可用。
        db.create_all()
        bootstrap_admin()

    return app
