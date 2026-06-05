import code
import email
import hashlib
import json
import re
import traceback

from flask import Blueprint, make_response, session, jsonify, request

from common.email_utils import gen_email_code, send_email
from common.utils import ImageCode
from model.user import User
from common import response_message
from app.config.config import config
from app.settings import env

user = Blueprint('user', __name__)

# @user.route("/user")
# def get_one():
#     user = User()
#     result = user.get_one()
#     print(result)
#     return "ok"

# 验证码控制流
@user.route('/vcode', methods=['GET'])
def vcode():
    try:
        code,bsrting = ImageCode().get_code()
        response = make_response(bsrting)
        response.headers['Content-Type'] = 'image/jpeg'
        #存储在内存中，就是session里
        session['vcode'] = code.lower()
        # print(code.lower())
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"验证码生成失败: {str(e)}", 500


# 检查登录状态
@user.route('/check_login', methods=['GET'])
def check_login():
    user_id = session.get('user_id')
    if user_id:
        u = User.get_by_id(user_id)
        if u:
            return jsonify({
                'is_login': True,
                'user': {
                    'email': u.email,
                    'nickname': u.nickname or '',
                    'picture': getattr(u, 'picture', '') or ''
                }
            })
    return jsonify({'is_login': False})


# 登录功能的实现
@user.route("/login", methods=['POST'])
def login():
    request_data = json.loads(request.data)
    username = request_data.get("username")
    password = request_data.get("password")
    vcode = request_data.get("vcode")

    if not session.get("vcode") or vcode != session.get("vcode"):
        return response_message.UserMessage.error("验证码输入错误或已过期")

    #实现登录功能
    password = hashlib.md5(password.encode()).hexdigest()
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




# 退出登录
@user.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'code': 200, 'msg': '已退出'})

# 更新用户资料（昵称、头像）
@user.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'msg': '未登录'})
    u = User.get_by_id(user_id)
    if not u:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    data = request.get_json()
    nickname = data.get('nickname')
    picture = data.get('picture')   # 接收 base64 或 URL
    u.update_profile(nickname=nickname, picture=picture)
    return jsonify({'code': 200, 'msg': '保存成功'})


# 邮箱获取验证码的实现
@user.route("/ecode", methods=['post'])
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
        session['ecode'] = code.lower()
        return response_message.UserMessage.success("邮件发送成功")
    except Exception as e:
        print(e)
        return response_message.UserMessage.error("邮件发送失败")

# 用户注册接口实现
@user.route("/reg",methods=['post'])
def reg():
    request_data = json.loads(request.data)
    username = request_data.get('username')
    password = request_data.get('password')
    confirm = request_data.get('confirm')
    ecode = request_data.get('ecode')
    #做数据的验证
    if ecode.lower() != session.get('ecode'):
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














