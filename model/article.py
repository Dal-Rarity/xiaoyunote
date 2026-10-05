"""文章模型：映射 article 表。

包含首页分页/栏目/搜索查询、详情与浏览量、草稿与发布、头图更新，
以及「我发布的 / 我收藏的 / 我评论过的」文章聚合查询。
drafted 字段约定：1=已发布，0=草稿。
"""
from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_, distinct

from model.collection import Collection
from model.feedback import Feedback
from model.user import User

engine, db_session, Base = db_connect()

class Article(Base):
    __table__ = Table("article", Base.metadata, autoload_with=engine)
    # 查询出所有文章，但不要草稿
    # 每页显示10条内容,page默认从1开始
    def find_article(self,page,article_type="recommend"):
        if int(page) < 1:
            page = 1
        per_page = config[env].page_count
        offset = (int(page) - 1) * per_page
        # 来到推荐标签的下面
        if article_type == "recommend":
            result = db_session.query(Article,User.nickname).join(
                User,User.user_id == Article.user_id
            ).filter(
                Article.drafted == 1
            ).order_by(
                Article.browse_num.desc()
            ).offset(offset).limit(per_page).all()
        else:
            result = db_session.query(Article,User.nickname).join(
                User,User.user_id == Article.user_id
            ).filter(
                Article.label_name == article_type,
                Article.drafted == 1
            ).order_by(
                Article.browse_num.desc()
            ).offset(offset).limit(per_page).all()

        return result

    # 实现文章搜索的函数
    def search_article(self,page,keyword):
    # 如果 keyword 为 None 或空字符串，直接返回空列表
        if not keyword:
            return []

        if int(page) < 1:
            page = 1
        per_page =config[env].page_count      #每页条数
        offset = (int(page) - 1) * per_page
        result = db_session.query(Article,User.nickname).join(
            User,User.user_id == Article.user_id).filter(
            or_(Article.title.like("%"+keyword+"%"),
                Article.article_content.like("%"+keyword+"%"))
            ).order_by(Article.browse_num.desc()).limit(per_page).offset(offset).all()
        return result


    # 获取文章详情
    def get_article_detail(self,article_id):
        result = db_session.query(Article).filter_by(article_id=article_id).first()
        if result is None:
            return None
        result.browse_num = result.browse_num + 1
        db_session.commit()
        return db_session.query(Article).filter_by(article_id=article_id).first()

    #获取相关文章详情
    def find_about_article(self,label_name):
        return db_session.query(Article).filter_by(
            label_name=label_name
        ).order_by(
            Article.browse_num.desc()
        ).limit(5)

    # 创建文章以及草稿
    def insert_article(self,user_id, title, article_content,drafted, label_name='', article_tag='' ):
        article = Article(
            user_id=user_id,
            title=title,
            article_content=article_content,
            drafted=drafted,
            label_name=label_name,
            article_tag=article_tag
        )
        db_session.add(article)
        db_session.commit()
        return article.article_id
    #更新文章相关信息
    def update_article(self,
                       article_id,
                       title,
                       article_content,
                       drafted,
                       label_name="",
                       article_tag="",
                       article_type="",
                       ):
        row = db_session.query(Article).filter_by(article_id=article_id).first()
        row.title = title
        row.article_content = article_content
        row.drafted = drafted
        row.label_name = label_name
        row.article_tag = article_tag
        row.article_type = article_type
        db_session.commit()
        return article_id

    #更新数据库相关信息
    def update_article_header_image(self,article_id,article_image):
        row = db_session.query(Article).filter_by(article_id=article_id).first()
        row.article_image = article_image
        db_session.commit()
        return article_id

    #获取所有我的草稿
    def get_all_article_drafted(self,user_id):
        result = db_session.query(Article).filter_by(user_id=user_id,drafted=0).all()
        return result
    #获取某一篇草稿的详情
    def get_one_article_drafted(self,article_id):
        result = db_session.query(Article).filter_by(article_id=article_id,drafted=0).first()
        return result

    #获取某一用户不是草稿的文章
    def get_article_by_userid(self,user_id):
        result = db_session.query(Article).filter_by(
            user_id=user_id,
            drafted=1
        ).all()
        return self.app_path(result)


    #获取某个用户所有收藏的文章
    def get_collection_article_by_userid(self,user_id):
        result = db_session.query(Article).join(
            Collection,
            Collection.article_id == Article.article_id
        ).filter(
            Collection.user_id == user_id,
        ).order_by(
            Collection.create_time.desc()
        ).all()
        return self.app_path(result)

    # 获取所有用户评论过的文章
    def get_feedback_article_by_userid(self, user_id):
        # 用子查询解决查询结果的问题
        article_id_list = db_session.query(
            distinct(Feedback.article_id)
        ).filter_by(user_id=user_id).subquery()
        # 在通过文章id的集合查询到所有文章数据
        result = db_session.query(Article).filter(
            Article.article_id.in_(article_id_list)
        ).all()
        return self.app_path(result)

    #添加文章中所有头部图片的路径
    def app_path(self,article_list):
        for article in article_list:
            # 脱离会话再改展示字段，避免路径字符串被 flush 回数据库造成数据污染
            db_session.expunge(article)
            # 发文章时未上传头图则 article_image 为 NULL，回退到默认头图
            article.article_image = config[env].article_header_image_path + (article.article_image or "1.jpg")
        return article_list

























