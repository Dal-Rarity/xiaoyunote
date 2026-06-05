import json
import logging
import random
import time
# from datetime import time

from flask import Blueprint, render_template, request, abort, session, jsonify, make_response, url_for

from app.config.config import config
from app.settings import env
from common import response_message
from common.utils import compress_image, model_to_json
from model.article import Article
from model.favorite import Favorite, db_session
from model.collection import Collection
from model.feedback import Feedback
from model.user import User

article = Blueprint("article", __name__)
label_types = config[env].label_types
article_types = config[env].article_types
article_tags = config[env].article_tags
# 判断登录状态
@article.before_request
def article_before_request():
    url = request.path
    is_login = session.get("is_login")
    if url.startswith("/article") and "new" in url and is_login != 'true':
        response = make_response("登录重定向",302)
        response.headers["location"] = url_for("index.home")
        return response

@article.route("/detail")
def article_detail():
    article_id = request.args.get("article_id")
    # 1. 检查参数是否存在且非空
    if not article_id:
        abort(404, description="缺少文章ID")

    article = Article()
    # 获取文章的所有信息
    article_content = article.get_article_detail(article_id)
    article_tag_string = article_content.article_tag
    article_tag_list = article_tag_string.split(",")
    # 2. 检查文章是否存在
    if article_content is None:
        abort(404, description="文章不存在")
    # 获取文章作者信息
    user = User()
    user_info = user.find_by_userid(article_content.user_id)

    feedback_data_list = Feedback().get_feedback_user_list(article_id)

    #收藏功能的实现
    is_collection = 1
    if session.get("is_login") == "true":
        user_id = session.get("user_id")
        # is_collection = collection().user_if_collection(user_id,article_id)
        # 直接查询数据库
        result = db_session.query(Collection.canceled).filter_by(
            user_id=user_id,
            article_id=article_content.article_id
        ).first()
        # 存在记录且 canceled == 0 表示已收藏
        if result and result[0] == 0:
            is_collection = 1

    # 喜欢功能的实现
    is_favorite = 1
    if session.get("is_login") == "true":
        user_id = session.get("user_id")
        # is_favorite = Favorite().user_if_favorite(user_id,article_id)
        # 直接查询数据库
        result = db_session.query(Favorite.canceled).filter_by(
            user_id=user_id,
            article_id=article_content.article_id
        ).first()
        # 存在记录且 canceled == 0 表示已收藏
        if result and result[0] == 0:
            is_favorite = 1

    # 查看评论数量
    feedback_count = Feedback().get_article_feedback_count(article_id)

    #相关文章推荐的实现
    about_article = article.find_about_article(article_content.label_name)


    return render_template("article-info.html",
                           article_content=article_content,
                           user_info=user_info,
                           is_favorite=is_favorite,
                           is_collection=is_collection,
                           article_tag_list=article_tag_list,
                           about_article=about_article,
                           feedback_data_list=feedback_data_list,
                           feedback_count=feedback_count
                           )

@article.route("/article/new")
def article_new():
    # article_id = request.args.get("article_id")
    user_id = session.get("user_id")
    # 我的草稿实现
    all_drafted = Article().get_all_article_drafted(user_id)

    return render_template("new-article.html",
                           label_types=label_types,
                           article_types=article_types,
                           article_tags=article_tags,
                           all_drafted=all_drafted,
                           drafted_count=len(all_drafted))
# 获取某一篇草稿的详情
@article.route("/article/drafted",methods=["POST"])
def get_drafted_detail():
    request_data = json.loads(request.data)
    result = Article().get_one_article_drafted(request_data.get("article_id"))
    #把结果转成json，然后给前端
    article_drafted = model_to_json(result)
    return response_message.ArticleMessage.success(article_drafted)

# 获取文章信息
def get_article_request_param(request_data):
    user = User().find_by_userid(session.get("user_id"))
    title = request_data.get("title")
    article_content = request_data.get("article_content")
    return user, title, article_content



# 草稿或文章储存
@article.route("/article/save", methods=["POST"])
def article_save():
    request_data = json.loads(request.data)
    article_id = request_data.get("article_id")
    drafted = request_data.get("drafted")

    # 获取可能用到的字段
    title = request_data.get("title", "")
    article_content = request_data.get("article_content", "")
    label_name = request_data.get("label_name", "")
    article_tag = request_data.get("article_tag", "")
    article_type = request_data.get("article_type", "")

    if article_id == -1:
        # 新文章：草稿(drafted=0) 或 直接发布(drafted=1)
        if title == "":
            return response_message.ArticleMessege.other("请输入文章标题")
        # 获取当前用户
        if 'user_id' not in session:
            return response_message.ArticleMessage.error("请先登录")
        user = User().find_by_userid(session['user_id'])
        if not user:
            return response_message.ArticleMessage.error("用户不存在")
        # 插入文章（传入所有字段）
        new_id = Article().insert_article(
            user_id=user.user_id,
            title=title,
            article_content=article_content,
            drafted=drafted,
            label_name=label_name,
            article_tag=article_tag
        )
        msg = "草稿存储成功" if drafted == 0 else "文章发布成功"
        return response_message.ArticleMessage.save_success(new_id, msg)

    elif article_id > -1:
        # 更新已有文章
        user, title, article_content = get_article_request_param(request_data)
        if title == "":
            return response_message.ArticleMessege.other("请输入文章标题")
        article_id = Article().update_article(
            article_id=article_id,
            title=title,
            article_content=article_content,
            drafted=drafted,
            label_name=label_name,
            article_tag=article_tag,
            article_type=article_type
        )
        # 根据 drafted 返回不同消息
        if drafted == 0:
            return response_message.ArticleMessage.save_success(article_id, "草稿更新成功")
        else:
            return response_message.ArticleMessage.save_success(article_id, "发布文章成功")
    else:
        return response_message.ArticleMessage.error("无效的文章ID")

# 上传文章头部图片的接口实现
@article.route("/article/upload/article_header_image",methods=["POST"])
def upload_article_header_image():
    # 获取前端图片文件
    f = request.files.get("header-image-file")
    filename = f.filename
    # 文件后缀名
    suffix = filename.split(".")[-1]
    newname = time.strftime("%Y%m%d_%H%M%S." + suffix)
    newname = "article-header-" + newname
    f.save("resource/upload/" + newname)
    # 大图片压缩
    source = dest = "resource/upload/" + newname
    compress_image(source, dest, 1200)
    # 更新数据库
    article_id = request.form.get("article_id")
    Article().update_article_header_image(article_id,newname)

    # 构造响应数据
    result = {}
    result["state"] = "SUCCESS"
    result['url'] = "/upload/" + newname
    result["title"] = filename
    result["original"] = filename
    return jsonify(result)

# 文章头部图像的随机选择接口实现
@article.route("/article/random/header/image",methods=["POST"])
def random_article_header_image():
    name = random.randint(1,20)
    newname = str(name) + ".jpg"
    # 更新数据库
    article_id = request.form.get("article_id")
    Article().update_article_header_image(article_id, newname)

    # 构造响应数据
    result = {}
    result["state"] = "SUCCESS"
    result['url'] = "/images/article/header/" + newname
    result["title"] = newname
    result["original"] = newname
    return jsonify(result)











