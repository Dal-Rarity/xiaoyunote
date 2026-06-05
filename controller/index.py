import logging

from flask import Blueprint, render_template, request

from app.config.config import config
from app.settings import env
from model.article import Article

index = Blueprint('index', __name__)


label_types = {
    "推荐":{"name":"推荐","selected":"selected"},
    "日记":{"name":"日记","selected":"no-selected"},
    "周记":{"name":"周记","selected":"no-selected"},
    "备忘录":{"name":"备忘录","selected":"no-selected"},
    "阅读笔记":{"name":"阅读笔记","selected":"no-selected"},
    "影后观感":{"name":"影后观感","selected":"no-selected"}
}

@index.route('/')
def home():
    # 首页数据填充
    # 获取当前到底是第几页
    page = request.args.get("page",1)
    article_type = request.args.get("article")
    logging.debug("page:"+str(page))
    logging.debug("article_type:"+str(article_type))
    if page is None:
        page = 1
    if article_type is None:
        article_type = 'recommend'
    #     到数据库中查询文章数据，然后返回给前端页面
    article = Article()
    # 文章搜索功能实现
    search_keyword = request.args.get("keyword")
    # 判断关键词是否存在且不为空字符串
    if search_keyword and search_keyword.strip():
        # 执行搜索
        db_result = article.search_article(page, search_keyword)
    else:
        # 无搜索关键词，正常显示文章列表
        db_result = article.find_article(page, article_type)


    for article,nickname in db_result:
        #英文分类内容显示转换
        label_info = label_types.get(article.label_name)
        article.label = label_info.get("name") if label_info else article.label_name
        # article.label = label_types.get(article.label_name).get("name")
        #日期显示
        article.create_time = str(article.create_time.month) + '.' + str(article.create_time.day)
        #图片路径处理问题
        article.article_image = config[env].article_header_image_path + str(article.article_image)
        #文章标签格式的修改
        article.article_tag = article.article_tag.replace(',','·')

    # 计算分页用的 start_num 和 end_num（用于前端显示“当前浏览范围”）
    start_num = request.args.get('start_num')
    if start_num is None:
        start_num = 0
    end_num = len(db_result)

    # 左侧菜单栏文章分类逻辑
    for  k,v in label_types.items():
        if article_type == k:
            v["selected"] = "selected"
        else:
            v["selected"] = "no-selected"


    return render_template("index.html",result=db_result,
                           start_num=start_num,end_num=end_num,
                           label_types=label_types,
                           search_keyword=search_keyword
                           )