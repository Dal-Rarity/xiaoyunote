"""消息通知蓝图：通知中心页面、未读数查询、单条/全部标记已读。

通知类型 follow/favorite/collection/comment 在页面层转换为
对应的文案与跳转链接（用户主页或文章详情）。
"""
import json
import logging

from flask import Blueprint, render_template, request, session, make_response, url_for

from app.config.config import config
from app.settings import env
from common import response_message
from common.utils import model_to_json
from model.notification import Notification, db_session
from model.user import User
from model.article import Article

notification_bp = Blueprint("notification", __name__)

# 登录拦截器
@notification_bp.before_request
def notification_before_request():
    url = request.path
    is_login = session.get("is_login")
    if url == "/message" and is_login != 'true':
        response = make_response("登录重定向", 302)
        response.headers["location"] = url_for("index.home")
        return response
    if url != "/message" and (not is_login or is_login != 'true'):
        return response_message.NotificationMessage.other("请登录")

# 消息页面
@notification_bp.route("/message")
def message_center():
    user_id = session.get("user_id")
    notification_model = Notification()

    notification_list = notification_model.get_notification_list(user_id)

    formatted_list = []
    for notification, sender, article in notification_list:
        # 安全地脱离会话
        try:
            db_session.expunge(sender)
        except Exception:
            pass
        if not sender.picture.startswith(config[env].user_header_image_path):
            sender.picture = config[env].user_header_image_path + sender.picture

        if notification.type == "follow":
            link = "/user/" + str(notification.sender_id)
            type_text = "关注了你"
        elif notification.type in ("favorite", "collection", "comment"):
            link = "/detail?article_id=" + str(notification.article_id)
            if notification.type == "favorite":
                type_text = "喜欢了你的文章"
            elif notification.type == "collection":
                type_text = "收藏了你的文章"
            else:
                type_text = "评论了你的文章"
        else:
            link = "#"
            type_text = "未知通知"

        formatted_list.append({
            "notification": notification,
            "sender": sender,
            "article": article,
            "link": link,
            "type_text": type_text
        })

    current_user = User().find_by_userid(user_id)
    unread_count = notification_model.get_unread_count(user_id)

    return render_template("message.html",
                           notification_list=formatted_list,
                           user=current_user,
                           unread_count=unread_count)

# 获取未读消息数量
@notification_bp.route("/message/unread_count")
def unread_count():
    user_id = session.get("user_id")
    if not user_id:
        return response_message.NotificationMessage.other("未登录")
    count = Notification().get_unread_count(user_id)
    return response_message.NotificationMessage.success(count)

# 标记单条消息为已读
@notification_bp.route("/message/read", methods=["POST"])
def mark_read():
    request_data = json.loads(request.data)
    notification_id = request_data.get("notification_id")
    try:
        Notification().mark_as_read(notification_id)
        return response_message.NotificationMessage.success("已读")
    except Exception as e:
        logging.error(e)
        return response_message.NotificationMessage.error("操作失败")

# 标记所有消息为已读
@notification_bp.route("/message/read_all", methods=["POST"])
def mark_all_read():
    user_id = session.get("user_id")
    try:
        Notification().mark_all_as_read(user_id)
        return response_message.NotificationMessage.success("全部已读")
    except Exception as e:
        logging.error(e)
        return response_message.NotificationMessage.error("操作失败")
