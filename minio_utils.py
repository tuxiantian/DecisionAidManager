import threading
from flask import Blueprint, request, jsonify
from minio import Minio
from minio.error import S3Error
import os
from werkzeug.utils import secure_filename

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


@minio_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 将文件名安全化
    filename = secure_filename(file.filename)

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
        file_url = f'http://localhost:5000/files/${filename}'

        return jsonify({'url': file_url}), 200

    except S3Error as err:
        return jsonify({'error': str(err)}), 500

@minio_bp.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    try:
        response = minio_client.get_object(BUCKET_NAME, filename)
        return response.data, 200, {
            'Content-Type': response.headers['Content-Type'],
            'Content-Disposition': f'inline; filename={filename}'
        }
    except S3Error as err:
        return jsonify({'error': str(err)}), 404
