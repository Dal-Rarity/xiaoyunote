from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_

from model.user import User
engine, db_session, Base = db_connect()
class Collection(Base):
    __table__ = Table("collection", Base.metadata,autoload_with=engine)

    def update_status(self,article_id,user_id,canceled=0):
        # canceled的值为0表示已收藏，为1的意思就是收藏
        # 查询用户是否收藏过，如果没有收藏插入数据，如果收藏就更新数据
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

# 查询数据库中用户是否收藏
def user_if_collection(self,user_id,article_id):
    result = db_session.query(Collection.canceled).filter_by(
        user_id=user_id,
        article_id=article_id
    ).first()
    # 存在记录且 canceled == 0 表示已收藏
    if result and result[0] == 0:
        return 1
    else:
        return 0