"""评论模型：映射 comment 表（类名为 Feedback）。

两级评论结构：一级评论 replay_id=0 且 base_replay_id=0 并占楼层号；
二级回复通过 base_replay_id 挂在所属一级评论下，replay_id 指向被回复的评论。
get_feedback_user_list() 组装「一级评论 + 回复列表（含回复人/被回复人信息）」。
"""
# 评论的具体实现

from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table, or_, func

from common.utils import model_to_json
from model.user import User

engine, db_session, Base = db_connect()

class Feedback(Base):
    __table__ = Table("comment", Base.metadata, autoload_with=engine)
    """
    我们需要最终给前端返回一个完整的数据，最终数据样式：
    final_data_list = [{
    最上层评论的数据以及用户数据，
    replay_list:[{
        from_user:"",
        to_user:"",
        replay:""
    },{},{}]
    },{},{}]
    """
    def get_feedback_user_list(self,article_id):
        final_data_list = []
        # 查询文章的一级评论，就是那些带有楼层的，新开的评论
        feedback_list = self.find_feedback_by_article_id(article_id)

        for feedback in feedback_list:
            user = User()
            #根据一级评论获取回复评论的内容
            all_replay = self.find_replay_by_replayid(base_replay_id=feedback.comment_id)
            #获取用户信息
            feedback_user = user.find_by_userid(feedback.user_id)
            replay_list = []
            #再根据每一条回复的评论查询用户数据
            for replay in all_replay:
                # 用于存储当前评论的所有回复评论，如果没有回复，则值为空
                replay_content_with_user = {}
                from_user_data = user.find_by_userid(replay.user_id)
                # 获取回复谁的评论的用户信息
                to_user_replay_data = self.find_replay_by_id(replay.replay_id)
                # to_user_data = user.find_by_userid(to_user_replay_data[0].user_id)
                if to_user_replay_data:
                    to_user_data = user.find_by_userid(to_user_replay_data[0].user_id)
                else:
                    to_user_data = None

                replay_content_with_user ["from_user"] = model_to_json(from_user_data)
                replay_content_with_user["to_user"] = model_to_json(to_user_data)
                replay_content_with_user["content"] = model_to_json(replay)
                replay_list.append(replay_content_with_user)

            #存储每一个回复下的所有数据
            every_feedback_data = model_to_json(feedback)
            every_feedback_data.update(model_to_json(feedback_user))
            every_feedback_data["replay_list"] = replay_list
            final_data_list.append(every_feedback_data)
        return final_data_list

    # 一级评论的查找方法实现
    def find_feedback_by_article_id(self,article_id):
        result = db_session.query(Feedback).filter_by(
            article_id = article_id,
            replay_id = 0,
            base_replay_id = 0,
        ).order_by(
            Feedback.comment_id.desc()
        ).all()
        return result

    # 二级评论的查找方法实现
    def find_replay_by_replayid(self,base_replay_id):
        result = db_session.query(Feedback).filter_by(
            base_replay_id = base_replay_id,
        ).order_by(
            Feedback.comment_id.desc()
        ).all()
        return result

    def find_replay_by_id(self,comment_id):
        result = db_session.query(Feedback).filter(
            Feedback.comment_id == comment_id
        ).order_by(
            Feedback.comment_id.desc()
        ).all()
        return result

    # 评论数量的实现
    def get_article_feedback_count(self,article_id):
        result = db_session.query(Feedback).filter_by(
            article_id = article_id,
            base_replay_id = 0,
            replay_id = 0
        ).count()
        return result

    # 插入一级评论
    def insert_comment(self,user_id,article_id,content,ipaddr):
        # label的意思就是重新起一个名字给字段
        feedback_max_floor = db_session.query(
            func.max(Feedback.floor_number).label("max_floor")
        ).filter_by(article_id = article_id).first()
        if feedback_max_floor.max_floor == 0 or feedback_max_floor.max_floor is None:
            feedback = Feedback(user_id=user_id,
                                article_id=article_id,
                                content=content,
                                ipaddr=ipaddr,
                                floor_number=1,
                                replay_id=0,
                                base_replay_id=0)
        else:
            feedback = Feedback(user_id=user_id,
                                article_id=article_id,
                                content=content,
                                ipaddr=ipaddr,
                                floor_number=int(feedback_max_floor.max_floor)+1,
                                replay_id=0,
                                base_replay_id=0)
        db_session.add(feedback)
        db_session.commit()
        # 做一个手动刷新就可以拿到插入的数据的值了
        db_session.reset()
        return feedback

    # 插入二级评论
    def insert_replay(self,article_id,user_id,content,ipaddr,replay_id,base_replay_id):
        feedback = Feedback(user_id=user_id,
                            article_id=article_id,
                            content=content,
                            ipaddr=ipaddr,
                            replay_id=replay_id,
                            base_replay_id=base_replay_id)
        db_session.add(feedback)
        db_session.commit()