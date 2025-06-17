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
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_term = request.args.get('search', '').strip()
        content_type = request.args.get('type')  # 'text' 或 'image'
        
        # 构建基础查询
        query = Inspiration.query.order_by(Inspiration.created_at.desc())
        
        # 添加搜索条件
        if search_term:
            if content_type == 'text':
                query = query.filter(
                    Inspiration.type == 'text',
                    Inspiration.content.ilike(f'%{search_term}%')
                )
            elif content_type == 'image':
                query = query.filter(
                    Inspiration.type == 'image',
                    Inspiration.description.ilike(f'%{search_term}%')
                )
            else:
                query = query.filter(
                    Inspiration.content.ilike(f'%{search_term}%')
                )
        
        # 添加类型过滤
        if content_type in ['text', 'image']:
            query = query.filter(Inspiration.type == content_type)
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        inspirations = pagination.items
        
        # 构建响应数据
        result = []
        for item in inspirations:
            has_reflections = bool(item.reflections)
            result.append({
                'id': item.id,
                'type': item.type,
                'content': item.content,
                'description': item.description,
                'created_at': item.created_at.isoformat(),
                'has_reflections': has_reflections
            })
        
        return jsonify({
            'data': result,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
        
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
            content=data['content'],
            description=data['description']
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
        inspiration.description = data['description']
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