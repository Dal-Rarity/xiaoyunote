"""评论蓝图：UEditor 评论编辑器配置/图片上传、发表一级评论与回复评论。

全部路由经 before_request 登录拦截；评论/回复成功后向文章作者发通知。
"""
import json
import logging
from datetime import time

from flask import Blueprint, render_template, request, abort, session, make_response, jsonify

from app.config.config import config
from app.config.ue_config import FEEDBACK_UECONFIG
from app.settings import env
from common import response_message
from common.utils import compress_image, model_to_json
from model.article import Article
from model.favorite import Favorite, db_session
from model.collection import Collection
from model.feedback import Feedback
from model.user import User

feedback = Blueprint("feedback", __name__)

# 拦截器设置
@feedback.before_request
def before_comment():
    if session.get("is_login") is None or session.get("is_login") != "true":
        return {"status": 9999,"data": "您好，请登录!"}

# 对接UE的接口开发
@feedback.route("/feedback", methods=["GET", "POST"])
def ueditor():
    param = request.args.get("action")
    print(param)
    if request.method == "GET" and param == "config":
        return make_response(FEEDBACK_UECONFIG)
    # 做图片上传的代码
    elif param == "image":
        f = request.files.get("file")
        filename = f.filename
        # 文件后缀名
        suffix = filename.split(".")[-1]
        newname = time.strftime("%Y%m%d_%H%M%S."+suffix)
        f.save("resource/upload/"+newname)
        #大图片压缩
        source = dest =  "resource/upload/"+newname
        compress_image(source,dest,1200)
        # 构造响应数据
        result = {}
        result["state"] = "SUCCESS"
        result['url'] = "/upload/"+newname
        result["title"] = filename
        result["original"] = filename
        return jsonify(result)
    else:
        # 其他 action（如 listimage 等）不做支持，返回空成功响应避免500
        return jsonify({"state": "SUCCESS"})

# 添加发表评论的接口开发
@feedback.route("/feedback/add", methods=["POST"])
def add():
    request_data = json.loads(request.data)
    article_id = request_data.get("article_id")
    content = request_data.get("content").strip()
    ipaddr = request.remote_addr
    user_id = session.get("user_id")

    # 对内容进行校验
    if len(content)<5 or len(content)>1000:
        return response_message.FeedbackMessage.other("内容长度不符合要求")

    feedback = Feedback()
    try:
        result = feedback.insert_comment(user_id=user_id,
                                         article_id=article_id,
                                         content=content,
                                         ipaddr=ipaddr)
        # 评论时给文章作者发通知
        from model.article import Article, db_session
        from model.notification import Notification
        article = db_session.query(Article).filter_by(article_id=article_id).first()
        if article:
            Notification().create_notification(
                user_id=article.user_id,
                sender_id=user_id,
                type="comment",
                article_id=article_id,
                content=content[:100]
            )
        # 返回前端
        result = model_to_json(result)
        # 返回给后端自己
        return response_message.FeedbackMessage.success("评论成功")
    except Exception as e:
        print(e)
        return response_message.FeedbackMessage.error("评论失败")


# 回复评论的评论区接口开发
@feedback.route("/feedback/replay", methods=["POST"])
def replay():
    request_data = json.loads(request.data)
    article_id = request_data.get("article_id")
    content = request_data.get("content").strip()
    ipaddr = request.remote_addr
    user_id = session.get("user_id")
    replay_id = request_data.get("replay_id")
    base_replay_id = request_data.get("base_replay_id")

    # 对内容进行校验
    if len(content) < 5 or len(content) > 1000:
        return response_message.FeedbackMessage.other("内容长度不符合要求")
    feedback = Feedback()
    try:
        result = feedback.insert_replay(user_id=user_id,
                            article_id=article_id,
                            content=content,
                            ipaddr=ipaddr,
                            replay_id=replay_id,
                            base_replay_id=base_replay_id)
        # 回复评论时给文章作者发通知
        from model.article import Article, db_session
        from model.notification import Notification
        article = db_session.query(Article).filter_by(article_id=article_id).first()
        if article:
            Notification().create_notification(
                user_id=article.user_id,
                sender_id=user_id,
                type="comment",
                article_id=article_id,
                content=content[:100]
            )
        # 返回给后端自己
        return response_message.FeedbackMessage.success("评论成功")
    except Exception as e:
        print(e)
        return response_message.FeedbackMessage.error("评论失败")