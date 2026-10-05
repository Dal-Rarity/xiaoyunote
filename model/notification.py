"""消息通知模型：映射 notification 表。

记录接收者、触发者、通知类型（follow/favorite/collection/comment）
及关联文章，支持未读计数与标记已读；自己给自己的行为不产生通知。
"""
from common.database import db_connect
from sqlalchemy import Table

engine, db_session, Base = db_connect()

class Notification(Base):
    __table__ = Table("notification", Base.metadata, autoload_with=engine)

    def create_notification(self, user_id, sender_id, type, article_id=None, content=None):
        """创建通知。user_id=接收者, sender_id=触发者"""
        if user_id == sender_id:
            return None
        notification = Notification(
            user_id=user_id,
            sender_id=sender_id,
            type=type,
            article_id=article_id,
            content=content,
            is_read=0
        )
        db_session.add(notification)
        db_session.commit()
        return notification

    def get_unread_count(self, user_id):
        """获取未读通知数量"""
        return db_session.query(Notification).filter_by(
            user_id=user_id,
            is_read=0
        ).count()

    def get_notification_list(self, user_id):
        """获取用户的所有通知列表(含发送者信息)"""
        from model.user import User
        from model.article import Article
        result = db_session.query(Notification, User, Article).join(
            User, User.user_id == Notification.sender_id
        ).outerjoin(
            Article, Article.article_id == Notification.article_id
        ).filter(
            Notification.user_id == user_id
        ).order_by(
            Notification.create_time.desc()
        ).all()
        return result

    def mark_as_read(self, notification_id):
        """标记单条通知为已读"""
        notification = db_session.query(Notification).filter_by(
            notification_id=notification_id
        ).first()
        if notification:
            notification.is_read = 1
            db_session.commit()

    def mark_all_as_read(self, user_id):
        """标记所有通知为已读"""
        db_session.query(Notification).filter_by(
            user_id=user_id,
            is_read=0
        ).update({"is_read": 1})
        db_session.commit()
