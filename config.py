# config.py

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/decisions_db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask 应用的其他配置
DEBUG = True  # 启用调试模式
SECRET_KEY = 'decision_aid'  # 用于会话和表单加密
