"""用户模型：映射现有 user 表（反射，非声明式建表）。

封装注册、按用户名/邮箱/ID 查询、资料更新等操作；
注册时随机分配 1~20.jpg 默认头像，密码由调用方做 MD5。
"""
import hashlib
import random

from app.config.config import config
from app.settings import env
from common.database import db_connect
from sqlalchemy import Table

engine, db_session, Base = db_connect()
# 定义 User 模型（从现有表反射）
class User(Base):
    __table__ = Table("user", Base.metadata, autoload_with=engine)

    def get_one(self):
        return db_session.query(User).first()

    # 注册时用户名输入结果查验
    def find_by_username(self, username):
        return db_session.query(User).filter_by(username = username).all()

    #注册时检验
    def do_register(self, username, password):
        nickname = username.split("@")[0]
        #头像（headers 目录共 20 张）
        picture_num = random.randint(1, 20)
        picture = str(picture_num) + ".jpg"
        user = User(username=username, password=password, nickname=nickname, picture=picture)
        db_session.add(user)
        db_session.commit()
        return user

    # 获取用户id返回给文章页面
    def find_by_userid(self, user_id):
        user_info = db_session.query(User).filter_by(user_id = user_id).first()
        # 简便调用者自己拼接用户头像
        if user_info.picture.startswith(config[env].user_header_image_path):
            return user_info
        else:
            user_info.picture = config[env].user_header_image_path + user_info.picture
        return user_info

    # ------------------ 新增方法 ------------------
    @staticmethod
    def get_by_email(email):
        """根据邮箱获取用户"""
        return db_session.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(uid):
        """根据用户ID获取用户"""
        return db_session.query(User).filter(User.user_id == uid).first()

    @staticmethod
    def create(email, password, nickname):
        """创建新用户（密码自动MD5加密）"""
        hashed_pwd = hashlib.md5(password.encode()).hexdigest()
        user = User(
            email=email,
            password=hashed_pwd,
            nickname=nickname
        )
        db_session.add(user)
        db_session.commit()
        return user

    def update_profile(self, nickname=None, picture=None, gender=None, age=None, address=None, bio=None):
        """更新用户资料（昵称、头像、性别、年龄、地区、简介）"""
        if nickname is not None:
            self.nickname = nickname
        if picture is not None:
            self.picture = picture
        if gender is not None:
            self.gender = gender
        if age is not None:
            self.age = age
        if address is not None:
            self.address = address
        if bio is not None:
            self.bio = bio
        db_session.commit()