from flask import Blueprint, request, jsonify
import json
import numpy as np
import pytz
from shared_models import AHPHistory, db  # 确保 AHP.py 文件在同一目录或 Python 路径中
from flask_login import current_user, login_required

ahp_bp = Blueprint('ahp', __name__)

