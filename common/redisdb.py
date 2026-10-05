"""Redis 连接与数据转换工具。

redis_connect() 按 .env 配置创建连接池（主站使用 db1，密码可选）；
model_list() 把 SQLAlchemy 实体列表转为可 JSON 序列化的字典列表。
"""
from datetime import datetime

import redis

from app.config.config import config
from app.settings import env
from model.user import db_session,User


def redis_connect():
    redis_config = config[env]
    pool_kwargs = dict(
        host=redis_config.REDIS_HOST,
        port=redis_config.REDIS_PORT,
        db=redis_config.REDIS_DB,
        decode_responses=redis_config.REDIS_DECODE_RESPONSES,
    )
    # 密码为可选配置：.env 中未设置时不传该参数，保持无密码连接
    if redis_config.REDIS_PASSWORD:
        pool_kwargs['password'] = redis_config.REDIS_PASSWORD
    pool = redis.ConnectionPool(**pool_kwargs)
    return redis.Redis(connection_pool=pool)


# 一次性把MySQL中的用户数据初始化到redis中
def model_list(result):
    if result is None:
        return None
    list = []
    for row in result:
        dict = {}
        for k, v in row.__dict__.items():
            if not k.startswith("_sa_"):
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                dict[k] = v
        list.append(dict)
    return list

def mysql_to_redis_string():
    redis_client = redis_connect()
    db_session.query(User).all()
    # 把这个result转换成[{},{},{}]
    user_list = model_list(result)
    for user in user_list:
        redis_client.set("user:"+user["username"], str(user))
# mysql_to_redis_string()

def mysql_to_redis_hash():
    redis_client = redis_connect()
    db_session.query(User).all()
    # 把这个result转换成[{},{},{}]
    user_list = model_list(result)
    for user in user_list:
        redis_client.hset("hash_user:" + user["username"], user["username"], user["password"])

# mysql_to_redis_hash()