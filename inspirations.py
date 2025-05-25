from flask import Flask, request, jsonify, Blueprint
from sqlalchemy import desc
from shared_models import Inspiration,Reflection, db
from datetime import datetime as dt
from flask_login import current_user, login_required
from sqlalchemy import func
inspiration_bp = Blueprint('inspiration', __name__)

# 获取所有启发内容（管理用）
@inspiration_bp.route('/api/admin/inspirations', methods=['GET'])
@login_required  # 需要管理员权限
def get_all_inspirations():
    try:
        inspirations = Inspiration.query.order_by(Inspiration.created_at.desc()).all()
        result = []
        for item in inspirations:
            # 检查是否有感想
            has_reflections = bool(item.reflections)
            result.append({
                'id': item.id,
                'type': item.type,
                'content': item.content,
                'created_at': item.created_at.isoformat(),
                'has_reflections': has_reflections
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 创建启发内容
@inspiration_bp.route('/api/admin/inspirations', methods=['POST'])
@login_required
def create_inspiration():
    data = request.get_json()
    if not data or not data.get('type') or not data.get('content'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        inspiration = Inspiration(
            type=data['type'],
            content=data['content']
        )
        db.session.add(inspiration)
        db.session.commit()
        return jsonify({
            'id': inspiration.id,
            'message': '创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新启发内容
@inspiration_bp.route('/api/admin/inspirations/<int:id>', methods=['PUT'])
@login_required
def update_inspiration(id):
    inspiration = Inspiration.query.get_or_404(id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'Content is required'}), 400
    
    try:
        inspiration.content = data['content']
        inspiration.type = data.get('type', inspiration.type)
        db.session.commit()
        return jsonify({
            'id': inspiration.id,
            'message': '更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除启发内容
@inspiration_bp.route('/api/admin/inspirations/<int:id>', methods=['DELETE'])
@login_required
def delete_inspiration(id):
    inspiration = Inspiration.query.get_or_404(id)
    
    # 检查是否有感想
    if inspiration.reflections:
        return jsonify({
            'error': '该启发已有用户感想，不能删除',
            'can_delete': False
        }), 400
    
    try:
        db.session.delete(inspiration)
        db.session.commit()
        return jsonify({
            'message': '删除成功',
            'can_delete': True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500