"""用户蓝图（Redis 版，与 controller.user 并存）。

邮箱验证码存 Redis 并设置 60 秒过期；/redis/login* 演示
「先查 Redis 缓存、未命中再查 MySQL」的登录流程。
"""
import code
import email
import hashlib
import json
import re
import traceback

from flask import Blueprint, make_response, session, jsonify, request

from common.email_utils import gen_email_code, send_email
from common.redisdb import redis_connect
from common.utils import ImageCode
from model.user import User
from common import response_message
from app.config.config import config
from app.settings import env

redis_user = Blueprint('redis_user', __name__)
# 邮箱获取验证码的实现
redis_client = redis_connect()
@redis_user.route("/redis/ecode", methods=['post'])
def email_code():
    # email = request.form.get('email')
    # return email
    email = json.loads(request.data).get('email')
    #简单的邮箱格式验证
    if not re.match(".+@.+\..+", email):
        return response_message.UserMessage.other("无效邮箱")
    # 生成邮箱验证码的随机字符串
    code = gen_email_code()
    # return code
    # 发送邮件
    try:
        send_email(email, code)
        # session['ecode'] = code.lower()
        email_vcode = "email:"+email
        redis_client.set(email_vcode, code.lower())
        # 单独设置过期时间
        redis_client.expire(email_vcode, 60)
        return response_message.UserMessage.success("邮件发送成功")
    except Exception as e:
        print(e)
        return response_message.UserMessage.error("邮件发送失败")


# 用户注册接口实现
@redis_user.route("/redis/reg",methods=['post'])
def reg():
    request_data = json.loads(request.data)
    username = request_data.get('username')
    password = request_data.get('password')
    confirm = request_data.get('confirm')
    ecode = request_data.get('ecode')
    redis_ecode = redis_client.get("email:"+username)
    #做数据的验证
    if ecode.lower() != redis_ecode:
        return response_message.UserMessage.error("邮箱验证码错误")
    #用户名和密码的验证
    if not re.match(".+@.+\..+", username):
        return response_message.UserMessage.other("无效邮箱")
    #密码格式的验证
    if len(password) < 6:
        return response_message.UserMessage.error("密码不能少于6位")
    #密码正确性验证
    if password != confirm:
        return response_message.UserMessage.error("两次输入密码不一致")
    #用户名是否注册
    user = User()
    if len(user.find_by_username(username=username)) > 0:
        return response_message.UserMessage.error("用户名已经存在")
    #实现注册功能
    password = hashlib.md5(password.encode()).hexdigest()
    result = user.do_register(username=username, password=password)
    return response_message.UserMessage.success("用户注册成功")

# 登录功能的实现
@redis_user.route("/redis/login", methods=['POST'])
def login():
    request_data = json.loads(request.data)
    username = request_data.get("username")
    password = request_data.get("password")
    # vcode = request_data.get("vcode")
    #
    # if not session.get("vcode") or vcode != session.get("vcode"):
    #     return response_message.UserMessage.error("验证码输入错误或已过期")

    #实现登录功能
    password = hashlib.md5(password.encode()).hexdigest()
    # 先到redis中查看用户数据，如果查询不到再到MySQL中进行查询
    result = redis_client.get("user:"+username)
    if result is None:
        user = User()
        result = user.find_by_username(username)
        if len(result) == 1 and result[0].password==password:
            #进行登录状态的管理
            session["is_login"] = "true"
            session["user_id"] = result[0].user_id
            session["username"] = username
            session["nickname"] = result[0].nickname
            session["picture"] = config[env].user_header_image_path + result[0].picture
            # return response_message.UserMessage.success("登录成功")
            #cookie里记录信息
            response = make_response(response_message.UserMessage.success("登录成功"))
            response.set_cookie("username", username,max_age=3600)
            # response.set_cookie("username", username, max_age=3600)
            return response
        else:
            # 登录失败：用户名或密码错误
            return response_message.UserMessage.error("用户名或密码错误")
    else:
        # 把字符串变成一个字典
        result = eval(result)
        if result.get("password") == password:
            response = make_response(response_message.UserMessage.success("登录成功"))
            return response
        else:
            # 登录失败：用户名或密码错误
            return response_message.UserMessage.error("用户名或密码错误")

# 登录功能的实现hash缓存
@redis_user.route("/redis/login2", methods=['POST'])
def login2():
    request_data = json.loads(request.data)
    username = request_data.get("username")
    password = request_data.get("password")
    # vcode = request_data.get("vcode")
    #
    # if not session.get("vcode") or vcode != session.get("vcode"):
    #     return response_message.UserMessage.error("验证码输入错误或已过期")

    #实现登录功能
    password = hashlib.md5(password.encode()).hexdigest()
    # 先到redis中查看用户数据，如果查询不到再到MySQL中进行查询
    redis_password = redis_client.hget("hash_user:"+username,username)
    if redis_password == password:
        response = make_response(response_message.UserMessage.success("登录成功"))
        return response
    else:
        return response_message.UserMessage.error("用户名或密码错误")