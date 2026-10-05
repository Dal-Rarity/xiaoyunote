"""关注蓝图：粉丝/关注列表页、关注/取关接口、他人主页。

/follow 开头路由经 before_request 登录拦截；关注成功时写入通知。
"""
import json
import logging

from flask import Blueprint, render_template, request, session, make_response, url_for

from app.config.config import config
from app.settings import env
from common import response_message
from common.utils import model_to_json
from model.article import Article
from model.follow import Follow, db_session
from model.user import User

follow = Blueprint("follow", __name__)

# 登录拦截器(只拦截/follow开头的路由)
@follow.before_request
def follow_before_request():
    url = request.path
    is_login = session.get("is_login")
    if url.startswith("/follow") and is_login != 'true':
        response = make_response("登录重定向", 302)
        response.headers["location"] = url_for("index.home")
        return response

# 关注页面
@follow.route("/follow")
def follow_center():
    type_name = request.args.get("type")
    if type_name is None:
        type_name = "followers"
    user_id = session.get("user_id")

    follow_model = Follow()
    if type_name == "followers":
        follow_data = follow_model.get_followers(user_id)
    elif type_name == "following":
        follow_data = follow_model.get_following(user_id)
    else:
        return response_message.PersonalMessage.error("参数传递错误")

    # 拼接头像路径
    user_list = []
    for follow_record, user in follow_data:
        db_session.expunge(user)
        if not user.picture.startswith(config[env].user_header_image_path):
            user.picture = config[env].user_header_image_path + user.picture
        user_list.append(user)

    current_user = User().find_by_userid(user_id)
    follower_count = follow_model.get_follower_count(user_id)
    following_count = follow_model.get_following_count(user_id)

    return render_template("follow.html",
                           user_list=user_list,
                           type_name=type_name,
                           active=type_name,
                           user=current_user,
                           follower_count=follower_count,
                           following_count=following_count)

# 关注/取消关注接口
@follow.route("/follow/update_status", methods=["POST"])
def update_status():
    request_data = json.loads(request.data)
    follower_id = session.get("user_id")
    following_id = request_data.get("following_id")
    canceled = request_data.get("canceled")

    try:
        Follow().update_status(
            follower_id=follower_id,
            following_id=following_id,
            canceled=canceled
        )
        # 关注成功时(canceled=0)创建通知
        if canceled == 0:
            from model.notification import Notification
            Notification().create_notification(
                user_id=following_id,
                sender_id=follower_id,
                type="follow",
                article_id=None,
                content=None
            )
        return response_message.FollowMessage.success("关注")
    except Exception as e:
        logging.error(e)
        return response_message.FollowMessage.error("操作失败")

# 用户主页
@follow.route("/user/<int:user_id>")
def user_home(user_id):
    user = User().find_by_userid(user_id)
    if user is None:
        return render_template("404.html"), 404

    article = Article()
    article_data = article.get_article_by_userid(user_id)

    is_following = False
    current_user_id = session.get("user_id")
    if session.get("is_login") == 'true' and current_user_id != user_id:
        is_following = Follow().is_following(current_user_id, user_id)

    follower_count = Follow().get_follower_count(user_id)
    following_count = Follow().get_following_count(user_id)

    return render_template("user_home.html",
                           user=user,
                           article_data=article_data,
                           is_following=is_following,
                           follower_count=follower_count,
                           following_count=following_count,
                           is_self=(current_user_id == user_id))
