import threading
from flask import Blueprint, request, jsonify
from minio import Minio
from minio.error import S3Error
import os
import re
import time
from urllib.parse import quote

minio_bp = Blueprint('minio', __name__)
minio_client = None
# 配置 MinIO 客户端
def initialize_minio():
    global minio_client
    try:
        minio_client = Minio(
            'localhost:9000',  # MinIO 的地址
            access_key='minioadmin',  # MinIO 的访问密钥
            secret_key='minioadmin',  # MinIO 的私密密钥
            secure=False  # 如果使用的是 HTTP 而不是 HTTPS
        )
    except S3Error as e:
        minio_client = None
        print("Warning: Unable to connect to MinIO, retrying...")

# 启动时异步初始化
threading.Thread(target=initialize_minio).start()


BUCKET_NAME = 'decision-aid-bucket'

# 使用 MinIO 时应检查 minio_client 是否可用
if minio_client:
    # MinIO 可用时的处理
    # 创建存储桶（如果不存在）
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
    pass
else:
    # MinIO 不可用时的处理，跳过或做替代方案
    pass

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@minio_bp.before_request
def check_file_size():
    if request.method == 'POST':
        # 处理单文件上传
        if 'file' in request.files:
            file = request.files['file']
            file.seek(0, 2)  # 移动到文件末尾
            size = file.tell()
            file.seek(0)  # 重置文件指针
            if size > MAX_FILE_SIZE:
                return jsonify({'error': f'单个文件大小不能超过 {MAX_FILE_SIZE//(1024*1024)}MB'}), 400
        
        # 处理多文件上传 (字段名为 files[])
        elif 'files[]' in request.files:
            for file in request.files.getlist('files[]'):
                file.seek(0, 2)
                size = file.tell()
                file.seek(0)
                if size > MAX_FILE_SIZE:
                    return jsonify({
                        'error': f'文件 {file.filename} 大小超过限制 ({MAX_FILE_SIZE//(1024*1024)}MB)'
                    }), 400
        
        # 处理自定义多文件字段名
        else:
            for file_field in request.files:
                for file in request.files.getlist(file_field):
                    file.seek(0, 2)
                    size = file.tell()
                    file.seek(0)
                    if size > MAX_FILE_SIZE:
                        return jsonify({
                            'error': f'文件 {file.filename} 大小超过限制 ({MAX_FILE_SIZE//(1024*1024)}MB)'
                        }), 400
        
def mixed_filename(original_filename):
    base, ext = os.path.splitext(original_filename)
    # 保留前10个安全字符（包括中文）
    safe_base = re.sub(r'[^\w\u4e00-\u9fa5]', '', base)[:10] 
    timestamp = int(time.time())
    return f"{timestamp}_{safe_base}{ext}"

ALLOWED_EXTENSIONS = {
    'avatar': {'jpg', 'jpeg', 'png'},
    'article': {'jpg', 'jpeg', 'png'},
    'feedback': {'jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'},
    'inspiration': {'jpg', 'jpeg', 'png'},
    'reflection': {'jpg', 'jpeg', 'png'}
}

def allowed_file(filename, business_type):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(business_type, set())
           
@minio_bp.route('/upload', methods=['POST'])
def upload_file():
    # 获取业务类型参数
    business_type = request.form.get('type')
    
    # 定义允许的业务类型和对应路径
    ALLOWED_TYPES = {
        'avatar': 'avatar/',
        'article': 'article/',
        'feedback': 'feedback/',
        'inspiration': 'inspiration/',
        'reflection': 'reflection/'
    }
    
    # 验证业务类型
    if not business_type or business_type not in ALLOWED_TYPES:
        return jsonify({
            'error': 'Invalid or missing type parameter',
            'allowed_types': list(ALLOWED_TYPES.keys())
        }), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename,business_type):
        return jsonify({
            'error': 'Invalid file type',
            'allowed_file_types': ALLOWED_EXTENSIONS.get(business_type)
        }), 400
    # 将文件名安全化并添加业务路径前缀
    filename = ALLOWED_TYPES[business_type] + mixed_filename(file.filename)

    try:
        # 将文件保存到 MinIO
        minio_client.put_object(
            BUCKET_NAME,
            filename,
            file.stream,
            os.fstat(file.fileno()).st_size,
            content_type=file.content_type
        )

        # 生成可访问的 presigned URL
        file_url = f'http://localhost:5000/files/{filename}'

        return jsonify({'url': file_url,'filename':filename}), 200

    except S3Error as err:
        return jsonify({'error': str(err)}), 500

def rfc5987_encode(filename):
    return "filename*=utf-8''{}".format(quote(filename, safe=''))

@minio_bp.route('/files/<business_type>/<filename>', methods=['GET'])
def serve_file(business_type, filename):
    # 定义允许的业务类型和对应路径
    ALLOWED_TYPES = {
        'avatar': 'avatar/',
        'article': 'article/',
        'feedback': 'feedback/',
        'inspiration': 'inspiration/',
        'reflection': 'reflection/'
    }
    
    # 验证业务类型
    if business_type not in ALLOWED_TYPES:
        return jsonify({
            'error': 'Invalid business type',
            'allowed_types': list(ALLOWED_TYPES.keys())
        }), 400

    # 构建完整的存储路径
    object_path = ALLOWED_TYPES[business_type] + filename
    
    try:
        response = minio_client.get_object(BUCKET_NAME, object_path)
        return response.data, 200, {
            'Content-Type': response.headers['Content-Type'],
            'Content-Disposition': f'inline; filename={rfc5987_encode(filename)}'
        }
    except S3Error as err:
        return jsonify({'error': str(err)}), 404