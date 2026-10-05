"""个人中心蓝图：我的文章/收藏/评论/设置页签，资料更新与头像上传压缩。

/personal 开头路由经 before_request 登录拦截。
"""
import json
import logging
import os
import random
import time

from flask import Blueprint, render_template, request, abort, session, jsonify, make_response, url_for

from app.config.config import config
from app.settings import env
from common import response_message
from common.utils import compress_image, model_to_json
from controller.article import article
from model.article import Article
from model.favorite import Favorite, db_session
from model.collection import Collection
from model.feedback import Feedback
from model.user import User

personal = Blueprint("personal", __name__)

# 判断登录状态
@personal.before_request
def personal_before_request():
    url = request.path
    is_login = session.get("is_login")
    if url.startswith("/personal") and is_login != 'true':
        response = make_response("登录重定向",302)
        response.headers["location"] = url_for("index.home")
        return response

@personal.route("/personal")
def personal_center():
    # url  ?type=我的评论、我的收藏
    type_name = request.args.get("type")
    if type_name is None:
        type_name = "article"
    user_id = session.get("user_id")
    user = User().find_by_userid(user_id)
    #如果是文章
    article = Article()
    if type_name == "article":
        article_data = article.get_article_by_userid(user_id)
    # 如果是收藏
    elif type_name == "collection":
        article_data = article.get_collection_article_by_userid(user_id)
    # 如果是评论
    elif type_name == "feedback":
        article_data = article.get_feedback_article_by_userid(user_id)
    elif type_name == "settings":
        article_data = []
    else:
        return response_message.PersonalMessage.error("参数传递错误")
    return render_template("personal_center.html",
                           article_data=article_data,
                           type_name=type_name,
                           active=type_name,
                           user=user)


@personal.route("/personal/update_settings", methods=['POST'])
def update_settings():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"code": 401, "msg": "未登录"})
    u = User.get_by_id(user_id)
    if not u:
        return jsonify({"code": 404, "msg": "用户不存在"})
    data = request.get_json()
    u.update_profile(
        nickname=data.get("nickname"),
        gender=data.get("gender"),
        age=data.get("age"),
        address=data.get("address"),
        bio=data.get("bio")
    )
    # 同步更新 session
    if data.get("nickname"):
        session["nickname"] = data.get("nickname")
    return jsonify({"code": 200, "msg": "保存成功"})


@personal.route("/personal/upload_avatar", methods=['POST'])
def upload_avatar():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"code": 401, "msg": "未登录"})
    u = User.get_by_id(user_id)
    if not u:
        return jsonify({"code": 404, "msg": "用户不存在"})
    file = request.files.get("file")
    if not file:
        return jsonify({"code": 400, "msg": "未选择文件"})
    # 保存并压缩头像
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resource", "images", "headers")
    filename = f"user_{user_id}_{int(time.time())}.jpg"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    compress_image(filepath)
    # 更新数据库（存相对路径）
    picture_path = f"/images/headers/{filename}"
    u.update_profile(picture=picture_path)
    session["picture"] = picture_path
    return jsonify({"code": 200, "msg": "头像更新成功", "picture": picture_path})