"""统一 JSON 响应封装。

按业务域约定状态码段：用户 1xxx、文章 2xxx、收藏 3xxx、评论 4xxx、
喜欢 5xxx、个人中心 6xxx、关注 7xxx、通知 8xxx；
每个域统一提供 success / error / other 三种结果。
"""
# 存放邮箱登录的详细信息

class UserMessage():
    """
    在企业中，一般会对响应状态码做出一些规定
    比如说，用户响应都以1开头，然后规定了{status：1000,data：'asdf'}
    错误状态码1002
    其他状态码1001
    """

    @staticmethod
    def success(data):
        return {"status": "1000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "1002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "1001", "data": data}

# 文章的状态 以2开头
class ArticleMessage():
    @staticmethod
    def success(data):
        return {"status": "2000", "data": data}
    @staticmethod
    def save_success(article_id,data):
        return {"status": "2003", "article_id": article_id, "data": data}

    @staticmethod
    def error(data):
        return {"status": "2002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "2001", "data": data}
# 收藏以3开头
class CollectionMessage():
    @staticmethod
    def success(data):
        return {"status": "3000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "3002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "3001", "data": data}

# 评论以4开头
class FeedbackMessage():
    @staticmethod
    def success(data):
        return {"status": "4000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "4002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "4001", "data": data}

# 喜欢以5开头
class FavoriteMessage():
    @staticmethod
    def success(data):
        return {"status": "5000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "5002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "5001", "data": data}

# 个人中心以6开头
class PersonalMessage():
    @staticmethod
    def success(data):
        return {"status": "6000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "6002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "6001", "data": data}

# 关注以7开头
class FollowMessage():
    @staticmethod
    def success(data):
        return {"status": "7000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "7002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "7001", "data": data}

# 消息通知以8开头
class NotificationMessage():
    @staticmethod
    def success(data):
        return {"status": "8000", "data": data}

    @staticmethod
    def error(data):
        return {"status": "8002", "data": data}

    @staticmethod
    def other(data):
        return {"status": "8001", "data": data}