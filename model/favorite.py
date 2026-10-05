"""喜欢（点赞）模型：映射 favorite 表，按 (用户, 文章) 维度 upsert 喜欢状态。"""
from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_

from model.user import User
engine, db_session, Base = db_connect()
class Favorite(Base):
    __table__ = Table("favorite", Base.metadata,autoload_with=engine)

    def update_status(self,article_id,user_id,canceled=0):
        # canceled：0=喜欢，1=取消喜欢
        # 没有记录则插入，已有记录则更新状态
        favorite_data = db_session.query(Favorite).filter_by(
            article_id=article_id,
            user_id=user_id,
        ).first()
        if favorite_data is None:
            favorite = Favorite(
                article_id=article_id,
                user_id=user_id,
                canceled=canceled
            )
            db_session.add(favorite)
        else:
            favorite_data.canceled = canceled
        db_session.commit()
