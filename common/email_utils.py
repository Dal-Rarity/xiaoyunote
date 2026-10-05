"""邮件工具：生成注册验证码并通过 QQ 邮箱 SMTP_SSL 发送。"""
# 所有邮箱相关的工具储存
import random
import string
import smtplib  # 导入邮件服务
from email.mime.text import MIMEText  # 发送的纯文本内容
from email.mime.multipart import MIMEMultipart  # 发送类似于多媒体的内容

from app.config.config import config
from app.settings import env

def gen_email_code():
    list = random.sample(string.ascii_letters+string.digits, 6)
    return "".join(list)

def send_email(email, code):
    email_name = config[env].email_name  # 发送方邮箱
    passwd = config[env].passwd  # 填入发送方邮箱的授权码
    # 把验证码发给谁
    msg_to = email
    # 正文
    content = f"""
    小语手记注册验证码是:<h1 style='color:red'>{code}</h1>
    """

    msg = MIMEMultipart()
    msg["Subject"] = "小语手记验证码"  # 发送对象
    msg["From"] = email_name  # 谁发的
    msg["To"] = msg_to  # 发给谁
    # 发送邮件正文，html格式的
    msg.attach(MIMEText(content, "html", "utf-8"))  # msg.attach(MIMEText(内容，格式，编码))

    # try:
    s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮箱服务器及端口号
    s.login(email_name, passwd)
    s.sendmail(email_name, msg_to, msg.as_string())