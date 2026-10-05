"""收藏蓝图：切换文章收藏状态（canceled=0 收藏 / 1 取消），
收藏时向文章作者写入一条通知。
"""
import json
import logging

from flask import Blueprint, render_template, request, abort, session

from app.config.config import config
from app.settings import env
from common import response_message
from model.article import Article
from model.collection import Collection
from model.user import User

collection = Blueprint("collection", __name__)

@collection.route("/collection/update_status", methods=["POST"])
def update_status():
    request_data = json.loads(request.data)
    user_id = session.get("user_id")
    article_id = request_data.get("article_id")   #get方式获取没取到报none，[]方式没取到报异常
    canceled = request_data.get("canceled")
    try:
        Collection().update_status(article_id=article_id,
                                 user_id=user_id,
                                 canceled=canceled)
        # 收藏时(canceled=0)给文章作者发通知
        if canceled == 0:
            from model.article import Article, db_session
            from model.notification import Notification
            article = db_session.query(Article).filter_by(article_id=article_id).first()
            if article:
                Notification().create_notification(
                    user_id=article.user_id,
                    sender_id=user_id,
                    type="collection",
                    article_id=article_id
                )
        return response_message.CollectionMessage.success("收藏")
    except Exception as e:
        logging.error(e)
        print(e)
        return response_message.CollectionMessage.error("已收藏")