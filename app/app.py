import os

from flask import Flask

def create_app():
    app = Flask(__name__,template_folder="../template",static_url_path="",static_folder="../resource")
    # 注册蓝图
    init_blueprint(app)
    app.config['SECRET_KEY'] = os.urandom(24)
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

    # from controller.user import user
    # app.register_blueprint(user)