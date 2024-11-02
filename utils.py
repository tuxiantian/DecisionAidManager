from functools import wraps
from flask import jsonify
from shared_models import TodoItem
from flask_login import current_user

def check_todo_permission(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # 检查用户是否已登录
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized access'}), 401
        todo_id = kwargs.get('id')
        todo = TodoItem.query.get(todo_id)
        
        if not todo:
            return jsonify({'error': 'Todo not found'}), 404
        if todo.user_id != current_user.id:
            return jsonify({'error': 'You are not allowed to access this Todo'}), 403
        return func(*args, **kwargs, todo=todo)  # 传递 todo 对象以避免重复查询
    return decorated_function
