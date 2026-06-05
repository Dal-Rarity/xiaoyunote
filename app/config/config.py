
# 全局通用配置
class Config(object):
    db_url = 'mysql+pymysql://xiaoyu:a3464579156@127.0.0.1:3307/xiaoyushouji'
    #前端页面显示的条数
    page_count=10
    #配置文章图片存储路径
    article_header_image_path = "/images/article/header/"

    email_name = '2125466096@qq.com'  # 发送方邮箱
    passwd = 'pjpbuhnkeyyrjiaa'  # 填入发送方邮箱的授权码

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

class TestConfig(Config):
    if_echo = True

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
