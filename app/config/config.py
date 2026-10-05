"""全局配置模块。

所有环境相关参数（MySQL、邮箱、Redis）均从根目录 .env 读取，
并按 FLASK_ENV 提供 TestConfig / ProductionConfig 两套配置；
config 字典供各处通过 config[env] 取用。
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# 显式加载项目根目录下的 .env（不依赖启动时的工作目录）
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_PROJECT_ROOT, '.env'))


# 全局通用配置
class Config(object):
    # MySQL：连接参数全部来自环境变量，禁止在代码中写明文密码
    db_host = os.getenv('DB_HOST', '127.0.0.1')
    db_port = os.getenv('DB_PORT', '3307')
    db_user = os.getenv('DB_USER', '')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'xiaoyushouji')
    db_charset = os.getenv('DB_CHARSET', 'utf8mb4')
    db_url = (
        f'mysql+pymysql://{quote_plus(db_user)}:{quote_plus(db_password)}'
        f'@{db_host}:{db_port}/{db_name}?charset={db_charset}'
    )
    #前端页面显示的条数
    page_count=10
    #配置文章图片存储路径
    article_header_image_path = "/images/article/header/"

    email_name = os.getenv('MAIL_USERNAME', '')  # 发送方邮箱
    passwd = os.getenv('MAIL_PASSWORD', '')  # 发送方邮箱的 SMTP 授权码

    #配置用户头像存储路径
    user_header_image_path = "/images/headers/"

    label_types = {
        "推荐": {"name": "请选择需要投递的栏目", "selected": "selected"},
        "日记": {"name": "日记", "selected": "no-selected"},
        "周记": {"name": "周记", "selected": "no-selected"},
        "备忘录": {"name": "备忘录", "selected": "no-selected"},
        "阅读笔记": {"name": "阅读笔记", "selected": "no-selected"},
        "影后观感": {"name": "影后观感", "selected": "no-selected"}
    }
    article_types = {
        "推荐": {"name": "请选择", "selected": "selected"},
        "首发": {"name": "首发", "selected": "no-selected"},
        "原创": {"name": "原创", "selected": "no-selected"},
        "其他": {"name": "其他", "selected": "no-selected"},
    }
    article_tags = ["灵感", "心情", "随笔", "感悟", "观点", "天气"]

    # 配置redis（连接参数来自环境变量）
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_POLL = 10
    REDIS_DB = int(os.getenv('REDIS_DB', '1'))
    REDIS_DECODE_RESPONSES = True

# class TestConfig(Config):
#     if_echo = True

# 测试环境
class TestConfig(Config):
    if_echo=True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    if_echo=False
    LOG_LEVEL = "INFO"

config = {
    'test': TestConfig,
    'production': ProductionConfig,
}
