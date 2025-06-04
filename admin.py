# routes/admin.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime as dt, timedelta
from shared_models import db, User, FreezeRecord

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query
    search = request.args.get('search')
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')))
    
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    users_data = []
    for user in users.items:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'is_frozen': user.is_frozen,
            'frozen_until': user.frozen_until.isoformat() if user.frozen_until else None,
            'created_at': user.created_at.isoformat(),
            'freeze_records': [{
                'id': record.id,
                'action': record.action,
                'reason': record.reason,
                'duration': record.duration,
                'admin_id': record.admin_id,
                'created_at': record.created_at.isoformat()
            } for record in user.freeze_records.limit(3).all()]
        })
    
    return jsonify({
        'users': users_data,
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    })

@admin_bp.route('/users/<int:user_id>/freeze', methods=['POST'])
@login_required
def freeze_user(user_id):
    data = request.get_json()
    reason = data.get('reason')
    duration = data.get('duration')  # '1week', '1month', '1year', 'permanent'
    
    if not reason or not duration:
        return jsonify({'error': 'Reason and duration are required'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # 计算冻结截止时间
    frozen_until = None
    if duration == '1week':
        frozen_until = dt.utcnow() + timedelta(weeks=1)
    elif duration == '1month':
        frozen_until = dt.utcnow() + timedelta(days=30)
    elif duration == '1year':
        frozen_until = dt.utcnow() + timedelta(days=365)
    elif duration == 'permanent':
        frozen_until = None  # 永久冻结
    
    # 更新用户状态
    user.is_frozen = True
    user.frozen_until = frozen_until
    
    # 创建冻结记录
    record = FreezeRecord(
        user_id=user.id,
        action='freeze',
        reason=reason,
        duration=duration,
        frozen_until=frozen_until,
        admin_id=current_user.id
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': 'User frozen successfully',
        'user': {
            'id': user.id,
            'is_frozen': user.is_frozen,
            'frozen_until': user.frozen_until.isoformat() if user.frozen_until else None
        }
    })

@admin_bp.route('/users/<int:user_id>/unfreeze', methods=['POST'])
@login_required
def unfreeze_user(user_id):
    data = request.get_json()
    reason = data.get('reason')
    
    if not reason:
        return jsonify({'error': 'Reason is required'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # 更新用户状态
    user.is_frozen = False
    user.frozen_until = None
    
    # 创建解冻记录
    record = FreezeRecord(
        user_id=user.id,
        action='unfreeze',
        reason=reason,
        duration=None,
        frozen_until=None,
        admin_id=current_user.id
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': 'User unfrozen successfully',
        'user': {
            'id': user.id,
            'is_frozen': user.is_frozen,
            'frozen_until': None
        }
    })