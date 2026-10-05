"""收藏模型：映射 collection 表，按 (用户, 文章) 维度 upsert 收藏状态。"""
from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_

from model.user import User
engine, db_session, Base = db_connect()
class Collection(Base):
    __table__ = Table("collection", Base.metadata,autoload_with=engine)

    def update_status(self,article_id,user_id,canceled=0):
        # canceled：0=已收藏，1=取消收藏
        # 查询用户是否收藏过：没有记录则插入，已有记录则更新状态
        collection_data = db_session.query(Collection).filter_by(
            article_id=article_id,
            user_id=user_id,
        ).first()
        if collection_data is None:
            collection = Collection(
                article_id=article_id,
                user_id=user_id,
                canceled=canceled
            )
            db_session.add(collection)
        else:
            collection_data.canceled = canceled
        db_session.commit()
