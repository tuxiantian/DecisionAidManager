from datetime import datetime
from datetime import datetime as dt

from flask import Flask, abort, request, jsonify, Blueprint
from shared_models import TodoItem, db
from flask_login import current_user, login_required
from utils import check_todo_permission


todolist_bp = Blueprint('todolist', __name__)