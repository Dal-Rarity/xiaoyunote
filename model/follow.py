"""关注关系模型：映射 follow 表。

提供关注/取关、粉丝与关注列表、关注关系判断与计数。
canceled：0=已关注，1=已取关（软删除，保留记录）。
"""
from common.database import db_connect
from sqlalchemy import Table

engine, db_session, Base = db_connect()

class Follow(Base):
    __table__ = Table("follow", Base.metadata, autoload_with=engine)

    def update_status(self, follower_id, following_id, canceled=0):
        """关注/取消关注。canceled=0表示已关注, 1表示取消关注"""
        follow_data = db_session.query(Follow).filter_by(
            follower_id=follower_id,
            following_id=following_id,
        ).first()
        if follow_data is None:
            follow = Follow(
                follower_id=follower_id,
                following_id=following_id,
                canceled=canceled
            )
            db_session.add(follow)
        else:
            follow_data.canceled = canceled
        db_session.commit()

    def get_followers(self, user_id):
        """获取关注了我的人列表(粉丝)"""
        from model.user import User
        result = db_session.query(Follow, User).join(
            User, User.user_id == Follow.follower_id
        ).filter(
            Follow.following_id == user_id,
            Follow.canceled == 0
        ).order_by(
            Follow.create_time.desc()
        ).all()
        return result

    def get_following(self, user_id):
        """获取我关注了的人列表"""
        from model.user import User
        result = db_session.query(Follow, User).join(
            User, User.user_id == Follow.following_id
        ).filter(
            Follow.follower_id == user_id,
            Follow.canceled == 0
        ).order_by(
            Follow.create_time.desc()
        ).all()
        return result

    def is_following(self, follower_id, following_id):
        """判断follower_id是否关注了following_id"""
        result = db_session.query(Follow).filter_by(
            follower_id=follower_id,
            following_id=following_id,
            canceled=0
        ).first()
        return result is not None

    def get_follower_count(self, user_id):
        """获取粉丝数量"""
        return db_session.query(Follow).filter_by(
            following_id=user_id,
            canceled=0
        ).count()

    def get_following_count(self, user_id):
        """获取关注数量"""
        return db_session.query(Follow).filter_by(
            follower_id=user_id,
            canceled=0
        ).count()
