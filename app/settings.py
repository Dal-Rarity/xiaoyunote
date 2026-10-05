"""运行环境标识。

从根目录 .env 读取 FLASK_ENV（production / test），
供 config.config 选择对应配置类。
"""
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

env = os.getenv('FLASK_ENV', 'production')     # 开发环境：production；测试环境：test
