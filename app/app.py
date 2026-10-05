"""应用工厂模块。

create_app() 负责创建 Flask 实例：
- 模板目录指向项目根的 template/，静态资源目录指向 resource/
  （static_url_path="" 使静态资源以根路径访问，如 /css/base.css）
- 集中注册全部业务蓝图（用户、首页、文章、收藏、评论等）
- 加载会话密钥 SECRET_KEY（环境变量 > .secret_key 文件 > 自动生成）
"""
import os

from flask import Flask

_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".secret_key")


def _load_secret_key():
    """SECRET_KEY 优先级：环境变量 SECRET_KEY（容器部署）> 持久化文件（本地开发）> 自动生成"""
    env_key = os.getenv("SECRET_KEY", "").strip()
    if env_key:
        return env_key
    try:
        with open(_SECRET_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        key = os.urandom(24).hex()
        with open(_SECRET_FILE, "w", encoding="utf-8") as f:
            f.write(key)
        return key


def create_app():
    app = Flask(__name__,template_folder="../template",static_url_path="",static_folder="../resource")
    # 注册蓝图
    init_blueprint(app)
    app.config['SECRET_KEY'] = _load_secret_key()
    return app

def init_blueprint(app):
    from controller.user import user
    app.register_blueprint(user)

    # 注册首页蓝图
    from controller.index import index
    app.register_blueprint(index)

    #文章页面注册
    from controller.article import article
    app.register_blueprint(article)

    # 喜欢的蓝图注册
    from controller.favorite import favorite
    app.register_blueprint(favorite)

    # 收藏的蓝图注册
    from controller.collection import collection
    app.register_blueprint(collection)

    # 评论的蓝图注册
    from controller.feedback import feedback
    app.register_blueprint(feedback)

    # 个人中心的蓝图注册
    from controller.personal import personal
    app.register_blueprint(personal)

    # 关注的蓝图注册
    from controller.follow import follow
    app.register_blueprint(follow)

    # 消息通知的蓝图注册
    from controller.notification import notification_bp
    app.register_blueprint(notification_bp)

    #邮箱缓存蓝图注册
    from controller.redis_user import redis_user
    app.register_blueprint(redis_user)

    # 智能知识库助手蓝图注册
    from controller.ai import ai
    app.register_blueprint(ai)

    # 下线 T10 MVP 蓝图
    # from controller.ai_mvp import ai_mvp
    # app.register_blueprint(ai_mvp)