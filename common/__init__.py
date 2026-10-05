"""公共工具包。

导入本包即配置全局日志：日志同时输出到控制台与 log/xiaoyunote.log
（按 1MB 滚动、最多保留 10 份），日志等级随 FLASK_ENV 切换。
"""
import logging
from logging.handlers import RotatingFileHandler
from app.config.config import config
from app.settings import env

# 增加日志的配置
def set_log():
    config_class =config[env]
    # 设置日志等级
    logging.basicConfig(level=config_class.LOG_LEVEL)
    #创建日志记录器,指定日志的保存路径，每个日志文件的最大大小，保存的日志个数
    file_log_handler = RotatingFileHandler("log/xiaoyunote.log", maxBytes=1024*1024, backupCount=10)
    # 创建日志记录的格式
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d %(message)s")
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


set_log()