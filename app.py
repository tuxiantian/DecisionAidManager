import base64
from flask import Flask, request, jsonify, render_template, send_from_directory, current_app
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required # type: ignore
from flask_cors import CORS
from ahp_routes import ahp_bp
from Checklist import checklist_bp
from TodoList import todolist_bp
from article import article_bp
from minio_utils import minio_bp
from BalancedDecision import balanced_decision_bp
from mermaid_utils import mermaid_bp
from statistics_routes import statistics_bp
from logic_errors import logic_errors_bp
from feedback import feedback_bp
from inspirations import inspiration_bp
from admin import admin_bp
import pymysql
from shared_models import AdminUser, db
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from logging.handlers import RotatingFileHandler
import os
import logging
pymysql.install_as_MySQLdb()

app = Flask(__name__, static_folder='build', template_folder='build')
CORS(app, supports_credentials=True)
def create_app():  
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 文件日志（100MB轮转，保留3个备份）
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024 * 100,
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # 按环境设置级别
    app.logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)
    app.logger.addHandler(file_handler)
    
    # 开发环境额外添加彩色控制台日志
    if app.debug:
        import colorlog
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s'
        ))
        app.logger.addHandler(stream_handler)
    
    return app

create_app()
# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

app.config.from_pyfile('config.py')
db.init_app(app)
app.register_blueprint(ahp_bp)
app.register_blueprint(checklist_bp)
app.register_blueprint(todolist_bp)
app.register_blueprint(article_bp)
app.register_blueprint(minio_bp)
app.register_blueprint(balanced_decision_bp)
app.register_blueprint(mermaid_bp)
app.register_blueprint(statistics_bp)
app.register_blueprint(logic_errors_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(inspiration_bp)
app.register_blueprint(admin_bp)

# 加载 RSA 私钥
def load_private_key():
    with open("private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
    return private_key

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder + '/static', path)

@app.route('/images/<path:path>')
def image_files(path):
    return send_from_directory(app.static_folder + '/images', path)

# 捕获所有前端路由，将其指向 index.html
@app.route('/<path:path>')
def serve_react_app(path):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test-log')
def test_log():
    current_app.logger.debug('Debug message')
    current_app.logger.info('Info message')
    current_app.logger.warning('Warning message')
    current_app.logger.error('Error message', exc_info=True)
    try:
        1/0
    except Exception as e:
        current_app.logger.critical('Critical error', exc_info=True)
    return "Check your logs"

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# 自定义未登录时的响应
@login_manager.unauthorized_handler
def unauthorized():
    # 返回 JSON 响应，通知前端用户未登录
    return jsonify({'error': 'Unauthorized', 'message': 'Please log in to access this resource.'}), 401

@app.route('/login', methods=['POST'])
def login():
    # 获取 JSON 数据
    data = request.get_json()
    username = data.get('username')
    encrypted_password = data.get('password')
            # 加载私钥
    private_key = load_private_key()

    # 解密密码
    password = private_key.decrypt(
        base64.b64decode(encrypted_password),
        padding.PKCS1v15()
    ).decode('utf-8')

    # 查询用户
    user = AdminUser.query.filter_by(username=username).first()
    
    # 验证用户和密码
    if user and user.check_password(password):
        login_user(user)  # 登录用户
        return jsonify({'message': 'Login successful', 'user_id': user.id,'username':username}), 200

    # 登录失败
    return jsonify({'message': 'Invalid credentials'}), 401
@app.route('/logout', methods=['POST'])
def logout():
    logout_user()  # 使用 Flask-Login 的 logout_user() 退出用户
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    avatar_url = data.get('avatar_url', None)  # 可选头像字段

    # 检查必填字段
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required.'}), 400

    # 检查是否有重复用户
    if AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
        return jsonify({'error': 'Username or email already exists.'}), 400

    # 创建新用户
    user = AdminUser(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        avatar_url=avatar_url
    )

    # 添加到数据库
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'AdminUser registered successfully.'}), 201


# 使用 current_user 的示例
@app.route('/profile')
@login_required
def profile():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5001)
