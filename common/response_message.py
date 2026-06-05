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