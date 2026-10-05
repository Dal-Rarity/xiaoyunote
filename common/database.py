"""数据库连接模块（单例）。

db_connect() 在首次调用时创建全局唯一的 SQLAlchemy engine、
线程安全的 scoped_session 和 declarative_base，之后所有模型共享，
避免重复建立连接池。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.config.config import config
from app.settings import env

# 单例：所有模型共享同一个 engine/session/Base
_engine = None
_db_session = None
_Base = None


def db_connect():
    global _engine, _db_session, _Base
    if _db_session is not None:
        return _engine, _db_session, _Base
    config_class = config[env]
    _engine = create_engine(config_class.db_url, echo=config_class.if_echo)
    session = sessionmaker(_engine, autoflush=False)
    _db_session = scoped_session(session)
    _Base = declarative_base()
    return _engine, _db_session, _Base