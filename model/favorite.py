from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_

from model.user import User
engine, db_session, Base = db_connect()
class Favorite(Base):
    __table__ = Table("favorite", Base.metadata,autoload_with=engine)

    def update_status(self,article_id,user_id,canceled=0):
        # canceled的值为0表示喜欢，为1的意思就是不喜欢

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

# 查询数据库中用户是否喜欢
def user_if_favorite(self,user_id,article_id):
    result = db_session.query(Favorite.canceled).filter_by(
        user_id=user_id,
        article_id=article_id
    ).first()
    # 存在记录且 canceled == 0 表示喜欢
    if result and result[0] == 0:
        return 1
    else:
        return 0