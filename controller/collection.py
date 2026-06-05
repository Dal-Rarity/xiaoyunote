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
        return response_message.CollectionMessage.success("收藏")
    except Exception as e:
        logging.error(e)
        print(e)
        return response_message.CollectionMessage.error("已收藏")